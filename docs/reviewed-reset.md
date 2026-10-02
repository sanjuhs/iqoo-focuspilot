# Reviewed session reset — v0.13 research

Reset now asks before clearing the focus session and clears a stale recovery
warning. **Qwen3.5-0.8B Q4_0 remains the command model.** This change does not
alter its prompt, action gate, native runtime or Mira artwork. The implementation
is pre-event research under `prototype/`, not an eligible event submission.

App source is `1eed4348d3d0233d786bcd3b86c05d225ebf8db6`, version code 13,
`0.13-reviewed-reset-research`. The app and separate instrumentation APK build;
148 JVM tests pass, with zero lint errors and 65 warnings. Five host boundary
tests for the phone harness also pass.

## Behavior and confirmation boundary

Previously, `FocusRepository.reset()` reset the timer, usage counter and virtual
points but retained the in-memory `interrupted` flag. Mira could continue showing
the interrupted-session warning until a new focus session started. Reset now
clears that flag too.

The dashboard's **Reset this session** button first opens **Reset your focus
session?**. The review explains that confirmation clears accumulated focus time,
the countdown and counted app usage, restores 100 virtual points, and stops focus
and its monitor. The task, checklist, saved labels and observation choice remain
saved. **Keep session** cancels. No stop/reset call runs just from opening the
review.

The activity dismisses its review and invalidates its review epoch on `onPause`.
Confirmation also requires the same session generation and a visible activity.
A changed or expired review is refused. This lifecycle and generation behavior
is source-reviewed; physical cancellation and stale-generation confirmation
have not yet been established on v0.13.

