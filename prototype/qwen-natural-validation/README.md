# Whole-request natural validator candidate

This is an isolated, unpromoted research candidate for the existing Android
`ModelCommandGate`. It adds explicit complete forms for focus/work blocks and
periods, ending an ongoing session, exact Clock wake-up requests, lasting/measured
countdowns, foregrounding approved apps and local focus-status/nudge questions.
The model proposes an intent; this validator checks the original full request,
exact tool and slots. It never executes actions or loads a model.

The existing 1–7200-second duration bounds, whole-number parser, clock-time checks,
negation/compound/conditional/control/length guards and tools remain selected.
Exactly/precisely are enumerated duration-slot modifiers. Noon and midnight are
exact named times. Alarm nouns can explicitly carry a new qualifier. Natural
clock/countdown forms are checked before the older broad slot captures so words
such as `lasting` and `that rings at` do not become part of the numeric slot.
All new forms match the entire request. No arbitrary text or keyword substring
is stripped or searched to manufacture a valid action.

Conversational wrappers retain their original rules, with one explicit inert
suffix added: `right now`. The exact `help me` wrapper remains original; new
explanation forms consume `understand why …` themselves and require focus-domain
context. Three polite-prefix applications are inherited; a fourth repeated prefix
still refuses. Global `without` refusal remains, even for the seen phrase about
studying without distractions. A semicolon wake-up/set-alarm utterance also stays
refused. These are limitations, not silently changed labels or actions.

Development uses **previously seen** balanced train/development/confirmation-v2
wording, exclusively. The old confirmation is now development; no fresh natural
corpus was authored, inspected or queried by this task. The selected baseline is
an immutable Git snapshot at `1eb2fb55bf0322237bce0bc04942cb0d6652ddcc`; the number
parser stays unchanged. Candidate and baseline compile into separate classes.

Actual development verification:

- **59 targeted JUnit methods pass:** 16 new natural/slot/adversarial methods and
  43 existing gate/number-parser methods.
- All **226 known requests × seven intent routes = 1,582 routes** are compared.
- All **80 previously executable routes** preserve kind, hour, minute, seconds
  and preview exactly; zero accepted-route regressions.
- All **476 required-unknown route checks** refuse; zero accepted wrong intents
  on supported development wording.
- Known manual oracle complete coverage: train **68→96/96**, development
  **0→12/12**, old confirmation-v2 **12→48/50**; zero losses. These are parser-only,
  development-only observations, not model accuracy or a fresh test result.

`development-results.json` binds source, datasets, helper, dependency and raw
artifact hashes. Initial development artifacts and the earlier candidate snapshot
remain under ignored `build/`; final verification is in `build/final-development/`.
Raw requests/proposals stay ignored. No app, phone, permission, native library,
training adapter or release was changed. No inference was performed.

Repeat development with a new ignored output directory:

```sh
python3 prototype/qwen-natural-validation/run_development.py \
  --out prototype/qwen-natural-validation/build/review-development
```

The helper reads only its three explicitly checksummed, already-seen datasets. It
has no discovery step and cannot silently use future fresh natural data. It uses
existing JDK/JUnit/Hamcrest, creates exclusive output and executes only Java
validation/tests. Root must freeze candidate and helper identities before fresh
independent authoring/evaluation. No promotion or broad safety claim follows from
these development results.
