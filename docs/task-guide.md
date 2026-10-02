# One small step — private authored task guide

Prepared 2 October 2026. **Pre-event research; v0.11 source `e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a`.** The final source passes 143 JVM tests and lint zero errors/65 warnings. Signed light packaging is inspected and installed with APK/private-model hash parity; paused focus, observation off and 100 points are unchanged. During the initial installation snapshot, no wake, UI, task action or permission grant was requested. [Immutable packaging identity](task-guide-artifacts.json) records both inspected signed packages. Later authored UI outcomes are recorded below; voice and the remaining branches stay unverified.

## Later physical coverage

The [12-phase Nothing-phone report](task-guide-phone-v011.json) covers a synthetic
three-step save, Mark/Undo, completion/Undo, exact saved-record recovery after real
process restart, replacement Cancel/confirm and clear Cancel/confirm with cleared
state still absent after restart. Focus remained paused, observation off, points
100 and elapsed 57,331 ms throughout. Cleanup restored the original empty goal
and removed the synthetic guide; task-save event entries and zero target keys may
remain. No model, voice, permission/settings or external-app action was invoked.
This is attributed physical evidence, not an independent replay, generated plan
or verification of real-world step completion. [Repeat and limitations](task-guide-phone.md).

## What the user controls

The dashboard's **ONE SMALL STEP** panel lets the user write their own checklist for the saved focus task. It is neither an LLM-generated plan nor a screen-action agent. One line is one step; blank lines are ignored, tabs become spaces and surrounding Unicode spaces are trimmed. The saved plan has **one to eight steps**, each at most **120 UTF-16 code units**, with original submitted input bounded to **1,024 UTF-16 units**, including blank lines. A supplementary character such as many emoji counts as two units. Invalid surrogate pairs, control characters and embedded Unicode line/paragraph separators are rejected rather than silently accepted.

**I've done this step** increments user-reported progress by one; **Undo last completed step** restores the last completed step. Both stop at the plan bounds. Completing every step displays a completion message, without finishing focus, charging/refunding points, opening an app or verifying any real-world outcome. Text such as “Send the draft” stays inert authored text. No command parser, model or external executor consumes it.

Saving a new plan is an explicit tap. Replacing an existing or invalid saved plan requires review and resets its progress; cancellation preserves it. **Clear my steps** separately reviews deletion of this plan and its completion marks, while retaining the task, model and focus state. Changing the saved focus task through the existing **Save task & targets** flow separately pauses focus/monitoring; that existing behavior must not be attributed to a checklist action.

## Task association and stale state

The plan stores the SHA-256 of the exact saved goal, not another copy of raw goal text. A blank/currently different goal disables Mark, Undo and Speak. Returning to the same exact saved goal can re-enable the retained plan; changing a goal does not silently relabel its steps. The editor can show retained steps for review, but saving them for a different task explicitly replaces and resets the plan. A goal hash is association metadata, not encryption or anonymity.

Each successful mutation writes a new random revision. Mark/Undo/Speak reject a revision changed since the displayed plan. Replacement confirmation checks both reviewed revision and goal hash again; clear confirmation checks the reviewed revision. A changed record is refreshed with a request to review again, rather than applying an old progress increment to new steps.

**Source-review repair:** Speak now checks the displayed revision before goal association; a changed record is refreshed and refused, without automatically reading the new content. Saving reloads the current record before deciding whether replacement review is required. The newly supplied stop-speech callback is invoked by persistence/progress changes, confirmed clear, global data deletion and saved goal changes. These repairs were inspected in source, not physically exercised. Two dashboard instances, pending confirmation and a background/resume transition remain in final verification.

## Local record, recovery and deletion

The existing app-private SharedPreferences file stores `taskGuide.*` fields: schema 1, revision, goal hash, count, completed count and up to eight plaintext steps. There is one saved plan, not a multi-goal archive. Restoration validates schema/count/hash/revision presence, entry types, text bounds and progress. Invalid records expose an unavailable-plan message with controls blocked until the user clears or saves a reviewed replacement; bad progress is never silently clamped and bad steps are not dropped from a partial plan.

