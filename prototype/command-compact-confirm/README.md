# Compact intent output — measured, rejected research

Prepared 3 October 2026. **The compact candidate is rejected for deployment.**
The selected phone app retains its original command prompt, gate, native runtime
and Qwen3.5-0.8B Q4_0 weights. This is pre-event host research; no phone action,
training, permission change, APK change or release promotion occurred.

Two real 100-request CPU/JNI captures completed with exit 0 from pre-capture
source `c0c7e898fcacf9cc93b6e1fb375d64e997bac7bb`. One-digit output improved timer
coverage and raw unknown classification, but lost both previously accepted Pause
requests and a supported focus duration. It also lost three prospectively tagged
hard semantic cases. Its larger prompt outweighed cheaper decoding: no host
latency improvement was observed.

## What was frozen

The [prospective protocol](PROTOCOL.md) and [machine-readable protocol](protocol.json)
were written before the author inspected the selected candidate or wrote requests.
The parent locked one development-selected candidate at
`2026-10-02T20:45:46.855733+00:00`; the corpus was authored at 20:49:11 UTC and
the final [freeze manifest](freeze-manifest.json) was written at 20:51:21 UTC.
Actual baseline/candidate captures started at 20:52:20/20:53:05 UTC and took
45.045/47.171 seconds. Both were terminal before outcome disclosure.

The baseline uses current `LocalModel.renderPrompt`, the existing JSON intent
grammar and 128-token ceiling. The locked candidate uses a longer system prompt,
15 examples, one ASCII classification digit and a four-token ceiling. Digits map
to the same seven semantic labels: unknown, start_focus, pause_focus, alarm,
timer, open_app and explain. Strict digit/JSON validation requires native EOS;
malformed/truncated output would fail semantic scoring and separately abstain at
the gate. Both actual captures had 100/100 valid format plus EOS.

Both arms use the same pinned model, actual host native library, context 1,024,
four CPU threads and activation capture disabled. Native recurrent/KV state is
cleared for each request. The complete original utterance and validated model
intent enter the same actual compiled current Java `ModelCommandGate` and
`CommandNumberWords`. The exact expected kind, hour, minute and seconds must all
match. Accepted proposals execute nothing. A separately authored oracle domain
route diagnoses the unchanged gate's coverage and refusal.

