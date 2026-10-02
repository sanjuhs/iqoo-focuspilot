# Authored-guide physical test harness archive

This is the exact harness snapshot used for the attributed research-v0.11
synthetic authored-guide phone run. It was copied while that process was live,
then checked against the unchanged source at terminal completion. It is not an
independent replay or a pre-start source attestation. The app APK remains bound to
its separate full source commit and pinned model/native identities.

The selected harness in `scripts/phone_task_guide.py` subsequently receives
failure-path cleanup improvements. The archived source preserves the actual run;
it is not the recommended script for future phone tests. It needs the existing
`scripts` directory on Python's import path, and its explicit action flag starts
only an own-app synthetic guide test. It refuses existing goals/plans, requires
unlocked own-app foreground and never grants permissions or invokes model/voice.
The original empty goal and no-plan state are restored through the app UI;
synthetic task-save event entries and explicit zero target keys may remain.

The record establishes only the exact observed authored UI branches. Full
readback, stale-instance, task-switch, validation/corruption, export/backup,
monitoring, iQOO/NPU, Office Kit and accepted event submission remain separate.
