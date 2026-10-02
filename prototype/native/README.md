# Local Qwen JNI bridge and activation observation

Pre-event laboratory code, 2 October 2026. This component provides **CPU-only** llama.cpp integration and observed tensor summaries. It executes no phone actions. It is not a mechanistic explanation, activation intervention, NPU integration, or proof of Finale eligibility.

## Android build

```sh
sh prototype/native/build-android.sh
```

The script verifies the source checkout at llama.cpp commit `57fe1f07c3b6a1de3f4fff19098e2056a85275b7`. Build prerequisites already installed on this machine: NDK **28.2.13676358**, CMake and Ninja. It cross-compiles for **arm64-v8a, Android API 28**, baseline `armv8-a`, with GPU backends, dynamic backend loading, BLAS, and OpenMP disabled. C++/llama/ggml are statically linked into one JNI shared library. A 16 KiB maximum ELF page alignment is requested.

Output: ignored `prototype/native/build/android-arm64/libfocuspilot_local.so`, approximately 4.9 MiB after stripping. ELF inspection confirms ARM aarch64 and only system `liblog.so`, `libm.so`, `libdl.so`, and `libc.so` dependencies; no separate `libc++_shared.so` is required. The artifact's SHA/build details are in [build-manifest.json](build-manifest.json). Compiled code alone does not confirm Android runtime execution.

### Optional optimized Nothing-phone variant

```sh
NATIVE_BUILD_VARIANT=optimized sh prototype/native/build-android.sh
```

This creates a **separate** `build/android-arm64-optimized/libfocuspilot_local.so`; the initial generic artifact is preserved under `build/android-arm64-baseline-20261002`, and the generic build uses the updated source. It enables `armv8.2-a+dotprod+i8mm+fp16` and the pinned upstream **KleidiAI v1.24.0** CPU integration. Use it only on devices that advertise the required DOTPROD/I8MM/FP16 capabilities. The connected Nothing A059 `/proc/cpuinfo` features supplied by the app integration include `asimddp`, `i8mm`, `fphp` and `asimdhp`. This is an instruction-specific CPU library, not a universal ARM64 binary or Snapdragon NPU execution.

The pinned llama.cpp source has Q4_0 KleidiAI matrix/vector kernels and runtime feature selection. Phone logs must establish which kernel actually runs (`kleidiai: primary q4 kernel feature ...`); compiled kernel availability alone is insufficient. [optimized-build-manifest.json](optimized-build-manifest.json) records the library SHA, source SHA values, archive SHA, API/NDK and instruction flags. Actual Nothing phone I8MM selection and warm CPU inference were verified for the earlier artifact; [phone-integration.json](phone-integration.json) records that hash. The cancellation fix creates a new hash with verification tracked separately.

The microbatch is now 256, fitting the ~158-token demo prefill in one chunk. This increases compute-buffer memory relative to the original 128 configuration. Unobserved generation has no eval callback, avoiding the callback branch and graph synchronization in `ggml-backend.cpp`. Since this pinned public API has no callback setter, switching observation mode recreates one context while retaining the same loaded model weights. `context_setup_ms` measures that switch separately from the reported `total_ms` inference timer. Every command still clears all recurrent and KV memory, including commands after mode switches. Real host JNI tests passed capture/unobserved switches, cross-thread cancellation, fresh inference after cancellation and closed-handle safety. The artifact should be tested with the same original prompt before combining it with prompt changes.

### Short-prompt regression experiment

[java/PromptBenchmark.java](java/PromptBenchmark.java) compares the original adapter prompt with one shorter candidate on the **previously used** 16 fixed cases from the Qwen lab. This is a regression set, not an independent untouched holdout. [prompt-comparison.json](prompt-comparison.json) preserves every prediction and timing. On the Apple M4 Pro CPU, exact native grammar/context1024/microbatch256/4 threads with reset state per request yielded original **9/16** correct versus lean **10/16**. Median prompt length fell **160.5→81.5 tokens**, median prefill **286.4→143.0 ms**, median inference **451.6→284.9 ms**. No phone latency can be inferred from these host values. This native configuration differs from the earlier local-server schema experiment, which achieved 12/16; the earlier number must not be carried over to this JNI path.

The shorter prompt remains an experiment; the production reference adapter is unchanged. Both prompts make unsupported/negated/compound errors and require the application's independent original-utterance policy and slot validation. A shorter prompt is not an accuracy fix. Use model output as a preview until a broader, separate validation gate passes.

Reproduce raw per-case envelopes with `sh prototype/native/benchmark-prompts.sh` (uses the already downloaded primary model and installed CPU runtime; no provider request). The ignored TSV retains predictions and timings for both variants, and stderr remains in the ignored build log.

For app integration, copy the library into `src/main/jniLibs/arm64-v8a/` in a build step, include the Java adapter, and put the verified model in app-private storage. Keep model data outside Git and validate its manifest hash before loading. The root application owns that integration; these research files do not modify app/Gradle sources directly.

## JNI contract

Java class/package: **`dev.focuspilot.prototype.LocalModel`**. Reference source: [java/LocalModel.java](java/LocalModel.java).

| Native method | Signature / meaning |
| --- | --- |
| `nativeInit` | `(String modelPath, int context, int threads) → long handle`; context 512–1024, threads 1–8 |
| `nativePrepare` | `(long handle) → void`; clears the previous request cancellation **before queueing** new work |
| `nativeGenerate` | `(long handle, String renderedPrompt, String gbnf, int maxTokens, boolean capture) → String JSON envelope`; max 1–128 tokens |
| `nativeCancel` | `(long handle) → void`; aborts active CPU work; closed handles are harmless |
| `nativeClose` | `(long handle) → void`; idempotent, removes the registry entry and marks active/queued work for shutdown |

