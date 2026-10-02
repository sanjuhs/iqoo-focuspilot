# Structured Qwen commands — development only

Keep the selected **Qwen3.5-0.8B Q4_0** and installed v0.16 app unchanged.
A separate structured-output prototype improves complete supported proposals
**2→9/18**, seven gains and no losses, on a small synthetic development cohort.
It still misses every focus-start case and nine supported commands overall.
This diagnostic authorizes neither deployment nor a general accuracy claim.

## What ran

Capture source was committed as
`5fc35d4735c01389e0fc9d911487acfd3914ef5c` before generation.
Root manually reviewed all 24 gold action/argument labels before gate or model
outputs. Labels did not change. Eighteen supported cases cover six tools; six
unsupported cases cover negation, combinations, conditions, invalid duration,
deletion and private capture. The author knew the response contract. This is
**development data**, with no blind/fresh-test claim.

One baseline run used the selected original intent-only prompt and current Java
gate. One candidate run used a new seven-example prompt and exact structured
JSON/GBNF plus an isolated original-request validator. Both reused identical
existing base GGUF weights and pinned standalone llama CPU binary/libraries:
four threads, context 1024, batch 1024, ubatch 256, fresh context per request, recurrent/
KV clear, no adapter/GPU/activation capture, grammar then greedy, maximum 128
sampled tokens including required actual EOS. No download, training or phone
operation occurred. Both processes exited zero and completed all 24 rows once.
Wrapper wall times were 11.42s baseline and 20.46s structured.

Before inference, vocabulary-only tokenization of exact rendered bytes measured
158–165 baseline tokens and 324–331 candidate tokens. Both inventories matched
all 24 IDs and fit the 896-token prompt allowance; tokenization used the same
special-token flags as capture. Source, binary, compiler, headers, libraries,
prompt bytes and measured records are bound in the
[execution freeze](../prototype/structured-eval/execution-freeze.json).

## Results

| Measured quantity | Original | Structured |
| --- | ---: | ---: |
| Supported raw intent correct | 11/18 | 13/18 |
| Complete accepted supported action and arguments | 2/18 | 9/18 |
| Supported false abstentions | 16/18 | 9/18 |
| Unsupported model outputs exactly unknown | 0/6 | 3/6 |
| Unsupported validator refusals | 6/6 | 6/6 |
| Wrong accepted actions/arguments observed, all 24 | 0 | 0 |
| Oracle full-proposal coverage, supported | 5/18 | 16/18 |
| First native request, host CPU | 479.99ms | 733.48ms |
| Subsequent 23 native median, host CPU | 456.08ms | 858.81ms |
| Actual canonical JSON plus EOS | 24/24 | 24/24 |

The candidate's raw exact action/argument objects are correct for 9/18 supported
cases before validation. Its 16/24 raw intent matches include three unsupported
abstentions; these should not be mistaken for16/18 complete commands. Oracle
coverage supplies manually correct outputs to the actual validators and measures
their source-evidence ceiling. It is not a model accuracy result.

| Complete supported proposals by tool | Original | Structured |
| --- | ---: | ---: |
| Start focus | 0/4 | 0/4 |
| Pause focus | 1/4 | 2/4 |
| Alarm | 1/3 | 3/3 |
| Timer | 0/3 | 1/3 |
| Open approved app | 0/2 | 2/2 |
| Focus explanation proposal | 0/2 | 1/2 |

The seven paired gains conceal no observed loss, but zero Start coverage is a
material product limitation. The candidate takes longer on this host; its prompt
and response are longer, so this comparison cannot establish a pure runtime
speed change or phone latency. Explain here means recognizing a proposal, not
answering a causal question about a previous warning.

## Error implications and next experiment

Several correctly identified focus/timer requests receive wrong converted seconds.
Independent source-slot agreement rejects them. Requiring an 0.8B model to perform
unit multiplication contributes avoidable failures. A **separate future contract**
should test a numeric quantity plus explicit source unit, with Android converting
units deterministically. It must retain independent original-request agreement
and explicit review. Do not repair this frozen prompt or gate against its outputs
and call a rerun confirmation.

Two supported oracle cases also fail source evidence. Finite lexical checks can
reject valid phrasing and cannot prove arbitrary semantic safety. The next source
revision needs broader prospective boundary cases, a new frozen protocol and fresh
confirmation covering current accepted commands, natural wording, exact units,
Pause regressions and adversarial compound requests. Development improvement alone
cannot qualify integration. Real reviewed Android execution, lifecycle and live
voice flows remain separate gates.

## Independent audit

The [actual-record audit](../prototype/structured-eval/independent-audit.json)
binds 154 files and checks 23 public freeze sources and 30 unique tracked source
identities. All 48 measured prompt counts match preflight. Four Java routes replay
byte-identically; independently recomputed full slots, confusion, paired gains/
losses and refusal totals match. No model rerun occurred. Audit SHA-256 is
`1053603ef15fca1af19badf2029d99cecf5d6d5c739717759295b4f1c28a466e`.

## Evidence and reproduction

[Aggregate results](../prototype/structured-eval/results.json),
[prospective protocol](../prototype/structured-eval/protocol.json),
[manual review](../prototype/structured-data/manual-review.json),
[data inventory](../prototype/structured-data/data-manifest.json),
[candidate contract/limits](../prototype/structured-command/README.md),
[native capture](../prototype/structured-native/README.md), and
[token-only preflight](../prototype/structured-eval/token-count-README.md).
Raw requests, gold datasets, prompts, native logs and detailed decisions remain
ignored. Their hashes and fixed denominators are public. Replaying existing
captures uses the frozen source commit, original ignored inputs/class snapshots
and pinned runtime; no model rerun is needed. New captures require a new study.

Research boundary checks pass 15 Java methods, 12 native-wrapper tests, 9 dataset
tests and 5 scorer tests. These establish their narrow contracts, not population
accuracy. No app integration, phone performance, ASR, new personalization, NPU,
Office Kit or causal interpretability is established. The full goal remains active.

Logical project storage at delivery is about 14.438 GB, including ignored artifacts
and Git, below the strict 15 GB cap. Shared pre-existing SDK caches are excluded.
