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
ownership; the existing20-second deadline remains. Listener registration failure
returns visibly before queueing speech. These changes initiate no microphone,
model, action or permission operation.

Android [utterance callbacks](https://developer.android.com/reference/android/speech/tts/UtteranceProgressListener)
identify the utterance that produced each event, and
[listener registration](https://developer.android.com/reference/android/speech/tts/TextToSpeech#setOnUtteranceProgressListener(android.speech.tts.UtteranceProgressListener))
reports success or error. The fix checks both contracts. The local speech factory
and installed-language preflight remain unchanged; availability is not a verified
transcription result. [Official speech API](https://developer.android.com/reference/android/speech/SpeechRecognizer).

Build, packaging, protected installation and publication results are recorded
separately once completed. This file alone proves no Android speech-engine run,
speaker audibility, permissioned ASR, iQOO/NPU, Office Kit or eligible submission.
