package dev.focuspilot.prototype;

/** Pure lifecycle gate for asynchronous readback callbacks; this does not start speech. */
public final class ReadbackState {
    private boolean foreground, closed, active;
    private long epoch;
    private String utteranceId;

    public synchronized void resume() { if(!closed) foreground=true; }

    /** A new request replaces the previous one. Zero means no request was accepted. */
    public synchronized long begin() {
        if(!foreground || closed) return 0;
        active=false;
        utteranceId=null;
        // Never wrap to zero/negative or reuse a token after exhausting the positive range.
        if(epoch==Long.MAX_VALUE) return 0;
        epoch++;
        active=true;
        return epoch;
    }

    /** Bind engine events to this utterance as well as the listener's request token. */
    public synchronized long beginWithUtterance(String prefix) {
        if(prefix==null || prefix.isEmpty()) return 0;
        long token=begin();
        if(token>0) utteranceId=prefix+token;
        return token;
    }

    public synchronized String utteranceId(long token) {
        return owns(token)?utteranceId:null;
    }

    public synchronized boolean ownsUtterance(long token,String id) {
        return owns(token) && utteranceId!=null && utteranceId.equals(id);
    }

    /** A replaced engine listener must not relabel an older utterance's event. */
    public synchronized boolean finishUtterance(long token,String id) {
        return ownsUtterance(token,id) && finish(token);
    }

    public synchronized boolean owns(long token) {
        return token>0 && token==epoch && active && foreground && !closed;
    }

    /** Accept exactly one terminal callback belonging to the current request. */
    public synchronized boolean finish(long token) {
        if(!owns(token)) return false;
        active=false;
        return true;
    }

    public synchronized void cancel() { active=false; }
    public synchronized void stop() { foreground=false;active=false; }
    public synchronized void close() { closed=true;foreground=false;active=false; }
    public synchronized boolean active() { return active; }
}