The model SHA is
`57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.
This confirmation uses host native SHA
`ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e`.
The preceding seen-development selection used a **different** host native
artifact, `2e9fa6676c4d68d0b4119cf13d8176d4d6674939c9361c48883c15cfad2cb156`;
its timings must not be merged with this comparison. Neither artifact establishes
phone or NPU performance.

## Corpus and its limits

The [corpus manifest](corpus-manifest.json) fixes 100 English synthetic requests
in 50 two-row families: 50 supported commands and 50 required unknowns. Supported
intent counts are 10 Start, 8 Pause, 8 Alarm, 10 Timer, 6 approved opens and
8 explanations. Each Settings/Calculator/Clock target has two requests. Twenty-five
supported rows carry prospective hard tags for boundaries, spoken slots,
midnight/noon, resume wording, current-session Pause and warned-focus explanation.

Exact and normalized overlap are zero across 16 pinned inventories: 1,027 texts
including duplicates, 800 unique exact texts and 798 normalized texts. Inventories
include earlier 58/373/v0.8/v0.10/confirmation corpora, all known v0.10/compact
development request fixtures, three existing rendered prompt inventories and
the selected candidate's actual examples. Normalization lowercases, replaces
non-ASCII-alphanumeric runs with spaces and collapses whitespace; it does not
normalize number words, meanings or paraphrase families.

The author knows earlier results and inspected the locked prompt/examples before
authoring. These are fresh synthetic words after selection, **not human-blind,
independently sampled user language or ASR transcripts**. Requests and expected
slots were frozen before capture; no rows or labels were changed after outcomes.
The parent received counts/hashes, not request text, before both captures were
terminal. That separation does not make this author independent. Common domain
vocabulary and known difficult wording remain intentionally represented.

## Actual results

| Measure | Current JSON prompt | Locked digit candidate |
| --- | ---: | ---: |
| Raw semantic correctness | 36/100 | 44/100 |
| Supported intent correctness | 35/50 | 35/50 |
| Required unknown correctly classified | 1/50 | 9/50 |
| Unsupported non-unknown model proposals | 49/50 | 41/50 |
| Format plus EOS valid | 100/100 | 100/100 |
| Exact supported gate proposals | 30/50 | 32/50 |
| Supported false abstentions | 20/50 | 18/50 |
| Correct gate abstentions on unsupported rows | 50/50 | 50/50 |
| Exact action/slots or required abstention | 80/100 | 82/100 |
| Wrong accepted kinds/slots | 0 | 0 |

All accepted proposals are correct on this authored set; that observation does
not establish universal safety. The model still incorrectly proposes a non-unknown
intent for most unsupported requests. Independent validation supplies rejection.
Formatting success must not be described as semantic understanding or task success.

| Supported intent | Rows | Current exact gate | Candidate exact gate |
| --- | ---: | ---: | ---: |
| Start/resume focus | 10 | 10 | 9 |
| Pause focus | 8 | 2 | **0** |
| Alarm | 8 | 7 | 7 |
| Timer | 10 | 4 | 9 |
| Approved app open | 6 | 6 | 6 |
| Explain focus/nudge | 8 | 1 | 1 |

There are **five supported gate gains and three losses**: all gains are timers;
losses are one spoken focus duration and two Pause requests. Supported semantic
scoring likewise has five gains and five losses: the same three gate losses plus
two warned-focus explanations that the current gate already rejects. Per-tag
accounting retains one spoken-slot semantic/gate loss and two warned-focus
semantic losses. These losses violate the prospective hard-case criterion and
reduce per-intent Start/Pause coverage. A net gain of two accepted requests does
not justify deploying this candidate.

The oracle route proposes 43/50 supported exact commands and rejects all
50 unsupported requests, with zero wrong accepts. Seven oracle false abstentions
retain existing wording limitations: two current-session Pause forms, one timer
wrapper and four explanation forms. Oracle failure is not a model misclassification;
these rows remain in the denominator. Better model classification alone cannot
remove this independent gate ceiling. No concrete authored slot/label mismatch
or scoring discrepancy was found in the post-terminal review.

## Descriptive host costs

Hardware is Apple M4 Pro; these are sequential baseline-first host CPU
observations, with separate model loads and unflushed OS caches. Thermals, power
and scheduling are uncontrolled. No cold-cache, phone, NPU, battery, activation
overhead or complete app/action speedup claim follows.

| Metric | Current JSON prompt | Locked digit candidate |
| --- | ---: | ---: |
| Model load | 367.36 ms | 372.49 ms |
| First native request | 463.19 ms | 465.49 ms |
| Subsequent native median, 99 rows | 448.70 ms | 465.74 ms |
| Subsequent nearest-rank p95, 99 rows | 465.38 ms | 480.21 ms |
| Prefill median, 100 rows | 287.61 ms | 430.60 ms |
| Decode median, 100 rows | 165.93 ms | 35.21 ms |
| Java request wall median, 100 rows | 449.46 ms | 466.52 ms |
| Prompt-token median, 100 rows | 164 | 253 |
| Generated-token median, 100 rows | 8 | 1 |

Every request adds 89 candidate prompt tokens. The paired candidate-minus-baseline
native total median is **+21.03 ms** across 100 rows; this differs from subtracting
the two separate medians. A one-token answer reduces decoding but increases
prefill here. All reported distributions have their full sample count and no
missing/nonfinite metrics; ranges and p95 are preserved in [results](results.json).

## Evidence and repeat procedure

[Evidence manifest](evidence-manifest.json) binds the public protocol/selection/
source/test/result files, private corpus/capture/metadata/log/gate-detail hashes,
actual model/native artifacts, pre-capture source revision and independent
post-terminal verification. It contains no utterances or raw model text. Raw
requests, generated text, compiled classes and detailed transitions remain in
Git-ignored `build/` directories. Public generator source can reproduce the
synthetic requests; generated raw data is not committed.

Twenty checks pass: eight corpus/label/overlap/immutability tests and twelve
strict-output, completeness, slot, structural, hard-regression and missing-metric
scoring tests. A separate post-terminal read-only review checked every frozen
source/overlap hash, raw capture exit/hash/ID/format, every expected tuple and
paired hard-tag transition against the actual aggregates. No new inference ran
during that review. The frozen source, corpus and results remain unchanged.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s prototype/command-compact-confirm -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s prototype/command-compact-runner -p 'test_*.py' -v
```

The corpus-overlap test requires the pinned ignored prior inventories. A public
checkout omits those files and the original raw captures. Reconstruct prior
synthetic inventories from their tracked generators and rendered prompt
inventory tools in a **separate scratch checkout**; see the
[earlier confirmation reproduction](../command-v10-confirm/README.md). Preserve
the original evidence directory. The following commands require those inventories,
the exact pinned GGUF/native artifact, full Git history for the selected app
revision and OpenJDK 17:

```sh
python3 prototype/command-compact-confirm/generate_data.py
PYTHONPATH=scripts python3 prototype/command-compact-runner/run_evaluation.py
```

Use the already tracked freeze manifest; the initial `--freeze-reviewed-runner`
command refuses an existing freeze and is not a reproduction step. The runner
refuses existing captures, and its `--score-only`
mode also refuses overwriting existing transition/result artifacts; it is not a
non-mutating verification command for this completed directory. Repeated now-seen
requests are reproduction, not another fresh confirmation. Rebuilt native bytes
or a different toolchain require separate provenance rather than claiming the
original artifact identity or timings. A next candidate must have a new locked
protocol and newly authored held-out families.

The full assistant goal remains active. This negative command experiment does
not establish ASR, monitoring, arbitrary phone control, disconnected operation,
iQOO/NPU, Office Kit, causal interpretation, eligible event code or accepted
submission. It preserves Qwen3.5 as the user-selected model and the working
reviewed command baseline while recording why this particular change was rejected.
