# Balanced Qwen3.5 adapter — measured research result

3 October 2026, IST. **Keep the installed original Qwen3.5-0.8B Q4_0.** A single
balanced LoRA improves native supported intent matches **41→48/50**, with seven
gains and no losses on this new informed synthetic set. Complete validated
proposals improve only **11→12/50**, one gain/no losses. The candidate **fails the
predeclared four-proposal gain requirement and is not promoted**. No Android
source, APK, selected weights, prompt, gate, permissions or service changed.

[Public aggregate and evidence hashes](../prototype/qwen-balanced-train/results.json)
bind the actual local records. Model weights, authored datasets, process logs and
individual predictions remain ignored. This is pre-event research under
`prototype/`, not an eligible event-written submission.

## Native confirmation

Both arms use the same existing phone-selected 563,036,064-byte Q4_0 GGUF, original
Java prompt/GBNF and selected whole-request Java gate/number parser. A newly
allocated CPU context per request has 1024 context/batch, 256 microbatch, four
threads, zero GPU layers, no activation capture, greedy grammar sampling and
128-token maximum. Only weights and the optional adapter are shared. This
standalone host C API differs from production JNI context reuse and provides no
new phone latency or NPU evidence.

| Metric | Original GGUF | Same GGUF + terminal adapter |
| --- | ---: | ---: |
| Supported raw intent matches | 41/50 | 48/50 |
| Complete proposal and exact slots | 11/50 | 12/50 |
| Supported refusals | 39/50 | 38/50 |
| Raw unknown predictions on unknown requests | 1/50 | 7/50 |
| Unknown requests refused by gate | 50/50 | 50/50 |
| Wrong accepted proposals | 0/100 | 0/100 |
| Canonical JSON and actual EOS | 100/100 | 100/100 |
| Runtime failures | 0 | 0 |

| Intent | Rows | Raw correct, original→adapter | Complete, original→adapter |
| --- | ---: | ---: | ---: |
| Start focus | 10 | 10→10 | 3→3 |
| Pause focus | 8 | 6→8 | 3→4 |
| Alarm | 8 | 8→8 | 2→2 |
| Timer | 10 | 10→10 | 2→2 |
| Open app | 6 | 5→6 | 1→1 |
| Explain | 8 | 2→6 | 0→0 |
| Unknown | 50 | 1→7 | 50→50 refusals |

All supported per-class complete counts preserve baseline. The paired native
comparison has seven supported semantic gains/no losses, one complete-proposal
gain/no losses, and six additional correct unknown predictions/no unknown semantic
losses. A guard refusal does not mean the model recognized an unsupported request.
Raw native unknown recall remains just 14%; these results support no general
safety guarantee.

The unchanged validator accepts only **12/50 even with independently supplied
correct intents**. That ceiling makes the required four-proposal gain from 11/50
unreachable on this cohort with a fixed gate. The cohort exposes a validator
bottleneck; it is not a useful estimate of unconstrained downstream execution.
Labels were authored independently and never filtered by the gate. Retain this
result instead of selecting easier phrases after outputs.

Some EXPLAIN labels ask about elapsed time, remaining time or progress. The current
executor reports active/paused status, usage budget and points; it does not fulfill
those subquestions. A classification or formal EXPLAIN proposal is not proof of
task fulfillment. No proposal in this experiment was executed.

## Prospective controls and actual training

The design was committed as `cd7d0b19cf3e6f71ffc59d282bb043889d983e8c`; complete
tool/source/input bindings were committed before inference as
`a2ba5df7405156a2f8365e43aad160b1b73166cb`.
[Protocol](../prototype/qwen-balanced-protocol/protocol.json) remains immutable.
[Execution freeze](../prototype/qwen-balanced-train/execution-freeze.json),
[pretraining-dev binding](../prototype/qwen-balanced-train/train-gate-freeze.json)
and [terminal binding](../prototype/qwen-balanced-train/terminal-freeze.json) are
separate immutable records. The latter was created before either confirmation arm.

- Existing offline MLX Qwen3.5-0.8B 4-bit weights and dependencies were reused.
- Training: 112 synthetic rows, 16 per intent; separate development: 14 rows,
  two per intent. Confirmation: 100 rows, 50 supported/50 unknown. Two rows per
  template family are correlated, not independent population samples.
- Seed 20261003, batch one, exactly two balanced epochs/224 optimizer updates;
  each training row appears twice, each intent 32 times. No checkpoint selection.
- Rank four, MLX scale eight, dropout zero; only layer 23's three MLP projections,
  with **55,296** trainable parameters. All base weights remain frozen.
