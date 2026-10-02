"""Pre-event synthetic policy experiment. No phone, payment, or LLM integration."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random
from typing import Any

FEATURES = (
    "selected_app_budget_overrun",
    "continuous_session_overrun",
    "reopen_count",
    "active_focus_overlap",
    "deferred_nudges",
    "elapsed_time_overrun",
)
SPLIT_FAMILIES = {
    "train": ("broad_mixture", "reopening", "budget_dominant", "session_dominant"),
    "dev": ("near_balanced_boundary", "split_overtime"),
    "holdout": ("correlated_overruns", "sparse_extremes", "moderate_everywhere"),
}
PARAMETER_COUNT = 65


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def validated_features(values: list[float]) -> list[float]:
    if len(values) != len(FEATURES):
        raise ValueError("Exactly six risk features are required")
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        raise ValueError("Risk features must be finite numbers in [0, 1]")
    return [float(v) for v in values]


def synthetic_label(x: list[float]) -> int:
    """Known, invented monotone teacher. This is not a human productivity label."""
    score = (3.1 * x[0] + 2.3 * x[1] + x[2] + 0.8 * x[3] + 0.55 * x[4]
             + 0.9 * x[5] + 2.5 * max(0.0, x[0] + x[1] - 0.95) - 4.1)
    return int(score >= 0)


@dataclass(frozen=True)
class Example:
    family: str
    features: list[float]
    label: int


def generate_data(seed: int = 20261002, per_family: int = 160) -> dict[str, list[Example]]:
    """Group by different synthetic feature distributions; never randomly split rows."""
    if per_family < 10:
        raise ValueError("At least ten examples per family are required")
    splits: dict[str, list[Example]] = {}
    for split, families in SPLIT_FAMILIES.items():
        splits[split] = []
        for family in families:
            family_seed = int(hashlib.sha256(f"{seed}:{family}".encode()).hexdigest()[:16], 16)
            rng = random.Random(family_seed)
            for _ in range(per_family):
                x = [rng.random() for _ in FEATURES]
                if family == "reopening":
                    x[0], x[1] = rng.uniform(0, 0.65), rng.uniform(0, 0.65)
                    x[2] = rng.uniform(0.6, 1)
                elif family == "budget_dominant":
                    x[0], x[1] = rng.uniform(0.25, 1), rng.uniform(0, 0.4)
                elif family == "session_dominant":
                    x[0], x[1] = rng.uniform(0, 0.4), rng.uniform(0.25, 1)
                elif family == "near_balanced_boundary":
                    x[0], x[1] = rng.uniform(0.25, 0.65), rng.uniform(0.25, 0.65)
                elif family == "split_overtime":
                    x[0] = rng.random()
                    x[1] = min(1, max(0, 1 - x[0] + rng.uniform(-0.25, 0.25)))
                elif family == "correlated_overruns":
                    center = rng.random()
                    x[0], x[1] = (min(1, max(0, center + rng.uniform(-0.1, 0.1)))
                                   for _ in range(2))
                elif family == "sparse_extremes":
                    x = [rng.uniform(0.75, 1) if rng.random() < 0.45
                         else rng.uniform(0, 0.12) for _ in FEATURES]
                elif family == "moderate_everywhere":
                    x = [rng.uniform(0.2, 0.75) for _ in FEATURES]
                splits[split].append(Example(family, x, synthetic_label(x)))
    return splits


def dataset_manifest(splits: dict[str, list[Example]]) -> dict[str, Any]:
    return {
        name: {"count": len(rows), "positives": sum(r.label for r in rows),
               "families": sorted({r.family for r in rows}),
               "sha256": canonical_hash([
                   {"family": r.family, "features": r.features, "label": r.label} for r in rows])}
        for name, rows in splits.items()
    }


class PositiveNetwork:
    """6 -> 8 ReLU -> 1 sigmoid, nonnegative weights and signed biases."""

    def __init__(self, parameters: dict[str, Any]):
        self.parameters = json.loads(json.dumps(parameters, allow_nan=False))
        p = self.parameters
        if (set(p) != {"input_weights", "hidden_biases", "output_weights", "output_bias"}
                or len(p["input_weights"]) != 8
                or any(len(row) != 6 for row in p["input_weights"])
                or len(p["hidden_biases"]) != 8 or len(p["output_weights"]) != 8):
            raise ValueError("Invalid 6->8->1 parameter shape")
        weights = [v for row in p["input_weights"] for v in row] + p["output_weights"]
        values = weights + p["hidden_biases"] + [p["output_bias"]]
        if any(isinstance(v, bool) or not isinstance(v, (int, float))
               or not math.isfinite(v) for v in values) or any(w < 0 for w in weights):
            raise ValueError("Finite parameters and nonnegative connection weights required")

    @classmethod
    def initialize(cls, seed: int) -> PositiveNetwork:
        rng = random.Random(seed)
        return cls({
            "input_weights": [[rng.uniform(0.03, 0.3) for _ in FEATURES] for _ in range(8)],
            "hidden_biases": [rng.uniform(-0.35, -0.05) for _ in range(8)],
            "output_weights": [rng.uniform(0.1, 0.4) for _ in range(8)],
            "output_bias": -0.5,
        })

    def forward(self, features: list[float]) -> tuple[list[float], list[float], float, float]:
        x = validated_features(features)
        p = self.parameters
        pre = [sum(w * v for w, v in zip(row, x)) + bias
               for row, bias in zip(p["input_weights"], p["hidden_biases"])]
        hidden = [max(0.0, value) for value in pre]
        logit = p["output_bias"] + sum(w * h for w, h in zip(p["output_weights"], hidden))
        return pre, hidden, logit, sigmoid(logit)

    def probability(self, features: list[float]) -> float:
        return self.forward(features)[3]

    def gradients(self, features: list[float], target: int) -> dict[str, Any]:
        x = validated_features(features)
        pre, hidden, _, probability = self.forward(x)
        delta = probability - target
        hidden_delta = [delta * w if z > 0 else 0.0
                        for w, z in zip(self.parameters["output_weights"], pre)]
        return {"input_weights": [[d * v for v in x] for d in hidden_delta],
                "hidden_biases": hidden_delta,
                "output_weights": [delta * h for h in hidden],
                "output_bias": delta}

    def step(self, features: list[float], target: int, learning_rate: float) -> None:
        gradients = self.gradients(features, target)
        p = self.parameters
        for j in range(8):
            for i in range(6):
                p["input_weights"][j][i] = max(
                    0.0, p["input_weights"][j][i] - learning_rate * gradients["input_weights"][j][i])
            p["hidden_biases"][j] -= learning_rate * gradients["hidden_biases"][j]
            p["output_weights"][j] = max(
                0.0, p["output_weights"][j] - learning_rate * gradients["output_weights"][j])
        p["output_bias"] -= learning_rate * gradients["output_bias"]

    def inspect(self, features: list[float]) -> dict[str, Any]:
        x = validated_features(features)
        pre, hidden, logit, probability = self.forward(x)
        units = []
        for j, (z, activation, weight) in enumerate(zip(
                pre, hidden, self.parameters["output_weights"])):
            contribution = activation * weight
            units.append({"unit": j, "preactivation": z, "activation": activation,
                          "output_weight": weight, "logit_contribution": contribution,
                          "probability_if_suppressed": sigmoid(logit - contribution)})
        ablations = []
        for i, name in enumerate(FEATURES):
            changed = x[:]
            changed[i] = 0.0
            changed_probability = self.probability(changed)
            ablations.append({"feature": name, "original": x[i], "intervened": 0.0,
                              "probability_after": changed_probability,
                              "score_drop": probability - changed_probability})
        return {"features": dict(zip(FEATURES, x)), "output_bias": self.parameters["output_bias"],
                "logit": logit, "probability": probability, "hidden_units": units,
                "feature_ablations": ablations,
                "interpretation": "Contributions sum exactly in logit space. Feature ablations are not additive. "
                                  "Units have no validated semantic concept labels. No LLM is interpreted."}


def policy_decision(model: PositiveNetwork, features: list[float], threshold: float,
                    *, paused: bool = False, permission_granted: bool = True,
                    focus_active: bool = True, cooldown: bool = False,
                    observation_fresh: bool = True) -> dict[str, Any]:
    """External gates dominate scoring; returns recommendations, never actions/debits."""
    flags = (paused, permission_granted, focus_active, cooldown, observation_fresh)
    if any(type(flag) is not bool for flag in flags):
        raise ValueError("Policy gates must be explicit booleans")
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be in [0,1]")
    for blocked, reason in ((paused, "paused"), (not permission_granted, "permission_denied"),
                            (not focus_active, "focus_inactive"), (cooldown, "cooldown"),
                            (not observation_fresh, "stale_observation")):
        if blocked:
            return {"recommendation": "blocked", "reason": reason, "probability": None}
    probability = model.probability(features)
    return {"recommendation": "offer_nudge" if probability >= threshold else "allow",
            "reason": "synthetic_score_threshold", "probability": probability,
            "threshold": threshold, "execution": "none"}


def metrics(model: PositiveNetwork, rows: list[Example], threshold: float) -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot evaluate an empty split")
    pairs = [(model.probability(r.features), r.label) for r in rows]
    tp = sum(p >= threshold and y == 1 for p, y in pairs)
    fp = sum(p >= threshold and y == 0 for p, y in pairs)
    tn = sum(p < threshold and y == 0 for p, y in pairs)
    fn = sum(p < threshold and y == 1 for p, y in pairs)
    ece = 0.0
    for bucket in range(10):
        values = [(p, y) for p, y in pairs if min(9, int(p * 10)) == bucket]
        if values:
            ece += len(values) / len(pairs) * abs(
                sum(p for p, _ in values) / len(values) - sum(y for _, y in values) / len(values))
    loss = sum(max(z, 0) - z * r.label + math.log1p(math.exp(-abs(z)))
               for r in rows for z in [model.forward(r.features)[2]]) / len(rows)
    return {"count": len(rows), "positives": tp + fn, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "accuracy": (tp + tn) / len(rows), "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "false_nudge_rate": fp / (fp + tn) if fp + tn else None,
            "binary_cross_entropy": loss, "brier": sum((p - y) ** 2 for p, y in pairs) / len(pairs),
            "ece_probability_bins_10": ece}


def train(seed: int = 20261002, epochs: int = 140, learning_rate: float = 0.02,
          per_family: int = 160) -> tuple[PositiveNetwork, dict[str, Any], dict[str, list[Example]]]:
    if epochs < 1 or not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("Positive epochs and finite learning rate required")
    splits = generate_data(seed, per_family)
    model = PositiveNetwork.initialize(seed)
    rng = random.Random(seed + 1)
    initial = metrics(model, splits["dev"], 0.5)
    best_parameters = json.loads(json.dumps(model.parameters))
    best_loss = initial["binary_cross_entropy"]
    best_epoch = 0
    history = []
    order = splits["train"][:]
    for epoch in range(1, epochs + 1):
        rng.shuffle(order)
        rate = learning_rate / math.sqrt(1 + epoch / 25)
        for row in order:
            model.step(row.features, row.label, rate)
        dev_loss = metrics(model, splits["dev"], 0.5)["binary_cross_entropy"]
        if dev_loss < best_loss:
            best_loss, best_epoch = dev_loss, epoch
            best_parameters = json.loads(json.dumps(model.parameters))
        if epoch == 1 or epoch % 20 == 0 or epoch == epochs:
            history.append({"epoch": epoch, "learning_rate": rate, "dev_cross_entropy": dev_loss})
    model = PositiveNetwork(best_parameters)
    # Tune only on dev. Holdout is never consulted by optimization or threshold choice.
    thresholds = [i / 100 for i in range(10, 91)]
    threshold = min(thresholds, key=lambda t: (
        1 - metrics(model, splits["dev"], t)["accuracy"], abs(t - 0.5), t))
    details = {"seed": seed, "epochs": epochs, "initial_learning_rate": learning_rate,
               "per_family": per_family, "selected_epoch": best_epoch,
               "selection": "lowest dev binary cross entropy; threshold maximizes dev accuracy",
               "threshold": threshold, "initial_dev_metrics": initial, "history": history,
               "optimizer": "per-example projected SGD; connection weights clipped at zero; signed biases",
               "learning_rate_schedule": "initial_rate / sqrt(1 + epoch/25)"}
    return model, details, splits


def monotonicity_check(model: PositiveNetwork, seed: int = 9, trials: int = 300) -> dict[str, Any]:
    rng = random.Random(seed)
    failures = 0
    largest_drop = 0.0
    for _ in range(trials):
        features = [rng.random() for _ in FEATURES]
        before = model.probability(features)
        for i in range(6):
            changed = features[:]
            changed[i] += rng.random() * (1 - changed[i])
            drop = before - model.probability(changed)
            largest_drop = max(largest_drop, drop)
            failures += drop > 1e-12
    return {"pairs": trials * 6, "seed": seed, "failures": failures,
            "largest_score_drop": largest_drop,
            "scope": "sampled checks plus architectural guarantee for finite [0,1] risk features"}


def evaluate(model: PositiveNetwork, splits: dict[str, list[Example]], threshold: float) -> dict[str, Any]:
    results = {name: metrics(model, rows, threshold) for name, rows in splits.items()}
    results["holdout_by_family"] = {
        family: metrics(model, [r for r in splits["holdout"] if r.family == family], threshold)
        for family in SPLIT_FAMILIES["holdout"]}
    # A deliberately simple practical rule, not the exact invented teacher.
    holdout = splits["holdout"]
    rule_correct = sum(int(r.features[0] >= 0.55 or r.features[1] >= 0.65) == r.label for r in holdout)
    majority = max(sum(r.label for r in splits["train"]),
                   len(splits["train"]) - sum(r.label for r in splits["train"]))
    majority_label = int(sum(r.label for r in splits["train"]) >= len(splits["train"]) / 2)
    results["baselines"] = {
        "simple_rule": {"rule": "budget_overrun >= .55 OR continuous_overrun >= .65",
                        "holdout_accuracy": rule_correct / len(holdout)},
        "training_majority": {"label": majority_label,
                              "train_accuracy": majority / len(splits["train"]),
                              "holdout_accuracy": sum(r.label == majority_label for r in holdout) / len(holdout)},
        "teacher_oracle": {"holdout_accuracy": 1.0,
                           "warning": "Labels are generated by this known rule; not an independent benchmark"},
    }
    results["monotonicity"] = monotonicity_check(model)
    return results
