# Seven-parameter policy baselines

Pre-event research, 2 October 2026; not an eligible event-created submission.
These local standard-library experiments fit
two logistic policies to the existing invented teacher. They do not update Qwen,
the Android app, the reference neural policy or any real user model. The holdout
was already reported; this is an informed comparison, not a new blind benchmark.

Both signed and nonnegative-projected logistic models score **469/480** with
6 false negatives and 5 false positives. The unchanged 65-parameter network
scores **472/480**, the original simple rule 379/480, training-majority 226/480,
and the known label-generating teacher 480/480 by definition. The logistic
variants make identical holdout decisions; signed training learns positive final
coefficients without imposing that constraint. See [measured results](results.json)
and [interpretation](../../docs/policy-baselines.md).

## Verify without fitting

From the repository root, with Python 3 and no added dependencies:

```sh
python3 -m unittest discover -s prototype/policy-baselines -p 'test_*.py' -v
python3 prototype/policy-baselines/experiment.py verify
```

Verification checks pinned reference bytes before importing its generator,
regenerates the 640/320/480 family splits, reconstructs the seven-parameter models
from the reported coefficients, verifies parameter hashes, and reproduces every
train/dev/holdout metric. Present ignored artifacts are hash-checked; their absence
on a public checkout does not prevent aggregate metric verification. Neither
command refits models or changes the frozen results.

## Reproduce fitting in a disposable checkout

The experiment refuses to overwrite an existing freeze or result. In a **separate
disposable checkout**, remove only this experiment's saved reporting files, then:

```sh
rm prototype/policy-baselines/protocol.json prototype/policy-baselines/results.json prototype/policy-baselines/run-manifest.json
python3 prototype/policy-baselines/experiment.py freeze
python3 prototype/policy-baselines/experiment.py run
python3 prototype/policy-baselines/experiment.py verify
```

The newly frozen protocol records source/reference/data hashes before fitting.
It keeps all six raw inputs, zero initialization, seed 20261002, 140 epochs,
per-example SGD at `0.02 / sqrt(1 + epoch/25)`, and no regularization or feature
transformations. Only training rows update weights. Development BCE selects the
epoch, including epoch zero; development accuracy selects a threshold over
0.10–0.90 in steps of .01, preferring proximity to .5 and then the smaller value
on ties. Holdout cannot be passed to `fit`. Both candidates are reported, without
choosing a winner on holdout. Expect identical coefficients and accuracy on the
recorded Python arithmetic; timestamps, provenance of the disposable checkout,
wall time and microbenchmark timings will differ.

The original run's freeze has a recorded **pre-fit correction**: a focused test
caught use of `decision` instead of the pinned gate's `recommendation` field.
The superseded protocol was retained under ignored `build/` and replaced before
experiment training. No budget, labels, split, optimizer or metric choice changed.

The run creates ignored `build/procedural-rows.json`, two tiny checkpoints and
`counterexamples.json`. The latter saves the first five wrong holdout rows per
logistic candidate in fixed dataset order, with full synthetic vectors, teacher
interaction and exact signed logit contributions. These are not committed.
`results.json` retains their IDs/hashes and all paired correctness counts.

To inspect a counterexample from a public checkout without training or captures:

```sh
python3 - <<'PY'
import importlib.util, json
from pathlib import Path
p = Path('prototype/policy-baselines')
s = importlib.util.spec_from_file_location('baseline', p / 'experiment.py')
e = importlib.util.module_from_spec(s); s.loader.exec_module(e)
policy, _, _, splits = e.load_reference()
r = json.loads((p / 'results.json').read_text())
row = splits['holdout'][33]  # frozen holdout-0033, first wrong example
for name in ('signed_logistic', 'projected_logistic'):
    c = r['coefficients'][name]
    model = e.Logistic(policy, [c['features'][f] for f in policy.FEATURES], c['bias'], name == 'projected_logistic')
    print(name, 'label', row.label, 'threshold', r['thresholds'][name], model.explain(row.features))
PY
```

Three focused tests cover reference/split tampering, train/dev-only deterministic
selection, and signed contribution arithmetic/projection/external vetoes. Thirty
Python gate checks block all six policies before scoring. These are not Android
permission/lifecycle tests. Five warm passes measure only Python CPU validation
and forward computation, excluding loading, voice, monitoring and phone execution.

`protocol.json`, `results.json` and `run-manifest.json` bind this run's source,
selection, split and output bytes. The reference files retain their original hashes.
Total experiment storage was under 0.6 MB including ignored artifacts and bytecode;
there are no downloads, provider calls, phone actions or model promotions.
