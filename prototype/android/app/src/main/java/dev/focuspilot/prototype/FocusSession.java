package dev.focuspilot.prototype;

/** Monotonic session duration; deliberately not restored after process death. */
public final class FocusSession {
    private long accumulatedMs, startedAt;
    private boolean active;
    public void start(long now) { if (!active) { startedAt = now; active = true; } }
    public void pause(long now) { if (active) { accumulatedMs += Math.max(0, now - startedAt); active = false; } }
    public long elapsed(long now) { return accumulatedMs + (active ? Math.max(0, now - startedAt) : 0); }
    public boolean isActive() { return active; }
    public void reset() { accumulatedMs = 0; active = false; }
    public void restorePaused(long elapsedMs) { accumulatedMs = Math.max(0, elapsedMs); active = false; }
}
