# Model and computer-use research

Reviewed 2 October 2026. This document records source inspection and proposed engineering choices. No model has been downloaded, benchmarked on the phone, fine-tuned, or shown to run on its NPU during this research.

## Updated direction

After this research, the user selected quantized Qwen3.5-0.8B Q4_0 as the primary
command-understanding candidate, with selected activation capture and planned causal
intervention experiments in llama.cpp. Laya remains a useful local decision-model
comparison. See [activation protocol](interpretability-experiment.md) and
[verified status](status.md) for subsequent experiments; findings below are the
original source-based comparison, not claims that later downloads/tests are absent.

## Initial recommendation

Build an Android productivity coach with a **bounded decision model**, explicit phone actions, and a separate transparent coaching policy. Start with a few reliably executable tasks: identify a focus-session distraction, speak a reminder, return home when the user requests it, and open the phone's alarm workflow. A working phone loop is the priority for the deadline.

Use Laya as the first model candidate: the 322M multilingual checkpoint fits the requested 0.1–0.5B range and offers an option for Hindi; the 421M English checkpoint is a second candidate. Keep the Android executor independent of the model so we can replace a model without rewriting phone control. For a richer conversational response, a 135M or 360M SmolLM2 is a separate optional component. A decision model can be central AI without generating long replies: the app can map typed decisions to clearly labeled response templates.

**On-device and NPU are separate milestones.** Prove local CPU inference first, then attempt a pinned, fixed-shape, quantized QNN build on the actual Snapdragon device. A model running on a laptop through a USB bridge is useful development infrastructure, but does not count as on-device model inference.

## What the three links actually contain

