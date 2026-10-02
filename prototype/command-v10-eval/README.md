# Blind v0.10 prompt and validator evaluation

This is pre-event synthetic research on the host CPU. It runs the same pinned
Qwen3.5-0.8B Q4_0 and existing verified JNI library with two frozen Java prompt
adapters and two original-request validators. No model parameters, native
runtime, phone permissions or phone actions are changed by this lab.

The independent author fixed 100 requests in 50 whole wording families before
candidate development at 2026-10-02T14:47:23.734651+00:00. Fifty expect supported
actions with independently authored exact slots; fifty require abstention. All
exact request text differs from the earlier 58, 373 and v0.8 100-case sets. Domain
words, semantic classes and allowed apps necessarily recur. Root received only
counts/hashes and must not inspect the generator/text before candidate source
lock. `freeze-manifest.json` binds generator, protocol, request and baseline
source bytes. Raw requests, logs, captures, snapshots and binaries are ignored
under `build/`; tracked source and aggregate evidence can reproduce them.

Two different labels serve distinct purposes. **Semantic intent** is unknown
for every unsupported original request. **Oracle domain intent** can still
propose a plausible tool for an unsupported in-domain request, deliberately
testing whether the independent validator rejects it. Oracle coverage is not
model accuracy. Each supported action must match kind, hour, minute and seconds
exactly. A right kind with wrong time/duration is a wrong accepted proposal.

The native model is loaded separately for baseline and candidate captures in a
fixed baseline-then-candidate order. Both use context 1024, four CPU threads,
grammar-bounded intent JSON and capture off. The model context is reused with
state cleared for each request. Timing includes model prefill and generation;
the first request follows a load but OS cache, thermals and power are uncontrolled.
These are host CPU measurements, not phone/NPU or disk-cold evidence.

The primary end-to-end comparison pairs each version's generated intents with
its own validator, so it changes both prompt and gate. Semantic model accuracy
separately describes prompt behavior. The oracle comparison isolates validator
coverage/rejection. Paired gains and losses expose regressions hidden by net
accuracy. No test-derived repair, prompt choice or promotion is part of the
frozen experiment, and no small synthetic set can establish universal safety.

## Reproduce

Inspect `protocol.json` and preserve any existing captures first. Re-running
these now-seen requests is not a new blind evaluation. The generator refuses to
overwrite changed requests, the runner requires locked source hashes, and an
existing model capture cannot be overwritten.

The current app has restored the historical adapter
`2f6784c524ca9304fd714b86c04f5b1c3c5deb7e5ff562fbc34ae32c39e51e5d`
and retains the expanded gate. This frozen experiment instead captured the
**rejected round2 adapter** `2152a4f73579d4d3ceabbec219e6bfbd6973ab0c659706b554c26e84bf0a6329`.
Running a fresh original experiment against the current app sources would fail
the adapter hash lock. Do not change that lock to make the current app pass.

With the original ignored captures and snapshots still present, recompute scores
without inference using their exact original source identities:

```sh
python3 prototype/command-v10-eval/run_evaluation.py --score-only \
  --candidate-gate-sha cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4 \
  --candidate-numbers-sha e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d \
  --candidate-adapter-sha 2152a4f73579d4d3ceabbec219e6bfbd6973ab0c659706b554c26e84bf0a6329
```

For a fresh replay, use an **isolated scratch checkout**, preserving the working
app's restored prompt. `FINAL_GATE_COMMIT` below means a saved repository commit
containing the archived round2 adapter and the gate/parser whose exact hashes are
passed below. Existing model/native files are read from the original checkout;
this recipe downloads and rebuilds nothing. Use a new scratch directory with no
prior evaluation captures, and do not replace the original evidence.

