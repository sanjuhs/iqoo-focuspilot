package dev.focuspilot.prototype;

/** Monotonic active time, optional bounded target, and explicitly paused recovery. */
public final class FocusSession {
    public static final long MIN_TIMED_MS=1000,MAX_TIMED_MS=7_200_000;
    private long accumulatedMs, startedAt, lastNow, remaining=-1, countdownTotal=-1, generation;
    private boolean active,completed;
    private long clock(long now) { lastNow=Math.max(lastNow,Math.max(0,now));return lastNow; }
    private long activeElapsed(long now) {
        long spent=active?Math.max(0,now-startedAt):0;
        return remaining>=0?Math.min(spent,remaining):spent;
    }
    public void start(long now) {
        long current=clock(now);
        if(!active) {
            if(completed) {remaining=-1;countdownTotal=-1;completed=false;}
            startedAt=current;active=true;generation++;
        }
    }
    /** A new explicit duration replaces the old target, preserving prior active time. */
    public void startTimed(long now,long durationMs) {
        if(durationMs<MIN_TIMED_MS || durationMs>MAX_TIMED_MS)throw new IllegalArgumentException("Focus duration must be 1 second to 120 minutes");
        long current=clock(now);pause(current);remaining=durationMs;countdownTotal=durationMs;completed=false;startedAt=current;active=true;generation++;
    }
    public void pause(long now) {
        long current=clock(now);
        if(active) {
            long spent=activeElapsed(current);accumulatedMs+=spent;
            if(remaining>=0) {remaining-=spent;completed=remaining==0;}
            active=false;generation++;
        }
    }
    public long elapsed(long now) { return accumulatedMs+activeElapsed(clock(now)); }
    public boolean isActive() { return active; }
    public boolean isTimed() { return remaining>=0; }
    public boolean isCompleted() { return completed; }
    /** Original explicitly recorded duration, or -1 for open-ended/legacy unknown metadata. */
    public long countdownTotalMs() { return countdownTotal; }
    /** -1 means open-ended. Paused timed sessions retain their unspent remainder. */
    public long remainingMs(long now) { return remaining<0?-1:Math.max(0,remaining-activeElapsed(clock(now))); }
    public long deadlineElapsedMs() { return active && isTimed()?startedAt+remaining:-1; }
    public long generation() { return generation; }
    public boolean isDue(long now) { return active && isTimed() && remainingMs(now)==0; }
    public boolean completeIfDue(long now) { if(!isDue(now))return false;pause(now);return true; }
    public void reset() { accumulatedMs=0;active=false;remaining=-1;countdownTotal=-1;completed=false;generation++; }
    public void restorePaused(long elapsedMs) { restorePaused(elapsedMs,false,0,false); }
    public void restorePaused(long elapsedMs,boolean timed,long savedRemaining,boolean savedCompleted) {
        restorePaused(elapsedMs,timed,savedRemaining,savedCompleted,-1);
    }
    /** Invalid optional target metadata never changes the legacy paused remainder/completion recovery. */
    public void restorePaused(long elapsedMs,boolean timed,long savedRemaining,boolean savedCompleted,long savedTotal) {
        accumulatedMs=Math.max(0,elapsedMs);active=false;lastNow=0;startedAt=0;generation++;
        remaining=timed && savedRemaining>=0 && savedRemaining<=MAX_TIMED_MS?savedRemaining:-1;
        countdownTotal=remaining>=0 && savedTotal>=MIN_TIMED_MS && savedTotal<=MAX_TIMED_MS
            && savedTotal>=savedRemaining?savedTotal:-1;
        completed=remaining>=0 && (remaining==0 || savedCompleted);
        if(completed)remaining=0;
    }
}
