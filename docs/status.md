# Verified status

Updated 3 October 2026 (IST). This file separates measured results from goals.

## Network-denied Qwen phone diagnostic — verified

Qwen3.5-0.8B Q4_0 completed ten fixed synthetic native CPU requests in the actual
Nothing app process after IPv4 TCP socket creation failed with numeric EPERM.
The first request took **16.83 seconds**; subsequent native requests took
**1.48–2.43 seconds**. Fresh native load took 2.49 seconds after full-file SHA
verification warmed the filesystem cache. Whole instrumented-process post-request
PSS was about 1.172 GiB, including test/framework overhead; this is not peak RAM.

The test-only runner passed 224 checks, observed four finite width-1,024 tensor
summaries on its single capture-on request and closed the native model. Eight raw
intents matched the illustrations; all ten gated proposals matched because the
gate refused two unsupported misclassifications. These openly seen diagnostics
are not an accuracy benchmark and do not replace the frozen host evaluation.

The installed v0.13 app/model/prompt stayed unchanged. All three named preference
identities, paused/off/100/97,331 ms checkpoint, model bytes/hash/inode, two runtime
grants and absent own services matched before, after inference and after restoring
the original test APK. Instrumentation restarted the paused target process; guarded
cleanup force-stopped it. No UI, action executor, observation, ASR, network setting
or grant change was used. The earlier Java-wrapper failure is preserved separately.

This establishes the bounded native path with socket creation denied, not a full
disconnected/voice workflow, NPU execution, Office Kit or causal interpretation.
The original five release assets and app source retain their existing attribution;
the new diagnostic source is `aff6fb940fb76f64f77aca8d4c0ff33164a7de43`.
[Procedure and limits](network-isolation-phone.md),
[sanitized phone record](network-isolation-phone-v013.json),
[source/artifact bindings](network-isolation-artifacts.json),
[preserved failed first attempt](network-isolation-phone-v013-first-attempt.json).

Three diagnostic assets are now published alongside the original five v0.13
assets. All eight server sizes/digests match; the original assets and app-source
tag are unchanged. The evidence/source backup is remote-equal. Measured project
storage is 14,398,647,815 logical file bytes, below 15 GB. This publication does
not add a runtime or eligibility result.
[Publication verification](network-isolation-publication-v013.json).

## Reviewed reset — v0.13

The research source now requires explicit session-reset review, dismisses that
review when the activity pauses, and refuses confirmation after the session
generation changes. Reset clears the stale interrupted-session warning. Qwen3.5
0.8B Q4_0, prompt, gate, native runtime and companion assets remain unchanged.
App source `1eed4348d3d0233d786bcd3b86c05d225ebf8db6` builds both light and
model-bundled APKs plus a separate test APK. All 148 JVM tests pass, with zero lint
errors and 65 warnings; five host harness boundary tests pass. Both app packages
pass signature, native/model, version, permission and six-notice inspection.

Actual Nothing instrumentation passes 22 checks using two uniquely owned
preference stores: paused interrupted checkpoint reset, counters/points, retained
settings and authored-data sentinels, same-process repository reconstruction and
a reset active countdown checked after its old deadline. The fixtures are removed.
The three named production preference identities, original model bytes/hash/inode,
paused/off/100/97,331 ms, microphone/notification grants and absent own services
match before/after. The v0.13 light APK and its separate test APK remain installed.
This fixture-only run uses no UI, model inference, wake or production reset. The
phone locked before the interactive repeat: Keep/Back/background-dismissal and
stale-generation UI branches remain pending. The first formatted-output checker
failure is preserved; the successful repeat captures raw structured results.

Packaging reserved a 14,966,902,017-byte two-copy peak below the strict 15 GB cap;
actual post-packaging project files are about 14.398 GB. A new bundled missing-model
phone import is not tested: v0.12's import result remains historical. The existing
v0.12 model/action/video evidence retains its original APK attribution. ASR,
permissioned monitoring/floating, disconnected operation, iQOO NPU, Office Kit and
eligible accepted submission remain unfinished.
[Reset scope and repeat procedure](reviewed-reset.md),
[physical fixture record](reviewed-reset-phone-v013.json),
[package identities](reviewed-reset-artifacts.json).

The [v0.13 research release](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.13)
is published with both app APKs, the separate synthetic test APK and two evidence
records. All five server asset sizes/digests match local files; the tag resolves
to the exact app/test source. Publication does not repeat runtime tests or establish
submission eligibility. [Publication verification](reviewed-reset-publication-v013.json).

