# Instructions — FocusPilot

FocusPilot is the working name for an opt-in, local Android productivity assistant.
It observes permitted phone context, makes fast bounded decisions, explains its
reasoning, and helps the user act through voice and a small set of reliable tools.

## Current v0.11 authored-guide phone coverage

A synthetic three-step plan was tested through the installed app's own UI on
Nothing: Save, Mark/Undo, completion/Undo, real process force-stop/restart with
exact record recovery, replacement Cancel/confirm and clear Cancel/confirm with
cleared-state recovery. All 12 recorded phases passed. The temporary plan was
removed and the original empty goal restored; focus stayed paused, observation off,
points 100 and total elapsed 57,331 ms. No model, voice, permission or external-app
action was invoked. Eight harness boundary/cleanup tests and six report-binding
tests pass; the latter preserve the full-task gate as incomplete. Readback, stale
reviews, goal-switch and other remaining branches are separate requirements.
[Phone record](docs/task-guide-phone-v011.json),
[coverage and repeat procedure](docs/task-guide-phone.md).

## Current v0.11 phone countdown

An actual typed Qwen3.5-0.8B request on Nothing produced a reviewed 20-second
focus proposal (1,932 ms reported CPU inference), which was confirmed and completed
automatically. Persisted elapsed time increased exactly 20,000 ms; focus ended
paused, observation off and points 100. One synthetic process-live case establishes
this narrow loop; task-guide UI, voice, sleep/recovery, iQOO/NPU and Office Kit
remain pending. The failed immediate checkpoint test is preserved separately;
the harness now polls asynchronous persistence and requires observed awake/unlocked
own-app foreground state. Seven harness tests pass.
[Physical record](docs/current-countdown-phone-v011.json),
[failed first attempt](docs/countdown-first-attempt-v011.json).

## Task-planning experiments — unpromoted

Actual local-model host planning failed useful-task criteria: the first candidate
served 0/8 benign goals; the example-based repair fully met 4/10 fresh benign
criteria and included nonsense/negation failures. Both experiments and a compiled
but unapplied reviewed-import scaffold are preserved. The selected v0.11 app,
model, prompt and native remain unchanged. [Evidence](docs/task-draft-research.md).

## Task guidance checkpoint — v0.11

Source `e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a` adds a private, user-authored plan for the
saved focus task: one to eight steps, explicit completion/undo, reviewed replacement
and clear, and optional local readback. Goal/revision checks block stale progress
and speech; step text executes no phone action and enters no model/export.
**143 JVM tests pass**, lint zero errors/65 warnings. Signed light packaging passed
native/license/permission inspection and installed with matching APK/model hashes;
focus paused, observation off and 100 points stayed unchanged during installation.
No wake, UI, permission or task action occurred during that installation; the
separate later phone tests above used the same installed APK. Both signed packages are inspected and [published with v0.11](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.11);
all four server asset sizes/SHA-256 digests match local files and the tag resolves
to the exact app source above. Authored step/save/progress/restart branches are observed above; readback and the
remaining task-guide branches stay pending.
Qwen3.5 Q4_0, prompt, gate and native are unchanged. The publication preflight measured
12,491,320,741 logical project bytes (about 12.491 GB), below the strict 15 GB cap;
ignored files and Git are included, pre-existing shared SDK caches excluded.
[Task guide](docs/task-guide.md),
[immutable identities](docs/task-guide-artifacts.json).

A seven-parameter logistic comparison now scores 469/480 synthetic cases versus
472/480 for the existing 65-parameter network. This informed known-teacher result
closes the baseline gap and promotes neither policy. [Evidence](docs/policy-baselines.md).

## Current research pitch — published video

A new **4:35 (274.836-second)** application concept/research video is locally
ready: `artifacts/pitch-current.mp4`, 1920×1080 H.264/24fps with AAC and **30 measured
caption segments**. It uses original procedural illustrations, with no phone
capture or new phone actions. The historical v0.3 `pitch-research.mp4` is preserved.

