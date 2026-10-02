"""One frozen host-only draft-guidance capture; no tools, UI or actions."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time

from generate_data import cases

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = HERE / "build"
JAVA = Path("/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin")
MODEL = ROOT / "models/qwen/Qwen3.5-0.8B-Q4_0.gguf"
MODEL_SHA = "57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf"
NATIVE = ROOT / "prototype/command-eval/build/native/libfocuspilot_local.dylib"
NATIVE_SHA = "ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e"
APP = ROOT / "prototype/android/app/src/main/java/dev/focuspilot/prototype"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def encoded(text):
    return base64.b64encode(text.encode()).decode()


def java(mode, path, **options):
    args = [str(JAVA / "java"), "-Djava.library.path=" + str(NATIVE.parent),
            "-cp", str(BUILD / "java"), "dev.focuspilot.prototype.TaskDraftEval", mode]
    if mode == "capture":
        args += [str(MODEL)]
    return subprocess.run(args + [str(path)], check=True, **options)


def freeze(contract_sha):
    if (HERE / "freeze-manifest.json").exists():
        raise ValueError("Already frozen")
    if sha(APP / "TaskDraft.java") != contract_sha:
        raise ValueError("Shared TaskDraft differs from agreed contract")
    if sha(MODEL) != MODEL_SHA or sha(NATIVE) != NATIVE_SHA:
        raise ValueError("Existing model/runtime digest mismatch")
    BUILD.mkdir(exist_ok=True)
    source = BUILD / "source"
    source.mkdir(exist_ok=True)
    snapshots = {}
    for name in ("LocalModel.java", "TaskDraft.java", "TaskPlan.java"):
        shutil.copyfile(APP / name, source / name)
        snapshots[name] = sha(source / name)
    (BUILD / "java").mkdir(exist_ok=True)
    subprocess.run([str(JAVA / "javac"), "-d", str(BUILD / "java"),
                    *map(str, source.glob("*.java")), str(HERE / "TaskDraftEval.java")], check=True)
    rows = cases()
    write(BUILD / "cases.json", rows)
    (BUILD / "input.tsv").write_text("".join(r["id"] + "\t" + encoded(r["goal"]) + "\n" for r in rows))
    inventory = java("inventory", BUILD / "input.tsv", capture_output=True, text=True, timeout=30).stdout
    (BUILD / "inventory.tsv").write_text(inventory)
    prompt_hashes = {}
    for line in inventory.splitlines():
        identifier, value = line.split("\t", 1)
        text = base64.b64decode(value).decode()
        if identifier == "GRAMMAR":
            (BUILD / "grammar.gbnf").write_text(text)
        else:
            file = BUILD / (identifier + ".prompt.txt")
            file.write_text(text)
            prompt_hashes[identifier] = sha(file)
    if set(prompt_hashes) != {r["id"] for r in rows}:
        raise ValueError("Actual rendered prompt inventory incomplete")
    protocol = {"origin": "Pre-event local research, not eligible event-created code",
                "counts": {"benign": 8, "tricky": 4, "total": 12},
                "selection": "One agreed fixed shared prompt/grammar, no candidate selection or post-output repair",
                "sampling": "Greedy, fresh recurrent/KV state, CPU1024 context4 threads, no thinking, max128, capturefalse",
                "qualitative_criteria": "Each frozen fixture specifies goal-relevant steps and constraints. Author reviews after capture; subjective feasibility evidence, no fabricated automated accuracy.",
                "completed_schema": "Requires actual EOS plus strict shared parser for exactly3 nonduplicate steps; exact empty array is explicit decline, not a usable plan",
                "deadlines": "20-second nativeCancel per request; 300-second overall subprocess deadline",
                "limits": "Synthetic cases, informed author; no real accounts, actions, phone/voice/NPU, safety guarantee, neural necessity or automatic promotion"}
    write(HERE / "protocol.json", protocol)
    write(HERE / "freeze-manifest.json", {
        "frozen_utc": datetime.now(timezone.utc).isoformat(), "frozen_before_any_model_run": True,
        "model_sha256": MODEL_SHA, "native_sha256": NATIVE_SHA,
        "model_revision": "ggml-org/Qwen3.5-0.8B-GGUF@8fea620810c4afa23dd6443f999a48574c1611a3",
        "model_license": "Apache-2.0", "native_llama_commit": "57fe1f07c3b6a1de3f4fff19098e2056a85275b7",
        "java_snapshots_sha256": snapshots, "prompt_sha256_by_id": prompt_hashes,
        "grammar_sha256": sha(BUILD / "grammar.gbnf"),
        "cases_sha256": sha(BUILD / "cases.json"), "input_sha256": sha(BUILD / "input.tsv"),
        "protocol_sha256": sha(HERE / "protocol.json"),
        "sources_sha256": {name: sha(HERE / name) for name in ("generate_data.py", "run_research.py", "TaskDraftEval.java", "test_research.py")}})
    print(json.dumps({"frozen": True, "manifest_sha256": sha(HERE / "freeze-manifest.json"), "counts": protocol["counts"]}))


def verify_freeze():
    frozen = json.loads((HERE / "freeze-manifest.json").read_text())
    checks = {HERE / "protocol.json": frozen["protocol_sha256"], BUILD / "cases.json": frozen["cases_sha256"],
              BUILD / "input.tsv": frozen["input_sha256"], BUILD / "grammar.gbnf": frozen["grammar_sha256"],
              MODEL: frozen["model_sha256"], NATIVE: frozen["native_sha256"]}
    checks.update({HERE / name: value for name, value in frozen["sources_sha256"].items()})
    checks.update({BUILD / "source" / name: value for name, value in frozen["java_snapshots_sha256"].items()})
    checks.update({BUILD / (name + ".prompt.txt"): value for name, value in frozen["prompt_sha256_by_id"].items()})
    for path, expected in checks.items():
        if sha(path) != expected:
            raise ValueError("Frozen bytes changed: " + str(path))
    return frozen


def capture():
    verify_freeze()
    if (BUILD / "process-result.json").exists() or (BUILD / "output.tsv").exists():
        raise ValueError("Capture already attempted; do not silently rerun")
    start = time.perf_counter()
    with (BUILD / "output.tsv").open("w") as output, (BUILD / "stderr.log").open("w") as errors:
        command = [str(JAVA / "java"), "-Djava.library.path=" + str(NATIVE.parent),
                   "-cp", str(BUILD / "java"), "dev.focuspilot.prototype.TaskDraftEval",
                   "capture", str(MODEL), str(BUILD / "input.tsv")]
        process = subprocess.Popen(command, stdout=output, stderr=errors)
        write(BUILD / "live-process.json", {"pid": process.pid, "started_utc": datetime.now(timezone.utc).isoformat()})
        print("PHASE live JNI capture pid=" + str(process.pid), flush=True)
        timed_out = False
        try:
            code = process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            code = process.wait()
    status = {"exit_code": code, "timed_out": timed_out, "wall_seconds": time.perf_counter() - start,
              "output_sha256": sha(BUILD / "output.tsv"), "stderr_sha256": sha(BUILD / "stderr.log")}
    write(BUILD / "process-result.json", status)
    print(json.dumps(status))


def summarize():
    frozen = verify_freeze()
    rows = json.loads((BUILD / "cases.json").read_text())
    process = json.loads((BUILD / "process-result.json").read_text())
    if sha(BUILD / "output.tsv") != process["output_sha256"]:
        raise ValueError("Capture bytes changed")
    outputs = {}
    load_ns = None
    for line in (BUILD / "output.tsv").read_text().splitlines():
        fields = line.split("\t")
        if fields[0] == "LOAD":
            load_ns = int(fields[1]); continue
        identifier, elapsed, status, data = fields
        outputs[identifier] = {"elapsed_ms": int(elapsed) / 1e6, "status": status,
                               "raw": base64.b64decode(data).decode()}
    parser_input = []
    for identifier, value in outputs.items():
        if value["status"] == "OK":
            outer = json.loads(value["raw"])
            value["outer"] = outer
            parser_input.append(identifier + "\t" + encoded(outer["text"]) + "\n")
    (BUILD / "parser-input.tsv").write_text("".join(parser_input))
    verdicts = java("validate", BUILD / "parser-input.tsv", capture_output=True, text=True, timeout=30).stdout
    parsed = dict(line.split("\t") for line in verdicts.splitlines())
    write(BUILD / "captured-details.json", outputs)
    completed = [value for identifier, value in outputs.items()
                 if value["status"] == "OK" and value["outer"]["metrics"]["reached_eos"]
                 and parsed[identifier] in ("PLAN_3", "DECLINE")]
    plans = [identifier for identifier in parsed if parsed[identifier] == "PLAN_3"
             and outputs[identifier]["outer"]["metrics"]["reached_eos"]]
    declines = [identifier for identifier in parsed if parsed[identifier] == "DECLINE"
                and outputs[identifier]["outer"]["metrics"]["reached_eos"]]
    metrics = [value["outer"]["metrics"] for value in outputs.values() if value["status"] == "OK"]
    def median(key, items=metrics):
        return statistics.median(m[key] for m in items) if items else None
    def extreme(key, operation):
        return operation(m[key] for m in metrics) if metrics else None
    aggregate = {"origin": "Pre-event host CPU draft feasibility research; no actions", "counts": {"expected": len(rows),
                 "captured": len(outputs), "completed_eos_and_schema": len(completed), "usable_shape_three_steps": len(plans),
                 "explicit_declines": len(declines), "invalid_or_incomplete": len(rows) - len(completed)},
                 "process": process, "model_load_ms": load_ns / 1e6 if load_ns else None,
                 "timing": {"native_total_median_ms": median("total_ms"),
                            "first_native_total_ms": metrics[0]["total_ms"] if metrics else None,
                            "warm_native_total_median_ms": median("total_ms", metrics[1:]),
                            "prompt_tokens_min": extreme("prompt_tokens", min),
                            "prompt_tokens_max": extreme("prompt_tokens", max),
                            "generated_tokens_min": extreme("generated_tokens", min),
                            "generated_tokens_max": extreme("generated_tokens", max)},
                 "capture_enabled_all_false": all(not m["capture_enabled"] for m in metrics),
                 "cpu_only_all_true": all(m["cpu_only"] for m in metrics),
                 "activations_all_empty": all(not value["outer"]["activations"] for value in outputs.values() if value["status"] == "OK"),
                 "freeze_sha256": sha(HERE / "freeze-manifest.json"), "model_sha256": frozen["model_sha256"],
                 "native_sha256": frozen["native_sha256"], "case_details_sha256": sha(BUILD / "captured-details.json"),
                 "qualitative": "Pending author review against prewritten fixture criteria; shape/EOS alone do not establish usefulness",
                 "limits": "Single greedy capture, tiny synthetic set, informed subjective review, host CPU only, no safety/generalization/phone proof"}
    write(HERE / "results.json", aggregate)
    print(json.dumps(aggregate, sort_keys=True))


def review():
    """Bind an explicit author review to existing capture; never refit or regenerate."""
    verify_freeze()
    review_path = BUILD / "qualitative-review.json"
    records = json.loads(review_path.read_text())
    rows = json.loads((BUILD / "cases.json").read_text())
    outputs = json.loads((BUILD / "captured-details.json").read_text())
    result = json.loads((HERE / "results.json").read_text())
    if sha(BUILD / "captured-details.json") != result["case_details_sha256"]:
        raise ValueError("Captured details changed before review")
    indexed = {record["id"]: record for record in records}
    if len(indexed) != len(records) or set(indexed) != {row["id"] for row in rows}:
        raise ValueError("Review must cover every frozen case exactly once")
    for record in records:
        for name in ("criterion_met", "goal_relevant", "respects_constraints", "invented_access_or_completion"):
            if type(record.get(name)) is not bool:
                raise ValueError("Qualitative judgment must be an explicit boolean")
        if not isinstance(record.get("reason"), str) or not record["reason"].strip():
            raise ValueError("Each qualitative judgment needs a written reason")
    for row in rows:
        record = indexed[row["id"]]
        captured = outputs.get(row["id"])
        if record["criterion_met"]:
            if not captured or captured["status"] != "OK" or not captured["outer"]["metrics"]["reached_eos"]:
                raise ValueError("A criterion cannot pass on failed/incomplete generation")
            plan = json.loads(captured["outer"]["text"])
            if row["expected"] == "decline" and plan != {"steps": []}:
                raise ValueError("Frozen explicit-decline criterion requires empty array")
            if row["expected"] in ("three_relevant_steps", "respect_negation") and len(plan.get("steps", [])) != 3:
                raise ValueError("Frozen three-step criterion requires exactly three")
    benign = [row for row in rows if row["kind"] == "benign"]
    tricky = [row for row in rows if row["kind"] == "tricky"]
    aggregate = {"reviewer": "Author, informed subjective qualitative review against prewritten fixture criteria; no independent rater",
                 "captured_results_sha256": sha(HERE / "results.json"), "review_sha256": sha(review_path),
                 "reviewed_utc": datetime.now(timezone.utc).isoformat(), "cases_reviewed": len(records),
                 "benign_goal_relevant": sum(indexed[row["id"]]["goal_relevant"] for row in benign),
                 "benign_criterion_met": sum(indexed[row["id"]]["criterion_met"] for row in benign),
                 "tricky_criterion_met": sum(indexed[row["id"]]["criterion_met"] for row in tricky),
                 "constraint_violations": sum(not record["respects_constraints"] for record in records),
                 "invented_access_or_completion": sum(record["invented_access_or_completion"] for record in records),
                 "criterion_failures": sum(not record["criterion_met"] for record in records),
                 "scope": "Qualitative usefulness on 12 synthetic goals, not validated accuracy or safety/generalization/phone evidence",
                 "actions_executed": 0}
    write(HERE / "qualitative-results.json", aggregate)
    print(json.dumps(aggregate, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "capture", "summarize", "review", "verify"))
    parser.add_argument("--contract-sha")
    options = parser.parse_args()
    if options.mode == "freeze":
        if not options.contract_sha:
            parser.error("freeze requires --contract-sha of agreed shared TaskDraft.java")
        freeze(options.contract_sha)
    else:
        {"capture": capture, "summarize": summarize, "review": review,
         "verify": lambda: print(json.dumps({"verified": True, "freeze": verify_freeze()}))}[options.mode]()
