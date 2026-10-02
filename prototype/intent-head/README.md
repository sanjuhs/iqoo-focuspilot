# Learned intent head on actual Qwen hidden states

**Pre-event research, host CPU only, not deployed.** This is a separate signed-weight linear classifier with7,175 learned parameters. It is not Qwen fine-tuning, the positive-weight feature policy, a phone/NPU result, or an explanation of the whole language model.

The existing Qwen3.5-0.8B Q4_0 remains frozen and unchanged. The probe observes the actual1024-coordinate `result_norm` at the final prefill position, using the same full Android prompt and reserved-control escaping, context1024,4 CPU threads and fresh context/KV/recurrent state per case. No text generation or model-state mutation occurs during capture. Primary runtime: pinned [llama.cpp](https://github.com/ggml-org/llama.cpp/tree/57fe1f07c3b6a1de3f4fff19098e2056a85275b7). Model revision/license are already documented in [Qwen research](../qwen/README.md).

## Frozen protocol and actual learning

Before any capture,42 train/16 validation/24 heldout template families were fixed:222/61/90 synthetic English rows. Entire templates and time/duration values differ between splits; task classes, allowed apps and some domain words recur. There is zero exact training-text overlap with the previous58-case evaluation. Labels were locally authored, not copied from that evaluation. Data/template/protocol hashes are in the tracked manifests; raw text JSONL/full vectors/checkpoints/logs stay ignored under `build/`.

Train-only coordinate mean/std (population std floor0.05) normalize the vectors. A1024×7 matrix plus7 biases learns with400 fixed full-batch class-balanced softmax/Adam updates, lr0.02 and0.02 mean-square weight penalty. Initial weights/biases are zero. Actual parameter L2 change10.1992, final parameter digest `087432badf15cf5ef04c273b6ced2b9111214a486cb607a763f92b9b3992f6b3`. The immutable checkpoint's SHA `fa72f4715788c1aab3391d533e8972a4f7c76e272cc5e23db07fee81e9403464` remained unchanged after all evaluation. Fitting took50ms using existing Python3.12/NumPy2.5.3, no downloads or paid APIs.

Validation alone selects probability/margin thresholds from a predeclared grid, requiring zero validation unknown-to-supported false positives, then maximizing correct accepted supported requests. No checkpoint/prompt/hyperparameter selection or retraining followed the heldout result. Holdout labels were first read after checkpoint and threshold freeze. Probe collection of holdout features beforehand involved no labels/training.

## Same90-case heldout comparison

| Metric | Autoregressive base | Raw linear head | Selected abstaining head |
|---|---:|---:|---:|
| Intent correct |46/90 (51.1%)|76/90 (84.4%)|66/90 (73.3%)|
| Unsupported intent falsely accepted |24/24|9/24|0/24|
| Supported intents correctly accepted |46/66|61/66|42/66|
| Intent proposal coverage |90/90|75/90|43/90|

Current v0.7 Java gate SHA `30f35d17a54717318492110d39c5de260a57d6878bab1d1365f658bd8ee7200d` was compiled and called independently on original utterances and slots:

| Strict gated result | Autoregressive base | Selected head |
|---|---:|---:|
| Correct action/slot or correct abstention |42/90|40/90|
| Supported requests correctly proposed |17/65|15/65|
| Required abstentions correct |25/25|25/25|
| Accepted proposals |17/90|15/90|
| Wrong accepted proposals |0|0|

One spoken alarm is a valid alarm intent with unimplemented time slots, explaining65 strict supported requests versus66 supported intent labels. The language classification gain **did not improve strict action coverage** under the current bounded lexical gate. Valid paraphrases outside gate syntax are deliberately rejected. Proposal acceptance is not permission, confirmation, action execution or outcome proof: zero phone actions ran.

The selected probability threshold is **1.0**, margin0.0. Finite float64 logits rounded softmax maxima to exactly1 for146/222 train,25/61 validation and43/90 heldout rows. This gate relies on numerical saturation, not calibrated certainty; a backend/precision change can change acceptance. Zero false accepts on24 invented requests is not a safety guarantee. **Do not promote this policy.** Keep this negative finding alongside the raw classification improvement; another candidate needs a newly frozen independent protocol/evaluation, calibration and real-device regressions.

## Costs and interpretation

All373 observed vectors were finite/nonzero, width1024, no generation. Repeated first training utterance produced exactly equal vectors (max difference0);7 malformed probe input tests passed. Reported total setup+prefill work115.62s, model load323ms, median prefill304ms plus setup4.47ms. Autoregressive heldout run41.60s; median native inference456.9ms, wall457.6ms. Selected head alone median0.0090ms from an already captured vector, excluding all model/prefill/capture/gate costs. The full observed-prefill route is roughly308ms on this host; this is no phone/NPU speedup claim. Probe uses a fresh context per row while the baseline reuses context and clears state. Instrumentation, setup and absence of decoding differ; it is not a head-only acceleration measurement. OS cache/thermals/power were uncontrolled.

For a class logit, `bias + sum(z[j] * weight[j,class])` reconstructs the result exactly (max residual1.71e-13). Signed contributions are real products of normalized observed coordinates and learned signed weights. Full per-case top10 tables remain in ignored `build/head-run/contribution-examples.json`. First heldout example: contributions sum42.70434816758454 plus bias−0.13976692233342738 equals logit42.564581245251134, within floating-point error.

A **head-only** intervention set the strongest top-versus-runner coordinate to its training mean (normalized zero); direct recomputation matched subtracting its contributions across classes within2.70e-13. This changed argmax in1/90 cases. No Qwen tensor/state was patched, ablated or trained. Anonymous coordinate indices have no assigned semantic meanings; these arithmetic checks do not establish full-model mechanistic understanding.

## Reproduce

Use the existing local NumPy runtime and pinned model, not cloud training. Inspect `protocol.json`/`freeze-manifest.json` first. Reproducing this already-seen set does not create a new heldout result. Preserve original ignored captures/checkpoint before a fresh reproduction, and use a distinct training output directory.

```sh
python3 prototype/intent-head/generate_data.py
sh prototype/intent-head/build-probe.sh
```

Capture with an actual exit-status supervisor; this writes ignored vectors/provenance and has a finite600second budget:

```sh
python3 - <<'PY'
import hashlib,json,pathlib,subprocess
p=pathlib.Path('prototype/intent-head/build')
with (p/'vectors.jsonl').open('w') as out,(p/'probe.log').open('w') as err:
    job=subprocess.run([str(p/'intent_vector_probe'),'--model','models/qwen/Qwen3.5-0.8B-Q4_0.gguf','--input',str(p/'all-cases.tsv'),'--context','1024','--threads','4'],stdout=out,stderr=err,timeout=600)
status={'exit_code':job.returncode,'vectors_sha256':hashlib.file_digest((p/'vectors.jsonl').open('rb'),'sha256').hexdigest()}
(p/'capture-status.json').write_text(json.dumps(status)+'\n')
job.check_returncode()
PY
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  prototype/finetuning/build/venv/bin/python prototype/intent-head/train_evaluate.py \
  --out prototype/intent-head/build/reproduction-head
prototype/finetuning/build/venv/bin/python -m unittest discover \
  -s prototype/intent-head -p 'test_*.py' -v
```

The trainer verifies vector count/width/finiteness, probe exit/file hash, frozen input/model/template hashes, CPU/no-generation metadata and unchanged checkpoint. Java gate execution uses the real app source; it refuses a different gate hash. For an autoregressive comparison, compile/run `IntentBaseline.java` with the unchanged app adapter and verified host JNI library, save `build/baseline.tsv`, and record its exit/source/model/input/output hashes in `baseline-metadata.json`; then `--attach-baseline-only --out YOUR_HEAD_OUTPUT` adds comparison without training. Existing measured baseline provenance is included in results. Original training source snapshot is ignored; later source changes add baseline provenance checks and read-only numerical-confidence diagnostics. The frozen training source SHA remains distinct from the current source SHA; these additions do not refit weights or select thresholds. To regenerate confidence diagnostics from the immutable checkpoint/captures without training, run `prototype/finetuning/build/venv/bin/python prototype/intent-head/train_evaluate.py --review-diagnostics-only`. Future training reproductions include these diagnostics automatically.

[results.json](results.json) records all aggregate evidence, limitations, per-family counts, source/probe/model/checkpoint digests and the no-promotion decision. Seven classifier/freeze tests pass, separately from the probe's7 input tests. Sources and aggregates are backed up; raw vectors/training/checkpoint artifacts are excluded from Git.
