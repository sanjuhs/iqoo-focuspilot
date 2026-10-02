# v0.12 edited research pitch

This is pre-event preparation. The renderer combines original procedural Mira
illustrations with two checksummed recordings of FocusPilot's own synthetic guide
and model screens. It uses local macOS Samantha narration, measured captions,
1920×1080 frames at 24 fps, and FFmpeg. It calls no APIs, starts no microphone and
performs no phone actions. Earlier pitch outputs and renderers remain untouched.

The eight-scene narration is authored separately in
`docs/v012-research-pitch-script.md`: three measured spoken beats per scene. Each
beat advances an explanatory state. Caption space begins at y=903. Backwards seek
checks verify the same requested frame produces identical pixels after another
time is rendered; sample hashes also require the three beats to differ.

## Inputs and binding

Commit the new renderer, narration and evidence before preparation. Every public
evidence file is recorded with its SHA-256 and its exact Git source revision.
Current app-source hashes must match both the inspected package manifest and its
source commit. The capture harness must match its pre-run Git commit, report hash,
and current file; its binding enters the video manifest too. Historical v0.11
activation observations retain that attribution;
they are not depicted as newly captured v0.12 tensors or semantic explanations.
The 65-parameter policy illustration uses its pinned executable inspector on a
labelled synthetic fixture; it does not control recurring real nudges.

The root-owned recording manifest is `artifacts/v012-phone-demo/record.json`:

```json
{
  "completed": true,
  "cleanup_verified": true,
  "visual_privacy_review": true,
  "microphone_started": false,
  "npu_verified": false,
  "pre_run_commit": "FULL_40_CHARACTER_CAPTURE_PROTOCOL_COMMIT",
  "harness_sha256": "FULL_64_CHARACTER_SHA256",
  "source_commit": "FULL_40_CHARACTER_APP_COMMIT",
  "apk_sha256": "FULL_64_CHARACTER_SHA256",
  "model_sha256": "FULL_64_CHARACTER_SHA256",
  "native_sha256": "FULL_64_CHARACTER_SHA256",
  "clips": [
    {"name": "guide", "file": "artifacts/v012-phone-demo/guide.mp4", "sha256": "FULL_64_CHARACTER_SHA256", "seconds": 25.0},
    {"name": "model", "file": "artifacts/v012-phone-demo/model.mp4", "sha256": "FULL_64_CHARACTER_SHA256", "seconds": 25.0}
  ]
}
```

These illustrative hashes are placeholders, never accepted by the renderer.
Both clips require actual hashes and durations matching FFprobe. Root must inspect
the cropped clips and explicitly set `visual_privacy_review=true` before any audio
preparation or full render. The recorded APK,
model and native identities must match `docs/guidance-readback-artifacts.json` and
the completed/cleaned physical v0.12 report. Crop private system bars and keyboards
in the root-owned recording workflow before offering clips to this renderer.
Keep private raw captures out of Git and the public release.

Each full clip plays once at its original speed in scenes 2 or 3. It must fit the
measured scene; the renderer refuses speed-up or silent truncation. If it ends
early, its final frame is held with an explicit label. The manifest records the
source interval, pitch interval, 1× speed and hold duration. Clip audio is omitted;
the final audio is separately generated narration. Engine completion is not proof
of independently audible phone speech.

## Run after recording is ready

```sh
python3 scripts/render_v012_pitch.py --prepare-only
python3 scripts/render_v012_pitch.py --render --reuse-timeline
```

Preparation alone writes measured narration, 24 captions, the timeline and input
bindings under `artifacts/v012-pitch/`. Measured duration must fall within 180–300
seconds. Inspect the prepared narration before requesting the full render.
An existing timeline requires the explicit reuse option; existing rendered assets
are never overwritten. Revisions need a separately reviewed output workflow.

Frames stream directly to FFmpeg rather than accumulating thousands of images.
The renderer reserves at most 600 MB of output capacity under the strict decimal
15 GB project limit, includes ignored files and Git in its logical-byte count,
and periodically checks storage while producing the base video. Two capped-bitrate
videos plus narration fit this reservation; this is storage, not peak RAM.

The final video gets a full decode check, FFprobe duration/resolution/fps checks,
and a manifest binding all footage, source, narration, captions and deterministic
seek checks. Rendering does not certify encoded-frame visual review, complete human
listening, iQOO/NPU, Office Kit, disconnected operation, event eligibility or
accepted submission. Those remain explicit false/unverified fields and separate
completion requirements.

## Retrieve the selected sanitized footage

From a fresh checkout with no existing capture outputs, download the two sanitized
clips and reviewed capture metadata from the research release. The JSON is copied
to the renderer's dedicated input location; no raw private capture is required.

```sh
mkdir -p artifacts/v012-phone-demo
gh release download research-v0.12 --repo sanjuhs/iqoo-focuspilot \
  --pattern guide.mp4 --pattern model.mp4 --pattern demo-capture-phone-v012.json \
  --dir artifacts/v012-phone-demo
cp -n artifacts/v012-phone-demo/demo-capture-phone-v012.json artifacts/v012-phone-demo/record.json
python3 scripts/render_v012_pitch.py --prepare-only
python3 scripts/render_v012_pitch.py --render --reuse-timeline
```

Keep model weights, private raw screen captures and any credentials out of Git.
This replay uses the existing public synthetic policy and filmed inputs, without
a phone, LLM inference, Office Kit or NPU execution. See
[the selected video and verification scope](../../docs/v012-pitch.md).
