package dev.focuspilot.qualcomm.research;

/** Inert ownership/result gate. Cancellation is sticky for this request, not the next one. */
public final class ProbeLifecycle {
    public static final class Request {
        public final long id;
        private final long epoch;
        private volatile boolean cancelled;
        private Request(long id, long epoch) { this.id = id; this.epoch = epoch; }
        public boolean isCancelled() { return cancelled; }
    }
    private boolean foreground;
    private long epoch, nextId;
    private Request active, latest;

    public synchronized void enterForeground() { foreground = true; }
    public synchronized void leaveForeground() {
        foreground = false; epoch++;
        if (active != null) active.cancelled = true;
    }
    public synchronized Request begin(HardwareGate.Assessment hardware, String mode) {
        if (!foreground || active != null || hardware == null || !hardware.allowed || !HardwareGate.explicitMode(mode))
            return null;
        active = latest = new Request(++nextId, epoch);
        return active;
    }
    public synchronized void cancel() {
        if (active != null) active.cancelled = true;
        // The native worker can finish before its main-thread result is delivered.
        // A visible Cancel in that gap must invalidate the pending result as well.
        if (latest != null) latest.cancelled = true;
    }
    public synchronized boolean mayStart(Request request) {
        return request != null && request == active && foreground && request.epoch == epoch && !request.cancelled;
    }
    public synchronized boolean mayDeliver(Request request) {
        return request != null && request == latest && foreground && request.epoch == epoch && !request.cancelled;
    }
    public synchronized void finish(Request request) { if (request == active) active = null; }
    public synchronized boolean isBusy() { return active != null; }
}
