# Compact Qwen decisions — evaluated and rejected

Pre-event research, 3 October 2026. **Qwen3.5-0.8B Q4_0 remains the selected
model, with the shipped prompt and validator unchanged.** A compact one-digit
intent format was tested to improve useful decisions. It does not qualify for
deployment because it loses focus/pause requests and fails prospective hard-case
criteria despite a small total coverage gain.

Three candidates were first compared on the same openly seen 36 development
requests. The best supported-action candidate, compact2, was then locked before
another informed author created 100 fresh requests: 50 supported and 50 required
abstentions in 50 two-row families. Exact and normalized overlap was zero across
16 pinned inventories. This is synthetic authoring, not independently sampled
human speech or general accuracy evidence.

The baseline uses the current JSON intent output. The candidate emits one digit
mapped to the same seven intents. Both use the same pinned Qwen weights, actual
host CPU JNI, context 1,024, four threads and unchanged original-request gate.
The gate receives the complete original text and validates exact action/time/
duration slots; it executes no action. Invalid/truncated output cannot count as
correct unknown semantics. Both 100-request captures completed with exit zero.

| Fresh frozen measurement | Shipped prompt | Compact2 |
| --- | ---: | ---: |
| Raw supported intent correct | 35/50 | 35/50 |
| Raw unsupported correctly unknown | 1/50 | 9/50 |
| Raw total semantic correct | 36/100 | 44/100 |
| Valid output with actual EOS | 100/100 | 100/100 |
| Correct supported complete action/slots | 30/50 | 32/50 |
| Supported false abstentions | 20/50 | 18/50 |
| Required unsupported gate abstentions | 50/50 | 50/50 |
| Wrong accepted proposals observed | 0 | 0 |
| Subsequent host native median, 99 requests | 448.70 ms | 465.74 ms |
| Median prompt tokens | 164 | 253 |
| Median emitted tokens | 8 | 1 |

The five gained action proposals are timers. Three previously correct proposals
are lost: one spoken focus duration and two pause forms. Start coverage falls
10/10 to 9/10; Pause falls 2/8 to **0/8**, while Timer rises 4/10 to 9/10.
Supported semantic predictions gain five and lose five overall. Prospectively
tagged spoken-number requests include one semantic and full-action loss;
warned-focus explanation includes two semantic losses. These failures violate
the criteria written before capture. No row, label, candidate or prompt was
repaired after scoring.

The gate still rejects all 50 unsupported requests, but compact2 proposes a tool
for 41/50 of them. Valid syntax and improved total semantic accuracy do not
establish dependable unknown detection. Even oracle domain labels reach only
43/50 exact supported gate actions, exposing seven unchanged validator limits.
Zero observed wrong accepts is scoped to this sample, not universal safety.

The candidate has roughly 3.8% higher subsequent native median on this host. Its
shorter answer reduces measured decode time, while its longer prompt has higher
measured prefill time; the aggregate is slower here. Baseline-first order, separate
loads, OS cache, thermal state and scheduling are uncontrolled. This is neither
an Android speed estimate nor NPU evidence. The full results retain first requests,
nearest-rank p95, ranges, paired differences and missing-metric counts.

## Evidence and reproduction

Executed source was committed before capture at
`c0c7e898fcacf9cc93b6e1fb375d64e997bac7bb`. The fresh runner,
data, prompt/map/grammar, selected app snapshots and inventories were frozen.
Development and confirmation use different recorded host native binaries:
development `2e9fa667…`, confirmation `ad57cd04…`. Their comparisons and timings
remain separate. Both use the same pinned model; no weights were trained.

- [Seen development and all candidates](../prototype/command-compact-dev/README.md).
- [Prospective protocol](../prototype/command-compact-confirm/PROTOCOL.md).
- [Fresh result aggregate](../prototype/command-compact-confirm/results.json).
- [Confirmation scope and source bindings](../prototype/command-compact-confirm/README.md).
- [Exact evidence manifest](../prototype/command-compact-confirm/evidence-manifest.json).
- [Runner and repeat procedure](../prototype/command-compact-runner/README.md).

Twenty research validation tests pass: eight authoring/overlap/immutability tests
and twelve scoring/format/slots/family/hard-case tests. Raw requests, generated
answers, detailed transitions, logs and classes remain ignored. Public source and
aggregate results are backed up separately from the selected APKs.

No app or phone change, new model download, provider call, training, action,
permission grant, NPU use or Office Kit integration follows from this experiment.
The research app still needs actual voice/background/iQOO testing, improved
real-language command reliability and the remaining full-goal deliverables.
