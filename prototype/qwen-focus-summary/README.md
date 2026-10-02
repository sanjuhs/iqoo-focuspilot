# Focus status summary candidate

Pre-event research utility, not deployed app behavior. `FocusStatusSummary` is a
pure Java formatter of immutable app facts. It does not infer a user request,
execute a tool, persist data, read permissions or invoke a model. Root may copy
the proven helper into the Android source in a separately reviewed integration.

API: construct `FocusStatusSummary.Snapshot(active, completed, recoveredPaused,
elapsedMs, remainingMs, countdownTotalMs, selectedUsageMs, budgetMs,
virtualPoints, observationEnabled, usagePermission)` and call `format(snapshot)`.
`UNKNOWN = -1` is allowed only for countdown remainder/total and selected usage.
`hasCountdown()` and `progressPercent()` expose explicit availability; progress
returns `-1` when the original total is unknown. Validation rejects contradictory
completion/recovery, negative or oversized durations, invalid totals and points.
Accumulated focus and budget formatting safely handle `Long.MAX_VALUE` without
addition or multiplication overflow.

Foreground adapter, using the current repository API:

```java
repository.completeTimedIfDue();
long now = SystemClock.elapsedRealtime();
FocusSession session = repository.session;
boolean permitted = FocusRepository.usageGranted(this);
FocusStatusSummary.Snapshot snapshot = new FocusStatusSummary.Snapshot(
    session.isActive(), session.isCompleted(), repository.interrupted,
    session.elapsed(now), session.remainingMs(now), session.countdownTotalMs(),
    repository.usage(), repository.budgetMs, repository.ledger.points(),
    repository.observe, permitted);
result.setText(FocusStatusSummary.format(snapshot));
```

Run this capture together on the main thread, after the existing explicit Explain
review. Read the same monotonic `now` for elapsed and remainder. When usage is not
available or the repository read fails, provide `UNKNOWN`; do not substitute zero.
A supplied saved usage value with observation off or permission absent is clearly
labelled saved and not live. Permission presence alone does not prove current
selected-app foreground or a successful fresh observation. The summary makes no
such claim. Negative restored usage is invalid and should be reported unavailable
by an adapter, rather than displayed as real usage.

Recorded countdown metadata is now present in the research app source: new timed
sessions retain the original duration through pause/resume/completion, and persist
`countdownTotalCheckpoint`. Legacy or corrupt optional totals remain unknown.
Accumulated elapsed includes earlier runs and survives countdown replacement, so
it cannot supply the countdown denominator. `countdownTotalMs()` supplies a
validated genuine total or -1; progress is `(total - remaining) / total`, rounded
down. Recovery remains paused and excludes unverified post-checkpoint time.
This source integration is not proof of installed UI or live voice behavior.

Completed countdowns report paused completion; an active zero remainder reports
that completion awaits the app's timer check. Open-ended focus explicitly has no
remaining time/progress. Elapsed/usage are shown in whole seconds (subsecond
positive durations say less than 1s); remaining rounds up so a positive remainder
never appears as zero. Progress rounds down to a whole percentage. Virtual points
are explicitly simulated. Observation/budget are current policy context, not an
invented reason for a past nudge. No raw selected-app name or user goal is included.

Nine JVM tests cover open-ended, paused/resumed, completed/recovered,
the actual existing FocusSession lifecycle adapter, overdue-but-not-finalized,
unknown/saved usage, extreme numeric bounds and corrupt state. Compile the helper
and test with the existing `FocusSession.java`, Java 17 and cached JUnit 4.13.2;
run `org.junit.runner.JUnitCore dev.focuspilot.prototype.FocusStatusSummaryTest`.
Generated classes belong in ignored `build/classes`. These are JVM utility checks,
not Android UI, voice, permission, or physical-device evidence.
