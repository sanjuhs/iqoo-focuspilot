# Qwen3.5 unit-command JNI — Nothing phone research

Qwen3.5-0.8B Q4_0 remains selected. One frozen six-request check verifies the
installed v0.17 app's actual structured unit-command JNI path on the Nothing
A059/SM7635/API36. All six actual model outputs match the fixed, already-seen
intent and argument examples. The validator accepts the five supported proposals
and refuses the negated request; no phone action is executed.

This is a runtime diagnostic, not a fresh accuracy evaluation. Every request
forces Qwen inference, although the normal product recognizes these five supported
requests locally and can skip model work. Model, fast-local and combined origins
are recorded separately in [public metrics and evidence hashes](unit-native-phone-v17.json).

## Measured CPU execution

One model load takes 2,236.592 ms. All six generations reach actual EOS; 313 runner
checks pass, the model closes, and the global 120-second watchdog does not trigger.
The complete instrumentation takes 27,779.792 ms.

| Fixed seen request | Native total, ms | Capture |
| --- | ---: | --- |
| Start focus for 20 seconds | 5,736.762 | Off |
| Stop focus | 2,393.061 | On |
| Set an alarm for 07:30 | 3,774.894 | Off |
| Set a five-minute timer | 4,402.776 | Off |
| Open calculator | 3,930.307 | Off |
| Do not open settings | 3,305.123 | Off |

The captured Pause request returns four finite 1024-wide summaries: `ffn_out-0`,
`ffn_out-11`, `ffn_out-23` and `result_norm`. These are actual observations, with
no ablation or causal interpretation. Instrumented-process PSS samples range
1,198,263–1,237,999 KiB; these include test/framework overhead and are not peak RAM.
Six cases establish no useful percentile or general throughput claim.

Before reading or loading weights, the actual app process verifies target/test
manifests omit INTERNET and IPv4 TCP socket creation fails with EPERM. No DNS,
connection or payload is attempted. This proves that bounded permission denial,
not airplane mode, USB disconnection or every network interface being disabled.

## Restoration and attribution

The original test package's single streamed restore client times out at 45 seconds.
The initial harness therefore remains **passed=false**, even though its model
runtime passes and the protected state stays unchanged. The first subsequent
read-only inspection still finds the diagnostic test installed. Before a separately
planned recovery could install anything, its exact-identity guard detects a changed
test package and refuses mutation. Final read-only inspection verifies the original
test package has completed restoring. There is no additional install, instrumentation
or model generation; all initial failure and inspection records remain intact.

Final target APK, three named preference-store identities/paused checkpoint,
canonical model identity, microphone/notification grants and own-service absence
match the baseline. This does not fingerprint every Android setting or AppOp.
The runner accesses no preferences, singleton, service, microphone or UI.

The installed app source remains `a4f7a15c66cc44361e0b811aa578497a6b1cc8f9`,
APK SHA `05a3fae677d464195186acbf330bd9ceb53ba49d42d97463d2c1d29cc521953e`.
The test/protocol/harness are frozen at
`d4452e8d06f8decb19336bb849f40aed33cd45b2`; the exact copied runner and APK
ownership inspection exclude target-class shadowing. Source hashes attribute build
inputs rather than recovering Java source from DEX. No main APK is rebuilt or replaced.

The [prospective protocol and harness](../prototype/compatible-native-phone/README.md)
describe the single-attempt method. Sixteen pure boundary tests pass. Exact native
outputs, tensors, captures, test APK and weights remain ignored/private; public
metadata contains measured values, counts, hashes and limitations.

The [independent actual-record audit](unit-native-phone-v17-audit.json) verifies
26 committed source bindings, eight evidence/package hashes, complete output slots,
DEX ownership and the initial timeout followed by final restoration. It performs
no phone operation or model rerun.

## Remaining product work

Verify the unlocked visible no-load fast flow, manual-load fallback, edits,
cancellation and confirmation. Local voice and opt-in persistent/floating workflows
still need their actual permission/lifecycle checks. Actual iQOO Snapdragon NPU,
Office Kit, organizer-approved eligibility and accepted submission remain required.
This is pre-event research, not eligible event-written competition code.
