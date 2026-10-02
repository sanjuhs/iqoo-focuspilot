# Selected on-device model and deployment gates

Updated 2 October 2026. User selected **Qwen3.5-0.8B**, expanding the initial
0.1–0.5B model range. The parameter count remains 0.8B after quantization.

## Artifact and runtime

Base: [Qwen/Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B).
Text-only conversion: [ggml-org/Qwen3.5-0.8B-GGUF](https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF).
The inspected revision provides Q4_0 rather than Q4_K_M: 563,036,064 bytes
(approximately 537 MiB). Pin the full revision and SHA-256 in the runtime lab
manifest. No vision projector is required for the first typed/voice command flow.

Use a pinned llama.cpp CPU runtime for the baseline, short context (512–1024),
fresh recurrent/attention state per command and thinking disabled. Generate only
an allowlisted intent. The original utterance is parsed independently for validated
time/duration/app slots; a model output never supplies unchecked arguments.
Unknown, ambiguous, contradictory or unsupported requests abstain or ask.

The prior 0.5B/Laya experiments are comparisons, not changes to this selection.
See [prototype/qwen](../prototype/qwen) for measured evidence as it is completed.

## Phone integration sequence

1. Verify GGUF and checksums on laptop; test intent output on fixed cases.
2. Build arm64 Android JNI against the same pinned llama.cpp source, CPU only.
3. Package the native library and copy the checksummed GGUF into app-private storage
   for debug installation. Model weights stay outside Git and provider keys stay
   outside Android. Provide reproducible model-preparation commands.
4. Load/generate on a background worker, expose cancel, serialize native access,
   bound tokens/context and handle Activity destruction without invalid handles.
5. Show proposed command and backend/latency in the app; execution remains separately
   gated. Validate installed-phone predictions before enabling broader actions.
6. Test with laptop disconnected and airplane mode, recording actual model identity,
   backend, cold load, warm inference, memory and failures.
7. Capture selected tensors only in developer mode. Keep read-only observations
   separate from interventions and follow [activation protocol](interpretability-experiment.md).

CPU-native phone execution is useful local AI; it is not proof of Snapdragon NPU.

## Qualcomm reference evidence

The [Qualcomm model card](https://huggingface.co/qualcomm/Qwen3.5-0.8B) lists
GENIEX_LLAMACPP Q4_0 reference rows at 512 context on Snapdragon 8 Elite Gen 5
**For Galaxy** with response rates about 46–81 tokens/s across configurations.
These measure generation after the first token on their tested configurations.
They are not our iQOO/Nothing measurements and do not establish NPU execution.
That card's universal artifact and GenieX route are different from a demonstrated
QNN HTP export. Investigate exact execution placement rather than inferring it
from the Qualcomm brand. The generic AI Hub page also has filter-dependent support
text; use per-device/backend manifests and profiling instead of a broad support label.

The user identifies a 16 GB iQOO 15 as the intended target; official
[specifications](https://www.iqoo.com/en/products/param/iqoo-15) confirm that variant,
OriginOS 6, Android 16 and Snapdragon 8 Elite Gen 5. Actual event loaner access and
identity are still unknown. The connected phone is Nothing A059/SM7635.

## What must be measured

Report raw and post-validation intent accuracy, abstention/false-accept rates,
slot validity, cold/warm p50/p95 with sample count, separate prompt/decode timing,
RSS/peak memory, context/thread settings and capture overhead. Small hand-written
smoke sets are not reliable accuracy estimates for arbitrary tasks. Benchmark on
the actual installed phone; desktop results do not substitute.

Storage includes GGUF metadata and runtime files; RAM includes model mapping,
buffers, caches and captured tensors. The user's 1–2 GB working-RAM estimate is a
planning range until measured. Keep the 10–15 GB development disk budget and avoid
simultaneous redundant full-precision conversions.

## Execution and interpretation limits

Qwen3.5's hybrid recurrent/attention architecture needs architecture-specific
instrumentation and state reset. Successful tensor capture can show actual values,
but a component's meaning needs controlled ablation/patching and holdout replication.
NPU fusion may prevent equivalent activation access; keep a developer CPU research
path and do not claim the same experiment ran on NPU without evidence.

Payments, outgoing messages and deletion remain action-level confirmation gates.
The main demo uses virtual penalties and avoids unrestricted screen agents.

## Measured Android research slice

Qwen3.5-0.8B is running in-process on Nothing A059, Android16/API36/SM7635.
The generic JNI bridge produced a cold19,853ms and a later observed4,107ms
request. The first optimized ARM/KleidiAI build (SHA425cceb189864e9039b9561c33e779b97f8f7930a7f5608074ea36c18b9902a8)
ran five synthetic smoke requests: cold13,521ms, warm1,646ms, capture-on1,719ms,
negated1,724ms, compound1,663ms. The model proposed start_focus for all five;
the independent gate rejected the negated and compound requests. No action ran
in that batch. These small samples are not aggregate accuracy/p50/p95, and the
three identical requests do not isolate instrumentation overhead from warm-up.
See [raw synthetic phone smoke](../prototype/native/phone-smoke-optimized.json).

The optimized build requires DOTPROD/I8MM/FP16 ARM capabilities; do not distribute
it to arbitrary ARM64 phones without checking those features. The generic variant
remains available. Build the optimized variant explicitly:

```sh
NATIVE_BUILD_VARIANT=optimized ./scripts/build_android.sh
```

Model load verified the exact hash on phone. One memory sample was PSS791,083KiB,
RSS899,052KiB; no peak-memory or battery claim is established. Phone logs additionally verified CPU KleidiAI I8MM selection, and a confirmed
proposal started focus before dashboard Stop paused it. Airplane-mode and
USB-disconnected demonstration still need a physical-user check. The app manifest
contains no INTERNET permission and this JNI path contains no cloud call.

The separate [activation intervention lab](../prototype/interpretability/README.md)
performed108 fresh-context laptop CPU cases. Selected-channel patching did not
outperform random controls or flip held-out decisions. No-op/restoration returned
identical full-vocabulary logits. This verifies intervention machinery but yields
no positive semantic-circuit claim; it does not establish phone/NPU interventions.

## Standalone bundled model option

`-PbundleLocalModel=true` packages the exact pinned GGUF into generated debug
assets after verifying its size/SHA. The537MiB asset stays uncompressed; weights
remain excluded from Git. Bundled APK568,490,197bytes; light APK5,454,021bytes.
Both include upstream model/runtime notices. First load streams and verifies the
asset on a worker before atomically publishing a private model file; cancellation
cleans partial imports, and existing private files remain intact.

Use [bundled-model-evidence.json](bundled-model-evidence.json) for actual phone
first-import verification rather than treating packaging alone as execution proof.
