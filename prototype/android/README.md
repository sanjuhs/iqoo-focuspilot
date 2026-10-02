# FocusPilot Android research prototype

**Pre-event research code, created 2 October 2026. Not eligible event-written competition code.**

This standalone native Java application demonstrates a friendly original animated companion, bounded phone commands, a local focus timer, opt-in visible foreground monitoring and an explainable hand-set focus policy. **The model lab runs Qwen3.5-0.8B Q4_0 in the actual phone app process on CPU**, with checksummed local weights and optional selected-tensor observations. A separate trained 65-parameter policy lab exposes contributions and ablations on synthetic inputs. Accessibility, Snapdragon NPU and Office Kit remain pending. No internet permission or remote API keys are present.

## Current private task guide 0.11

Source `e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a` adds one private plan associated with the saved
focus goal. Write one to eight steps, mark/undo completion and optionally read the
current step through the existing local TTS path. Replacement/clear require review;
changed goals/revisions block stale actions. Authored text is inert and omitted
from exports/model input. 143 JVM tests pass, lint zero errors/65 warnings. Signed
light APK inspected/installed with APK/model parity, paused/off/100 unchanged.
Actual UI/readback/recovery remains pending; Qwen/prompt/gate/native are unchanged.
[Contract](../../docs/task-guide.md), [identities](../../docs/task-guide-artifacts.json).
Both signed packages inspected; release publication pending. The new
[streaming packaging recipe](../../docs/bundled-packaging.md) preserves light-payload
bytes and adds the pinned model without extra merged model working copies.

## Previous command gate update 0.10

Source `bcc24733655e4eced67d68ff5c47f7ab97d60b36` ships only the conversational gate revision.
Qwen3.5-0.8B Q4_0, original prompt and native runtime remain unchanged; longer
few-shot prompts were rejected after worse useful-command accuracy and higher
host latency. Fresh frozen synthetic model-backed supported proposals rose
15→31/50 with 16 gains/zero losses, all 50 required abstentions and zero wrong
accepts observed. Raw model semantic correctness remains 36/100; 19 supported
requests still abstain. Full-request validation and explicit action review remain.

133 JVM tests pass; lint zero errors/62 warnings. Both signed APKs passed
version/native/model/license/permission inspection. Updated light installation
verified APK and retained model hashes; paused/off/100 points and permissions
were unchanged. No UI/command/overlay test ran on the asleep phone. These are
host and package results, not physical voice, countdown or NPU evidence.
[Contract/results](../../docs/conversational-commands.md),
[artifact identities](../../docs/conversational-commands-artifacts.json).

## Previous floating companion update 0.9

Source `6e483aaf9e42889794ed77c272b8a912539cfc7c` adds a separate visual `specialUse` service.
On the dashboard expand **Mira while you use your phone**, review Android overlay
permission and visible notifications, return, then explicitly review **Show floating
Mira**. Drag the portrait; Open returns to FocusPilot; Pause focus stops the session
and its monitor; Hide leaves focus unchanged. Screen-off/lock/revocation ends the
service and requires Show again. No automatic restart, wake lock, voice or model
run. Prior-consented repository accounting may flush on a deadline or explicit Pause.

127 JVM tests pass; lint zero errors/62 warnings. Signed light/bundled APKs passed
identity/native/model/license/permission checks; light installed with APK/model
hash parity. Actual floating UI/touch/lifecycle is untested, as the phone was asleep.
Qwen3.5, native CPU runtime and v0.8 command gate remain unchanged.
[Contract](../../docs/floating-companion.md),
[artifact identities](../../docs/floating-companion-artifacts.json).

## Build and tests

Java 17, Android SDK platform36, NDK28.2 and Gradle8.14 are required. The APK supports Android9/API28+ and ARM64; the optimized variant additionally needs DOTPROD/I8MM/FP16. Set `ANDROID_HOME` to your SDK, then:

```sh
# From the repository root, builds JNI and then the Android app:
./scripts/build_android.sh
python3 scripts/prepare_phone.py --serial YOUR_DEVICE_SERIAL
```

Default build makes a light APK that needs separately prepared weights. For a
standalone debug APK with the pinned model bundled, run from the repository root:

```sh
NATIVE_BUILD_VARIANT=optimized ./scripts/build_android.sh -PbundleLocalModel=true
```

Only use the optimized variant on a device with its required CPU features; omit
that environment option for the generic variant. The bundled debug APK includes
an uncompressed, hash-verified537MiB GGUF asset. First model load streams it on a
worker into private storage, checks SHA/size, and publishes atomically; later loads
reuse it. Cancel/background/destroy removes partial imports. No network download
or provider key is used. Existing private files are never replaced by import.
Expect roughly1.1GiB installed model/APK storage plus installation staging space.

APK: `app/build/outputs/apk/debug/app-debug.apk`. Application ID: `dev.focuspilot.prototype`.

Initially verified on 2 October 2026: 26 JVM tests and `assembleDebug lintDebug` completed successfully with Gradle 8.14 / AGP 8.12.1 / Java 17 / SDK 36; lint had zero errors. Tests cover core policy, monitor gates, trained-policy parity and independent model-command validation. APK permission inspection confirms no internet permission. Actual phone inference and selected activation capture were observed on Nothing A059; latency and remaining tests are recorded in [status](../../docs/status.md).

