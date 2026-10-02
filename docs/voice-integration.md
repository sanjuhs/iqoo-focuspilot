# Ask Mira: local voice drafts and companion

Pre-event research, 2 October 2026. Ask Mira now includes the original procedural `CompanionView`, a bounded push-to-talk draft flow and optional explicit readback of a confirmed benign focus action. Qwen3.5 remains the existing text-intent model running through llama.cpp on the CPU. Android speech recognition is a separate OS capability; its speech weights are not included in the Qwen APK.

The user flow is **Speak → review/edit transcript → Understand command locally → review proposal → confirm action**. Recognition callbacks only populate the editable command field. Partial results appear as unfinished text in voice status. Neither partial nor final transcription automatically runs Qwen, a phone action or a shortcut. Typed input remains available when voice cannot run.

## On-device speech boundary

`LocalVoiceInput` calls only `SpeechRecognizer.createOnDeviceSpeechRecognizer`, available on API 31+. It checks `isOnDeviceRecognitionAvailable` and microphone permission. There is no generic/cloud recognizer factory, model-download call, voice-intent Activity, retry loop, wake word or background microphone.

On API 33+, the wrapper invokes `checkRecognitionSupport` before listening and requires an installed on-device English language. It normalizes case and underscore/dash forms such as `en-IN` and `en_IN`. If the preferred English locale is missing, it can recheck one installed English locale. This changes only the local language choice. Empty installed-language lists, unavailable models and failed/unsupported preflight checks keep voice off with a readable message. The app does not trigger a language download.

API 31–32 lacks that language-support preflight API; the wrapper makes this limitation visible and attempts the on-device factory only, handling missing-language/service errors. API 28–30 remains usable for typed commands and local Qwen but voice input is unavailable. These API boundaries follow the official [SpeechRecognizer reference](https://developer.android.com/reference/android/speech/SpeechRecognizer) and [installed language support contract](https://developer.android.com/reference/android/speech/RecognitionSupport).

An explicit Speak tap can open Android's microphone permission prompt. Granting permission does not start recognition: the user taps Speak again when ready. Permission denial or revocation leaves typed input usable. No permission is granted through ADB or application code.

## Lifecycle and exclusion

The pure `VoiceDraftState` assigns a new epoch to every speech request. Background, cancellation, destruction or model-busy transitions invalidate callbacks. Old support checks, partial results, final transcripts and errors cannot overwrite a newer draft. A session may be checking support, listening or processing; all three states exclude local model load/inference. Ask Mira also cancels the actual recognizer before model work. Recognition is bounded to 20 seconds including support checking; timeout cancels/destroys it and requires another explicit tap.

OnStop cancels speech and existing Qwen work, stops readback and invalidates the activity's action-review epoch. OnDestroy destroys the recognizer, shuts down TTS and preserves existing queued native-close cleanup. The Qwen checksum, bundled import, cancellation-before-worker-start and repeated independent action validation remain in place.

`LocalVoiceInput` public API, called on the main thread:

| API | Purpose |
| --- | --- |
| constructor `(Context, VoiceDraftState, Listener)` | Bind platform ASR to the pure gate and UI callbacks |
| `available(Context)` | Check API 31+ on-device factory availability |
| `start()` | Check permission and installed local language support, then begin one bounded session |
| `finishListening()` | Stop recording and await a final editable draft |
| `cancel()` | Invalidate callbacks and cancel/destroy the recognizer |
| `close()` | Permanently destroy the state and platform recognizer |
| Listener `onStatus`, `onDraft`, `onChanged` | Display status, edit the input, refresh controls; no action execution |

Call `state.resume()` onResume; call `state.stop()` and `voice.cancel()` onStop; close onDestroy. Setting `state.setModelBusy(true)` invalidates state, but the caller must also cancel the platform recognizer. The wrapper stores no audio file, transcript history or telemetry. Draft text stays only in the current screen's memory.

## Companion and readback

Ask Mira reads the existing `mute`, `reduceMotion` and `hideCompanion` preferences. Reduced motion disables the illustration's animation; hiding removes only the artwork. Voice recording is still an explicit user control. Listening and local model work change the companion's visible state; leaving the screen pauses it.

The optional **Read confirmed focus status** button is enabled only after an explicitly confirmed Start/Pause focus action. It speaks a fixed benign acknowledgement, not the raw transcript, arbitrary model output or an unconfirmed action. It never speaks automatically. Muting blocks readback. The TTS engine must expose an installed English voice whose `isNetworkConnectionRequired()` is false; unavailable engines/voices leave the text on screen. Initialization/playback has a 20-second timeout, stops the engine and releases the audio busy gate; cancelled or late callbacks cannot announce success. Starting another task or leaving the screen stops audio. This follows Android's [Voice contract](https://developer.android.com/reference/android/speech/tts/Voice).

## What is verified

Seven isolated JVM tests pass for the pure lifecycle state: explicit permission/service/foreground prerequisites; partial versus final draft behavior; late-callback invalidation; background/destroyed screens; model/voice exclusion; malformed or over 500-character transcripts; and one-session bounds. The Android-facing sources were compiled with `javac` against the installed Android 36 SDK and existing app classes. No Gradle build or phone installation was run by this slice while other agents edited the app.

Actual microphone audio transcription, installed language reporting, offline TTS, platform callbacks and permission prompt behavior require root's unified phone test. Their availability is not established by Java unit tests or by Qwen's successful CPU inference. Record device/API/service/language and observed outcomes for each tested branch, including unavailable/denied paths; do not present a simulated transcript as recognized speech.
