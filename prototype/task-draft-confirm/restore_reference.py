"""Recover immutable ignored source/input/prompt snapshots; performs no inference."""
import base64
import json
from pathlib import Path
import subprocess

import run_research as research


def checked_write(path, data, expected):
    path = Path(path)
    if path.exists() and path.read_bytes() != data:
        raise ValueError("Existing snapshot differs; refusing overwrite: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if research.sha(path) != expected:
        raise ValueError("Recovered snapshot checksum mismatch: " + str(path))


def main():
    frozen = json.loads((research.HERE / "freeze-manifest.json").read_text())
    for name, expected in frozen["sources_sha256"].items():
        if research.sha(research.HERE / name) != expected:
            raise ValueError("Original capture source changed")
    for name, expected in frozen["java_snapshots_sha256"].items():
        original = research.HERE / "reference" / name
        if research.sha(original) != expected:
            raise ValueError("Public reference archive changed")
        checked_write(research.BUILD / "source" / name, original.read_bytes(), expected)
    rows = research.cases()
    data = (json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    checked_write(research.BUILD / "cases.json", data, frozen["cases_sha256"])
    data = "".join(row["id"] + "\t" + research.encoded(row["goal"]) + "\n" for row in rows).encode()
    checked_write(research.BUILD / "input.tsv", data, frozen["input_sha256"])
    (research.BUILD / "java").mkdir(exist_ok=True)
    subprocess.run([str(research.JAVA / "javac"), "-d", str(research.BUILD / "java"),
                    *map(str, (research.BUILD / "source").glob("*.java")),
                    str(research.HERE / "TaskDraftEval.java")], check=True)
    inventory = research.java("inventory", research.BUILD / "input.tsv", capture_output=True,
                              text=True, timeout=30).stdout
    for line in inventory.splitlines():
        identifier, encoded = line.split("\t", 1)
        data = base64.b64decode(encoded)
        if identifier == "GRAMMAR":
            checked_write(research.BUILD / "grammar.gbnf", data, frozen["grammar_sha256"])
        else:
            checked_write(research.BUILD / (identifier + ".prompt.txt"), data,
                          frozen["prompt_sha256_by_id"][identifier])
    print(json.dumps({"recovered_original_snapshots": True, "generation": False,
                      "mutable_app_sources_used": False, "model_loaded": False}))


if __name__ == "__main__":
    main()
