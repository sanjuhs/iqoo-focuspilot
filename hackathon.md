# iQOO Grand Finale — expectations and our project

Research date: 2 October 2026, IST. Primary sources:
[official guide](https://iqoo.reskilll.com/guide),
[event homepage](https://iqoo.reskilll.com/),
[tracks](https://iqoo.reskilll.com/problems),
[Terms](https://iqoo.reskilll.com/terms), and
[direct Finale application](https://iqoo.reskilll.com/register?city=finale).
See [verified research](docs/hackathon-research.md) for detailed findings and uncertainties.

## Dates and eligibility

- Grand Finale: Bengaluru, **9–11 October 2026**, advertised as a 48-hour event.
- Our target: prepare the concept/prototype/application by **3 October morning**.
  This is a user target; the signed-in application deadline is not yet verified.
- Team size: 1–3; student/professional categories cannot be mixed.
- Final entries run and are demonstrated on iQOO hardware.
- Pre-event idea preparation is permitted. Competition code must be created in the
  event window; a pre-built product cannot be shipped as the event submission.
- Third-party/open-source dependencies need attribution and compliant licenses.
- Loaner devices must not be modified/unlocked. We use normal Android APIs.
- Final Sunday submission cutoff and application video requirements need dashboard
  confirmation. The published pitch duration is 3–5 minutes.

This repository documents research and labels pre-event code under `prototype/`.
It does not prove eligibility of that code for the Finale.

## Tracks

| Track | Where it runs | Fit for FocusPilot |
| --- | --- | --- |
| FinTech and Commerce | City battles | Not selected; simulated penalties are not a finance product |
| Smart Education | City battles | Possible learning use case, not Finale entry track |
| HealthTech | City battles | Not selected; no medical claims |
| Productivity | City battles + Finale | **Primary**: focus coaching, task assistance, repetitive phone actions |
| Smart Living | City battles + Finale | Optional future local IoT workflow |
| Developer Tools | City battles + Finale | Only if developer workflow becomes the central product |
| Mobility | Finale | Not selected |
| Community App | Finale | Not selected |
| Open Innovation | Everywhere | Fallback for general local assistant positioning |

Choose Productivity unless dashboard/organizer classification requires otherwise.
Fewer strong workflows should lead the pitch; a broad list of unrelated functions
would weaken product quality and impact.

## Full judging rubric and our evidence

| Dimension | Weight | Evaluator | What we will show |
| --- | ---: | --- | --- |
| End product quality | 30% | Jury | A repeatable focus-to-nudge-to-action workflow, usable UI, pause/override, reliable alarm command |
| Novelty and impact | 20% | Jury | Local fast decisions plus user-controlled accountability and exact feature explanations |
| Creative phone use | 15% | HackTracker | Voice, app usage context, on-device inference and phone-first interaction on actual iQOO |
| Technical depth | 15% | Jury | Small model, constrained outputs, permissions, held-out evaluation, latency/memory and backend evidence |
| Office Kit usage | 10% | HackTracker | Actual supported phone/laptop pairing, transfer or remote input used during the event |
| Demo and presentation | 10% | Jury | Compelling 3–5 minute pitch, live workflow and backup video |
| Total | **100%** | | |

These are currently published weights, subject to organizer updates. HackTracker
evidence is separate from self-reported measurements or a GitHub commit.

## Hardware and on-device AI

The guide encourages a local/open-source core and targets Snapdragon NPU use.
There is no verified mandatory parameter count or prescribed runtime in the public
guide. We independently target 0.1–0.5B parameters and a 10–15 GB development budget.

Office Kit is advertised for iQOO phones running OriginOS 6, with macOS 10.14.6+
or Windows 10+ laptops. Nothing-phone USB debugging establishes development access,
not Office Kit support. Ask the dashboard/organizers for the actual loaner SKU,
SDK access and pairing instructions. ADB is not equivalent to Office Kit.

Local CPU inference, GPU inference and Snapdragon NPU inference are distinct
claims. Record the actual backend. Model export/conversion may require laptop
tooling and unsupported operations can cause fallback. Do not promise NPU success
before profiling the tested artifact on the relevant device.

## Proposed application summary

**FocusPilot — a private productivity copilot that turns phone context into fast,
explainable actions.** Users choose app budgets and a focus goal, speak bounded
commands and receive timely nudges when their own limits are exceeded. A small
local language decision model selects intent; a tiny interpretable policy scores
distraction; Android executes approved actions. A simulated commitment balance
illustrates accountability without withdrawing real money.

Example: start a work session, spend beyond the configured social-app budget,
receive one spoken nudge with feature contributions, record a virtual penalty,
and say "set an alarm for 7:30" to open the phone's clock confirmation flow.

## Submission assets checklist

- [ ] Complete direct-entry dashboard and confirm actual cutoff.
- [ ] Confirm permitted treatment of pre-event research code.
- [ ] Team/category/track details and concept write-up.
- [ ] Source repository with license, attribution and build instructions.
- [ ] APK or required runnable artifact, tested on iQOO.
- [ ] Model revision/license, local/NPU evidence, evaluation and limitations.
- [ ] Office Kit demonstration and HackTracker activity during official event.
- [ ] 3–5 minute pitch script; recording format/length adapted to dashboard.
- [ ] Backup video/screenshots containing only consented synthetic content.
- [ ] Submission receipt before official cutoff; repository alone is not submission.

The user signs in and supplies missing dashboard details. No registration,
acceptance of Terms, external message or submission has been performed by the agent.
