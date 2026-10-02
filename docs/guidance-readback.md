# Mira's task readback — v0.12 research

Pre-event research, 3 October 2026. The task panel now shows when Mira is preparing
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
66 warnings. The readback integration compiled and the light APK was assembled.
These checks do not prove an installed voice, speaker audibility, platform timeout
or actual microphone/voice exclusion on a phone.

Qwen3.5-0.8B Q4_0, its prompt, native runtime and command gate stay unchanged.
Version code is 12 / `0.12-guidance-readback-research`. The release manifests and
separate physical records identify the exact source, packages and phone outcomes;
v0.11 phone results retain their original APK attribution.

## Phone verification

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
