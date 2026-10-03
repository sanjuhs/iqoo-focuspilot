package dev.focuspilot.prototype;

/** Visual availability only. No Android, permissions, actions, observation or startup. */
public final class CompanionAvailability {
    public enum Effect { NONE, ATTACH, DETACH, STOP }
    private enum State { STOPPED, DISPLAYED, DORMANT }
    private State state = State.STOPPED;
    private boolean returnAfterUnlock;
    private long lease;

    /** Only a reviewed foreground Show can begin a session; repeated Show cannot change its mode. */
    public Effect begin(boolean requestedReturn, boolean permanentReady, boolean displayReady) {
        if (state != State.STOPPED || !permanentReady || !displayReady) return Effect.NONE;
        returnAfterUnlock = requestedReturn; state = State.DISPLAYED; lease++;
        return Effect.ATTACH;
    }
    public Effect suspend(boolean permanentReady) {
        if (state == State.STOPPED) return Effect.NONE;
        if (!permanentReady || !returnAfterUnlock) return stop();
        if (state == State.DORMANT) return Effect.NONE;
        state = State.DORMANT; return Effect.DETACH;
    }
    /** Protected USER_PRESENT, or separately reviewed manual Show, with actual current guards. */
    public Effect resume(long expectedLease, boolean permanentReady, boolean displayReady) {
        if (expectedLease != lease || state == State.STOPPED) return Effect.NONE;
        if (!permanentReady) return stop();
        if (state != State.DORMANT || !displayReady) return Effect.NONE;
        state = State.DISPLAYED; return Effect.ATTACH;
    }
    public Effect stop() {
        if (state == State.STOPPED) return Effect.NONE;
        state = State.STOPPED; returnAfterUnlock = false; lease++; return Effect.STOP;
    }
    public long lease() { return lease; }
    public boolean isRunning() { return state != State.STOPPED; }
    public boolean isDormant() { return state == State.DORMANT; }
    public boolean returnAfterUnlockActive() { return isRunning() && returnAfterUnlock; }
}
