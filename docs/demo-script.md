# Mira — current research demo and application pitch

Prepared 2 October 2026. **Reviewable recording script; not a claim that every shot is already captured.** Target a 3–5 minute concept/research pitch, subject to the actual dashboard requirements. The public guide's presentation rubric describes a 3–5 minute pitch; no authenticated application upload format, word limit or deadline is assumed. [Official guide](https://iqoo.reskilll.com/guide).

Keep a visible **“Pre-event research prototype”** label. Current v0.9 source
`6e483aaf9e42889794ed77c272b8a912539cfc7c` has 127 JVM tests, zero lint errors/62 warnings and
inspected/installed APK identity. Floating Mira is implemented but untested on the
phone: label its visual as **“source concept; actual overlay proof pending”** until
user-granted Show/drag/Hide/Pause and lock/notification/revocation tests pass.
The Qwen/prompt/native/v0.8 gate is unchanged. [Floating contract](floating-companion.md).

Historical v0.8 build has 119 passing JVM tests, zero lint errors and 59 warnings. Both APKs passed packaging inspection and the light APK installed with matching APK/private-model hashes. Physical v0.8 command/countdown outcomes remain pending. The completed frozen 100-request/50-family host test improved gated strict correctness 64→72/100 with zero wrong accepts, but only 12/40 supported successes and 28/40 false abstentions, including nine gains and six losses. Its model-facing gate adds whole-request forms and deterministic English-number/clock slots while leaving Qwen weights/prompt/native unchanged. [Command contract](natural-commands.md). Historical v0.7 has 105 tests/59 lint warnings with timer phone proof pending unlock; source-bound v0.6 Start/Pause remains historical. Read [status](status.md), [timed focus](timed-focus.md) and [application draft](application-draft.md) before filming.

## Copyable opening

“I pick up my phone for one task and lose the reason I opened it. Mira is a quiet productivity companion that helps me return to my own plan. I choose the task and limits, review her proposed actions, and can pause at any time. This is our dated pre-event research prototype. The local model runs on phone CPU; voice, permissioned monitoring and iQOO deployment still need physical verification.”

## Four-minute research recording sequence

| Time | Visual / action | Narration and proof boundary |
|---|---|---|
|0:00–0:25|Original companion, project title and a synthetic task illustration.|“Mira helps me follow my own goal. The same app can support work or distract me, so the limits are mine.” State Productivity as the proposed track.|
|0:25–0:55|Show Set up Mira on an unlocked app if available; otherwise use a clearly labelled readiness diagram.|“Optional features have visible setup. In the v0.6 phone test, usage, notifications and microphone were off; opening setup changed none of them.” Do not enable permissions as an unannounced filming step.|
|0:55–1:30|Show the reviewed command flow, with source-bound v0.6 evidence card; record a fresh own-app Start/Pause only after its current proof gates pass.|“Qwen proposes an action. The original-request gate and my confirmation decide whether it runs. Historical v0.6 Start and Pause changed the session checkpoint; a wrong alarm-cancellation proposal was rejected.” Label 17.323s/1.814s/1.655s as three historical typed observations; no ASR or p50/p95 claim.|
|1:30–1:55|Show the 25-minute review and textual examples “Focus for twenty-five minutes” / “Take a study break,” or a diagram labelled “v0.8 source — physical verification pending.”|“A complete request is checked, including its number slots, before I review the action. Timed focus preserves remaining time when paused; recovery stays paused.” Do not present a diagram as a completed phone countdown. If the short physical test later passes, insert its exact source-bound outcome.|
|1:55–2:25|Show the synthetic decision lab and one contribution/ablation; label invented inputs.|“Repeated nudges use a bounded rule. This separate tiny trained head exposes contributions, and a shadow panel evaluates complete permitted summaries. Synthetic training accuracy is not human productivity accuracy.” No charge, monitor or real-event success inferred from the sandbox.|
|2:25–3:05|Run the laptop consumer on a generated Java synthetic export; show only aggregate report and byte/policy identities.|“A deliberate private summary can support deeper laptop review. Here the actual Java export is understood by the Python consumer, which replays our existing policy without retraining.” State temporary local-file transport, 15 bridge tests and synthetic interoperability; **actual Office Kit transfer is pending**.|
|3:05–3:35|Show the new frozen 100-request host comparison, supported coverage and paired gains/losses.|“The same model and a new validator rejected all 60 unsupported requests in this set. Supported successes rose from 9 to 12 of 40; 28 still abstained. We gained nine cases and lost six, so zero observed wrong accepts does not establish broad reliability.” Label host CPU/no actions. Raw Qwen scored 29/100 and never abstained on those unsupported requests; preserve older 58-case failures separately.|
|3:35–4:00|Show pause, simulated-points disclosure, repository/evidence links and remaining deployment gates.|“We have a local model, reviewed focus actions and a working laptop review path. Next are real permissioned monitoring, local speech and actual iQOO/Office Kit verification. No money moves. Eligible event code and submission remain separate steps.”|

