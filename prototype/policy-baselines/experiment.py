"""Pre-event, standard-library baselines on an already-seen synthetic holdout."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import random
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PINS = {
    "policy.py": "52810b9e0d982d3d04cd611bb9b908ce0d69c8fde77069055d594d8ad5ce178c",
    "synthetic-model.json": "6924de782bd52944d5bf87352f9a7dd0bc1e4e0518bcd5ba04f9ea6fcffb67b8",
    "synthetic-model-results.json": "c53df744e75e5ab0ebe0f2f37da0b743c57bb42e1e44e56e210fe71f61123123",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_reference(directory=ROOT / "prototype/policy"):
    """Verify all reference bytes before executing the pinned generator."""
    directory = Path(directory)
    for name, expected in PINS.items():
        if sha(directory / name) != expected:
            raise ValueError(f"Pinned reference changed: {name}")
    spec = importlib.util.spec_from_file_location("pinned_baseline_policy", directory / "policy.py")
    policy = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = policy
    spec.loader.exec_module(policy)
    artifact = json.loads((directory / "synthetic-model.json").read_text())
    original_results = json.loads((directory / "synthetic-model-results.json").read_text())
    if policy.canonical_hash(artifact["parameters"]) != artifact["parameters_sha256"]:
        raise ValueError("Reference parameter checksum mismatch")
    splits = policy.generate_data(artifact["training"]["seed"], artifact["training"]["per_family"])
    verify_splits(policy, splits, artifact["dataset"])
    return policy, artifact, original_results, splits


def verify_splits(policy, splits, expected):
    if policy.dataset_manifest(splits) != expected:
        raise ValueError("Procedural split checksum mismatch")
    families = [{row.family for row in splits[name]} for name in ("train", "dev", "holdout")]
    if any(families[i] & families[j] for i in range(3) for j in range(i)):
        raise ValueError("Split family overlap")
    row_sets = [{policy.canonical_hash(row.features) for row in splits[name]}
                for name in ("train", "dev", "holdout")]
    if any(row_sets[i] & row_sets[j] for i in range(3) for j in range(i)):
        raise ValueError("Exact feature-vector overlap")


class Logistic:
    """Six-input logit, with optional nonnegative weight projection; signed bias."""
    def __init__(self, policy, weights=None, bias=0.0, projected=False):
        self.policy = policy
        self.weights = list(weights if weights is not None else [0.0] * 6)
        self.bias = bias
        self.projected = projected
        if len(self.weights) != 6 or any(not math.isfinite(x) for x in self.weights + [bias]):
            raise ValueError("Invalid logistic parameters")
        if projected and any(w < 0 for w in self.weights):
            raise ValueError("Projected coefficients must be nonnegative")

    def parameters(self):
        return {"weights": self.weights[:], "bias": self.bias, "projected": self.projected}

    def forward(self, values):
        x = self.policy.validated_features(values)
        z = self.bias + sum(w * v for w, v in zip(self.weights, x))
        return None, None, z, self.policy.sigmoid(z)

    def probability(self, values):
        return self.forward(values)[3]

    def explain(self, values):
        x = self.policy.validated_features(values)
        contributions = {name: w * v for name, w, v in zip(self.policy.FEATURES, self.weights, x)}
        z = self.bias + sum(contributions.values())
        return {"bias": self.bias, "contributions": contributions, "logit": z,
                "probability": self.policy.sigmoid(z)}

    def step(self, features, label, rate):
        x = self.policy.validated_features(features)
        error = self.probability(x) - label
        self.weights = [w - rate * error * v for w, v in zip(self.weights, x)]
        if self.projected:
            self.weights = [max(0.0, w) for w in self.weights]
        self.bias -= rate * error


def fit(policy, train, dev, protocol, projected):
    """No holdout argument: updates use train, checkpoint/threshold use dev only."""
    model = Logistic(policy, projected=projected)
    initial = model.parameters()
    best = initial
    best_loss = policy.metrics(model, dev, 0.5)["binary_cross_entropy"]
    best_epoch = 0
    order = list(train)
    rng = random.Random(protocol["seed"] + 1)
    history = []
    for epoch in range(1, protocol["epochs"] + 1):
        rng.shuffle(order)
        rate = protocol["initial_learning_rate"] / math.sqrt(1 + epoch / 25)
        for row in order:
            model.step(row.features, row.label, rate)
        dev_loss = policy.metrics(model, dev, 0.5)["binary_cross_entropy"]
        if dev_loss < best_loss:
            best_loss, best_epoch, best = dev_loss, epoch, model.parameters()
        if epoch == 1 or epoch % 20 == 0 or epoch == protocol["epochs"]:
            history.append({"epoch": epoch, "dev_bce": dev_loss, "learning_rate": rate})
    selected = Logistic(policy, **best)
    threshold = min(protocol["threshold_grid"], key=lambda t: (
        1 - policy.metrics(selected, dev, t)["accuracy"], abs(t - 0.5), t))
    return selected, {"selected_epoch": best_epoch, "threshold": threshold,
                      "history": history, "initial_parameters_sha256": policy.canonical_hash(initial),
                      "selected_parameters_sha256": policy.canonical_hash(best),
                      "parameter_update_l2": math.sqrt(sum(v * v for v in best["weights"]) + best["bias"] ** 2)}


class HardRule:
    def __init__(self, policy, rule):
        self.policy, self.rule = policy, rule

    def probability(self, values):
        return float(self.rule(self.policy.validated_features(values)))


def hard_metrics(policy, model, rows):
    pairs = [(model.probability(row.features), row.label) for row in rows]
    tp = sum(p == 1 and y == 1 for p, y in pairs)
    fp = sum(p == 1 and y == 0 for p, y in pairs)
    tn = sum(p == 0 and y == 0 for p, y in pairs)
    fn = sum(p == 0 and y == 1 for p, y in pairs)
    error = (fp + fn) / len(rows)
    return {"count": len(rows), "positives": tp + fn, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "accuracy": 1 - error, "precision": tp / (tp + fp) if tp + fp else 0,
            "recall": tp / (tp + fn) if tp + fn else 0,
            "false_nudge_rate": fp / (fp + tn) if fp + tn else 0,
            "brier": error, "ece_probability_bins_10": error,
            "binary_cross_entropy": None if fp + fn else 0.0,
            "bce_scope": "Point-mass 0/1 predictions: null denotes infinite BCE when any prediction is wrong; no fitted probabilities"}


def gate_checks(policy, models, thresholds):
    gates = {"paused": {"paused": True}, "permission": {"permission_granted": False},
             "focus": {"focus_active": False}, "cooldown": {"cooldown": True},
             "freshness": {"observation_fresh": False}}
    results = {}
    for name, model in models.items():
        trace = {}
        for gate, flags in gates.items():
            result = policy.policy_decision(model, [1.0] * 6, thresholds[name], **flags)
            trace[gate] = result
            if result["recommendation"] != "blocked" or result["probability"] is not None:
                raise ValueError(f"External gate bypass: {name}/{gate}")
        results[name] = trace
    return {"checks": len(models) * len(gates), "failures": 0, "trace": results,
            "scope": "Pinned Python external gate; not Android lifecycle/permission or extraction evidence"}


def freeze():
    policy, artifact, _, splits = load_reference()
    protocol = {"schema": "focuspilot.policy-baselines.protocol.v1",
                "frozen_utc": datetime.now(timezone.utc).isoformat(),
                "origin": "Pre-event research; synthetic labels, informed previously reported holdout",
                "source_sha256": sha(__file__), "references": PINS,
                "dataset": policy.dataset_manifest(splits), "seed": 20261002,
                "epochs": 140, "initial_learning_rate": 0.02,
                "initialization": "All six coefficients and bias zero; no feature transformations or regularization",
                "optimizers": ["signed SGD", "SGD with nonnegative coefficient projection; signed bias"],
                "schedule": "initial_rate / sqrt(1 + epoch/25)",
                "selection": "Epoch 0 through 140: strict minimum development BCE, earliest tie; then development accuracy threshold, closest to .5 then smallest on ties",
                "threshold_grid": [i / 100 for i in range(10, 91)],
                "parameter_count_per_logistic": 7,
                "holdout_role": "Reporting only after dev selection; author knows earlier reference results and teacher. No blind benchmark claim.",
                "comparators": ["immutable 65-parameter network", "known teacher", "original simple rule", "training-majority label"],
                "counterexamples": "First five wrong rows per learned model in existing holdout order; all pairwise correct-only counts. Never used for selection.",
                "benchmark": "Five passes through 480 holdout inputs after one warm pass; Python host CPU validation+forward only, no phone/NPU/end-to-end claim"}
    path = HERE / "protocol.json"
    prior = HERE / "build/pre-fit-protocol.json"
    if prior.exists():
        protocol["pre_fit_revision"] = {"superseded_protocol_sha256": sha(prior),
            "reason": "Focused gate test caught recommendation/decision field-name mismatch before experiment training; no training-budget or data changes"}
    if path.exists():
        raise ValueError("Protocol already frozen; do not overwrite")
    write_json(path, protocol)
    print(json.dumps({"protocol_sha256": sha(path), "dataset": protocol["dataset"]}, sort_keys=True))


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    if sha(__file__) != protocol["source_sha256"]:
        raise ValueError("Experiment source differs from frozen protocol")
    if (HERE / "results.json").exists():
        raise ValueError("Results already frozen; use --verify instead of fitting again")
    policy, artifact, original_results, splits = load_reference()
    if policy.dataset_manifest(splits) != protocol["dataset"]:
        raise ValueError("Protocol dataset differs from pinned reference")
    build = HERE / "build"
    build.mkdir(exist_ok=True)
    write_json(build / "procedural-rows.json", {
        split: [{"id": f"{split}-{i:04d}", "family": row.family, "features": row.features, "label": row.label}
                for i, row in enumerate(rows)] for split, rows in splits.items()})
    models = {"positive_network": policy.PositiveNetwork(artifact["parameters"])}
    thresholds = {"positive_network": artifact["training"]["threshold"]}
    selection = {}
    print("PHASE fitting fixed signed and projected logistic candidates", flush=True)
    for name, projected in (("signed_logistic", False), ("projected_logistic", True)):
        start = time.perf_counter()
        model, details = fit(policy, splits["train"], splits["dev"], protocol, projected)
        details["fit_and_dev_selection_host_cpu_seconds"] = time.perf_counter() - start
        models[name] = model
        thresholds[name] = details["threshold"]
        write_json(build / f"{name}.json", model.parameters())
        details["checkpoint_sha256"] = sha(build / f"{name}.json")
        selection[name] = details
        print(f"PHASE {name} fixed epoch={details['selected_epoch']} threshold={details['threshold']}", flush=True)
    majority = int(sum(row.label for row in splits["train"]) >= len(splits["train"]) / 2)
    models.update({"teacher_oracle": HardRule(policy, policy.synthetic_label),
                   "simple_rule": HardRule(policy, lambda x: int(x[0] >= 0.55 or x[1] >= 0.65)),
                   "training_majority": HardRule(policy, lambda x: majority)})
    thresholds.update({name: 0.5 for name in ("teacher_oracle", "simple_rule", "training_majority")})
    print("PHASE reporting unchanged previously-seen holdout; no selection", flush=True)
    evaluations = {}
    for name, model in models.items():
        metric = (lambda rows: hard_metrics(policy, model, rows)) if isinstance(model, HardRule) else (
            lambda rows: policy.metrics(model, rows, thresholds[name]))
        evaluations[name] = {split: metric(rows) for split, rows in splits.items()}
        evaluations[name]["holdout_by_family"] = {
            family: metric([row for row in splits["holdout"] if row.family == family])
            for family in policy.SPLIT_FAMILIES["holdout"]}
    for split in splits:
        if evaluations["positive_network"][split] != original_results[split]:
            raise ValueError("Immutable network metric reproduction mismatch")
    correctness = {name: [int(model.probability(row.features) >= thresholds[name]) == row.label
                          for row in splits["holdout"]] for name, model in models.items()}
    paired = {f"{a}_vs_{b}": {"a_correct_b_wrong": sum(x and not y for x, y in zip(correctness[a], correctness[b])),
                              "a_wrong_b_correct": sum(not x and y for x, y in zip(correctness[a], correctness[b]))}
              for i, a in enumerate(models) for b in list(models)[i + 1:]}
    witnesses = {}
    contribution_summaries = {}
    coefficients = {}
    for name in ("signed_logistic", "projected_logistic"):
        model = models[name]
        errors = []
        max_sum_error = 0.0
        for i, row in enumerate(splits["holdout"]):
            explanation = model.explain(row.features)
            max_sum_error = max(max_sum_error, abs(explanation["logit"] - model.forward(row.features)[2]))
            pred = int(model.probability(row.features) >= thresholds[name])
            if pred != row.label and len(errors) < 5:
                errors.append({"id": f"holdout-{i:04d}", "family": row.family,
                               "features": row.features, "label": row.label, "prediction": pred,
                               "threshold": thresholds[name], "teacher_relu_interaction": 2.5 * max(0, row.features[0] + row.features[1] - .95),
                               "explanation": explanation})
        witnesses[name] = errors
        coefficients[name] = {"features": dict(zip(policy.FEATURES, model.weights)), "bias": model.bias,
                              "negative_coefficients": sum(w < 0 for w in model.weights)}
        contribution_summaries[name] = {"rows_checked": 480, "max_additive_logit_error": max_sum_error,
                                        "scope": "Exact coefficient*x contributions to this seven-parameter logit; not Qwen neurons or validated human concepts"}
    write_json(build / "counterexamples.json", witnesses)
    times = {}
    for name, model in models.items():
        for row in splits["holdout"]:
            model.probability(row.features)
        start = time.perf_counter()
        for _ in range(5):
            for row in splits["holdout"]:
                model.probability(row.features)
        times[name] = {"passes": 5, "calls": 2400,
                       "mean_microseconds_per_call": (time.perf_counter() - start) * 1e6 / 2400}
    results = {"schema": "focuspilot.policy-baselines.results.v1", "completed_utc": datetime.now(timezone.utc).isoformat(),
               "protocol_sha256": sha(HERE / "protocol.json"), "source_sha256": sha(__file__),
               "references": PINS, "dataset": policy.dataset_manifest(splits),
               "reference_parameters_sha256": artifact["parameters_sha256"],
               "raw_rows_sha256": sha(build / "procedural-rows.json"),
               "selection": selection, "coefficients": coefficients, "thresholds": thresholds,
               "evaluations": evaluations, "paired_holdout": paired,
               "external_gates": gate_checks(policy, models, thresholds),
               "additive_logit_checks": contribution_summaries,
               "counterexamples_sha256": sha(build / "counterexamples.json"),
               "counterexample_ids": {name: [row["id"] for row in rows] for name, rows in witnesses.items()},
               "projected_monotonicity": policy.monotonicity_check(models["projected_logistic"]),
               "host": {"python": platform.python_version(), "platform": platform.platform(), "machine": platform.machine()},
               "warm_forward_microbenchmark": times,
               "limitations": ["Known synthetic teacher, shared across family splits; holdout already reported and author-informed.",
                               "Two newly fitted seven-parameter policies, no Qwen fine-tuning or change to reference network.",
                               "Fixed 140-epoch SGD budget, not proof of optimal logistic regression fit or neural necessity.",
                               "ECE ten bins on 480 synthetic rows is descriptive, not calibrated real-world confidence.",
                               "No real productivity labels, feature extraction, phone benchmark, NPU, payment, runtime promotion or event eligibility."]}
    write_json(HERE / "results.json", results)
    write_json(HERE / "run-manifest.json", {"source_sha256": sha(__file__), "protocol_sha256": sha(HERE / "protocol.json"),
               "results_sha256": sha(HERE / "results.json"), "references": PINS,
               "artifact_hashes": {p.name: sha(p) for p in sorted(build.glob("*.json"))}})
    print(json.dumps({name: value["holdout"] for name, value in evaluations.items()}, sort_keys=True))


def verify():
    policy, artifact, _, splits = load_reference()
    manifest = json.loads((HERE / "run-manifest.json").read_text())
    for key, path in (("source_sha256", Path(__file__)), ("protocol_sha256", HERE / "protocol.json"),
                      ("results_sha256", HERE / "results.json")):
        if sha(path) != manifest[key]:
            raise ValueError(f"Frozen file changed: {path.name}")
    results = json.loads((HERE / "results.json").read_text())
    verify_splits(policy, splits, results["dataset"])
    checked = []
    for name, expected in manifest["artifact_hashes"].items():
        path = HERE / "build" / name
        if path.exists():
            if sha(path) != expected:
                raise ValueError(f"Ignored artifact changed: {name}")
            checked.append(name)
    for name in ("signed_logistic", "projected_logistic"):
        values = results["coefficients"][name]
        model = Logistic(policy, [values["features"][feature] for feature in policy.FEATURES], values["bias"],
                         projected=name == "projected_logistic")
        if policy.canonical_hash(model.parameters()) != results["selection"][name]["selected_parameters_sha256"]:
            raise ValueError("Learned parameter hash mismatch")
        for split, rows in splits.items():
            if policy.metrics(model, rows, results["thresholds"][name]) != results["evaluations"][name][split]:
                raise ValueError("Learned metric reproduction mismatch")
    print(json.dumps({"verified": True, "ignored_artifacts_present_and_checked": checked,
                      "fitting": False, "references": PINS}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "run", "verify"))
    args = parser.parse_args()
    {"freeze": freeze, "run": run, "verify": verify}[args.mode]()
