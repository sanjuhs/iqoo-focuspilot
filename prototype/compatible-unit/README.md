# Compatible unit candidate — development repair

This is a new, source-only pre-event development repair after the previous unit
candidate failed integration conditions. It is not a fresh confirmation result,
app integration, deployment or evidence of model accuracy. The installed app,
original model/prompt/gate/native runtime and all previous candidates remain
unchanged. No fresh data, captured outputs, model calls or phone operations were
used to write this repair.

`CompatibleUnitCommand` delegates **exactly** to `UnitCommand` for SYSTEM_PROMPT,
GBNF, ChatML rendering and strict response parsing. Duration forms still copy
amount/unit and normalize to bounded canonical seconds; the other five forms
retain their original schema. Its Proposal matches the previous public fields
and `canonicalJson()`, with a diagnostic `validationRoute` and `origin`/`source`.
The identical provenance aliases are `FAST_LOCAL_REQUEST`, `CHECKED_MODEL` or
`UNKNOWN`. Parse-only acceptance
is schema validity, not authorization. Every real action requires the original
separate action-level review.

Validation runs these checks in order:

1. The unchanged global Unit/Structured original-input guard, plus a prospective
   local-context restriction for personal possessives and third-person pronouns/
   family/work roles. My/our own state, normal contractions and phone's Settings
   remain allowed. This additional scope check precedes both recognition/model
   validation branches.
2. The unchanged exact Unit response parser, including all bounds and types.
3. Mandatory copied source quantity and unit agreement. Untimed focus cannot
   ignore a duration or numeric argument. Equivalent-but-converted quantities
   remain invalid, even if the selected gate would accept their seconds.
4. Explain requires a local focus-status domain and every lexical token to come
   from a bounded English status/policy vocabulary. A focus keyword cannot admit
   weather, translation, calculation, financial or unrelated factual questions.
5. The selected app `ModelCommandGate` may preserve a complete original request
   only when its kind and **all** canonical hour/minute/second/app slots agree.
   Otherwise the unchanged Unit validator decides the proposal.

The quantity helper is explicitly derived from
`../unit-command/UnitCommand.java`'s `quantityAgrees`, not reflection access.
It adds a zero/none source check and normalization of contiguous digit/unit
slots such as `17minutes`, which the selected gate already accepts. Existing
longest exact numeric suffix and public `CommandNumberWords` behavior remain.
The bounded trailing privacy-clause analysis pattern comes from the immutable
Structured validator. Explain strips only those known inert privacy clauses
before testing all remaining tokens; the actual prompt keeps them intact.

Compile the new Java files with unchanged `UnitCommand.java`,
`UnitCommandRender.java`, `StructuredCommand.java`, app `CommandNumberWords.java`
and the selected app `ModelCommandGate.java` using cached Java17/JUnit4. Classes
belong in ignored `build/classes`. Run
`org.junit.runner.JUnitCore dev.focuspilot.prototype.CompatibleUnitCommandTest`.
The renderer CLI delegates the immutable Unit renderer: `--grammar` or a selected
`id<TAB>utterance` TSV, yielding `id<TAB>base64(prompt)` after whole-file checks.
Freeze every dependency SHA; candidate source alone does not bind behavior.

The first eleven grouped pure tests check exact contract delegation, prior pause direction
and app punctuation, mandatory quantity copies, all clock/tool slots, malformed
JSON, bounded Explain, off-domain/adversarial requests, unchanged Unit fallback
and no inferred numeric arguments. They neither prove preservation of an entire
external cohort nor establish fresh language-model, Android or action outcomes.
The lexical vocabulary is deliberately bounded and can reject legitimate
questions. It is not semantic understanding or a security guarantee; a supported
Explain proposal still does not prove actual answer fulfillment or a past nudge's
cause. A finite development checker, frozen fresh qualification and real
phone/runtime/lifecycle evidence would remain separate requirements.

`recognize(original)` is a separate, pure local fast path. After the mandatory
global guard it tests all seven selected gate intent routes, checks complete kind
and canonical slots, requires copied duration evidence, and restricts Explain to
the same whole-token status vocabulary. Exactly one match yields an inert
`FAST_LOCAL_REQUEST` proposal; ambiguity/no match yields unknown. Unknown can be
offered to the model through a separate reviewed flow, but never triggers model
inference here. Accepted `validate(original,response)` proposals are labelled
`CHECKED_MODEL`; refusal/abstention and parse-only proposals are `UNKNOWN`.
Known local requests do not establish Qwen accuracy. Model-only and fast-plus-model
pipeline evaluation must be reported separately. This fast path intentionally
retains the selected gate's narrower coverage (including no hours); the unchanged
Unit model-validation route can handle unfamiliar forms independently.

Fourteen grouped tests include all supported fast-recognition kinds, actual
source/slot preservation, provenance and refusal of ambiguous, conditional,
negated, off-domain or unfamiliar requests. No model fallback is run in tests.

The third-person scope check is also finite: named possessives (including curly
apostrophes), plural possessives and common family/work roles are refused. It can
overreject a harmless role mentioned as context and cannot identify every name
or indirect reference. Accepted requests still require explicit action review.

Dependency provenance at authoring:

- UnitCommand.java: `ab4dda259e6c914c416e38abc8a00af00075d5fe0f6e0eb89ddff193956cb8ed`
- StructuredCommand.java: `e178e05d2c64473e5bbed2072c69b163faaeb7cafa07077263824b615e92575a`
- CommandNumberWords.java: `e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d`
- Selected ModelCommandGate.java: `b4b04604b42920ed41186a5b0d20cba40302e4a41f6091055cdf92cc7dbe3c15`
- UnitCommandRender.java: `4c346603244f26c849c885d2e90146c2db6e9d1e21e1602d12464f2573b72a26`
