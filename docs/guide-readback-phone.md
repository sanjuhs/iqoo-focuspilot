# Authored-step readback — actual Nothing phone check

Pre-event research, 3 October 2026. All four recorded phases passed and scoped
cleanup was verified. The installed feedback-layout light APK, retained model,
packaged native and app/harness sources match the frozen identities in
[the package manifest](guidance-readback-artifacts.json) and
[the exact physical record](guide-readback-phone-v012.json).

App source: `24f10b62a4a62c22ad6db90ac6339f29e2426dbd`. Pre-run commit: `ada0e3bb6e040f7f21e5b686c1b64a4d21882888`.
Executed harness SHA-256: `6cb39df766a439cb7b6a7f64608db4c684b736604f82dbfddccc324acd8ff71c`.
The harness/selected manifest are recoverable from that pre-run commit; the
record retains their exact digests. No app or harness edits occurred during the run.

## Observed phases

1. Saved one synthetic goal and three authored steps with zero completion marks.
2. Explicit Speak while muted returned the exact refusal; progress stayed unchanged.
3. Restored mute false and explicitly requested the current step. Android's installed
   offline-English engine reached `onDone`, observed as “Mira finished reading aloud.”
   The saved authored record stayed identical. This is callback/UI hierarchy evidence,
   not an independent screenshot or human audibility observation.
4. Loaded the retained Qwen3.5-0.8B Q4_0 model and typed `Stop focus`. The model
   proposed `pause_focus`, `REVIEW REQUIRED`, **1,749 ms** reported native CPU time
   (799 ms prefill, 950 ms decode). No review or action was confirmed. Returning
   to the dashboard left the guide record unchanged. One case is not a latency distribution.

Cleanup removed only the synthetic steps and restored the empty task and mute
false. Focus stayed paused, observation off, 100 virtual points and elapsed
57,331 ms. Microphone and notification grants stayed false; no monitor-service
record appeared. Saving may leave local task-log entries and zero-valued target
keys, so cleanup does not claim byte-identical preferences. No OS permission or
setting, external-app action, microphone or model weight changed.

## Repeat

Use the matching package on an already unlocked own-app foreground. The harness
refuses existing goals/guides/targets, an active session/monitor, mismatched source
or model, or existing mute true. It enters only synthetic authored text, positions
controls clear of this Nothing phone's fixed overlays and scopes cleanup by exact
goal/guide ownership. It never grants permissions or confirms a model action.

```sh
python3 scripts/phone_guide_readback.py --serial YOUR_SERIAL \
  --output artifacts/guide-readback-repeat.json --execute-synthetic-guide-readback
```

Both `completed` and `cleanup_verified` must be true. Merely accepted TTS queue
requests, preparing/reading statuses and the virtual points balance cannot stand
in for a completion callback. Three unsuccessful attempts and the original
package identities remain [preserved](guidance-readback.md#preserved-attempts).

## Still pending

Human audibility, disconnected operation, active microphone exclusion, Stop during
actual playback, unavailable/error/timeout/background platform branches, real ASR
and permissioned monitoring/floating remain separate checks. Qwen inference uses
CPU/KleidiAI I8MM; no iQOO/NPU or Office Kit result is established. This updated
light installation reused existing weights, rather than testing a clean bundled
import. Historical v0.11 phone results retain their original APK identities.
The full hackathon/application/demo goal remains incomplete.
