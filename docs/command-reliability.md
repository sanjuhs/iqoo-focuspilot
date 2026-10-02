# Independent command reliability — host native baseline

This **pre-event research evaluation** measures the existing Qwen3.5-0.8B Q4_0 through the same Java prompt/JNI/native grammar contract as Android. It performs no phone action, uses no cloud/API, trains nothing and changes no prompt/model. It is new evidence, distinct from the prior 16-case test and negative adapter experiment.

58 synthetic textual voiced forms across 26 frozen families were authored before inference and final Java-gate handoff. Supported commands and alarm/timer/app slots mix with unsupported spoken/date slots, negation, cancellation, compound requests, statements and outside-capability requests. Cases, predictions and source snapshots are ignored; the generator and content/family hashes are tracked. This covers text that might be spoken, not real ASR accuracy. The exact current Java `ModelCommandGate` was compiled/called with javac rather than duplicated in the evaluator.

| Result | Count |
|---|---:|
| Raw native schema valid and EOS reached |58/58|
| Raw semantic intent correct |25/58 (43.1%)|
| Raw unsupported-request abstention |0/22|
| Gated exact action/slot or correct abstention |49/58 (84.5%)|
| Supported strict requests correctly proposed |16/23 (69.6%)|
| Requests requiring abstention correctly rejected |33/35 (94.3%)|
| Supported requests incorrectly abstained |7/23|
| Accepted proposals / all cases |18/58 (31.0%)|
| Correct / accepted proposals |16/18 (88.9%)|

The gate's 49/58 score includes correct rejections; supported-task correctness is 16/23. Accepted proposals still require Android review/confirmation and separate outcome verification. **Zero actions were executed.** Format-valid model outputs were often wrong, and none of 22 unsupported-intent requests elicited model `unknown`.

The two accepted mismatches were a 17 minute focus request converted to disclosed open-ended focus, and an unsupported erase-picture request converted to harmless local status display through `explain`. The latter did not delete pictures. Neither counts as satisfying the original request. The gate source SHA-256 was `258bc03d39dab13de4b6da84b0370415ffe83994a2f990ad1339265d3405e9e7`; future repairs must be labelled post-test changes against known cases.

Actual host CPU timing: model/context load 923.4 ms; process-first inference 454.3 ms native / 458.6 ms wall. The remaining 57 requests had 444.1 ms median native total, 283.0 ms median prefill and 164.3 ms median decode; wall median 444.9 ms. Same first utterance repeated at end returned the same label in 440.8 ms native. Each request reset all recurrent/KV state; loaded weights remained shared. The OS cache was not flushed, so “process-first” is not a disk-cold measurement. No NPU, phone execution, thermal/power result or causal interpretability is claimed.

See [reproduction and limitations](../prototype/command-eval/README.md), [aggregate result/source digests](../prototype/command-eval/results.json) and [frozen family hashes](../prototype/command-eval/data-manifest.json). This small invented English set does not prove broad reliability. Keep bounded tools, original-text slot validation, abstention and explicit user confirmation; the current raw LLM is unsuitable for autonomous phone actions.
