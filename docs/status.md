# Verified status

Updated 2 October 2026 (IST). This file separates measured results from goals.

## Natural-command update 0.8

- App source `a214bd7fc6ddd3cc3917d7a1f1aa9d854b7f3eb3` adds full-request
  validation, bounded English integer/duration/clock slots and friendly examples.
  Qwen3.5-0.8B Q4_0, its prompt and optimized CPU library are unchanged; the
  separate trained representation classifier remains unpromoted.
- **119 JVM tests pass**, zero failures/errors/skips; lint zero errors/59 warnings.
  Four independent evaluation tests and ten artifact-audit tests pass. Both signed
  light/bundled APKs passed packaged native/model/license/permission inspection.
- Frozen-before-edit independent 100 requests/50 families: raw semantic model
  29/100 (29/40 supported intents; all 60 unsupported requests proposed non-unknown).
  Generated model + v0.7→v0.8 strict correctness **64→72/100**, supported **9→12/40**,
  wrong accepts **5→0**. New gate has 28/40 false abstentions and nine gains/six
  regressions; oracle support 14→19/40 still leaves 21 false abstentions. No actions
  executed, prompt/data/source repairs or autonomous reliability claim.
- Light APK installed on Nothing; actual installed APK and retained private-model
  hashes verified. Before install, session checkpoint paused and points 100;
  observation absent/default-off. No OS permissions changed. Own-app foreground
  remained unavailable on the sleeping phone; physical v0.8 outcomes are pending.
- [Contract and limits](natural-commands.md),
  [artifact identities](natural-commands-artifacts.json),
  [frozen evaluation](../prototype/command-v08-eval/README.md). Historical phone,
  timer and research results below keep their original binary/source scopes.
- Latest measured logical workspace size is **11.51 GiB**, within the authorized
  15 GB ceiling. No model download or paid API use in this update.
- [0.8 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.8)
  publishes both APKs and their manifest. All three server sizes/SHA-256 digests
  match local files and the source tag matches the stated app commit.

## Frozen-Qwen decision-head research

- Actual read-only CPU extraction captured 373 full 1,024-coordinate Qwen3.5
  `result_norm` vectors from the unchanged complete Android prompt, fresh context
  per request. Protocol/data/template identities were frozen before capture.
- A separate **7,175-parameter signed linear head** completed 400 updates on 222
  synthetic training rows; 61 validation rows selected abstention before 90
  held-out rows were scored. Qwen weights and Android APK remain unchanged.
- Same-set raw intent correctness: autoregressive **46/90**, head **76/90**.
  Unknown false accepts: **24/24** vs **9/24**. Selected abstaining head: **66/90**,
  43/90 coverage and 0/24 unknown false accepts. Threshold **1.0** relies on
  rounded softmax saturation and is explicitly unsuitable for deployment.
- Actual frozen v0.7 gate yields only **15/65** correct supported actions for the
  selected head versus **17/65** for generation; required abstentions 25/25 for
  both, no wrong accepted proposals in this set and no actions executed. This
  research gain does not improve end-to-end command coverage.
- Host extraction setup+prefill median **308.47 ms**; head-only median **0.00904 ms**
  excludes extraction. Generation native median **456.86 ms**. Different context
  construction and sample sets prevent a paired speedup claim; no phone/NPU result.
- Contribution reconstruction error 1.71e-13 and head-input intervention error
  2.70e-13 verify the separate classifier's algebra. No semantic coordinate names
  or full-Qwen causal understanding are established. Seven focused tests pass.
- Candidate remains unpromoted. [Report](intent-head.md),
  [aggregate evidence](../prototype/intent-head/results.json). Application copy
  and recording script now reflect current verified and pending features.
- Latest measured logical workspace file size is **10.98 GiB**, within the
  authorized 15 GB ceiling. No new model download or cloud/API expense.

## Timed focus update 0.7

- App source `6bd4841b170be0445470eff9977133bc2accc8f6` adds reviewed countdowns,
  a 25-minute shortcut, one-second visible clock updates, retained remainder on
  pause/resume and bounded focus/status explanations. Timed replacement preserves
  accumulated focus time; completed Start begins open-ended. Recovery stays paused.
