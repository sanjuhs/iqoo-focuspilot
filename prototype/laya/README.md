# Laya comparison lab

This is a **pre-event laptop research prototype**, dated 2 October 2026. It does not establish Finale eligibility or represent work created during the event. See [the project eligibility notes](../../hackathon.md). It performs genuine, local inference with pinned Laya weights, without an API key. It never executes phone actions, sends messages, or deducts money.

The user's selected primary direction is now **quantized Qwen2.5-0.5B with an activation inspector**. The next main path is a llama.cpp GGUF CPU integration instrumented for activation experiments. This Laya experiment remains a comparison of single-pass bounded decisions. It is not the primary phone runtime, and its probabilities are not neural activation traces.

## Reproduce

Requirements: Node.js 20+, npm, curl, approximately 2 GB free disk for this lab's model/runtime, and enough free RAM for a 421M fp32 model plus native session working memory. The measured runtime memory will be recorded below rather than inferred from the parameter count.

```sh
cd prototype/laya
npm ci --no-audit --no-fund
npm run prepare:model
npm test
LAYA_INTEGRATION=1 npm test
npm run classify -- "Set an alarm for seven tomorrow morning."
npm run benchmark -- benchmark-results.json
```

Run these commands from the project root as shown. `npm ci` uses the committed lockfile. Model preparation downloads one English Laya ONNX bundle into ignored `models/laya-english-68f27dfe/`, verifies exact sizes and SHA-256 hashes, and does not download training checkpoints or the multilingual model. Restarting preparation reuses verified files. Inference uses `modelDir`, which bypasses the upstream downloader, so classification makes no Hugging Face freshness requests and works with networking disabled after setup.

`benchmark-results.json` contains only hand-written lab commands, probabilities, timings and host metadata. It must never be treated as a held-out accuracy result or phone measurement. The integration test checks real inference, probability normalization, supported output shape, and a simple focus command with JavaScript network fetch disabled. This is not an OS-wide network isolation test. The default tests check CLI validation and ambiguity handling without requiring the model.

## What the model does

The CLI submits the command and five explicit candidate intents to `Laya.systemOne()`:

| Intent | Meaning |
| --- | --- |
| `focus` | Start a focus session or concentration timer |
| `alarm` | Create or open an alarm/wake-up reminder |
| `pause` | Pause/stop/end the focus session |
| `open` | Open an app, settings, or home screen |
| `unknown` | Ambiguous, unrelated, or unsupported command |

Each result includes the model's actual raw winner and its full distribution. A separate deterministic abstention gate requires top probability ≥0.70 and a margin ≥0.15; otherwise the selected intent becomes `unknown`. These thresholds are exploratory lab settings, not validated confidence guarantees. No keyword rule replaces inference. The unknown option is a candidate label, not a reliable safety filter: sensitive actions must be excluded by the Android executor independently.

The model only selects an intent. It does **not** extract the alarm hour, resolve “tomorrow,” identify an Android package, generate a multi-step plan, or verify completion. Slot extraction and permission/postcondition checks remain separate implementation work. Inputs longer than 2,000 characters are explicitly rejected by the CLI; the model still has a 512-token sequence limit and can truncate long state text. This lab's short fixture commands fit that limit.

## Pinned artifacts and licenses

