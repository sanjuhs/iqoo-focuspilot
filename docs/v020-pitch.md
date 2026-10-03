# Mira v0.20 — current research pitch

The selected edited video is **4:04** (244.083333 seconds), 1920×1080 H.264 at
24 fps, with AAC narration and 24 measured captions. It introduces original Mira,
user-authored steps, local proposals, fast/Qwen review routes, opt-in availability,
inspection tools and the actual iQOO/Office Kit work still ahead.

[Editable narration and shot directions](v020-research-pitch-script.md),
[renderer and reproduction](../prototype/v020-pitch/README.md),
[render manifest](v020-pitch-render-manifest.json),
[QA](v020-pitch-qa.json) and [artifact identities](v020-pitch-evidence.json).
App source stays `81287b2b08ccedc050635b0b8a27154bed3b5d87`; renderer source is
`4ec1d17b74560df615fa394d29b860a4ebf20595`. The movie does not change the app.

## Footage and illustrations

Two existing privacy-reviewed v0.12 own-app clips play once at original speed:
the 10.369829-second authored guide and 9.339-second unconfirmed typed model
proposal. Historical version labels stay visible, and final-frame holds are
labelled. Clip audio is omitted; narration is separately generated using the
installed local Samantha voice. No new phone capture, microphone, permission,
model call or action occurs. The guide's TTS callback does not prove speaker
audibility; the model clip confirms no action.

The current command and lock/unlock/Hide flows are source-bound illustrations.
Physical v20 portrait restoration remains unverified. The model remains
Qwen3.5-0.8B Q4_0. v19's six openly seen CPU requests and 2.361-second load retain
that release attribution; they are not fresh accuracy or current-video latency.
Historical tensor bars show the first eight values normalized within each vector,
without a shared amplitude scale or semantic claim. The separately labelled
65-parameter shadow policy uses its actual pinned inspector on synthetic inputs;
its toy suppression is not causal interpretation of the LLM or a live phone policy.

## Actual media checks

Full decode and duration/resolution/frame-rate checks pass. Captions are monotonic
and fit within the movie. Mean audio level is −18.9 dB, peak −4.3 dB and audio/video
duration difference 0.004333 seconds. Deterministic backward seeks and explanatory
progression pass. The assistant sampled all 24 encoded beats, inspected full-size
return/late Hide/final frames, and found no caption overlap or private content.
These are sampled visual checks; complete human playback/listening remains pending.

Four source-versus-encoded samples at 1 and 7 seconds measure 37.6–40.5 dB PSNR.
The [first QA attempt](v020-pitch-first-qa.json) is preserved as failed: it cropped
at requested x=1345 rather than encoded x=1344. A separate corrected QA matches the
actual YUV420 chroma grid and reference pixel format; the 28 dB threshold is
unchanged and the video was not rerendered. This diagnosis is supported by measured
shift comparisons; FFmpeg documents the overlay's subsampling variables in its
[official overlay contract](https://ffmpeg.org/ffmpeg-filters.html#overlay).

## Remaining live demo

Keep this as a dated research pitch. Current UI, permitted voice/usage workflows,
physical Mira lifecycle, current bundle import, actual iQOO NPU, Office Kit,
general phone/IoT automation and complete human listening remain unfinished.
Eligible event-written code and accepted application/submission are separate
requirements. [Full remaining delivery](remaining-deliverables.md).

Older movies and their exact source attribution remain available; this recording
does not relabel historical footage as v20 phone execution.
