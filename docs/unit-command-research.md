# Qwen source units — development evidence

Keep **Qwen3.5-0.8B Q4_0** and the installed v0.16 app unchanged. On the same 24
previously seen synthetic development cases, a new quantity/unit contract improves
complete supported commands **9→12/18**, three gains and no losses. All six
unsupported requests are refused; no wrong accepted command is observed.
The model development criteria pass, but the broader known-gate check fails:
**18 prior accepted proposals regress and one unsupported mock route is accepted**.
This complete candidate is rejected for integration; the installed app stays unchanged.

## Method

The candidate asks Qwen to copy numeric quantity and unit. Java performs bounded
long multiplication, then runs the unchanged structured original-request validator
and checks copied quantity/unit agreement. Non-duration parsing, source guards,
clock/app checks and review semantics remain unchanged. Equivalent converted units
are refused because the tested contract requires copying the source unit.

Source, protocol, manual labels, reference, prompt/grammar and token counts were
frozen before generation at `963800cfea1ad177771cac0a1986e2e85df60bc1`.
One new capture reused the same original model, pinned standalone CPU runtime and
settings: four threads, context 1024, fresh contexts/recurrent clear, grammar then
greedy, actual EOS within 128 sampled tokens, no adapter/GPU/activation capture.
No training, download, model copy or phone operation occurred.

The reference is the exact already recorded structured-seconds capture at
`5fc35d4735c01389e0fc9d911487acfd3914ef5c`. Its published audit bindings and full
scores replay unchanged. No reference model rerun was needed. Gold action/argument
labels stay unchanged; copied-unit labels were manually reviewed before the new
outputs and remain ignored. This is **seen development**, not fresh confirmation.

## Measured results

| Quantity | Recorded seconds contract | New unit contract |
| --- | ---: | ---: |
| Complete checked supported commands | 9/18 | 12/18 |
| Raw canonical commands after deterministic conversion | 9/18 | 13/18 |
| Raw copied quantity/unit plus other exact fields | Different schema | 13/18 |
| Supported raw intent matches | 13/18 | 13/18 |
| Start focus complete | 0/4 | 2/4 |
| Pause complete | 2/4 | 2/4 |
| Alarm complete | 3/3 | 3/3 |
| Timer complete | 1/3 | 2/3 |
| Approved-app complete | 2/2 | 2/2 |
| Explanation proposal complete | 1/2 | 1/2 |
| Unsupported model abstentions | 3/6 | 3/6 |
| Unsupported validator refusals | 6/6 | 6/6 |
| Observed wrong accepted commands | 0 | 0 |
| Oracle supported source-evidence ceiling | 16/18 | 16/18 |

Raw intent totals conceal **one supported semantic gain and one loss**: a
previously misclassified regular two-hour timer now receives Timer, while a
previously classified two-hour focus request receives Timer instead of Start.
Only 22/24 raw intents stay identical. Complete-command losses remain zero because
the latter request was already refused. These semantic failures must remain visible.

All 24 new outputs contain strict JSON and actual EOS, with exit zero.
Vocabulary-only preflight and capture both measure 362–369 prompt tokens within
the 896-token allowance. The new run's first request is 792.10ms and subsequent 23
median 967.15ms; model load 328.99ms, wrapper 22.41s. These are host CPU measurements.
The historical reference median is 858.81ms; different capture timing and longer
prompt/output prevent a controlled speed-change or Android latency claim.

The three gains are two focus durations and one timer duration. Six supported
cases still fail: four semantic misses and two source-evidence refusals. Unit
copying addresses arithmetic; it does not establish general language understanding.
Explanation recognition is not a fulfilled answer about a historical warning.

## Independent audit

