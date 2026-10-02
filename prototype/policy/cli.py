"""Run from any directory: python3 /absolute/path/to/cli.py train|evaluate|inspect."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time

from policy import (FEATURES, PARAMETER_COUNT, PositiveNetwork, canonical_hash,
                    dataset_manifest, evaluate, generate_data, policy_decision, train)

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / "synthetic-model.json"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def load_artifact(path: Path) -> tuple[dict, PositiveNetwork]:
    artifact = json.loads(path.read_text())
    if artifact.get("schema") != "focuspilot.synthetic-positive-policy.v1":
        raise ValueError("Unknown model artifact schema")
    if artifact["features"] != list(FEATURES):
        raise ValueError("Incompatible feature order")
    if canonical_hash(artifact["parameters"]) != artifact["parameters_sha256"]:
        raise ValueError("Model checksum mismatch")
    return artifact, PositiveNetwork(artifact["parameters"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-event synthetic 65-parameter policy research; no phone integration")
    sub = parser.add_subparsers(dest="command", required=True)
    training = sub.add_parser("train")
    training.add_argument("--seed", type=int, default=20261002)
    training.add_argument("--epochs", type=int, default=140)
    training.add_argument("--per-family", type=int, default=160)
    training.add_argument("--learning-rate", type=float, default=0.02)
    training.add_argument("--output", type=Path, default=DEFAULT_MODEL)
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    evaluation.add_argument("--output", type=Path)
    inspection = sub.add_parser("inspect")
    inspection.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    inspection.add_argument("--features", required=True, help="Six comma-separated values in documented order")
    inspection.add_argument("--intervene", help="A single feature name=value counterfactual")
    inspection.add_argument("--paused", action="store_true")
    inspection.add_argument("--permission-denied", action="store_true")
    inspection.add_argument("--cooldown", action="store_true")
    args = parser.parse_args()
    if args.command == "train":
        started = time.perf_counter()
        model, details, splits = train(args.seed, args.epochs, args.learning_rate, args.per_family)
        elapsed = time.perf_counter() - started
        artifact = {
            "schema": "focuspilot.synthetic-positive-policy.v1",
            "origin": "Pre-event laboratory research created 2026-10-02; not event-created submission",
            "limitations": "Invented synthetic labels; no real productivity learning, phone integration, LLM interpretation, or NPU proof",
            "architecture": "6 -> 8 ReLU -> 1 sigmoid; nonnegative connection weights, signed biases",
            "parameter_count": PARAMETER_COUNT, "features": list(FEATURES),
            "feature_domain": "Dimensionless synthetic risk values [0,1]; no calibrated real-world units",
            "teacher": "3.1*x0+2.3*x1+x2+0.8*x3+0.55*x4+0.9*x5+2.5*relu(x0+x1-0.95)-4.1 >= 0",
            "implementation_sha256": hashlib.sha256((ROOT / "policy.py").read_bytes()).hexdigest(),
            "training": details, "dataset": dataset_manifest(splits),
            "parameters": model.parameters, "parameters_sha256": canonical_hash(model.parameters),
        }
        write_json(args.output, artifact)
        results = evaluate(model, splits, details["threshold"])
        results["measurement"] = {"training_seconds": elapsed, "python": platform.python_version(),
                                  "platform": platform.platform(), "backend": "standard-library Python CPU"}
        write_json(args.output.with_name(args.output.stem + "-results.json"), results)
        print(json.dumps({"artifact": str(args.output), "training_seconds": elapsed,
                          "holdout": results["holdout"], "monotonicity": results["monotonicity"]}, indent=2))
        return
    artifact, model = load_artifact(args.model)
    if args.command == "evaluate":
        config = artifact["training"]
        splits = generate_data(config["seed"], config["per_family"])
        if dataset_manifest(splits) != artifact["dataset"]:
            raise ValueError("Dataset manifest differs from saved experiment")
        results = evaluate(model, splits, config["threshold"])
        timings = []
        for row in splits["holdout"][:100]:
            started = time.perf_counter_ns()
            model.probability(row.features)
            timings.append((time.perf_counter_ns() - started) / 1e6)
        timings.sort()
        results["local_cpu_microbenchmark"] = {
            "count": len(timings), "p50_ms": statistics.median(timings),
            "p95_ms": timings[int(0.95 * (len(timings) - 1))],
            "scope": "Warm Python forward pass, validation included; not phone/NPU/end-to-end latency",
            "python": platform.python_version(), "platform": platform.platform()}
        if args.output:
            write_json(args.output, results)
        print(json.dumps(results, indent=2))
        return
    features = [float(value) for value in args.features.split(",")]
    report = model.inspect(features)
    report["external_policy"] = policy_decision(
        model, features, artifact["training"]["threshold"], paused=args.paused,
        permission_granted=not args.permission_denied, cooldown=args.cooldown)
    if args.intervene:
        name, value = args.intervene.split("=", 1)
        if name not in FEATURES:
            raise ValueError(f"Unknown feature {name}")
        changed = features[:]
        changed[FEATURES.index(name)] = float(value)
        report["counterfactual"] = {
            "intervention": args.intervene, "before": report["probability"],
            "after": model.probability(changed),
            "policy_after": policy_decision(model, changed, artifact["training"]["threshold"],
                paused=args.paused, permission_granted=not args.permission_denied, cooldown=args.cooldown)}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
