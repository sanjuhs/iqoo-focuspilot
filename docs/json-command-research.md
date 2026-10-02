# JSON command reliability — frozen research

Qwen3.5-0.8B Q4_0 remains selected. One revised JSON prompt is being evaluated
against the shipped prompt; the installed app and its prompt are unchanged.
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
remain unfinished. The fresh captures are pending at this source checkpoint.
