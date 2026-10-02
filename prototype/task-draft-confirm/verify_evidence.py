"""Read-only final public evidence/archives verification; no model load or inference."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = json.loads((HERE / "evidence-manifest.json").read_text())
    for relative, expected in manifest["public_files_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError("Public evidence changed: " + relative)
    checks = {}
    for name in ("task-draft-research", "task-draft-confirm"):
        directory = ROOT / "prototype" / name
        frozen = json.loads((directory / "freeze-manifest.json").read_text())
        results = json.loads((directory / "results.json").read_text())
        review = json.loads((directory / "qualitative-results.json").read_text())
        if review["captured_results_sha256"] != sha(directory / "results.json"):
            raise ValueError("Review/capture binding changed")
        for filename, expected in frozen["java_snapshots_sha256"].items():
            if sha(directory / "reference" / filename) != expected:
                raise ValueError("Archived shared contract changed")
        for filename, expected in frozen["sources_sha256"].items():
            if sha(directory / filename) != expected:
                raise ValueError("Capture source changed")
        raw = directory / "build/output.tsv"
        raw_present = raw.exists()
        if raw_present and sha(raw) != results["process"]["output_sha256"]:
            raise ValueError("Raw capture changed")
        checks[name] = {"archived_sources_verified": True, "results_review_binding_verified": True,
                        "raw_capture_present_and_checked": raw_present}
    print(json.dumps({"verified": True, "checks": checks, "model_loaded": False,
                      "inference": False, "mutable_app_sources_used": False}, sort_keys=True))


if __name__ == "__main__":
    main()