- **105 JVM tests pass**, zero failures/errors/skips; lint zero errors/59 warnings.
  Seven new pure timer tests and five gate regressions are post-test repairs;
  they are not an independent accuracy gain or proof of Android sleep handling.
- Light and bundled APKs passed signature/model/native/license/permission inspection.
  Model and optimized CPU runtime are unchanged. Light installed on Nothing;
  the timed phone test refused the unlocked-own-app foreground precondition before
  inference or action. Subsequent read-only status found the phone asleep and our
  app not focused. Physical countdown verification awaits the user's unlock.
- [Timer contract](timed-focus.md), [artifact identities](timed-focus-artifacts.json).
  Handler delivery can be delayed by deep sleep; elapsed/usage accounting caps at
  the deadline when the app can run. No exact-alarm/wakelock or 24/7 promise.
- Workspace logical file size **10.96 GiB**, within the authorized 15 GB ceiling.
  [0.7 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.7)
  contains both APKs and the artifact manifest. Voice/monitor/actual iQOO/NPU/Office Kit and final
  event eligibility/submission remain pending as recorded below.

## Command readiness and laptop bridge update 0.6

- Research build source is `29c4c3372fcc913d3672e59803a3aa870fa2426b`. Both APKs and
  hash evidence are in the [0.6 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.6);
  earlier releases and the 0.3 concept pitch remain historical.
- **Set up Mira** was opened on Nothing A059/API36: Usage Access off, notifications
  blocked and microphone off were displayed. No permission changed, monitor started
  or voice recording began. [Setup and repeat procedure](command-readiness.md).
- Exact installed light-APK/model/native identities bind the typed phone test to
  v0.6. Qwen Start took **17,323 ms** and Pause **1,814 ms**; both proposals required
  review, were explicitly confirmed, and changed the private session checkpoint
  active then paused. Alarm cancellation took **1,655 ms**, was wrongly proposed
  as `alarm`, and the independent gate **ABSTAINED**; no Clock action executed.
  Final state: focus paused, usage reading off, virtual points 100.
  [Phone evidence](command-readiness-phone.json). Three observations are not p50/p95.
- Root measured logical workspace file size at **10.43 GiB** on 2 October, within
  the authorized 15 GB ceiling; this is measured file size, not peak RAM.
- Integrated host build: **93 JVM tests pass**, zero failures/errors/skips; lint zero
  errors and **60 warnings**. These reports describe this research build; newer tests
  must not be attributed to earlier APKs.
- Frozen 58-case native host evaluation: raw semantic intent correct **25/58**;
  gated exact action/slot or correct abstention **49/58**; supported strict requests
  correct **16/23**. Two wrong accepted proposals remain explicitly reported: timed
  focus became open-ended focus, and erase-picture became local status display.
  No actions ran in this evaluation. Format validity did not establish correctness.
  [Evaluation and counterexamples](command-reliability.md).
- Offline laptop consumer validates bounded private exports and replays the pinned
  existing policy, without retraining, input discovery, uploads or phone actions.
  It emits aggregate scores/counts plus byte/provenance identities, omitting app
  identity, goal hash, timestamps and vectors. **15 tests pass**; an actual Java-rendered
  synthetic export parsed/replayed through the Python CLI: three records, one exact
  context group. [Interoperability evidence](bridge-java-interop.json) is a temporary
  local-file workflow, **not actual app usage/export or Office Kit transfer**.
- [Office Kit export workflow](officekit-export-workflow.md) documents the implemented
  laptop-compute piece and current official India desktop V6+/OriginOS6+/account
  guidance. Physical ASR/TTS, Clock outcome, user-enabled live/background monitoring,
  disconnected offline execution, actual iQOO/NPU execution and Office Kit pairing/
  transfer remain pending. Event eligibility, authenticated cutoff/admission and
  accepted submission are still external completion gates.

Earlier sections preserve their release-specific observations and limitations.

