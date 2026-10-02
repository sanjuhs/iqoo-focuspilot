# Prospective original-request gate confirmation

Prepared 3 October 2026 before this author inspects the new gate candidate or
creates its confirmation corpus. This is pre-event research under `prototype/`,
not eligible competition code. No corpus, native capture, result or promotion
exists at protocol creation. Root must lock one useful candidate and explicitly
authorize corpus authoring after committing its selection lock.

The question is whether a narrowly changed original-request validator recovers
useful complete proposals while retaining correct behavior and rejecting unsupported
requests. The two rejected prompt experiments and their raw semantic limitations
remain evidence. This study keeps **Qwen3.5-0.8B Q4_0 and its shipped prompt unchanged**;
a parser repair cannot be described as model learning or improved raw model accuracy.

## Locked comparison

Use the existing pinned model and host CPU JNI library, context 1,024, four
threads, original seven-label JSON grammar, 128 maximum generated tokens and
capture disabled. Perform **one** frozen 100-row native capture using shipped
`LocalModel.renderPrompt`. Both gate arms receive the identical complete original
request and the same strictly decoded model intent from that single capture.

Strict output validation requires native EOS and an exact JSON object containing
only `intent`, whose string is one of start_focus, pause_focus, alarm, timer,
open_app, explain, unknown. No trimming, prose extraction, schema/label repair,
retry or changed prompt is permitted. Invalid/truncated output has no semantic
prediction, counts as a raw failure even for unknown, and routes to UNKNOWN with
separately counted invalid-output fallback abstention.

The baseline gate/parser are exact selected app-source snapshots. One separately
locked research candidate gate/parser is compiled in isolation under the same
Java interface. Freeze both gate files and number-word parsers even when parser
bytes are identical. No source-class collision, accidental baseline replacement,
partial-text extraction or proposal execution is allowed. Compare actual proposal
kind and every integer hour/minute/seconds slot; a wrong duration, alarm time or
unintended untimed start is a failure.

Root must commit candidate source/metadata/development-request inventories,
protocol and selection lock before authoring. Candidate hashes remain prospective
nulls until that lock; null does not authorize an unfrozen study. After explicit
authorization, the informed author may inspect locked candidate source and request
fixtures to avoid overlap, but not new development outputs or fresh outcomes.
Do not repair or select another gate using this confirmation set.

Before capture, bind protocol, selected original prompt/grammar/ceiling, model/
native identities, both gates/parsers, native runner, strict decoder/scorer, Java
gate harness, generic data validator, private authored rows, ordered requests,
labels and every overlap inventory in the final freeze manifest. Source changes
after viewing results require a new protocol and corpus; preserve the first result.

## Fresh informed-author corpus

Author exactly 100 synthetic English rows in 50 two-row near-negative families:
one supported immediate request and one related required-UNKNOWN counterpart.
Supported counts are start_focus 10, **pause_focus 8**, alarm 8, timer 10,
open_app 6 and explain 8. Settings, Calculator and Clock each receive two rows.
Freeze reciprocal counterpart IDs, family, complete request, semantic/oracle intent,
expected kind/hour/minute/seconds and prospective tags before capture.

All eight Pause rows carry `pause_preservation`; at least four test natural spoken
or current-focus pause/break wording. Include two resume/start distinctions,
four nudge-cause explanations, eight spoken-number slots, four duration endpoints,
two seconds/minutes contrasts and two midnight/noon meridians. Keep difficult
useful phrasing even when the baseline gate is known to abstain. Never filter or
relabel rows based on oracle-gate output, candidate development output or capture.

Supported behavior is one immediate focus start/resume/pause, focus status/nudge
explanation, one unambiguous colon or explicit AM/PM English alarm, one integer
focus/timer duration 1–7,200 seconds or 1–120 minutes, or one approved app open.
Slotless starts/resumes use zero seconds; a stated duration must survive exactly.
Alarm uses 24-hour hour/minute and zero seconds. Other slotless actions and UNKNOWN
have zero slots. The independently authored oracle domain route diagnoses each
gate separately and is never treated as a model prediction or real action.

Unknown counterparts collectively cover negation/refusal, compound actions,
conditional/delayed/hypothetical requests, quotation/translation/reported speech,
unapproved apps, sensitive purchases/payments/messages/deletion, unrelated questions,
ambiguous/invalid alarm times, calendar/repeated/multiple alarms, signed/fractional/
multiple/out-of-range durations, unsupported modifiers, cancellation of existing
clock actions and prompt injection. Vary the refusal mechanism rather than making
every negative a trivially negated positive.

