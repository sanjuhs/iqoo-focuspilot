# FocusPilot delivery plan

Prepared 2 October 2026, IST. Working preparation/application target: 3 October
morning; the authenticated dashboard cutoff is still unknown. Public Grand Finale:
9–11 October. The broader goal is a working local Android assistant and a recorded
demo, with an honest, measurable System 1 decision path.

## Milestones and acceptance gates

| Order | Deliverable | Done when | Status |
| --- | --- | --- | --- |
| 1 | Hackathon/repository research | Rules, licenses, tracks and hardware assumptions are sourced | In progress |
| 2 | Phone and GitHub setup | Authorized ADB, device facts, secrets ignored, public source backup | In progress |
| 3 | Research prototype | Focus/virtual penalty/decision trace/alarm workflow runs on Nothing phone | Planned pre-event experiment |
| 4 | Local model baseline | 0.1–0.5B model loads on Android and produces bounded decisions offline | Pending |
| 5 | Few-shot sandbox | User-labelled examples improve held-out decisions with recorded comparison | Pending |
| 6 | Voice and automation | Local speech availability established; approved commands verify outcomes | Pending |
| 7 | iQOO acceleration and bridge | NPU backend and actual Office Kit flow measured on approved hardware | Needs hardware/account access |
| 8 | Demo and application assets | Reviewable 3–5 minute pitch, backup capture and upload requirements known | Pending dashboard requirements |
| 9 | Eligible event build | Competition app is created within permitted event window | October 9–11 unless rules clarified |

Use [docs/status.md](docs/status.md) for up-to-date results rather than reading this
initial milestone table as a completed-work report.

## Scope: one useful assistant, three layers

**Fast lane:** compact monotone policy takes explicit features such as focus mode,
user-set app category, budget overrun and repeated reopening. It recommends allow,
nudge or confirm exit. It records exact feature contributions and obeys cooldowns.

**Language lane:** evaluate Laya's 322M multilingual or 421M English decision model
for short bounded intent selection. These are encoder/decision models, not a chat
assistant that freely writes plans. Compare a small generative model only if a
decision model cannot handle required command slots. Keep action candidates closed.

**Action lane:** Android native intents first, accessibility selectors later.
An allowlist, user-confirmation gates and postcondition checks stay outside the model.
Phone control is bounded by permissions and Android restrictions, not unrestricted.

The first research prototype has no LLM and must say so visibly. Its hand-set
weights are a transparent baseline, not a trained model or claimed discovery.

## Today and tomorrow: preparation

1. Finish Markdown files and device verification; create public repository.
2. Build a clearly dated pre-event laboratory prototype to validate phone UX.
3. Test focus state, app-usage consent, simulated penalty, typed alarm request and
   explanations. Document actual voice availability.
4. Choose one model and fetch only its necessary artifacts after checking licenses
   and size. Establish tokenizer/input/output contracts before Android integration.
5. Prepare concept pitch, storyboard, application text and question list for dashboard.
6. Review submission eligibility before publishing a competition deliverable. Keep
   research code distinguishable from event-created implementation.

## Eligible 48-hour event sequence

| Event time | Build focus | Evidence |
| --- | --- | --- |
| Hours 0–4 | Fresh app scaffolding, permissions, local state and basic UI | Clean event-start commit, installable APK |
| Hours 4–12 | Model runtime, closed intent decisions, focus policy | Airplane-mode inference, model revision/backend |
| Hours 12–20 | Voice/alarm and distraction workflow | End-to-end success/failure log |
| Hours 20–28 | Few-shot sandbox, held-out evaluation, explanation panel | Metrics plus counterfactual examples |
| Hours 28–36 | Actual iQOO hardware, NPU attempt, Office Kit workflow | Backend trace or explicit CPU fallback |
| Hours 36–42 | Robustness, accessibility scope, consent/override | Repeatable demo, crash-free checklist |
| Hours 42–48 | Record, pitch, source audit, submit before dashboard cutoff | Video, repository, assets and receipt |

Adapt coding work to published Red/Green Light intervals; do not plan prohibited
laptop use during Red Light. The table is an ordering plan, not permission to bypass
the event schedule. Confirm final submission time at check-in.

## Stretch work after the baseline

- Fine-tune a decision adapter only after a baseline and immutable evaluation set exist.
  Stop if export or regression tests fail; retain working baseline.
- Train a nonnegative tiny network on synthetic/consented features; compare against
  hand-set weights, logistic regression and rules. Report accuracy/calibration and
  false-nudge rates separately from speed.
- Mechanistic experiments: feature ablation, hidden-unit interventions and
  counterfactual screen states. Treat these as evidence about the small policy head.
- One real IoT command can be added with hardware in hand and local protocol support;
  no broad Smart Living claim from a simulated lamp alone.
- Persistent observation, wake words and broad cross-app automation follow battery,
  privacy and reliability testing. They are outside the first runnable slice.

## Storage budget

| Bucket | Working ceiling |
| --- | ---: |
| Source and docs | 0.2 GB |
| Shallow upstream research checkouts | 2 GB |
| One baseline model + tokenizer | 2 GB |
| Conversion/quantization outputs | 2 GB |
| Training adapter and consented sandbox set | 1 GB |
| APK/build/dependency caches incremental to this project | 3 GB |
| Demo recordings and temporary files | 1 GB |
| Reserve | 3.8 GB |
| Maximum | 15 GB |

Measure disk use before every large download. Theoretical int4 weight size is not
the same as total RAM/storage; tokenizer, activations, runtime and conversions count.
Reuse existing SDK/Gradle installations instead of duplicating them. Cleanup only
this project's generated outputs after preserving needed evidence.

## Stop/go decisions

Do not wait for NPU export to make the product useful. A CPU model is a truthful
local fallback, but misses some hardware evidence. If offline ASR is unavailable,
keep typed input and TTS with a visible limitation. If app-screen automation is
fragile, use Android intents for the main demo. If application rules prohibit a
pre-event prototype, submit only permitted concept assets and build code fresh
during the event. Real penalties stay simulated for this iteration.

## Verification and demo evidence

- Device/permission state: authorized ADB; app permissions granted by the user.
- Policy: below-budget cases do not nudge; overrides and cooldowns prevent repeated charges.
- Actions: malformed/ambiguous commands abstain; alarm time is displayed before launch.
- Offline AI: model loads cold and warm; airplane mode; no remote runtime calls.
- Performance: device identity, backend, sample count, p50/p95, model initialization
  separate from inference, memory footprint and battery observations.
- Learning: split by workflow/session rather than duplicate paraphrases; report unseen states.
- NPU: operator coverage and trace prove HTP execution, not only SDK presence.
- Demo: all simulated states identified; reliable short backup capture; no private screens.