| Link | Actual project | Practical fit |
| --- | --- | --- |
| [jaredpalmer/kev](https://github.com/jaredpalmer/kev) | Jared Palmer's open Jev-like decision models, with Python training and serving | Architecture and calibration reference; older 0.5B prototype is research-only; current family begins at 0.8B |
| [receptron/laya](https://github.com/receptron/laya) | TypeScript/Node.js ONNX runtime wrapper for Convai Innovations' Laya decision model | Useful runnable laptop baseline and export/tokenization reference; Android requires a mobile runtime integration |
| [trycua/cua](https://github.com/trycua/cua) | Cua computer-use drivers, sandbox tooling, benchmarks, and specialist CUA-S1 models | Reuse bounded-action and evaluation concepts; native Android phone execution is our own adapter |

Names: **Cua/CUA-S1**, rather than “CUEQA”; **Laya**, rather than a version of Java; **Kev** is the supplied repository, while **Jev** is the hosted model/API its interface resembles. Compatibility with an API does not make the underlying models identical.

### Kev

Kev returns yes/no, choice, or ordered-score probabilities without autoregressive text generation. The current family uses Qwen3.5/3.8 backbones with Python serving and CUDA/ROCm/MLX paths. Its source license is Apache-2.0. [Current README](https://github.com/jaredpalmer/kev).

An older, explicitly superseded `jaredpalmer/kev-0.5b@v0.1` remains available. It has a 494M Qwen2.5 backbone, 8.8M LoRA parameters, and a roughly 0.46M pointer head; counting the unmerged adapter puts its total slightly above 500M. Merging the adapter changes that accounting, but also requires new parity validation. Its custom attention mask and readout need export work; loading a Qwen GGUF alone does not reproduce Kev. The prototype's card documents option-order sensitivity and calibration limits on new tasks. It is an alternative experiment, not the fastest Android integration. [Prototype card](https://huggingface.co/jaredpalmer/kev-0.5b).

### Laya

The publisher lists English Laya at 421M parameters and multilingual Laya at 322M. Both answer typed closed questions; neither generates prose. The English model uses ModernBERT-large and the multilingual model mmBERT-base, with an added decision head. The weights are Apache-2.0. Publisher latency figures are measured on their hardware and are not phone measurements. Avoid loading all routed checkpoints on a phone; select one explicitly. [Publisher model card](https://huggingface.co/convaiinnovations/laya), [multilingual card](https://huggingface.co/convaiinnovations/laya-multilingual).

The linked MIT-licensed wrapper requires Node.js 20+, depends on `onnxruntime-node`, and downloads about 1.7 GB of fp32 ONNX weights on first use; it estimates approximately 2 GB loaded RAM plus batching overhead. Its default English state limit is 512 tokens, with 192 tokens for the option header. Its exporter emits dynamic batch, sequence, and option dimensions and separate uncalibrated logits plus action probabilities. Therefore its export is a starting point for mobile conversion, not an already proven QNN artifact. [Wrapper README](https://github.com/receptron/laya), [exporter](https://github.com/receptron/laya/blob/main/export/export_onnx.py).

### Cua and CUA-S1

Cua Driver primarily targets macOS, Windows, and Linux desktop control. The broader repository also includes Android sandbox/test infrastructure; this is distinct from a packaged, autonomous assistant on a physical Nothing/iQOO phone. Source licensing is mostly MIT, with component-specific exceptions including FSL-1.1-MIT for Spaces components. Preserve notices for anything reused. [Licensing](https://github.com/trycua/cua/blob/main/LICENSING.md).

The CUA-S1 forms checkpoint is a 706,048-parameter label-driven classifier; Nano has 855,296 trainable parameters in its text path. They select among supplied actions and are not small general LLMs. The forms model card reports confident skips on unseen labels. Nano's card also documents weak held-out text performance. Its multimodal path adds a separately licensed frozen vision model. Neither justifies claiming arbitrary phone control. [CUA-S1 model card](https://github.com/trycua/cua/blob/main/libs/cua-s1/MODEL_CARD.md), [artifact pins and downloads](https://github.com/trycua/cua/blob/main/libs/cua-s1/README.md).

**Our inference:** its most useful contribution here is an option scorer over a compact UI state, a sandbox for generating trajectories, and explicit verification of actions. We can train a tiny specialist for our own sandbox without describing it as a general-purpose LLM.

## Downloadable model shortlist

| Candidate | Size | License | Role and limitation |
| --- | --- | --- | --- |
| [Laya multilingual](https://huggingface.co/convaiinnovations/laya-multilingual) | 322M | Apache-2.0 | First bounded-decision candidate; mobile export/quantization needs verification |
| [Laya English](https://huggingface.co/convaiinnovations/laya) | 421M | Apache-2.0 | English-only demo alternative; larger ONNX working set |
| [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) | 135M | Apache-2.0 | Optional short English replies; restricted intent evaluation required |
| [SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) | 360M | Apache-2.0 | Optional more capable English generator with larger memory cost |
| [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Approximately 0.49B | Apache-2.0 | Alternative multilingual generative parser; strict action schema required |
| [Kev-0.5B prototype](https://huggingface.co/jaredpalmer/kev-0.5b) | 494M base plus adapter/head | Apache-2.0 | Research comparison; total/counting and custom mobile readout require care |

SmolLM2's small variants are mainly English and should not be assumed to have the larger variant's function-calling capability. Qwen's small model card states a 32,768-token context; the app should use much shorter bounded prompts for memory and latency. These are candidates, not validated device recommendations. [SmolLM2 card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct), [Qwen card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct).

Approximate weight-only storage is `parameter_count × bits_per_weight / 8`: 135M at 4 bits is about 68 MB; 360M is about 180 MB; 421M at 8 bits is about 421 MB. These are arithmetic lower bounds, **not download sizes or RAM estimates**. Tokenizers, quantization scales, activations, caches, runtime libraries, and export intermediates add overhead. Keep one selected model, one deployed export, and one training experiment within the 10–15 GB project budget; avoid the CUA 4B backbone whose published download is already about 9.34 GB.

## Android and Snapdragon integration

### Local baseline

For Laya, use ONNX Runtime Mobile through an Android binding/JNI integration. Port its exact tokenizer, input packing, option markers, truncation, and temperature calibration; compare identical inputs against the laptop reference. The Node package is not an Android library. [ONNX Runtime Mobile](https://onnxruntime.ai/docs/tutorials/mobile/).

For a generative SmolLM2/Qwen experiment, llama.cpp has an Android native build path. Keep this as a CPU/GPU baseline unless the selected backend is separately proved to use the target NPU. [llama.cpp Android documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md).

### NPU experiment

ONNX Runtime documents a QNN provider for Android builds. Its HTP backend maps compute to the Qualcomm NPU, requires quantized models, and requires fixed shapes; unsupported operators can fall back to CPU. Its documentation provides `session.disable_cpu_ep_fallback` for a strict support check and profiling controls. The current Laya dynamic fp32 export needs a new static QDQ artifact, representative calibration data, runtime/QAIRT compatibility, and matching Android native libraries. Package loading alone is insufficient proof. [QNN provider](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html), [Android build instructions](https://onnxruntime.ai/docs/build/eps.html#qnn).

Proposed experiment: fixed batch 1, short state, a small maximum option count, padding/masks, and an identical held-out dataset before and after quantization. Choose exact dimensions after measuring actual task inputs. Do not assume a Qualcomm AI Hub deployment listing or a successful hosted compile proves performance on our physical phone. [Qualcomm AI Hub](https://aihub.qualcomm.com/models).

### Evidence gates

| Claim | Required artifact |
| --- | --- |
| USB debugging works | ADB authorized `device` status, device properties, successful harmless read |
| Phone control works | Native action launched, observed postcondition, cancel/stop path demonstrated |
| AI runs on-device | Model ID/revision/hash, model loaded in Android process, offline test, measured cold/warm latency and RAM |
| NPU is used | Exact device/SoC, QNN/HTP backend log and profile, supported partition report, strict no-CPU-fallback check where feasible |
| Some operations use NPU | Profile identifying those operations and explicit CPU partitions; describe as mixed execution |
| Fine-tuning improved performance | Dataset manifest, fixed splits, baseline and trained scores on untouched real/sandbox holdout |
| Office Kit was used | Actual official bridge integration/session evidence; ordinary ADB is development plumbing |

Report median and p95 latency separately for model scoring, Android action execution, and speech. Published desktop/GPU milliseconds are not evidence for phone speed. A Nothing phone can validate Android behavior; it cannot substitute for measurements on the final iQOO hardware.

## System 1 action loop

```text
User opt-in and focus goal
  → foreground-app/usage event or user command
  → compact state + enumerated allowed intents/actions
  → local decision model → calibrated distribution
  → deterministic permission and consequence gate
  → Android intent / approved accessibility action / coaching prompt
  → observe postcondition → store local outcome and latency
```

The app supplies the option set. Begin with `allow`, `nudge`, `ask`, and user-command actions such as `open_alarm`. Include `unknown/ask` and a user-configurable threshold, validated on our tasks. Screen text and app content are input data; they must not modify executor permissions. Prefer Android intents for alarms/timers and app launching; use accessibility only for user-enabled, scoped actions that require UI interaction. Keep autonomous transfers, messages, and destructive actions outside the demo executor.

For voice, make speech-to-text an interchangeable adapter and show whether it is local. Android speech recognition availability does not guarantee offline execution; verify the installed recognizer/model or use a separately downloaded local ASR. TTS also needs an offline voice check. A typed command path should remain available for the demo.

## Few-shot learning, fine-tuning, and interpretability

**Few-shot prompting** supplies examples at inference and does not alter weights. **Retrieval/personalization** uses saved user examples or policy settings and also does not imply training. **Fine-tuning** updates weights or an adapter offline, then exports a versioned model back to the phone. Our demo should name the mechanism actually implemented.

Build a labeled sandbox first: focus goal, foreground package, elapsed time, command text, permission status, expected intent, and expected action. Include ambiguous commands, near-limit usage, denied permission, unavailable app, screen changes, and legitimate productive Instagram use. Split by user/scenario/template family rather than randomly duplicating near-identical examples. Keep a real-phone holdout separate from generated examples. A teacher can create labels offline, but teacher use does not imply cloud dependency during deployed inference.

The transparent policy experiment should be small and independent of the LLM: nonnegative inputs and weights for **distraction evidence only**, such as normalized overtime, repeated reopen count, and configured distraction status. Show each contribution and ablate one feature at a time. Model productive context in a separate explicit exemption/permission gate; forcing every contextual variable into a positive network makes contradictory behavior difficult to express.

A nonnegative monotone network is not automatically mechanistically understood. For the tiny policy, test monotonicity, visualize neuron/concept contributions, and perform interventions that change one factor while holding the others fixed. For Laya/Kev, attention displays and probability distributions are useful diagnostics but not causal explanations of the entire model. Treat LLM circuit analysis as a later research stretch; the hackathon proof can honestly explain the small coaching policy and its limits.

The user's financial accountability idea should initially be a visible **simulated commitment ledger** with configurable stakes and undo. Monetary deduction must not depend on an unvalidated language-model classification. It can later use a separate, explicitly authorized payment workflow; do not portray virtual points as a real debit.

## Reproducibility and source checkout pins

Read-only shallow source checkouts in ignored `research/`:

| Repository | Inspected commit |
| --- | --- |
| `jaredpalmer/kev` | `84847f0a883d900f7de5b7a57eaa341ca7f9a6b4` |
| `receptron/laya` | `6478649e723122ca24bbf5fb69ed1010023c9750` |
| `trycua/cua` | `ab628e0d1cf1e993eef2f7f99d9ed8faf364506c` |

No weights or third-party dependencies were installed. Research checkouts occupy approximately 1.5 GB combined. Do not commit them or API secrets. Before any model download, resolve the selected Hugging Face revision to a full commit, record filenames and SHA-256 hashes, retain model licenses/notices, and record the converter/runtime versions. Source pins above are not model-weight pins.

CUA's published small-artifact reference pins, if later needed: Nano `abbd98492307dc20373f79f7141725412df63c42`; forms `4a7a9f42a3d42e6dfbd111c0c843e37ac50f1332`. These are references only; no artifact has been loaded here.

## Deadline decision

Ship the native observation/action loop and an honest local inference baseline first. Time-box QNN conversion once the target hardware is identified. If full NPU execution misses the deadline, retain the working offline CPU product and explicitly describe NPU integration as pending. If Laya conversion is too slow, use a very small app-specific trained scorer plus an independently validated tiny local LLM; label rule-only/demo paths clearly. Do not spend the remaining time building a general GUI agent, porting fleet infrastructure, or attempting broad LLM mechanistic interpretation.
