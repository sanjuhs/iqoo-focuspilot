# FocusPilot · meet Mira

A private Android productivity companion: choose a task, keep a focus session,
and ask Mira for a short, reviewed phone action. Mira is an original animated goth
character with gentle reactions and mute, hide and reduce-motion controls.

**Qwen3.5-0.8B Q4_0 remains the primary local command model.** Research v0.23
fixes readback retry during speech-engine initialization: after cancelling request
A, an explicit request B waits for the same initializer and retains its own
20-second deadline. Cancel, background and destroy prevent automatic speech;
failed or timed-out initialization can be retried explicitly. The v22 dashboard
draft protection and request-token-plus-utterance callback gate remain.
[Current fix and limits](docs/readback-init-v23.md).

All **227 JVM tests** across 30 suites pass, with zero failures/errors/skips;
lint has zero errors and 79 warnings. Six new state fixtures cover the initializer
race and cancellation. The exact light APK installed once in **1,397 ms**,
preserving checked preferences/checkpoint, model, grants, absent services and the
original test APK. The bundle passes payload/signing/alignment checks. All five
published assets and the frozen source tag are verified.
[Publication](docs/readback-init-publication-v23.json). [Installation](docs/readback-init-phone-install-v23.json).
Model, native runtime, permissions and companion availability are retained.
Physical ASR, speaker audibility, lock/unlock, current bundle import, permitted
monitoring, iQOO NPU and Office Kit remain unverified. No new inference ran;
v19 CPU evidence retains its own attribution. [Measured CPU scope](docs/native-page-v19.md).
The dated [v22 readiness check](docs/delivery-readiness-v22.json) found the phone
locked/screen-off with microphone and notification grants off; the v23 install
used no UI, wake, grant or inference operation.

Balanced Qwen3.5 research improves supported native intent matches 41→48/50,
but complete proposals 11→12/50 fail the locked promotion criterion. The selected original model remains installed; no adapter is promoted. [Measured result and limits](docs/balanced-qwen-research.md).

The unchanged v0.13 app also completed ten synthetic Qwen CPU requests after
Android denied socket creation: **16.83 s first request, then 1.48–2.43 s**.
Production state and the original test APK were restored. This is a bounded native
path diagnostic; the complete disconnected voice workflow remains pending.
[Proof and limits](docs/network-isolation-phone.md).

