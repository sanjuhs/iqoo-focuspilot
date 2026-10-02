# Mira v0.12 — current recorded research demo

The selected video is **4:41** (280.638 seconds), 1920×1080 H.264 at 24 fps with
AAC narration and 24 measured, burned-in caption segments. Eight scenes explain
Mira, authored guidance, actual local Qwen inference, reviewed actions, tensor
observations, the shadow policy, open-source evidence and the iQOO next step.

This is an edited research recording with original procedural Mira artwork.
The goal remains the complete on-device assistant and eligible hackathon demo;
this video does not establish final admission, eligibility or accepted submission.

## Actual phone footage

A harness committed before the run recorded two silent clips from the matching installed
v0.12 APK on Nothing: guide 10.369829 s and model 9.339 s. Keyboard entry happened
before recording. The selected crop removes system bars; metadata guards checked
own-app foreground throughout capture. Sampled assistant review saw only synthetic
content, with no keyboard, account or real task/history. Raw captures stay ignored.
The [exact capture record](demo-capture-phone-v012.json) and source at its recorded
pre-run commit bind APK/model/native/harness identities.

The guide shows the current authored step, explicit Speak and the completed TTS
status. Mark/Undo was verified before recording; it is not presented as filmed.
The model clip shows already-entered `Stop focus`, Understand and an actual
`pause_focus` / `REVIEW REQUIRED` result: 1,849 ms native CPU,899 ms prefill/950 ms
decode,155 prompt/eight generated tokens,capture enabled. Model load, context
setup, UI, ASR and user review are outside that native timing. No action was
confirmed. Four finite width 1,024 tensor summaries were independently read after
recording; they are not all visible in the selected clip. Scene 5 deliberately
shows labelled historical v0.11 summaries. Bar heights are normalized per vector;
shape and sign are illustrated without a shared amplitude scale or semantic claim.

Both clips play once at 1× speed. The final frames are held for narration with a
visible label. The diagrammatic review/cancel choices are illustrations, not
unrecorded executions. Audio is separately generated local Samantha at 170 words per minute narration;
phone audio and microphone recording are absent. A TTS completion status does
not prove independently audible playback.

Scoped cleanup removed the synthetic guide and restored empty task/mute false,
paused focus, observation off, 100 virtual points and elapsed 57,331 ms; runtime
grants stayed unchanged and no monitor record appeared. Saved task-log entries
and zero target keys may remain. [First failed capture](demo-capture-first-attempt-v012.json)
is retained; a scroll-position error stopped it before recording and cleanup passed.

## Source and checks

[Editable narration and shot directions](v012-research-pitch-script.md),
[renderer](../scripts/render_v012_pitch.py), [reproduction instructions](../prototype/v012-pitch/README.md),
[immutable render manifest](v012-pitch-render-manifest.json),
[identities](v012-pitch-evidence.json) and [QA](v012-pitch-qa.json).
The selected app source is 24f10b62a4a62c22ad6db90ac6339f29e2426dbd; media changes
do not modify its APK or relabel historical phone outcomes.

Full decode passed. Caption timing is monotonic/non-overlapping within the video.
Audio mean −19.0 dB and peak −4.2 dB; A/V duration difference 0.013 s. Deterministic
backwards seeks passed and 24 encoded beat samples were inspected, including
full-size critical captions. Four source-versus-encoded phone-frame comparisons
at 1 s/7 s yielded 37.6–39.6 dB PSNR with changing pixels in both clips; those samples
support original-speed presentation, not proof of every encoded frame. This
sampled assistant review does not replace complete human listening/playback,
which remains false in the manifests. The source crop has its own sampled review.

[First failed narration preparation](v012-pitch-first-prepare.json) produced no
speech/video; its FFmpeg duration argument was repaired. The [first complete
render](v012-pitch-first-render.json) stays preserved unselected after clarifying
that phone tensor observation and laptop intervention experiments are separate.
Historical [v0.10 pitch](current-pitch.md) assets remain unchanged.

## Remaining delivery

Actual ASR, consented monitoring/floating, disconnected operation, clean bundled
import, iQOO/NPU/Office Kit, general phone/IoT tasks, complete human playback,
event-written eligible code and accepted application/submission are still pending.
Qwen3.5-0.8B Q4_0 remains the selected CPU model. The synthetic 65-parameter network
remains in shadow mode with nonnegative connection weights and signed biases;
its displayed ablation is a toy forward computation, not LLM semantic understanding.
[Full remaining deliverables](remaining-deliverables.md).

The selected video, captions, sanitized source clips, capture metadata, render
manifest, QA and identity evidence are backed up with the
[v0.12 research release](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.12).
Raw private captures and host narration intermediates remain excluded.
