package dev.focuspilot.prototype;

/** Engine initialization ownership, separate from each explicitly requested readback. No speech starts here. */
public final class ReadbackInitialization {
    public enum Admission { START_ENGINE, WAIT, SPEAK, REJECT }
    private enum Phase { EMPTY, INITIALIZING, READY, FAILED, CLOSED }
    private Phase phase=Phase.EMPTY;
    private long engineEpoch, waitingToken;

    public synchronized Admission request(long token) {
        if(token<=0 || phase==Phase.CLOSED)return Admission.REJECT;
        if(phase==Phase.READY)return Admission.SPEAK;
        waitingToken=token;
        if(phase==Phase.INITIALIZING)return Admission.WAIT;
        if(engineEpoch==Long.MAX_VALUE){waitingToken=0;return Admission.REJECT;}
        engineEpoch++;phase=Phase.INITIALIZING;return Admission.START_ENGINE;
    }

    public synchronized long engineEpoch() { return engineEpoch; }
    public synchronized boolean ownsInitialization(long epoch) {
        return epoch>0 && epoch==engineEpoch && phase==Phase.INITIALIZING;
    }

    /** Complete one engine once; return only the latest explicit waiting request, or zero. */
    public synchronized long complete(long epoch,boolean ready) {
        if(!ownsInitialization(epoch))return 0;
        phase=ready?Phase.READY:Phase.FAILED;
        long token=waitingToken;waitingToken=0;return token;
    }

    public synchronized void cancelRequest(long token) {
        if(waitingToken==token)waitingToken=0;
    }
    public synchronized void cancelRequests() { waitingToken=0; }
    public synchronized void close() { waitingToken=0;phase=Phase.CLOSED; }
}