Renderer source is `6ca1d02284ecffd643b9d50ea6b1b18d610f88d1`; the video references
v0.10 app source `bcc24733655e4eced67d68ff5c47f7ab97d60b36`. The new v0.11 task guide
is not depicted in that video. Video SHA-256 is
`1bb3fd1d96330b5320b8d8281e8f824212ada852a84835c3b1cbcb0895e82a25`.
Full decode, caption timing, encoded-frame/transition review and audio-level checks
passed. **Complete human listening/playback review remains pending.** The video's
historical typed actions, current install identity and synthetic metrics retain
their different evidence scopes; no live iQOO/NPU/Office Kit result or eligible-entry
claim is established. Dashboard format/cutoff, event-code eligibility and accepted
submission remain unresolved.

The video, captions and both evidence manifests are [published with v0.10](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.10).
All four new server sizes/SHA-256 digests match local files; the original three
APK/manifest assets remain unchanged and the tag still points to the app source.

[Current pitch and reproduction](docs/current-pitch.md),
[immutable video evidence](docs/current-pitch-evidence.json),
[render manifest](docs/current-pitch-render-manifest.json),
[editable narration/shot plan](docs/current-research-pitch-script.md).

## Current research baseline — v0.10

Source `bcc24733655e4eced67d68ff5c47f7ab97d60b36`, version code **10** /
`0.10-conversational-gate-research`, selects the expanded original-request gate
while keeping **Qwen3.5-0.8B Q4_0, native runtime and original prompt unchanged**.
The longer prompt candidate was rejected; there is no deployed model fine-tuning.

Fresh frozen synthetic confirmation: correct supported actions/slots **15→31/50**,
16 gains/zero losses, all 50 unsupported requests rejected and zero wrong accepted
proposals observed. **19/50 supported requests still falsely abstain**. Raw model
semantic correctness is **36/100** (35 supported, one unknown), with 49 unsupported
tool proposals. This is host evidence by an informed author, not voice/phone or
universal safety. Explicit action review remains required.

