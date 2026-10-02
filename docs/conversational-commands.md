# Conversational commands — v0.10 gate-only research selection

Pre-event research. Qwen3.5-0.8B Q4_0, native runtime and selected prompt remain unchanged.
The candidate consumes one complete original request while accepting explicitly
listed conversational wrappers. It never uses a valid prefix to discard another
action or malformed time. A matching model intent and explicit user review remain
necessary; Clock creation and real Android outcomes still need physical proof.

## Supported wrapper changes

- Greetings such as “Hello, Mira,” or “Hey,”.
- “Please,”, “kindly” or “just” around the existing request prefix.
- “I need you to” / “I'd like you to”, alongside the existing direct requests.
- At most two terminal “please”, “now” or “for me” wrappers, with optional comma.
- “Calculator application” as well as “Calculator app”, still only Settings,
  Calculator or Clock.

All exact duration/hour/minute parsers and rejection guards are unchanged. Negation,
conditions, multiple actions, unsafe operations, quotes/descriptions, unsupported
apps, extra arguments and wrong model direction must still abstain. Voice examples
are textual forms, not measured speech recognition. The separate dashboard quick
parser remains narrower. App settings, monitoring, microphone and floating Mira
are never enabled by these wrappers.

## Prompt experiments and selection boundary

A seen 36-request development benchmark compared the original prompt with two
fixed few-shot chat-pair variants. The shorter second variant handled 15/18 supported
cases versus 12/18, but took about 2.1 times as long on the laptop. These are openly
seen development results, not a held-out gain or phone/NPU latency.

An independently authored, frozen 100-request experiment then tested both locked
prompts and gates. New-prompt supported semantic correctness fell 37→30/50 while
unknown rejection improved 0→28/50. Native median rose 449→985ms. The new prompt is
**rejected for deployment**; higher total accuracy masked worse useful-command
understanding. The original prompt still incorrectly proposes a non-unknown tool
for every unsupported request in that experiment; the external gate supplies
rejection. No learned Qwen parameters or fine-tuning were changed.

The primary paired prompt-plus-gate comparison improved exact supported proposals
11→28/50 with zero wrong accepts observed. A separately labelled **post-hoc**
factorial check reused immutable outputs and isolated old-prompt/new-gate proposals:
35/50 supported correct,24 gains/0 losses versus 11/50 baseline, with all 50 unsupported
requests rejected. This component choice was made after seeing that set and cannot
be called independently confirmed there. The prompt/gate/source/data hashes,
failures and all four combinations are preserved; no case was repaired or removed.

A fresh 100-request/50-family confirmation froze the already-selected gate before
authoring its requests. The unchanged old-prompt Qwen capture was shared by both
gates. Correct supported actions/slots improved **15→31/50**, with **16 gains and
zero losses**; both gates rejected all 50 unsupported requests, with zero wrong
accepted proposals observed. Selected-gate strict correctness was **81/100**, but
**19/50 supported requests still falsely abstained**. Raw model semantic intent
correctness was only **36/100** (35/50 supported and one correctly unknown); it
proposed a tool for 49/50 unsupported requests. All 100 outputs met schema/EOS,
which did not establish semantic correctness.

This confirms the gate-only coverage gain on fresh synthetic wording after source
selection. Its author knew earlier results, so it is not independent human sampling
or real voice evidence. Zero observed wrong accepts does not establish universal
safety or autonomous reliability. Five oracle-supported forms also remain rejected;
failures and coverage are retained, with no repair after scoring. No phone action
executed and host CPU timing is not phone/NPU latency.

The expanded gate is **selected for v0.10 research packaging**, retaining the
original prompt, Qwen3.5 Q4_0 weights and native runtime. Source/package/build
and installation identities are recorded below; physical regressions remain
pending. Prior v0.9 APKs and historical phone outcomes do not prove this new
gate's physical behavior.

[Seen development](../prototype/command-v10-dev/README.md),
[first frozen experiment](../prototype/command-v10-eval/README.md),
[fresh frozen confirmation](../prototype/command-v10-confirm/README.md),
[full remaining deliverables](remaining-deliverables.md).

## Packaged research revision

App source `bcc24733655e4eced67d68ff5c47f7ab97d60b36` is versionCode10,
`0.10-conversational-gate-research`. 133 Android JVM tests pass, lint has zero errors
and 62 warnings, and 11 artifact-audit tests pass. Both signed light/bundled APKs
passed version/native/model/license/permission inspection. Updated light installed
with matching APK and retained private-model hashes; focus paused, observation off,
100 virtual points and OS permissions remained unchanged. No wake/UI/command
operation was performed: the display remained asleep and own app not focused.
Fresh bundled import, voice, timer, floating and disconnected outcomes are pending.

[Immutable package manifest](conversational-commands-artifacts.json) records exact
bytes/hashes and source attribution. The frozen experiment's no-promotion field
describes its evaluation run; this later source/package selection ships only the
gate, not either rejected prompt or new model parameters. Logical project files
total 13.511 decimal GB (12.583 GiB), including ignored builds/models/releases;
pre-existing shared developer SDK/Gradle caches are outside that measured scope.
