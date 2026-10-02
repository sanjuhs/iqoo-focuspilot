# Demo and application video specification

Prepared 2 October 2026, Asia/Kolkata. **This is a storyboard, not a record of completed capabilities.** Read [architecture.md](architecture.md), [hackathon.md](../hackathon.md), and [status.md](status.md) before filming. The official guide calls for a compelling 3–5 minute pitch. Target **4 minutes**. [iQOO event guide](https://iqoo.reskilll.com/guide)

The rendered pre-event research pitch uses [this editable narration](research-pitch-script.md)
and `scripts/render_pitch_video.py`: original graphics, a sanitized app still,
measured local narration and captions. It explicitly labels research, simulations
and remaining work. It is not a continuous live phone demo or an eligible event entry.

## Two different deliverables

The user's 3 October morning target is an early concept/application handoff unless the signed-in dashboard explicitly requires something else. For that video, show the problem, architecture, research, and actual completed diagnostics. Label storyboard screens “Proposed experience.” An actual pre-event prototype under `prototype/android` may be shown with its real research date and explicit “Pre-event laboratory prototype; not event-created submission” label. The current model lab has actual Qwen3.5 CPU inference; dashboard shortcuts and recurring nudges use deterministic logic. Identify the component actually shown. Do not imply a fine-tuned language model, NPU run, or Office Kit integration exists.

The Grand Finale demo is prepared during the official 9–11 October build window, subject to the dashboard/organizer rules recorded in hackathon.md. It can use the live sequence below only after the respective proof gates pass. A required early working-app submission would conflict with the event-window interpretation and needs organizer/dashboard clarification; record that outcome before changing scope.

## Four-minute final-demo sequence

| Time | Visual and action | Spoken point | Required proof / rubric |
| --- | --- | --- | --- |
| 0:00–0:25 | Presenter and phone; show a small focus goal | “I pick up my phone for one task, drift into a feed, and lose the reason I opened it. This assistant helps me return to my own plan.” | Concrete Productivity problem; novelty and impact |
| 0:25–0:50 | Start focus, choose a distracting app, enable observation, show pause control | “I choose the apps and limits. My usage and decisions stay local. This balance is simulated focus accountability.” | Working consent and pause; end-product quality |
| 0:50–1:30 | Open opted-in feed; a short sandbox limit expires; nudge appears | “The app sees the session exceeded my limit. It asks whether I want a break or to return to work.” | Label “Demo limit: 15 seconds”; disclose sandbox acceleration; no real-money debit |
| 1:30–2:00 | Open decision inspector with observed features, activations, score and policy reason; change one feature | “This small positive-weight scorer lets us inspect how a feature changes the nudge score. The language model routes the request separately.” | Actual ablation output; show values rather than invented confidence; technical depth |
| 2:00–2:35 | Push-to-talk “Set a timer for five minutes” or “Set an alarm for 7:30 AM”; clock opens; verify created item | “A local decision model selects an allowed task, then Android's clock handles it.” | Offline speech proof if claiming local voice; receiver state, native adapter, action completion |
| 2:35–3:05 | Airplane mode, laptop physically disconnected; repeat typed or voice command; show backend panel | “This verified component runs on the phone. Here are the model revision, runtime, backend, and measured latency.” | On-device AI / technical depth; explicitly CPU/GPU/NPU as measured |
| 3:05–3:30 | Reconnect event Office Kit; send a permitted heavier task; show phone and laptop responses | “When I ask for a larger plan, the paired laptop helps. Core focus tasks still work without it.” | Official Office Kit trace. If absent, replace with transparent scope/limits instead of claiming rubric credit |
| 3:30–4:00 | Pause and delete local history; show repository, evidence, measured result and next step | “Fast decisions, visible reasons, and a stop button. We built a focused assistant that helps people follow their own goals.” | Working product and concise finish; demo and presentation |

Do not call the phone “Snapdragon NPU powered” unless runtime/profiler evidence identifies accelerator execution for the demonstrated component. If only the tiny scorer runs on NPU, say exactly that. If speech is unavailable offline, type the command and explain the current limitation. A laptop-run model controlling a USB phone must be labeled as laptop inference.

## Early concept/application adaptation

Keep the same four-minute arc, replacing unbuilt operations with explicitly labeled storyboards, or a verified pre-event research prototype with its origin and limitations visible:

1. 0:00–0:40: user problem and Productivity track choice.
2. 0:40–1:30: three storyboard scenes: focus, explained nudge, voice alarm.
3. 1:30–2:20: architecture and research: Cua interaction loop, Laya/Kev typed decisions, native Android adapters.
4. 2:20–3:10: actual USB/device diagnosis and proposed model/NPU proof plan; only report verified diagnostics.
5. 3:10–4:00: event build schedule, simulated accountability, offline-first intent, and limitations.

Suggested truthful opening: “This is our proposed build for the iQOO Grand Finale. Today we have completed research and preparation; competition implementation is planned for the eligible event window.” If showing the laboratory app, add: “This dated research prototype validates the phone workflow; it is pre-existing work and currently uses the backend named on screen.” Adjust implementation claims only when the verification record changes.

## Recording checklist

- Obtain the dashboard's exact application/video requirements and submission deadline before exporting. The personal 3 October target is not proof of an official cutoff.
- Film a clean test account and sandbox feed; hide notifications, contacts, debug serial numbers, tokens, and unrelated apps. Avoid recording passwords or banking apps.
- Use a new alarm/timer that cannot interrupt an important existing one; show the result and delete the test item afterwards.
- Capture a continuous offline proof segment with backend and model identity visible. Do not cut away from failed actions and imply they succeeded.
- Show simulated balance text on screen while discussing penalties. No money moves.
- Benchmark before narration: report sample count, hardware, p50/p95, warm/cold status, and whether speech/action time is included. Targets are not measurements.
- Use the app's own phone-control path. ADB commands, prerecorded screens, or laptop-driven gestures must be identified if included.
- Record official Office Kit activity only after integration. Generic screen mirroring or USB connection is not equivalent evidence.
- Keep private raw phone recordings outside Git; place a sanitized exported video or link in the submission evidence only after review.
- Export a readable 1080p MP4 if the dashboard accepts it; use clear voice and captions; verify duration, audio, upload playback, repository URL, and permissions.

## Evidence attached to the final submission

Maintain a small sanitized manifest: source commit and APK checksum; model/revision/checksum/license; phone model/SoC/API; runtime and active providers; fallback nodes; offline-run trace; command evaluation summary; nudge-scorer intervention results; Office Kit trace if integrated; limitations; video URL. Never attach .env, personal usage history, raw private recordings, or third-party model weights without license review.

The video must match the manifest. Useful honest limitations include: only seven supported intents; monitoring only while supported services are active; access can be revoked; offline speech support varies; UI automation may fail on custom or secure views; accountability is simulated; mechanistic analysis covers the tiny scorer, not the entire LLM.
