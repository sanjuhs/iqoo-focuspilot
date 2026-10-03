# Current v20 research pitch renderer

Eight scenes explain the problem, historical guide and typed Qwen footage, current
fast/fallback review routes, reviewed Mira availability, observed activations versus
the synthetic shadow policy, current build evidence and remaining iQOO/event work.
This is pre-event research presentation tooling, not an eligible event submission.

The renderer uses existing local Pillow, FFmpeg/ffprobe and macOS `say` (Samantha,
170 words/minute by default). It downloads nothing, makes no API or model calls,
and never reads the phone. Only `artifacts/v020-pitch/` receives new media. The
two existing privacy-reviewed v12 clips each appear once at original speed, with
continuous historical attribution and a final-frame hold. Their audio is omitted.
Historical app/harness bytes are verified using their own Git snapshots, not
current v20 source equality. Current v20 package/install/bundle/publication and
v19 six-seen-request CPU records receive separate exact committed bindings.

Commit the narration, renderer, README, helpers and all public evidence before
preparing. Supply that full 40-character commit; uncommitted binding changes fail
before output creation. Rendering revalidates sources, footage and preparation.

```sh
python prototype/v020-pitch/render.py --prepare-only --source-commit FULL_COMMIT
python prototype/v020-pitch/render.py --render --reuse-timeline --source-commit FULL_COMMIT
```

`--render` without reuse prepares and renders once into a new directory. Existing
preparation requires `--reuse-timeline`; existing render outputs are refused.
Failures remain visible and require separately reviewed recovery, not overwrite.
No historical script, narration, clip or render is written.

Frames are pure deterministic 1920×1080 RGB at 24 FPS. Existing visual primitives
and the v12 pure frame/seek functions are reused with module-local `OUT` and
`shot` hooks only; historical input/preparation/render functions are never called.
The lock/unlock shot removes the portrait and refresh work, restores only after
checks, then visibly ends the same session with Hide. Diagrams are illustrations,
not physical phone evidence. Scene progression and backward seeks are checked;
encoding verifies duration/streams and fully decodes the final MP4. Root's separate
QA reviews encoded compositions, clips and audio levels. Human complete listening
and physical v20 lock/unlock remain unverified by this utility.

Outputs include `pitch-v020.mp4`, `pitch-v020.srt`, `pitch-v020.ass`, narration,
eight previews, exact input/timeline/prepared-audio identities and a render manifest.
The manifest distinguishes v12 footage, v19 CPU runtime and v20 build/installation;
no current overlay, NPU, Office Kit, causal LLM interpretation, accepted submission
or human audio-review claim is made. The toy's suppression experiment is synthetic
and shadow-only; recurring live policy remains hand-set.

A 600 MB output allowance includes speech, base video, final video and previews.
The strict 15 GB logical budget also counts 218,929,328 bytes of known new global
cache growth. Initial checks reserve the remaining allowance; periodic checks
guard preparation and frame streaming. Existing root storage and symlinks are
handled conservatively; media uses bounded duration/bitrate and no stored frames.
Current bundled weights are hashed as existing input and never copied.
