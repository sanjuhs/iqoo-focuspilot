# Prospective JSON-command confirmation

Prepared 3 October 2026 before this author receives the selected new JSON prompt,
its development outputs or any fresh confirmation requests. This is pre-event host
research under `prototype/`, not eligible competition code. No corpus, inference
capture, confirmation result or promotion exists at protocol creation.

The experiment asks whether **one locked prompt change**, retaining the shipped
seven-label JSON contract, improves complete useful proposals without losing
Pause or other existing behavior. Valid JSON, fewer prompt tokens and a faster
classification alone cannot qualify a candidate. The preceding compact-digit
study lost Pause coverage despite a small aggregate gain; preserve that result.

## Fixed comparison and authoring gate

Both arms use the existing Qwen3.5-0.8B Q4_0 model, host CPU JNI library
`ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e`, context
1,024, four threads, capture off and a 128-token generation ceiling. The baseline
is shipped `LocalModel.renderPrompt`; the candidate changes only the locked prompt
renderer. Both use the **identical shipped JSON grammar** and strict output parser:
an object containing exactly `intent`, whose string is one of `start_focus`,
`pause_focus`, `alarm`, `timer`, `open_app`, `explain`, `unknown`, plus native EOS.
No additional key, digit mapping, trimming, prose extraction, label repair or retry
is allowed. Keep existing chat-control escaping, input bounds, tokenizer, weights,
native implementation and request-state reset unchanged.

The entire original request and validated model intent go to the identical current
`ModelCommandGate` and `CommandNumberWords`. Count actual proposal kind and every
hour/minute/seconds slot. A correct intent with wrong slots, an unintended untimed
focus start, or a wrong accepted action is a failure. Execute no proposal.

The parent must lock the candidate source, rendered template/prompt examples,
grammar, ceiling, development-request inventories and selected baseline/gate/parser
identities, then explicitly authorize corpus authoring. Candidate hashes are
prospectively unset; that is **not permission to author or run an unfrozen arm**.
The informed corpus author may then inspect locked prompts, examples and request
fixtures for overlap, but not candidate development model outputs or fresh results.
Do not repair/select another candidate on this confirmation set.

Freeze protocol, adapters, runner, scorer, Java gate harness, generator, complete
ordered requests/labels, all overlap inventories and model/native/source identities
before either capture. Later amendments after seeing outcomes are development and
require another prospective protocol and new corpus.

## Fresh corpus

Author exactly 100 synthetic English requests: **50 two-row near-negative
families**, each containing one supported immediate request and one closely related
request requiring UNKNOWN. Fixed supported counts are 10 start, **8 Pause**,
8 alarm, 10 timer, 6 app open and 8 explain. Settings, Calculator and Clock each
receive two supported rows. Neither trivial negation nor a known gate rejection
should define every negative: vary refusal, added action, report/quotation,
condition/delay, malformed slots and unrelated or sensitive extensions.

All eight Pause rows are prospectively tagged `pause_preservation`; at least four
also exercise current/ongoing focus or naturally spoken break/cancel-focus wording.
Include at least two resume/start distinctions, four nudge-cause explanations,
eight spoken-number slots across focus/timer/alarm, four duration endpoints
(1 second/7,200 seconds or 120 minutes), two seconds/minutes unit contrasts, and
two midnight/noon meridians. Apply tags before capture and retain difficult useful
phrasing even when the unchanged gate is known to abstain. No exact utterances are
specified here, to avoid creating additional seen prompt fixtures.

A supported request is one immediate focus start/resume/pause, focus status or
nudge explanation, an unambiguous colon alarm or explicit AM/PM English alarm,
one integer focus/timer duration from 1 to 7,200 seconds or 1 to 120 minutes, or
one approved app open. Slotless focus starts/resumes have zero seconds; a duration
in a request must survive as its exact value. All slotless and UNKNOWN slots are
zero. Alarm slots use 24-hour hour/minute integers and zero seconds.

The 50 unknown counterparts collectively cover negation/refusal, compound actions,
conditional/delayed/hypothetical instructions, quotation/translation/reported speech,
unapproved apps, purchases/payments/messages/deletion, unrelated questions,
ambiguous/invalid alarm times, calendar/repeated/multiple alarms, signed/fractional/
multiple/out-of-range durations, unsupported modifiers, cancellation of existing
clock actions, and prompt injection. The semantic label is always `unknown`; an
authored plausible counterpart-domain oracle label independently tests gate refusal.
The oracle route is diagnostic only, not a model prediction or executed action.

Each row freezes ID, family, counterpart ID, utterance, semantic intent, oracle
intent, expected kind/hour/minute/seconds and prospective tags. Do not drop,
relabel or rewrite rows after the first capture. Publish counts/hashes/aggregate
metrics only; corpus text, raw outputs and detailed rows stay in ignored `build/`.
A reproducible generator must keep authored strings in ignored storage too, not
smuggle the complete raw corpus into tracked generator source.

