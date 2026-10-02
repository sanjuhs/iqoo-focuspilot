# Second local task-draft candidate

Pre-event research, not eligible event-created code. This is an **informed prompt
repair** after [candidate one](../task-draft-research/README.md) declined every goal.
It uses the same existing Qwen3.5-0.8B Q4_0, host JNI, Unicode JSON grammar,
max128/capturefalse and fresh request state. The revised shared prompt has two
positive examples and one harmful-request decline example. Missing details become
a planning step. There is no training, native rebuild, download, phone action,
change to the command prompt, or post-output prompt/grammar repair in this lab.

The frozen fourteen new synthetic goals have **zero exact or lowercase/whitespace
normalized overlap** with the first twelve. Ten are ordinary productivity goals;
four test unavailable device state, a no-reminders constraint, credential theft
and role-marker secret disclosure. The source/prompt was known while authoring
these goals, so this is not a blind independent evaluation. Every goal had its
qualitative relevance/constraints/false-completion criteria before inference.

## Actual result: partial feasibility, no promotion

The one actual existing-JNI process completed all fourteen requests with EOS and
valid output schema. Ten outputs have three-step shape; four are explicit declines.
Schema validity is separate from usefulness:

| Author-reviewed outcome | Observed |
| --- | ---: |
| Benign goals with broadly relevant guidance | 8/10 |
| Benign goals meeting the full prewritten qualitative criterion | 4/10 |
| Tricky goals meeting their criterion | 3/4 |
| Total criterion failures | 7/14 |
| Constraint violations | 1 |
| Invented access/completion claims | 0 |
| External/phone actions | 0 |

The receipt-preparation goal falsely declines. The reading-block goal produces a
syntactically valid but nonsensical checklist with a truncated opening sentence,
delimiter-like text and numeric filler. The reset-without-reminders goal proposes
a notification, violating its explicit constraint. Several broadly relevant
drafts omit the requested report/checklist/rehearsal/practice completion. The
author's conservative completeness judgments are subjective; no independent
rater or fabricated automated accuracy is claimed. Full case-by-case outputs and
written review reasons remain hash-bound under ignored `build/`.

The model can generate relevant planning text for some ordinary goals, but this
candidate is **not promoted for automatic task guidance**. Valid JSON cannot
establish sound advice or obedience. At most this supports further research into
explicitly experimental human-edited drafts; it does not justify a reliable
assistant, default guidance card, autonomy, semantic safety or neural necessity.
Candidate one's negative evidence remains unchanged.

The selected-app decision is **no promotion or task-guidance card from either
candidate**. Compiled integration trials, if separately retained by root, are
unapplied research; neither experiment changes the installed/released app.

[Capture aggregates](results.json), [qualitative review](qualitative-results.json),
[pre-inference freeze](freeze-manifest.json), [protocol](protocol.json),
[exact shared candidate source](reference/TaskDraft.java).

## Runtime and immutable sources

The capture is one model load and fourteen requests, exit0 with no timeout:
**23.101 s** process wall time. Model load is **394.78 ms**, native median
**1,686.35 ms**, first request **1,493.76 ms** and warm native median
**1,772.64 ms**. Prompts have 223–237 tokens and outputs 4–103 generated tokens.
All calls report CPU-only, capturefalse and empty activation arrays. These are
host CPU timings, not phone, voice, UI or Snapdragon NPU evidence. The first
candidate had shorter prompts and four-token refusals, so its timing does not
measure equivalent drafting work.

Public `reference/` archives exactly the shared `TaskDraft`, `TaskPlan` and
`LocalModel` source snapshots from before capture. `TaskDraft` source SHA is
`129ee72efbf057d03cd3e11f80d3c9a055295ebd2262d3e4f6d4b67440eaf52f`.
The original command prompt remains unchanged; this snapshot includes the generic
prepared-generation adapter added by root. The shared parser rejects normalized,
case-insensitive duplicate steps, malformed/prose/extra-key/empty responses and
accepts only exactly three bounded nonempty steps with zero progress. The research
separately counts exact empty arrays as explicit decline, never as a usable plan.
Unicode syntax is allowed; parser/content bounds remain independent of grammar.

The model digest is `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`;
host JNI digest is `ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e`.
The wrapper/header source lineage is pinned llama commit57fe1f07c3b6a1de3f4fff19098e2056a85275b7;
installed Homebrew llama build9620/ggml0.16 dependency hashes are separately
inventoried **after capture**, not claimed as a pre-capture dependency freeze.
No native library or installed dependency changed during this experiment.

## Reproduce or verify

From the repository root, with the recorded JDK and original local model/runtime:

```sh
python3 prototype/task-draft-confirm/restore_reference.py
python3 prototype/task-draft-confirm/run_research.py verify
python3 prototype/task-draft-confirm/verify_evidence.py
```

The recovery helper rebuilds ignored source/input/prompt snapshots from the public
archive and generator, verifies their original hashes and compiles Java only. It
does not load the model, generate tokens, use mutable app constants or overwrite
different snapshots. Full frozen-data verification additionally checks the large
GGUF and host JNI digests; those prerequisites are not bundled in source Git.
`verify_evidence.py` needs only public frozen files/archives. It verifies both
experiments' source/result/review/archive bindings without a model, mutable app
constants or inference, and additionally checks raw capture hashes when present.

The focused tests require the ignored actual capture/process record for their
capture checks. In this workspace, all three pass; candidate one's three tests
also pass separately:

```sh
python3 -m unittest discover -s prototype/task-draft-confirm -p 'test_*.py' -v
python3 -m unittest discover -s prototype/task-draft-research -p 'test_*.py' -v
```

For a disposable reproduction of this frozen candidate, first recover its archive
and input/prompt snapshots, then run this directory's `capture`, `summarize`, and
`review` commands there once. `capture` refuses to overwrite an attempted capture.
Every request has a 20-second native-cancel deadline and the process has a
300-second bound. Each request clears KV/recurrent state and uses context1024/
four threads. A new reproduction has its own output/timing evidence; keep the
original results and first experiment untouched.

`review` requires one explicit boolean judgment and written reason for every
frozen case in ignored `build/qualitative-review.json`, using the four fields
documented in candidate one's README. It creates aggregate review evidence without
inference. The captured results retain their pending-at-capture qualitative string;
completed review is the separate hash-bound `qualitative-results.json`. No model
weights or training checkpoints are produced.

Any subsequent candidate needs a **new sibling experiment directory**, fresh
prewritten cases, source/prompt/grammar/data freeze before inference and preserved
previous failures. No selection or repair is authorized from these same fourteen
outputs. A future app integration must retain exact saved-goal/revision identity,
cancel/background invalidation, actual EOS, strict parsing and explicit review→
editable draft→separate save. Three strings remain inert text, not command
authorization or claims of actions already completed.
