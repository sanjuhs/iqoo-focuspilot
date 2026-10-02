# Verified status

Updated 2 October 2026 (IST). This file separates measured results from goals.

## Verified

- Public guide/Terms/track research completed; Finale is October 9–11, with event-written code rules.
- Public repository created and initial documentation pushed:
  https://github.com/sanjuhs/iqoo-focuspilot (initial commit `7abfa1b`).
- `.env` exists with `OPENAI_API_KEY`; ignored, values never printed or copied into source.
- Android SDK 35/36, platform tools, Java 17 and cached Gradle 8.14/AGP 8.12.1 available.
- Phone initially unauthorized; user accepted RSA prompt and ADB now reports `device`.
- Read-only shell check succeeded: Settings package located.
- Device properties: Nothing A059, Android 16, API 36, SoC `SM7635`, `arm64-v8a`.
- Android lab APK built, installed and launched on Nothing A059. Four JVM tests and
  lint passed (zero errors); app has no INTERNET permission. Device start/pause,
  sandbox nudge and cooldown verified. Broader runtime/permissions remain unverified.
- Fixed system-bar insets after actual device visual inspection.
- Laya 421M pinned/checksummed comparison runs on laptop ONNX CPU: 15 smoke cases,
  13/15 labels correct; warm median 234 ms/p95 249 ms on Apple M4 Pro. Four tests,
  including real inference with JavaScript fetch disabled, passed. This is not phone/NPU evidence.
- A separate 65-parameter positive-weight network was actually trained on synthetic
  scenario-group splits: 472/480 holdout correct, seven tests passed, 1,800 monotonic
  pairs with zero violations. This reproduces a synthetic teacher, not human productivity
  or LLM mechanistic understanding; not yet integrated with the Android app.
- Research checkouts, downloaded weights and dependencies are ignored. Workspace
  was about 3.9 GB before the new 0.8B runtime/build experiment.
- User selected Qwen3.5-0.8B Q4_0 as main model, expanding the initial size cap.

## In progress

- Friendly animated goth companion inspired by user's earlier MIT project;
  opt-in persistent focus monitor with foreground notification/Stop.
- Qwen3.5-0.8B laptop and Android-native CPU port, distinct from measured phone inference.
- Selected-activation instrumentation and controlled command-model experiment.
- Updated GitHub backup and staged secret audit.

## Unverified / remaining

- Completed direct-entry application, deadline, required video format and admission.
- Permission to reuse any pre-event prototype in an eligible event submission.
- Full APK end-to-end/permission/voice/alarm/background behavior beyond verified slice.
- Phone LLM inference, language-model fine-tuning, few-shot improvement and causal outcomes.
- Snapdragon NPU execution, acceleration metrics and Office Kit on an iQOO device.
- Persistent monitoring under actual OEM lifecycle, wake word and general cross-app automation.
- Real financial deductions: out of scope; accountability balance is simulated.
- Final demo recording and submission receipt.

The broader goal remains active. A plan, APK shell or public repository alone is
not completion of the entire assistant or a hackathon submission.

## Model/precision research — 2 October 2026

This review concerns the user-confirmed intended **iQOO 15, 16 GB physical RAM**,
not the measured Nothing development device. No models were downloaded or run
in this review, and no app implementation scope was changed.

- [Snapdragon 8 Elite Gen 5 product brief](https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/images/company/news-media/media-center/press-kits/snapdragon-summit-2025-press-kit/day-2-/documents/Snapdragon8EliteGen5_ProductBrief.pdf)
  lists INT2, INT4, INT8, INT16, FP8 and FP16 with mixed precision. Native FP4
  is not listed. A 4-bit GGUF does not prove FP4 arithmetic or NPU execution.
- [Official Qwen release history](https://github.com/QwenLM/Qwen3.8) confirms
  Qwen3.8 exists. [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) is dense:
  nominal 4-bit language weights alone require 13.5 GB before vision, scales,
  cache, runtime and Android. No official sub-10B Qwen3.8 checkpoint was found.
  Nominal 2-bit packing (6.75 GB) is not evidence of usable quality/performance.
- Current small candidates: [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B)
  and [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B), using hybrid recurrent
  and attention components plus a vision encoder. Instrumentation must cover
  recurrent states. Model availability alone does not establish reliable phone
  automation or screenshot understanding.
- Qualcomm publishes universal GENIEX_LLAMACPP q4_0 assets for
  [0.8B](https://huggingface.co/qualcomm/Qwen3.5-0.8B) and
  [2B](https://huggingface.co/qualcomm/Qwen3.5-2B). Its 512-context mobile rows
  range roughly 46–81 and 30–40 generated tokens/s respectively, on Snapdragon
  8 Elite Gen 5 For Galaxy. Repeated rows represent different configurations
  without compute-unit labels in the extracted table. They are vendor reference
  results, not iQOO measurements or unequivocal NPU benchmarks.
- [GenieX platform documentation](https://github.com/qualcomm/GenieX/blob/main/docs/en/get-started/platforms.mdx)
  lists SM8850 Android/Kotlin support. Its GGUF runtime can target Hexagon,
  Adreno OpenCL or CPU, including explicit hybrid HTP+CPU scheduling. Its QAIRT
  runtime uses per-chipset compiled NPU bundles. [Runtime notes](https://github.com/qualcomm/GenieX/blob/main/notes/run.md)
  prefer Q4_0/Q8_0 over Q4_K_M for HTP; validate operations, placement and fallback
  on the actual phone. A runtime label alone does not establish NPU acceleration.
- [Qwen3-0.6B](https://huggingface.co/qualcomm/Qwen3-0.6B) and
  [Qwen3-1.7B](https://huggingface.co/qualcomm/Qwen3-1.7B) offer ordinary text
  transformer alternatives and list GENIE w4a16 QAIRT 2.45 artifacts for the
  For Galaxy chipset. iQOO compatibility and the current migration from GENIE
  remain unverified. w4a16 means 4-bit weights / 16-bit activations.
- Non-Qwen candidates: [Gemma 4 E2B](https://ai.google.dev/gemma/docs/core),
  [Ministral 3 3B](https://docs.mistral.ai/models/ministral-3-3b-25-12),
  [SmolLM3 3B](https://huggingface.co/HuggingFaceTB/SmolLM3-3B). Gemma E2B denotes
  effective parameters, not the full weight count. Google provides mobile
  QAT/LiteRT-LM formats with targeted 2-bit layers; published loading-memory
  estimates exclude context/software overhead and do not prove iQOO NPU use.
- Research recommendation: compare Qwen3.5-0.8B and 2B at 4-bit for current small
  inference; Qwen3-0.6B/1.7B for conventional-transformer instrumentation and
  Qualcomm deployment comparisons; Gemma 4 E2B mobile for multimodal evaluation.
  Benchmark task success/arguments/abstention, peak RAM, prompt and decode
  latency, power/thermals, actual backend and activation-capture overhead.
  Activation heatmaps do not establish causal mechanistic understanding.
