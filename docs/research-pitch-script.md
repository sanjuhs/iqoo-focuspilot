# Mira / FocusPilot: a quiet local productivity companion

**PRE-EVENT CONCEPT / RESEARCH PITCH — 2 October 2026.** This recording is a research demonstration, not an eligible event-created competition submission. The public Grand Finale is 9–11 October 2026. Do not remove the preparation label or present this implementation as event-written work.

Editable narration source for `scripts/render_pitch_video.py`. Each quoted paragraph is one measured speech segment and one caption. The renderer uses installed macOS `say`, Pillow and FFmpeg; it does not call an API or operate the phone. The inspected `artifacts/mira-home-v2.png` is a research UI still, not a live demonstration; system status/navigation bars are cropped out. Original `prototype/companion/avatar.svg` supplies the title artwork where local SVG thumbnail rendering is available.

Evidence snapshot: [verified status](status.md), [on-device model research](on-device-model.md), [synthetic policy results](../prototype/policy/synthetic-model-results.json), and [official guide](https://iqoo.reskilll.com/guide). Initial phone timings were **19.853 seconds first / 4.107 seconds next**, only two baseline observations. The optimized five-case CPU smoke recorded **13.521s cold, 1.646s warm, 1.719s captured, 1.724s negated and 1.663s compound**; the last two raw model outputs were wrong but rejected by the independent gate, with no actions executed. These are single smoke observations, not averages or percentile benchmarks. A separate reviewed phone proposal was confirmed to start focus, then Stop produced a paused checkpoint. Phone activation summaries are observational. A separate 108-trial laptop causal experiment had byte-identical restoration controls but no reliable selected-channel steering advantage. The 65-parameter network scored **98.33% on synthetic held-out data**, not real-world productivity outcomes. A 32-label local few-shot sandbox has tests and a 720-case grouped synthetic comparison: answered accuracy improved, roughly 70% coverage, lower overall correct count due to abstention. Phone label save/persistence/delete are verified; live-policy integration and fine-tuning remain pending. Background-service permission/device verification, Office Kit and NPU remain pending.

Render with:

```sh
python3 scripts/render_pitch_video.py
```

Outputs: ignored `artifacts/pitch-research.mp4`, editable captions `pitch-research.srt` and `.ass`, narration `.wav`, storyboard frames and a render manifest. Default voice: installed Samantha, 190 words/minute. The generated duration must be between three and five minutes. Narration and caption timing are measured from each spoken segment rather than guessed from a target length.

## Scene 01: A quiet local companion

Visual: Original Mira portrait, prominent product title, compact research label; a warm introduction rather than a hardware claim.

> Meet Mira, the face of FocusPilot: a quiet, local productivity companion for your phone.

> The goal is simple: help you return to what matters, without turning a short distraction into a punishment.

> This is our pre-event concept and research prototype, with working pieces and clearly marked work still ahead.

## Scene 02: The moment we want to help

Visual: A task leads to a small detour; a gentle return path appears. A diagram illustrates the product idea, not measured distraction reduction.

> You pick up your phone for one useful task, then a familiar app pulls you into a longer detour.

> Mira starts with your goal and your chosen app budget, instead of deciding that every break is bad.

> A useful assistant should support your intention, and leave the final choice with you.

## Scene 03: A product you can pause

Visual: Inspected current phone UI still, cropped to app content, beside three commitments: choose your limit, start focus, pause whenever needed. Rubric cue: product quality, 30%.

> Our Android prototype has a focus session, local settings, an event trail, and an original animated companion.

> You can reduce motion, mute her voice, hide the artwork, or stop focus while keeping the controls easy to reach.

> Product quality means the everyday loop feels useful and dependable, before we add more ambitious automation.

## Scene 04: From a request to an approved action

Visual: Request → local model → independent review → Android action. Stages appear in order; the final stage is labelled confirmation required.

> Ask Mira opens the local language-model lab, where a natural request becomes a small action proposal.

> An independent gate checks the proposal before review. A confirmed phone proposal started focus, and Stop paused it.

> Quick typed commands remain available, and alarm requests go through Android's Clock flow without claiming the alarm was verified.

## Scene 05: Two speeds, one accountable assistant

Visual: Separate language and fast-policy lanes converge on bounded actions. Rubric cue: novelty and impact, 20%.

> We separate understanding a new request from making the same small decision repeatedly.

> A quantized language model handles the first lane; a compact, explainable policy handles recurring focus decisions.

> Today's recurring policy uses hand-set positive weights, visible contributions, a cooldown, and virtual points only. No real money moves.

## Scene 06: Actual phone inference, honest timing

Visual: Optimized cold13.521s / warm1.646s / captured1.719s bars; baseline19.853s /4.107s kept in a small footnote. Negative/compound wrong outputs visibly stop at the validator. Rubric cue: creative phone use, 15%.

> Quantized Qwen three point five, zero point eight billion now runs inside the Android process on the Nothing development phone.

> Our optimized five-case CPU smoke recorded thirteen point five two one seconds cold, one point six four six warm, and one point seven one nine with capture.

> These are single observations, not a robust benchmark. Two negated or compound requests were misclassified by the model, but the independent gate rejected both without executing an action.

## Scene 07: Look inside, without overstating it

Visual: Phone tensor → measured summary → observation; separate laptop intervention lane shows108 trials and16 byte-identical restoration controls, but no reliable steering advantage. Rubric cue: technical depth, 15%.

> The phone captures selected actual activation summaries through an explicit research switch. These are observations, not proof of semantic causes.

> Separately, we ran one hundred and eight laptop intervention trials. Sixteen restoration controls matched the full logits exactly.

> Selected channels did not steer decisions reliably better than random controls. That negative finding is useful evidence, not a claim that we decoded the model's meaning.

## Scene 08: A tiny trained decision laboratory

Visual: Six input nodes connect to eight hidden units and one output, then reveal 65 parameters and 98.33% synthetic holdout accuracy.

> Separately, we trained a sixty-five parameter positive-weight network on synthetic sandbox examples.

> It reached ninety-eight point three three percent accuracy on its synthetic held-out set, with contributions and intervention tools we can inspect.

> That result tests a toy decision task. It is not real-world productivity accuracy, and this trained sandbox does not replace the recurring hand-set policy yet.

## Scene 09: Stay present, with permission

Visual: Explicit opt-in → usage access → visible notification, with a large Stop control. Clearly mark background permission/device testing pending.

> The background focus monitor is implemented as an opt-in foreground service, with a visible notification and a Stop action.

> Usage access and notification permissions must be allowed first; the companion does not keep a microphone open or capture the screen.

> Background permission and device testing are still pending, and Android power rules mean we cannot promise uninterrupted, twenty-four-hour operation.

## Scene 10: The phone and laptop bridge

Visual: Development phone and laptop, with Office Kit and NPU paths dashed and marked pending. Rubric cue: Office Kit usage, 10%.

> The Nothing phone proves a development path, while the competition experience must run and be demonstrated on iQOO hardware.

> Office Kit is a separate phone-to-laptop bridge, and it has its own judging weight.

> Actual Office Kit pairing and Snapdragon acceleration are still pending; a USB debugging connection is not evidence that either one works.

## Scene 11: Learning comes after a reliable baseline

Visual: 32 local labels → neighbor retrieval →720 grouped synthetic cases; answered accuracy, roughly70% coverage and fewer overall correct cases are shown as a tradeoff, not a fabricated improvement curve.

> Our local few-shot research sandbox supports thirty-two labels and neighbor retrieval, with eight tests. Phone labels can be saved, restored, and deleted.

> Across seven hundred and twenty grouped synthetic cases, answered accuracy improved, but coverage was about seventy percent and overall correct answers fell because it abstained more.

> This is a research sandbox, not fine-tuning or live policy. Real-user productivity benefits remain unproven.

## Scene 12: A focused Productivity entry

Visual: Three score themes, with all six published weights distributed across meaningful groups rather than a dense table. Rubric cue: demo and presentation, 10%.

> Productivity is our primary track: one repeatable loop, from a chosen task to a gentle nudge and an approved next action.

> The rubric rewards product quality and impact, real phone use and technical depth, Office Kit use, and a clear demonstration.

> We will show working behavior, explain what is simulated, and keep the hardware and learning claims tied to reproducible evidence.

## Scene 13: Preparation and competition are different

Visual: Dated research preparation → 9–11 October event window, with an explicit boundary. Event rules source appears beside the boundary.

> This video and repository are pre-event research, prepared before the public Grand Finale on October ninth to eleventh, twenty twenty-six.

> The published rules require original competition work during the event window and do not allow shipping a pre-built product as that submission.

> We will keep preparation clearly labelled and create eligible event code in the allowed window, unless organizers explicitly approve reuse.

## Scene 14: Make room for what matters

Visual: Original Mira portrait returns; the final task path completes with three clear commitments: local, understandable, user-controlled.

> Mira is a small companion with a practical ambition: less friction between what you intend to do and what your phone helps you do.

> Our next steps are measured inference improvements, permission-tested background focus, and an honest iQOO demonstration.

> A little focus, a friend beside you, and clear control over every next step. That is FocusPilot.