## Observed learning update 0.5

- Research source adds a fresh current-foreground gate before recurring budget nudges.
  Cumulative over-budget time alone cannot charge again after leaving the selected app.
  Clock alignment, consent, permission, focus, scope and cooldown remain required.
- Separately opted-in private real-summary labels can veto a normal nudge only for a
  matching Allow. Nudge labels cannot create actions or bypass the original gates.
  Label review retains a complete foreground sample for at most 15 seconds; current
  decisions never use that retained history. No real-phone accuracy gain is claimed.
- Optional Accessibility service implements actual selector ACTION_CLICK and checked/
  visible postcondition verification for two controls inside the own-app synthetic
  sandbox. Exact Activity/window/root, manual five-second arm and cancellation are
  enforced. Android enablement and a physical service proof remain pending.
- Manual private summary export uses a user-chosen document destination. It excludes
  task text, raw event trail/screens/tensors and other-app identities. Failed deletion
  or provider writes report an unconfirmed result. Physical export remains pending.
- Integrated host build: **89 JVM tests pass**, zero failures/errors/skips; Android lint
  zero errors (52 warnings). This report describes 0.5 source, not already published 0.4 APKs.
- Installed 0.4 evidence has now been bound to its exact bundled APK/private-model
  hashes: typed positive request required review at 1,705 ms; negation was wrongly
  proposed as start_focus but independently rejected at 1,710 ms. Neither performed
  an action. [Exact binding](companion-phone-bound-v04.json).
- Both 0.5 signed debug APKs were built; bundled model/native hashes match the pin.
  Light and bundled APKs installed on Nothing. Actual own-app permission-off UI
  showed learning disabled with zero labels after a blocked save, and the selector
  sandbox reported its service disconnected. No permission or selector was enabled.
- Exact installed 0.5 bundled APK/private-model hashes were verified. Positive typed
  command required review at 11,583 ms first request; negation was wrongly proposed
  as start_focus but independently rejected at 1,723 ms warm. No action executed.
  [Phone binding](observed-learning-phone.json). Disconnected offline proof is pending.
- [0.5 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.5)
  contains both APKs and artifact hashes, preserving earlier packages/video.
- Actual local QLoRA performed 80 updates of 55,296 Qwen adapter parameters on laptop
  GPU with frozen synthetic families. Canonical decoder baseline 29/41 vs adapter
  12/41; unsupported abstention 3/13 vs 0/13. Candidate rejected; phone base unchanged.
  Format learning is not safe semantic improvement. One exported adapter host fixture
  loaded successfully; this is compatibility evidence only. [Training report](qwen-finetuning.md).
- At the latest read-only check, microphone/notifications remain ungranted and Usage
  Access is default. User permission steps are pending; no ADB grants were used.

## Companion update 0.4

- Source backed up at `3bcf8a8`; [0.4 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.4)
  published with both APKs and evidence JSON. GitHub reports all four assets uploaded;
  APK digests match the local artifact manifest. Earlier release/video remain preserved.
- Integrated Android build: **47 JVM tests pass**, lint has zero errors, light APK
  installs and launches on the same Nothing phone. App still has no INTERNET permission.
- Final 0.4 light/bundled APKs passed packaged model/native hash and permission checks;
  bundled APK installed, and both companion screens launched. Bundled weights match
  the exact 0.3 pin; fresh import was tested in 0.3 rather than repeated here.
  [Artifact sizes and hashes](companion-artifacts.json). Workspace is now about 8.2 GiB.
- Ask Mira now includes the original animated companion, styled action controls and
  draft-only on-device speech integration. Main shortcuts use the same cancellation
  and late-callback gate. Seven speech-state tests pass; no physical ASR/TTS claim.
- Actual typed phone smoke: start-focus proposal required review (15,871 ms first
  request); negated request was wrongly classified by Qwen but independently rejected
  (1,736 ms warm). No actions executed. See [phone evidence](companion-integration.json).
- Private task and explicit planned/continuous limits saved through actual phone UI;
  saving pauses focus. Test settings were cleared afterward. Missing observation
  consent blocked the shadow panel, and invalid deferral left points unchanged.
