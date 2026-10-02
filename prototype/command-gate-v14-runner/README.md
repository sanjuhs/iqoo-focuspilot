# Gate-only frozen confirmation

Pre-event host CPU research. One unchanged shipped `LocalModel.renderPrompt`
capture supplies identical raw intents to baseline and candidate request gates.
The gates receive the same 100 complete original requests; each is also evaluated
on separately authored oracle domain labels. No phone actions, model downloads,
training or app promotion occur.

The model is pinned Qwen3.5-0.8B Q4_0, original seven-intent JSON grammar, maximum
128 output tokens, 1024 context, four CPU threads and capture disabled. Source
`1eed4348d3d0233d786bcd3b86c05d225ebf8db6` supplies original LocalModel,
ModelCommandGate and CommandNumberWords; the candidate replaces only the gate
snapshot. The number-word parser remains byte-identical.

Checksummed helpers are imported unchanged: `command-json-runner` supplies strict
canonical JSON/EOS decoding, complete ordered capture validation, semantic and
paired scoring, distributions and runtime inventory verification;
`command-v10-confirm` supplies actual Java gate evaluation and full-proposal
scoring. Gate subprocesses have a 30-second ceiling. All proposals include exact
kind, hour, minute and seconds. Invalid model output remains a semantic failure;
its gate abstention is counted separately. Oracle fallback statistics do not
reuse invalid model-output counts.

Root commits candidate, protocol and selection lock before fresh corpus authoring,
then creates `command-gate-v14-confirm/freeze-manifest.json` with the required
hash keys listed in the runner's `checks` inventory. The freeze also includes
`selected_source_sha256`, `candidate_number_words_sha256`,
`linked_libraries_sha256` and every prior/current overlap inventory. Selection
lock uses `candidate_source_sha256`; the final freeze uses `candidate_gate_sha256`.
The lock's `candidate_parser_sha256` binds the freeze's
`candidate_number_words_sha256`. Candidate Java, safety test fixtures and the
seen development request TSV must occur in the overlap inventory; metadata with
no embedded request examples is not treated as a request corpus.
Raw requests, authored cases and detailed outputs stay in ignored `build/`.

Root alone authorizes the single native execution:

```sh
python3 prototype/command-gate-v14-runner/run_evaluation.py --source-commit FULL_FROZEN_HEAD
```

The source HEAD must be clean and exact; the runner build directory and capture
outputs must be new. Started PID/command, stdout, stderr and terminal metadata
are preserved. The known native child has a 300-second ceiling and is killed and
reaped on timeout or unexpected errors. Partial results never receive a smaller
denominator or an automatic retry. `--score-only` permits only an already terminal
complete capture with no derived scoring artifacts; existing evidence is never
overwritten.

All source/corpus hashes, model/native bytes, every private overlap inventory and
the three referenced Homebrew libraries are rechecked at preflight, after the
terminal capture and before public results. These library bindings cover the
referenced files, not the whole OS or dynamically loaded backend dependency
closure. Own work is limited to 2 MB, with a 10 MB project reserve below 15 GB.

Public results contain one raw semantic/timing aggregate and paired gate
aggregates. There is no raw semantic or native latency improvement between gate
arms because both use the same capture. First-request timing stays separate;
cache, thermal and power conditions are uncontrolled. These informed synthetic
host rows do not establish phone, NPU or user-language performance.

At least four supported generated full-proposal gains, zero generated/oracle
supported losses, zero wrong accepts across both gates/routes, preserved Pause
outcomes and no per-intent declines are necessary review criteria. Passing
criteria never automatically changes the selected app or release.

Failure-oriented tests run without model inference:

```sh
python3 -m unittest discover -s prototype/command-gate-v14-runner -p 'test_*.py'
```
