# Mira's task readback — v0.12 research

Pre-event research, 3 October 2026. Feedback and Stop readback sit beside Speak, before the expandable editor, so
opening the editor does not push speech feedback below it. The task panel shows when Mira is preparing
to read, reading, finished, stopped or unable to speak. A separate **Stop readback**
button stops speech without pausing focus or changing checklist progress. The
same feedback applies to the dashboard's explicit focus-status readback.

The previous dashboard submitted TTS requests without inspecting completion or
queue failures. The updated path uses unique utterance IDs and Android's
[utterance progress callbacks](https://developer.android.com/reference/android/speech/tts/UtteranceProgressListener).
Submitting a speech request is asynchronous; an accepted queue request alone
does not establish playback completion. The [TTS contract](https://developer.android.com/reference/android/speech/tts/TextToSpeech)
also exposes immediate queue/listener failures, which now leave readable feedback.

Only an installed English voice reporting no network requirement is selected.
Requests time out after 20 seconds. Matching start/done/error/stop callbacks return
to the UI thread; old IDs and request tokens cannot finish or relabel a newer
request. Mute, task/progress changes, clear/delete, microphone start, focus Pause
and leaving the dashboard stop playback and invalidate ownership. Returning to
the screen does not automatically resume speech. Task steps remain authored text
and do not execute actions or enter Qwen's prompt.

`ReadbackState` has no Android dependency and gates foreground ownership,
replacement, cancellation, one-time completion and permanent closure. Its five
JVM tests cover delayed callbacks and lifecycle changes. The complete build passes
**148 JVM tests**, zero failures/errors/skips; Android lint has zero errors and
65 warnings for the selected feedback layout. The first layout had 66 warnings. The readback integration compiled and the light APK was assembled.
These checks do not prove an installed voice, speaker audibility, platform timeout
or actual microphone/voice exclusion on a phone.

Qwen3.5-0.8B Q4_0, its prompt, native runtime and command gate stay unchanged.
Version code is 12 / `0.12-guidance-readback-research`. The release manifests and
separate physical records identify the exact source, packages and phone outcomes;
v0.11 phone results retain their original APK attribution.

## Phone verification

The selected build passed the four observed physical phases and scoped cleanup.
[Actual results and repeat procedure](guide-readback-phone.md) distinguish engine
completion from human audibility.

Use the matching APK on an unlocked own-app screen, initially paused with usage
reading off. Use an otherwise empty task/guide and synthetic harmless text.
Verify explicit step readback reaches a terminal callback/status with unchanged
progress. Toggle the app's companion mute preference to verify refusal, restore
its initial value, and remove only the synthetic plan/goal. Record speaker
audibility separately through a human check. Active-microphone, unavailable-engine,
runtime-error/timeout, interrupted playback and background platform branches need
their own observed outcomes; they are not certified by the pure state tests.

Final full-scope gates still include actual ASR, consented monitoring/floating mode,
iQOO NPU, Office Kit, model-generated guidance, eligible event code and accepted
submission. [Remaining deliverables](remaining-deliverables.md).

## Preserved attempts

The first package at `9fb4f7a4b341b8d563f033429b505a4432e7e09e` remains
identified by [its original manifest](../prototype/guidance-readback/first-layout-artifacts.json).
Two harness attempts stopped before saving because the phone keyboard corrected
synthetic wording; their records remain [first](guide-readback-first-attempt-v012.json)
and [second](guide-readback-second-attempt-v012.json). No keyboard settings were changed.
A grammatical goal then passed save and mute refusal, but the harness observed no
terminal readback status within 35 seconds. [That failure](guide-readback-layout-attempt-v012.json)
is retained; it does not establish engine failure or playback completion. Cleanup
was verified in all three attempts. The selected app places feedback before the
editor, and the harness positions controls clear of this phone's fixed overlays.

[Selected source, packages and installation](guidance-readback-artifacts.json)
identify the later layout at `24f10b62a4a62c22ad6db90ac6339f29e2426dbd`.
These revisions are pre-event research. Historical v0.11 results retain their
original package attribution.

[Published research v0.12](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.12)
contains both APKs and source-bound manifest/phone evidence. Four server
sizes/digests and the exact source tag matched [the publication record](guidance-publication-v012.json).
