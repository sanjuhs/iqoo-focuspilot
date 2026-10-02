package dev.focuspilot.prototype;

/** Foreground/freshness gate for baseline nudges; independent of optional NN features. */
public final class ObservedNudgeGate {
    private ObservedNudgeGate() {}
    public static boolean eligible(ObservationSnapshot snapshot,long expectedScopeId,long nowElapsed,
            boolean consent,boolean usagePermission,boolean activeFocus) {
        return consent && usagePermission && activeFocus && snapshot!=null && snapshot.scopeId==expectedScopeId &&
            nowElapsed>=snapshot.observedAtElapsed && nowElapsed-snapshot.observedAtElapsed<=ObservationSnapshot.MAX_AGE_MS &&
            snapshot.timestampAlignmentValid && snapshot.summary!=null && snapshot.summary.complete && snapshot.summary.selectedForeground;
    }
}
