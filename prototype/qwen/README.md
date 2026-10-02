# Quantized Qwen research lab

**Primary model: Qwen3.5-0.8B, Q4_0, text-only.** This is pre-event research code dated 2 October 2026; it does not establish permission to submit existing code as event-created work. See [eligibility notes](../../hackathon.md). No API credits, hosted inference, phone actions, or training were used here.

The original Qwen2.5-0.5B experiment remains a comparison. User steering selected Qwen3.5 and expanded the original 0.5B size limit. The primary conversion repository publishes **Q4_0**, not Q4_K_M; the manifest uses the actual filename and quantization. No vision projector/mmproj was downloaded, so this lab makes no camera/vision claim.

## Reproduce the primary intent baseline

Requirements: Node 20+, curl, and llama.cpp **build 9620, commit `57fe1f07c3b6a1de3f4fff19098e2056a85275b7`**. The lab reused the existing Homebrew runtime rather than installing packages. `LLAMA_SERVER` can select a matching binary.

```sh
cd prototype/qwen
node prepare-model.mjs qwen35
node --test test/*.test.mjs
node cli.mjs classify qwen35 "Wake me up at seven tomorrow morning."
node cli.mjs benchmark qwen35 benchmark-qwen35-intent.json
```

Preparation downloads one pinned GGUF into ignored `models/qwen/` and verifies SHA-256. Inference verifies it again, starts a temporary localhost-only llama-server, runs genuine model generation, and closes the process. The local OpenAI-compatible HTTP shape does not call OpenAI or require an API key.

CPU flags include **`--device none`, `-ngl 0`, and `--no-op-offload`**. Thinking is disabled through the Qwen3.5 chat-template setting. Temperature is zero, the output is schema-constrained, and prompt caching is disabled. These measurements concern the development laptop, not Android, Snapdragon, NPU, Office Kit, or phone energy consumption.

## Separate intent from trusted slots

The default mode returns only one label: `start_focus`, `pause_focus`, `alarm`, `timer`, `open_app`, `explain`, or `unknown`. The model does not invent a duration, alarm time, package name, monetary amount, or executor command in this hot path.

The Android application must parse and bound slots from the **original utterance** using its trusted parser. It must reject unsupported apps, negation, compound requests, ambiguous/missing times, and out-of-range durations or ask for clarification. Schema constraints guarantee an allowed output shape; they do not guarantee that the selected intent matches the user's request. Until behavior is validated on the phone workload, model results are previews for review rather than authorization to act.

The separate `classify-slots` / `benchmark-slots` modes preserve the earlier experiment in which the model generated bounded time/duration/app fields. Their output receives both JSON-schema and cross-slot semantic validation; invalid results fall back to unknown. This experiment is evidence for moving slot parsing out of the LLM.

```sh
node cli.mjs benchmark-slots qwen25 benchmark-qwen25.json
node cli.mjs benchmark-slots qwen35 benchmark-qwen35.json
```

## Measured results and failures

Apple M4 Pro, arm64 macOS, four CPU threads. Each report includes exact runtime/model pins, flags, timings, input commands, raw output, and validation failures. The two fixed evaluation sets were authored for this lab, contain 16 cases each, and are not a broad reliability benchmark. No weights were updated. Prompt examples are distinct from the evaluation sentences; further prompt tuning would require a new untouched holdout.

| Experiment | Correct final intents | Correct requested slots | Warm median / p95 |
| --- | --- | --- | --- |
| Qwen2.5-0.5B Q4_K_M, full generated slots | 8/16 | 7/16 | 661 / 683 ms |
| Qwen3.5-0.8B Q4_0, full generated slots | 12/16 | 10/16 | 1,004 / 1,057 ms |
| Qwen3.5-0.8B Q4_0, intent only | 12/16 | Not generated | 416 / 547 ms |

The intent-only set still fails “Do not set an alarm” (`alarm`), a compound request (`start_focus`), a general knowledge question (`start_focus`), and an unsupported Instagram request (`open_app`). Output remains perfectly schema-valid in these failures. **Do not use its winner as an autonomous execution gate.** These are observed limitations, not solved by the grammar.

The slot experiment invents/misreads some alarm times, fails to suppress unused fields, and mistakes a 900-minute out-of-range focus request for 90 minutes. The 0.8B full-slot run has two semantic validation failures; the 0.5B run has nine. Actual raw outputs are preserved in [benchmark-qwen35.json](benchmark-qwen35.json), [benchmark-qwen25.json](benchmark-qwen25.json), and [benchmark-qwen35-intent.json](benchmark-qwen35-intent.json).

Session readiness and hash verification are reported separately. “First request” is the first call in a new process/session; the OS file cache is not flushed. The intent benchmark's p95 includes ordinary host scheduling and concurrent development activity; treat the numbers as a lab observation, not a tuned hardware performance claim.

## Pins, sizes, and licenses

See [model-manifest.json](model-manifest.json) for full revisions, byte counts, SHA-256 hashes, and source/runtime licenses.

| Artifact | Source | Download |
| --- | --- | --- |
| Primary Qwen3.5-0.8B Q4_0 | [ggml-org conversion](https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/tree/8fea620810c4afa23dd6443f999a48574c1611a3), derived from [Qwen's model](https://huggingface.co/Qwen/Qwen3.5-0.8B) | 563,036,064 bytes |
| Comparison Qwen2.5-0.5B Q4_K_M | [Official Qwen GGUF](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/tree/9217f5db79a29953eb74d5343926648285ec7e67) | 491,400,032 bytes |
| llama.cpp source/runtime | [Pinned source](https://github.com/ggml-org/llama.cpp/tree/57fe1f07c3b6a1de3f4fff19098e2056a85275b7) | Existing host binaries reused; source checkout ignored |

Model cards declare Apache-2.0; llama.cpp and ggml are MIT. Retain the actual licenses/notices when redistributing model/runtime artifacts. [Qwen2.5's license copy](LICENSE.Qwen2.5) is included; Qwen3.5 conversion provenance and license declaration must also remain attached. Project-wide disk usage after these experiments and the Android native build was approximately 4.6 GiB, below the 10 GiB target.

## Native Android and activation work

[../native](../native/README.md) contains a built arm64-v8a JNI library, a Java reference adapter, and a real host activation callback probe. That library has not been measured on a phone by this research lab. Android integration and phone tests are owned by the main application work.

Qwen3.5 uses a hybrid architecture with recurrent gated delta-network layers and full-attention layers. Every native request clears both recurrent/KV memory. Intervention comparisons must do the same; a dense Qwen2.5 cache experiment is not equivalent. Selected tensor observations are implemented; causal ablation, restoration, activation patching, and an interpreted semantic circuit are not. [Pinned Qwen3.5 implementation](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/src/models/qwen35.cpp).

GGUF plus native CPU execution does not establish Snapdragon NPU support. A separate supported vendor/runtime export and actual device profile are required before making that claim.
