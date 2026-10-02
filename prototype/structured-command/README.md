# Structured command development candidate

Pre-event development research only. The installed app, selected original Qwen
model, original prompt, validator, native binary and action-review flow remain
unchanged. No model inference, training, phone action, weights or downloads are
part of this utility. Unit boundaries do not establish language-model accuracy.

`StructuredCommand.java` defines one compact ChatML no-thinking prompt and GBNF
grammar. The response schema uses **intent**, not action:

```json
{"intent":"start_focus","duration_seconds":0}
{"intent":"pause_focus"}
{"intent":"alarm","hour":19,"minute":30}
{"intent":"timer","duration_seconds":300}
{"intent":"open_app","app":"settings"}
{"intent":"explain"}
{"intent":"unknown"}
```

Start duration 0 means start/resume without a new target, otherwise 1–7200 seconds
replaces the countdown. Timer duration requires 1–7200; alarm hour/minute require
0–23/0–59; approved apps are settings/calculator/clock. The GBNF allows only these
seven exact forms and bounded unsigned integers. The pure parser also accepts
arbitrary key order/standard JSON whitespace and escapes, while rejecting extra,
missing or duplicate decoded keys, wrong types, floats, signs, leading zeros,
nulls, booleans, nested values, malformed Unicode and trailing prose. Output is
bounded to 1024 UTF-16 characters. Syntactic validity does not prove EOS; a capture
must separately require actual canonical JSON and model EOS within 128 tokens.

API in package `dev.focuspilot.prototype`:

- `SYSTEM_PROMPT`, `GRAMMAR`, `renderPrompt(original)` freeze the exact renderer.
- `parseResponse(output)` throws on malformed syntax/schema and returns a Proposal.
- `guardReason(original)` returns a conservative preflight reason or null.
- `validate(original, output)` returns a reviewed candidate or canonical unknown
  on guarded, malformed, unsupported, or source-disagreeing proposals.
- Public Proposal fields: `intent`, `hour`, `minute`, `durationSeconds`, `app`,
  `accepted`, `reason`; `canonicalJson()` emits only the normalized exact schema.
  `accepted` means eligible for **explicit action review**, never execution consent.

Input is one nonblank line up to 500 UTF-16 characters with valid Unicode and no
C0/C1 controls or line separators. Reserved chat markers are escaped in the
renderer, and independently rejected by source validation. Quotes, policy
injection wording, action negation, compound/conditional/deferred requests,
financial/message/deletion/capture/permission requests, existing Clock edits,
unsupported extra tool arguments and ambiguous numeric evidence abstain. Ordinary
enumerated trailing no-upload/no-audio-recording preferences remain inert privacy
constraints rather than action negations. Those clauses stay present in the
actual prompt; only validation's analysis copy omits the recognized inert clause.

This candidate avoids enumerating complete request sentences. It uses explicit
request direction/domain evidence and independently checks source arguments:
contiguous English/digit numeric spans, seconds/minutes/hours converted to bounded
seconds, one clock expression with 24-hour notation or explicit AM/PM/noon/
midnight, and exactly one approved app target. Numeric evidence must agree with
the generated slots; additional number spans, malformed adjacent number words,
multiple clocks/durations, approximate values, wrong tools and wrong focus
direction abstain. `CommandNumberWords` is imported unchanged from existing app
source and compiled alongside the candidate; its provenance is shared, not copied.
Independent capability cues also refuse an appended app launch or
explicit focus action even when there is no conjunction. Clock as the device
that wakes the user and a timer's studying-purpose context remain permitted;
neither is automatically interpreted as a separate app launch or focus action.
Bare open/launch/navigate cues conservatively refuse non-app proposals even for
an unapproved app name; display/bring/visibility cues identify approved targets.

Limits: these are finite English lexical/argument heuristics, not arbitrary
semantic understanding or a security guarantee. Genuine requests can abstain.
Unrecognized paraphrases, indirect assertions, adversarial wording and missing
arguments may still expose gaps. Tool-purpose clauses and privacy exceptions are
bounded; argument agreement alone cannot prove the rest of a sentence is harmless
or fulfilled. Explain establishes only a focus-domain status proposal; it cannot
invent the cause of a past nudge or establish current-session elapsed information
that the app has not recorded. No unconstrained tool call, automatic execution or
deployment is justified by this lab.

`StructuredCommandRender` CLI accepts `--grammar` (GBNF to stdout) or one selected
UTF-8 TSV path with `id<TAB>utterance`, emitting `id<TAB>base64(exact rendered
prompt)` to stdout. It rejects duplicate/malformed IDs, extra columns, overlong
inputs and more than112 rows, and validates all rows before printing. Compile all
three Java files plus the unchanged app `CommandNumberWords.java` using the cached
Java17/JUnit4 tools; classes belong in ignored `build/classes`. Run
`org.junit.runner.JUnitCore dev.focuspilot.prototype.StructuredCommandTest`.

Fifteen isolated JUnit methods cover exact schemas and parser ambiguity,
source-slot/tool/direction agreement, hour conversion, privacy preservation,
unsupported/injected requests, numeric partial matches, no-conjunction cross-tool
requests, legitimate device/purpose contexts and renderer boundaries.
The grammar is below4096 bytes. Before any model capture, count actual pinned
tokenizer prompts and require at most896 tokens for context1024/output128; source
character length is not a token-count proof. Freeze source/prompt/grammar/parser
identities and openly label any first small capture **development feasibility**.
Fresh qualification, Android lifecycle/package proof and action confirmation
would be separate required work before considering integration.
