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
