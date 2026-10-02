# Frozen JSON prompt confirmation runner

Pre-event CPU research utility. Compares the original shipped JSON prompt with
the locked `JsonIntentCandidate` on the same prospective 100 requests. It never
executes phone tools, downloads models, trains weights or promotes a candidate.

Both arms use the original seven-label JSON grammar, maximum 128 generated
tokens, 1024 context and four CPU threads. Java clears model state before every
request. Strict decoding rejects duplicate keys, extra fields, malformed JSON,
noncanonical serialization and loss of the actual native EOS flag. Invalid
outputs count as semantic failures; gate UNKNOWN fallback is reported separately.
Complete gate scoring includes kind, hour, minute and seconds, using the original
full request and unchanged selected gate/parser snapshots from app source
`1eed4348d3d0233d786bcd3b86c05d225ebf8db6`.

The semantic scorer, paired summary and distributions are imported unchanged
from checksummed `command-compact-runner/run_evaluation.py`; gate evaluation and
complete-proposal scoring are imported unchanged from the checksummed
`command-v10-confirm/run_evaluation.py`. A subprocess proxy gives unchanged gate
compilation/execution a 30-second ceiling. Native confirmation uses the fixed
`command-eval/build/native` library (`ad57cd04…`), separately identified from the
development library (`2e9fa667…`).

Root must commit the selection lock before authoring and freeze protocol,
candidate, source, inventory, requests, cases, runner and shared helper bytes
before execution. `freeze-manifest.json` lives in `command-json-confirm/`;
`generator_sha256` refers to its tracked generic `generate_data.py`, and raw
authored cases stay ignored. Required freeze keys are listed by the `checks`
inventory in the runner. The selection lock is `command-json-confirm/selection-lock.json`.
All available prospective prior/example inventories must retain their hashes.

Only root authorizes execution. With a clean exact source commit, run once:

```sh
python3 prototype/command-json-runner/run_evaluation.py --source-commit FULL_FROZEN_HEAD
```

Before any inference, both captures must be absent and the runner build directory
must be new. Each arm has an ignored started record with PID/command, stdout,
stderr and terminal metadata; its native process has a 300-second ceiling. An
incomplete capture is preserved and never automatically rerun. Output, log,
request and source hashes bind both successful terminal captures before scoring.
The runner checks frozen source bytes again after capture and before publication.
It requires a 10 MB project reserve within 15 GB and limits its own work to 2 MB.
Model, native library, every private overlap inventory and the three referenced
Homebrew libraries are rehashed at preflight, after each terminal capture and
before publication. `linked_libraries_sha256` is required in the freeze manifest.
This binds those referenced libraries, not the entire OS or every dynamically
loaded backend dependency.

`--score-only` is for two already terminal successful captures with no derived
gate/scoring outputs yet. It refuses partial inventories, changed hashes and
existing derived evidence. It does not overwrite previously published results.

Raw model strings, all requests/cases and detailed paired failures stay in
ignored `build/`; tracked results contain aggregate counts and hashes. Report
first request separately from subsequent timing, all per-intent/family/hard-tag
regressions, wrong accepts, EOS failures and cost tradeoffs. Host cache, thermals
and power are uncontrolled; these are informed synthetic examples, not human
sampling, phone measurements or NPU evidence.

At least four supported complete-proposal gains, zero supported complete losses,
zero semantic losses across all 100 rows, no per-intent declines, no Pause losses,
zero wrong accepts in either arm and all 100 valid candidate schema/EOS outputs
are necessary review criteria. Passing them never automatically changes the app.

Run failure-oriented host tests without model inference:

```sh
python3 -m unittest discover -s prototype/command-json-runner -p 'test_*.py'
```
