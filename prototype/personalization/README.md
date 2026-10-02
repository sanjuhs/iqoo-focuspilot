# Local few-shot preference sandbox

Pre-event research, 2 October 2026. The Android sandbox lets a person manually label an invented six-feature situation **Allow** or **Nudge**, then inspect nearby saved examples. It runs entirely in Java on the CPU; no provider request, new dependency, LLM inference or neural fine-tuning is involved. This component does not monitor phone activity, start services, issue notifications, or move money.

The features exactly match `TrainedPolicy.featureNames()`: selected-app budget overrun, continuous-session overrun, reopen count, active-focus overlap, deferred nudges and elapsed-time overrun. All six are explicitly supplied finite values in `[0,1]`, with no calibrated real-world units. Missing phone observations must never become invented input values in a product integration.

## Retrieval and explanation

`FewShotPolicy` keeps at most **32** examples, preserving insertion order. Adding a 33rd evicts the oldest. Every saved vector is copied defensively; callers can delete one example, clear everything or restore a fully validated collection. Invalid restoration is atomic and leaves prior data intact.

Distance is `sqrt(sum((query[i] - example[i])²) / 6)`. The three nearest examples vote with normalized weights proportional to `1 / (0.05 + distance)`. Their weighted Nudge-label contributions sum exactly to `nudgeVote`. Each neighbor also reports the saved vector and six squared-distance contributions; those sum to that neighbor's distance squared. These are exact arithmetic explanations of retrieval, not causal claims about productivity or neural activations.

Exact matches use only exact examples, including all exact duplicates. Conflicting exact labels always abstain, even if a conflicting example appears after the first three. Other queries abstain when the nearest example is farther than **0.25**, or the weighted Nudge vote lies strictly between **0.35** and **0.65**. There is no silent fallback to the trained policy. The uncertainty index combines vote disagreement and distance; it is heuristic and uncalibrated.

Pause, consent, required permission, active focus, observation freshness and cooldown are **external gates**. Any failing gate yields `BLOCKED` before neighbors are read. Examples cannot override those checks. The pure Java class performs no Android permission request or observation.

## Android sandbox

New sources in `prototype/android/app/src/main/java/dev/focuspilot/prototype/`:

- `FewShotPolicy.java`: platform-independent retrieval and gate evaluator.
- `PersonalizationActivity.java`: manual feature form, Allow/Nudge label buttons, comparison with the existing synthetic trained baseline, neighbor explanations and per-record/all-delete controls.

The Activity opens paused, with every consent/permission/focus/freshness/cooldown **simulation** disabled. Rotation preserves explicit sandbox edits. Switches never grant real permission or start a session. The UI makes that separation explicit. It does not collect observations or seed itself with the evaluation's invented examples.

Records persist in app-private `SharedPreferences` named `focuspilot_fewshot_sandbox`, under `examples_v1`, with schema1, IDs, six numeric features and labels. No raw text, app history, inference activation or account key is stored. Reads cap payload size and validate every record before restoring. The existing Android manifest disables app backup. Reset removes the preference key. Root application integration owns adding the Activity to the manifest and adding navigation; this slice changes no existing app file.

## Reproducible synthetic comparison

```sh
python3 prototype/personalization/evaluate.py
```

Uses only Python's standard library, the checked-in trained synthetic checkpoint, and installed Java. It compiles `FewShotParity.java` with the actual Android pure policies and checks every result against the Python retrieval reference. No model retraining, optimization or parameter search occurs.

Each of three invented preference profiles receives **32** labeled support examples: eight each from broad mixture, reopening, budget-dominant and session-dominant families. The heldout groups are correlated overruns, sparse extremes and moderate-everywhere, **80** cases per family, **240** per profile. Family membership, seed20261003, support selection and retrieval constants are fixed before evaluation. No heldout label enters retrieval. The teacher's threshold is shifted for lenient/strict preferences, or its focus sensitivity is changed. These are mathematical labels, not human judgments.

[synthetic-exemplars.json](synthetic-exemplars.json) preserves evaluation support data; it is never automatically loaded into the app. [evaluation.json](evaluation.json) records hashes, constants, grouped counts, parity and limitations.

| Invented profile | Baseline correct /240 | Few-shot answered | Few-shot correct / answered | Baseline accuracy on same answered cases |
| --- | ---: | ---: | ---: | ---: |
| Lenient |187|168 (70.0%)|155/168 (92.26%)|74.40%|
| Strict |169|175 (72.92%)|145/175 (82.86%)|70.86%|
| Focus sensitive |202|167 (69.58%)|145/167 (86.83%)|84.43%|

The few-shot policy improves accuracy on the subset it answers in this invented shifted-preference test, while abstaining on **65–73** cases per profile. Across all240 cases, its correct-answer counts **155/145/145** are lower than the baseline's **187/169/202**. Abstentions are never counted as successes. Sparse extreme vectors frequently fall outside the support neighborhood. There is no claim that personalization improves real outcomes, or that the 32-example limit is optimal.

**Java/Python parity:** all **720** heldout cases matched recommendations and numeric vote/uncertainty/baseline scores within `1e-10`; maximum observed absolute error **1.05e-15**.

## Verification and next gate

```sh
cd prototype/android
./gradlew :app:testDebugUnitTest --tests dev.focuspilot.prototype.FewShotPolicyTest :app:assembleDebug
```

Eight meaningful JVM tests pass: all six external gates override an exact Nudge label; missing and distant support abstain; conflicting exact labels cannot hide beyond the top three; uncertain neighbors abstain; exact Allow preference remains independent of the network; explanation sums and copies are valid; bounded eviction/delete/atomic restore work; malformed input is rejected. Android debug compilation also passed. Manual Activity/phone interaction is a separate integration check owned by the root app.

Before a live policy uses this store, define real feature normalization and availability, explicit opt-in labeling, user-specific validation and missing-data behavior. Keep the external lifecycle/permission/pause gates intact. Collect separate consented preference labels for evaluation; synthetic retrieval accuracy is insufficient for automated intervention.