| Component | Pin | License |
| --- | --- | --- |
| [Laya English ONNX export](https://huggingface.co/receptron/laya-onnx/tree/68f27dfe5a27a54fb2b1fefc432f43f972e90868) | `68f27dfe5a27a54fb2b1fefc432f43f972e90868` | Apache-2.0 weights; Convai Innovations |
| [Node wrapper](https://github.com/receptron/laya) | `@receptron/laya` 0.1.2; inspected source `6478649e723122ca24bbf5fb69ed1010023c9750` | MIT |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | `onnxruntime-node` 1.22.0 | MIT |
| [Hugging Face tokenizers JS](https://github.com/huggingface/tokenizers.js) | `@huggingface/tokenizers` 0.2.0 | Apache-2.0 |

The exact model file sizes and hashes are in [model-manifest.json](model-manifest.json). Native/tokenizer npm integrity pins are in [package-lock.json](package-lock.json). The full model bundle is **1,692,649,436 bytes** (about 1.58 GiB). Installed dependencies on the measured Mac use approximately 240 MiB. No provider API credits were used. Model hashes are verified before every session; that verification time is reported separately from loading and scoring.

Third-party licenses remain applicable to redistributed artifacts. Retain their license files/notices when assembling a deliverable; the repository's own license does not replace them.

## Measurement contract

The lab forces `executionProviders: ["cpu"]`, with four intra-op threads and one inter-op thread. The backend is **ONNX Runtime CPUExecutionProvider on the development laptop**. It makes no Core ML, Android, NPU, Snapdragon, or Office Kit claim.

The report separates SHA-256 verification, ONNX session loading, the first scoring call after load, and subsequent scoring calls. `firstScoringMs` is process/session-cold inference, **not** guaranteed OS disk-cache-cold inference. Warm median/p95 includes JS tokenization, input packing, native model scoring, calibration, and result rendering; it excludes session setup, download, and phone actions. RSS is a snapshot after scoring rather than a peak memory profiler.

The 15-command smoke set covers all five labels. It is intentionally small and hand-written; failures, abstentions, coverage, raw accuracy, and selected accuracy are reported as measured. We do not infer arbitrary real-world reliability from it.

### Measured comparison result

Measured on the development **Apple M4 Pro**, arm64 macOS, Node 22.23.1, ONNX Runtime CPU provider with four threads. The model was not fine-tuned. See [benchmark-results.json](benchmark-results.json) for the complete outputs.

| Measurement | Observed |
| --- | --- |
| Bundle hash verification | 672 ms |
| ONNX session loading | 731 ms |
| First scoring call after session load | 257 ms |
| Warm scoring median / p95 over 15 commands | 234 ms / 249 ms |
| Process RSS after scoring | 1,731,166,208 bytes, about 1.61 GiB |
| Raw model winners correct | 13/15 |
| Final selected intents correct | 13/15 |
| Commands passing the action threshold | 10/15, all 10 matched these smoke labels |

The raw model confused “End this focus session now” with `focus`, and “Delete all my photos” with `open`. Both were stopped by the probability gate. “Stop the concentration timer” had the correct raw `pause` winner but also abstained. These failures demonstrate why neither the unknown label nor a pretrained confidence number is a sufficient production gate. All three alarm examples matched `alarm`, but no alarm was set and no alarm-time slot was extracted.

The 234 ms result is CPU scoring on a laptop, not a phone latency claim. It does not demonstrate Snapdragon acceleration, final-device power consumption, or the Qwen model's behavior.

## Exact Android conversion feasibility

The upstream exporter already provides an ONNX graph with an external `.data` file and tokenizer/config JSONs. Native Android ONNX Runtime can be a CPU integration target, but this Node package itself depends on `onnxruntime-node` and cannot be dropped into an Android APK. No Android inference has been executed here. [ONNX Runtime Mobile](https://onnxruntime.ai/docs/tutorials/mobile/).

Port these contracts together before claiming parity:

1. Tokenize with the bundle's exact tokenizer JSON and special `[CLS]`, `[SEP]`, `[MASK]`, `[PAD]` IDs. Use a verified Android tokenizer implementation/JNI binding; do not assume Android's tokenizer matches the JS implementation.
2. Reproduce upstream sequence packing: question/instructions, option `[MASK]` markers, state, special tokens, truncation, and right padding. Preserve JS/Python JSON serialization behavior or use plain string state in both references.
3. Feed `input_ids` and `attention_mask` as int64 `[B,L]`, `marker_pos` as int64 `[B,K]`, `marker_mask` as bool `[B,K]`, and `qtype` as int64 `[B]`.
4. Read float32 `logits` `[B,K]` and `act_probs` `[B,2]`; divide logits by the exact question-type/cardinality temperature before softmax. For this five-option choice, use `choice:3-5` from the pinned config. Preserve the winner and threshold calculation without confusing entropy confidence with top-class probability.
5. Check golden token IDs, marker positions and probabilities against this CPU reference for supported commands, empty/long state, option order, punctuation, and marker-like input. Package graph, external data, tokenizer, and config together and verify hashes.

The public bundle uses dynamic batch/sequence/option dimensions and fp32 weights. QNN HTP requires fixed shapes and quantized models, and supports only a subset of operators. A new fixed-shape QDQ export plus representative calibration data, QAIRT/QNN libraries, native build, and actual device profiling is required. Both tokenizer/preprocessing and unsupported graph partitions may remain CPU work. Verify supported partitions and disable CPU fallback for a strict check where feasible; otherwise report mixed execution. This lab establishes none of those NPU milestones. [Upstream export implementation](https://github.com/receptron/laya/blob/6478649e723122ca24bbf5fb69ed1010023c9750/export/export_onnx.py), [QNN requirements](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html), [Android QNN build](https://onnxruntime.ai/docs/build/eps.html#qnn).

The current ONNX export is English Laya. The upstream model family has a 322M multilingual variant, but this experiment did not download it; Hindi capability must not be claimed for this selected model. The pretrained probabilities are calibrated for the publisher's workloads, not automatically for our phone intents.