The [actual-record audit](../prototype/unit-eval/independent-audit.json) binds
238 files and 25 tracked source identities, validates the historical reference,
labels, token counts and actual process, and replays four Java routes byte-identically.
Independent full-slot, confusion, paired and decision totals match; raw semantic
regression is recorded separately. Audit SHA-256 is
`5c6d2d49bc691d1effc37b04a81bbcc7c191ab08301395ecbd40e8fbfb0df47a`.
No model rerun occurred.

## Known-gate regression — fails integration conditions

A separately prepared/frozen harness at
`7a40125f6f87f8355ee4eaacfb2fd3ed863da5db` independently extracts source units,
clocks and app targets from 226 previously seen synthetic gold requests. Its prepared
source-unit responses and labels were pinned before any candidate gate call. It
compiles the exact unchanged Unit/Structured/number-parser sources and executes
all 1,582 pure Java routes, with no model inference or phone actions.

| Actual known-gate check | Outcome |
| --- | ---: |
| Prior accepted canonical proposals preserved | 62/80 |
| Prior accepted safe-refusal regressions | 18/80 |
| Supported correct source-unit oracle proposals | 125/158 |
| Supported correct-route wrong accepts | 0/158 |
| Unknown mock routes falsely accepted | 1/476 |
| Supported wrong-intent mock routes falsely accepted | 0/948 |

The 18 refusals comprise three Start, five Pause and ten app launches. Source
request/direction and punctuation checks cause these regressions, rather than
unit conversion. A forced Explain response to an unsupported weather-forecast
question containing focus-session terms is accepted. This is **mock gate behavior**,
not a new Qwen prediction, and exposes an inherited off-domain question weakness.
Do not hide it behind the smaller six-case unknown result.

[Known-regression results](../prototype/unit-regression/results.json) and
[pre-output input/source inventory](../prototype/unit-regression/readiness.json).
The [independent gate audit](../prototype/unit-regression/independent-audit.json)
checks eight committed source identities/readiness, historical hashes, all 1,582
records and seven compiled classes. Java replays byte-identically; all counts and
full slots independently match. Public metadata omits the raw request and gold
numeric slots; the unchanged original private audit SHA-256 is
`136d0156d6bcd757adf478cc7b76aaec619ab571a752fa3b9d80f1c8abeaf770`.
The public audit SHA-256 is `f50cdc30284e4b2383767f5cd782c47361e02a7b482089725dc3d43fe2ec2f4a`.
The finite one-response-per-route challenge cannot prove arbitrary output safety.
No labels, prompt or gate were repaired after outputs; no retry occurred.

## Qualification and reproduction

Development advancement requires at least two net complete gains, no complete
loss, at least one Start, zero wrong accepts and all six unsupported refusals.
All five model-development checks pass. The known-gate preservation and false-accept
conditions fail, so this candidate cannot proceed to integration. A separate source
revision must preserve the existing accepted behavior and restrict off-domain
questions before a newly frozen fresh confirmation and actual reviewed Android/
lifecycle workflows. No seen-development rerun can substitute for those.

[Aggregate results](../prototype/unit-eval/results.json),
[Prospective protocol](../prototype/unit-eval/protocol.json),
[execution freeze](../prototype/unit-eval/execution-freeze.json),
[private-label hash manifest](../prototype/unit-eval/labels-manifest.json),
[unit contract](../prototype/unit-command/README.md), and
[capture runtime](../prototype/unit-native/README.md).
Raw labels, prompts, native logs and detailed decisions remain ignored. Replay
requires the preserved inputs and compiled classes with the exact frozen source;
no generation is needed to recheck decisions. New captures require a new study.

Ten isolated Java methods, 14 native-wrapper tests, 5 scoring tests and 9 regression-
authoring tests pass. The actual known-regression conditions fail as reported above.
No deployment, fresh/population/ASR accuracy, NPU, Office Kit, personalization or
causal interpretability result follows. The full assistant goal remains active.

Logical project storage is about 14.441 GB including ignored artifacts and Git,
below the strict 15 GB cap; shared pre-existing SDK caches are excluded.