## Compact intent experiment — rejected

A locked one-digit Qwen candidate was compared with the shipped prompt on 100
fresh synthetic host requests. Supported complete proposals rose 30→32/50, but
five gains came with three focus/pause losses, including a hard spoken-number
case; Pause coverage fell 2→0/8. Warm host native median rose 448.70→465.74 ms.
The candidate is rejected; selected app/model/prompt remain unchanged. Twenty
research validation tests pass. This is host research, not phone/NPU evidence.
[Results, regressions and source bindings](compact-intent-research.md).

## Current v0.12 bundled-model import

The selected bundled APK imported Qwen3.5-0.8B Q4_0 on Nothing with the canonical
model absent and existing app data retained: 1,077 ms import/SHA, 2,320 ms CPU load.
The first typed Pause proposal took 9,534 ms and required review; no action ran.
Second load reused the exact imported file. Cleanup restored the original model
and light APK, all named preference identities, paused/off/100/97,331 ms and the
two measured runtime grants. Fifteen ownership/foreground boundary tests pass.
This closes the selected missing-model import branch; clean fresh-data installation,
ASR/monitoring, disconnected operation, iQOO NPU, Office Kit and eligible accepted
submission remain pending. [Physical proof and repeat procedure](bundled-import-phone-v012.md).

## Current v0.12 phone export

The selected Nothing APK passed export-review Cancel, document-picker Cancel and
actual local Save. A new 496-byte zero-label summary matched phone/laptop hashes;
the laptop validator accepted zero records/contexts with no policy inference.
Focus stayed paused/off/100/97,331 ms, grants unchanged and monitor absent.
Payload and aggregate stay private/ignored; metadata and failed attempts are
preserved. This proves a local export plus ADB interoperability. Actual Office Kit
transport and real-record replay remain pending.
[Physical proof and scope](phone-export.md).

## Current v0.12 countdown and recovery

Ten actual own-app phone phases passed on the selected APK: reviewed Cancel,
timed Start, early Pause, exclusion of paused time, reviewed resume, automatic
completion, process force-stop/restart with exact paused checkpoint recovery,
explicit resume and refused alarm cancellation. Two countdowns added exactly
40,000 ms; final elapsed 97,331 ms, paused/off/100 points, empty goal/no guide,
unchanged grants and no monitor. Three supported Qwen proposals took 1.824–1.928 s
native CPU. Qwen misclassified cancellation, and validation correctly abstained.
This establishes last-checkpoint recovery, with ASR, deep sleep, monitoring,
iQOO/NPU, Office Kit and accepted eligible submission still pending.
[Physical proof and repeat procedure](focus-recovery-phone.md).

## Current recorded v0.12 research demo

A new 4:41 video includes original Mira artwork and two actual own-app phone clips
at 1× speed: explicit authored-step readback and typed Qwen3.5-0.8B Q4_0 inference
(1,849 ms native CPU, capture enabled, no action confirmed). Synthetic Mark/Undo,
four finite tensor summaries and scoped cleanup were verified on the same APK;
unfilmed flows remain labelled illustrations. Captions, full decode, deterministic
seeks, sampled encoded visuals and source-clip comparisons passed. Complete human
listening, actual ASR/monitoring/floating, iQOO/NPU, Office Kit and eligible accepted
submission remain pending. [Video, source and scope](v012-pitch.md).
Eight new media/evidence assets and all original release identities were verified
against server metadata. Post-publication storage is 13,821,501,677 logical bytes
(about 13.822 GB), below the 15 GB cap.
[Publication record](v012-pitch-publication.json).

## Selected v0.12 task readback

Mira now keeps speech feedback and Stop readback beside Speak, with unique request
ownership, engine callbacks and a 20-second timeout. The selected source is
`24f10b62a4a62c22ad6db90ac6339f29e2426dbd`; 148 JVM tests pass and lint has
zero errors/65 warnings. Both signed packages passed model/native/license/version/
permission inspection, and the light installation reused the pinned Qwen model.

On Nothing, a synthetic authored plan passed save, mute refusal, explicit readback
completion callback and an unconfirmed typed Qwen Pause proposal (1,749 ms native
CPU). Checklist progress stayed unchanged. Cleanup restored empty goal/no guide/
mute false; paused/off/100/57,331 ms and runtime grants stayed unchanged.
[Actual record and repeat procedure](guide-readback-phone.md),
[package/source identities](guidance-readback-artifacts.json).
No speaker audibility, real ASR, permissioned monitoring/floating, disconnected
operation, iQOO NPU, Office Kit or eligible accepted submission is established.
The broader goal remains active. Earlier results below retain their historical
package attribution.

