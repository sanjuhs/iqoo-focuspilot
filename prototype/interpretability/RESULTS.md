# First command-model intervention readout

Measured 2 October 2026 on the laptop CPU, exact pinned Qwen3.5-0.8B Q4_0 artifact. **Negative result for a semantic focus circuit or useful steering.** The experiment did verify actual activation writes, byte readback, fresh-context execution, and no-op/restoration parity. This is not a phone/NPU result, synthetic-policy result, or full application decoding benchmark.

The test teacher-forces a common assistant JSON prefix, then selects among seven unique label-initial tokens. Candidate-token scoring is narrower than complete grammar-constrained JSON generation. Its baseline failures must not be silently generalized into, or excluded from, the app's separate task benchmark.

| Partition | Correct first-token intent decisions |
| --- | ---: |
| Discovery, four matched wording families | 7/8 |
| Selection, two distinct families | 3/4 |
| Held out, four further families | 6/8 |
| Alarm/timer/calculator/negation controls | 3/4 |

Discovery-only activation association ranked four channels per layer. Selection-only opposite-donor patch tests chose **`ffn_out-11`, channels 970, 430, 948, 941**. The selection directional margin shift averaged +0.05080, versus +0.04097 for layer0's bundle and +0.00167 for layer23's bundle. That modest selection effect failed to generalize to held-out wording.

The sign convention below is positive when a patch moves the recipient's start/pause margin toward its matched opposite-command donor. Margin change and intent change are different outcomes.

| Held-out intervention | Correct | Intent changes | Mean directional margin shift | Cases in predicted direction |
| --- | ---: | ---: | ---: | ---: |
| Selected opposite-class patch | 6/8 | 0 | −0.00829 | 4/8 |
| Selected-channel zero ablation | 6/8 | 0 | +0.03410 | 5/8 |
| Random four-channel opposite patch | 6/8 | 0 | −0.00976 | 4/8 |
| Norm-matched random-channel patch | 6/8 | 0 | −0.04526 | 2/8 |
| Same-class discovery donor patch | 6/8 | 0 | −0.01979 | 5/8 |
| Identical-vector no-op write | 6/8 | 0 | 0 | — |
| Zero vector then restore before downstream compute | 6/8 | 0 | 0 | — |
| Entire last-token layer11 output zeroing | 5/8 | 1 | −0.34200 | 3/8 |

The seeded random control channels were 164, 694, 144, 884. Selected and norm-matched random patch perturbations had the same average L2 norm (approximately 0.00442). One random bundle and eight held-out commands are insufficient for a distributional significance claim, but the observed outcomes offer no evidence that the selected bundle provides semantic steering.

Whole-vector ablation changed `Deactivate focus while I work.` from the correct `pause_focus` to `start_focus`. That is broad degradation, not discovery of a pause circuit. On unrelated controls, selected-channel zeroing changed no intents. Whole-layer zeroing preserved alarm/timer/calculator labels and changed `Do not start a focus session.` from the incorrect baseline `start_focus` to `unknown`. A correction under one broad perturbation does not establish a negation mechanism.

Baseline misclassifications included `Switch focus mode off.`, `Take me out of focus mode.`, `Let's finish this block of focused work.`, and `Please help me leave focus mode.` as `start_focus`; the negated command was also misclassified. Thus the baseline reliability gate fails, independently of the weak intervention effects.

`summary.json`, `frozen-selection.json`, and `intervention-cases.json` retain the actual chosen bundle, every control's baseline/changed logits and intents, mutation counts, and write-readback checks. No-op and restoration cases compare full vocabulary-logit bytes against retained fresh-context baselines; all 16 comparisons passed. The experiment totals 108 native calls. The source/model hashes and actual elapsed time are recorded in `summary.json`.

The supported conclusion is: **controlled CPU activation mutation works at the inspected graph boundary, but this association-selected four-channel intervention does not explain or steer start-versus-pause semantics on the held-out wording.** No semantic neuron label should be added to the product inspector from this run. Further experiments need a reliable baseline, stronger channel selection hypotheses, multiple random-control bundles, new untouched wording, and complete decoder/phone replication. Do not tune these candidates repeatedly against this exposed holdout and report the tuned result as held-out generalization.
