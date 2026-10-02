package dev.focuspilot.prototype;

/** Explicit feedback for an actual hand-set-rule nudge. In-memory and scope-local. */
public final class ScopedNudgeFeedback {
    private long latest=-1,deferred=-1;
    private int count;
    public void reset() { latest=-1;deferred=-1;count=0; }
    public void recordActualNudge(long now) { if(now>=0) latest=now; }
    public int count() { return count; }
    public boolean defer(long now,boolean scopeEligible) {
        if(!scopeEligible || latest<0 || deferred==latest || now<latest || now-latest>DecisionPolicy.COOLDOWN_MS) return false;
        count++;deferred=latest;return true;
    }
}