Writes/deletion use `commit()` and disclose failure to confirm durable storage. A failed commit is not proof that disk contents changed; recovery may return the older record, so retry before relying on saving/deletion. Clearing removes the plan prefix; existing **Delete focus data** clears the common preference file, then resets this panel/editor. App-level deletion retains downloaded model weights as already disclosed. An unsaved editor draft is not promised durable recovery.

Task steps do not enter the bounded private summary export, event trail, model prompt, few-shot examples or laptop consumer. The manifest disables app backup and the data-extraction rules exclude shared preferences/cloud backup/device transfer. These are source configuration boundaries, not a test of every OEM migration tool or a claim that plaintext private preferences are encrypted. The user can still manually disclose text they type or choose to speak.

## Optional local readback

**Speak this step offline** is a separate explicit tap that sends the current authored step to the existing Android TTS engine. It honors the companion mute preference, blocks during active microphone draft input and uses an installed English voice advertised as not requiring a network. Missing/not-ready local voice leaves readable text/status; there is no cloud recognizer fallback or automatic language-model request. The TTS engine receives the spoken step, so “not exported” does not mean “never passed to an on-device OS component.”

MainActivity's existing `onStop` stops playback and `onDestroy` shuts down TTS. Checklist progress/replacement, confirmed clear, global deletion and saved task edits explicitly request playback stop through the supplied callback. Periodic refresh does not automatically stop unrelated status speech. No checklist operation starts a microphone, monitor, overlay, exact alarm, wake lock or new permission prompt. Actual installed voice availability, audio, mute and lifecycle stop behavior remain physical test requirements. [Existing voice boundary](voice-integration.md).

## Manual checklist — partial physical coverage

The later record covers parts of items 1–4 and 6: exactly three steps, progression,
replacement and scoped clear, plus actual process restart. Input limits/corruption,
stale two-instance reviews, task switching, all-data deletion, TTS and exports
remain pending. The complete checklist is retained below so partial proof cannot
close those branches.

Use synthetic, harmless authored text on the exact final installed APK; record source/APK/model identities and initial focus/observation/virtual-point state. No OS grant is needed just to create/mark a checklist.

1. Save a task, then one to eight steps; inspect normalization and rejection of a ninth step, 121-unit step, over-1,024-unit input and malformed Unicode. No rejected submission changes the saved plan.
2. Mark one step, Undo, finish all steps and Undo again. Compare focus checkpoint, points and enabled services before/after; task progress alone changes none of them.
3. Recreate/return to the Activity and recover exact saved steps/progress. Separately test process recovery; distinguish durable saved plan from an unsaved draft and the existing focus recovery policy.
4. Edit and cancel replacement, then confirm replacement and verify progress resets. With two dashboard instances or a record changed during review, stale Mark/Undo/Speak/replacement/clear must refuse instead of acting on old content.
5. Save a different goal: old plan completion/readback stays disabled until explicitly reviewed/saved for that goal. Switch back to the exact original goal and inspect association. Record the separate goal-edit focus pause instead of misreporting it as a checklist effect.
6. Cancel clear, then confirm clear; recreate to verify removal. Exercise global focus-data deletion and confirm plan/editor removal without deleting the model. Inject corrupt fixture records only in a separate test environment to verify blocked restoration and explicit replacement/clear; no private production preference scan is needed.
7. Try explicit readback with mute on/off, unavailable local voice, active voice draft and Activity stop. Verify no hot microphone/automatic inference, and verify progress/replacement/clear/deletion/task edits stop actual playback as requested, without claiming unobserved audio cancellation.
8. Produce a harmless bounded summary export through the existing reviewed flow and check it omits authored step text. No export/backup claim is upgraded to physical proof until the actual output/recovery is inspected.

The [v0.11 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.11) is published with both APKs and both immutable evidence files;
all four server sizes/SHA-256 digests match local files and the tag resolves to the full app-source commit above.
The authored branches above are observed; the **full task-guide verification remains incomplete**. An authored checklist is a useful guidance layer; it does not complete broad phone automation, actual iQOO/NPU/Office Kit use or eligible submission. [Remaining deliverables](remaining-deliverables.md).