Exported ELF symbol names are exactly `Java_dev_focuspilot_prototype_LocalModel_nativeInit`, `nativePrepare`, `nativeGenerate`, `nativeCancel`, and `nativeClose` with that prefix. The wrapper uses llama.cpp's C API for model/context loading, tokenization, memory clearing, grammar sampling, greedy token selection, decoding, synchronization, and freeing.

Envelope shape:

```json
{"text":"{\"intent\":\"start_focus\"}","metrics":{"prompt_tokens":163,"generated_tokens":8,"prefill_ms":300,"decode_ms":180,"total_ms":480,"reached_eos":true,"cpu_only":true,"capture_enabled":true},"activations":[]}
```

Parse `text` separately and require a complete allowed intent; **`reached_eos=false` is a generation-limit failure**, not a valid partial command. The default Java prompt/grammar uses only `start_focus`, `pause_focus`, `alarm`, `timer`, `open_app`, `explain`, or `unknown`, disables thinking with an empty closed thinking prefix, and scrubs reserved chat controls from user data. Durations/time/package slots are parsed by the application from the original utterance, independently of the model. Model outputs remain previews until validated.

Use a worker/executor for initialization and generation, never the UI thread. The native registry retains shared ownership of models during calls, generation is serialized per model, preparation occurs before queueing and generation never clears a cancellation issued after preparation, cancellation is atomic and can run from another thread, and close refuses queued work. Close may finish freeing memory on whichever thread retains the final reference. The abort callback acts between CPU execution checkpoints; it is not guaranteed to interrupt immediately. Do not overlap UI lifecycle calls without catching closed/cancelled-generation exceptions.

Inputs use standard UTF-8 conversion from JNI UTF-16 rather than modified UTF-8, including supplementary characters. Outputs convert back to UTF-16. Every request clears all llama memory and recreates the grammar sampler, so there is no prior-command conversation or recurrent state reuse. Context overflow is rejected explicitly rather than truncated. Backend initialization is process-scoped; individual model/context memory is released on close.

## Actual activation observation

The optional eval callback selectively reads **`ffn_out-0`, `ffn_out-11`, `ffn_out-23`, and `result_norm`** float32 contiguous nodes during prompt prefill. It copies the last-position 1024-channel vector, reports mean/RMS/min/max and the first eight channel values, and retains only the latest chunk for each node. Generation capture is disabled to keep the interpretation of the recorded position explicit.

This is an observational read via `ggml_backend_tensor_get`; it does not write, zero, patch, or replace activations. It does not label a neuron as “productivity” or prove that a channel caused the decision. The values can be negative, as expected for the actual Qwen network. A separately designed monotone coaching policy is distinct from Qwen's learned activations.

Actual host result: the pinned primary Qwen3.5 Q4_0 model returned `start_focus` for the checked-in [fixture-prompt.txt](fixture-prompt.txt). [activation-observation.json](activation-observation.json) records four real 1024-wide tensor summaries. [unobserved-baseline.json](unobserved-baseline.json) returns the same intent without captured summaries. That one matching answer does not demonstrate equality of every internal tensor/logit or establish causal interpretation. Instrumentation changes scheduling/transfer work, so its latency should be reported separately.

The host probe reuses installed llama.cpp build 9620 and the Homebrew ggml runtime; the Android build compiles pinned bundled ggml source. Both use CPU-only devices. No host result here is a phone latency claim.

## Real JNI host smoke test

The host build script uses the existing Java runtime (`JAVA_HOME`) and existing Homebrew llama libraries:

```sh
sh prototype/native/build-host.sh
java -Djava.library.path=prototype/native/build/host \
  -cp prototype/native/build/java dev.focuspilot.prototype.NativeSmoke \
  models/qwen/Qwen3.5-0.8B-Q4_0.gguf
```

This test performs real JNI inference, observes selected activations, requests cancellation from another thread, performs a fresh-memory request after cancellation, and checks harmless close/cancel on an already closed handle. It does not load an Android binary on the host. Test status is recorded in the build manifest.

## Next causal gate

Before claiming ablation/patching, implement controlled tensor writes at a verified graph boundary and test zero, restoration, and clean-to-corrupt patch conditions. Hold tokenization, quantized weights, grammar, sampling, selected position, and all other execution settings fixed; reset both recurrent state and KV memory before each run. Include no-op intervention controls and show output/logit changes across a separate holdout and repeated trials. Preserve an uninstrumented baseline and measure callback overhead. Qwen3.5's hybrid recurrent stack means cache/state contamination can imitate an intervention effect.

Licenses: own repository license applies to the adapter; llama.cpp/ggml remain MIT, included as [LICENSE.llama.cpp](LICENSE.llama.cpp). The primary Qwen model is Apache-2.0 with the pinned [model manifest](../qwen/model-manifest.json) and converter/source attribution. No provider API or account key is embedded.

The optional KleidiAI sources are supplied by Arm under Apache-2.0 and BSD-3-Clause according to individual source headers. Both license texts are preserved as [LICENSE.KleidiAI.Apache-2.0.txt](LICENSE.KleidiAI.Apache-2.0.txt) and [LICENSE.KleidiAI.BSD-3-Clause.txt](LICENSE.KleidiAI.BSD-3-Clause.txt). Primary sources: [pinned llama.cpp CPU build](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/ggml/src/ggml-cpu/CMakeLists.txt), [pinned KleidiAI integration](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/ggml/src/ggml-cpu/kleidiai/kleidiai.cpp), and [Arm release v1.24.0](https://github.com/ARM-software/kleidiai/releases/tag/v1.24.0).
