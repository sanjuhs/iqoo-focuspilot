# Mira / FocusPilot — current Phase 1 application copy

Prepared **3 October 2026** from the [v20 structured copy](phase1-form-copy-v20.json).
The live description and video URL are updated and all five public field hashes
match this copy; the existing PDF link remains attached.
[Current UI evidence](phase1-prepared-dashboard-draft-v20.json). Server draft
persistence, document validation and accepted submission remain unverified. The
[earlier prepared draft](phase1-prepared-dashboard-draft.json) and
[earlier form copy](phase1-form-copy.json) remain historical records.
Human experience answers, prior builds, attestation and submission remain pending.

The authenticated dashboard observation shows **Productivity**, one registered
member and the Grand Finale on **9–11 October 2026**. The displayed Phase 1 idea
deadline is **5 October 2026**; its exact cutoff time and timezone are unknown.
The required fields are a title (5–200 characters), description (50–2,000), and
PDF/PPT deck/document up to 25 MB or a document link. Video and prototype URLs
are optional. [Observed requirements](phase1-dashboard-observation.json).

## Idea title

**Mira: A Private Productivity Companion**

## Description — 1,577 of 2,000 characters

Mira is a local-first Android productivity companion that helps people return to the task they intended to do. A friendly animated companion accepts editable typed or optional voice drafts for focus sessions, timers, alarms and a small approved app list. Quick local checks handle familiar requests without loading a language model; unfamiliar wording can use explicitly loaded Qwen3.5-0.8B Q4_0 on the phone's CPU. An independent validator checks complete arguments, and proposed actions require Review and Confirm. User-authored checklists and opt-in app limits support a calmer workflow; accountability uses simulated points.

Our v0.20 light pre-event research prototype is published and installed on a Nothing phone, with 216 JVM tests passing. A default-off availability option is designed to hide Mira while locked and restore the reviewed session after unlock; physical verification is pending. The published bundled APK includes pinned Qwen weights; packaging is verified, current bundle import/load is not. A separate v0.19 CPU diagnostic completed six already-seen Qwen requests with 313 runtime checks and no actions. This is scoped runtime evidence, not general accuracy or NPU proof. The 4:04 edited research video labels historical v12 phone clips and current source illustrations. Complete human playback, current voice/monitoring/lock-unlock, actual iQOO Snapdragon NPU and Office Kit remain to verify. We disclose pre-existing research, Qwen and llama.cpp; eligible competition code must be created in the allowed event window unless organizers approve reuse.

## What makes the team stand out — project-based copy

Our approach combines a friendly companion with explicit user control and reproducible evidence. We distinguish quick deterministic recognition from actual Qwen inference, validate full arguments and invalidate stale or edited proposals before confirmation. We publish tests, exact artifact identities, paired evaluation losses and unfinished proof gates instead of presenting every prototype feature as verified. The next step is a small, reliable productivity workflow on actual iQOO hardware, with organizer-approved code eligibility and Office Kit verification.

This describes the project, not personal credentials or awards. Android
proficiency, LLM experience and prior builds are **unanswered human self-reports**;
agent-assisted implementation does not select an experience level for the user.

## Prototype, video and document

- Prototype: [public repository](https://github.com/sanjuhs/iqoo-focuspilot) and
  [current v0.20 research release](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.20).
  The release offers a [bundled APK with pinned Qwen weights](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.20/focuspilot-research-v020-mira-availability-bundled.apk)
  and a light APK requiring separately prepared private weights. v20 light is
  installed on Nothing. Bundle packaging is verified; current bundled
  installation, missing-model import and model load remain unverified.
- Optional video: [current 4:04 edited research pitch](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.20/pitch-v020.mp4).
  It combines clearly labelled historical v12 silent phone clips with current
  source illustrations. It is not current v20 lock/unlock, voice, NPU or Office Kit
  proof. Media checks pass; complete human playback/listening remains pending.
  [Footage, checks and limitations](v020-pitch.md).
- Required document: [immutable four-page concept PDF](https://github.com/sanjuhs/iqoo-focuspilot/blob/3f04ac3ca31deafc73ba288239177bcdb1f9c3d3/output/pdf/focuspilot-phase1-concept.pdf),
  25,456 bytes. The current dashboard record shows its link attached, with no file
  upload or submission. This is the dated concept document, not a newly rebuilt
  v20 deck. [Source and QA](phase1-document-evidence.json) and
  [public identity](phase1-document-publication.json). Final server document
  validation and draft persistence remain unverified.

## Originality and pre-existing-work disclosure

This application includes pre-event research already present in the public FocusPilot repository. Our Android integration, Mira interface, bounded validation/review flow and research utilities build on third-party open-source dependencies and AI-assisted development. The selected runtime uses Qwen3.5-0.8B Q4_0 and llama.cpp, with licenses/notices retained. Kev, Laya and Cua informed research; they are not deployed phone runtimes or an implemented Cua phone-control port. The published v0.20 bundled APK includes the pinned Qwen weights; the light option requires separately prepared private weights. Bundle packaging is verified, but current bundled installation, missing-model import and model load remain unverified. We do not assert that pre-event implementation is eligible event-written code. Competition code will be separately created in the permitted window unless organizers explicitly approve reuse.

The observed checkbox says: “I confirm this idea is our team’s original work and
any pre-existing components are disclosed.” Review that attestation before any
human acceptance; this file neither checks it nor submits the application.

## Evidence and remaining proof

- [Current v20 availability/build](mira-availability-v20.md): **216 JVM tests**
  pass; lint has zero errors/fatal findings and 79 warnings. Signed light
  installation preserves protected state, the model, grants and original test
  package. The default-off return-after-unlock behavior is implemented and tested
  with pure state fixtures; physical portrait restoration and OEM persistence
  remain unverified.
- [Current bundle packaging](mira-availability-bundle-artifact-v20.json): the
  signed 568,604,151-byte APK preserves all 16 original light payloads and adds
  only the pinned 563,036,064-byte model asset. Signature/certificate, alignment
  and model identity checks pass. This is packaging evidence, not current import,
  model load or unlocked interaction proof.
- [v19 CPU diagnostic](native-page-v19.md): **six already-seen requests and 313
  runtime checks**, with correct raw slots, five supported proposals and one
  negation refusal. Load took 2.361 seconds. No action executed. These measurements
  belong to v19 on Nothing with 4 KB pages; they do not establish general accuracy,
  iQOO/NPU acceleration, voice success or 16 KB runtime.
- [Current edited pitch](v020-pitch.md): 244.083333 seconds, 24 measured captions,
  full decode and sampled clip-parity checks. Historical v12 guide/readback and
  unconfirmed typed model footage retain their own source attribution. A TTS
  callback is not verified speaker audibility.

The 65-parameter trained policy remains synthetic and shadow-only; Qwen activation
observations establish no causal semantic interpretation. Current permitted
voice/monitoring, lock/unlock, bundled import, actual iQOO/NPU, Office Kit, eligible
event code, admission and accepted submission remain unfinished. Keep those
limits visible in the application; a release or video is not a submission receipt.
