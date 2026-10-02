"""Actual CPU activation writes on a fixed Qwen artifact; narrow pre-event lab."""
from pathlib import Path
import hashlib
import json
import math
import random
import statistics
import subprocess
import time

LAB = Path(__file__).resolve().parent
PROJECT = LAB.parents[1]
MODEL = PROJECT / "models/qwen/Qwen3.5-0.8B-Q4_0.gguf"
EXPECTED_HASH = "57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf"
SEED = 20261002
NODES = ["ffn_out-0", "ffn_out-11", "ffn_out-23"]
PAIRS = {
    "discovery": [
        ("direct", "Start focus.", "Stop focus."),
        ("work_session", "Begin a work session.", "End my work session."),
        ("mode", "Switch focus mode on.", "Switch focus mode off."),
        ("timed", "Start a twenty-minute focus session.", "Stop my twenty-minute focus session."),
    ],
    "selection": [
        ("in_out", "Put me into focus mode.", "Take me out of focus mode."),
        ("concentration", "Begin a concentration session.", "Pause my concentration session."),
    ],
    "holdout": [
        ("work_block", "Let's begin a block of focused work.", "Let's finish this block of focused work."),
        ("resume_suspend", "Resume my focus session now.", "Suspend my focus session now."),
        ("activate", "Activate focus while I work.", "Deactivate focus while I work."),
        ("enter_leave", "Please help me enter focus mode.", "Please help me leave focus mode."),
    ],
}
CONTROLS = [
    ("alarm", "Set an alarm for seven thirty in the morning.", "alarm"),
    ("timer", "Start a ten-minute countdown timer.", "timer"),
    ("calculator", "Open calculator.", "open_app"),
    ("negation", "Do not start a focus session.", "unknown"),
]


