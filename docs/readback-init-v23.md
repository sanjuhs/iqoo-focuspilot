# Readback initialization retry — v23 pre-event research

The v22 command screen can report a false unavailable result when the user stops
readback A during speech-engine initialization, then explicitly requests B before
the engine finishes. A nonnull engine is not yet a ready voice. The old callback
belongs to A, so it cannot deliver the initialized voice to B.

The fix separates engine initialization ownership from each explicit readback
request. B waits for the existing initializer and keeps its own request deadline.
Completion consumes only the latest pending request once. Cancellation and
backgrounding remove the pending request; initialization alone starts no speech.
An independent engine deadline retires an initializer that never responds. A
later explicit request can create a replacement; old callbacks cannot configure
or release it. Destroy closes admission and releases Android speech resources.

Android permits synthesis only after initialization completes, reported by
[OnInitListener](https://developer.android.com/reference/android/speech/tts/TextToSpeech.OnInitListener).
The [TextToSpeech contract](https://developer.android.com/reference/android/speech/tts/TextToSpeech)
also requires resource release after use. The implementation keeps the existing
installed offline English voice requirement and v22 request-plus-utterance
terminal-event check. Runtime speech exceptions return visible text and finish
only the owned request.

Qwen3.5-0.8B Q4_0, native inference, permissions, action review and companion
availability remain selected. This source fix establishes no actual speech-engine
run, audible output, transcription, NPU or Office Kit result.

Frozen app source: `1fc31da5787a49c7680e5bf13b827b6114a0fbe6`. The one offline
Gradle invocation succeeds: **227 JVM tests** across 30 suites, zero failures,
errors or skips; lint zero errors/fatal findings and 79 warnings. Six new tests
exercise the actual coordinator and request state across cancel/retry, no retry,
late old cancellation, background/destroy, failed-engine replacement and invalid
requests. These are state fixtures, not Android speech-engine simulations.
[Signed light artifact](readback-init-artifact-v23.json).

The light APK is 5,579,136 bytes. The 568,620,535-byte bundle adds only the pinned
563,036,064-byte model; every original non-signature app/native/license payload
matches the light APK. Signing, certificate and 16 KiB ZIP alignment pass. The
seven permissions and native library are unchanged; no INTERNET permission.
[Bundle evidence](readback-init-bundle-artifact-v23.json). Current import and
actual 16 KiB device execution remain unverified. Protected installation and
publication are recorded separately once completed.

One guarded non-streamed light update installs the exact APK on Nothing in
**1,397 ms**. Three checked preference stores/checkpoint, canonical model identity,
measured microphone/notification grants, absent own services and the original
test APK remain unchanged. Focus stays paused, observation off, balance 100
virtual points and accumulated focus 97,331 ms. No UI, wake, permission change,
action or model inference occurred. [Protected update](readback-init-phone-install-v23.json).
The packaging-era install flag describes packaging only; the later update record
proves installation. Raw snapshots remain private.

Independent source review checked cancellation, replacement, engine epochs,
deadlines, exception handling and the guarded installer before execution. Root
restored runtime exception handling inside speech dispatch and made the helper
and test source mandatory installation bindings before freezing the installer.
This review and six JVM fixtures establish no physical Android engine behavior.
The pre-update [v22 readiness check](delivery-readiness-v22.json) verifies the exact
installed bytes and shows the phone locked/off with microphone/notifications off.
Its first path check refused Android tilde characters before streaming/file
creation; corrected explicit path validation passed without device mutation.

Only the exact older v21 generated bundle was removed locally after its public
asset size and server digest matched the local bytes. v22/v23 bundles, canonical
weights, private data and historical records remain. [Recovery](recoverable-bundle-cleanup-v23.json).
The complete goal still requires real permissioned voice/monitoring and companion
lock/unlock, current bundle import, actual iQOO/NPU, Office Kit, event-eligible code
and accepted submission. The Phase 1 form remains its verified v21 draft and the
4:04 video remains the dated v20 research pitch.

For the physical retry check, use synthetic focus status and record the exact
installed APK, engine and offline voice. After explicitly reviewing a benign
focus action, tap Read and then Stop while initialization is visibly pending;
explicitly tap Read again. Only the current request may be spoken. Repeat with
no replacement and with backgrounding; neither may start audio later. Resume
requires another explicit Read. Check mute and unavailable-voice text separately.
If the real initializer completes too quickly to exercise cancellation/retry,
report that branch as unexercised. Callback completion alone does not establish
audibility; retain the operator's actual listening result separately.

Published [research v0.23](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.23):
all five server asset sizes/SHA256, notes and frozen source tag match.
[Publication record](readback-init-publication-v23.json). Logical project files
including ignored/.git plus recorded new global-cache growth total 9,786,981,042
bytes, below the 10 GB aim. [Storage scope](readback-init-storage-v23.json). No
new model was downloaded. Publication does not establish physical voice or submission.
