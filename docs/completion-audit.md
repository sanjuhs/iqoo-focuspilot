# Completion audit — 2 October 2026, IST

This project is an implemented **pre-event research prototype**, with useful public artifacts and some reported Nothing-phone behavior. It is **not a completed iQOO deployment or an eligible, accepted hackathon submission**. This audit preserves the full requested scope; it does not redefine success as passing tests, publishing an APK, or recording a concept video.

The requirements were read from `instructions.md`, `plan.md`, `hackathon.md`, and `docs/status.md`, including later additions: a friendly companion, local model, few-shot personalization, interpretability, foreground monitoring, voice, iQOO NPU deployment, Office Kit, open-source backup, and submission. Broader cross-app control and IoT remain proposed work; actual local LLM fine-tuning is now being evaluated separately and is not promoted to the phone; these cannot be inferred from the current assistant UI.

## Reproduce the read-only audit

```sh
python3 -m unittest discover -s scripts -p test_audit_deliverables.py -v
python3 scripts/audit_deliverables.py --live-github > artifacts/completion-audit.json
```

The auditor reads only named project evidence, APK ZIP contents, host XML reports, video metadata, and public repository/release metadata through `gh`. It streams existing local files; it does not download weights, scan credentials, operate a phone, install anything, or upload. Optional `--manual-proof path.json` accepts evidence bundles with `{requirement: {artifacts: [{path, sha256}]}}`; matching hashes still require human review and never automatically certify NPU, Office Kit, voice, offline operation or event eligibility. Paths escaping the public project evidence directories, including symlink escapes, are rejected.

“Verified” is scoped to a specific byte, arithmetic, signature, source binding or metadata check. JSON reports of physical behavior remain attributed observations, not independent repetitions. The machine-readable report always leaves `goal_complete` false.

## Current 0.7 addition

The auditor also inspects both 0.7 APKs and their public assets, bound to app source
`6bd4841b170be0445470eff9977133bc2accc8f6`. It reports the phone-countdown requirement
as **incomplete** while no separate physical report exists. The APK installed, but
its own-app unlocked/foreground precondition failed before inference or action.
Current XML contains 105 JVM tests and lint zero errors/59 warnings; these do not
prove a phone deadline, deep sleep or process recovery. The regression fixes are
post-test changes against known 0.6 failures, not a newly measured held-out gain.
See [timed focus](timed-focus.md) for behavior, reproduction and unverified cases.

## Previous 0.6 addition

The auditor now includes both 0.6 APKs, their required release assets and the
separate [phone report](command-readiness-phone.json), bound to the **light** APK
with already present, verified private weights. Source attribution is
`29c4c3372fcc913d3672e59803a3aa870fa2426b`. Two typed model proposals were reviewed
and confirmed through the own-app UI: focus started and then paused. A wrong alarm
creation proposal for cancellation was rejected. These observations establish no
ASR, Clock, disconnected-offline, NPU or Office Kit result. A new bundled-import
test was not performed. Current host XML reports 93 JVM cases and lint zero errors
with 60 warnings; these reports must not be attributed to historical releases.

The separate frozen [58-case command evaluation](command-reliability.md) reports
25/58 raw intent matches, 49/58 correct gated actions or rejections, and 16/23
correct supported actions. Two accepted proposals were wrong, including a timed
focus request becoming an open-ended session. The [laptop export consumer](officekit-export-workflow.md)
passes 15 synthetic tests; actual Java-renderer → Python-CLI interoperability was
tested with a synthetic fixture. Neither result proves real usage or Office Kit
transport. Historical audit findings below retain their original version scope.

## What the actual audit establishes