Both APKs, the package manifest and physical record are
[published as research v0.12](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.12).
The server's four sizes/digests and exact source tag were verified;
[publication record](guidance-publication-v012.json).

Post-publication storage measured 13,647,373,232 logical project bytes, including
ignored files and Git, below the 15,000,000,000-byte cap. Shared pre-existing SDK
caches are excluded.

## Historical v0.11 approved app launches — actual phone outcomes

Typed `Open calculator` and `Open clock` each produced Qwen `open_app`, review
required, followed by Cancel and then reviewed Confirm. Native CPU inference was
2,016 and 1,998 ms. Foreground metadata observed Calculator's resolved component
and Clock's main activity after a same-package redirect from its resolved API
handler. No target UI was inspected or touched; no alarm/timer was created.
Return and a fresh-screen check left Review disabled. Focus paused/off/100/57,331
ms, grants and absent monitor stayed unchanged. The first harness attempt stopped
at full-versus-shorthand component comparison; its report and exact executed source
are retained. APK/model/native and selected app sources stayed unchanged.
[Current proof and repeat procedure](app-launch-phone.md).

## Historical v0.11 activation viewer — actual phone comparison

Nine typed Qwen3.5-0.8B Q4_0 requests (one warm-up plus four off/on pairs) ran
on the matching installed Nothing APK. All eight measured trials proposed Pause,
155 prompt/eight generated tokens, with no action confirmed. Every capture-on
trial displayed all four finite width-1,024 tensor summaries, identical within UI
formatting across repeats; off emitted none. Native totals ranged 1,864–2,166 ms,
with paired differences −199, −302, −46 and +135 ms. No fixed overhead, full-request
latency or causal semantic finding is established. Post-request PSS snapshots
ranged about 1.25 GiB. Final focus/grants/monitor state stayed unchanged. Source,
APK/model/native and executed harness hashes are recorded; no build or model
change was made. [Measurements and method](capture-benchmark-phone.md).

## Historical v0.11 readback and monitoring prerequisite check

On Nothing, typed `Stop focus` produced a reviewed Pause proposal in 1,804 ms
reported CPU time. Explicit fixed-status readback reached Android's completed TTS
callback for an installed offline English voice. Speaker audibility and whole-device
network-disconnected operation are not verified. A visible-monitor attempt with
observation off was refused; its switch stayed off and no own monitor-service record
appeared. Paused/off/100 points/57,331 ms remained unchanged. Setup reports an
on-device speech service available, but Microphone, notifications and Usage Access
are off; English ASR support and transcription remain untested. No grants/settings
changes or microphone activation occurred. Four harness tests and six report-binding
tests pass. [Physical branches and repeat procedure](readback-phone.md).
The post-test storage check measured 12,498,097,200 logical project bytes
(12.498 decimal GB), including ignored files and Git, below the 15 GB cap;
external shared SDK caches are excluded.

## Historical v0.11 authored-guide phone coverage

A synthetic three-step plan was tested through the installed app's own UI on
Nothing: Save, Mark/Undo, completion/Undo, real process force-stop/restart with
exact record recovery, replacement Cancel/confirm and clear Cancel/confirm with
cleared-state recovery. All 12 recorded phases passed. The temporary plan was
removed and the original empty goal restored; focus stayed paused, observation off,
points 100 and total elapsed 57,331 ms. No model, voice, permission or external-app
action was invoked. Eight harness boundary/cleanup tests and six report-binding
tests pass; the latter preserve the full-task gate as incomplete. Readback, stale
reviews, goal-switch and other remaining branches are separate requirements.
[Phone record](task-guide-phone-v011.json),
[coverage and repeat procedure](task-guide-phone.md).
The post-test storage check measured 12,497,893,061 logical project bytes
(12.498 decimal GB), including ignored files and Git, below the strict 15 GB cap;
external shared caches are excluded.

## Historical v0.11 reviewed countdown — actual phone outcome

The installed light v0.11 APK and retained model hashes matched their pinned
identities before an actual typed “Start focus for 20 seconds” request on Nothing
A059/SM7635/API36. Qwen3.5-0.8B Q4_0 proposed `start_focus`; the original-request
gate required review and preserved 20 seconds. Reported native CPU inference was
1,932 ms (788 prefill, 1,144 decode); this single observation is not a latency
benchmark. After explicit review confirmation, persisted active focus was observed,
then automatic pause without a user Stop. Elapsed checkpoint delta was exactly
20,000 ms; final focus paused, observation off and virtual points 100.

