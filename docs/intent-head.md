# Qwen representation classifier — measured research

Prepared 2 October 2026. **The selected phone model remains Qwen3.5-0.8B Q4_0.**
This experiment trains a separate 7,175-parameter signed linear classifier on
actual frozen-model activations. It is not internal Qwen fine-tuning, the
65-parameter positive-weight productivity policy, or a deployed phone feature.
The candidate is **not promoted**.

The hypothesis was that one model prefill followed by a small decision head could
understand bounded commands without generating JSON token by token. The result
supports a narrow classification gain on authored English templates, but does not
improve usable actions through the current Android validator.

## Frozen experiment and actual training

- The existing pinned 563,036,064-byte GGUF and llama.cpp commit
  `57fe1f07c3b6a1de3f4fff19098e2056a85275b7` ran on laptop CPU, four threads,
  context 1,024. No new model download or paid API was used.
- Before capture, the protocol, complete current Android prompt and authored
  template families were fixed: **222 training / 61 validation / 90 held-out**
  rows, in 42 / 16 / 24 families. Training has zero exact utterance overlap with
  the earlier 58-case test. Task classes and vocabulary still overlap; this is
  neither independent human data nor a multilingual/domain-shift evaluation.
- The read-only probe captured the complete 1,024-coordinate `result_norm`
  vector at the last prefill position, with a fresh recurrent/KV context for
  each request. All 373 vectors were finite and nonzero. Two identical requests
  in fresh contexts produced byte-identical vectors. No tokens were generated
  and no model tensors were changed.
- Train-only normalization preceded **400 actual full-batch Adam updates**.
  Parameter delta L2 was **10.1992**; fit time was **0.04997 seconds**, excluding
  the much larger model extraction cost. Validation alone selected abstention
  thresholds before held-out labels were evaluated. The checkpoint remained
  unchanged when the autoregressive comparison was subsequently attached.

## Same 90-case comparison

| Measure | Existing autoregressive model | Raw trained head | Head with validation-selected abstention |
| --- | ---: | ---: | ---: |
| Semantic intent correct, including unknown | 46/90 | 76/90 | 66/90 |
| Unsupported intent incorrectly accepted | 24/24 | 9/24 | 0/24 |
| Non-unknown predictions | 90/90 | 75/90 | 43/90 |
| Correct among non-unknown predictions | 46/90 | 61/75 | 42/43 |

Both the existing model and selected abstaining head were then evaluated through
the **actual frozen v0.7 Java `ModelCommandGate`**, using the original utterance
and exact expected slots. One semantically supported spoken alarm has no supported
action representation, so this evaluation has 65 supported actions and 25 required
abstentions rather than the semantic task's 66/24 split.

| Strict action result | Existing model + gate | Abstaining head + gate |
| --- | ---: | ---: |
| Correct action/slots or required abstention | 42/90 | 40/90 |
| Supported action correctly proposed | 17/65 | 15/65 |
| Required abstention correctly rejected | 25/25 | 25/25 |
| Incorrect accepted proposals | 0 | 0 |

**No actions executed.** A classifier's semantic improvement cannot be presented
as improved phone task completion. The existing lexical validator rejects many
otherwise correctly classified requests. Future work needs an independently
evaluated argument/validation contract as well as better classification.

## Confidence and latency limits

Validation selected minimum softmax probability **1.0**, with zero margin.
Finite logit gaps round to exactly 1.0 in float64; this occurred in 25/61 validation
and 43/90 held-out rows. Acceptance therefore depends on numerical saturation,
not certainty. Precision/backend changes can change it. Zero false accepts on
24 synthetic unknown requests is not a safety guarantee. This policy is not ready
for deployment, and its threshold must not be repaired against this held-out set.

Observed host CPU median extraction cost was **308.47 ms** for fresh context setup,
the complete Android prompt and full-vector capture. Model load separately took
323.45 ms. Head-only normalization/classification was **0.00904 ms median**, assuming
the vector already exists. That is not the latency of the assistant.

The same 90-case autoregressive baseline took **456.86 ms native median** and
457.59 ms Java wall median, with model load 480.37 ms. It uses the existing cached
native context, cleared between requests, whereas the probe creates a new context
each time. Extraction covers all 373 rows; the generation baseline covers 90.
These are sequential laptop observations with unflushed OS caches, not a controlled
paired benchmark, phone measurements, NPU results, or an app speedup claim.

## What the explanation establishes

For each head class, standardized coordinate × signed weight contributions plus
bias reconstruct its logit: maximum absolute error **1.71e-13**. Setting one
normalized input coordinate to zero matched the predicted head-logit change within
**2.70e-13**. Removing the strongest top-versus-runner contribution changed the
predicted class in **1/90** cases.

This explains this separate linear head algebraically and verifies a head-input
intervention. The coordinates have no assigned semantic meanings. It does not
identify a “focus neuron,” establish a causal mechanism inside Qwen, or explain
the entire phone assistant. Qwen weights and the Android APK remain unchanged.

## Reproduction and evidence

See [source and commands](../prototype/intent-head/README.md),
[frozen protocol](../prototype/intent-head/protocol.json),
[data manifest](../prototype/intent-head/data-manifest.json),
[freeze identities](../prototype/intent-head/freeze-manifest.json) and
[measured aggregate results](../prototype/intent-head/results.json).
Seven focused classifier/data tests pass. Probe malformed-input checks reject
seven invalid fixtures before loading the model. Raw generated datasets, vectors,
checkpoints, binaries and detailed examples remain under ignored `build/`.
The generator and hashes allow reproduction without committing these artifacts.

Next experiments must use a newly frozen protocol and new held-out families.
Actual Android extraction, calibration, argument accuracy, memory/battery cost,
real user language and backend compatibility remain unverified. The broader
project goal remains active; these results do not complete the assistant.