```sh
ORIGINAL_ROOT="$(pwd)"
REPLAY_ROOT="/tmp/focuspilot-v10-replay"
git worktree add --detach "$REPLAY_ROOT" FINAL_GATE_COMMIT
mkdir -p "$REPLAY_ROOT/models" "$REPLAY_ROOT/prototype/native/build"
ln -s "$ORIGINAL_ROOT/models/qwen" "$REPLAY_ROOT/models/qwen"
ln -s "$ORIGINAL_ROOT/prototype/native/build/host" "$REPLAY_ROOT/prototype/native/build/host"
cd "$REPLAY_ROOT"
cp prototype/command-v10-dev/candidates/round2/LocalModel.java prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java
python3 prototype/command-v10-eval/generate_data.py
python3 -m unittest discover -s prototype/command-v10-eval -p 'test_*.py' -v
python3 prototype/command-v10-eval/run_evaluation.py \
  --candidate-gate-sha cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4 \
  --candidate-numbers-sha e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d \
  --candidate-adapter-sha 2152a4f73579d4d3ceabbec219e6bfbd6973ab0c659706b554c26e84bf0a6329
```

The runner validates these locked hashes before capture; the restored deployed
adapter must not substitute for the archived one. Preserve the scratch replay's
metadata separately and return to the original checkout afterward. Since the
prompt replacement occurs only in the scratch checkout, no restoration of the
working app is needed. A replay of these disclosed requests remains seen data,
not a new blind confirmation. The later gate-only selection and its separate
confirmation are different experiments, with the historical prompt restored.

The runner uses existing OpenJDK 17, the verified host JNI library and local
GGUF; it downloads nothing. Each subprocess has a 300-second bound and records
actual terminal status/input/output/source/runtime hashes. It captures baseline
and candidate once each, compiles both actual Java gates, passes full original
requests and records exact proposal slots. `--score-only` reviews the completed
captures with already snapshotted sources without new inference. Six tests cover
semantic/oracle label separation, wrong slots, abstention, output completeness
and paired regression accounting.

## Actual frozen result

The candidate sources were locked before any capture or disclosure of requests:

- LocalModel adapter `2152a4f73579d4d3ceabbec219e6bfbd6973ab0c659706b554c26e84bf0a6329`.
- Original-request gate `cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4`.
- Number-word parser `e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d`.

A Java helper rendered each immutable adapter with a unique marker, without
constructing a model or generating tokens. The baseline contained eight fixed
prose examples; candidate contained thirteen fixed user/assistant chat examples.
**Exact request overlap is 0/100 for both**, also zero after case/whitespace
normalization. All 100 rows stayed unchanged. The inventory method, actual prompt
hashes and helper-source hash are recorded; raw inventories remain ignored.

| Semantic model result | Baseline v0.9 | Candidate v0.10 |
|---|---:|---:|
| Overall correct intent | 37/100 | 58/100 |
| Supported intent correct | 37/50 | 30/50 |
| Unsupported correctly unknown | 0/50 | 28/50 |
| Unsupported non-unknown proposals | 50/50 | 22/50 |
| JSON schema + EOS valid | 100/100 | 100/100 |
| Start-focus correct | 10/10 | 9/10 |
| Pause-focus correct | 4/4 | 1/4 |
| Alarm correct | 7/8 | 7/8 |
| Timer correct | 4/10 | 4/10 |
| Approved-app intent correct | 11/12 | 5/12 |
| Focus explanation correct | 1/6 | 4/6 |

The overall semantic improvement comes from unsupported-request abstention and
explanation accuracy; **supported classification declined**, especially app
launches and pauses. The model still makes a non-unknown proposal on 22/50
unsupported requests. Schema compliance is not semantic reliability.

| Exact original-request action/slots | Model + v0.9 | Model + v0.10 | Oracle + v0.9 | Oracle + v0.10 |
|---|---:|---:|---:|---:|
| Correct supported actions/slots | 11/50 | 28/50 | 20/50 | 48/50 |
| Supported false abstentions | 39/50 | 22/50 | 30/50 | 2/50 |
| Correct required abstentions | 50/50 | 50/50 | 50/50 | 50/50 |
| Correct action/slots or abstention | 61/100 | 78/100 | 70/100 | 98/100 |
| Wrong accepted proposals | 0 | 0 | 0 | 0 |
| Wrong accepted supported slots | 0 | 0 | 0 | 0 |
| Accepted proposals | 11/100 | 28/100 | 20/100 | 48/100 |

