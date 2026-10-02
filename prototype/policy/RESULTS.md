# Reference synthetic experiment

Measured 2 October 2026 using Python 3.14.3 on macOS arm64. This is a dated pre-event laboratory result, not a phone, NPU, LLM, real productivity, or competition-submission result.

The 6→8→1 network has **65 parameters**, nonnegative connection weights, and signed biases. Training used projected SGD, seed 20261002, 140 epochs, and 160 examples per family. The train/dev/holdout groups contain 640/320/480 procedurally generated scenarios, with no scenario family shared between splits. Model selection and threshold tuning used dev only. The selected threshold is **0.62**. Reproduction details and hashes are in [synthetic-model.json](synthetic-model.json).

| Metric | Synthetic holdout result |
| --- | ---: |
| Accuracy | 98.33% (472/480) |
| Precision | 98.81% |
| Recall | 98.03% |
| False-nudge rate among teacher-negative rows | 1.33% (3/226) |
| False negatives | 5/254 |
| Binary cross-entropy | 0.04225 |
| Brier score | 0.01174 |
| ECE, 10 probability bins | 0.01556 |
| Simple two-overrun rule accuracy | 78.96% |
| Training-majority baseline accuracy | 47.08% |
| Known synthetic teacher accuracy | 100%, by construction |
| Sampled monotonicity comparisons | 1,800, zero violations |

Held-out family accuracies were 98.75% for correlated overruns, 98.75% for sparse extremes, and 97.50% for moderate-everywhere scenarios. See [evaluation.json](evaluation.json) for confusion counts and other per-family metrics. That file also records a 100-run warm Python CPU microbenchmark; its roughly 0.005 ms forward-pass median is a laptop measurement excluding Android, speech, and model loading.

All seven unit tests passed: disjoint deterministic data groups, finite-difference gradient agreement, exact hidden-unit logit decomposition and interventions, monotonicity after projected updates, external pause/permission/focus/cooldown/freshness gates, invalid input rejection, and deterministic training with improved dev loss.

For the example `0.7,0.6,0.4,0.8,0.2,0.5`, reducing the synthetic budget-overrun feature to 0.1 changes the score from approximately 1.0 to 0.00292 and the recommendation from `offer_nudge` to `allow`. A pause or denied permission blocks either recommendation independently of score. The intervention is a controlled change inside this tiny model, not a causal conclusion about people or a language model.

The teacher is a known hand-designed monotone formula. Every split shares that label function, so strong accuracy only shows that this network approximates that formula under the chosen synthetic distributions. Knowing the exact rule is more accurate and avoids training. Neither this result nor the probability-bin ECE establishes useful real-world calibration, good user outcomes, learned phone habits, or a need for neural inference. The Android prototype's hand-set policy remains separate.

## Java export verification

The checkpoint was exported as constants into `TrainedPolicy.java` using [export_java.py](export_java.py). Six Java17/JUnit tests passed: nine held-out reference fixtures, exact contribution/ablation parity, 1,800 monotonic comparisons, invalid-value rejection, defensive copies, and non-increasing hidden-unit suppression. The standalone Android `PolicyLabActivity` and evaluator also compiled against Android API36; this is compilation evidence, not a tested-phone UI claim.

The reproducible `--verify` pass compared **all 480 held-out vectors** on Java17 against the Python implementation. Maximum absolute differences were 1.23e-15 for sigmoid scores, 1.43e-14 for logits, 7.11e-15 for hidden logit contributions, and 1.84e-15 for feature ablation scores. There were **zero threshold decision disagreements**. Full hashes, compiler version and measured differences are in [java-export-results.json](java-export-results.json). Those small discrepancies are normal floating-point summation differences; both implementations preserve the selected decisions. This desktop-JVM result does not establish physical-phone or NPU performance.
