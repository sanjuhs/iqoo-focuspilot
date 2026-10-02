# Local task planning — evaluated, not promoted

Prepared 2 October 2026. The selected and installed app remains **research v0.11**
with user-authored task steps and unchanged Qwen3.5-0.8B Q4_0 command understanding.
No automatic task planner has been added. Two real host-JNI experiments test the
same pinned model and native runtime with separate planning prompts, no thinking,
greedy sampling, context 1024, four threads, maximum 128 new tokens and capture off.
Neither experiment trains or fine-tunes the model, operates a phone or executes a task.

| Candidate | Frozen sample | Real EOS / JSON shape | Useful guidance evidence | Decision |
| --- | --- | --- | --- | --- |
| First conservative prompt | Eight benign + four tricky goals | 12/12; all empty declines | 0/8 benign goals served; nine total criterion failures | Reject |
| Example-based repair | Ten fresh benign + four fresh tricky goals | 14/14; ten three-step shapes, four declines | 8/10 benign outputs broadly relevant, **4/10** meet all written criteria; seven total criterion failures | Reject for promotion |

The repaired prompt includes concrete examples and asks the model to collect
missing details instead of declining ordinary tasks. Its sample has no exact or
normalized overlap with the first sample. The same informed author wrote and
reviewed synthetic criteria; this is not a blind independent or real-user study.
The second run contains a syntactically valid nonsensical reading draft and a
notification suggestion despite a no-reminders constraint. Other outputs omit
requested preparation/completion components; receipt preparation falsely declines.
There were no observed access/completion claims, but that does not establish
semantic correctness or safety.

The first host run completed in 4.253 seconds and emitted only four tokens per
request; the second completed in 23.101 seconds, with 4–103 generated tokens and
warm native median 1,772.64 ms. Different prompt/output lengths make these unsuitable
as a same-work latency comparison. Neither is a phone benchmark or NPU result.

[First capture and archived sources](../prototype/task-draft-research/README.md),
[fresh repair capture and author review](../prototype/task-draft-confirm/README.md),
[final public evidence bindings](../prototype/task-draft-confirm/evidence-manifest.json).
Six research tests pass. A no-model verifier checks archived source/result/review
bindings and available ignored raw capture hashes:

```sh
python3 prototype/task-draft-confirm/verify_evidence.py
python3 -m unittest discover -s prototype/task-draft-research -p 'test_*.py' -v
python3 -m unittest discover -s prototype/task-draft-confirm -p 'test_*.py' -v
```

## Integration preserved, selected app unchanged

The [unapplied UI patch](../prototype/task-draft-ui/README.md) implements an explicit
saved-goal request, bounded strict draft parser, private nonce/revision/editor
checks and two separate reviews before placing suggestions in the editable guide.
Save remains separate; no focus, virtual balance, speech, external task or model
fine-tuning occurs from import. Its source compiled with **156 JVM tests passing**
and lint zero errors/76 warnings. The signed light candidate passed SDK version,
native, license and permission inspection, but was never installed or released.
Source review and compilation do not prove Android lifecycle/import outcomes.

The integration was removed from the selected Android worktree after the quality
result. The restored v0.11 source rebuild passes **143 JVM tests**, lint zero
errors/65 warnings; existing installed/published APKs and model/native identities
are unchanged. A better prompt or trained planning model needs a new frozen
evaluation with constraint and nonsense failures retained, before this scaffold is
applied. Physical phone guidance, iQOO/NPU, Office Kit and eligible accepted
submission remain unfinished. [Full remaining scope](remaining-deliverables.md).
