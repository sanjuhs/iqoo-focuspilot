# Balanced Qwen native research capture

This small standalone C++ tool links the existing pinned Homebrew llama.cpp 9620
CPU libraries. It reads the **existing phone-selected Qwen3.5-0.8B Q4_0 GGUF**
without copying weights, and optionally loads one final-layer three-projection f32
LoRA. No dependency download, Android edit, tool execution or promotion occurs.

The original Java `LocalModel.renderPrompt` and `INTENT_GRAMMAR` generate exact
prompt bytes. The renderer initializes the existing JNI shared library but calls
no native model methods. Preparation snapshots source and hashes runtime, model,
headers, input, derived prompt/grammar, small binary and extra protocol/data pins.
The fixed study contract uses **a newly allocated context for every request**,
sharing only loaded weights/adapter; this differs from production JNI's reused
context plus recurrent/KV clearing. Both arms allocate identically, clear memory,
use 1024 context/batch, 256 microbatch, one sequence, four threads, zero GPU layers,
CPU devices, no KQV/operation offload, no activation callback, GBNF then greedy,
128 generated-token maximum and actual vocabulary EOG. No history is retained.
Load, context allocation/adapter attachment, prefill and decode are separate.

The optional LoRA is attached with API scale 1; its own GGUF alpha/rank encodes MLX
scale 8. Model loading retains existing defaults, including extra buffers. Actual
stderr identifies any CPU_REPACK→CPU fallback for adapted projections; this is
not assumed before a real capture. Different MLX/Q4_0 base quantization and model
lineage mean prediction transfer is an empirical gate, not an identity claim.
This is host research, not unchanged JNI, phone, NPU or ASR evidence.

Only root may authorize captures after the shared source/protocol/data freeze.
Commands are explicit; compilation and preparation perform no inference:

```sh
python3 prototype/qwen-balanced-native/run_capture.py compile
python3 prototype/qwen-balanced-native/run_capture.py prepare \
  --requests prototype/qwen-balanced-data/build/development-requests.tsv \
  --out prototype/qwen-balanced-native/build/dev-lock \
  --pin prototype/qwen-balanced-protocol/protocol.json \
  --pin prototype/qwen-balanced-data/build/development.jsonl
python3 prototype/qwen-balanced-native/run_capture.py capture \
  --lock prototype/qwen-balanced-native/build/dev-lock/lock.json \
  --out prototype/qwen-balanced-native/build/dev-base \
  --source-commit FROZEN_COMMIT
```

Prepare the same confirmation lock before its first base/candidate capture. Run
base first, then candidate serially using the same frozen lock and distinct new
output directories. Candidate adds `--adapter PATH --adapter-sha FROZEN_SHA256`.
Root records the final checkpoint/export hash before candidate loading. Frozen
tracked bytes must match the specified current commit; all inputs are checked
before and after the capture. An exclusive base/adapter claim in the shared lock directory prevents a second
attempt of the same arm, even if another output directory is requested. No retry,
overwrite or partial denominator is supported. A 240-second child deadline kills and reaps only that owned PID.
Initial metadata exists before loading; raw output, process records and logs stay
under ignored `build/`. A failed attempt remains intact for diagnosis.

Run boundary checks with `python3 -m unittest discover -s
prototype/qwen-balanced-native -p 'test_*.py'`. No tests load model weights.
Selected full-request Java gate scoring uses the frozen app gate and number-word
parser; `CommandGateEval` is the unchanged prior harness. Labels and slots come
from independently authored data, not model output or parser output. Supported
semantic accuracy, all seven-class confusion, unknown behavior, complete proposal
kind/hour/minute/seconds, oracle ceiling, paired losses and cold/warm allocation/
inference timings must be reported separately. A guard-refused unknown is not
model abstention. No synthetic result supports a general safety guarantee.

Full-slot scoring after a successful capture (no model calls):

```sh
python3 prototype/qwen-balanced-native/score.py \
  --lock prototype/qwen-balanced-native/build/dev-lock/lock.json \
  --capture-dir prototype/qwen-balanced-native/build/dev-base \
  --data prototype/qwen-balanced-data/build/development.jsonl \
  --out prototype/qwen-balanced-native/build/dev-base-score \
  --source-commit FROZEN_COMMIT
```

The gold corpus must be pinned when preparing the lock. Scoring calls only the
selected original-request Java gate; generated and independently supplied oracle
intents are separate routes. Exact kind/hour/minute/seconds determine complete
correctness. Unknown model abstention and gate refusal remain distinct. Paired
comparison is available as `score.paired(baseline_details, candidate_details)`; its
summary reports aggregate and per-intent/hard-tag gains and losses. Detailed IDs
and predictions stay in ignored build files.
