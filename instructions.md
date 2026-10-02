# Instructions — FocusPilot

FocusPilot is the working name for an opt-in, local Android productivity assistant.
It observes permitted phone context, makes fast bounded decisions, explains its
reasoning, and helps the user act through voice and a small set of reliable tools.

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
- Learning demo: user labels a few sandbox states; retrieval uses those examples to guide
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
Usage Access and Accessibility by hand after reading the app's permission screen.
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

Keep a small LLM for understanding varied commands; keep repeated decisions in a
compact classifier. Train offline from consented sandbox data. Fine-tuning is a
stretch gate after a baseline works, with a frozen held-out set and reported gains.
Few-shot retrieval, fine-tuning and in-context examples are different methods; name
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