- Ten new timestamp/feature/feedback tests verify the six-input shadow policy.
  Missing values remain missing; the trained score changes no actions or points.
  [Mapping and limits](live-policy-evidence.md) distinguish real summaries from
  synthetic training. Complete live event/battery/permission testing is pending.
- Microphone and notification permissions remain ungranted; Usage Access remains
  default/ungranted. No permission was changed through ADB. The phone remains paused.
- Isolated GenieX 0.7.0 adapter compiles against the published AAR and Android 36;
  six preflight tests pass. SM8850 is vendor-validated; this SM7635 is outside its
  validated set. [Deployment preparation](snapdragon-deployment.md) is host evidence,
  with no SDK integration, NPU execution or Office Kit pairing claimed.

The prior 0.3 release and 4:53 research pitch remain a preserved baseline. Newer
source does not turn that video into proof of real speech, NPU or live training.

## Verified

- Public guide/Terms/track research completed; Finale is October 9–11, with event-written code rules.
- Public repository created and initial documentation pushed:
  https://github.com/sanjuhs/iqoo-focuspilot (initial commit `7abfa1b`).
- `.env` exists with `OPENAI_API_KEY`; ignored, values never printed or copied into source.
- Android SDK 35/36, platform tools, Java 17 and cached Gradle 8.14/AGP 8.12.1 available.
- Phone initially unauthorized; user accepted RSA prompt and ADB now reports `device`.
- Read-only shell check succeeded: Settings package located.
- Device properties: Nothing A059, Android 16, API 36, SoC `SM7635`, `arm64-v8a`.
- Android lab APK built, installed and launched on Nothing A059. Twenty-six JVM tests
  and lint passed (zero errors); app has no INTERNET permission. Device start/pause,
  sandbox nudge and cooldown verified. Broader runtime/permissions remain unverified.
- Qwen3.5-0.8B Q4_0 actually loaded from checksummed app-private storage and generated
  inside the Android process through CPU JNI. First request: 19,853 ms total
  (18,626 prefill / 1,227 decode); next request with capture: 4,107 ms total
  (3,178 / 928). Both proposed start_focus correctly, with independent review gates.
  Context 1,024, four threads, 158 prompt / eight generated tokens. Two smoke
  observations do not establish p50/p95, accuracy or capture overhead.
- Actual phone activation observations succeeded: ffn_out-0/11/23 and result_norm,
  1,024-wide vectors summarized at last prefill position. This is observational
  evidence, not causal semantic interpretation.
- Phone memory snapshot during loaded-model testing: PSS 791,083 KiB, RSS 899,052
  KiB; one sample, not a measured peak. Model bytes 563,036,064 / SHA-256
  57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf.
- Original native Canvas companion Mira and opt-in foreground monitor code built.
  Actual phone artwork inspected; persistent service/notification tests await user permissions.
- Fixed system-bar insets after actual device visual inspection.
- Laya 421M pinned/checksummed comparison runs on laptop ONNX CPU: 15 smoke cases,
  13/15 labels correct; warm median 234 ms/p95 249 ms on Apple M4 Pro. Four tests,
  including real inference with JavaScript fetch disabled, passed. This is not phone/NPU evidence.
- A separate 65-parameter positive-weight network was actually trained on synthetic
  scenario-group splits: 472/480 holdout correct, seven tests passed, 1,800 monotonic
  pairs with zero violations. This reproduces a synthetic teacher, not human productivity
  or LLM mechanistic understanding. Exported Android Java policy matches all 480
  holdout outputs (maximum score error 1.22e-15); separate sandbox UI built.
- Research checkouts, downloaded weights and dependencies are ignored. Workspace
  is about 7.6 GiB including models, checkouts and incremental builds.
- User selected Qwen3.5-0.8B Q4_0 as main model, expanding the initial size cap.
- Native pre-entry/in-flight cancellation race fixed and real host JNI checks pass.
  Updated phone build cancellation settled correctly; a fresh captured request
  then produced start_focus in 1,869 ms with I8MM confirmed.
