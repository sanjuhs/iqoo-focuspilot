# Compact Qwen intent development — unpromoted

This is pre-event research, not competition code. It runs the already selected
Qwen3.5-0.8B Q4_0 through the existing checksummed host CPU JNI. No model weights,
Android app, native library, phone settings or release were changed. No training,
download, remote inference or phone action occurred.

The actual development native is
`prototype/native/build/host/libfocuspilot_local.dylib` (85,224 bytes), SHA
`2e9fa6676c4d68d0b4119cf13d8176d4d6674939c9361c48883c15cfad2cb156`.
The parent's fresh confirmation uses the separate
`prototype/command-eval/build/native/libfocuspilot_local.dylib`, SHA
`ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e`.
Keep these binary/corpus scopes separate; development comparisons below are only
within the actual development backend. [Runtime provenance](runtime-provenance.json)
records observed dependencies, runtime version and current source/build instructions.
The pre-existing development dylib was not rebuilt, so its exact immutable
build-time compiler/source attribution is not newly established.

The openly seen prior development set contains 36 requests: 18 supported and 18
unsupported, including negation, conditions, delayed commands, compounds,
alarm/timer cancellation, payments, deletion, messaging and unrelated questions.
The generator is `../command-v10-dev/generate_corpus.py`; its unchanged identity
and exact requests hash are recorded for every actual capture. This is **not an
independent holdout**. Raw requests, logs, generated text and classes remain under
ignored `build/`; the tracked aggregate contains IDs, families, failures and hashes.

## Captured results

All four captures used context 1,024, four threads, capture off, and the same model,
native, current whole-request gate and bounded-slot parser. Each sequential native
request clears KV/recurrent state. All 36 outputs in every round satisfied their
exact format and reached actual native EOS. One compact emitted token means one
digit; the native metric does not count EOS as an emitted text token.

| Actual seen capture | Supported correct action+slots /18 | Raw unknown correct /18 | Raw intent correct /36 | Gated wrong accepts | Median prompt tokens | Median emitted tokens | Median native ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Deployed JSON prompt baseline | 12 | 2 | 14 | 0 | 158 | 8 | 444.05 |
| compact1: short prose examples | 10 | 5 | 15 | 0 | 180 | 1 | 349.43 |
| compact2: balanced prose examples | 15 | 3 | 18 | 0 | 247 | 1 | 465.33 |
| compact3: alternating chat examples | 13 | 10 | 23 | 0 | 266 | 1 | 499.40 |

compact1 and compact2 were fixed before any candidate inference. compact3 was a
development repair authored after compact1 results, before inspecting compact2
outputs. It changed example presentation and wording together; this experiment
does not isolate which feature caused a difference. Each candidate ran once;
there was no best-of-repeat selection. All attempts and failures are retained in
[development-results.json](development-results.json).

compact2 is frozen for a fresh independently authored synthetic confirmation
because it served the most supported development requests. This exploratory
selection prioritizes exact useful action+slots, then raw unknown rejection, then
native median time. It is **not promoted**. Its median is about 4.8% slower than
the same-set baseline despite shorter output. compact1 is faster but regresses
supported coverage; compact3 has better raw rejection but fewer useful actions.
The selected candidate still proposes a non-unknown intent for 15/18 unsupported
requests; only the independent whole-request gate blocks them in this set.

Against the same-set baseline it gains four supported cases (seconds timer,
countdown wording, Clock navigation and focus status) and loses one (spoken alarm).
Three selected supported requests still abstain: study break, spoken alarm
(wrongly classified as timer) and remaining focus time. All per-ID raw/gated
failures are preserved, including rejected candidates' regressions.

Host timings include native request prefill/decode and fresh state handling,
exclude model initialization and action/UI work, and have uncontrolled OS cache,
thermals and scheduling. They establish neither Android latency nor NPU use,
autonomous reliability, universal rejection or a mechanistic interpretation.

## Frozen candidate contract

[CompactIntentCandidate.java](CompactIntentCandidate.java) is the exact captured
compact2 source. [candidate.json](candidate.json) pins its Java hash, grammar,
maximum generation limit, actual rendered-marker prompt hash, model/native and
15 literal fixed examples for confirmation overlap inventory.

| Digit | Intent |
| --- | --- |
| 0 | unknown |
| 1 | start_focus |
| 2 | pause_focus |
| 3 | alarm |
| 4 | timer |
| 5 | open_app |
| 6 | explain, including focus status |

`renderPrompt(String)`, `GRAMMAR` and `MAX_TOKENS = 4` are public. Grammar admits
exactly one digit. A caller must require exact one-digit output and real EOS,
map it to the existing seven intents, validate the **entire original request**
and all arguments through the unchanged gate, then require explicit action review.
Never execute the digit directly. Invalid output becomes unknown, never a
fallback accepted command. Reserved chat-control delimiters in user text are
escaped identically to the baseline. No dialogue history is retained.

The immutable Java SHA is
`9ab64c5c7291c713aca37822d32f5d822d63805da5c607ba3773b45052f9cef9`.
Grammar SHA is
`5a578ecc14e19ddf20a25f9cd3a276fd32de635f8adf6929a2bd5e64a5300066`.
Actual `renderPrompt("UNIQUE_COMPACT_INVENTORY_REQUEST_314159")` SHA is
`01058d025401f173f310b38e64232302248fefbb5a1f03fc55f03ded73e36cca`.
The marker is inventory data, not a training/evaluation request.

## Reproduction and provenance

The runner hashes the existing model/native and app adapter/gate/parser, snapshots
selected Java sources, uses a new named ignored output directory, checks all
request IDs and formats, bounds compilation/gate subprocesses to 30 seconds and
the sole inference subprocess to 180 seconds, and closes the native handle in
`finally`. It refuses any previously used round name. No existing output or
model file is deleted. The entire directory is bounded to 10,000,000 bytes and
currently uses under 1 MB, including ignored captures.

```sh
python3 prototype/command-compact-dev/run_development.py --round replay-baseline --candidate compact2 --baseline
python3 prototype/command-compact-dev/run_development.py --round replay-compact2 --candidate compact2
```

Replays remain seen development evidence. They cannot replace a fresh frozen
confirmation. `run_development_initial.py` preserves the exact runner bytes used
for baseline/compact1/compact2. The current runner additionally permits compact3
and snapshots its own source; captured metadata retains each exact runner hash.
Those runner command-line/provenance changes did not alter native generation or scoring.
`freeze_candidate.py compact2` created the selected source and aggregate once; it
refuses to overwrite an already frozen selection. Candidate source must remain
unchanged during the parent's independent confirmation.

No app or release changes follow from these development scores. Promotion needs
fresh frozen supported/unsupported confirmation with explicit gains/losses, exact
slot outcomes, all failures, prompt overlap inventory and then actual device cost.
