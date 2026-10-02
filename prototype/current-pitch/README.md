# Current research-pitch metrics

`metrics.json` is a public, source-bound input for the animated **v0.10 research
video**. It contains no real phone history, screen capture, credentials or private
export. Every group lists its source paths; `sources` maps each path to its exact
SHA-256 and the last commit containing that source file. A group's `source_commit`
attributes the app or experiment itself, which can differ from the later document
commit. `repository_snapshot_commit` records the read-only repository snapshot.

Use these distinctions in narration and captions:

- **Current app:** source `bcc24733655e4eced67d68ff5c47f7ab97d60b36`, v0.10,
  133 Android JVM tests and lint zero errors/62 warnings. Installation and APK/model
  byte identities are verified; this is not current physical command/voice proof.
  The recorded balance is **100 virtual points**, never money.
- **Current command evidence:** one unchanged old-prompt Qwen host CPU capture on
  100 fresh synthetic requests. Supported exact actions/slots improve **15→31/50**,
  with 16 gains/zero losses and all 50 unsupported requests rejected. Keep the
  **19 supported false abstentions** and raw model **36/100**, including **49/50
  unsupported tool proposals**, visible. The gate provides rejection. The same
  informed author generated the fresh set; it is not human/real-voice sampling.
- **Historical phone:** source `29c4c3372fcc913d3672e59803a3aa870fa2426b`, v0.6,
  typed and reviewed Nothing-phone Start/Pause/cancellation observations at
  17,323/1,814/1,655 ms. Start/Pause changed the private focus state; cancellation
  was misclassified then rejected. These three samples are not current v0.10,
  speech, disconnected execution, Clock outcome or latency-distribution evidence.
- **Tiny trained policy:** 65 learned parameters, 472/480 synthetic teacher-label
  holdout matches, with three false nudges and five misses. Nonnegative connection
  weights have signed biases. Its separate shadow/sandbox score does not control
  recurring nudges; the live rule remains hand-set. This is neither human
  productivity learning nor a fine-tuned or completely positive LLM.
- **Mechanistic research:** 108 actual laptop CPU intervention trials, eight heldout
  commands. Opposite patches and matched random controls both remain 6/8, with
  no heldout intent changes; broad layer zeroing falls to 5/8. No-op/restoration
  logit parity verifies machinery, while reliable semantic steering and complete
  model understanding are unestablished. It is not phone/NPU intervention evidence.
- **Laptop bridge:** 15 recorded synthetic tests and actual Java-renderer/Python
  CLI interoperability for three synthetic records in one context group. The
  temporary local-file transport is **not Office Kit** or an actual phone export.
  It replays the policy without training or phone actions.

The `pending` list preserves current physical-command/voice/observation/overlay,
fresh bundled import, disconnected execution, iQOO/NPU, Office Kit, real-user
calibration, general phone/IoT and eligibility/submission gaps. A research
animation explains the architecture and saved evidence; it is not a live feature
demonstration or an accepted hackathon submission.

No new inference, training, tests, downloads, phone operations or research-source
changes were performed to create this metrics file. Counts above come from saved
reports. Native host and packaged Android hashes are distinct and explicitly
labelled. The immutable confirmation's inherited two-load timing string has a
README erratum; the actual experiment has **one** shared capture.

Validate source identities from the repository root before rendering:

```sh
python3 - <<'PY'
import hashlib,json,pathlib
m=json.loads(pathlib.Path('prototype/current-pitch/metrics.json').read_text())
for name,identity in m['sources'].items():
    with pathlib.Path(name).open('rb') as stream:
        actual=hashlib.file_digest(stream,'sha256').hexdigest()
    assert actual==identity['sha256'], 'Source changed: '+name
assert m['commands']['baseline']==15 and m['commands']['selected']==31
assert m['commands']['supported_total']==50
assert m['historical_phone']['version'].startswith('0.6-')
assert m['current_app']['version']=='0.10'
assert m['current_app']['npu_verified'] is False
assert m['bridge']['officekit_transport_verified'] is False
print('Source-bound metrics verified; no model inference performed.')
PY
```

If any source changes, review its evidence and refresh the metrics deliberately
before recording; do not substitute a new build's results for historical samples.
