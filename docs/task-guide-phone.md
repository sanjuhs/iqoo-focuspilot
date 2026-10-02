# Authored task guide — actual phone branches

Prepared 2 October 2026. **Pre-event research v0.11**, app source
`e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a`. An actual own-app UI test ran on
Nothing A059/SM7635/API36 with the matching installed light APK, private Qwen model
and native library. It began with no goal/guide, paused focus, observation off,
100 virtual points and 57,331 ms accumulated focus. No model inference occurred.

| Observed branch | Result |
| --- | --- |
| Save synthetic task and three authored steps | Exact steps and task association persisted; UI showed the first step |
| Mark / Undo | Progress 0→1→0; UI and durable record agreed; Mark rotated revision |
| Actual process force-stop and restart | Exact saved record, revision and progress 1 recovered; next-step UI agreed |
| Complete all / Undo | Progress 3, completion UI and disabled Mark; Undo restored step 3 at progress 2 |
| Replacement Cancel | Original record and progress unchanged, including revision |
| Replacement confirm | New two-step plan saved, progress reset to 0, old extra step absent |
| Clear Cancel | Saved record unchanged |
| Clear confirm and process restart | All guide fields removed and no-plan UI restored; task remained until cleanup |
| Cleanup and later read-only check | Original empty goal and no-guide state restored; paused/off/100/57,331 ms unchanged |

All **12 recorded phases passed**, with the same focus checkpoint at each phase.
Steps report what the user marked; they do not prove an external task was completed.
No microphone, TTS, permission/settings, external-app action or Android install was
performed by this harness. Saving a task uses the app's existing pause/target flow;
focus was already paused. No global data deletion occurred. Synthetic task-save log
entries and explicit zero target keys may remain: this is semantic cleanup, not a
byte-identical restoration of the complete preference file.

[Source/APK/model/native/harness-bound report](task-guide-phone-v011.json),
[exact raw report and execution archive](../prototype/phone-guide-proof/README.md).
The harness source was copied while its process was live and checked unchanged at
terminal completion; the evidence is attributed, not an independent replay or a
pre-start source attestation. Subsequent mock-tested cleanup repairs record errors
on lock/ADB failure and enable ownership-checked cleanup before a Save tap can time
out. Those repairs were not part of the archived physical run.

Eight harness tests protect existing goals/plans, active sessions, declared targets,
user changes and failed cleanup. Six report-binding fixtures reject changed frozen
sources, partial commits, malformed/missing/reordered phases, Boolean progress,
cleanup failure and inconsistent raw records. The artifact auditor's separate
`v11_authored_task_report_binding` checks these bindings; `v11_task_phone_proof`
remains incomplete. No validator independently sees the phone or certifies hardware.

## Repeat only in an empty, paused research installation

Unlock FocusPilot and keep its dashboard in front. The script refuses any existing
goal, guide or declared target and any active focus/observation. It uses only
synthetic text, restores the empty goal/no-guide state through the app's UI and
never changes OS permissions. If the phone locks, ADB fails or the user changes the
state, the report records failure; do not assume cleanup succeeded. Inspect both
`completed` and `cleanup_verified`, then review final state before retrying.

```sh
python3 scripts/phone_task_guide.py --serial YOUR_DEVICE_SERIAL \
  --local-apk artifacts/focuspilot-research-v011-light.apk \
  --expected-apk-sha256 6541ced715c48d8fd226e6dd2c8ff762485cda6901ded06e43bae4f97893adc2 \
  --source-commit e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a \
  --output artifacts/phone-guide-repeat.json --execute-authored-guide
python3 -m unittest discover -s scripts -p test_phone_task_guide.py -v
python3 -m unittest discover -s scripts -p test_authored_phone_audit.py -v
```

## Still required

The [full checklist](task-guide.md) retains input/Unicode limits, corrupt records,
disk failure, two-instance/stale reviews, goal switching, unsaved drafts, global
data deletion, actual readback/mute/voice cancellation, export omission and OEM
backup/migration branches. Voice, monitoring, floating companion, disconnected
inference, sleep, Clock, iQOO/NPU, Office Kit, event-code eligibility and accepted
submission remain separate. This authored UI proof does not certify the rejected
model-generated task-draft/import scaffold.
