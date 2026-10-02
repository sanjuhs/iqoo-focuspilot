# Logistic policy comparison

Pre-event research, 2 October 2026; not an eligible event-created submission.
The missing logistic-regression baseline is
now measured on the same immutable procedural data as the existing policy.
Each seven-parameter logistic model correctly classifies **469/480** synthetic
holdout rows, versus **472/480** for the unchanged 65-parameter positive network.
This narrow difference supports keeping simpler models in future comparisons;
it does not establish a benefit for real users or a need for a neural network.
Nothing was promoted into the Android monitoring path.

[Experiment and reproducible commands](../prototype/policy-baselines/README.md),
[frozen protocol](../prototype/policy-baselines/protocol.json),
[full results](../prototype/policy-baselines/results.json),
[source/output bindings](../prototype/policy-baselines/run-manifest.json).

## Protocol and evidence scope

The reference source and both JSON artifacts were byte-verified before import;
the original network was loaded, never retrained. Its original train/dev/holdout
metrics reproduce exactly. Train has 640 rows in four scenario families, dev 320
in two families, and holdout 480 in three separate families. Exact feature-vector
and family overlaps are checked. All labels come from the same known invented
teacher, including its `2.5 * max(0, x0+x1-.95)` interaction. Holdout results were
already public and the author knew the teacher and earlier results: this is
family-distribution shift on synthetic data, not an independent blind evaluation.

Both new models use the original six dimensionless inputs in [0,1], with no
transformations or regularization. The signed model allows negative coefficients;
the projected model clips each coefficient to zero after an SGD update and leaves
its bias signed. Both start at zero and follow the same fixed original training
budget: seed 20261002, 140 epochs and learning rate
`0.02 / sqrt(1 + epoch/25)`. Training rows alone update parameters. Strict minimum
development BCE chooses a checkpoint; the original dev-accuracy threshold grid
and tie rules choose the threshold. Both variants select **epoch 140, threshold
.49**. Both are reported; holdout does not select either candidate.

The selected parameter vectors actually changed: L2 distance from zero is
18.4275 for signed and 18.4609 for projected. Their last-epoch development BCE is
still improving, so neither the limited optimization budget nor this comparison
proves the best possible logistic fit. The reference network uses its original
epoch 100 and threshold .62, not a refitted common threshold.

## Same-row measured results

FP means an invented allow label received a nudge proposal; FN means an invented
nudge label received allow. These are label errors, not observed user harms.

| Policy | Correct /480 | FP | FN | BCE | Brier | ECE, 10 bins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Existing 65-parameter positive network | 472 | 3 | 5 | .04225 | .01174 | .01556 |
| Signed logistic, 7 parameters | 469 | 5 | 6 | .15282 | .03857 | .10199 |
| Projected logistic, 7 parameters | 469 | 5 | 6 | .15258 | .03850 | .10181 |
| Original simple overrun rule | 379 | 49 | 52 | ∞ | .21042 | .21042 |
| Train-majority: always allow | 226 | 0 | 254 | ∞ | .52917 | .52917 |
| Known label-generating teacher | 480 | 0 | 0 | 0 | 0 | 0 |

The hand rule is `budget_overrun >= .55 OR continuous_overrun >= .65`.
The majority label is selected from the 640 training labels, not holdout.
Rule, majority and teacher scores are hard 0/1 predictions, not fitted confidence:
BCE is infinite when any such prediction is wrong, represented as JSON `null`
with an explicit explanation. Their Brier/ECE are point-mass diagnostics, not a
claim of calibrated probabilities. Ten-bin ECE on 480 synthetic rows is only
descriptive for learned models as well.

The network is correct where either logistic is wrong on **six rows**; the reverse
occurs on **three**. The logistic decisions agree on all 480 holdout rows despite
slightly different coefficients/probabilities. The teacher wins by construction,
which limits any claim that learning is necessary when the true rule is known.

## Exact contributions and counterexamples

For either logistic model, `logit = bias + Σ coefficient_i * feature_i`.
Each named feature contribution is its exact signed product before sigmoid;
the sum plus bias reproduces all 480 logits with zero measured arithmetic error.
These are effects inside a seven-parameter decision model, not an explanation
of Qwen internals, a positive LLM, or validated human productivity concepts.

| Feature | Signed coefficient | Projected coefficient |
| --- | ---: | ---: |
| selected_app_budget_overrun | 10.242934 | 10.260359 |
| continuous_session_overrun | 8.084370 | 8.098724 |
| reopen_count | 2.385185 | 2.390813 |
| active_focus_overlap | 2.284435 | 2.288906 |
| deferred_nudges | .985630 | .988305 |
| elapsed_time_overrun | 2.587035 | 2.591726 |
| Bias | −12.277093 | −12.300100 |

All final signed coefficients happen to be positive. Signed training permits
negative weights; nonnegative projection guarantees monotonicity throughout its
updates. The projected checkpoint also passes 1,800 sampled monotonic comparisons
with zero score drops. Architectural monotonicity does not prove sensible labels.

The first fixed-order counterexample is **holdout-0033**, from correlated overruns:
the teacher says allow, while both models offer a nudge at threshold .49. Signed
probability is .496831, projected .496534; their logits are −.012676 and −.013864.
Thus the development-selected threshold can offer a nudge even below probability
.5. This is a concrete false positive, retained without retuning. The first five
wrong-row IDs, signed contributions, original synthetic vectors and teacher
interaction are reproducible via the README; raw vectors remain under ignored
`build/`, and their file hashes bind the run.

Conversely **holdout-0110** should receive a nudge according to the teacher, but
signed probability .488212 and projected .488461 fall just below .49, so both
allow it. Both false-positive and false-negative examples are retained; no
holdout-directed threshold repair was made.

## Gates, timing and limits

Thirty checks cover five external vetoes for each of six policies: pause,
permission denial, inactive focus, cooldown and stale observation. Each blocks
before probability computation using the unchanged Python policy gate. Three
focused unit tests pass and verify source/data tampering detection, absence of
holdout from fit, dev selection, projection, signed arithmetic and veto behavior.
They do not replace Android consent or lifecycle verification.

On this arm64 macOS laptop with Python 3.14.3, fitting and development selection
take .495 s signed and .514 s projected. Five warm passes through 480 vectors
measure approximately **1.43/1.45 µs** per logistic call versus **4.87 µs** for the
network, including input validation. These Python CPU timings exclude model
loading, feature extraction, speech, scheduling and end-to-end phone behavior;
there is no Snapdragon NPU or on-device timing claim. All new files, raw procedural
rows and two tiny checkpoints together occupy less than .6 MB.

Future promotion requires consented real labels, verified feature extraction,
fresh scenario-separated testing and an explicit choice of false-positive costs.
This informed synthetic comparison alone promotes neither logistic model nor a
recurring trained policy. It closes a research baseline gap while retaining the
original app, network, published video and model evidence unchanged.
