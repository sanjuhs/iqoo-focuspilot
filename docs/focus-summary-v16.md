# Focus snapshots — v0.16 research

Version 16 makes reviewed focus status useful: it shows accumulated active time,
the countdown remainder, its explicitly recorded original duration and percentage
progress. It retains the selected Qwen3.5-0.8B Q4_0, original prompt, native library
and existing command validator. The separately tested natural grammar candidate
is rejected and stays out of this package.

New timed sessions record their target. Pause/resume excludes paused time and
retains that target; replacement records a new target without deleting earlier
active time. Completion keeps the completed target; reset and a subsequent
open-ended run clear it. Optional checkpoint metadata persists the target; legacy
checkpoints report unknown original duration. Invalid optional totals do not
change legacy remainder/completion recovery. A wrong-type optional preference is
treated as unknown. No total is inferred from accumulated historical focus.

The formatter identifies accumulated time as across sessions. It reports missing
usage as unavailable, marks saved usage when applicable, distinguishes paused
recovery and completion, and states that current status cannot identify an earlier
reminder's cause. Reviewed EXPLAIN uses a main-thread snapshot after finalizing a
due countdown. Explicit offline readback identifies the last reviewed snapshot;
it does not present an aging spoken remainder as a live update.

App/harness source is `78f8b2b05d89965daf57c2cfc95abc6b70daf4a1`.
All **182 JVM tests** pass, with zero failures/errors/skips. Lint has zero errors
and 64 warnings. Three phone-report boundary tests pass. Signed package inspection
checks version 16, all six notices, unchanged native bytes, seven permissions and
no INTERNET permission. The light APK is 5,513,492 bytes with SHA-256
`1f25c95c7d58d354e55675778fc975768049495be20a05bf7cd709423b73218b`.

On Nothing A059, the exact light APK installed with retained data and the pinned
563,036,064-byte Qwen file. A separate test APK passed **12 grouped installed-app
in-memory invariants**: target, pause/resume/history, replacement, completion,
open-ended/reset clearing, legacy/valid recovery, malformed totals, validation
before completion normalization, and truthful usage/cause limits. Synthetic clocks
and fresh objects are used throughout; the production repository is never opened.
The previous exact v0.13 test APK is restored afterward.

All three named preference identities, paused/off/100 points/97,331 ms checkpoint,
private-model SHA/inode/link count, microphone/notification grants and absent own
services match before upgrade and after fixtures/restoration. There is no activity
launch, wake, permission grant, model inference or tool execution. Instrumentation
restarts the own app process; its prior activity lifecycle is not preserved.

This establishes installed pure-class behavior, not actual new-key preference
migration, process-death persistence, visible reviewed EXPLAIN, readback audibility,
ASR, floating/monitor lifecycle or Clock results. Existing phone/model evidence
retains its earlier package attribution. Actual iQOO/NPU, Office Kit, real-user
learning and an eligible accepted submission remain outstanding.

Measured project logical storage is about 14.44 GB including ignored files and
Git, below the strict 15 GB cap. No new weights/dependencies are downloaded.
A v16 bundle is not created because the two-copy storage reserve does not fit;
the historical v14 bundled package remains available. This is pre-event research
under `prototype/`; it must not be relabelled as event-written competition code.

[Package/source/host reports](focus-summary-artifacts-v16.json),
[actual installed-class record](focus-summary-phone-v16.json),
[rejected wording experiment](natural-command-research.md),
[isolated runner](../prototype/android/app/src/androidTest/java/dev/focuspilot/prototype/FocusSummaryIsolationInstrumentation.java),
[guarded physical harness](../scripts/phone_focus_summary.py).

To rebuild with existing cached tools, from `prototype/android`:

```sh
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home \
ANDROID_HOME=/Users/sanju/Library/Android/sdk \
./gradlew --offline testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug \
  -PbundleLocalModel=false -PdiagnosticRunner=focusSummary
```

Physical repetition requires exact committed source and local APK hashes, a
paused/off own app, its pinned private model and the known original test package.
The harness requires the predeclared previous app hash and an exclusive ignored
record, then upgrades once and restores only a known test identity. The captured
v15→v16 run cannot be silently repeated against the already updated app. Inspect
the CLI and preserve each actual attempt; do not downgrade, clear data or grant
permissions to make the evidence appear successful.
