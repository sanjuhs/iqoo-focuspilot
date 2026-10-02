# Network-denied native inference — v0.13 research

On 3 October 2026, the pinned **Qwen3.5-0.8B Q4_0** completed ten synthetic
native CPU requests in the actual Nothing-phone app process after IPv4 TCP
socket creation failed with **EPERM**. The diagnostic passed 224 infrastructure
checks and restored the original test APK and protected production snapshots.
This establishes the measured inference path with denied socket creation;
the full disconnected assistant workflow remains unfinished.

[Public physical record](network-isolation-phone-v013.json) and
[artifact identities](network-isolation-artifacts.json) bind the result to
diagnostic source `aff6fb940fb76f64f77aca8d4c0ff33164a7de43`. The installed
user-facing APK remains the v0.13 app from
`1eed4348d3d0233d786bcd3b86c05d225ebf8db6`. Its model, prompt, command gate,
native runtime and companion artwork are unchanged. This is pre-event research,
not evidence of eligible event-written competition code.

## What actually ran

The separate instrumentation APK injected diagnostic code into the target main
process, `dev.focuspilot.prototype`. Actual process UID 10425 matched the target
application UID; the test package had a different UID. Both installed packages
omitted `android.permission.INTERNET`, and the actual process permission check
returned `PERMISSION_DENIED` (-1).

The runner called public `android.system.Os.socket(AF_INET, SOCK_STREAM,
IPPROTO_TCP)`. It received `android.system.ErrnoException` for `socket` with
numeric errno 1, **EPERM**, in 0.081 ms. No descriptor returned. No connect, DNS,
destination or payload operation ran. A returned descriptor or a different
failure would fail the probe before model loading; a returned descriptor would
be closed. The gate requires numeric EACCES or EPERM rather than interpreting an
exception message.

