# Six-request unit JNI phone diagnostic

This prospective diagnostic verifies the installed v0.17 Java wrapper's exact
unit-output JNI path on the Nothing development phone. It is pre-event research.
The protocol must be source-frozen, independently reviewed and explicitly
authorized before any phone or model call. The current files are preparation;
they contain no measured result.

The six strings come unchanged from the existing
`LocalModelIsolationInstrumentation.REQUESTS` at indices 0, 1, 2, 3, 4 and 6:

| ID | Exact request | Manual canonical gold | Capture |
| --- | --- | --- | --- |
| native-unit-1 | Start focus for 20 seconds | start_focus, duration_seconds 20 | Off |
| native-unit-2 | Stop focus | pause_focus | On |
| native-unit-3 | Set an alarm for 07:30 | alarm, hour 7, minute 30 | Off |
| native-unit-4 | Set a five-minute timer | timer, duration_seconds 300 | Off |
| native-unit-5 | Open calculator | open_app, calculator | Off |
| native-unit-6 | Do not open settings | unknown | Off |

The source-unit gold is 20 seconds for the first request and 5 minutes for the
timer. Gold, ordering and capture selection are fixed before output. These
examples are already seen; they are neither a new holdout nor general accuracy
evidence. There is one call per row, one attempt, no output-driven repair or
retry, and no executed phone action.

One existing checksummed Qwen3.5-0.8B Q4_0 file is loaded through the actual
installed `LocalModel` class. Every row calls `prepareGeneration` and then
`generatePreparedUnitCommand` with the unchanged Compatible→Unit renderer and
GBNF, context 1024, four CPU threads and a 128-sample limit. The runner records
each actual prompt/grammar SHA, generated JSON, native envelope and timings.
Generation must reach actual EOG, with at most 127 non-EOG generated tokens and
896 prompt tokens. No adapter, weight copy, download or application edit is
part of this diagnostic.

Every request forces Qwen inference, even when pure local recognition would
accept it in the product. Report raw model intent/unit/full-slot correctness,
checked-model proposals, separate fast-local recognition and the combined
pipeline with their actual origins. Fast successes never count as Qwen
predictions. Runtime success requires all six bounded valid CPU/EOG results,
the specified capture observations, model closure, verified network denial and
protected cleanup. Safe semantic misses/refusals remain descriptive coverage
results. Any checked-model, fast-local or pipeline proposal that **accepts wrong
complete canonical slots**, including an accepted negated command, fails the
diagnostic. Runtime success alone does not establish command accuracy.

Capture is enabled only for the second request, `Stop focus`. Its four expected
1024-wide prefill summaries are `ffn_out-0`, `ffn_out-11`, `ffn_out-23` and
`result_norm`, with eight finite first values and finite vector statistics.
They are observational associations. This procedure performs no activation
patch, ablation or causal interpretation experiment. Keep the captured request's
latency separate from uncaptured requests; six cases establish no percentile or
peak-memory claim. Any PSS sample includes instrumentation/framework overhead.

Before model access, verify exact target UID/main process and both packaged
manifests omit INTERNET. Check the actual target-process permission denial,
then attempt only IPv4 TCP **socket creation** through `android.system.Os.socket`.
It must fail with EACCES or EPERM, with no DNS, connection or payload. Close an
unexpected owned descriptor and fail before reading/loading weights. This
bounded denial evidence does not mean airplane mode, USB disconnection or every
device network interface was disabled. No network or permission setting changes.

The test APK contains the runner, while the target APK defines `LocalModel` and
all selected parser/review dependencies. Inspect DEX class ownership to exclude
test copies shadowing those classes. Bind exact test/target/original-test APKs,
native/model bytes, signatures and committed source digests. Source digests are
build attribution, not Java hashes recovered from DEX. Android's
[Instrumentation lifecycle](https://developer.android.com/reference/android/app/Instrumentation)
uses `onCreate`→`start` and the instrumentation thread's `onStart`; `finish`
reports the result and ends instrumentation. The runner's global watchdog and
independent host deadline bound the diagnostic separately.

There is one **global 120-second cooperative watchdog** across verification,
load and all six requests. It never resets per request. The host allows at most
150 seconds for instrumentation, preserves partial/failed output, and may
force-stop only this own target with the expected APK identity still verified.
Cancel/close the model and dispose watchdog resources; report any timeout or
unsafe/closure failure honestly. Do not extend a deadline or rerun a failed
request. Root binds the full execution source commit and protocol/runner/harness
identities before execution; the null execution commit in the preparation
protocol conveys no execution authorization.

The runner accesses no preferences, production singleton, microphone, service,
UI or phone action. The harness compares three named preference-store identities,
the complete paused/off checkpoint, canonical model bytes/hash/inode/link count,
microphone/notification grants and own service absence before and after. Keep
the selected v17 target installed and restore only the exact original test APK.
Refuse mutation over an unknown package. Install/restore clients have a
45-second polled deadline. Preserve each client's timeout/return code; subsequent
read-only inspection can separately establish the effective exact package state,
without another installation or instrumentation. Keep that reconciliation
distinct from client success.
This snapshot scope does not cover every Android setting or AppOp.

Exact outputs and phone records stay in exclusive ignored private artifacts.
An initial record labels inference as requested; actual generation completion is
derived from the native report. A failed preflight is no inference result.
Publish only counts, measured timings, source/package/evidence hashes and explicit
limitations. Require the strict 15 GB project cap and 10 MB reserve without new
dependencies or model copies. Actual visible fast proposals, manual-load fallback,
edits/cancellation/confirmation, local voice, floating/monitoring, iQOO/NPU,
Office Kit and eligible accepted submission remain separate work.
