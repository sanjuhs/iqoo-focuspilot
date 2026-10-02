# Private phone export → laptop shadow review

This is an implemented local laptop-compute consumer for the app's explicit private export, **not an implemented or verified Office Kit integration**. The bridge can be prepared and tested without an iQOO phone, enabling services, signing in, fetching a SDK or downloading another model. It never executes a phone action or sends results back into the app.

## What is implemented

`prototype/bridge/review_export.py` reads exactly one operator-selected input file, validates the complete private export schema, then reuses the existing `prototype/policy/policy.py` implementation and `synthetic-model.json` checkpoint. It verifies their pinned byte identities before importing the implementation, checks the checkpoint parameter checksum/feature order, and performs only forward inference on standard-library Python CPU. No training or parameter update occurs. A changed implementation/checkpoint requires a deliberate compatibility review; it is not silently accepted.

Input is limited to 80,000 bytes before JSON decoding and reading is bounded again to handle file growth. UTF-8 is strict. Unknown or missing fields, duplicate JSON keys, `NaN`/infinite constants, boolean numeric values, unsafe integers, invalid current package/settings/hash, invalid flags, more than 32 records, duplicate IDs, wrong provenance/mapping, invalid observation/label times, and non-six/nonfinite/out-of-range vectors are rejected. The top-level current limits may be zero when unknown; recorded live contexts must retain their original complete positive limits. No UI text or arbitrary extra fields are accepted.

Records are grouped by **exact original mapping, budget, continuous limit, planned focus duration and goal hash**. A context change therefore cannot merge unrelated preference labels. The groups receive local opaque indices; context hashes/settings are not output. For each group, the report includes count, minimum/maximum/mean model score, number of shadow threshold crossings, manual Nudge-label count and label-agreement count. The original package, goal hash, timestamps, feature vectors, session duration, virtual points, raw text and file path are omitted. The report also contains the input SHA-256 and pinned policy source/checkpoint hashes, explicit CPU attribution and false flags for phone actions, Office Kit verification and NPU verification.

These aggregate scores remain private. Opaque indices and a content hash do not anonymize a person, and an input hash can link identical copies. The learned head was trained on invented synthetic labels; its output is not calibrated human risk or confidence. Comparing replay scores to saved labels is **in-sample descriptive agreement**, not held-out productivity accuracy. Permission, focus, cooldown and human action-review gates are not replayed or bypassed by this consumer. `REAL_OBSERVATION` is an input declaration, not independently attested usage-event truth.

## Explicit local use

```sh
python3 -m unittest discover -s prototype/bridge -p 'test_*.py' -v
python3 prototype/bridge/review_export.py --input /path/you/chose/focuspilot-summary.json
```

By default, aggregate JSON is printed to the terminal. To verify a previously recorded source-payload checksum and save a new local report:

```sh
python3 prototype/bridge/review_export.py \
  --input /path/you/chose/focuspilot-summary.json \
  --expected-sha256 SOURCE_PAYLOAD_SHA256 \
  --output artifacts/local-shadow-review.json
```

Replace the source-checksum placeholder with an independently recorded lowercase SHA-256; omitting this argument produces an observed received-file hash, **not transfer parity**. There is no input auto-discovery. Input can be outside the project because the operator selects that exact file. Output requires an explicit new path under this project's Git-ignored `artifacts/`; its parent must already exist, tracked/unignored paths and symlink escapes are rejected, and existing files are never overwritten. Failed CLI runs produce a generic error without echoing private paths, values or provider messages. No output file is created when validation or policy identity checks fail.

Keep private exports and reports outside Git and public release assets. The renderer/exporter's document picker can target a cloud-synced provider selected by the user; neither the app renderer nor this consumer can certify the provider's transport or encryption. App data deletion does not delete exported copies. The report contains sensitive aggregates even though raw fields are omitted.

## Future real Office Kit workflow

The current [official India iQOO 15 page](https://www.iqoo.com/in/products/iqoo15) describes Office Kit connection to Windows/Mac, cross-device transfer through an iQOO account even across different networks, **desktop V6.0.0 or newer** and **OriginOS 6.0 or newer**. Mirrored drag-and-drop uses vivo's native Albums/File Manager apps. This is stronger current India guidance than the older same-network connection lead. Installation/login remains an operator action through the [official desktop site](https://pc.vivoglobal.com/); actual firmware/region availability must be checked on the device. No public programmable Office Kit API is assumed.

1. On the actual eligible iQOO, use only a synthetic goal and selected-app test workflow. Explicitly export the bounded summary to a chosen local destination. Record the exact source-payload hash before transfer, using a reviewed app/phone checksum procedure; the laptop's received-file hash alone cannot establish this.
2. Manually pair actual Office Kit using the installed current build's prompts, with account details masked. Unplug ADB for this demonstration; do not call an ADB copy an Office Kit transfer. Verify whether the chosen path uses local transfer or a network/cloud service instead of claiming offline transport.
3. Use the native File Manager and actual Office Kit to hand off that test summary to the laptop. Record source/received byte identities and a consented synthetic-screen pairing/transfer observation. Generic drag-and-drop or a renamed local file is insufficient transport evidence.
4. Run the explicit laptop consumer with the independently recorded source hash. Review its grouped CPU result and preserve input identity, policy identity and report hash. This demonstrates useful laptop computation while all phone actions remain disabled.
5. Repeat reconnect/cancel and a modified-file counterexample; the checksum mismatch must reject the altered file. Delete test export/report copies from both selected destinations after review.

Actual Office Kit installation, pairing and transfer have **not been performed** by this task. The implemented consumer closes the laptop-compute portion of the workflow, leaving transport/account/device evidence explicit. It does not complete iQOO deployment, prove Snapdragon NPU execution or certify hackathon eligibility.

## Verification

Fifteen tests use only generated synthetic fixtures in temporary directories. They cover pinned policy replay, exact context grouping, omitted private fields, unknown/duplicate keys, UTF-8 and pre-parse size limits, nonfinite and boolean numbers, safe-integer bounds, 32-record/duplicate-ID limits, provenance/settings/freshness checks, content tampering, empty exports, changed-policy rejection, ignored-output containment/no overwrite/symlink escape, and CLI error privacy. The CLI is additionally exercised end-to-end on a generated synthetic export. No real private export is read by the test suite.

The actual Java `FocusDataExport` renderer was also compiled and its 1,615-byte,
three-record synthetic fixture consumed by the Python CLI with checksum parity.
[Recorded interoperability](bridge-java-interop.json) binds the Java source and
payload hashes. The fixture's provenance flag is invented test data; this is
format compatibility, not an actual phone export or transfer. Reproduce with:

```sh
python3 scripts/verify_bridge_java_interop.py --output artifacts/bridge-interop-repeat.json
```
