# Original-request validation — research v0.14

Qwen3.5-0.8B Q4_0 remains selected. This revision improves the validator around
the unchanged model and prompt; it does not train the model or improve its raw
predictions. It accepts complete natural request forms for qualified focus
sessions, personal breaks, desired alarms/timers, approved app display and
focus-domain status/reason questions. Original intent agreement, whole-request
matching, numeric parsing, refusals and explicit action review remain required.

The candidate and prospective protocol were committed at
`7fb7a5b30f66fae7ceabfd526726f1151107607e` before new corpus authoring.
The 100 fresh informed-author synthetic requests have 50 supported/unknown pairs,
eight Pause cases and independently reviewed labels/slots. All 137 authoring
inventories have zero exact/normalized overlap; the final freeze also inventories
the already-seen Android fixture source. Raw requests/results stay ignored.

The sole original-prompt host capture completed at
`2648d826d1ad0cbdb4ad5d0232f5fe8752d26920`, exit zero, in 45.89 seconds.
Both validators receive its identical raw intents and full original requests.

| Fresh synthetic measurement | Original gate | Revised gate |
| --- | ---: | ---: |
| Complete supported proposals | 13/50 | 32/50 |
| Supported false abstentions | 37/50 | 18/50 |
| Correct unsupported abstentions | 50/50 | 50/50 |
| Wrong accepted actions/slots | 0 | 0 |
| Complete Pause proposals | 0/8 | 3/8 |
| Oracle-intent supported coverage | 19/50 | 50/50 |

Nineteen complete gains come with zero losses and no per-intent decline.
Oracle routing adds 31 gains without losses or incorrect accepts. All prospective
criteria pass. The model itself is correct on only 32/100 requests: 32 supported
and zero unknown. It proposes tools for all 50 unsupported cases; independent
validation rejects them here. The 18 supported misses remain model intent errors,
including five Pause, seven timer and six explanation requests. This sample does
not prove general safety or real-user/voice accuracy.

One shared capture has 100 canonical JSON/EOS results, 425.13 ms load, 458.36 ms
first native request and 453.74 ms subsequent median on host CPU. There is no
native latency comparison between gates. JVM launch plus 100 validations/output
takes 79.39/78.34 ms for generated baseline/candidate; those are process totals,
not isolated gate or phone latency. Cache/thermal/power conditions are uncontrolled.

Both seen development rounds remain preserved. The final round reuses actual
original-prompt output: supported proposals 24→35/50, oracle 31→50/50, zero losses
or incorrect accepts. All 58 targeted JUnit checks pass. Fresh authoring/runner
utilities pass 17/11 boundary tests. Independent label, source and result reviews
are separate from inference and execute no actions.

App source `1eb2fb55bf0322237bce0bc04942cb0d6652ddcc` integrates the exact
qualified gate into version 14 / `0.14-command-gate-research`. All 158 app JVM
tests pass; lint has zero errors and 65 warnings. Signed light/bundled packages
pass native/model, version, permission and six-notice inspection. Neither requests
Internet access. Streaming packaging reserves a 14,982,537,330-byte peak below
15 GB after removing one verified duplicate generated model asset.

Actual Nothing instrumentation passes all 334 already-seen pure gate checks:
25 positive full-slot checks, 273 negative-route checks and 36 wrong-route checks.
The v0.14 light APK remains installed; the original test APK is restored. Three
named preference identities, paused/off/100/97,331 ms checkpoint, model bytes/hash/
inode, two measured runtime grants and absent own services match before upgrade,
after upgrade, after instrumentation and after cleanup. No model inference,
product UI/tool action, wake, permission grant or network setting change occurs.
Instrumentation/cleanup restart and stop the own process; prior activity lifecycle
is not preserved. Three harness boundary tests pass. [Actual phone record](command-gate-phone-v014.json).

The model/prompt/native runtime, Mira assets and remaining voice/floating workflows
retain their prior evidence scopes; no new NPU, Office Kit, causal interpretation,
bundled-import or eligible accepted submission proof follows from this revision.

[Prospective protocol](../prototype/command-gate-v14-confirm/PROTOCOL.md),
[selection lock](../prototype/command-gate-v14-confirm/selection-lock.json),
[frozen source/data/runtime](../prototype/command-gate-v14-confirm/freeze-manifest.json),
[actual aggregate](../prototype/command-gate-v14-confirm/results.json),
[seen development](../prototype/command-gate-v14-dev/README.md),
[runner and reproduction limits](../prototype/command-gate-v14-runner/README.md),
[Android fixture scope](../prototype/command-gate-v14-device/README.md),
[reversible storage cleanup](command-gate-v14-storage.json).

Reproduction must use the capture-source revision and matching private synthetic
inputs. Integration changes the tracked app gate after that capture; its old
inventory identity remains available in Git and the isolated source snapshots.
Do not overwrite the first capture, reuse this now-seen corpus as a fresh holdout,
or relabel this pre-event prototype as event-written competition code.

The phone harness records the pinned v0.13→v0.14 upgrade once. It refuses a
second run against the already-updated app; no downgrade or data clearing is
part of this proof. [Signed package and source identities](command-gate-v14-artifacts.json),
[separate root selection](../prototype/command-gate-v14-confirm/decision.json).
