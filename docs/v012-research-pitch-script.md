# FocusPilot v0.12 — research demo narration

Production plan, 3 October 2026. This script is prepared for an edited recording;
no new footage or narration audio has yet been verified for this version. Record
only synthetic content in FocusPilot's own screens. Crop the keyboard and system
bars out of exported shots. Use deliberate holds rather than accelerated inference.
Keep numerical overlays bound to the recorded request or clearly labelled history.
Record the guide after its synthetic setup, and the model after loading and typing.
Guide footage shows explicit Speak and the terminal engine status, without phone
audio. Model footage shows Understand and its proposal, without action review or
confirmation. Mark/Undo is checked before recording and is not depicted as filmed.
Use labelled animation for unfilmed interaction choices and historical tensors.
Reserve 15–25 seconds of additional reading holds across the eight scenes;
measure final encoded duration rather than presenting estimates as results.

Selected app source: `24f10b62a4a62c22ad6db90ac6339f29e2426dbd`.
Evidence: [verified status](status.md), [v0.12 readback](guide-readback-phone.md),
[historical activation comparison](capture-benchmark-phone.md),
[synthetic policy](policy-baselines.md), and [remaining gates](remaining-deliverables.md).
This is pre-event research, not an eligible or accepted competition submission.

## Scene 1: Meet Mira

> Your phone is where work begins, and where distraction can swallow half an hour. FocusPilot helps you find your next useful step without turning productivity into punishment.

> Meet Mira, our original, friendly goth companion. Her job is simple: keep your chosen goal close, make the next step feel manageable, and give you controls you can understand.

> This edited recording presents our Android research prototype, version zero point twelve: a personal assistant that responds locally and leaves the final choice with you.

Visual: Original Mira portrait and gentle idle motion → clean title → cropped own-app dashboard; overlay “v0.12 · pre-event research · Nothing development phone”.

## Scene 2: Make the task smaller

> Start with a goal you care about. Our demonstration goal: prepare a short focus demo. Break that job into three small steps.

> Open my notes, draft three points, and review the draft. This checklist is already saved beside the focus task. These are authored instructions; the model has not invented or executed them.

> Mark and undo keep progress editable. Explicit readback reaches the engine's completion status, with a clear Stop control. Phone audio is absent, so this recording does not prove speaker audibility.

Visual: Actual cropped own-app guide clip begins after setup: goal “Prepare a short focus demo”, authored steps “Open my notes”, “Draft three points”, “Review the draft” → explicit Speak → terminal completion status. No Save/Mark/Undo footage or phone audio; label any separate progress illustration as product capability, verified before recording.

## Scene 3: Understand on the phone

> The model is loaded, and stop focus is already typed. Tap Understand. Qwen three point five, zero point eight billion, quantized to Q four zero, processes those words on the phone.

> Our pinned runtime uses the CPU. It produces a structured intent proposal, while Android code independently checks the original request. The screen separates the model suggestion from the reviewable action.

> An earlier version twelve test reported one point seven four nine seconds of native inference for this request. That is one historical observation, not a promised response time for every device or command.

Visual: Actual cropped model clip starts with model already loaded and “Stop focus” already typed → Understand → actual proposal. No keyboard/loading or Review/Cancel/Confirm footage. Preserve actual metrics; label any historical 1,749 ms figure separately.

## Scene 4: Keep the action yours

> Understanding a sentence does not automatically change your phone. This diagram explains review choices: compare your request with the proposed action, or cancel before anything runs.

> Confirmation is a separate decision. Supported commands cover focus controls and a small Android tool allowlist. Requests outside that boundary need clarification rather than an improvised chain of taps.

> This makes everyday help easier to inspect. Our accountability balance is virtual points only. It illustrates a commitment you chose; this prototype never withdraws money, makes purchases, or sends messages for you.

Visual: Explicitly labelled animated diagram: request → independent gate → review choices Cancel or Confirm. No actual dialog footage, filmed button press or executed action; distinguish the diagram from the model recording.

## Scene 5: Look inside carefully

> Optional activation capture opens another window into the local model. The viewer exposes selected tensor summaries from actual inference, alongside the command result.

> Previous version eleven phone trials displayed four finite summaries consistently. Their labels, dimensions, and numerical ranges are observations of computation. They do not tell us that a neuron means focus or distraction.

> Understanding a mechanism requires interventions and repeatable behavioral effects. Our viewer supports those experiments. We keep that research separate from testing whether the requested command works.

Visual: Clearly labelled historical v0.11 evidence diagram: four finite tensor summaries were observed outside the selected model clip. Present recorded facts and observational limits; do not imply all four summaries appear in new footage or invent tensor output.

## Scene 6: Explain recurring decisions

> Recurring coaching has a different path. Users would choose the app budget and opt into permitted usage context. Explicit rules currently govern nudges, with permission, focus, and cooldown checks.

> A separate sixty five parameter network was trained on synthetic examples. Its connection weights are nonnegative, its biases can be signed, and its inspector shows contributions and controlled ablations.

> That network remains in shadow mode. Agreement with invented labels does not prove human productivity. Real usefulness needs consented testing with real sessions.

Visual: Own-app Decision Lab or labelled synthetic policy diagram → contributions and ablation; persistent “synthetic training · shadow only · signed biases” caption.

## Scene 7: Let others verify it

> FocusPilot is open source. The repository contains build instructions, model attribution, reproducible test procedures, and evidence tied to specific source revisions and packages. Failed experiments stay visible too.

> The selected Android source has one hundred forty eight passing JVM tests. Physical phone records answer narrower questions, such as checklist persistence or a reviewed command, with their limits documented.

> Keeping those layers distinct helps others reproduce and improve the work. A useful assistant should earn trust through checkable behavior and a welcoming interface.

Visual: Repository and source identity card → “148 JVM tests” → physical evidence labels; keep private phone captures, credentials and weights outside repository graphics.

## Scene 8: Take it to iQOO

> Our next step is the iQOO device: measure this model on the supported hardware, verify any Snapdragon NPU backend, and demonstrate the actual Office Kit connection to deeper laptop compute.

> Voice transcription, permissioned monitoring, floating mode, and disconnected operation still need verification. Eligibility and submission details need confirmation. We will demonstrate those capabilities with supporting evidence.

> The product direction remains clear: a warm companion, local understanding, visible next steps, and actions you approve. FocusPilot helps turn the phone from a source of interruption into a place to make progress.

Visual: Mira beside “Next: iQOO · verified backend · Office Kit · voice” → repository address `github.com/sanjuhs/iqoo-focuspilot` → calm final portrait and product name.
