# Direct-entry concept draft

Prepared 2 October 2026. Draft for the user to adapt to dashboard fields; not
submitted. Public application requirements and permitted pre-event assets need
confirmation. This describes the intended product, not completed functionality.

## Name and track

**FocusPilot, with Mira — a quiet local productivity companion for your phone.**
Primary track: **Productivity**. Team/category/member details: user to supply.

## Problem

People open a phone for a useful task, get pulled into feeds, and lose the original
goal. Existing app timers often ignore context and cannot help finish the task.
Instagram can be work, so productivity should follow the user's own intent and
limits rather than a model's blanket judgment about an app.

## Proposed solution

An opt-in Android assistant that keeps a focus goal, notices the user's configured
limits and supports short voice commands. A quantized Qwen3.5-0.8B model is the
primary command model, already running on CPU in the research app; Laya is a laptop comparison.
A separate positive-weight policy explains why a nudge is offered. Android checks
permissions and action arguments, then performs approved tasks. A virtual
commitment balance illustrates accountability without moving real money.

## What makes it different

Fast bounded actions, an inspectable tiny model and focused activation experiments
in the actual command model. Test a narrow hypothesis with ablations/patching and
unseen commands; an activation visualization alone does not establish causality.
The local core is intended to work offline. User examples personalize decisions in
a sandbox; any training gain is measured on a separate holdout.

## Technical approach and planned demo

Qwen GGUF + instrumented llama.cpp CPU baseline, then verify any acceleration.
Android usage-access consent and native clock intents provide the first actions.
Show focus → sandbox overrun → explained nudge → simulated penalty → alarm request
→ verified clock outcome. Repeat offline and identify the actual model/backend.
Show an intervention only if it passes the experiment protocol. Use official Office
Kit for a heavier laptop task only after actual pairing is verified.

## Current readiness and honest limits

Research, architecture and Android USB authorization are complete. Development
phone: Nothing A059, Android 16/API 36. The dated pre-event research app runs
Qwen3.5-0.8B Q4_0 on CPU, with I8MM selection confirmed and warm smoke requests
around 1.65–1.87 seconds. A reviewed proposal started focus; Stop paused it. A
friendly original animated goth companion, selected tensor observations, synthetic
trained policy sandbox and local few-shot label sandbox are implemented. Twenty-six
Android tests pass. Controlled laptop activation experiments found no reliable
semantic steering; that negative result is retained.

A narrated research pitch is available from [the editable script](research-pitch-script.md).
This is preparation, not event-created code. Full offline physical demonstration,
background permission/lifecycle tests, voice/clock completion, NPU, Office Kit and
real-user learning gains remain pending. Real-money deduction is outside scope.
See [verified status](status.md). Competition code must meet event-window rules.

## Details to fill from the dashboard

Application deadline, text limits, team/category information, required links,
whether an early concept video is required, its duration/file constraints, and the
organizer's policy for pre-event research code. Do not accept Terms or submit
incomplete placeholders automatically.
