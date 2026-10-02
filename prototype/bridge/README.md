# Offline laptop review bridge

Pre-event research. Reads one explicitly selected private Mira summary and runs the existing synthetic-trained 65-parameter policy on laptop CPU. No discovery, retraining, phone actions, return import, credentials or network operations. **Office Kit transport and NPU execution are unverified.**

```sh
python3 -m unittest discover -s prototype/bridge -p 'test_*.py' -v
python3 prototype/bridge/review_export.py --input /path/you/chose/focuspilot-summary.json
python3 prototype/bridge/review_export.py --input /path/you/chose/focuspilot-summary.json \
  --expected-sha256 SOURCE_PAYLOAD_SHA256 \
  --output artifacts/local-shadow-review.json
```

The input must be a <=80,000-byte UTF-8 schema1 export. Unknown/duplicate keys, nonfinite/boolean numerics, unsafe integers, more than32/duplicate IDs, bad timestamps, unknown provenance and non-six bounded feature vectors are rejected. Output is aggregates and payload/policy identity only, with no app identity, goal hash, timestamps, vectors or raw text. Aggregates remain private; they are not anonymous or calibrated productivity measurements.

The default output is stdout. Saving requires an explicit **new**, Git-ignored path inside this project's `artifacts/`; existing files, unignored files and escaping symlinks are rejected. Do not upload actual user exports/reports to GitHub releases. See [workflow and limits](../../docs/officekit-export-workflow.md).
