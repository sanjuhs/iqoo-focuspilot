# Mira / FocusPilot — Phase 1 application copy

Prepared **3 October 2026**. Public title, description, repository link and team
summary are now populated in the live dashboard draft, with the PDF link attached.
No personal experience selection, attestation or submission was performed.
Draft server persistence and final document validation remain unverified. Productivity is
already selected for the Grand Finale, 9–11 October, with one registered member.
The displayed Phase 1 deadline is **5 October 2026**; its exact cutoff time and
timezone are not shown. No private team/profile information is included here.

The dashboard requires an idea title (5–200 characters), description (50–2,000),
and a PDF/PPT deck/document up to 25 MB or a link. Video walkthrough and
prototype URLs are optional. It also asks Android proficiency, LLM experience,
prior builds, what makes the team stand out, and an originality/pre-existing-work
attestation before **Submit idea**. Its observed wording is: “I confirm this idea
is our team’s original work and any pre-existing components are disclosed.”
[Structured copy and unresolved fields](phase1-form-copy.json).
[Actual draft preparation](phase1-prepared-dashboard-draft.json).

## Idea title

**Mira: A Private Productivity Companion**

## Description — ready to copy

Mira is a local-first Android productivity companion that helps people return to
the task they intended to do. A friendly animated companion accepts editable
typed or optional voice drafts for focus sessions, timers, alarms and a small
approved app list. Quick local checks handle familiar requests without loading a
language model; unfamiliar wording can use explicitly loaded Qwen3.5-0.8B Q4_0
on the phone’s CPU. An independent validator checks complete arguments, and
proposed actions still require Review and Confirm. Focus goals, user-authored
checklists and opt-in app limits support a calmer workflow; accountability uses
simulated points, never automatic money withdrawal.

Our current v0.18 light pre-event research prototype is published and installed
on a Nothing phone. A separate published bundled APK includes the pinned Qwen
weights. Its packaging is verified; current bundled installation, missing-model
import and model load remain unverified. A separate v0.17 diagnostic completed
six already-seen local Qwen requests; a frozen host evaluation improved complete
supported proposals from 4/50 to 19/50 with no paired losses, while refusing all
50 unsupported examples. These are scoped tests, not general accuracy or a
complete voice demo. Unlocked v0.18 interaction, permissioned monitoring/voice,
actual iQOO Snapdragon NPU and Office Kit remain to verify. We disclose the
pre-existing repository and open-source dependencies; eligible competition code
must be created in the allowed event window unless organizers approve reuse.

## What makes the team stand out — project-based draft

Our approach combines a friendly companion with explicit user control and
reproducible evidence. We distinguish quick deterministic recognition from actual
Qwen inference, validate full arguments and invalidate stale or edited proposals
before confirmation. We publish tests, exact artifact identities, paired evaluation
losses and unfinished proof gates instead of presenting every prototype feature
as verified. The next step is a small, reliable productivity workflow on actual
iQOO hardware, with organizer-approved code eligibility and Office Kit verification.

This describes the project approach, not personal credentials or awards. Android
proficiency, LLM experience and prior builds remain **unanswered human self-reports**.
No experience level or achievement is inferred from agent-assisted implementation.

## Optional links and required document

- Prototype: [public repository](https://github.com/sanjuhs/iqoo-focuspilot), with
  [current v0.18 research release](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.18).
  The release offers a [bundled APK with pinned Qwen weights](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.18/focuspilot-research-v018-mira-commands-bundled.apk)
  and a light APK requiring separately prepared private weights. Bundle packaging
  is verified; current bundled installation, missing-model import and model load
  remain unverified. Quick recognition needs no model load. [Bundle scope](mira-bundle-v18.md).
- Optional video: [historical v0.12 walkthrough](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.12/pitch-v012.mp4),
  **4:41**, with [source and limitations](v012-pitch.md). It includes historical
  v0.12 phone footage and edited narration, not current v0.18 interface or complete
  voice/monitoring proof. Complete human playback/listening remains pending.
- Required deck/document: the [four-page concept PDF](../output/pdf/focuspilot-phase1-concept.pdf)
  is prepared and visually checked, 25,456 bytes. Its immutable link is now attached
  in the live draft, with the document link and Remove document control visible.
  No file upload or final submission occurred. [Source and QA](phase1-document-evidence.json).
  An [immutable public PDF link](https://github.com/sanjuhs/iqoo-focuspilot/blob/3f04ac3ca31deafc73ba288239177bcdb1f9c3d3/output/pdf/focuspilot-phase1-concept.pdf)
  is ready; its server file identity matches the local PDF.
  [Publication proof](phase1-document-publication.json). Final server validation of
  that link and draft persistence remain unverified; the PDF is also available for upload.

## Originality and pre-existing-work disclosure

This application includes pre-event research already present in the public
FocusPilot repository. Our Android integration, Mira interface, bounded
validation/review flow and research utilities build on third-party open-source
dependencies and AI-assisted development. The selected runtime uses
**Qwen3.5-0.8B Q4_0 and llama.cpp**, with licenses/notices retained. **Kev, Laya and
Cua informed research**; they are not deployed phone runtimes or an implemented
Cua phone-control port. The published v0.18 bundled APK includes the pinned Qwen
weights; the light option requires separately prepared private weights. Bundle
packaging is verified, but current bundled installation, missing-model import and
model load remain unverified.

We do not assert that pre-event implementation is eligible event-written code.
Competition code will be separately created in the permitted window unless
organizers explicitly approve reuse. Review the actual attestation wording before
checking it; this file neither attests nor submits.

## Evidence that can support the deck

- [v0.18](mira-commands-v18.md): 208 JVM tests pass; lint zero errors and 79 warnings;
  signed light package and protected retained-data installation verified. The
  phone was locked/off, so the revised layout, examples, touch, voice and fallback
  were not physically exercised in that update.
- [v0.18 bundle](mira-bundle-v18.md): the 568,608,247-byte signed APK includes
  the pinned 563,036,064-byte Qwen model. All 16 original non-signature payloads
  match the light APK; signature/certificate, licenses and alignment pass. This is
  packaging evidence only: the light variant remains installed, and current bundle
  installation/import/load/UI have not been exercised.
- [v0.17 local JNI diagnostic](unit-native-phone-v17.md): six already-seen requests
  complete with actual EOS, correct model slots and no executed actions. It proves
  its own Nothing CPU runtime scope, not iQOO/NPU or fresh phone accuracy. The
  initial restore harness remains failed; final read-only records verify recovery.
- [Frozen host qualification](compatible-command-research.md): complete supported
  proposals 4→19/50 with 15 gains/no losses; all 50 unsupported requests refused,
  zero wrong accepts observed. Coverage remains limited: 31 supported refusals,
  0/8 Explain and a model-only alarm loss. This is informed synthetic evaluation.

The separate 65-parameter policy is a synthetic, shadow-only explanation lab;
activation observations do not establish causal Qwen understanding. Actual
permissioned workflows, iQOO/NPU, Office Kit, event-code eligibility and accepted
submission remain unfinished. The application should present this scope clearly,
without treating a release, test result or video as admission or submission proof.