def write(name, value):
    (LAB / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def strip_vectors(value):
    return {k: v for k, v in value.items() if k != "captures"}


class Probe:
    def __init__(self):
        self.log = (LAB / "build/probe.log").open("w")
        self.process = subprocess.Popen([str(LAB / "build/intervention_probe"), str(MODEL)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log, text=True, bufsize=1)
        self.calls = 0

    def call(self, command, mode="capture", node="all", channels=(), patches=()):
        if any(c in command for c in "\t\n\r"):
            raise ValueError("Single-line synthetic command required")
        self.process.stdin.write("\t".join([mode, node, ",".join(map(str, channels)) or "-",
            ",".join(map(str, patches)) or "-", command]) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Probe exited; inspect build/probe.log")
        row = json.loads(line)
        if not row["write_verified"] or (mode != "capture" and row["writes"] == 0):
            raise RuntimeError("Requested tensor mutation was not verified")
        self.calls += 1
        return row

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=30)
        self.log.close()
        if self.process.returncode:
            raise RuntimeError("Native probe exited with failure")


def directional_shift(baseline, changed, target):
    delta = changed["margin_start_minus_pause"] - baseline["margin_start_minus_pause"]
    return -delta if target == "start_focus" else delta


def main():
    started = time.perf_counter()
    if hashlib.file_digest(MODEL.open("rb"), "sha256").hexdigest() != EXPECTED_HASH:
        raise RuntimeError("GGUF checksum mismatch")
    subprocess.run(["sh", str(LAB / "build.sh")], check=True)
    examples = []
    for split, pairs in PAIRS.items():
        for family, start, pause in pairs:
            examples += [{"id": family + "_" + label, "split": split, "family": family,
                          "command": command, "target": label}
                         for label, command in [("start_focus", start), ("pause_focus", pause)]]
    examples += [{"id": family, "split": "unrelated_control", "family": family,
                  "command": command, "target": target} for family, command, target in CONTROLS]
    write("protocol.json", {
        "origin": "Pre-event laboratory, 2026-10-02", "seed": SEED, "examples": examples,
        "runtime_commit": "57fe1f07c3b6a1de3f4fff19098e2056a85275b7", "gguf_sha256": EXPECTED_HASH,
        "context": 512, "batch": 512, "ubatch": 512, "threads": 4,
        "cache_policy": "New llama_context for every case; no recurrent/KV memory reuse",
        "position": "Last token of forced assistant JSON prefix {\"intent\":\"; all prefill in one microbatch",
        "scoring": "Greedy argmax among seven unique first-label-token logits; not full generated JSON or calibrated command probability",
        "discovery_rule": "Rank channels by absolute start/pause mean difference divided by within-group standard deviation floor1e-3; top4 per layer",
        "selection_rule": "Among three frozen layer/channel bundles choose largest mean opposite-donor directional margin shift on selection only",
        "holdout_rule": "Freeze layer/channels before holdout interventions; no holdout-driven tuning",
        "controls": ["zero selected channels", "opposite-class patch", "same-class discovery patch", "random4-channel opposite patch",
                     "norm-matched random-channel patch", "identical-vector no-op write", "zero then restore before downstream compute",
                     "whole last-token ffn_out zeroing", "unrelated alarm/timer/open/negation cases"],
    })
    probe = Probe()
    try:
        baseline = {e["id"]: probe.call(e["command"]) for e in examples}
        write("baseline-captures.json", baseline)
        print("Baseline captured for 24 fixed commands.", flush=True)
        def opposite(e):
            label = "pause_focus" if e["target"] == "start_focus" else "start_focus"
            return baseline[e["family"] + "_" + label]
        bundles = []
        discovery = [e for e in examples if e["split"] == "discovery"]
        selection = [e for e in examples if e["split"] == "selection"]
        for node in NODES:
            scores = []
            starts = [baseline[e["id"]]["captures"][node] for e in discovery if e["target"] == "start_focus"]
            pauses = [baseline[e["id"]]["captures"][node] for e in discovery if e["target"] == "pause_focus"]
            for channel in range(1024):
                a, b = [v[channel] for v in starts], [v[channel] for v in pauses]
                difference = statistics.mean(a) - statistics.mean(b)
                variation = math.sqrt((statistics.pvariance(a) + statistics.pvariance(b)) / 2)
                scores.append({"channel": channel, "difference": difference,
                               "rank_score": abs(difference) / max(1e-3, variation)})
            chosen = sorted(scores, key=lambda r: (-r["rank_score"], r["channel"]))[:4]
            channels = [r["channel"] for r in chosen]
            cases = []
            for e in selection:
                donor = opposite(e)["captures"][node]
                changed = probe.call(e["command"], "patch", node, channels, [donor[i] for i in channels])
                cases.append({"id": e["id"], "target": e["target"],
                    "directional_shift": directional_shift(baseline[e["id"]], changed, e["target"]),
                    "changed": strip_vectors(changed)})
            bundles.append({"node": node, "channels": channels, "discovery_ranks": chosen,
                            "selection_mean_shift": statistics.mean(c["directional_shift"] for c in cases),
                            "selection_cases": cases})
        chosen = max(bundles, key=lambda b: b["selection_mean_shift"])
        node, channels = chosen["node"], chosen["channels"]
        random_channels = random.Random(SEED).sample([i for i in range(1024) if i not in channels], 4)
        write("frozen-selection.json", {"candidates": bundles, "chosen": chosen,
                                        "random_control_channels": random_channels,
                                        "selection_frozen_before_holdout": True})
        print("Frozen selection:", node, channels, flush=True)
        cases = []
        for e in examples:
            if e["split"] not in ("holdout", "unrelated_control"):
                continue
            base = baseline[e["id"]]
            modes = ["zero", "zero_layer"] if e["split"] == "unrelated_control" else [
                "opposite_patch", "zero", "random_patch", "matched_norm_random_patch", "same_class_patch", "noop", "restore", "zero_layer"]
            for mode in modes:
                indices, patches, native_mode = channels, [], mode
                norm = 0.0
                if mode.endswith("patch"):
                    recipient = base["captures"][node]
                    donor = (opposite(e) if mode != "same_class_patch" else baseline["direct_" + e["target"]])["captures"][node]
                    indices = random_channels if mode in ("random_patch", "matched_norm_random_patch") else channels
                    patches = [donor[i] for i in indices]
                    if mode == "matched_norm_random_patch":
                        intended = math.sqrt(sum((donor[i] - recipient[i]) ** 2 for i in channels))
                        actual = math.sqrt(sum((donor[i] - recipient[i]) ** 2 for i in indices))
                        patches = [recipient[i] + (donor[i] - recipient[i]) * intended / max(actual, 1e-12) for i in indices]
                    norm = math.sqrt(sum((v - recipient[i]) ** 2 for i, v in zip(indices, patches)))
                    native_mode = "patch"
                changed = probe.call(e["command"], native_mode, node, indices, patches)
                cases.append({"id": e["id"], "split": e["split"], "target": e["target"], "mode": mode,
                    "channels": list(indices), "patch_delta_l2": norm,
                    "baseline": strip_vectors(base), "changed": strip_vectors(changed),
                    "margin_delta": changed["margin_start_minus_pause"] - base["margin_start_minus_pause"],
                    "directional_shift": directional_shift(base, changed, e["target"]) if e["split"] == "holdout" else None,
                    "noop_full_logits_equal": changed["full_logits_byte_equal_to_baseline"] if mode in ("noop", "restore") else None})
        write("intervention-cases.json", cases)
        summaries = {}
        for mode in sorted({c["mode"] for c in cases if c["split"] == "holdout"}):
            rows = [c for c in cases if c["mode"] == mode and c["split"] == "holdout"]
            summaries[mode] = {"n": len(rows), "correct": sum(c["changed"]["intent"] == c["target"] for c in rows),
                "mean_directional_margin_shift": statistics.mean(c["directional_shift"] for c in rows),
                "predicted_direction_count": sum(c["directional_shift"] > 1e-5 for c in rows),
                "intent_changes": sum(c["changed"]["intent"] != c["baseline"]["intent"] for c in rows),
                "mean_patch_delta_l2": statistics.mean(c["patch_delta_l2"] for c in rows)}
        summary = {"status": "Actual CPU interventions; exploratory narrow command experiment, no universal semantic circuit claim",
            "baseline_correct": {s: {"n": len([e for e in examples if e["split"] == s]),
                "correct": sum(baseline[e["id"]]["intent"] == e["target"] for e in examples if e["split"] == s)}
                for s in PAIRS.keys() | {"unrelated_control"}},
            "frozen_node": node, "frozen_channels": channels, "random_channels": random_channels,
            "holdout": summaries,
            "noop_restore_full_logits_parity": all(c["noop_full_logits_equal"] for c in cases if c["mode"] in ("noop", "restore")),
            "unrelated_controls": [{"id": c["id"], "mode": c["mode"], "baseline_intent": c["baseline"]["intent"],
                                    "changed_intent": c["changed"]["intent"], "margin_delta": c["margin_delta"]}
                                   for c in cases if c["split"] == "unrelated_control"],
            "native_calls": probe.calls, "elapsed_seconds": time.perf_counter() - started,
            "probe_source_sha256": hashlib.sha256((LAB / "probe.cpp").read_bytes()).hexdigest(),
            "runner_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "model_sha256": EXPECTED_HASH,
            "limitations": ["10 hand-authored command pairs, only4 heldout pairs", "One seed and one random4-channel control bundle",
                "Forced common JSON prefix and first-token scoring, not the app's full grammar decoding",
                "All comparisons use same Q4_0 CPU artifact; no phone or NPU replication", "Selection considers only three layers and four channels per bundle",
                "No generic focus neuron or transformer-wide mechanistic understanding established"]}
        write("summary.json", summary)
        print(json.dumps(summary, indent=2), flush=True)
    finally:
        probe.close()


if __name__ == "__main__":
    main()
