# Qwen task-guidance research — rejected candidate

Qwen3.5-0.8B Q4_0 remains selected for the app. This separate planning experiment
does **not** add model-generated guidance to Mira. The installed and published app
remains v20; task checklists remain user-authored.

The new candidate permits one to five concise steps instead of forcing three.
Its prompt asks for preparation, actual work and completion, respects exclusions,
and collects missing details. The 32 synthetic goals and semantic criteria were
written before inference, informed by earlier failures. They have no normalized
goal overlap with the two older studies. This is not blind or real-user validation.

## Preserved initialization failure and separate repair

The [initial attempt](../prototype/task-draft-v21/results.json) exits 1 in 0.046 s
because its requested 2048 context exceeds the existing JNI's 512–1024 bound.
The constructor refuses before model loading; there are zero request outputs.
Read-only source inspection also finds the existing 128-token generation limit.
The failure, source and pre-capture freeze remain unchanged.

A [separate compatibility attempt](../prototype/task-draft-v21-compatible/runtime-compatibility.json)
uses context1024/max128, the same model/native library and the exact same untested
cases, prompt, grammar and parser. Runtime constants and strict boolean scoring
are the only candidate/scorer changes. No outputs informed prompt or case repair.
Its own source, rendered prompts, criteria, installed native dependencies and
30-second request / 600-second child limits were frozen before capture.

## Actual compatible capture and quality decision

| Evidence | Observed |
| --- | ---: |
| Requests completed with actual EOS and strict schema | 32/32 |
| Valid plan shapes / explicit declines | 30 / 2 |
| Benign full semantic criteria | **0/20** (7 broadly relevant) |
| Constraint full semantic criteria | **2/8** |
| Tricky full semantic criteria | **2/4** |
| Exact copies of the reading example | **22/32** |
| Observed harmful guidance / invented access or completion | 0 / 0 |
| Executed phone or external actions | 0 |

Two informed qualitative reviewers agree on all five recorded judgment fields
for every case. Relevance alone does not satisfy the prewritten preparation/work/
completion criteria. The paper-only revision and brief-before-outline cases pass;
both credential-related requests explicitly decline. Several partially relevant
plans omit needed practice, checks or finishing work. The tablet output tells the
user to check the screen but does not request supplied context or give a grounded
next step. User-directed instructions are not falsely labelled assistant actions.

The predeclared gate requires at least 16/20 benign, all 8 constraints and all 4 tricky
cases, all 32 EOS/schema, and zero false access/completion or harmful claims. It
fails. **No app promotion, planner card or automatic import is justified.**
Grammar/parser success and lack of observed harmful output do not prove semantic
accuracy, general safety or useful guidance.

One CPU-only host process exits0 without timeout in **53.905 s**. Model load is
416.824 ms; native generation median 1690.166 ms (range 929.605–2165.047 ms), prefill
median 841.378 ms and decode median 848.509 ms. Prompts contain 435–446 tokens and
outputs 4–35 tokens, all reaching EOS below 128. Activations stay disabled/empty.
These are laptop measurements, not phone, NPU or a like-for-like speed comparison
with shorter previous prompts. No training, new weights or native build occurred.
The effective project plus known new cache growth stays below 10 GB; the freeze
reserves 32 MB and checks the strict 15 GB ceiling.

## Reproducible records

- [Prospective protocol](../prototype/task-draft-v21-compatible/protocol.json) and
  [source/data/runtime freeze](../prototype/task-draft-v21-compatible/freeze-manifest.json).
- [Capture aggregate](../prototype/task-draft-v21-compatible/results.json),
  [criterion author's review](../prototype/task-draft-v21-compatible/author-review.json),
  [root review with actual synthetic steps](../prototype/task-draft-v21-compatible/root-review.json),
  [qualification and bindings](../prototype/task-draft-v21-compatible/qualification.json).
- 27 parser/goal rejection and identity checks pass before capture. They cover
  structure and Unicode/role boundaries, not semantic guidance or Android lifecycle.
- The source-only verifier passes against both preserved attempts, public review
  bindings and the available ignored raw outputs. It executes no model or phone:

```sh
python3 prototype/task-draft-v21-compatible/verify_evidence.py
```

Raw transport/stderr/details remain ignored under each `build/`. Public synthetic
evaluation cases and reviewed steps contain no phone/account data and are not
training data. Source freezes are immutable; runners refuse overwrite/retry.
The existing live command prompt, model, installed app, voice/monitoring controls,
virtual balance and permissions remain unchanged. Physical current workflows,
iQOO/NPU, Office Kit and eligible accepted submission remain required.

[Final audit](task-draft-v21-audit.json) verifies the preserved source/result/review
bindings and available raw capture. Read-only checks still find authorized USB,
v20 installed, the phone locked/off and microphone/notification grants absent.
An additional source/evidence reviewer finds no current record mismatch. This
does not verify the current physical app workflows.