The first attempt failed an immediate disk-state check after confirmation and
cleanup Stop were tapped. SharedPreferences persistence is asynchronous; later
read-only state was paused/off/100. That failed attempt is retained and does not
prove no action occurred. The corrected harness polls for persisted state, records
confirmation before validation and checks cleanup. Its foreground guard requires
actual awake and unlocked metadata plus the exact own-app owner; missing flags
cannot authorize UI inspection. Seven harness tests pass.

[Successful source/APK/model/native/harness-bound report](current-countdown-phone-v011.json),
[failed attempt](countdown-first-attempt-v011.json). No new APK, permission grant,
model, command prompt or native change was made. After these experiments, the
storage check measured 12,497,522,266 logical project bytes (12.498 decimal GB),
including ignored files and Git, below the 15 GB cap; external shared SDK caches
are excluded. This attributed typed process-live
case alone does not verify ASR/TTS, task-guide UI, monitoring, floating mode, deep sleep,
recovery, disconnect, Clock, iQOO/NPU or Office Kit.

## Unpromoted local task-planning research

Two real Qwen3.5-0.8B Q4_0 host planning experiments are preserved: the first
returns empty declines for all eight benign goals; an example-based repair meets
only 4/10 fresh benign criteria, with one nonsense draft and one negation violation.
Both have real EOS/JSON evidence, which does not prove useful guidance. Neither
is promoted. Six research tests and archived-source/evidence verification pass.
An unapplied reviewed-import UI scaffold compiled with 156 tests/zero lint errors
and 76 warnings; its candidate APK was not installed or released. Selected v0.11
source was restored and rebuilt: 143 tests pass, zero lint errors/65 warnings;
installed/published packages, command prompt, model and native remain unchanged.
[Results and reproduction](task-draft-research.md),
[unselected integration](../prototype/task-draft-ui/README.md).

## Task guidance checkpoint — v0.11

Source `e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a` adds a private, user-authored plan for the
saved focus task: one to eight steps, explicit completion/undo, reviewed replacement
and clear, and optional local readback. Goal/revision checks block stale progress
and speech; step text executes no phone action and enters no model/export.
**143 JVM tests pass**, lint zero errors/65 warnings. Signed light packaging passed
native/license/permission inspection and installed with matching APK/model hashes;
focus paused, observation off and 100 points stayed unchanged during that installation.
No wake, UI, permission or task action occurred during installation; the separate
reviewed countdown above was subsequently tested. Both signed packages are inspected and [published with v0.11](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.11);
all four server asset sizes/SHA-256 digests match local files and the tag resolves
to the exact app source above. The later authored-guide test covers selected steps
and restart branches; readback and other task-guide branches remain pending.
Qwen3.5 Q4_0, prompt, gate and native are unchanged. The publication preflight measured
12,491,320,741 logical project bytes (about 12.491 GB), below the strict 15 GB cap;
ignored files and Git are included, pre-existing shared SDK caches excluded.
[Task guide](task-guide.md),
[immutable identities](task-guide-artifacts.json).

A seven-parameter logistic comparison now scores 469/480 synthetic cases versus
472/480 for the existing 65-parameter network. This informed known-teacher result
closes the baseline gap and promotes neither policy. [Evidence](policy-baselines.md).

## Current research pitch — published video

A new **4:35 (274.836-second)** application concept/research video is locally
ready: `artifacts/pitch-current.mp4`, 1920×1080 H.264/24fps with AAC and **30 measured
caption segments**. It uses original procedural illustrations, with no phone
capture or new phone actions. The historical v0.3 `pitch-research.mp4` is preserved.

Renderer source is `6ca1d02284ecffd643b9d50ea6b1b18d610f88d1`; the video references
v0.10 app source `bcc24733655e4eced67d68ff5c47f7ab97d60b36`. The new v0.11 task guide
is not depicted in that video. Video SHA-256 is
`1bb3fd1d96330b5320b8d8281e8f824212ada852a84835c3b1cbcb0895e82a25`.
Full decode, caption timing, encoded-frame/transition review and audio-level checks
passed. **Complete human listening/playback review remains pending.** The video's
historical typed actions, current install identity and synthetic metrics retain
their different evidence scopes; no live iQOO/NPU/Office Kit result or eligible-entry
claim is established. Dashboard format/cutoff, event-code eligibility and accepted
submission remain unresolved.