Raw author rows, requests, model outputs and per-case details stay in ignored
`build/`. A tracked generic generator must not contain authored corpus literals.
Public manifests contain hashes, counts, extraction methods and aggregate outcomes.
The author is informed by prior failures and locked candidate source; this is fresh
synthetic wording, not blind, independent-user, ASR or general-accuracy evidence.

## Zero-overlap inventory

Require zero exact and zero normalized overlap within the new corpus and against
all earlier request/example/development/current-test inventories. The companion
JSON pins the actual available inventories, including previous command/head/
fine-tuning datasets, prompt examples, native/Laya/task-draft requests, the ten
seen phone diagnostics, prior compact/JSON development fixtures, and **the last
100-row JSON corpus plus its preserved initial author set**. No prior captured
model responses, activation vectors or private phone screenshots are inputs.

At freeze, rescan current Android/Python test fixtures and include new gate
candidate source, generic tests and every development request. Every required
inventory must exist and have a recorded hash/count/extraction method; fail rather
than silently omit unavailable sources. Conservative decoded source-string
supersets are acceptable and must be labelled. Zero literal strings in a pinned
structural test file is explicitly recorded, not treated as a missing file.

Normalization lowercases, replaces runs outside ASCII a–z/0–9 with spaces and
collapses whitespace. It does not equate meanings, synonyms or number words;
zero overlap does not establish semantic independence. Resolve accidental overlaps
only before the final corpus freeze, retain the initial author set and document
replacement count/reason without using model or oracle outcomes. After capture
begins, drop or rewrite no row.

## Single capture, two gates

Load the model once and capture all 100 rows in the same frozen order. Clear native
recurrent/KV state before every request. Bound the subprocess at 300 seconds; no
retry, selective recapture, overwrite or retuning. Record actual start/end/exit/
timeout, completed/missing IDs and artifact hashes. An interrupted or incomplete
capture remains incomplete with its first output retained; do not score a smaller
denominator as confirmation or restart it as unseen data.

After terminal capture, compile isolated baseline/candidate gate snapshots and feed
the same validated raw intents plus full requests to each. Also evaluate separately
authored oracle domain routes for both gates. The model-only semantic score must
be identical across arms by construction; independently verify this binding.
Oracle coverage/false abstentions/wrong accepts are a separate parser diagnostic.
No accepted proposal executes, reaches a phone or changes Android app source.

Report raw semantic/confusion/schema/EOS/invalid fallback once; report each gate's
exact full proposals, supported correct/false abstention, wrong accepted kinds/slots,
unknown false accepts, accepted coverage/precision and per-intent counts. Report
paired full-proposal gains/losses for every family, hard tag and supported intent,
including all eight Pause cases and all previously correct regressions. Keep
explicit 50/50 and per-intent denominators; retain detailed rows privately.

Report single-capture load, first-request and subsequent native distributions,
prefill/decode/context setup/Java wall time, prompt/generated tokens, sample counts,
ranges/medians/nearest-rank p95 and missing metrics. Report actual gate processing
time only if measured. There is **no native latency difference between gates**:
they share one capture. Timing is descriptive host CPU evidence with warmed caches
and uncontrolled thermals/power, not phone/NPU latency, energy or an app speedup.

## Prospective decision

Necessary conditions for a separate integration/device review are complete frozen
capture and gate evaluations; at least **four paired supported full-proposal gains**;
zero supported full-proposal losses; zero per-intent full-proposal decline; and
zero wrong accepted proposals among supported rows or unsupported false accepts
in **both** arms. All eight Pause cases remain in the denominator, with zero Pause
losses. Disclose oracle-gate outcomes and any new parser behavior, including costs.

A failed condition rejects this candidate for promotion; preserve the first result
without retuning. Passing only qualifies it for root review, broader language/
voice testing, real phone regressions and measured device costs before deployment.
It does not automatically select a new app gate or prove general safety. Existing
app/release/model/prompt state is unchanged during this research. No Snapdragon
NPU, Office Kit, mechanistic interpretation or eligible submission claim follows.

New protocol/corpus/run work is bounded to 2 MB. Protocol authoring performs no
model inference, gate execution, Android build, phone operation, download, training,
provider call or Git mutation.
