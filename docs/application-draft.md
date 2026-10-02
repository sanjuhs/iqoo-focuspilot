# Mira / FocusPilot — reviewable application draft

Prepared 2 October 2026. **Pre-event research; not submitted.** The following copy is ready to adapt once the authenticated dashboard and organizer requirements are known. No team details, required field names, word limits, admission, deadline or permission to reuse pre-event code are assumed. Proposed primary track: **Productivity**.

## Copyable project summary

Mira is a quiet local productivity companion for Android. It helps people return to the task they intended to do: choose a focus goal, review a short command, start or pause a session, and inspect a nudge based on their own app-use limits. An original animated companion makes the experience friendly, while a quantized open-source Qwen model understands bounded commands on the phone. Observation and voice are optional, actions require review, and accountability uses virtual points. A private summary export lets a laptop review policy scores without copying raw goals or screen content. Our pre-event prototype establishes the CPU model and reviewed focus workflow; permissioned monitoring, voice and actual iQOO/Office Kit deployment remain verification work.

## Problem and intended end-user utility

People open a phone for a task, drift into a feed and forget why they opened it. The same app can be productive or distracting depending on the person's goal. Mira is designed to use the user's selected app, declared limits and manual feedback instead of treating every minute of social media as wasted time.

The intended everyday flow is a reviewed focus countdown, a visible opt-in session, an understandable nudge and an easy pause/override. Push-to-talk is intended to create an editable command draft followed by local understanding and confirmation. The laptop bridge is intended for a deliberate summary handoff and deeper review. These are product goals; the verified subset is listed below.

## Copyable technical brief

The Android research app packages Qwen3.5-0.8B Q4_0 and runs it through a pinned llama.cpp ARM64 CPU bridge. The original-request validator checks a closed action allowlist and numeric slots before user confirmation. A deterministic shortcut parser remains available. Recurring budget nudges use explicit rules and separate permission/focus/cooldown gates; an inspectable 65-parameter positive-weight head supplies shadow explanations. Private few-shot labels are scoped to the original goal and settings. The laptop consumer strictly validates a bounded export, groups exact original contexts and replays the pinned policy on Python CPU, emitting only private aggregates and provenance hashes. All accountability points are simulated. Snapdragon NPU execution and actual Office Kit transport are not established.

## Current evidence and known limits

- **v0.7 research build:** timed focus implementation accepts one duration written in digits from 1 second to 120 minutes, retains remaining time across pause/resume and recovers paused after process loss. Integrated build: **105 JVM tests**, zero lint errors and **59 warnings**. Actual v0.7 countdown verification is pending phone unlock/own-app foreground readiness. [Timer contract and artifact identity](timed-focus.md).
- **Historical v0.6 phone proof:** exact source/APK/model/native identities bind typed Start and Pause to 17,323 ms and 1,814 ms. Both were reviewed and confirmed; session state changed active then paused. Alarm cancellation took 1,655 ms, was misclassified by Qwen and independently rejected. Usage stayed off, permissions were unchanged and the final virtual balance was 100. These are three observations, not p50/p95 or v0.7 timing evidence. [Phone report](command-readiness-phone.json).
- **Command reliability:** frozen 58-case host raw intent correctness is 25/58; gated correctness including abstentions is 49/58; supported-command correctness is 16/23. Two accepted mismatches are retained. v0.7 repairs are known-case regressions, not an independent accuracy gain. The raw model is unsuitable for autonomous phone actions. [Evaluation](command-reliability.md).
- **Laptop compute:** 15 bridge tests and actual Java-rendered synthetic export → Python consumer interoperability pass. This establishes file/schema/compute compatibility, not real app-use export or Office Kit transfer. [Workflow](officekit-export-workflow.md), [interop evidence](bridge-java-interop.json).
- **Explanation research:** the small head was trained on invented labels, not human productivity. Laptop Qwen activation interventions found no reliable steering advantage; observations and negative results are retained. No general mechanistic-understanding claim is made.
- **Pending physical proof:** on-device ASR/TTS, Clock outcome, user-enabled monitoring/OEM lifecycle, disconnected offline operation, iQOO hardware/NPU and Office Kit pairing/transfer. Broad cross-app control and IoT are not demonstrated. The existing 4:53 v0.3 video is a historical concept pitch with graphics/stills, not current live-feature evidence. [Status](status.md), [demo script](demo-script.md).

A separate 7,175-parameter classifier trained on **frozen Qwen representations** scored 76/90 raw intents versus 46/90 for generation on the same synthetic held-out set. Validation-selected abstention reduced unsupported false accepts in that set, but relies on numerical saturation; the current action gate gives only 15/65 correct supported actions versus 17/65 for generation. It remains unpromoted and does not fine-tune internal Qwen weights. [Measured research](intent-head.md).

## Eligibility and submission boundary

The public Finale dates are 9–11 October 2026, and the guide/Terms require competition work within the allowed event window. The current implementation is dated preparation research. Eligible competition code must be created in that window unless the organizers explicitly authorize reuse. An APK, public repository or application draft does not establish eligibility or acceptance. Confirm the authenticated dashboard's actual requirements and cutoff before adapting or submitting this copy. [Rules and rubric](../hackathon.md).