- Safe phone model preparation now force-stops only the research app, checksums
  a temporary private file and atomically renames it; actual retransfer succeeded.
- Latest CPU backend log on phone verifies actual KleidiAI I8MM kernel selection.
  Confirming a local-model proposal started the actual focus state; dashboard Stop
  returned its persisted checkpoint to paused. Latest request 1,688 ms.
- First optimized ARM CPU five-case phone smoke completed: first request 13,521 ms; three
  unobserved warm cases 1,646/1,724/1,663 ms; captured warm 1,719 ms. Model misclassified
  negated/compound requests as start_focus; independent gate rejected both. No
  actions executed in that batch. See prototype/native/phone-smoke-optimized.json.
- Local few-shot sandbox phone screen opens; saving and deleting synthetic labels
  verified against app-private storage. Gates stayed paused/off; no actions ran.
- Local few-shot sandbox implemented with 32-record limit, neighbor explanations,
  delete controls and non-overridable simulated gates. Eight targeted JVM tests
  passed; 720 synthetic Java/Python outputs match. Answered-case accuracy improves
  under shifted toy preferences, but coverage about 70% and total correct count is
  below the trained baseline because of abstentions. No language-model fine-tuning
  or live personalization claim.
- Actual laptop Qwen activation-write experiment ran 108 fresh-context cases.
  Selected channel patch/ablation gave no reliable steering advantage; random
  controls comparable, held-out baseline 6/8. All 16 no-op/restoration full-logit
  comparisons exactly matched. This is a negative semantic result with verified
  intervention machinery, separate from observational phone capture.

- Research pitch rendered at 1080p/H.264/AAC:293.208 seconds, 42 narration/caption
  segments. Full FFmpeg decode, audio levels and encoded frame layouts checked;
  sanitized phone system bars cropped. Evidence in docs/pitch-evidence.json.

- Standalone bundled APK installed on Nothing with the private model initially
  absent. It imported the pinned asset and verified SHA in 1,089 ms, loaded CPU
  runtime in 2,299 ms, and proposed start_focus in 1,654 ms. No ADB model transfer
  was used for this import. Temporary parity-checked backup was cleaned.
- Both light 5.45 MB and bundled 568.49 MB APKs include six license/notice assets;
  26 JVM tests/build/lint passed for both. ZIP inspection verifies the bundled
  uncompressed model size and SHA. See docs/research-artifacts.json.

- Source commits 6487c27/5d75293 and research-v0.3 prerelease are public on
  GitHub. Both APKs, sanitized pitch, captions and evidence manifests uploaded;
  GitHub asset digests match local SHA-256 values. Secret/index checks passed.
  https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.3

## In progress

- Actual persistent notification/Stop verification after user grants permissions.
- Optimized ARM CPU inference comparison; generic baseline preserved.
- Few-shot retrieval remains a sandbox; integration into recurring live decisions
  requires additional user-labelled evaluation.
- Controlled command-model experiment completed with a negative steering result;
  phone replication and wider controls remain pending.
- Future source changes continue through staged secret audits.
- Final APK/background/voice/clock verification when the required user permissions
  and hardware are available.

## Unverified / remaining

- Completed direct-entry application, deadline, required video format and admission.
- Permission to reuse any pre-event prototype in an eligible event submission.
- Full APK end-to-end/permission/voice/alarm/background behavior beyond verified slice.
- Airplane-mode/USB-disconnected proof, beneficial deployed language-model fine-tuning,
  real-user few-shot improvement and causal LLM outcomes. Actual app-process CPU inference is verified.
- Snapdragon NPU execution, acceleration metrics and Office Kit on an iQOO device.
- Persistent monitoring under actual OEM lifecycle, wake word and general cross-app automation.
- Real financial deductions: out of scope; accountability balance is simulated.
- Eligible final live demo and submission receipt. A 4:53 research concept pitch
  with local narration/captions is rendered; it uses sanitized stills and original
  diagrams, not continuous live phone footage.

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
