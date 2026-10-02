# Selected v0.12 phone countdown recovery

Verified 3 October 2026 on Nothing A059 / SM7635 / API 36. This is pre-event
research. The selected installed light APK, Qwen3.5-0.8B Q4_0 and CPU native
library match [the package manifest](guidance-readback-artifacts.json).
The app source remains `24f10b62a4a62c22ad6db90ac6339f29e2426dbd`;
no app rebuild, model replacement or permission change was needed.

[Exact physical record](focus-recovery-phone-v012.json) binds the installed APK,
retained model, native library, executed harness commit
`8fa6d48338e0f8c47ff047fda9ad634b6f111628` and harness SHA-256. The successful
first run is retained unchanged under ignored artifacts as well as this public copy.

## Actual outcomes

| Branch | Observed result |
| --- | --- |
| Typed 20-second proposal, review Cancel | Checkpoint unchanged; no action executed. |
| Review again, Confirm, dashboard Stop | Paused after 3,717 ms; retained 16,283 ms. |
| Wait two seconds while paused | Elapsed and remaining values unchanged. |
| Typed plain Start, review Confirm | Resumed the retained remainder, then automatically completed; exactly 20,000 ms added. |
| Second typed 20-second start, review Confirm | Persisted active countdown observed. |
| Force-stop only FocusPilot, reopen | Exact saved elapsed/remainder restored paused; interruption message displayed. |
| Explicit dashboard Start | Resumed retained countdown, then completed; another exact 20,000 ms added. |
| Typed `Cancel my alarm at 7:30` | Qwen proposed `alarm`; original-request validation returned `ABSTAIN`. No alarm/action confirmed. |

All ten recorded phases passed. Native CPU inference for the three supported
proposals was 1,919 / 1,824 / 1,928 ms; the cancellation proposal took 1,772 ms.
These four observations measure native inference, not end-to-end interaction
latency or a performance distribution. Capture was off.

The initial elapsed total was 57,331 ms; final total was 97,331 ms. Final state:
paused, completed countdown with zero remainder, observation off, 100 virtual
points, empty goal/no guide, unchanged denied microphone/notification grants,
and no own focus-monitor service record. Both sequence completion and cleanup
were independently required before accepting the record. Recorded synthetic-session
timer history was retained rather than overwritten to the old total.

The physical report is backed up with [research v0.12](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.12).
Its server size/digest, the original twelve unchanged asset identities and the
unchanged selected source tag passed [publication verification](focus-recovery-publication-v012.json).
Project storage at verification was about 13.822 GB, below the strict 15 GB cap.

## Scope

Recovery uses the **last persisted checkpoint**. This does not establish accounting
for intervals after that checkpoint, deep sleep, unattended survival, ASR, speaker
audibility, permissioned app monitoring, disconnected operation, iQOO/NPU, Office
Kit, or accepted eligible submission. No external-app UI, microphone, Android
settings or alarm action was used. This run is not included in the existing video.
The earlier v0.11 countdown and v0.12 readback/video retain their own attribution.

## Repeat

Use an unlocked, foreground FocusPilot on the exact selected v0.12 light APK.
The harness refuses an active session, observation, existing authored goal/guide,
declared targets, monitor, or unfinished paused countdown. It never wakes the
display or changes permissions. Commit the harness and keep the worktree clean.
Use a new output path; existing evidence is never overwritten.

```sh
python3 scripts/phone_focus_recovery.py --serial YOUR_DEVICE_SERIAL \
  --local-apk artifacts/focuspilot-research-v012-feedback-light.apk \
  --output artifacts/focus-recovery-repeat.json --execute-reviewed-recovery
```

The procedure intentionally starts/resumes two synthetic countdowns, pauses and
force-stops only this research app, then leaves it paused. Python compilation,
five foreground-guard and two asynchronous-checkpoint tests passed. Additional
accounting/observation/balance rejection checks passed; these checks are separate
from the actual ten-phase phone record and do not replace it.

A review also found a minor unaddressed UI branch: resetting an interrupted
recovery may retain its interruption message until the next Start. It does not
change timer arithmetic; physical Reset coverage and any repair remain separate.
