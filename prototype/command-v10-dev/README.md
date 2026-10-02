# Seen command development benchmark

Pre-event, synthetic, openly seen development data. These 36 authored commands are for prompt/gate iteration: 18 supported requests (three each for focus start, focus pause, alarms, timers, approved apps and focus explanation), plus 18 unsupported requests. Known failure families and familiar phrasing are intentionally included. This is **not** an independent holdout, calibration set, phone test, or evidence that a candidate should ship. The blind v10 evaluation directory is not read by this workflow.

`generate_corpus.py` defines every request, expected semantic intent and exact allowed action/slot tuple. Unsupported families include negation, conditions, compound requests, unsafe operations, existing alarm/timer cancellation, unsupported tools, general questions and assertions. `DevBaseline.java` uses the snapshotted actual `LocalModel` adapter and existing host JNI to capture proposals; `DevGateEval.java` calls the snapshotted actual `ModelCommandGate` plus `CommandNumberWords` on each complete original request. No tool or phone action executes.

Run the historical v0.8 baseline once:

```sh
python3 prototype/command-v10-dev/run_benchmark.py \
  --round baseline-v08 --ref 6e483aaf9e42889794ed77c272b8a912539cfc7c
```

After reviewing a candidate, capture a **new named round** from a directory containing its three Java sources:

```sh
python3 prototype/command-v10-dev/run_benchmark.py \
  --round candidate-01 --source-dir PATH_TO_CANDIDATE_SOURCES
```

Each round retains its source snapshot/hashes, dataset, requests, raw model envelopes, stderr, capture exit status, complete per-case results and aggregates under ignored `build/<round>/`. Existing captures are never overwritten. The historical baseline is compiled from the named Git commit, independently of later app edits. Candidate source files are copied before compilation/inference and checked unchanged afterward.

The runner verifies the existing Qwen3.5-0.8B Q4_0 GGUF SHA and current host JNI SHA, uses CPU/context1024/four threads with capture disabled, requires complete allowed JSON plus EOS, and bounds a capture to 180 seconds. It loads the model once and the existing native core clears recurrent/KV state per command. Invalid/unfinished generation becomes unknown and is counted separately. Output includes raw semantic correctness, supported exact action/slot correctness, unsupported model non-unknown proposals, gate false accepts, and false abstentions. Report both model and gate evidence; rejection by the gate does not make a bad model proposal correct.

Timing is instrumented sequential laptop CPU evidence with uncontrolled caches/thermals; subsequent commands reuse the allocated native context while clearing state. No phone/NPU, task-completion or generalization claims follow. Any prompt selected using these results requires the root agent's separate source lock and untouched blind evaluation before promotion. This directory does not modify app/native sources, earlier frozen evaluation evidence or any blind data. No model download/provider call is involved.

## Completed development rounds

These measurements use the same 36 seen cases, unchanged model/JNI, exact snapshotted app adapters and gates. Correct actions require both the expected tool and every bounded slot. All unsupported false accepts below are **after** the actual deterministic gate; unsupported model proposals remain separate errors.

| Seen round | Raw intent /36 | Supported exact actions /18 | Unsupported model non-unknown /18 | Unsupported accepted actions /18 | Median prompt tokens | Subsequent native median ms |
|---|---:|---:|---:|---:|---:|---:|
| Historical v0.8 | 14 | 12 | 16 | 0 | 158 | 460 |
| Candidate round1 | 28 | 11 | 1 | 0 | 589 | 1243 |
| Candidate round2 | 30 | 15 | 3 | 0 | 467 | 972 |

Round1 was not promoted: rejection improved while useful command coverage declined, and its longer prompt took about 2.7 times as long on this host. It abstained on all three focus explanation requests, two pause requests and two approved-app requests. The result supports shortening and balancing the development prompt; it does not establish which prompt feature caused the regressions. Both rounds produced 36 complete allowed JSON outputs ending in EOS. Detailed raw evidence and snapshot hashes are retained in `build/baseline-v08/` and `build/round1/`.

Round2 shortened the prompt and interleaved examples. Supported exact actions improved to 15/18 with all three focus explanations correct; its remaining false abstentions were study break, polite settings opening and navigation to Clock. All three remaining unsupported model proposals were blocked by the gate. Supplying the expected intent to the actual snapshotted gate accepted all 18 supported requests with exact slots, isolating these particular misses to model proposal abstention. This diagnostic is not a model score. Round2's host median remains about 2.1 times baseline; it was about 22% faster than round1. Each candidate had one real capture, no best-of-repeat selection. Aggregate metrics, source/runtime hashes and strict failures are retained in tracked `development-results.json`; full raw captures stay in ignored `build/`. No round is promoted by this benchmark.

## Rejected prompt source archive

`candidates/round1/LocalModel.java` and `candidates/round2/LocalModel.java` preserve the exact actual Java adapters captured above. They are development prompt artifacts, **rejected for promotion** after the root agent's separate evaluation; they do not replace the deployed adapter. They are source only: no model weights or raw capture outputs are included here.

| Source | SHA-256 |
|---|---|
| Round1 adapter | `8916ef91bb41a38a250333344803f23e22cc586272807b9f7d9d360a26848f45` |
| Round2 adapter | `2152a4f73579d4d3ceabbec219e6bfbd6973ab0c659706b554c26e84bf0a6329` |
| Shared candidate gate | `cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4` |
| Shared number parser | `e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d` |
| Historical/deployed prompt adapter | `2f6784c524ca9304fd714b86c04f5b1c3c5deb7e5ff562fbc34ae32c39e51e5d` |

To reproduce one rejected round later, place its archived `LocalModel.java` in a new directory under ignored `build/`, along with `ModelCommandGate.java` and `CommandNumberWords.java` from the final candidate commit whose hashes match the two shared values above. Verify all three hashes before running `run_benchmark.py --round replay-round2 --source-dir <that-directory>` (choose a fresh name). The final commit may retain the historical prompt while retaining the candidate gate: do not accidentally use its `LocalModel.java` when reproducing a rejected prompt. The runner snapshots the three selected sources again, so later app changes cannot alter a retained named capture. The original historical baseline is reproducible from commit `6e483aaf9e42889794ed77c272b8a912539cfc7c` via the earlier `--ref` command. Reproduction remains seen development evidence, not a new holdout.