The end-to-end candidate gained twenty supported cases and lost three that the
baseline handled, net +17. Loss families were a spoken alarm, a friendly pause
wrapper and a Settings wrapper. The oracle validator gained twenty-eight and
lost zero; its two remaining failures were a request to end the current focus
session and an explanation of why Mira warned during focus. Semantic predictions
gained 34 cases and lost 13, net +21. These paired counters are generated directly
by the runner. No failed text, model prompt, label or parser was repaired after
seeing the holdout.

The broad validator substantially improves coverage, but the model remains the
bottleneck: oracle coverage is 96% of supported cases while model-backed coverage
is 56%. Zero observed wrong accepted proposals on this small invented set does
not prove safety or real-world reliability. Phone permissions, explicit
confirmation and execution/postcondition proof remain separate. This lab does
not promote the candidate.

| Host CPU cost | Baseline v0.9 | Candidate v0.10 |
|---|---:|---:|
| Capture wall time, 100 requests | 45.287 s | 99.079 s |
| Model load | 380.06 ms | 377.86 ms |
| First native request | 461.93 ms | 1030.27 ms |
| Subsequent native median | 449.03 ms | 984.73 ms |
| Request wall median | 449.85 ms | 986.25 ms |
| Median prompt tokens | 162 | 471 |
| Prompt token range | 159–172 | 468–481 |

The candidate prompt has about 2.9 times as many input tokens and measured native
median latency is about 2.19 times the baseline. Each process completed once with
exit 0. The fixed order and uncontrolled host caches/thermals limit attribution;
no statistical device speedup or phone/NPU claim follows. Six tests pass. No
models/dependencies were downloaded, no API credits spent, and no phone actions
executed.

`results.json` contains aggregate/per-class/per-family/paired counts, prompt
inventories and actual provenance. `experiment-metadata.json` binds sources and
raw result hashes. Raw captures and snapshots are ignored; frozen generator,
protocol, request, runner, adapter and gate bytes remain unchanged.


## Explicitly post-hoc separation of prompt and gate

After the primary results, root requested a **post-hoc** 2×2 comparison using the
same locked generated outputs and actual locked validators. This generated zero
new model tokens, changed no sources/data and preserved `results.json` byte for
byte. `posthoc_compare.py` and `posthoc-results.json` separately record the
analysis, original result hash and selection boundary.

| Correct supported action/slots | Old v0.9 gate | New locked gate |
|---|---:|---:|
| Old v0.9 prompt output | 11/50 | **35/50** |
| New candidate prompt output | 13/50 | 28/50 |

All four combinations correctly rejected 50/50 unsupported requests, with zero
wrong accepted proposals or wrong accepted slots observed. Gate-only expansion
with old prompt output gained 24 supported cases and lost zero; false abstentions
fell from 39/50 to 15/50. Prompt-only changes under the old gate gained five and
lost three. Under the new gate, the new prompt gained six but lost thirteen,
net −7 compared with the old prompt.

**The longer prompt candidate is rejected:** it regresses supported semantics
and costs about 2.19× measured host latency, while the old prompt plus expanded
gate yields better supported coverage here. The gate-only route is a candidate
chosen from already-seen post-hoc evidence, not an independently confirmed or
promoted outcome. Root requires a separately authored/frozen blind set before
its deployment. Existing old-prompt timing can describe reused model capture;
no new timing claim follows from this Java-only crossing.

To reproduce the post-hoc analysis from retained frozen captures/snapshots:

```sh
python3 prototype/command-v10-eval/posthoc_compare.py
```

No parser/prompt repairs or additional model inference occur in that command.