Android documents [INTERNET as the network-socket permission](https://developer.android.com/reference/android/Manifest.permission#INTERNET),
[Os.socket's descriptor/ErrnoException API](https://developer.android.com/reference/android/system/Os#socket(int,%20int,%20int)),
and [ErrnoException.errno](https://developer.android.com/reference/android/system/ErrnoException#errno).
Default [instrumentation targets the app's main process](https://developer.android.com/guide/topics/manifest/instrumentation-element);
this run additionally measured its actual UID and process name.

Only after this proof did the runner verify the complete canonical model:
563,036,064 bytes, SHA-256
`57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`,
inode 1136035, one link and a regular file. Full verification took 675.67 ms;
the Java model-construction call took 2,487.31 ms. The native library SHA was
`822695ae5ca3467392f48ff04d9eda824f52a5f470ba48264fd457f51881259e`.
The actual process backend log reported Q4 and Q8 KleidiAI I8MM kernels and
SME disabled. Every response reported CPU-only execution and reached EOS.

Ten openly seen synthetic inputs exercised six supported intents, two unsafe
requests and repeated Pause proposals across capture off/on/off. The runner
validated exact intent-only JSON, finite timing/token metrics, EOS, capture
identity and expected activation-summary shape. It called the pure
`ModelCommandGate` to construct proposals. It never invoked an action executor,
repository singleton, preferences, services, UI, speech or permission requests.
The native model closed successfully at the end.

## Measurements and their limits

The first native request took **16.83 seconds**; the next nine took
**1.48–2.43 seconds**, with a 2.08-second median. These are native-reported
request times, separate from full model verification and construction. The
file cache had been warmed by complete SHA reads before fresh native loading;
the first request is therefore not a fully cold-storage benchmark. Native
context-setup time is recorded separately, and Java request timings include
additional overhead. Sequential requests and changing device conditions do not
establish controlled performance comparisons.

Whole-process PSS was 1,198,597 KiB after loading and
1,228,721–1,229,269 KiB after requests, approximately **1.172 GiB** for the latter
samples. These snapshots include instrumentation/framework overhead and
shared-page attribution. They are neither model-only memory nor measured peak
RAM, and no release-memory or battery claim follows from them.

Raw intent predictions matched eight of ten illustrations. Complete gated
proposals matched all ten: both “Do not open settings” and “Start focus and open
settings” were wrongly predicted as `start_focus`, then rejected by validation
as `UNKNOWN`. These fixed, openly seen examples are diagnostics, not held-out
accuracy evidence. Semantic agreement was explicitly excluded from the
infrastructure pass condition, and no proposal was executed.

Capture-on returned four finite, width-1024 summaries: `ffn_out-0`,
`ffn_out-11`, `ffn_out-23` and `result_norm`. Capture-off returned none, including
after capture was disabled again. These are observational tensors. They prove
neither causal interpretation nor what a component means, and this short
sequence does not measure capture overhead. Raw tensor vectors and full native
responses remain private in ignored artifacts.

Socket creation was denied in this process. This does not prove whole-device
airplane-mode/disconnected operation, IPv6 behavior, absence of network-capable
IPC delegation, or that omitted INTERNET permission was the sole causal reason
for denial. ASR, phone actions, permissioned monitoring/floating, actual iQOO
hardware/NPU execution and Office Kit integration remain unverified by this run.
Instrumentation restarts the target process; its previous activity lifecycle
was not preserved or tested.

## Preservation and the failed first attempt

Before inference, after inference and after restoration, all three named
production preference-store identities matched semantically. The checkpoint
remained paused, observation off, 100 virtual points and 97,331 ms elapsed.
Microphone and notification grant snapshots matched; these two snapshots do not
establish every Android permission. Own focus-monitor and floating services
were absent. Original model size, SHA, inode and single-link identity matched,
as did installed app SHA
`33c0f61cc60b6186bd9a091d9021ba3feb5cc4e8a46a30b58fc8ca34cb218a7b`.
The original reset-test APK SHA
`b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b`
was restored exactly. No app-data clear, uninstall, network-setting change or
permission grant ran.

The earlier source `d5fef64946fe9fd05474d8b14238ac0532292ddc` used Java Socket.
It failed closed because the actual SocketException had no nested numeric errno.
That attempt completed zero model requests and restored the original test APK
and protected production state. Its evidence remains separate; it establishes
no numeric socket-denial result. The later direct-Os probe changed the API used
to observe denial while retaining the numeric-denial requirement.

## Repeat procedure

Use the reviewed source and packages, an authorised ADB connection and the
already provisioned canonical model. Require the exact v0.13 light app and
original reset-test APK installed, focus paused, observation off and both own
services absent. Respect any different package or production state. The harness
does not unlock or wake the phone and does not open an activity. Commit reviewed
source changes before running: it requires a clean worktree and the supplied
source commit to equal HEAD. Preserve existing evidence; each repeat needs a
new output directory under ignored `artifacts/` with an existing parent.

The test-only runner is selected at build time; the default remains `reset`:

```sh
cd prototype/android
./gradlew assembleDebugAndroidTest -PdiagnosticRunner=nativeIsolation
```

Inspect package, registered runner/target, signer and omitted INTERNET permission
before accepting a rebuilt test APK. A rebuild may have a different byte hash;
the frozen command below requires the retained exact successful artifact.
Run it from the repository root in a clean checkout of the frozen diagnostic
revision, with the existing ignored models/artifacts available:

```sh
python3 scripts/phone_network_isolation.py \
  --serial "$FOCUSPILOT_ADB_SERIAL" \
  --test-apk artifacts/focuspilot-research-v013-network-test-direct.apk \
  --test-sha 36d24aedbe0cd1593125af1b7b8c9873f1589cd0106063f5d12e4833fd928b46 \
  --source aff6fb940fb76f64f77aca8d4c0ff33164a7de43 \
  --output-dir artifacts/network-isolation-v013-direct-repeat-01 \
  --execute-synthetic-native-probe
```

The harness checks original/candidate identities, registered runner, matching
signers and absent INTERNET permission before replacing only the test APK with
`adb install -r`. It reserves 25 MB within the strict 15 GB project cap. Per-request
native cancellation is cooperative at 120 seconds; the host independently
bounds instrumentation at 150 seconds and preserves partial failed output.

Before cleanup it rechecks the complete protected snapshot and recognises only
the exact original or run-owned test APK. Only while those guards hold does it
force-stop the known paused target and reinstall the original test APK. If
production state changes concurrently or a different test APK appears, cleanup
refuses to mutate that state and records the incomplete restoration. Check both
`passed` and `restored`, terminal code -1, raw-file hashes, denial proof, all ten
request results and exact before/after snapshots before publishing a new scoped
aggregate. Keep raw preferences, responses and tensor vectors out of Git.
