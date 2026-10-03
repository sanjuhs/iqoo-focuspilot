# Preserved initialization failure

The initial capture exits1 before model loading: the existing JNI accepts only
context 512–1024 and max128 new tokens, while this candidate requested 2048/256.
Zero request outputs were produced. [Failed aggregate](results.json) and the
source freeze remain unchanged. A separately frozen compatibility attempt is
recorded in [the study](../../docs/task-draft-v21.md). This directory is not retried.

# Isolated Qwen3.5 task-draft candidate

Pre-event source preparation, not eligible event-created competition code. The
selected Android app is unchanged. Previous task-draft candidates remain archived
and rejected; their universal refusal, nonsensical reading draft, omitted task
completion and no-reminders constraint failure motivate this separate candidate.
No successful model load or guidance result is established here.

The shared prompt requests one to five concise user instructions rather than
exactly three. It explicitly asks for preparation, the actual work and completion
or checking where needed. It forbids adding unrequested reminders/notifications,
claiming access or completed actions, and inventing missing details. Examples
cover reading plus its summary, a desk reset without notifications, expense-report
completion and explicit decline. These prompt instructions are hypotheses, not
semantic guarantees. JSON validity does not establish useful or obedient advice.

`reference/TaskDraft.java` is a pure Java source contract in the same package as
the archived `TaskPlan`/`LocalModel` adapters. Root owns dependency snapshots,
capture runner, prewritten corpus criteria, source freeze and later evaluation.
Do not edit historical files or selected app source to compile this candidate.

| Interface | Contract |
|---|---|
| `SYSTEM_PROMPT`, `GRAMMAR` | Shared fixed prompt and zero-or-one-to-five-string JSON grammar. |
| `validatedGoal(String)` | Preserve exact saved-goal identity; 1–120 UTF-16 units, nonblank single-line plain Unicode. |
| `renderPrompt(String)` | Quote the goal as untrusted JSON data, separate reserved chat markers, append the explicit no-thinking prefix. |
| `isDecline(String)` | Strictly parse the complete schema; true only for an empty steps array, throw for invalid text. |
| `parseOutput(String)` | Return `TaskPlan` with 1–5 valid steps and zero progress; decline and invalid text throw. |
| `MAX_NEW_TOKENS` | 256 total generation samples; actual EOS is separately required. |
| `CONTEXT_TOKENS`, `THREADS` | Planned 2048-token CPU context and four threads. |
| `MAX_OUTPUT_CHARS`, `GENERATED_STEP_CHAR_LIMIT` | 4096 encoded UTF-16 units; each decoded step at most 80 UTF-16 units. |

The archived `LocalModel` method names remain compatible, but its hardcoded
1024-context/128-token calls must not be mistaken for these new runtime settings.
Root's isolated runner should call `nativeInit(model, 2048, 4)`, then, once per
request, `nativePrepare(handle)` before
`nativeGenerate(handle, TaskDraft.renderPrompt(goal), TaskDraft.GRAMMAR, 256, false)`.
Use fresh recurrent/KV state, greedy decoding, no thinking/capture, fixed pinned
Qwen3.5-0.8B Q4_0 and the existing pinned host JNI. CPU timings cannot establish
phone latency or Snapdragon NPU use. Context and token changes also preclude a
like-for-like timing claim against the old candidates.

The parser consumes the entire JSON object, permits only the `steps` key and a
string array, checks count and decoded bounds, rejects malformed escapes,
unpaired surrogates, controls, line separators, Unicode format/bidi characters
and noncharacters, and rejects blank or duplicate steps. Duplicate comparison
uses NFKC, Unicode space collapse and root-locale lowercase. Stored advice remains
ordinary inert text; `TaskPlan` applies its existing trimming and progress bounds.
Grammar code-point/escape counts and Java decoded UTF-16 limits are independent,
so a grammar-valid string can still be rejected. Goal validation never truncates
or changes the identity used for later review.

No wording filter claims to determine semantic safety, constrain real-world tool
effects or prove compliance. Decline is not a zero-step plan. Drafts cannot read
the screen, execute steps, mark completion, send messages, transfer money or grant
permissions. Any future UI must separately bind the original goal/revision,
invalidate on edits/cancel/background, require actual EOS and strict parsing, then
use explicit review → editable draft → separate Save. No automatic promotion.

Before the first generation, root must freeze source/runtime/corpus and manually
written usefulness/constraint criteria, including the old failure families.
Preserve all raw outputs and failures outside Git. Independent content review is
separate from structural parser results; data from earlier experiments is already
seen development evidence, not fresh qualification. Model weights, credentials,
private captures and training data stay outside Git and within the 15 GB budget.
