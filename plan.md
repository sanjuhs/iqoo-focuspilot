# FocusPilot delivery plan

Prepared 2 October 2026, IST. Working preparation/application target: 3 October
morning; the authenticated dashboard cutoff is still unknown. Public Grand Finale:
9–11 October. The broader goal is a working local Android assistant and a recorded
demo, with an honest, measurable System 1 decision path.

## Current checkpoint — v0.10

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

**133 Android JVM tests pass**, lint zero errors/**62 warnings**; **11 artifact-audit
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

## Previous checkpoint — v0.9

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

The [0.9 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.9)
publishes light/bundled APKs and the immutable artifact manifest. All three server
sizes/SHA-256 digests match local files; tag resolves to the stated app-source SHA.
After installation, one display-wake/own-app-launch attempt failed the unlocked
own-app foreground guard. No UI was inspected, permissions granted or commands
executed; subsequent metadata still reported asleep/not-own-app-focused. Actual
overlay and countdown tests remain pending. This later attempt is separate from
the initial installation snapshot.

Next: user-granted overlay drag/Hide/Pause, notification controls, lock/revocation,
rotation/keyboard, and actual timer/voice/monitor/offline checks. Neither packaging
nor service declarations establish these behaviors. Actual iQOO/NPU/Office Kit and
accepted eligible submission still require external evidence.

## Previous checkpoint — v0.8

Source `a214bd7fc6ddd3cc3917d7a1f1aa9d854b7f3eb3` adds whole-request validation
and English-number slots while keeping Qwen3.5/prompt/native unchanged. 119 JVM
cases pass; lint zero errors/59 warnings. Both APKs passed packaging inspection,
and light installed on Nothing with APK/private-model identity verified. Physical
spoken-number/countdown proof awaits an unlocked own-app foreground state.

The independently frozen 100-request/50-family result improves generated+gate
supported correctness 9→12/40 and wrong accepted proposals 5→0, but has 28 false
abstentions, nine gains and six regressions. Raw semantic Qwen correctness is
29/100. [Contract/results](docs/natural-commands.md). Keep these failures frozen;
future usability repairs require a new evaluation rather than rescoring as unseen.

Next delivery gates: actual reviewed short countdown, local speech, user-permitted
monitor/background/Stop behavior, disconnected inference and actual iQOO/Office Kit.
These remain physical evidence requirements, not satisfied by a new APK.
Measured logical workspace file size is **11.51 GiB**, within the 15 GB ceiling.

## Previous checkpoint — v0.7

Source `6bd4841b170be0445470eff9977133bc2accc8f6` implements reviewed bounded timed
focus and focus-domain explanations. 105 JVM tests pass; lint zero errors and
59 warnings. Both signed APKs passed model/native/license/permission inspection.
The light build installed; its action test stopped before inference because the
own-app unlocked/foreground guard failed. Actual countdown proof awaits the
user's unlock. These known-case regression repairs do not replace the frozen
0.6 reliability score. [Timer contract and test](docs/timed-focus.md).

Both APKs and the manifest are [published](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.7).
Current logical file size is **10.96 GiB** (2 October), within the 15 GB ceiling.

## System 1 research checkpoint

A separate 7,175-parameter intent head was actually trained on frozen Qwen3.5
representations: 222 training / 61 validation / 90 held-out synthetic rows.
Raw intent correctness rose from 46/90 for generation to 76/90; however, the
selected abstaining head and current Java gate propose only 15/65 supported actions
correctly versus 17/65 for generation. The threshold depends on numerical saturation.
The candidate is not deployed. [Measured experiment](docs/intent-head.md).

Next language work must evaluate calibrated rejection and argument/validation
coverage on newly frozen families, followed by actual device costs. Preserve the
existing held-out results; do not tune against them or infer autonomous reliability.

## Previous checkpoint — v0.6

Research build source: `29c4c3372fcc913d3672e59803a3aa870fa2426b`; both APKs and
hash evidence are [published](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.6). Setup readiness was inspected with permissions off;
actual typed Start/Pause proposals were reviewed and confirmed on Nothing, with
the final state paused, usage off and 100 virtual points. Cancellation abstained.
The integrated host build has 93 passing JVM tests, zero lint errors and 60 warnings.
Root measured logical workspace file size at **10.43 GiB** on 2 October; this is
within the authorized 15 GB ceiling. Recheck before adding another model/runtime.
[Readiness](docs/command-readiness.md) records the narrow phone proof.

The [frozen host evaluation](docs/command-reliability.md) reports 25/58 raw and
49/58 gated correctness, with only 16/23 supported tasks correct and two accepted
mismatches. Repairing known cases requires a new labelled evaluation rather than
reusing this score. The [laptop bridge](docs/officekit-export-workflow.md) now runs
existing-policy shadow replay after bounded export validation; 15 tests and actual
synthetic Java-export/Python-consumer interoperability pass.

Next acceptance gates remain user-consented physical voice/Clock and live monitoring,
disconnected offline execution, actual iQOO/HTP execution and Office Kit pairing/
transfer, followed by eligible event code and an accepted submission. The laptop
consumer completes the local compute piece; it does not complete the transport gate.

## Milestones and acceptance gates

| Order | Deliverable | Done when | Status |
| --- | --- | --- | --- |
| 1 | Hackathon/repository research | Rules, licenses, tracks and hardware assumptions are sourced | Verified; dashboard details pending |
| 2 | Phone and GitHub setup | Authorized ADB, device facts, secrets ignored, public source backup | Verified; ongoing source backup |
| 3 | Research prototype | Focus/virtual penalty/decision trace/alarm workflow runs on Nothing phone | Installed; bounded focus/sandbox tested, alarm outcome pending |
| 4 | Local model baseline | Selected Qwen3.5-0.8B model loads on Android and produces bounded decisions offline | Actual CPU inference and activation capture verified; offline disconnect test pending |
| 5 | Few-shot sandbox | User-labelled examples improve held-out decisions with recorded comparison | Implemented/tested; synthetic comparison trades coverage for accuracy, live evaluation pending |
| 6 | Voice and automation | Local speech availability established; approved commands verify outcomes | Draft-only voice integrated/tested in code; physical ASR/TTS and action outcomes pending |
| 7 | iQOO acceleration and bridge | NPU backend and actual Office Kit flow measured on approved hardware | Needs hardware/account access |
| 8 | Demo and application assets | Reviewable 3–5 minute pitch, backup capture and upload requirements known | 4:53 research pitch rendered; dashboard/submission requirements pending |
| 9 | Eligible event build | Competition app is created within permitted event window | October 9–11 unless rules clarified |

Use [docs/status.md](docs/status.md) for up-to-date results rather than reading this
initial milestone table as a completed-work report.

## Scope: one useful assistant, three layers

**Fast lane:** compact monotone policy takes explicit features such as focus mode,
user-set app category, budget overrun and repeated reopening. It recommends allow,
nudge or confirm exit. It records exact feature contributions and obeys cooldowns.

**Language lane:** use quantized Qwen3.5-0.8B Q4_0 as the selected command-understanding
candidate, with llama.cpp CPU instrumentation for selected activation experiments.
Keep Laya 322M/421M as a decision-model comparison. Validate a closed command
schema and slots before executing. Keep action candidates closed.

**Action lane:** Android native intents first, accessibility selectors later.
An allowlist, user-confirmation gates and postcondition checks stay outside the model.
Phone control is bounded by permissions and Android restrictions, not unrestricted.

The initial research prototype used only a deterministic parser. The current app
adds actual Qwen3.5 CPU inference in the model lab. Recurring dashboard nudges still
use transparent hand-set weights; a separate trained sandbox demonstrates the
65-parameter network. A shadow panel can evaluate that network on complete real
summaries without changing actions. Private task/target settings are implemented;
real-event calibration and physical live-personalization testing remain pending. Opt-in private real-summary labels are now integrated in the research source; only a matching Allow may veto an otherwise valid budget nudge. Keep each component
clearly identified.

## Companion and persistent-mode slice

Create the original friendly companion from [design](docs/companion-design.md).
Add subtle native animation, reduced-motion, mute/hide and a persistent foreground
monitor started explicitly from the visible app. Validate notification Stop, consent
revocation, background/return and process-interruption behavior. Always-listening
voice and floating overlays are separate later gates.

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

## Activation experiment and stretch work

Follow [docs/interpretability-experiment.md](docs/interpretability-experiment.md)
for the user-requested command-model activation inspector. Establish baseline
command accuracy, no-op intervention parity and held-out controls before claiming
a narrow causal result. NPU inference and CPU activation experiments are distinct.

## Stretch work after the baseline

- Actual local QLoRA research now exists with a frozen evaluation; the first adapter regressed and was rejected. Fine-tune any next decision adapter only against a newly frozen independent evaluation set.
  Stop if export or regression tests fail; retain working baseline.
- Train a nonnegative tiny network on synthetic/consented features; compare against
  hand-set weights, logistic regression and rules. Report accuracy/calibration and
  false-nudge rates separately from speed.
- Mechanistic experiments: feature ablation, hidden-unit interventions and
  counterfactual screen states. Treat these as evidence about the small policy head.
- One real IoT command can be added with hardware in hand and local protocol support;
  no broad Smart Living claim from a simulated lamp alone.
- Background foreground-service monitoring is implemented but still needs real
  permission/lifecycle checks. Wake words and broad cross-app automation follow battery,
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
