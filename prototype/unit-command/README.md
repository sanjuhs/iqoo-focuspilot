# Unit-aware command candidate

Pre-event development research only. This source-only candidate preserves the
installed app, selected model, command prompt, gate and native runtime. No model
calls, phone operations, training, downloads or deployment are part of these
tests. No development corpus or captured outputs were read while writing it.

The seven intents remain unchanged. Duration responses copy the original numeric
quantity and unit instead of asking the model to multiply:

```json
{"intent":"start_focus","amount":0,"unit":"none"}
{"intent":"start_focus","amount":14,"unit":"minutes"}
{"intent":"timer","amount":2,"unit":"hours"}
{"intent":"pause_focus"}
{"intent":"alarm","hour":19,"minute":30}
{"intent":"open_app","app":"calculator"}
{"intent":"explain"}
{"intent":"unknown"}
```

Positive amounts are bounded to 7200 seconds, 120 minutes or two hours. Zero and
`none` are exclusive to untimed Start/resume. Deterministic Java long arithmetic
converts to seconds, then delegates original-request validation to the unchanged
`StructuredCommand`. A separate copy check also requires the original quantity
and unit to agree: a request for fourteen minutes does not accept a model response
of 840 seconds, despite equal total duration. English number words and existing
unit aliases in input use the unchanged `CommandNumberWords` and corresponding
source normalization; output uses canonical plural units only.

`UnitCommand` shares package `dev.focuspilot.prototype` and exposes
`SYSTEM_PROMPT`, `GRAMMAR`, `renderPrompt`, `guardReason`, `parseResponse` and
`validate`. Its Proposal exposes `intent`, `hour`, `minute`, `durationSeconds`,
`app`, `accepted`, `reason`, `amount`, `unit` and `canonicalJson()`. Canonical JSON
uses the previous **seconds** schema for paired scoring. `accepted` means eligible
for a separate explicit review; no action, permission or persistence occurs.
Nonduration forms have amount -1/unit null and delegate the existing parser.
Rejected proposals normalize to unknown; parseResponse throws for malformed data.

Duration parsing conservatively requires exact literal keys in intent/amount/unit
order, literal intent/unit strings, unsigned decimal integers without leading
zeros and whole-object acceptance. Standard JSON whitespace is permitted. Escaped
duration keys or values, reordered duration fields, duplicates, extras, missing
fields, null/boolean/string/floating numeric types, overflow-sized numbers and
trailing output fail. Nonduration forms retain the original strict parser's
key-order and JSON-escape support. Every output is bounded to 1024 UTF-16 chars.
GBNF couples amount ranges to their unit and permits only the exact seven forms.
Actual grammar acceptance and EOS require a separate pinned native capture.

The renderer preserves the original seven generic examples and ChatML/no-thinking
frame, changing only the duration instructions and the Start/Timer example slots.
Reserved input markers remain escaped, with unchanged input/guard bounds. The
existing finite lexical tool/direction, clock/app, negation, compound, privacy,
injection and numeric-evidence rules remain authoritative. Those rules can reject
genuine phrasing or miss unfamiliar semantics; quantity agreement is not a safety
or language-understanding proof. Explain remains a proposal, not evidence of
answer fulfillment or knowledge of a past nudge's cause.

Compile `UnitCommand.java`, `UnitCommandRender.java`, `UnitCommandTest.java` with
the immutable `../structured-command/StructuredCommand.java` and existing
`../android/app/src/main/java/dev/focuspilot/prototype/CommandNumberWords.java`,
using cached Java17/JUnit4, into ignored `build/classes`. Run
`org.junit.runner.JUnitCore dev.focuspilot.prototype.UnitCommandTest`.
Ten grouped JUnit methods cover conversion bounds, zero/none semantics, overflow,
raw parsing, original quantity/unit agreement, malformed source evidence,
nonduration parity, tool/direction controls, privacy/adversarial cases and renderer
bounds. They do not establish LLM accuracy or Android outcomes.

`UnitCommandRender --grammar` prints the exact GBNF. With one selected UTF-8
`id<TAB>utterance` TSV it prints `id<TAB>base64(exact prompt)` after validating all
rows (unique IDs, 1–112 rows, input bounds). Freeze candidate and dependency hashes
before any capture; count actual tokenizer prompts and require <=896 tokens for
context1024/output128. This design has no actual token-count measurement yet.
First captures are openly seen development feasibility; fresh predeclared
qualification and phone/runtime/lifecycle checks precede any integration.
