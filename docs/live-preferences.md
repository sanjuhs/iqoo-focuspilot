# Few-shot preferences from real observations

Pre-event research, 2 October 2026. `LivePreferencePolicy` is a pure Java nearest-example policy for user-provided **Allow / Nudge** labels on complete, opt-in selected-app observations. It performs no gradient training, network calls, payments or Android actions. It shares the sandbox's distance/voting mathematics, but uses separate records with `REAL_OBSERVATION` provenance and strict contextual checks. The synthetic-trained neural score remains a shadow trace; it is not this preference policy.

## Exact context and source checks

`LivePreferenceScope` fingerprints a canonical schema-1 context: feature mapping version `selected-events-v1`, selected package, app budget, declared continuous selected-app limit, declared planned focus duration, and the SHA-256 of the exact goal text. Changing any app, duration or goal changes the fingerprint. Plaintext goal text is used transiently by `fromGoal()` and is not retained by the scope or records. A hash does not encrypt or guarantee anonymity of a guessable goal. Empty goals are consistently hashed; the UI should explain what goal the current label describes.

The scope constructor accepts the already hashed goal for restoration. `ObservationSnapshot` now exposes the actual budget/continuous/planned settings used for its vector. Saving and evaluating require matching package and those settings, the currently expected observation scope ID, explicit personalization opt-in, observation consent, Usage Access, active focus, a query no older than 15 seconds and all six present features. Missing limits/data remain missing; no manual sandbox vector is accepted through the save API. App/goal/settings edits must rebuild the scope; goal edits should also restart the repository's observation scope through the settings flow to avoid a pending UI label attaching to a previous goal.

`REAL_OBSERVATION` denotes this application's validated observation path. It is not a cryptographic device attestation, and the timestamp aggregation still has the [documented OS-event limits](live-policy-evidence.md). These checks do not establish that the selected app activity is productive for a real goal.

## Retrieval and action boundaries

At most 32 records exist across all scopes; a 33rd accepted label replaces the oldest inserted record. Only matching fingerprints participate in retrieval. Evaluation requires at least three scoped labels spanning at least two distinct vectors. This is a declared abstention heuristic, not a measured minimum sample size for reliable personalization.

The policy reuses `FewShotPolicy`: RMS distance across six normalized dimensions, up to three nearest examples, inverse `(0.05 + distance)` normalized vote weights, nearest-distance cutoff 0.25, Allow vote cutoff 0.35 and Nudge cutoff 0.65. All exact matches participate in conflict checks; opposite labels at the same vector cause abstention. An empty store, insufficient labels, distant situations and mixed nearby votes abstain. Neighbors expose exact numeric distance and label-vote contributions. Vote and uncertainty are heuristics, not calibrated confidence or validated human productivity measures.

`Decision.canVetoHandSetNudge()` is true only for an eligible **ALLOW** result. `permitsHandSetNudge(existingBudgetCooldownDecision)` returns `existingDecision && !allowVeto`. **NUDGE cannot produce a nudge on its own**: app budget, focus state, permissions and the existing cooldown still have to authorize the original hand-set rule. BLOCKED/ABSTAIN never veto; with live personalization disabled, the existing rule keeps its behavior. A repository integration must evaluate eligibility again at each tick and must not cache an Allow decision across pause, scope, permission or freshness changes. The repository integrates this veto after the foreground/budget/cooldown gate, before any virtual debit.

## Android-store contract

The integrated Android store/UI uses a private preference file named `focuspilot_live_preferences`, separate from `focuspilot_fewshot_sandbox`, with `enabled` defaulting to **false**. Do not mix synthetic records, manual developer vectors or imported unverified provenance into the live store. Delete live labels when the user chooses to delete focus data and examples. The downloaded model can remain installed as disclosed by the app.

Scope serialization fields are `schema`, `mappingVersion`, `selectedPackage`, `budgetMs`, `continuousLimitMs`, `plannedFocusMs`, `goalSHA256` and computed `fingerprint`. On restore, reject unknown schema/mapping, rebuild `LivePreferenceScope` from the hash/settings, and compare the serialized fingerprint with `scope.fingerprint()`.

Each record serializes `id`, that full scope, six feature numbers, enum `label`, `observedAtWall`, `observedAtElapsed`, `labeledAtElapsed`, and `provenance` exactly `REAL_OBSERVATION`. Raw goal text, transcripts and raw usage boundaries are not record fields. `observedAtWall` documents the historical query time. The two monotonic times prove that labeling occurred within 15 seconds of that query in its original process; they are not reused to judge today's query freshness after restart. Historical saved examples can remain usable under the identical current fingerprint; their age is not claimed as evidence of unchanged personal preferences.

Restore validates the entire list before replacement: maximum 32 records, positive unique IDs, nonzero declared time limits, finite six-element vectors in [0,1], supported labels/provenance, valid timestamp ordering and a label delay no greater than 15 seconds. Reject malformed/oversized records atomically; never silently convert missing inputs to zero or merge partial loads.

## Stable Java API

```java
LivePreferenceScope scope = LivePreferenceScope.fromGoal(
    selectedPackage, budgetMs, continuousLimitMs, plannedFocusMs, currentGoal);
LivePreferencePolicy.Gates gates = new LivePreferencePolicy.Gates(
    explicitlyEnabled, observationConsent, usagePermission, activeFocus,
    currentExpectedObservationScopeId);

// UI must obtain this from the current repository, never the developer sandbox.
ObservationSnapshot snapshot = repository.reviewableObservation();
LivePreferencePolicy.Record saved = policy.save(
    scope, snapshot, LivePreferencePolicy.Label.ALLOW, gates, nowElapsed);
LivePreferencePolicy.Decision decision = policy.evaluate(
    scope, snapshot, gates, nowElapsed);
```

`save()` rejects blocked input with `IllegalArgumentException` and leaves the store unchanged. `evaluate()` returns BLOCKED/ABSTAIN/ALLOW/NUDGE plus reason, vote, uncertainty and neighbors. The caller persists only after successful mutation. `records()` returns an immutable list and `features()` returns a defensive copy. `restore()`, `delete(id)` and `clear()` support bounded local lifecycle operations. `Record`'s public constructor is the strict restoration boundary; all metadata fields are immutable.

## Reviewing a recent foreground episode

The repository retains the latest complete selected-foreground vector for at most 15 seconds. Returning to the dashboard does not replace that vector with a zero-continuity background sample. The manual label dialog and Save recheck current goal/settings, active scope, consent, permission and age. Pause, reset or settings/permission changes invalidate it. The visible monitor must have sampled the selected app before returning; no guessed/manual sample is created if one is unavailable. This review history never authorizes current nudges; their gate uses the latest actual foreground observation.

The private store disables matching after an unconfirmed write or deletion. The dashboard reports incomplete deletion instead of claiming every label was removed. Export only occurs after a separate user-selected document destination.

## Evidence

Nine new pure JUnit tests passed, together with the ten observation tests: **19 tests total**, compiled/run directly with Java17 without Gradle or a phone install. They exercise all contextual fingerprint edits, no plaintext-goal scope restoration, opt-off/consent/permission/pause/scope gates, stale/future/missing inputs, settings mismatch, goal-label isolation, insufficient examples, conflicting exact labels, distant abstention, Allow veto, Nudge non-bypass, bounded eviction, defensive copies/deletion, provenance and all-or-nothing malformed restoration.

Host integration and UI compilation are separate from physical verification. No held-out real-phone accuracy gain or user-granted live preference session has been established. Those require recorded device tests before being claimed in the demo.
