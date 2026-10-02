# Current Mira research pitch

A separately rendered **4:35** video reflects v0.10 and keeps the historical v0.3
pitch intact. This is a reviewable application concept/research asset with original
procedural illustrations, not current live phone footage or an eligible event entry.
The narration separates historical typed phone actions, the current installed
package, fresh synthetic command results and actual remaining hardware gates.

- Video: `artifacts/pitch-current.mp4`, 1920×1080 H.264/24fps, AAC, 274.836 seconds.
- Captions: `artifacts/pitch-current.srt`, 30 measured narration segments, also burned in.
- [Editable narration and shot plan](current-research-pitch-script.md).
- [Source-bound figures](../prototype/current-pitch/README.md).
- [Immutable evidence](current-pitch-evidence.json) and
  [automated render manifest](current-pitch-render-manifest.json).

Renderer source: `6ca1d02284ecffd643b9d50ea6b1b18d610f88d1`. App source shown in the
video remains `bcc24733655e4eced67d68ff5c47f7ab97d60b36`; adding a video does not
change the installed APK or establish a new physical action result.

## Reproduce locally

Python with Pillow, installed macOS Samantha/`say`, FFmpeg and FFprobe are required.
No network, provider key, model weights or phone connection is used. From the repository:

```sh
python3 scripts/render_current_pitch.py --prepare-only
python3 scripts/render_current_pitch.py --reuse-timeline
```

The first command measures each speech paragraph, validates the 3–5 minute bound,
and binds voice/rate/full source plus audio/timeline/caption hashes. Reuse refuses a
mismatch. Frames are stateless and streamed to FFmpeg rather than kept as thousands
of PNGs. Outputs stay in ignored `artifacts/current-pitch/`. Narration timing is
274.836 seconds at the measured Samantha185 settings; the script's early estimate
was shorter because word-count timing does not include actual speech pauses.

Metric inputs are pinned by source SHA and commit. Mutable historical documentation
may be recovered at the recorded commit; executable policy/checkpoint bytes must
match the actual pinned synthetic model. An invented six-feature example is passed
to the real policy's `inspect`; contributions sum in logit space, and unit suppression
changes the actual synthetic score. No transformer mechanism or human risk concept
is inferred from that diagram.

## Checks and remaining review

Full FFmpeg decode passes. Caption timing is monotonic/non-overlapping and within
the video; A/V duration difference is approximately 0.003 seconds. Audio mean is
−18.9 dB and peak −4.6 dB. Ten out-of-order scene requests reproduce exact pixels;
early/late scenes change and actual encoded chart frames show the intended reveal.
All encoded scene end states, critical full-size captions and a crossfade sequence
were inspected. These checks do not replace complete human listening/playback.
That review remains pending and is explicitly false in both manifests.

The video uses no phone screenshot, account, raw usage trace or private transcript.
The friendly procedural Mira is original renderer artwork using the project's
charcoal/lilac/teal vocabulary. It illustrates the product; the actual Android
floating window still requires manual permissions and physical lifecycle tests.

Before submission, verify the signed-in dashboard's format/deadline, event-source
eligibility and actual live iQOO/NPU/Office Kit requirements. A GitHub asset and a
research label cannot substitute for admission or an accepted submission receipt.
[Full remaining deliverables](remaining-deliverables.md).