## Overlap inventory

Require zero exact and zero normalized request overlap within the new corpus and
against **all available earlier request datasets, prompt examples, development
fixtures and current test fixtures**. The companion JSON lists actual available
sources, counts/hashes where obtained, and extraction methods. At corpus freeze,
rescan for newly created request/example fixtures and include the selected new
candidate and all its development requests. Missing required inventories stop
freezing; do not silently omit them.

Command sources include the 58-case baseline, 373-row intent-head pool, v0.8/v0.10
sets and confirmation, previous 100-row compact confirmation, every v0.10/compact
development request file, fine-tuning train/validation/held-out requests, native
prompt cases, Laya command cases, earlier task-draft goals, shipped and prior prompt
examples, and all ten synthetic phone requests extracted from their source array.
Include request literals in current Android unit/instrumentation and phone/research
Python test/harness sources. Conservatively including other string literals is
acceptable; record that superset method and counts. Never extract prior model
responses, tensors or private phone captures as request inventories.

Normalize by lowercasing, replacing runs outside ASCII a–z/0–9 with spaces, and
collapsing whitespace. It does not equate number words, synonyms or meanings.
Zero overlap under this rule proves no exact/normalized reuse, **not semantic
independence**. The author knows previous failures and locked candidate examples;
this is informed-author synthetic confirmation, not blind, independent-user,
ASR, multilingual or general-accuracy evidence.

## Bounded execution and scoring

Run exactly two captures: baseline then candidate, 100 frozen rows each, separate
model loads, identical row order, native recurrent/KV state cleared per request.
Each subprocess is bounded at 300 seconds; no retries, overwrites, selective
recaptures or candidate repairs. Preserve the first execution, its start/end/exit/
timeout and every completed/missing ID. If either arm is incomplete, report an
incomplete experiment rather than a reduced-denominator pass or a fresh restart.
Disclose no model scores until both arms are terminal.

An invalid JSON/schema/EOS result has **no semantic prediction** and counts as a
semantic failure even for an unknown row. Route it to gate UNKNOWN, separately
recording invalid-output fallback abstention. Compile the unchanged gate/parser
and run the full original texts through both model routes plus one oracle route;
the oracle outcome must be identical between arms. Refuse changed source hashes,
missing/duplicate IDs, altered row order, malformed integers or absent metrics.

Report raw exact intent, per-intent supported/unknown correctness, confusion,
schema/EOS validity, truncations and invalid fallback counts separately from
model-plus-gate exact full proposal correctness. Report supported false abstention,
wrong accepted kind/slots, unsupported false accept, accepted coverage/precision,
and oracle gate limitations. Preserve complete denominators. Report paired gains
and losses for semantic and full proposals, all six intents, all families/tags,
and every previously correct regression; detailed request rows remain private.

Report model load, first request and subsequent request distributions separately;
prefill/decode/native total, context setup when supplied, Java wall time,
prompt/generated tokens and paired differences. Use sample counts, ranges,
medians, nearest-rank p95 and missing values. Baseline-first ordering, warmed OS
cache, separate loads and uncontrolled thermals/power make timing descriptive host
evidence, not phone latency, NPU throughput, energy savings or activation overhead.

## Prospective decision

A candidate qualifies only for **separate integration/device review**, never
automatic promotion, if both captures are complete and all of these hold:

- At least **four paired supported complete-proposal gains** and zero supported
  complete-proposal losses; supported correct proposals improve by at least four.
- Zero paired semantic-correctness losses across all 100 rows; no per-intent raw
  semantic or complete-proposal coverage decline. All **eight Pause** cases remain
  in the denominator with zero semantic or complete-proposal losses, including
  the prospectively tagged hard spoken/current-focus rows.
- Zero wrong accepted proposals among supported rows and zero unsupported gate
  false accepts in **both** arms. Invalid fallback abstentions stay separately
  visible and cannot inflate semantic accuracy.
- Every latency/token/memory tradeoff and oracle false abstention is disclosed.

A failed criterion rejects this candidate for promotion; preserve the first result.
Passing this small synthetic confirmation still requires a root decision, broader
language/voice evidence, actual phone regressions and measured device costs before
deployment. Existing phone app, releases, model and prompt stay unchanged during
this experiment. This research proves no full assistant, causal mechanistic
interpretability, Snapdragon NPU, Office Kit or eligible submission claim.

Total new protocol/corpus/run artifacts are bounded to 2 MB; no model download,
provider call, training, phone operation, permission change, APK build or Git action
belongs to this protocol authoring task.
