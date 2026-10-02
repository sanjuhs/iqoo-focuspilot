# Actual command-model activation intervention lab

**Pre-event research, 2 October 2026. CPU laptop only. No phone actions.** This experiment writes to selected Qwen3.5-0.8B activation channels and measures the resulting change in command logits. It is separate from the 65-parameter synthetic policy and does not claim universal “focus neurons” or full transformer understanding.

Run with the already provisioned model and pinned llama.cpp runtime:

```sh
python3 prototype/interpretability/run.py
```

The script builds only `prototype/interpretability/build/intervention_probe`, checks the Q4_0 GGUF checksum, and runs the fixed discovery/selection/holdout protocol. No provider key, network call, big dependency, downloaded dataset, or personal phone record is used. It leaves the production/native runtime sources untouched. Compiler: local `clang++`; linked llama.cpp build9620, commit `57fe1f07c3b6a1de3f4fff19098e2056a85275b7`. See the pinned model/runtime manifest in `prototype/qwen/model-manifest.json` and the shared [llama.cpp MIT notice](../native/LICENSE.llama.cpp).

## Exact scope and measurement

The model artifact is `models/qwen/Qwen3.5-0.8B-Q4_0.gguf`, SHA-256 `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`. It is the same quantized artifact selected for the app; **the scoring procedure here is deliberately narrower than the app**. The probe teacher-forces the common assistant prefix `{"intent":"` after the app-style system prompt. It reads the next-token logits for seven distinct label-initial tokens and selects their greedy maximum. It reports a closed `intent` field and `start_focus` minus `pause_focus` logit margin. That field is a candidate-token decision assembled by the probe, not proof of successful free JSON generation or the app's complete grammar path. These logits are not calibrated command probabilities.

Only the final token of that common prefix is intervened on, keeping decision position comparable across varying command lengths. All prompt tokens fit within context512/batch512/microbatch512. The probe checks float32, contiguous storage, width1024, and singleton higher dimensions before capture/write. Each request uses a **new llama_context**, so recurrent and attention/KV memory are fresh. The model weights are shared read-only between contexts; no finetuning occurs.

## Why the mutation boundary is deliberate

The pinned ggml scheduler asks which node needs an evaluation callback, evaluates the graph slice through that node, calls `ggml_backend_synchronize(split_backend)`, then invokes the callback with `ask=false` **before scheduling downstream nodes**. This is inspected in [pinned ggml-backend.cpp lines1680–1710](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/ggml/src/ggml-backend.cpp#L1680).

The callback uses `ggml_backend_tensor_get` and the synchronous `ggml_backend_tensor_set` to copy/modify the final contiguous row. The setter checks allocated storage and offset/size bounds, then uses the backend buffer setter. The callback reads back and checks the exact bytes written. See [setter implementation](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/ggml/src/ggml-backend.cpp#L324) and [API declaration](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/ggml/include/ggml-backend.h#L92). Do not recursively invoke `llama_synchronize` inside the callback. This inspected CPU graph boundary is not a claim that arbitrary GPU/fused/NPU activations can be mutated safely.

## Protocol and controls

Ten hand-authored matched paraphrase pairs are grouped by family: four discovery pairs, two selection pairs, and four held-out pairs. Four unrelated command/negation controls are additional. The exact texts, split, seed, prompt-position contract, and selection rule are saved in `protocol.json` before inference. Every split shares the same command semantics; this is a small wording holdout, not a population study.

1. Capture last-position `ffn_out-0`, `ffn_out-11`, and `ffn_out-23` vectors on the fixed baseline commands.
2. Rank each layer's channels using discovery-only absolute start/pause mean difference divided by within-group standard deviation, floor1e-3. Freeze four channels per layer before selection.
3. On the four selection commands, replace those channels with activations from the matched opposite-command baseline. Choose the layer/bundle with the largest average margin shift toward the donor's command. Freeze it before held-out interventions.
4. On all eight held-out commands, measure opposite-class patch, zero ablation, same-class discovery patch, an independently seeded random four-channel bundle, and a random bundle whose perturbation norm matches the selected patch. Pairwise donor baseline vectors are captured for patch construction, but held-out wording never influences candidate ranking/selection.
5. Test identical-vector no-op writes and zero-then-restoration writes before downstream execution. Compare the actual bytes of **all vocabulary logits**, not just the selected intent, against retained capture baselines. Also report their hashes and maximum absolute logit difference.
6. Zero the whole last-token layer vector as a broad perturbation. Run channel/layer zeroing on alarm, timer, calculator, and negated focus commands to check wider behavior changes.

The directional metric is negative margin delta for start-command recipients and positive margin delta for pause-command recipients: positive values move toward the matched opposite donor. The reported score changes and classifications remain separate. A tiny margin shift without a decision flip is not successful steering. Whole-layer zeroing can show sensitivity/necessity under the prompt but cannot identify a semantic circuit. Association-based ranking does not establish causation on its own.

The first random-control bundle is fixed by seed20261002 and excludes selected channels. One random bundle, two selection pairs, and four holdout pairs offer weak statistical coverage; a stable claim needs more independently seeded controls and frozen-wording replication. No held-out tuning is performed by this script. Repeated experiments chosen for attractive holdout outcomes would invalidate that claim.

## Results and go/no-go

`baseline-captures.json` contains the real baseline vectors, candidate logits and identities. `frozen-selection.json` records every selection candidate and the chosen bundle. `intervention-cases.json` records original/changed intents, margins, write verification and controls; `summary.json` aggregates them. Native diagnostic output remains in ignored `build/probe.log`. The captures are generated from these public hand-authored toy commands, not private screen data or trained weights.

Do not claim semantic causal understanding if baseline decisions are inaccurate, no-op/restoration parity fails, random controls have comparable effects, or unrelated commands degrade substantially. Even passing those gates just supports a bounded statement about this artifact, prompt, position, intervention and held-out wording. Keep observation-only heatmaps labeled exploratory. Physical-phone CPU replication and the app's complete structured-generation path remain separate gates; NPU interpretation is unverified.

This lab emits no action, opens no app, records no money movement, and changes no user permissions. The ordinary product should remain usable with intervention tooling disabled.
