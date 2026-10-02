# Independent command validator evaluation

Pre-event synthetic research on the host CPU. This experiment executes no phone
actions and changes no model, prompt, adapter or training parameters. The same
unchanged Qwen3.5-0.8B Q4_0 JNI outputs were passed to separately compiled v0.7
and v0.8 Java validators, retaining each full original request.

The independent author froze 100 requests across 50 families at
2026-10-02T13:50:09.784611+00:00, before the candidate validator edit. Forty rows
expect supported actions and sixty require abstention. The implementer received
only counts and hashes before locking candidate sources; it must not inspect the
generator or request text before that lock. `freeze-manifest.json` records source,
protocol and data digests. The v0.7 source snapshot was retained in ignored
`build/v07-source/`. Exact overlap with the previous 58-case and 373-case texts
is zero; classes and common domain words necessarily recur.

Oracle intents deliberately use the closest domain intent for unsupported
in-domain requests. For example, the oracle can propose a tool while the original
request requires rejection. This measures the validator's ability to reject
unsupported intent proposals; it is not raw semantic intent accuracy. Supported
requests independently specify exact action kind and hour/minute/duration slots.
Unsupported requests must return UNKNOWN. Wrong accepted actions and wrong
accepted slots both fail, even when the resulting action would be benign.

One model capture is reused across both validator versions. The native runtime
uses the unchanged full Android prompt, context 1024, four CPU threads and no
tensor capture. The first request follows a model load; subsequent requests reuse
context with model state cleared. OS page cache, thermals and power are not
controlled, so these measurements cannot establish disk-cold or phone/NPU speed.
There is no candidate promotion from this synthetic comparison alone.

## Reproduce

Inspect the frozen protocol first. Do not change request labels, source, prompt or
parser from evaluation results and then report the same data as unseen. The
generator refuses to overwrite changed request files. Raw data, outputs, source
snapshots and compiled Java classes are ignored under `build/`.

```sh
python3 prototype/command-v08-eval/generate_data.py
mkdir -p prototype/command-v08-eval/build/v07-source
git show 6bd4841b170be0445470eff9977133bc2accc8f6:prototype/android/app/src/main/java/dev/focuspilot/prototype/ModelCommandGate.java > prototype/command-v08-eval/build/v07-source/ModelCommandGate.java
cp prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java prototype/command-v08-eval/build/LocalModel.java
python3 -m unittest discover -s prototype/command-v08-eval -p 'test_*.py' -v
python3 prototype/command-v08-eval/run_evaluation.py \
  --candidate-sha 54d1f3d71ff76c8b271c76a2fe1475e185f1f07370f4664d121a1e87a78cbc71 \
  --number-words-sha e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d
```

The runner requires the existing verified host JNI library, pinned local GGUF
and OpenJDK 17. It does not download or rebuild the native runtime. It refuses to
overwrite an existing model capture; `--score-only` reviews the existing capture
with already snapshotted sources. It records terminal exit status, input/output,
model, JNI, adapter and source hashes. The model process has a 300-second bound.
No API credits, private device history, permission grants or phone actions are
used. Reproducing these now-seen requests is not a new independent experiment.

## Actual frozen result

The implementer locked both sources before seeing requests. Candidate gate SHA
`54d1f3d71ff76c8b271c76a2fe1475e185f1f07370f4664d121a1e87a78cbc71`,
number-word helper SHA
`e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d`.
The native process completed once with exit 0 in 45.850 seconds. All 100 responses
met the intent JSON schema and reached EOS. Qwen correctly classified 29/40
supported requests; every one of the 60 unsupported requests received a
non-unknown model proposal. Overall raw semantic intent accuracy is therefore
29/100 (29%): the expected semantic intent for every unsupported request is
unknown, distinct from the adversarial oracle domain intent. This is reproducible
from aggregate counters as `supported_intent_correct + must_abstain_rows -
unsupported_model_nonunknown_proposals` = 29 + 60 - 60. The original-request validator is doing the rejection,
so schema success must not be described as understanding or safe autonomy.

| Exact original-request/slot result | Model + v0.7 | Model + v0.8 | Oracle + v0.7 | Oracle + v0.8 |
|---|---:|---:|---:|---:|
| Correct supported action/slots | 9/40 | 12/40 | 14/40 | 19/40 |
| Correct required abstentions | 55/60 | 60/60 | 54/60 | 60/60 |
| Correct action/slots or abstention | 64/100 | 72/100 | 68/100 | 79/100 |
| Supported false abstentions | 31/40 | 28/40 | 26/40 | 21/40 |
| Unsupported false accepts | 5/60 | 0/60 | 6/60 | 0/60 |
| Accepted proposals | 14/100 | 12/100 | 20/100 | 19/100 |
| Wrong accepted proposals | 5 | 0 | 6 | 0 |

Paired supported outcomes expose regressions behind the net gain: model-backed
v0.8 gained nine requests and lost six that v0.7 handled; the oracle comparison
gained twelve and lost seven. English integer focus durations, alarm times and
Clock launch phrasing improved. Valid polite comma suffixes, some focus/pause
wrappers, a colon-time alarm suffix and a Calculator application qualifier were
rejected by v0.8 despite v0.7 accepting them. The oracle also lost a valid timer
phrased with "lasting". No requests or validator rules were repaired after these
results. Raw paired details are in ignored `build/v07-*-results.json` and
`build/v08-*-results.json`; gains mean supported + current correct + previous
incorrect, losses mean supported + current incorrect + previous correct.

The v0.7 wrong accepts included a signed negative timer, omitted recurrence and
unsupported extra app/timer qualifiers. V0.8 rejected them on this set. The small
synthetic set does not prove universal rejection or production safety. Coverage
remains low: model-backed v0.8 handles 30% of the supported requests, versus
47.5% with oracle domain intents. This candidate is not promoted by this lab.

Host CPU timings: model load 451.08 ms, first native request 474.40 ms, subsequent
native median 455.39 ms, wall median 456.18 ms. These include unchanged Qwen
prefill and generation; capture was off. No OS-cache reset, phone timing, NPU or
execution outcome is claimed. Four evaluation tests pass. Storage added is about
628 KiB, with zero downloads or paid API calls. Frozen request, source and runtime
digests remain unchanged.

`results.json` contains aggregate/per-family evidence and actual provenance;
`experiment-metadata.json` records test and raw-result digests. Raw requests,
outputs and binaries stay ignored. No device actions ran.
