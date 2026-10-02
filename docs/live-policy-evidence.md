# Live selected-app shadow policy

Pre-event research, 2 October 2026. This adds actual opt-in OS timestamp aggregation and an **SHADOW · NO ACTIONS** evaluation of the existing 65-parameter synthetic-trained network. The live hand-set rule, its cooldown and virtual ledger remain responsible for recurring nudges. The network is not trained or validated on real human productivity; its score is not calibrated distraction risk.

## Observation and validity

`UsageReader.observe()` runs only with observation consent, an active focus session and Usage Access. Existing dashboard/service ticks refresh the snapshot; querying the latest snapshot does not start monitoring or make an OS query. OS events are reduced to selected-app resume/pause, anonymous other-app resume, screen-off and device-boundary timestamps. No class name, text or other-app identity enters the aggregator. These temporary boundaries and the resulting feature vector are not persisted.

Android's [queryEvents documentation](https://developer.android.com/reference/android/app/usage/UsageStatsManager#queryEvents(long,%20long)) describes a permission-dependent, bounded history and a nullable result for a locked user on Android R+. An empty/null stream is not evidence of zero usage. The query includes a five-minute seed window; if it cannot establish the selected-app state at the observation start, completeness is false and affected features are missing. The seed contributes no duration or reentries from before consent/scope start. Future timestamps are ignored; out-of-order boundaries and device restart/shutdown within the scope block the shadow trace.

The [event documentation](https://developer.android.com/reference/android/app/usage/UsageEvents.Event) defines per-Activity foreground/background transitions, including multiple activities within one package. API29's resume/pause values alias the earlier foreground/background constants; screen-non-interactive is available at API28. A selected pause/resume alone does not count as a reopen. A confirmed return after another app resumes or the screen turns off does. These are **observed foreground reentries**, not application-launch counts. Duplicate resume events do not add reentries. Screen-off ends selected use until another selected resume.

This is a chronological foreground-boundary approximation. Split-screen, OEM event delivery, missing transitions and late OS reporting can affect it. It establishes what the queried stream reports, not actual attention or completeness of Android's internal event log. Freshness means the query occurred within 15 seconds; it does not prove zero OS reporting delay.

## Explicit mapping: `selected-events-v1`

The synthetic checkpoint originally used dimensionless invented inputs with no real-unit calibration. The following newly defined mapping preserves their names, with operational scales declared here; it does not retrospectively validate the synthetic accuracy on phone data. Let `overrun(t,L) = clamp((t-L)/L, 0, 1)`.

| Input | Actual source and transformation | When missing |
| --- | --- | --- |
| Selected-app budget overrun | Observed selected foreground duration in this consent/focus scope; `overrun(duration, selectedAppBudget)` | Incomplete event stream or invalid budget |
| Continuous-session overrun | Current uninterrupted selected foreground interval, clipped to scope start; `overrun(interval, explicitContinuousAppLimit)` | Incomplete events or undeclared continuous limit |
| Reopen count | Confirmed foreground returns within the scope; `min(returns / 5, 1)` | Incomplete event stream |
| Active-focus overlap | Selected foreground milliseconds / monotonic milliseconds in the observed active-focus scope | Incomplete events or a zero-length scope |
| Deferred nudges | Count of explicit `userDeferredNudge()` feedback for actual hand-set-rule nudges in this scope; `min(count / 3, 1)` | Feedback scope unavailable; no feedback in a valid scope is a known zero |
| Elapsed-time overrun | Monotonic elapsed time since the current active focus phase began; `overrun(elapsed, explicitPlannedFocusDuration)` | Planned duration undeclared, as for the current open-ended focus timer |

The duration/return count features start a new observation scope on pause/resume, reset, package/budget changes, observation changes, explicit limit changes and detected permission loss. Elapsed focus time includes the current active phase before an observation scope was changed; it excludes earlier paused phases. A wall/monotonic discrepancy greater than two seconds invalidates timestamp-derived features. Process recovery stays paused; no snapshot or feedback counter is restored. Only declared limit settings are persisted. Package/budget changes clear the declared limits so another app cannot silently inherit them.

## Repository contract for UI integration

- `shadowContinuousLimitMs` and `shadowPlannedFocusMs` expose the declared settings. `configureShadowLimits(continuousMs, plannedFocusMs)` saves values from 0 to 24 hours. **0 means unknown**, and default settings block the network. Call the setter instead of changing fields directly.
- `refreshShadowObservation()` is already called by the existing gated tick. `latestObservation()` returns a fresh snapshot or null when paused, unconsented, unpermitted or stale. The snapshot may be incomplete: `features()` retains **NaN for missing entries**, and `missingReasons()` explains why. Consumers must check `complete()` before storing or evaluating a vector.
- `shadowDecision()` returns `ObservationSnapshot.ShadowTrace`. `evaluation` is null unless scope, consent, permission, active focus, query freshness and all six feature-validity checks pass. `blockedReason` describes the failure. Successful traces expose the trained network's exact eight hidden contributions, output bias, logit, score, feature ablations and hidden-unit suppression through the existing `TrainedPolicy.Evaluation` API.
- `userDeferredNudge()` accepts explicit feedback once per actual nudge within its 60-second window, only while this same observation scope is eligible. It increments an in-memory counter and invalidates the old vector until the next observation. Calling it never moves money, applies another nudge or labels model training data. UI feedback wiring is separate work.

No preference veto or few-shot action policy is integrated by this change. No trained shadow score influences the ledger, service, notification or phone tools.

## Verification and remaining evidence

Ten new pure Java/JUnit tests passed without Gradle: clipping the seed history, same-package transitions, duplicate resumes, confirmed returns, screen-off, future-event exclusion, missing leading intervals, invalid ordering, device boundaries, declared feature formulas, exact hidden-contribution summation, missing limits, zero-duration scopes, wall-clock changes, permission/consent/pause/scope/freshness gates, and explicit feedback validity/reset. The repository and Android adapter compiled against SDK36 with Java17. Existing full trained-network/Python parity evidence is separate and unchanged.

No phone install, new physical-phone event validation, or Gradle build was run for this slice. Next evidence must exercise a user-granted Usage Access flow: select one test app, declare limits, start focus, switch into/out of that app, turn the screen off, return, inspect summaries, then revoke permission and pause. Compare the boundary-derived totals against a manually timed session, including an internal app activity switch. Do not claim live behavioral accuracy until those results are recorded. This scope still cannot assess whether the selected activity is productive for the user's actual goal.
