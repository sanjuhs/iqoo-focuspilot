package dev.focuspilot.qualcomm.research;

/** Process-wide admission retained across Activity destruction/recreation.
 * A worker releases its lease only after native handle cleanup, never on UI stop.
 */
public final class ProcessProbeOwner {
    private static final ProcessProbeOwner SHARED = new ProcessProbeOwner();
    public static ProcessProbeOwner shared() { return SHARED; }
    public static final class Lease { private Lease() {} }
    private Lease active;
    private boolean quarantined;
    public synchronized Lease acquire() {
        if (active != null) return null;
        active = new Lease(); return active;
    }
    public synchronized void release(Lease lease) { if (!quarantined && lease != null && lease == active) active = null; }
    public synchronized void quarantine(Lease lease) { if (lease != null && lease == active) quarantined = true; }
    public synchronized boolean isQuarantined() { return quarantined; }
    public synchronized boolean isBusy() { return active != null; }
}
