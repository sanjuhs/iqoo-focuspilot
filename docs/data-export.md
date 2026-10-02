# Private summary export

The user explicitly chooses **Export private summary** and a destination with Android Storage Access Framework (`ACTION_CREATE_DOCUMENT`, MIME `application/json`). The app assembles and validates a bounded snapshot before opening the picker. Cancellation or an expired pending payload writes nothing; the caller writes only the returned content URI, without retaining a persistent URI grant. A provider write failure can leave a partial destination file, so the UI must report failure and advise deleting that file. No GitHub upload, background export, network request or automatic cloud send is implemented by the renderer.

A destination provider can be local storage or a cloud-synced provider chosen by the user. The export is ordinary unencrypted JSON, and selected app identity, timestamps, feature vectors and a goal hash can reveal habits. A hash is not anonymization: short or predictable goals can be guessed. The UI therefore describes the contents and provider-sync possibility before the picker. Delete exported copies from the selected provider separately; clearing app data does not delete those copies.

## Schema and strict boundary

`FocusDataExport` is pure Java with immutable input DTOs and UTF-8 JSON rendering. It has no Android, repository, file, network or `JSONObject` dependency. There are no arbitrary additional fields or raw-text input fields.

- Schema `1`, kind `focuspilot-private-summary`, explicit `research_only: true` and `money_moved: false`.
- One current `selected_package`; current declared budget, continuous limit, planned focus duration, goal SHA-256 only, observation/live-matching enabled flags.
- Virtual points `0..100`, active-focus flag and nonnegative focus elapsed milliseconds.
- Zero to **32** live records: ID, `ALLOW`/`NUDGE` label, six finite features in `0..1`, fixed `REAL_OBSERVATION` provenance, fixed `selected-events-v1` mapping, own numeric settings/goal-hash context, observation wall/elapsed and labeling elapsed timestamps.
- Other app records are rejected even when their context otherwise validates. The caller filters records to the currently selected package before constructing the snapshot. Older goal/limit contexts for that same app retain their own hashes and declared limits.
- Raw goal, event trail, UI text, other app identities, credentials, images/screens, activations/tensors and model weights have no fields in the schema.
- More than 32 records, duplicates, invalid package/hash/settings, missing values, nonfinite vectors, future observation timestamps, incomplete record limits, invalid provenance or labeling more than 15 seconds after observation are rejected. No truncation or partial JSON is returned.
- JSON output is capped at **80,000 UTF-8 bytes**. Integers are nonnegative and capped at JavaScript's exact-integer maximum where applicable; app budget/limit/virtual-point bounds are stricter. JSON escaping covers quotes, backslashes, all control characters and Unicode; unpaired surrogates are rejected.

`REAL_OBSERVATION` records are supplied by the caller's private live-label store. The renderer cannot independently attest to Android usage-event accuracy, user consent, device identity or the original labeling act. Its provenance check prevents exporting differently marked records, not falsification by an arbitrary caller. This summary is not a reproducible raw-events archive or a model-training dataset containing personal UI content.

## Caller API

```java
FocusDataExport.Settings settings = new FocusDataExport.Settings(
    selectedPackage, budgetMs, continuousLimitMs, plannedFocusMs,
    goalSHA256, observationEnabled, liveMatchingEnabled);
FocusDataExport.Record record = new FocusDataExport.Record(
    id, recordSettingsContext, features, FocusDataExport.Label.ALLOW,
    observedWallMs, observedElapsedMs, labeledElapsedMs, "REAL_OBSERVATION");
FocusDataExport.Snapshot snapshot = new FocusDataExport.Snapshot(
    exportedWallMs, settings, virtualPoints, focusElapsedMs, focusActive, records);
byte[] payload = FocusDataExport.render(snapshot);
```

Hash the goal through the existing scope API before constructing `Settings`; never pass the raw goal into this exporter. Build the snapshot on the repository owner thread to capture a consistent instant. Capture the resulting payload before presenting the picker, clear it on cancellation/result handling or expiration, and write that same immutable payload only after the user selects a destination. An inactive/unknown current limit may be zero, but exported live records require their original complete positive limits.

The parent integration supplies the explicit picker flow and selected-package filtering in `MainActivity`. Physical picker save/cancel, provider failure, external-file parsing and deletion have **not been verified** by this renderer task. Required device checks: cancel produces no file; save produces parseable JSON <=80 KB with only the documented keys; wrong/expired callback writes nothing; failing provider reports possible partial file; app deletion leaves explicit notice that exported copies remain. Use synthetic goals and selected-app usage for a shareable test, and keep actual private exports outside Git and public release assets.

## Verification

Twelve standalone JVM tests cover raw-goal/package injection rejection, cross-app leakage, JSON escaping, surrogate rejection, nonfinite vectors, strict record/byte limits, defensive copies, duplicate IDs, provenance, freshness/timestamps, declared settings and virtual balance bounds. A separate Python JSON parse of a synthetic exported fixture validates syntax and the exact allowed top-level/context/record key sets. These checks establish renderer behavior; they do not establish physical save/provider behavior or consent.
