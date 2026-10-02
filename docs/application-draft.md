# Direct-entry concept draft

Prepared 2 October 2026. Draft for the user to adapt to dashboard fields; not
submitted. Public application requirements and permitted pre-event assets need
confirmation. This describes the intended product, not completed functionality.

## Name and track

**FocusPilot — a local productivity copilot for your phone.**
Primary track: **Productivity**. Team/category/member details: user to supply.

## Problem

People open a phone for a useful task, get pulled into feeds, and lose the original
goal. Existing app timers often ignore context and cannot help finish the task.
Instagram can be work, so productivity should follow the user's own intent and
limits rather than a model's blanket judgment about an app.

## Proposed solution

An opt-in Android assistant that keeps a focus goal, notices the user's configured
limits and supports short voice commands. A quantized Qwen3.5-0.8B model is the
primary command-understanding candidate; Laya is a bounded-decision comparison.
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
phone: Nothing A059, Android 16/API 36. A dated pre-event research prototype is
being developed; it is not represented as event-written code. Android LLM/NPU,
Office Kit, real-phone learning gains and final video remain unverified until
[status.md](status.md) records evidence. Real-money deduction is outside scope.
Competition code must meet published event-window rules.

## Details to fill from the dashboard

Application deadline, text limits, team/category information, required links,
whether an early concept video is required, its duration/file constraints, and the
organizer's policy for pre-event research code. Do not accept Terms or submit
incomplete placeholders automatically.
