package dev.focuspilot.prototype;

/** Demo points only. No payment API or money movement exists. */
public final class VirtualLedger {
    private int points = 100;
    private long lastNudge = -1;
    public int points() { return points; }
    public long lastNudge() { return lastNudge; }
    public boolean apply(DecisionPolicy.Result result, long now) {
        if (!result.nudge || (lastNudge >= 0 && (now < lastNudge || now - lastNudge < DecisionPolicy.COOLDOWN_MS))) return false;
        points = Math.max(0, points - 5); lastNudge = now; return true;
    }
    public void reset() { points = 100; lastNudge = -1; }
    public void restore(int savedPoints, long savedNudge, long now) { points = Math.max(0, Math.min(100, savedPoints)); lastNudge = savedNudge <= now ? savedNudge : -1; }
}
