# Local readback and prerequisite refusal — actual phone branches

Prepared 2 October 2026. Pre-event research v0.11, app source
`e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a`. On Nothing A059/SM7635/API36,
matching installed APK, retained model and native identities were checked before
a protocol-bound own-app test. The harness and protocol were committed before
the physical run; the installed app was unchanged.

| Observed branch | Result |
| --- | --- |
| Setup readiness | Usage Access off; local observation off; notifications blocked; microphone off; on-device speech factory available |
| Attempt visible monitor with observation off | Prerequisite message appeared, switch reset off and no own monitor-service record appeared |
| Typed `Stop focus` | Qwen3.5-0.8B Q4_0 proposed `pause_focus`; gate required review; native CPU metrics 1,804 ms (855 prefill + 949 decode) |
| Explicit reviewed Pause | App displayed the confirmed pause result; session was already paused, so no active→paused transition is claimed |
| Explicit fixed-status readback | UI displayed the engine's completed callback with an installed offline English TTS voice |
| Return and read-only recheck | Paused focus, observation off, points 100 and elapsed 57,331 ms unchanged; own monitor-service record absent; microphone/notification grants still false |

The readback speaks the app's fixed acknowledgement, “You confirmed a pause. Take
a gentle breath.” It is not arbitrary transcript/model output. The app selects an
English voice whose Android API says a network connection is not required; the
specific engine/voice ID was not recorded. **The completion callback does not prove
independently audible speaker output, volume, human-heard words or a disconnected
whole-device workflow.** Actual microphone transcription and installed English ASR
support remain untested and separate from TTS and Qwen.

The monitor attempt reached the early observation/Usage Access guard. It does not
exercise later notification denial, real selected-app events, cooldown/override,
notification Stop, permission revocation or OEM background behavior. No permission,
settings, microphone or external-app action was performed by this harness.

[Physical report](readback-phone-v011.json),
[fixed-label readiness snapshot](voice-readiness-v011.json),
[pre-run protocol](../prototype/readback-proof/protocol.json),
[raw report](../prototype/readback-proof/result.json).
Four test-harness fixtures distinguish transient/error/missing/muted messages from
engine completion and reject changes to paused focus/points/elapsed time. Six
report-audit fixtures protect source/protocol bindings, branch order, callback
classification, finite consistent metrics and failed cleanup. The read-only auditor
attributes this record and explicitly leaves full voice/monitoring incomplete.

## Repeat the bounded test

Keep the matching research app in unlocked foreground, already paused with local
observation off and no own monitor service. The test confirms a benign Pause and
explicitly attempts fixed-status readback. It never grants permissions. Missing,
muted, failed or timed-out voices are recorded as their actual terminal branch;
`completed` alone is not a claim of speech success. Review `tts_outcome`,
`engine_completion_callback_observed` and `cleanup_verified` separately.

```sh
python3 scripts/phone_readback.py --serial YOUR_DEVICE_SERIAL \
  --local-apk artifacts/focuspilot-research-v011-light.apk \
  --expected-apk-sha256 6541ced715c48d8fd226e6dd2c8ff762485cda6901ded06e43bae4f97893adc2 \
  --source-commit e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a \
  --output artifacts/readback-repeat.json --execute-reviewed-pause-readback
python3 -m unittest discover -s scripts -p test_phone_readback.py -v
python3 -m unittest discover -s scripts -p test_readback_phone_audit.py -v
```

For actual voice/monitor tests, the user can choose Microphone, notifications and
Usage Access through **Set up Mira**, then separately start a bounded voice draft
or enable local usage reading/background focus. The setup path does not itself
start recording or observation. The pending manual choices, actual ASR/audio,
permissioned monitoring, floating mode, disconnected execution, Clock, iQOO/NPU,
Office Kit and eligible accepted submission remain in the [full plan](remaining-deliverables.md).