**133 Android JVM tests pass**, lint zero errors/**62 warnings**; **14 artifact-audit
tests pass**. Both signed version-10 packages passed native/model/license/permission
inspection: all six notices present and no `INTERNET` permission.

| Package | Bytes | SHA-256 |
| --- | ---: | --- |
| Light | 5,480,648 | `a1a85e70f5d459df6e73b4294dcbeed81518489fe419b30729333ec11e083103` |
| Bundled | 568,516,824 | `1cb5678781ca3a4aa63f462d445b05516d93f1d363e78f6e2a05f7f46a777bf0` |

The light APK installed on Nothing with matching installed-APK/private-model
hashes. Focus inactive, observation off and virtual points 100 stayed unchanged;
microphone and notification grants stayed false, overlay remained default with no
operation. Display was asleep and own app not focused; the lockscreen metadata flag
was false, which does not establish a usable unlocked foreground state. **No wake,
UI test, command, permission grant or overlay test occurred.** Physical timer,
voice/TTS, monitor/Stop, Clock, disconnected inference, iQOO/NPU and Office Kit remain
pending. Prior build outcomes retain their historical binary/source attribution.

Measured project files total **13,511,076,286 bytes = 13.511 GB = 12.583 GiB**,
below the strict decimal 15 GB limit. This includes ignored project files and
excludes pre-existing shared SDK/`.gradle` caches; it is not peak RAM. The
[v0.10 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.10)
is published: all three server sizes/SHA-256 digests match local artifacts and
the tag resolves to the exact app-source revision above. Publication does not
establish physical execution or submission acceptance.

[Command selection and confirmation](docs/conversational-commands.md),
[immutable artifact manifest](docs/conversational-commands-artifacts.json),
[full remaining deliverables](docs/remaining-deliverables.md).

## Previous research baseline — v0.9

Source `6e483aaf9e42889794ed77c272b8a912539cfc7c` adds optional floating Mira with explicit reviewed
Show, movable portrait, Open, Pause focus and Hide controls. The separate service
requires user-granted overlay permission, visible floating notifications, unhidden
artwork and an interactive unlocked phone. Permission return starts nothing.
Hide/screen-off/lock/revocation stop the visual companion without pausing focus;
Pause explicitly stops focus and its monitor. No new observation, microphone or
model run is started. Existing consented accounting may flush at deadline/Pause.

**127 JVM tests pass**, lint zero errors/62 warnings. Both signed APKs passed
packaging inspection; light installed with matching installed APK/private-model
hashes. No floating permission was granted or actual overlay UI tested: the phone
was asleep/our app not focused. Qwen3.5, prompt, native runtime and command gate
are unchanged. Logical project size **12.05 GiB**, within 15 GB.
[Controls and proof gates](docs/floating-companion.md),
[platform sources](docs/floating-companion-platform.md).

## Previous research baseline — v0.8

Use [natural commands](docs/natural-commands.md): one whole supported request,
bounded English/digit slots and matching model intent, followed by explicit review.
Spoken alarm times require AM/PM; colon times may use 24-hour notation. Malformed
slots and extra prose must not disappear. The dashboard's quick parser is unchanged.
Source `a214bd7fc6ddd3cc3917d7a1f1aa9d854b7f3eb3` has 119 passing JVM tests,
zero lint errors/59 warnings. Both APKs passed packaging inspection; light installed
with verified APK/private-model hashes. No physical v0.8 command outcome yet.

Frozen generated-model results are 12/40 correct supported commands versus 9/40
for v0.7; wrong accepts fell five to zero on 60 unsupported cases. Nine gains and
six regressions are retained. 28 supported requests still abstain. This is an
independent synthetic host result, not ASR, live actions or autonomous reliability.

## Previous research baseline — v0.7

Timed focus accepts one validated digits duration of 1 second–120 minutes after
review, or use the reviewed 25-minute shortcut. Pause retains the remainder;
process recovery is paused, and Android sleep may delay completion visibility.
No monitor/microphone is enabled by a timer. The actual short phone-countdown test
is pending an unlocked foreground app; current code has 105 passing JVM tests.
See [timed focus](docs/timed-focus.md). Keep the earlier physical evidence separate.

The [frozen-Qwen intent head](docs/intent-head.md) is a separate measured research
candidate. Its raw semantic score improved on 90 synthetic cases, but strict action
coverage decreased and the selected threshold relies on float rounding. Do not
promote it, label it internal Qwen fine-tuning, or cite head-only time as app latency.
Use a new frozen evaluation for future changes; preserve this negative result.

## Previous research baseline — v0.6

Use source `29c4c3372fcc913d3672e59803a3aa870fa2426b` as the v0.6 build identity;
both APKs and hash evidence are [published](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.6). **Set up Mira** reads optional feature
readiness without granting permissions or starting services. Actual typed Qwen
Start/Pause were reviewed, confirmed and verified on Nothing; alarm cancellation
was rejected. These tests do not establish voice, Clock, disconnected offline,
iQOO NPU or Office Kit operation. [Readiness evidence](docs/command-readiness.md).

Keep the [58-case command limits](docs/command-reliability.md) visible: 25/58 raw,
49/58 gated including correct rejections, 16/23 supported commands correct, and
two wrong accepted proposals. Continue explicit action review. The [laptop bridge](docs/officekit-export-workflow.md)
validates one user-selected private export and computes aggregate shadow scores;
15 bridge tests and synthetic [Java/Python interoperability](docs/bridge-java-interop.json)
are verified. Never treat a temporary local-file test as an Office Kit transfer.

## Read this first

1. Read [hackathon.md](hackathon.md) for eligibility and judging requirements.
2. Read [plan.md](plan.md) for delivery order and acceptance gates.
3. Read [docs/status.md](docs/status.md) for what has actually been verified.
4. Read [docs/architecture.md](docs/architecture.md) and
   [docs/model-research.md](docs/model-research.md) before choosing runtimes.

The public Finale dates are October 9–11, 2026. October 3 morning is our working
preparation/application target, pending the signed-in dashboard. The guide and
Terms require competition work to be created in the event window. This repository
starts as planning, research and development utilities; competition app code starts
in the permitted window unless the organizers explicitly allow earlier code.
Do not submit a pre-event prototype as event-created work.

## Product contract

- Track: Productivity; Open Innovation is the fallback if organizers classify it differently.
- Companion: friendly original goth character with subtle motion, mute/hide/reduce-motion
  controls. Persistent mode is opt-in foreground monitoring with visible Stop, not
  a constantly lit screen or silent microphone. See [design](docs/companion-design.md).
- Main demo: start focus mode, recognize excessive use of a user-selected distracting app,
  explain a nudge, record a simulated penalty, and return the user to their chosen task.
- Voice demo: a push-to-talk request creates a proposed alarm through Android's clock intent.
- Learning demo: user labels sandbox states, with separate opt-in real-summary labels; retrieval uses those examples to guide
  subsequent decisions. Show a held-out evaluation, not only training examples.
- Model demo: load the selected licensed quantized Qwen3.5-0.8B language model on the phone and record its actual
  inference backend. A deterministic parser is an explicit fallback, not an LLM claim.
  Selected candidate: Qwen3.5-0.8B Q4_0, with the user expanding the original
  0.1–0.5B size target. Laya and the prior 0.5B are comparison baselines.
- Explanation demo: show feature values and contributions from a tiny positive-weight
  classifier. This explains that classifier, not every activation of a transformer.
- Bridge demo: use the documented Office Kit workflow once account/device access is
  available. A generic USB laptop link is a separate development bridge.

## Android setup

Installed SDK: `/Users/sanju/Library/Android/sdk`. Java 17 and adb are available.
The development phone is now authorized; its initial state was `unauthorized`
before the user accepted the RSA prompt. Verified: Nothing A059, Android 16/API 36,
`SM7635`, ARM64, successful read-only shell command. Recheck with:

```sh
python3 scripts/check_device.py
```

The checker only reads device properties. It does not grant app permissions,
enable observation, unlock the bootloader or collect screen contents.
If authorization does not appear, reconnect the USB cable with the phone unlocked;
check USB debugging under Developer options. Revoke debugging authorizations only
if reconnecting fails and you are comfortable reauthorizing existing computers.

During app development, install the debug APK on the selected serial only. Enable
Usage Access, notifications and microphone only through the app/Android permission
screens when you choose those features. The optional Accessibility proof is restricted to two selectors in FocusPilot’s own synthetic sandbox. It requires manual Android enablement and a separate five-second arm; it cannot control other apps.
Use a sandbox account and synthetic screen content for automation evaluation.
Nothing-phone tests establish Android compatibility, not Snapdragon/iQOO eligibility.

## Installable research packages

The default light APK needs model preparation through the documented debug script.
The optional bundled APK contains Qwen3.5-0.8B Q4_0, imports/verifies it once into
private storage, and can start without laptop model transfer. Both are research
builds; neither establishes eligible event-created code or NPU use.

```sh
node prototype/qwen/prepare-model.mjs qwen35
# Generic ARM64 baseline with bundled weights:
./scripts/build_android.sh -PbundleLocalModel=true
# Optimized CPU variant only for verified DOTPROD/I8MM/FP16 devices:
NATIVE_BUILD_VARIANT=optimized ./scripts/build_android.sh -PbundleLocalModel=true
```

After installing a bundled build, open Ask Mira and load the local model. Consent,
Usage Access, notifications and microphone are separately user-controlled. Read
[Android package details](prototype/android/README.md) and [current evidence](docs/status.md).

## Implementation order

1. Establish a native Java Android app with a visible session switch and local settings.
2. Implement usage accounting, simulator balance, event log, and positive-weight decision head.
3. Add bounded commands: focus session, pause/resume, open approved app, propose alarm.
4. Integrate and benchmark one small local LLM with constrained output and abstention.
5. Add push-to-talk, local speech where available, and text-to-speech.
6. Add selector-based accessibility actions and read-back verification in the sandbox.
7. Validate Snapdragon acceleration and Office Kit on organizer-approved hardware.
8. Record the demo and package source, metrics, model attribution and limitations.

Do not start with a general agent that can click every screen. Start with actions
whose preconditions, outcomes and cancellation can be tested. A model proposes;
the permission-aware executor validates and executes. Text found on a screen is
untrusted input and never overrides the user's goal or the action allowlist.

## Local AI and explanations

In the focus screen, **Choose your task & targets** saves a private task and optional
planned-focus/continuous-app limits. Blank or zero means unknown. Saving pauses
monitoring for review; these targets do not stop a session automatically. Changing
the monitored app/budget clears its explanation limits. The research explanation
panel evaluates the trained network only from complete, fresh, consented summaries;
its score does not trigger actions. See [feature mapping](docs/live-policy-evidence.md).

Ask Mira's voice flow is explicit: Speak, review/edit the draft, Understand locally,
review the proposal, confirm. Microphone permission and an installed local speech
language are separate from Qwen weights. Granting microphone permission does not
start recording. See [voice lifecycle](docs/voice-integration.md).

Keep a small LLM for understanding varied commands; keep repeated decisions in a
compact classifier. Train offline from consented sandbox data. Fine-tuning is a
stretch gate after a baseline works, with a frozen held-out set and reported gains.
See [live preferences](docs/live-preferences.md) for the private real-summary label path and [local export](docs/data-export.md) for user-selected exports. Few-shot retrieval, fine-tuning and in-context examples are different methods; name
the method actually used. Positive weights make effects monotonic only with a
defined nonnegative feature encoding. They do not automatically make an entire
network interpretable. Use feature ablation and counterfactual checks.

CPU/GPU inference is a valid local baseline. Claim Snapdragon NPU only after
export, supported operator coverage, hardware execution logs and device latency
are verified. Quantizing a model or running ONNX does not establish NPU execution.

## Privacy, actions and spending

Observation is opt-in, scoped to the session, visible and pausable. Exclude password,
banking and sensitive screens; do not send personal screen data to remote APIs.
Keep raw captures local and ignored by Git. Provide delete/export controls.
Use virtual rupees/points in the demo. Never debit money solely because a model
labels an activity unproductive. User labels and app budgets take precedence.
Require confirmation for real payments, outgoing messages, purchases and deletion.
Honor focus cooldowns, emergency use and manual overrides.

`.env` contains an OpenAI key for optional laptop development tooling. It stays
ignored; do not print it, commit it, put it in an APK or use it as the local demo's
runtime dependency. No API spend is needed for initial planning and setup.

## Storage and source control

Budget 10–15 GB total. Download one model at a time; keep weights under ignored
`models/`, external checkouts under ignored `research/`, captures/builds under
ignored `artifacts/`. Track model IDs, immutable revisions, hashes, license and
download commands instead of uploading weights. Measure the actual budget with
`du -sh .` plus external dependency caches used by this project.

Run the secret check before every push:

```sh
python3 scripts/check_secrets.py
git status --short
```

Back up source and documentation to the public GitHub repository. Commit only
named files after reviewing staged changes. Attribute any copied upstream code
and preserve its license. Do not copy research repositories wholesale.

## Definition of done

The APK installs and the scripted demo completes on the tested phone; local LLM
inference works in airplane mode; distraction nudges have cooldowns and override;
commands have explicit outcomes; evaluation reports failures and latency; a 3–5
minute video and complete attribution are ready. NPU/Office Kit are separately
marked verified or unavailable. Registration and submission remain user-led until
the user explicitly authorizes a completed dashboard action.