## Research demo

1. Start/resume focus and pause; paused time does not accumulate. One repository owns state across Activity instances and service use. Local checkpoints retain elapsed time, usage, virtual points and cooldown. A new process restores the last checkpoint **paused**, with an explicit interruption message if it was previously active; it never automatically restarts observation.
2. Try the sandbox button. Its input is clearly simulated (twice the app budget); the positive-weight policy deducts five **virtual points**, with a 60-second cooldown. No payments occur. Sandbox and real usage points are separate; sandbox resets on process death while real virtual-point checkpoints are retained.
3. Optionally enable local usage reading, then grant Android Usage Access by hand. Choose one package/budget. The dashboard queries OS history for active session intervals; only selected-app summaries are kept. A five-minute look-back seeds the current foreground state, so an app continuously open before that look-back can be undercounted. OEM event delivery and multi-window can affect accuracy. Changing settings pauses the monitor/session for review.
4. For monitoring after leaving the dashboard, separately enable **Keep this focus session in the background** from the visible screen. Usage reading, Usage Access and allowed notifications are prerequisites; Android13+ prompts for notification permission. A `specialUse` foreground service shows an ongoing notification with **Stop focus** and checks usage about every ten seconds. Pause, Stop, disable observation or delete data ends the session/service. Permission revocation is detected on the next check. No boot receiver, sticky restart, wake lock, always-listening mic, screen capture or always-on display exists. Android/OEM power management, force-stop and process death can interrupt it: **24/7 persistence is not guaranteed**. Actual device/background/notification verification is separate from unit tests.
5. Type `start focus`, `pause`, `alarm 7:30 pm`, or `alarm 19:30`. Alarm requests require an app confirmation before handing to Clock with system UI enabled. Clock completion is explicitly unverified. Unknown/compound commands abstain.
6. Push to talk uses only Android's API31+ on-device recognition service. Availability does not establish that the requested language model is installed; failures are shown and no cloud fallback is used. Voice creates a draft which must be reviewed and run. TTS selects an installed English voice which reports no network requirement; otherwise it displays the text. Voice stops when the Activity leaves the foreground.
7. The original Canvas companion has breathing/blinking, listening, celebration, gentle nudge and paused reactions. Paused/hidden/background artwork has no animation loop; visible active motion is capped at about 25fps. Reduce motion, mute voice and hide artwork are user controls. The native artwork is independent of the personal browser's static PNG portraits.
8. Open the local command model, load the verified artifact, then understand a short request. Generation runs on a cancellable worker with fresh recurrent/attention state. Every action has a separate review dialog; malformed, ambiguous, negated or unsupported requests abstain through an independent validator. Enable tensor capture only for research: it displays actual layer summaries, not a causal explanation. The model stays loaded while this screen is open and closes on destruction.
9. Explore the trained decision sandbox with synthetic features. Its 65 parameters reproduce a synthetic teacher, not human productivity. Feature ablations and hidden-unit suppression explain this small network only.
10. Teach Mira in the few-shot sandbox: manually label six synthetic features as Allow/Nudge, inspect up to three neighbors and compare the trained baseline. Its simulated gates open paused/off; saved examples cannot override them. At most32 labels persist locally, with per-record and all-record deletion. This is example retrieval, not LLM fine-tuning or live phone personalization.
11. Delete focus data and saved examples to stop the session/monitor, disable observation and clear settings/history/labels; the model artifact remains installed. Android permissions are revoked separately in system settings. At most 30 summary events are retained; raw usage events and speech audio/transcripts are not persisted.

## What the explanation means

The score uses two nonnegative features: excess usage divided by budget, capped at one (weight 0.80), and total usage divided by budget, capped at one (weight 0.20). A nudge requires score ≥0.65, over-budget usage, active opt-in session, and elapsed cooldown. This is a monotonic hand-set linear rule, **not model training or transformer mechanistic interpretability**. JVM tests verify monotonicity, pause/resume timing, cooldown, bounded virtual points, and parser time bounds/abstention.

## Primary Android API sources

- [UsageStatsManager](https://developer.android.com/reference/android/app/usage/UsageStatsManager)
- [On-device SpeechRecognizer](https://developer.android.com/reference/android/speech/SpeechRecognizer#createOnDeviceSpeechRecognizer(android.content.Context))
- [AlarmClock intents](https://developer.android.com/reference/android/provider/AlarmClock)
- [Voice network requirement](https://developer.android.com/reference/android/speech/tts/Voice#isNetworkConnectionRequired())
- [Foreground service types and specialUse](https://developer.android.com/develop/background-work/services/fgs/service-types)
- [Foreground service launch restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start)
- [Notification permission and foreground services](https://developer.android.com/develop/ui/views/notifications/notification-permission)

The service declares `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE`, and a specific `PROPERTY_SPECIAL_USE_FGS_SUBTYPE`. The `specialUse` classification is an Android-supported research path, **not proof of Google Play approval**; published distribution requires review of the declared use case. Starts are restricted by our product gate to explicit actions in the visible Activity, even though Android has other exemptions. The service does not restart after reboot or a killed process.

The Nothing phone is development hardware. Installation and runtime verification must be recorded separately; building an APK alone is not a tested-device claim.