The review uses Android's
[AlertDialog title and action-button APIs](https://developer.android.com/develop/ui/views/components/dialogs).
Android recommends `DialogFragment` for lifecycle management; this small native
prototype explicitly dismisses its activity-owned dialog on pause. It does not
claim to implement `DialogFragment`.

## Physical verification scope

On 3 October 2026, the raw-output fixture run passed **22 checks** on the actual
v0.13 light APK. Its one completed phase covers recovered/active reset,
owned-fixture cleanup and exact before/after production snapshots.
[Exact physical record](reviewed-reset-phone-v013.json) binds executed harness
`9fa0b583d31783209c60f8137d5a0ccad3996035` and SHA
`38a73327e7cd0d9a02f9af86a2d59bccfd928e8b61b56869e9dc6b3bd3175501`
to the APKs, native library and model identities. The record explicitly sets
`fixture_only=true`, `passed=true` and
`production_ui_cancellation_verified=false`. The synthetic fixtures exercised
the real repository on Android; dashboard cancellation remains pending.

[The first phone harness record](reviewed-reset-phone-v013-first-attempt.json)
remains preserved as a failed checker attempt.
It used formatted `am instrument -w` output while expecting raw result fields;
the first record did not retain that output or complete its production UI phases.
A separate same-APK diagnostic run emitted a formatted 22-check success message;
it is not attributed to the first invocation. The harness now uses
`am instrument -r -w` and captures raw output before validating result fields.
The later UI repeat stopped at its initial awake/unlocked own-app guard because
the phone was asleep/locked; no cancellation result is attributed to that attempt.

The instrumentation creates a unique preference prefix and refuses existing
files with that prefix. A `ContextWrapper` maps every preference-store request
to that prefix and returns itself as the application context. The repository is
constructed reflectively; its production singleton is never requested. Service
start/stop calls are forbidden in the fixture context. No model file is loaded.
The Android APIs used are documented in
[Instrumentation](https://developer.android.com/reference/android/app/Instrumentation)
and [ContextWrapper](https://developer.android.com/reference/android/content/ContextWrapper).

The recovered fixture seeds 5,000 ms elapsed, a 15,000 ms remaining countdown,
2,000 ms counted usage, 75 virtual points and an active checkpoint. Recovery must
be paused and marked interrupted. Reset must clear interruption, active/timed/
completed state and counters, and restore 100 points. Observation is seeded
**true** so its preservation assertion would catch accidental disabling; the
fixture is paused and reads no actual app usage. Synthetic task/checklist and
live-label sentinel keys, budget and planned-focus settings must survive.

A second fixture phase explicitly disables observation, starts a one-second
countdown, resets it, waits 1.25 seconds off the main thread, and checks that the
old countdown cannot complete. Repository operations run on Android's main
thread. Pending preference writes are drained before cleanup, which removes
only the two exact test-owned stores. Failure and cleanup errors are reported
separately.

These assertions establish preservation of sentinel keys, not valid checklist
or label deserialization. Reconstructing a repository in the same process reads
SharedPreferences' cached state; it is not a process-restart or independent
disk-reload test. Waiting beyond the deadline proves that the old countdown
does not complete; it does not separately measure callback removal.

The v0.13 light APK is installed. The fixture run independently verified that
the production checkpoint remains paused, observation off, 100 points and
97,331 ms. The original private model retains its recorded inode, size, single
link and SHA. Microphone and notification grants remain denied. These two grant
snapshots do not establish the state of every Android permission.
All three named preference-store identities
match semantically before/after, and the focus-monitor and floating services are
absent. The recorded final project size was 14,397,887,431 logical bytes.
The separate synthetic test APK remains
installed; no production Reset confirmation, app-data clear or uninstall is
part of this verification.

## Package identities and historical evidence

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| v0.13 light APK | 5,497,068 | `33c0f61cc60b6186bd9a091d9021ba3feb5cc4e8a46a30b58fc8ca34cb218a7b` |
| v0.13 bundled APK | 568,538,615 | `6af9c572dbe50934d09c7d17e0460d4710f501a792786675da87bcbc99577ae0` |
| v0.13 isolated test APK | 29,334 | `b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b` |
| Bundled/private Qwen GGUF | 563,036,064 | `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf` |

The native ARM64 library remains
`822695ae5ca3467392f48ff04d9eda824f52a5f470ba48264fd457f51881259e`.
Packaging verified both signatures, matching public debug certificate,
16 KiB alignment and every original non-signature payload. The only added
non-signature entry is the stored GGUF asset. The packaging estimate reserved
two temporary copies and stayed below the 15,000,000,000-byte project limit.
This establishes the bundle's bytes and packaging; it does not establish a new
v0.13 bundled import or LLM inference run.

Earlier [v0.12 bundled import](bundled-import-phone-v012.md),
[countdown/recovery](focus-recovery-phone.md),
[task readback](guide-readback-phone.md), [export](phone-export.md) and
[4:41 demo](v012-pitch.md) retain their original APK/source attribution. They
are not silently relabeled as v0.13 measurements. The reset change is not shown
in that video.

## Repeat without clearing production data

Use the frozen light and test APK identities above and a clean checkout of
executed harness commit `9fa0b583d31783209c60f8137d5a0ccad3996035`.
The completed fixture-only mode requires the exact light and test APKs already
installed, performs no installation or UI interaction, and does not wake or
unlock the device. Its paused/off, service, model and snapshot guards still apply.
For dashboard checks, FocusPilot must already be awake, unlocked and foreground,
focus paused, observation off and both own monitor/floating services absent.
The exact regular, single-link pinned private model must already exist.
Choose a new path inside the existing writable ignored `artifacts/` directory.

```sh
python3 scripts/phone_reviewed_reset.py --serial YOUR_DEVICE_SERIAL \
  --light artifacts/focuspilot-research-v013-reset-light.apk \
  --test-apk artifacts/focuspilot-research-v013-reset-test.apk \
  --light-sha 33c0f61cc60b6186bd9a091d9021ba3feb5cc4e8a46a30b58fc8ca34cb218a7b \
  --test-sha b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b \
  --source 9fa0b583d31783209c60f8137d5a0ccad3996035 \
  --output artifacts/reviewed-reset-repeat-v013.json \
  --execute-isolated-reset --reuse-installed-test --fixture-only
```

The explicit reuse flag accepts only one exact installed test APK path and its
frozen checksum. Fixture-only mode refuses an absent package. For the pending
full UI mode, remove `--fixture-only`; omit `--reuse-installed-test` when the
test package is absent. A transport failure does not imply absence, and an
existing different test APK is left unchanged.
The full UI mode is still awaiting successful completion and must start with
the awake/unlocked own app. A fixture-only pass is not a UI-proof claim. Full UI
mode checks exact production snapshots after isolated fixtures, opening review,
Keep session, Back and Home.
It never taps the production **Reset session** confirmation and never dumps the
launcher UI after Home.

For the raw fixture result format, Android documents `-r` with `am instrument`
in its [command-line testing guide](https://developer.android.com/studio/test/command-line):

```sh
adb -s YOUR_DEVICE_SERIAL shell am instrument -r -w \
  dev.focuspilot.prototype.test/dev.focuspilot.prototype.ResetIsolationInstrumentation
```

A standalone instrumentation result does not prove unchanged production
preferences/model/grants or successful UI cancellation; collect the separate
before/after snapshots and fixture-cleanup checks too. Host boundary checks:

```sh
PYTHONPATH=scripts python3 -m unittest discover -s scripts \
  -p test_phone_reviewed_reset.py
```

The broader goal remains active: genuine offline ASR and opt-in background/
floating operation, current-package inference and complete human demo review,
verified iQOO/NPU use, actual Office Kit transport, eligible event-written code
or organizer reuse approval, and an accepted hackathon submission remain
outstanding. This reset work adds no mechanistic-interpretability, training,
NPU, Office Kit or unrestricted phone-control result.
