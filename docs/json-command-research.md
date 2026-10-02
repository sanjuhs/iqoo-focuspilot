# JSON command reliability — evaluated and rejected

Qwen3.5-0.8B Q4_0 remains selected. One revised JSON prompt was evaluated
against the shipped prompt and rejected; the installed app and its prompt are unchanged.
This is pre-event host research, not a new Android release or eligible submission.

The actual seen development comparison increased complete supported proposals
from 12/18 to 16/18, with four gains and no supported semantic or proposal losses.
Raw unknown predictions rose 2/18 to 9/18. All 36 outputs had exact JSON and native
EOS; the gate accepted no incorrect proposals. Pause remained 2/3 and two supported
requests still abstained. Subsequent host native median rose 444.00 to 483.84 ms;
median prompt tokens rose 158 to 200. These are exploratory, uncontrolled host
measurements. [Full development evidence](../prototype/command-json-dev/README.md).

The candidate, grammar, token ceiling and prospective protocol were committed at
`542d9c5afd117fb32b4d3878e37d924a3e840451` before fresh corpus authoring.
The fresh informed-author set has 50 supported/unsupported pairs, including eight
Pause cases and natural wording beyond the current validator's patterns. All
labels/slots were reviewed before inference. Two signed-duration negative rows
were reworded before capture because normalization removes sign punctuation;
the original set is retained privately. Raw requests and model outputs stay ignored.

Necessary criteria include at least four complete supported gains, no supported
proposal losses, no semantic losses across all 100 rows, no intent/Pause decline,
and no incorrect accepted proposal in either arm. Passing is only a prerequisite
for separate integration and real-device review. It cannot automatically change
the app. [Prospective protocol](../prototype/command-json-confirm/PROTOCOL.md),
[selection lock](../prototype/command-json-confirm/selection-lock.json),
[corpus metadata](../prototype/command-json-confirm/corpus-manifest.json),
[runner and repeat constraints](../prototype/command-json-runner/README.md).

Both confirmation arms use the same pinned model, JSON grammar, full original
requests, argument validator, 1,024-token context and four CPU threads. Their
confirmation JNI binary is distinct from the seen development binary; results
and timings remain separately attributed. There is no weight training, phone
action, permission change or NPU execution in this experiment. Complete voice,
persistent monitoring, actual iQOO/Office Kit and accepted eligible submission
remain unfinished. The two fresh captures completed successfully without retries at source
`1f36dfdd635d3b94c26a307d968673587eaf598c`.

## Fresh frozen result and decision

| Measurement | Shipped prompt | JSON candidate |
| --- | ---: | ---: |
| Complete supported proposals | 24/50 | 29/50 |
| Supported false abstentions | 26/50 | 21/50 |
| Raw semantic predictions | 35/100 | 57/100 |
| Raw unsupported correctly unknown | 0/50 | 16/50 |
| Exact JSON with native EOS | 100/100 | 100/100 |
| Wrong accepted proposals | 0 | 0 |
| Complete Pause proposals | 2/8 | 1/8 |
| Raw Pause intent correct | 4/8 | 4/8 |
| First native request | 470.40 ms | 499.66 ms |
| Subsequent host native median | 448.14 ms | 478.50 ms |
| Median prompt tokens | 164 | 206 |

**Rejected for promotion.** Seven complete supported gains came with two Pause
losses. Five semantic predictions regressed: four Pause and one warned-focus
explanation. The unchanged raw Pause total masks four gains and four losses;
complete Pause coverage actually declines. The candidate still proposes tools
for 34/50 unsupported requests, although the validator rejected them all here.
Zero observed wrong accepts does not prove universal safety.

The oracle-intent route reached only 31/50 complete supported proposals, with
19 validator abstentions. It establishes a separate parser limitation: model
changes alone cannot make these requests executable through the current gate.
Retain these natural requests as seen development evidence for a later carefully
validated grammar repair, followed by a new frozen confirmation. Do not treat
this confirmation set as fresh again after inspecting its results.

The candidate's subsequent host median is about 6.8% higher here. Baseline-first
ordering, warmed filesystem cache, changing device conditions and differing
outputs preclude causal or population performance conclusions. No peak-memory,
battery or phone-latency measurement was collected in this comparison.

The runner enforces hashes/order/complete IDs, CPU-only/capture-off metrics and
exact slots, and bounds each native subprocess at 300 seconds. Both completed
in 45.25/48.42 seconds with exit zero. Fifteen authoring/overlap tests and twelve
runner failure tests pass. An independent audit verified both raw records, every
proposal/transition, all source/runtime and 89 inventory hashes, and public
metadata privacy. Raw requests, generated strings and activations from this comparison stay out of Git.

[Full aggregate](../prototype/command-json-confirm/results.json),
[explicit rejection](../prototype/command-json-confirm/decision.json),
[executed source/artifact bindings](../prototype/command-json-confirm/freeze-manifest.json).
The selected app, model, prompt, phone state and release APKs are unchanged.

A later read-only phone check matched the previous restoration snapshot and
original test APK: selected app/model unchanged, paused/off/100/97,331 ms, the
two measured grants unchanged and own services absent. No phone behavior was
exercised by that preservation check.
