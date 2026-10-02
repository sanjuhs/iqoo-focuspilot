# Frozen compact intent comparison runner

Pre-event host research. This runner compares the shipped Qwen3.5-0.8B Q4_0
JSON prompt with one development-selected digit candidate. It executes no phone
action. The selected APK/model/prompt remain unchanged. The fresh candidate is
rejected; [result and decision](../../docs/compact-intent-research.md).

Sources were committed before capture at `c0c7e89`. Two complete 100-request native
captures ran sequentially, baseline then candidate, using the existing checksummed
Mac host JNI library, context 1,024 and four threads. State is cleared per request.
The second capture finished before any gate score files were produced.

`CompactCapture.java` passes only the request text to native inference. Semantic
labels and oracle slots are scoring data, never model input. The candidate's exact
one-digit answer and actual EOS are required before mapping to the original seven
intents. The unchanged Java gate checks the complete original utterance and exact
action/slots. No retries, candidate repair, training, provider call or deployment
occurs. Raw corpus/captures/results remain ignored.

The Python runner verifies candidate/map/grammar/source and protocol identities,
all prior/example inventory hashes, required counts/slots/hard tags, and model/
native hashes before capture. It refuses existing evidence and reserves 10 MB
within the 15 GB project cap. Each native subprocess is bounded to 300 seconds;
timeout/exit/output metadata are retained. Both terminal capture identities and
complete request IDs must pass before derived gate scores. Missing/nonfinite
metrics remain explicit; parser failure cannot inflate unknown-intent success.

## Validation without model inference

```sh
python3 -m unittest discover -s prototype/command-compact-runner -p test_scoring.py -v
python3 -m unittest discover -s prototype/command-compact-confirm -p test_data.py -v
```

Twelve scoring tests cover truncation, extra text/keys, duplicate JSON keys,
same-intent mapping, missing captures, semantic mistakes, hidden hard regressions,
missing metrics, invalid slots and family/tag constraints. Eight authoring tests
cover the frozen synthetic corpus and overlap/provenance checks.

## Repeat in a separate scratch checkout

The original workspace contains completed captures and is deliberately not a
replay destination. A repeat uses now-seen requests and is not a new independent
confirmation. Preserve every original aggregate and capture.

Use a separate scratch checkout with the same selected app history, public
research sources and exact existing model/native/runtime prerequisites. The host
native is `prototype/command-eval/build/native/libfocuspilot_local.dylib`, SHA
`ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e`.
OpenJDK 17 is located at the runner's recorded Homebrew path. The GGUF is the
already pinned 563,036,064-byte file. This script installs or downloads nothing.
Other platforms/runtime builds need separately attributed experiments.

Reconstruct the mandatory earlier synthetic and prompt inventories using their
tracked generators/adapters, retaining each hash in the freeze manifest. The
[authoring protocol](../command-compact-confirm/PROTOCOL.md) and generator list
the exact sixteen inputs. Missing or changed inputs abort; do not bypass the
hashes. Then run the generator to reproduce its exact cases and requests.

Before repeating in that scratch copy, preserve its published `results.json` in
an ignored archive and leave the new result destination absent. This is only a
throwaway-copy setup step; never move or overwrite original-workspace evidence.
The runner intentionally refuses an existing public aggregate or derived score.

```sh
python3 prototype/command-compact-runner/run_evaluation.py
```

`--score-only` is for both completed captures with no previously derived scores;
it verifies both terminal identities before scoring. It does not replace or repair
earlier results. Original raw captures are ignored, so a public checkout cannot
score them without retained matching local files. Source recovery alone cannot
reproduce measured timings. The public aggregate and evidence manifest bind the
actual completed run; broader hardware/voice reliability remains unverified.