The video, captions and both evidence manifests are [published with v0.10](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.10).
All four new server sizes/SHA-256 digests match local files; the original three
APK/manifest assets remain unchanged and the tag still points to the app source.

[Current pitch and reproduction](current-pitch.md),
[immutable video evidence](current-pitch-evidence.json),
[render manifest](current-pitch-render-manifest.json),
[editable narration/shot plan](current-research-pitch-script.md).

## Conversational gate update — v0.10

Source `bcc24733655e4eced67d68ff5c47f7ab97d60b36`, version code **10** /
`0.10-conversational-gate-research`, selects the expanded original-request gate
while keeping **Qwen3.5-0.8B Q4_0, native runtime and original prompt unchanged**.
The longer prompt candidate was rejected; there is no deployed model fine-tuning.

Fresh frozen synthetic confirmation: correct supported actions/slots **15→31/50**,
16 gains/zero losses, all 50 unsupported requests rejected and zero wrong accepted
proposals observed. **19/50 supported requests still falsely abstain**. Raw model
semantic correctness is **36/100** (35 supported, one unknown), with 49 unsupported
tool proposals. This is host evidence by an informed author, not voice/phone or
universal safety. Explicit action review remains required.

**133 Android JVM tests pass**, lint zero errors/**62 warnings**; **14 artifact-audit
tests pass**. Both signed version-10 packages passed native/model/license/permission
inspection: all six notices present and no `INTERNET` permission.

| Package | Bytes | SHA-256 |
| --- | ---: | --- |
| Light | 5,480,648 | `a1a85e70f5d459df6e73b4294dcbeed81518489fe419b30729333ec11e083103` |
| Bundled | 568,516,824 | `1cb5678781ca3a4aa63f462d445b05516d93f1d363e78f6e2a05f7f46a777bf0` |

The light APK installed on Nothing with matching installed-APK/private-model
hashes. Focus inactive, observation off and virtual points 100 stayed unchanged;
microphone and notification grants stayed false, overlay remained default with no
operation. Display was asleep and own app not focused; the lockscreen metadata flag
was false, which does not establish a usable unlocked foreground state. **No wake,
UI test, command, permission grant or overlay test occurred.** Physical timer,
voice/TTS, monitor/Stop, Clock, disconnected inference, iQOO/NPU and Office Kit remain
pending. Prior build outcomes retain their historical binary/source attribution.

Measured project files total **13,511,076,286 bytes = 13.511 GB = 12.583 GiB**,
below the strict decimal 15 GB limit. This includes ignored project files and
excludes pre-existing shared SDK/`.gradle` caches; it is not peak RAM. The
[v0.10 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.10)
is published: all three server sizes/SHA-256 digests match local artifacts and
the tag resolves to the exact app-source revision above. Publication does not
establish physical execution or submission acceptance.

[Command selection and confirmation](conversational-commands.md),
[immutable artifact manifest](conversational-commands-artifacts.json),
[full remaining deliverables](remaining-deliverables.md).

## Historical floating companion update — v0.9

Source `6e483aaf9e42889794ed77c272b8a912539cfc7c` adds optional floating Mira with explicit reviewed
Show, movable portrait, Open, Pause focus and Hide controls. The separate service
requires user-granted overlay permission, visible floating notifications, unhidden
artwork and an interactive unlocked phone. Permission return starts nothing.
Hide/screen-off/lock/revocation stop the visual companion without pausing focus;
Pause explicitly stops focus and its monitor. No new observation, microphone or
model run is started. Existing consented accounting may flush at deadline/Pause.

**127 JVM tests pass**, lint zero errors/62 warnings. Both signed APKs passed
packaging inspection; light installed with matching installed APK/private-model
hashes. No floating permission was granted or actual overlay UI tested: the phone
was asleep/our app not focused. Qwen3.5, prompt, native runtime and command gate
are unchanged. Logical project size **12.05 GiB**, within 15 GB.
[Controls and proof gates](floating-companion.md),
[platform sources](floating-companion-platform.md).

The [0.9 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.9)
publishes light/bundled APKs and the immutable artifact manifest. All three server
sizes/SHA-256 digests match local files; tag resolves to the stated app-source SHA.
After installation, one display-wake/own-app-launch attempt failed the unlocked
own-app foreground guard. No UI was inspected, permissions granted or commands
executed; subsequent metadata still reported asleep/not-own-app-focused. Actual
overlay and countdown tests remain pending. This later attempt is separate from
the initial installation snapshot.

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