| Requirement | Evidence and result | Remaining scope |
|---|---|---|
| Open-source source backup | Public [MIT repository](https://github.com/sanjuhs/iqoo-focuspilot); public main matched local committed HEAD at inspection. | Uncommitted changes are not backed up by HEAD parity. A source ref is not a device-runtime binding. |
| Reviewable delivery | All ten existing asset sizes and server SHA-256 digests on [research v0.4](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.4) and [research v0.3](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.3) matched local files. Required assets were present. | GitHub metadata parity, without redownloading the large assets. This is delivery evidence, not submission acceptance. |
| Installable Android payload | Both v0.4 APK signatures validated, packaged manifest/DEX and ARM64 library found; package `dev.focuspilot.prototype`; packaged permissions parsed by `aapt2`. | Cryptographic validity does not establish trusted publisher identity or installation on a particular device. |
| Local model packaged | Bundled APK contains exactly one 563,036,064-byte Qwen3.5-0.8B Q4_0 GGUF, uncompressed, matching the declared model hash. Light APK contains no GGUF. | The 0.8B choice is the user's later expanded scope; it exceeds the original 0.1–0.5B idea. Packaging does not prove execution or offline state. |
| License notices | Six APK notice files exactly match the project’s MIT, Qwen Apache, llama.cpp MIT and KleidiAI Apache/BSD/notices source files. | Notice parity is not an independent legal opinion or proof of every upstream provenance claim. |
| Network isolation | Both v0.4 packaged manifests contain no `android.permission.INTERNET`. | An actual airplane-mode, USB-disconnected complete workflow remains unrecorded. System speech/TTS/Clock dependencies need separate offline testing. |
| Native CPU implementation | Current native source hashes match the optimized build manifest; both APK native hashes match. Manifest explicitly reports no GPU/NPU inference. | Source identity is not a compilation replay. Nothing CPU evidence cannot establish iQOO NPU execution. |
| Host verification | At the first inspection, actual XML contained 47 JVM cases, zero reported failures/errors, no skipped tests; declared counts and failure child elements agreed. Lint had zero errors and **46 warnings**. The later generated audit sees **89 cases**, zero failures/errors/skips. These newer reports are not evidence for the already released v0.4 APK. The generated audit measures the currently present reports, which may be superseded during further implementation. | Report timestamps/mtime are recorded, but files are not bound to a particular APK/source hash. Newer test counts must not be attributed to older APKs. They do not certify Android lifecycle, microphone, Usage Access or phone hardware behavior. |
| Phone command safety | Historical phone reports show negative/compound model mistakes proposing `start_focus`, with independent validator `ABSTAIN` and no action. | Fast historical benchmark used a different native hash from v0.4. New `companion-phone-bound-v04.json` matches the exact bundled APK/native/private-model hashes and release source attribution. Its two typed cases report 1.705/1.710 seconds, review/ABSTAIN and no action. Existing `companion-integration.json` remains historical and unbound. |
| Focus, virtual balance, cooldown, override | Existing implementation and host tests support reviewable local behavior; reported prior actual confirmed focus action and Stop exist. | Fresh permissions, real selected-app time boundaries, revoked permissions, notification Stop and process/OEM recovery need user-enabled device proof. Never claim a money transfer. |
| Persistent companion | Procedural original avatar and dashboard are source-visible; consent/Stop/motion controls exist. | Animation is not model activity. No constant microphone or absolute 24/7 process-survival guarantee is established. Companion preferences need device usability verification. |
| Explainable trained head | Metric arithmetic verifies 472/480 synthetic holdout correctness (98.33%), three false nudges and five misses; checkpoint parameter hash and generated Java/source identities match. | A 65-parameter toy head trained on invented labels is not the language model, a positive-only network including biases, or real-human productivity accuracy. |
| Few-shot research | All recorded source/checkpoint hashes match. Across 720 grouped synthetic cases, coverage is about 70–73%, selective answered accuracy improves, but total correct cases fall from **558 to 445**. | This is retrieval/abstention research, not LLM fine-tuning. Live consented workflow accuracy and false-nudge rates remain unknown. Abstentions are not counted as correct. |
| LLM mechanistic experiments | Probe/runner/model identities agree; 16 recorded no-op/restoration control records have matching reported full-logit hashes, candidate values and zero delta. | Raw full logits were not recomputed by this auditor. Selected opposite patches and random patches both changed **zero** held-out intents: no steering advantage was established. CPU laptop experiment, not phone/NPU causal validation. |
| 3–5 minute pitch | Existing video hash matches; `ffprobe` measures **293.208333 seconds**, 1920×1080 H.264 with audio. All 42 SRT caption intervals are ordered and within the video; the complete streams decode with FFmpeg. Narration, renderer, caption and video hashes bind to render metadata. | It is a concept/research pitch with title cards and a historical app still, not a live feature walkthrough or eligible final entry. Full human listening and final pitch review remain needed. |
| Pitch asset provenance | Original SVG authoring is documented; phone crop `[0,126,1080,2292]` is recorded to remove status/navigation areas. Current asset hashes can be observed. | Historical renderer metadata did not bind avatar/still input hashes. New hashes cannot retroactively establish the exact render inputs, capture consent or visual privacy. Human privacy review is required. |
| Voice and Clock | On-device ASR/TTS and reviewed alarm interfaces are implemented and described in `docs/voice-integration.md`. | Actual permitted speech/transcription/TTS, denied/revoked/offline behavior, and confirmed Clock postcondition remain manual device tests. No voice success inferred from typed examples. |
| iQOO / NPU | Isolated Qualcomm adapter/preflight research exists; selected CPU fallback and hardware placement requirements are documented. | Actual iQOO15 identity, runtime/model transfer and correlated executed HTP operator trace are missing. SDK compilation, “NPU” labels and timing cannot certify execution. |
| Office Kit | Public setup/proof checklist exists in `docs/snapdragon-deployment.md`. | Actual eligible account/device pairing and a synthetic phone/laptop handoff outcome are missing. ADB is not Office Kit. |
| Eligible final submission | Official guide/rubric and research plan are documented. | Event-window original code or organizer-approved reuse, authenticated admission/cutoff and accepted receipt remain absent. Current pre-event artifacts cannot satisfy these by being renamed. |

## Concrete artifact identities

- v0.4 light APK: 5,543,813 bytes; SHA-256 `e2fb4f0115881e156c27af60b31f1dc62032061d912512209049c1580df9d8e6`.
- v0.4 bundled APK: 568,579,989 bytes; SHA-256 `966a5390527d35b4901a86048074c62a2f198b96d302e4c7bb9bff1d4e2812c2`.
- Packaged native library: SHA-256 `822695ae5ca3467392f48ff04d9eda824f52a5f470ba48264fd457f51881259e`.
- Packaged Qwen GGUF: SHA-256 `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.
- Published research pitch: SHA-256 `a81bba83c607c07557af55552f9a83b86231449f35159b531a9d29bfb0611d8b`.
- v0.4 source tag: `3bcf8a8af6d9e0ad380470afd96f2c6619e93311`. Newer source does not retroactively become the code running in a released APK.

## Genuine remaining verification and delivery work

The additive `docs/companion-phone-bound-v04.json` now binds reported installed v0.4 APK/native/private-model identities and source attribution. Positive typed input required review; negated input was rejected by the validator; neither test executed an action. It explicitly records `offline_disconnect_verified: false`. This auditor checked identity and report consistency, not a new physical repetition. Published as a unique additional v0.4 asset after this audit; historical evidence must not be overwritten. The v0.5 implementation has its separate observed-learning-phone.json binding and artifact manifest; its reported measurements cannot be inferred from v0.4 observations.

Then perform user-consented voice/Clock, real app-use monitoring, notification/revocation/recovery and USB-disconnected offline checks. Test actual iQOO hardware and collect executed NPU placement evidence before making any Snapdragon acceleration claim. Pair official Office Kit and prove a concrete phone/laptop workflow. Clarify whether broad phone/IoT control and LLM fine-tuning remain required launch scope; do not silently replace them with typed focus commands and a synthetic policy head.

For the competition, verify authenticated admission and dashboard deadline, secure eligible original event code or explicit organizer reuse authorization, and capture an accepted submission receipt. Public research releases and the narrated video are useful preparation, but these external requirements cannot be resolved by local tests or an audit checklist.

The fixture suite tests corruption, missing manifests/assets, wrong native/license contents, deceptive JUnit counts/failure elements, invalid captions, incomplete phone bindings, fabricated metric coverage and claimed NPU proof. Ten fixtures passed at this audit. A passing fixture suite establishes auditor behavior; it does not certify the app’s untested real-world features.

The current auditor also inspects both v0.5 APKs, its separate exact phone binding and all four required v0.5 release assets. v0.4 and v0.3 historical checks remain separate. The v0.5 source tag is `9dade07f1c5a3d627e56a06704826d9b83621599`; phone observations are bound to that APK, while later commits add research/evidence.