[Download research v0.23](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.23)
· [Watch the dated 4:04 v20 research pitch](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.20/pitch-v020.mp4)
· [Build source](https://github.com/sanjuhs/iqoo-focuspilot/tree/research-v0.23)
· [Verified status](docs/status.md)

> **Pre-event research, not an eligible Finale submission.** The public iQOO
> guide requires competition code to be written during the event. Preparation
> prototypes live under `prototype/`; reuse needs explicit organizer approval.
> [Rules, tracks and full judging rubric](hackathon.md).

## Try the research app

The app supports Android 9/API 28+ on ARM64. The v0.23 packages use an
optimized CPU library requiring **DOTPROD/I8MM/FP16**; it has been tested on
Nothing A059 / SM7635 / Android 16. For other hardware, build the generic variant
below. These are signed debug research packages, not a Play Store release.

| Download | Size | Model setup |
| --- | ---: | --- |
| [Bundled v0.23 APK](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.23/focuspilot-research-v023-readback-init-bundled.apk) | 568.62 MB | Includes the pinned 563.04 MB GGUF; explicit model load imports/verifies it into private storage when missing. Allow roughly 1.1 GiB plus installation staging space. Current bundle import remains untested. |
| [Light v0.23 APK](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.23/focuspilot-research-v023-readback-init-light.apk) | 5.58 MB | Same command screen; needs model preparation below or the already prepared private model for Qwen fallback. Quick commands need no model. |

Verify downloaded bytes against the [v0.23 light manifest](docs/readback-init-artifact-v23.json)
or [v0.23 bundle manifest](docs/readback-init-bundle-artifact-v23.json).
Both use app source `1fc31da5787a49c7680e5bf13b827b6114a0fbe6`.
Only the bundled GGUF is added; all original app/native/license payloads match.
[Readback initialization scope](docs/readback-init-v23.md).
The historical v0.12 bundled APK passed actual missing-model import and second-load reuse
on Nothing, with app data retained: **1,077 ms** import/SHA and **2,320 ms** CPU load.
Its first unconfirmed typed request took **9,534 ms**. The original model, light APK
and recorded app state were restored. Clean fresh-data installation remains a
separate test. [v0.12 import proof](docs/bundled-import-phone-v012.md) ·
[Historical import proof](docs/bundled-model-evidence.json).

1. Install the compatible APK and open FocusPilot. Observation starts off.
2. Open **Ask Mira** and type `Start focus for 20 seconds`. Load Qwen explicitly
   when a request needs model fallback; loading alone performs no inference.
3. Choose **Understand**, inspect the proposal, then review and confirm
   the action. Cancel leaves it unexecuted. Stop pauses; Start can resume the
   remaining countdown. Process recovery starts paused.
4. Save your own task and one to eight steps. Mark/Undo changes your checklist;
   **Speak** requests the current step and **Stop readback** cancels it.
5. Explore the clearly labelled policy and few-shot sandboxes with synthetic
   examples. The accountability balance is virtual; no money is withdrawn.

Use **Set up Mira** for optional microphone, notifications and Usage Access.
Enable those through Android only when you choose the associated feature.
Push-to-talk requires an installed on-device recognition language; recognition
creates an editable draft before inference and action review. Availability alone
is not a tested voice workflow. [Feature setup](docs/command-readiness.md).

Persistent mode is an opt-in, visible focus-monitor service with Stop controls.
Optional floating Mira has separate overlay permission and an explicit Show
review. Enable **Keep Mira nearby after I unlock** for the next Show to retain
that session while locked; Hide ends it. Neither is a silent microphone or a guarantee of 24/7 survival through
Android/OEM process management. Actual monitoring, notification and floating
lifecycle checks remain pending. [Background contract](prototype/android/README.md)
· [Current floating controls](docs/mira-availability-v20.md).

## What is measured

Results below describe the named research builds and experiments. Small smoke
sets are not general automation accuracy or population latency benchmarks.

| Capability | Evidence and current boundary |
| --- | --- |
| Local command understanding | Qwen3.5-0.8B Q4_0 executes through pinned llama.cpp JNI in the Nothing app process; ARM CPU/KleidiAI I8MM is observed. Three supported v0.12 timer proposals took **1.824–1.928 s native inference**, excluding interaction time. [Phone record](docs/focus-recovery-phone.md). |
| Focus action and recovery | **Ten v0.12 phone phases passed**: reviewed Cancel/Start, early Pause, paused-time exclusion, resume, automatic completion and exact paused recovery after force-stop. Two countdowns added exactly 40,000 ms; final total 97,331 ms, observation off and 100 points. This is last-checkpoint recovery, not deep-sleep survival. [Procedure](docs/focus-recovery-phone.md). |
| Task guidance and speech | v0.12 save, mute refusal and explicit readback reached the installed offline-English TTS engine's completion callback; checklist state stayed unchanged. Speaker audibility and ASR remain unverified. Broader checklist/restart branches retain v0.11 attribution. [Readback](docs/guide-readback-phone.md) · [Checklist](docs/task-guide-phone.md). |
| Approved app launches | Historical v0.11 reviewed Calculator/Clock launches matched foreground metadata. No external UI was touched and no alarm was created. Alarm completion and general cross-app automation remain pending. [Launch evidence](docs/app-launch-phone.md). |
| Command reliability | v0.14 gate-only repair improves complete proposals **13→32/50** on 100 fresh informed synthetic host requests: 19 gains, zero losses/observed wrong accepts, all 50 unknown requests refused. Raw model correctness stays 32/100; 18 supported misses remain. **334 actual pure Android gate checks pass**. No universal safety or voice accuracy claim. [Selected evidence](docs/command-validation-v14.md) · [Rejected JSON prompt](docs/json-command-research.md). |
| Activation viewer | Four finite width-1,024 tensor summaries are observed on phone, including v0.12 capture. Historical v0.11 paired timings establish no fixed capture overhead. Laptop interventions produced no positive semantic steering finding. [Capture comparison](docs/capture-benchmark-phone.md) · [Causal experiment](docs/interpretability-experiment.md). |
| Fast decision research | A separate **65-parameter positive-weight policy** scored 472/480 synthetic held-out cases versus 469/480 for a logistic baseline. It remains sandbox/shadow-only. Few-shot retrieval has abstentions; rejected LoRA and intent-head candidates are not deployed. [Policy](docs/policy-baselines.md) · [Learning limits](docs/live-preferences.md). |
| Build and packaging | v0.23: **227 JVM tests**, zero failures/errors/skips and zero lint errors/79 warnings. Exact light installed with protected state preserved; bundled model SHA, complete app-payload parity, signing and alignment pass. Publication verification is pending. No `INTERNET` permission. Physical voice/readback/lock-unlock, current bundle import/UI, thermals and peak memory remain pending. [Light manifest](docs/readback-init-artifact-v23.json) · [Bundle manifest](docs/readback-init-bundle-artifact-v23.json). |
| Phone export | v0.12 review/picker Cancel and actual local Save passed. A 496-byte empty summary matched phone/laptop checksums and passed zero-record schema validation. No policy inference or Office Kit transfer occurred. [Actual export](docs/phone-export.md). |
| Hardware, bridge and submission | Actual iQOO/NPU execution, Office Kit pairing/transfer, live permissioned monitoring, IoT hardware, accepted application and eligible event submission remain unfinished. Local laptop export validation is separate from Office Kit. [Remaining deliverables](docs/remaining-deliverables.md). |

The [4:04 v20 research pitch](docs/v020-pitch.md) combines original Mira
animation, v20 source diagrams and two explicitly historical v12 own-app clips
at 1× speed. Full decode, captions/audio checks and sampled encoded visuals/clip
parity pass. Complete human listening and current live workflows remain pending.

Historical release results and videos remain in [status](docs/status.md) and
[previous releases](https://github.com/sanjuhs/iqoo-focuspilot/releases).

## How it works

```mermaid
flowchart LR
    A[Typed command / reviewed speech draft] --> B[Fast local command or explicit Qwen fallback]
    B --> C[Original-request validation]
    C --> D[Explicit action review]
    D --> E[Bounded Android action]
    E --> F[Outcome and local checkpoint]
    G[Opt-in usage summary] --> H[Budget / cooldown / override policy]
    H --> I[Virtual accountability nudge]
    J[Private authored steps] --> K[Mira checklist / explicit readback]
```

The language model proposes an intent. Independent code validates the complete
original request, arguments and permissions before execution. Repeated focus
nudges use a hand-set policy; the trained tiny network evaluates explanations in
a separate sandbox/shadow path. It cannot create live actions. Authored steps are
inert private text, excluded from model input and exports.

The larger goal includes voice-controlled assistance, few-shot personalization,
a useful fast decision path, scoped phone automation, activation experiments and
an actual iQOO/laptop bridge. [Architecture](docs/architecture.md) and
[the delivery plan](plan.md) preserve those requirements and their acceptance gates.
An ADB cable is development access, not Office Kit integration; local CPU inference
is not Snapdragon NPU evidence.

## Build from source

Use Java 17, Android SDK platform 36, NDK 28.2, Gradle 8.14, Node.js and Python 3.
Set `ANDROID_HOME` to your SDK. The build script fetches the pinned llama.cpp
source into ignored `research/`, builds JNI, and runs Android tests, assembly and
lint. [Detailed Android setup](prototype/android/README.md)
· [Model pin and runtime](docs/on-device-model.md).

```sh
git clone https://github.com/sanjuhs/iqoo-focuspilot.git
cd iqoo-focuspilot
git checkout research-v0.23

# Download and verify the selected model into ignored local storage.
node prototype/qwen/prepare-model.mjs qwen35

# Generic ARM64 CPU build with bundled model.
./scripts/build_android.sh -PbundleLocalModel=true

# Inspect authorized USB debugging; unlock and accept RSA on the phone yourself.
python3 scripts/check_device.py --serial YOUR_DEVICE_SERIAL
adb -s YOUR_DEVICE_SERIAL install -r prototype/android/app/build/outputs/apk/debug/app-debug.apk
```

For a light build, omit `-PbundleLocalModel=true`, install it, then run
`python3 scripts/prepare_phone.py --serial YOUR_DEVICE_SERIAL --skip-install`. That preparation
checks hashes and transfers the pinned model into the debug app's private storage.
Use `NATIVE_BUILD_VARIANT=optimized` only after verifying the required CPU features.
The generic build is portable to supported ARM64 CPUs; it is not byte-identical
to the published optimized APK.

No provider API key is required by the Android runtime. Keep total project,
dependencies, models and generated artifacts under **15,000,000,000 bytes**;
aim below 10 GB. Avoid redundant model/runtime copies. Model weights and private
captures stay outside Git; only explicitly sanitized research media is published.

## Documentation and research

| Start with | Purpose |
| --- | --- |
| [instructions.md](instructions.md) · [plan.md](plan.md) | Working rules, implementation sequence and acceptance gates |
| [hackathon.md](hackathon.md) · [event research](docs/hackathon-research.md) | Productivity track, 100% rubric, event-written code and application requirements |
| [Verified status](docs/status.md) · [remaining deliverables](docs/remaining-deliverables.md) | Current proof, historical attribution and full unfinished scope |
| [Architecture](docs/architecture.md) · [model research](docs/model-research.md) | Android design, Kev/Laya/CUA research, licenses and model comparisons |
| [Companion design](docs/companion-design.md) · [voice](docs/voice-integration.md) · [readback initialization](docs/readback-init-v23.md) | Original Mira artwork, accessibility controls and speech lifecycle |
| [Task guide](docs/task-guide.md) · [timed focus](docs/timed-focus.md) | Authored steps, review/cancellation, countdown and recovery contracts |
| [Data export](docs/data-export.md) · [phone proof](docs/phone-export.md) · [laptop review](docs/officekit-export-workflow.md) | Private export schema and bounded local replay; Office Kit proof gates |
| [Tiny policy](docs/policy-baselines.md) · [fine-tuning](docs/qwen-finetuning.md) · [intent head](docs/intent-head.md) | Measured research, rejected candidates and synthetic limitations |
| [Task-planning research](docs/task-draft-research.md) · [sandbox automation](docs/sandbox-automation.md) | Unpromoted planning experiments and two own-app selector controls |
| [Snapdragon deployment](docs/snapdragon-deployment.md) · [activation experiments](docs/interpretability-experiment.md) | Actual-backend and causal-evidence requirements |
| [Dated v20 pitch](docs/v020-pitch.md) · [editable narration](docs/v020-research-pitch-script.md) | Video, captions, exact evidence and reproducible rendering |

## Contribute

Original project code and documentation are [MIT licensed](LICENSE). Model,
runtime and dependency licenses remain their own; immutable pins and notices are
in [model research](docs/model-research.md). Check upstream redistribution terms,
including mixed-license CUA components, before copying code or weights.

Use synthetic or consented sandbox content. Keep `.env`, credentials, weights,
training data and private phone captures ignored. Optional cloud development tools
must not become a hidden dependency of the local runtime. Real payments,
purchases, messages and destructive actions require action-level confirmation;
the current accountability balance is simulated.

Before a push, inspect the Git index and named changes:

```sh
python3 scripts/check_secrets.py
git status --short
```

The checker avoids printing credentials but cannot recognize every secret format.
Keep measured limitations with new evidence in [docs/status.md](docs/status.md).