## Short on-camera technical brief

“Qwen3.5-0.8B Q4_0 runs inside Android through a pinned llama.cpp CPU bridge. Typed requests pass through a closed action validator and explicit review. A compact explainable policy handles repeated decisions; the laptop receives a bounded private export only when I choose to share it. We report the backend actually tested, retain failures and separate synthetic experiments from real phone outcomes.”

The measured frozen-Qwen-representation classifier is optional research. If mentioned: “A separately trained head classified 76 of 90 synthetic held-out requests correctly versus 46 for generation. That gain did not improve accepted phone commands under our current validator, so we kept it out of the app.” Explain the brittle confidence threshold if discussing rejection. Do not call it internal Qwen-weight fine-tuning, a deployed improvement, phone speedup or general mechanistic understanding. [Results](intent-head.md).

## Historical video and eligible event demo

The published **4:53 v0.3 research pitch** remains a preserved baseline: [video release](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.3), [editable narration](research-pitch-script.md). It uses original title cards, graphics and a sanitized app still. It is not continuous live phone footage and does not prove v0.6/v0.7/v0.8 commands, timed focus, actual voice, Office Kit or NPU. Keep its historical label when sharing; do not overwrite the asset or imply the updated script has already been filmed.

For an eventual eligible event demo, create the competition code in the 9–11 October window unless the organizers explicitly authorize reuse. Add a live segment only after its specific proof passes: actual consented app use and notification Stop; local speech transcript and reviewed Clock outcome; USB-disconnected/airplane-mode run with exact model/backend identity; actual eligible iQOO operator placement; and paired Office Kit source/received checksum plus laptop review. A generic ADB copy, a renderer fixture or an SDK label does not establish those results. [Rules](../hackathon.md), [deployment gates](snapdragon-deployment.md), [Office Kit workflow](officekit-export-workflow.md).

## Recording and handoff checks

- Confirm authenticated dashboard requirements, admission and cutoff. The user's preparation target is not an official deadline. Do not invent fields or submit placeholders.
- Record only synthetic own-app content with the phone unlocked and an explicit action review. Mask system notifications, account identities, debug serials, contacts and unrelated screens. Keep raw private recordings/exports out of Git.
- Use the exact installed APK/source/model hashes in the evidence manifest. A source update does not change which binary an old recording demonstrates. Keep historical latency observations and host results separately labelled.
- Show denied/unavailable features truthfully; type a command when ASR is unavailable. No cuts may imply a failed action succeeded. A requested timer/Clock launch requires a verified result before claiming completion.
- Keep virtual-points/no-money labels visible. Focus timer deep sleep and process loss can delay visible completion; no exact-alarm or 24/7 guarantee.
- Review the final 3–5 minute export for readable text, complete narration/captions, privacy, audio and playback. Current natural-command/timer/bridge additions require a new recording, not a renamed v0.3 video.
- Submit only permitted assets after human review and organizer eligibility clarification; preserve the actual acceptance receipt. No submission has been performed by preparing this script.
