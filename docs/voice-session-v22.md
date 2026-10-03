# Mira voice sessions — v22 pre-event research

This research update fixes three source-level voice/readback defects. Qwen3.5-0.8B
Q4_0, native inference, action validation, permissions and companion availability
stay selected. Physical voice and current lifecycle verification remain pending.

The dashboard draft is disabled while recognition is checking, listening or
processing, so a final transcript cannot overwrite a correction typed during
that request. Existing text is retained; final/cancel/failure/timeout use the
existing refresh path to restore editing. The listening instruction names the
actual dashboard **Push to talk / stop** control.

Ask Mira now uses the existing pure readback lifecycle state with an utterance
bound to each request. A delayed old utterance completion, error or stop delivered
to a replacement listener must match both its event ID and listener request token
before releasing the current busy guard. Stop, background and destroy invalidate
ownership; the existing 20-second deadline remains. Listener registration failure
returns visibly before queueing speech. These changes initiate no microphone,
model, action or permission operation.

Android [utterance callbacks](https://developer.android.com/reference/android/speech/tts/UtteranceProgressListener)
identify the utterance that produced each event, and
[listener registration](https://developer.android.com/reference/android/speech/tts/TextToSpeech#setOnUtteranceProgressListener(android.speech.tts.UtteranceProgressListener))
reports success or error. The fix checks both contracts. The local speech factory
and installed-language preflight remain unchanged; availability is not a verified
transcription result. [Official speech API](https://developer.android.com/reference/android/speech/SpeechRecognizer).

The frozen app source is `08af30893d6ca7ecec70cf66b5026a88be463ca5`.
All **221 JVM tests** across 29 suites pass with zero failures, errors or skips.
Five new regressions check old-event/new-listener and new-event/old-listener
crossing, null/unrelated IDs, one terminal completion, cancellation/lifecycle
invalidation and compatibility with existing unbound readback callers. These
fixtures verify state behavior; they do not simulate a physical speech engine.
Lint reports zero errors/fatal findings and 79 warnings.
[Build and signed light artifact](voice-session-artifact-v22.json).

The light APK is 5,562,748 bytes; the bundle is 568,604,151 bytes and contains the
same 563,036,064-byte pinned Qwen3.5-0.8B Q4_0 model. Every original non-signature
payload matches the light APK; only the stored model entry is added. Signature,
certificate and 16 KiB ZIP alignment pass. The seven-permission set, native library
and six license assets are unchanged. The APK has no `INTERNET` permission.
[Bundle evidence](voice-session-bundle-artifact-v22.json). Current bundle import
and actual 16 KiB device execution remain unverified.

One guarded non-streamed update installs the exact light APK on Nothing in
**1,520 ms**. The original test APK and checked three preference stores/checkpoint,
canonical model identity, grants and service absence remain unchanged. Focus is
paused, observation off, balance 100 virtual points and elapsed time 97,331 ms.
The installer uses no UI, wake, permission change or model inference.
[Protected installation](voice-session-phone-install-v22.json). Its raw device
snapshot stays private; the packaging-era `phone_installed:false` field describes
that earlier packaging step, while this later install record proves the update.

The first build launch refused at a wrong log directory before Gradle started;
one corrected offline invocation succeeded. The first inspector stopped on
permission-order comparison; it resumed after exact APK parity and canonical
set comparison. Neither changed the APK. Recoverable v20 bundle bytes were
removed only after their public release asset size/digest was verified.
[Recovery record](recoverable-bundle-cleanup-v22.json).

Physical ASR, speaker audibility, permitted monitoring, lock/unlock, current
bundled import, iQOO/NPU, Office Kit and eligible accepted submission remain
pending. No new inference ran; v19 CPU and activation observations retain their
own source/APK attribution. This remains pre-event research.

Published [research v0.22](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.22):
all five server asset sizes/SHA256, release notes and frozen source tag are verified.
[Publication record](voice-session-publication-v22.json). Logical project files
including ignored/.git plus recorded new global-cache growth total 9,779,793,207
bytes, below the 10 GB aim; no new model was downloaded.
[Storage scope](voice-session-storage-v22.json). The live application stays at
its previously verified v21 copy and dated v20 pitch; this update did not submit it.