- Adam lr0.0002, betas(0.9,0.999), eps1e-8, explicit bias correction; constant rate.
- Completion loss: intent-value token weight eight, shared JSON and EOS one,
  prompt zero, per-example sum-weight normalization. Actual cumulative tokenizer
  offsets verify each span; no mixed-boundary value tokens occur in these labels.
- Every training sequence fits whole; maximum 181 tokens against the fixed 256
  bound. No truncation or row omission.

The run completes once in **74.06 seconds** inside the trainer (75.96 seconds
including its launcher). First/last 14-update mean loss is 1.524→0.419; this is
training loss, not held-out accuracy. Parameter identities change and delta L2 is
0.875201236. An independent float64 recomputation differs by 1.71e−8. Peak MLX
allocator is 1,405,688,670 bytes; this is not process RSS or phone memory.

## Development and MLX diagnostic

Before training, original MLX and original native each complete all 14 development
requests. Raw intent matches are **12/14 versus 6/14**, with seven paired intent
disagreements. Both produce zero supported complete proposals; the oracle also
produces zero of 12. This is diagnostic, with no selection or data changes.

MLX and GGUF use different quantization and have unresolved source lineage. The
MLX card's conversion description and base-model field disagree. A small dev
comparison cannot establish base equivalence. MLX uses a canonical-token trie;
native uses GBNF. Tokenization/prompt parity is verified, but the decoders differ.

The separate 100-request MLX confirmation has supported raw matches **47→48/50**
(three gains/two losses), complete proposals **11→11/50** (one gain/one loss), and
unknown predictions **4→18/50**. Both reach 100 actual canonical EOS results with
zero wrong accepted proposals. These diagnostic losses are preserved. Constrained grammar/trie EOS does not
establish unconstrained output-format reliability. Native
qualification uses the prospectively selected native arms, not a preferred
decoder chosen after results.

## Adapter conversion and timing

Terminal safetensors: 221,908 bytes, SHA
`28306f9251df52e39434643a08ef035a47fc767fe29702e25b0b6746d18af5ee`.
GGUF adapter: 221,888 bytes, SHA
`80990163fb894b766dc4fafb1dba429ffb76a15db9ba1c23b10eac922d9decf8`.
Exactly six finite f32 A/B tensors map to layer 23 gate/up/down weights. Each GGUF
payload is independently verified byte-for-byte against its source transpose.
Alpha32/rank4 and native load scale one give MLX scale eight. The converter's
matrix check has max absolute error 2.98e−7; an independent seven-vector check on
the read payloads also passes. This establishes narrow conversion correctness.
The actual native capture loads the adapter; prediction transfer is measured above.
No full model was merged, dequantized or copied.

Native first/subsequent median inference: original **455.76/450.51 ms**, adapter
**421.99/407.08 ms**. Context allocation, model load, prefill and decode are recorded
separately in the aggregate. Arms run once serially, original then candidate, with
different predicted labels. These are observations, not causal speedup evidence.
Native stderr records buffer fallback and adapter attachment; runtime/source hashes
are checked before and after. No iQOO, Snapdragon NPU or Office Kit result follows.

## Data repair, verification and repeat procedure

Manual review before any output caught one ambiguous unknown case: a summary
request with a no-recording constraint. A separate v2 replaces that phrase with a
request that additionally asks for a private screen capture. All other 99 rows,
labels, slots, counts and order stay unchanged. The original cohort is retained;
[revision metadata](../prototype/qwen-balanced-data/pre-output-revision.json)
binds both versions and the reason. No labels change after predictions.

Forty-two pure research tests pass: seven training/order/weight tests, fourteen
data-contract tests and twenty-one native capture/scoring boundary tests. Independent
agents check actual training order/delta, GGUF tensors and final paired outcomes.
The initial launcher fails before creating a process record because the ignored
build parent is absent. The parent is created and the failed preparation is
recorded. No child, model load, phase claim or inference had started; all actual
phases/capture arms run once. Failed preparation and all process records remain.

Local replay requires retained ignored corpora, weights and pinned runtimes. The
public repository publishes tooling and hashes, not raw training data. To rescore
existing records, use the frozen source commit and documented native/MLX scoring
CLIs; they perform no inference. Existing exclusive phase claims and raw evidence
must remain intact. A new experiment needs its own prospective record and fresh
inputs, with the 15 GB project cap checked before allocation.

The next product work is a separately evaluated whole-request validator and
permissioned live voice/companion workflows. Do not retry this checkpoint or
quietly tune its confirmation data. The installed v0.15 remains selected. Actual
iQOO/NPU, Office Kit, allowed event code and accepted submission remain pending.
This training result establishes no causal mechanistic interpretation.
