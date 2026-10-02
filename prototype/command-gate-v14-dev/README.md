# Complete-request validator development — unpromoted

This pre-event research repairs complete natural forms in an isolated copy of
`ModelCommandGate`. The original app, selected Qwen3.5-0.8B Q4_0 model, prompt,
number parser, JNI, APKs and phone remain unchanged. No new inference, training,
download or action ran.

The previously frozen JSON comparison's 100 requests are now openly seen
development data. We reuse **only its original-prompt baseline output**, not the
rejected prompt's output, to compare original and candidate gates. Both consume
the identical complete original request and model intent. A separate oracle-intent
route exposes validator coverage without claiming actual model accuracy.

| Seen route | Original correct supported /50 | Candidate correct supported /50 | Gains | Losses | Wrong accepts | Unsupported abstentions /50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original-prompt generated intent | 24 | 35 | 11 | 0 | 0 | 50 |
| Same separately authored oracle intents | 31 | 50 | 19 | 0 | 0 | 50 |

Generated Pause coverage rises 2→4/8. The remaining 15 generated-route supported
abstentions come from original model intent errors on these examples; the candidate
never repairs, overrides or infers another model intent. The oracle's 50/50 result
is seen grammar coverage, not learned model performance or universal safety.

The repair adds anchored noun requests with explicit durations, qualified focus
nouns, focused-work wording, return-to-session and personal-break forms,
concentration countdown cancellation, approved-app display and complete
focus-domain status/reason questions. All original early refusals and normalization
are byte-identical. Number parsing, duration bounds, clock parsing and intent
agreement stay unchanged. Slots are parsed from complete matched forms; no general
substring extraction or discarded argument tail is introduced. Newly added
passive/causal reason forms require explicit focus context; bare generic warning
questions remain unsupported. Existing original nudge wording retains its scope.

**58 JUnit tests pass:** all five current `*GateTest` suites and the unchanged
number-parser suite (48 tests), plus ten new candidate tests. Existing unsafe
fixtures cover negation, compounds, conditions, quotes, reported commands,
unsupported apps, clock cancellation, controls, signed/fractional/multiple slots,
wrappers and wrong intent. Candidate tests add qualified/noun forms with exact
slots, correct contraction versus malformed spaced contraction, explicit-domain
questions and the corresponding refusal/cross-intent regressions. These are host
unit checks, not Android execution or fresh held-out evidence.

Two named development rounds are retained. `initial` passed the same aggregate
scores but allowed two new generic reason forms; `explicit-domain` restricts them
and adds meaningful refusal fixtures. The final source/tests were fixed before its
compilation/evaluation. Both rounds used the same prior raw capture; no model ran
again and no corpus was replaced. This repair is openly disclosed in
[development-results.json](development-results.json).

## Frozen selection

- Candidate [ModelCommandGate.java](ModelCommandGate.java), SHA-256
  `b4b04604b42920ed41186a5b0d20cba40302e4a41f6091055cdf92cc7dbe3c15`.
- New tests [CandidateGateTest.java](CandidateGateTest.java), SHA-256
  `90c351fc9c05f07bff2de2f4db088d96a33de479e1e45c51dba33655fadcdfd1`.
- Original gate SHA-256
  `cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4`.
- Unchanged number-parser SHA-256
  `e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d`.
- Unchanged original model adapter SHA-256
  `2f6784c524ca9304fd714b86c04f5b1c3c5deb7e5ff562fbc34ae32c39e51e5d`.

[candidate.json](candidate.json) binds selected source/tests, prior cases/requests,
original-prompt capture/source and unchanged refusal/numeric blocks.
[development-results.json](development-results.json) publishes aggregate routes,
per-intent/per-family gains, source hashes and all attempts. Raw requests, captured
proposals, source snapshots, class files and test logs remain ignored under
`build/`. The directory reserves at most 2 MB, including ignored files; completed
work uses about 1.15 MB.

**GO to independently authored fresh frozen gate confirmation only.** Selection
needs root's committed lock before new corpus authoring, unchanged original model
prompt, identical raw intents across both gate arms, complete exact-slot scoring,
all baseline safety tests, meaningful new unsafe examples and no automatic app
promotion. Model/voice errors and actual phone cost remain separate requirements.

## Reproduction

From the repository root with existing Java 17/JUnit caches and prior private
JSON100 artifacts:

```sh
python3 prototype/command-gate-v14-dev/run_development.py --round replay
```

A unique named round is required; existing evidence is never overwritten. The
runner snapshots candidate/tests, original test/support sources, helper and prior
capture hashes before compilation. It uses the unchanged checksummed gate scorer,
with 30-second compilation/JUnit/gate subprocess bounds. Complete tuple scoring
compares kind/hour/minute/seconds. A failed test preserves logs and refuses reduced
suite scoring. No native library is loaded or generation called in this runner.
