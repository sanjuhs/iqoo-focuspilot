# Prospective compact-intent confirmation

Prepared 3 October 2026 before this author sees the selected compact candidate,
its outputs or fresh requests. This is pre-event research, not eligible
event-written competition code. At protocol creation there is no corpus, model
capture, result or promotion. The parent will lock one candidate and explicitly
authorize corpus authoring before the next phase.

The question is whether a shorter prompt and a constrained one-digit answer can
improve useful bounded-command coverage with the existing Qwen3.5 model and
original-request validator. The earlier representation head improved semantic
classification but reduced accepted correct actions; a short answer or valid
schema alone therefore cannot qualify this candidate.

## Fixed comparison

Both arms use the existing Qwen3.5-0.8B Q4_0 GGUF, CPU host JNI library, context
1,024, four threads and capture disabled. Model weights, tokenizer, native
implementation, selected Android `ModelCommandGate` and `CommandNumberWords`
remain unchanged. No provider calls, training, downloads, phone operations,
permissions, actions, APK replacement, NPU execution or release promotion occur.

The baseline is the current `LocalModel.renderPrompt`, JSON intent grammar and
128-token generation ceiling. The candidate is one locked research class exposing
`renderPrompt`, `GRAMMAR`, `MAX_TOKENS` and a fixed digit-to-intent map. Its raw
answer must be exactly one ASCII digit from 0 through 6, followed by native EOS;
no trimming, prose extraction, retry, label repair or parser guessing is allowed.
The locked map is 0 unknown, 1 start_focus, 2 pause_focus, 3 alarm, 4 timer,
5 open_app, 6 explain. Any changed map or serialization requires a new protocol
and a new held-out corpus. Both arms give the complete original utterance and
their validated semantic intent to the same compiled current Java gate.

The freeze manifest must bind the protocol, both adapter classes, rendered
constant prompt inventories, grammars, generation ceilings/map, runner, corpus
generator, labels/requests, Java gate harness, model/native identities and selected
gate/parser source hashes before the first fresh capture. Candidate development
fixtures and examples are seen data and belong in the overlap inventory. Do not
evaluate multiple candidates on this held-out set or repair the selected
candidate against its outcomes. An amendment after viewing results is a new
development experiment, not this confirmation.

## Fresh corpus and scope

Author 100 synthetic English requests after the candidate freeze: 50 supported
requests in 25 two-row families and 50 required abstentions in another 25 two-row
families. The supported counts are fixed at 10 start_focus, 8 pause_focus, 8 alarm,
10 timer, 6 approved-app opens and 8 explain. Each approved Settings, Calculator
and Clock target receives one two-row family. Families vary wording, wrappers and
digit/English-number representation while keeping the same bounded contract.

Every row receives a stable ID, family, semantic label, oracle domain intent,
expected kind/hour/minute/seconds, and prospective hard-case tags before capture.
Unsupported semantic intent is always unknown; a plausible non-unknown oracle
domain label tests the independent gate's refusal. UNKNOWN expectations have
zero slots. All other expectations preserve the complete required action/slots;
partial parsing, correct intent with wrong duration/time, or an unintended
open-ended focus session is a failure.

Supported requests are one immediate focus start/resume/pause, focus status or
nudge explanation, an alarm with an unambiguous colon time or explicit AM/PM
English time, an integer timer/focus duration of 1–7,200 seconds or 1–120 minutes,
or an approved app open. The corpus retains fresh hard wording for current-focus
pause and warned-during-focus explanation even where the unchanged gate is known
to abstain. Label usefulness separately from the gate's observed coverage.

Unsupported families must cover negation/refusal, compound instructions,
conditional/delayed/hypothetical requests, quotation/reported speech/translation,
unapproved apps, destructive/payment/message requests, unrelated questions,
ambiguous or invalid alarm times, calendar/repeated/multiple alarm modifiers,
signed/fractional/multiple/out-of-range durations, unsupported extra modifiers,
existing-action cancellation and prompt injection. Unsupported rows are not
selected merely because the gate readily recognizes a negation word.

Hard tags must identify all boundary durations, midnight/noon meridians,
spoken-number slots, resume-versus-new-focus wording, current-focus pause and
warned-focus explanations in the authored corpus. These tags cannot be assigned
after seeing outcomes. Known gate limitations remain rows in the denominator.

Reject exact and normalized utterance overlap within this corpus and against all
mandatory prior command inventories: the 58-case baseline, all 373 intent-head
rows, v0.8 evaluation, v0.10 evaluation, v0.10 confirmation, the 36-request v0.10
development round, baseline prompt examples, and the locked candidate's examples
and development fixtures. Record each inventory's SHA, count and extraction
method. If a required inventory is unavailable, stop rather than silently omit
it. Additional known command fixtures must also be inventoried before freezing.
Normalization lowercases, replaces runs outside ASCII a–z/0–9 with spaces and
collapses whitespace; it does not normalize number words, meanings or paraphrase
families. Zero overlap under this limited rule is not semantic independence.
Revise overlapping authored rows only before the corpus freeze, recording the
final complete corpus. After capture begins, drop or rewrite no rows.

