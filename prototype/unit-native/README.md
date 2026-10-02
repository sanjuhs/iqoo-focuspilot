# Unit native development capture

This unpromoted host research wrapper is copied from the generic structured-native
driver SHA-256 `d4eb744192574ae7b0f08d00093758324d280c4376d98289d1299dc5deff601f`
with task paths, schema/event namespaces and descriptive text changed. No imported
module globals are mutated. It reuses the existing compiled
`prototype/qwen-balanced-native/build/capture` byte-for-byte. It does not compile
another native implementation or modify the selected app. The native source is
generic: it emits the generated text for its supplied grammar. The old Python
intent-only validator is not reused.

The existing pinned Qwen3.5-0.8B Q4_0 file is the only supported model. The command
fixes the adapter argument to `-`. CPU devices, four threads, context/batch 1024,
ubatch 256, one sequence, fresh context plus full recurrent/KV clear per request,
disabled tensor capture and grammar-then-greedy sampling are inherited from the
pinned core. Each request must reach actual `llama_vocab_is_eog` within 128
samples; the core emits at most 127 non-EOG tokens on a successful request. No
string stop-marker coercion, repair, retry or partial scoring is implemented.

Inputs come from the separately frozen architecture renderer: ASCII TSV rows
`id<TAB>canonical-base64(exact UTF-8 prompt)<LF>` and UTF-8 GBNF with a `root` rule.
IDs are unique, 1–64 ASCII alphanumeric/underscore/hyphen characters. Bounds are
1–200 rows, 1 MB TSV, 12,000 bytes per decoded prompt, and 4,096 bytes GBNF.
Input validation permits renderer newlines/special-token text and preserves them
exactly. Prompt+128 must fit the 1024-token context at native execution.

```sh
python3 prototype/unit-native/run_capture.py check-runtime
python3 prototype/unit-native/run_capture.py prepare \
  --prompts /absolute/path/to/rendered-prompts.tsv \
  --grammar /absolute/path/to/grammar.gbnf \
  --out prototype/unit-native/build/development-lock \
  --pin /absolute/path/to/renderer.java \
  --pin /absolute/path/to/development.jsonl
```

`check-runtime` verifies existing source/binary/build-record, three shared library
hashes, seven compiled-header hashes and required exported API symbols; it loads
no model. `prepare` additionally runs the binary's input-parser-only branch,
which exits before backend initialization. It creates an exclusive lock binding
all inputs, additional supplied pins and wrapper source. Neither command performs
inference. No dependencies/downloads/weights copies are required: Python standard
library and the existing native runtime suffice.

Only after root authorizes inference on a frozen commit:

```sh
python3 prototype/unit-native/run_capture.py capture \
  --lock prototype/unit-native/build/development-lock/lock.json \
  --out prototype/unit-native/build/development-capture \
  --source-commit FULL_FROZEN_COMMIT
```

The lock's single capture claim prevents an output-directory alias retry. All
outputs are exclusive and confined to ignored `build/`. `initial.json` exists
before any model-loading child, `started.json` binds its owned PID, and
`process.json` records exit/timeout, elapsed time and output hashes even on
failure. Only that child is killed/reaped after 240 seconds. Pre/postflight check
HEAD, frozen tracked-source bytes, all lock file hashes and the pinned model.
The wrapper reserves 3 MB below the strict project 15 GB logical-byte cap.

`raw.jsonl` contains a load record then ordered `{id,text,metrics}` rows. `text`
is the untouched generated JSON object string; duplicate keys, nonfinite JSON,
nonobjects, missing/reordered rows and false EOS evidence are rejected. Keys and
whitespace are not rewritten or assumed to be intent-only. Action/schema/slot
validation belongs to the independent evaluator; an arbitrary object is not
treated as an accepted action by this capture wrapper. `capture-summary.json`
binds raw/process/stderr/lock/model/source identities and reports complete rows.
Nothing is executed on the phone; this is host development evidence, with no
qualification, on-device/NPU or promotion claim.

Boundary verification, without inference:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 prototype/unit-native/test_capture.py
```

The unit and previous seconds encodings are development research inputs. Run
each paired arm on its own lock; both must share the frozen evaluator/corpus
pins. Retained known cases remain development evidence. This wrapper assigns no
unit meaning, performs no normalization, and makes no fresh qualification claim.
The schemas are `focuspilot.unit_native_lock.v1`,
`focuspilot.unit_native_process.v1` and `focuspilot.unit_native_capture.v1`.