The author is informed by earlier results and may inspect the locked prompt and
examples after this prospective protocol. This is fresh synthetic wording after
candidate selection, not human-blind evaluation, independent user sampling,
ASR-transcript evidence, multilingual robustness or general command accuracy.
The parent receives corpus counts/hashes, not request text, before terminal
evaluation; that separation does not make the informed author independent.

## Execution and runner adaptation

Adapt the existing `command-v10-confirm` runner in a separate research directory.
Compile the current baseline adapter and compact candidate against the same JNI;
invoke native prepare/generate using each arm's frozen prompt/grammar/ceiling.
Perform one complete 100-row capture per arm, baseline then candidate, with a
separate model load per arm, identical frozen row order, and native recurrent/KV
state cleared per request. Bound each subprocess at 300 seconds. Record actual
start/end/exit/timeout and artifact hashes; refuse overwriting existing captures.
Do not disclose per-case or aggregate model outcomes until both captures are
terminal. An interrupted/incomplete arm remains incomplete; preserve its output
and report missing IDs rather than scoring a reduced denominator as confirmation.

Use strict baseline JSON object validation (only `intent`, one of the seven
allowed string labels) plus native EOS, and strict candidate digit plus native
EOS. Invalid or truncated outputs have no semantic prediction: count them as
semantic failures even for unknown rows. Route them to UNKNOWN for the action
gate and separately count invalid-output fallback abstentions. This prevents
parser failure from inflating raw unknown-intent accuracy.

Compile the unchanged gate/parser and evaluate both mapped model routes on all
original texts. Also evaluate the separately authored oracle domain route once;
both arms must have identical oracle-gate outcomes. The oracle diagnostic exposes
gate limitations rather than claiming they are model errors or executed tasks.
Use the actual `Proposal` kind/hour/minute/seconds; execute no proposal. Runner
checks should catch missing/duplicate IDs, malformed digit/JSON/EOS, incorrect
slots and invalid-output unknown fallback accounting before inference.

## Required reporting

Report separate model-only and model-plus-gate results for both arms:

- Semantic exact intent correctness, supported correctness and required unknown
  correctness, confusion counts and per-intent counts; invalid outputs separately.
- Schema plus EOS validity, EOS truncations, emitted digit/JSON validity and any
  invalid-output fallback abstentions. Valid syntax is not semantic correctness.
- Exact kind and all slots, supported correct proposals, supported false
  abstentions, wrong accepted kinds/slots, required-unknown false accepts,
  total accepted coverage and accepted precision. Keep denominators explicit.
- Paired supported gains/losses and per-intent/per-family/hard-tag transitions for
  semantic and full-gate correctness. Include all wrong accepted outcomes and
  all previously-correct supported regressions; preserve detailed rows privately.
- Oracle exact gate coverage/refusal and its unchanged identity across arms.
- Model load, first request and subsequent native latency, prefill/decode/total
  native times, Java wall times, prompt/generated tokens and paired latency
  differences. Report medians and nearest-rank p95 with sample counts and ranges,
  retaining the first request separately. Include actual metrics per arm and
  count missing values explicitly rather than inventing measurements.

Host latency is descriptive. Baseline-first order, unflushed OS cache, uncontrolled
thermals and separate loads are confounders. It cannot establish phone latency,
NPU throughput, energy savings, activation overhead or an app speedup. A fewer-token
answer is not itself measured end-to-end improvement. Store raw text, utterances,
requests, compiled classes and per-case results in ignored `build/`; tracked
aggregates/manifests omit request text and raw model output.

## Promotion decision

The candidate qualifies for a separate device/integration review only if exact
supported model-plus-gate correctness strictly improves, observed wrong accepted
proposals remain zero in both supported and unsupported groups, and there are no
paired semantic or full-gate losses on the prospectively tagged hard supported
rows. Report per-intent losses and every other supported regression explicitly;
any per-intent coverage decrease requires rejection or a separate documented
tradeoff review, never automatic promotion. Report prompt-token and latency
tradeoffs even if coverage improves; timing benefits alone cannot qualify it.

Passing these criteria on 100 authored requests does not promote the candidate,
prove universal safety, repair known gate limitations, or establish the assistant's
full objective. Preserve a rejected/uncertain result. A root decision, broader
independent language/voice evidence, actual phone regression and measured device
costs are separate prerequisites before any deployed prompt change. The selected
phone app, Qwen weights and existing releases remain unchanged by this experiment.
