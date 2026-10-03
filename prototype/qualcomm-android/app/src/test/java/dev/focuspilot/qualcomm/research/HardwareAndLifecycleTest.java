package dev.focuspilot.qualcomm.research;

/** Standard-library host checks; no Android/vendor SDK/runtime/model access. */
public final class HardwareAndLifecycleTest {
    private static int checks;
    private static HardwareGate.Assessment supported() { return HardwareGate.assess(36, "SM8850", "arm64-v8a", true, 4096); }
    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    private static void fixture(Runnable check) { check.run(); checks++; }
    public static void main(String[] args) {
        fixture(() -> {
            for (String mode : new String[]{"cpu", "npu", "hybrid"}) {
                ProbeLifecycle gate = new ProbeLifecycle(); gate.enterForeground();
                int[] simulatedInitCalls = {0};
                if (gate.begin(HardwareGate.assess(36, "SM7635", "arm64-v8a", true, 4096), mode) != null) simulatedInitCalls[0]++;
                require(simulatedInitCalls[0] == 0 && !gate.isBusy(), "Unsupported SoC admitted native initialization");
            }
        });
        fixture(() -> {
            require(!HardwareGate.assess(30, "SM8850", "arm64-v8a", true, 4096).allowed, "Missing public SoC API");
            require(!HardwareGate.assess(36, "SM8850", "x86_64", true, 4096).allowed, "Wrong ABI");
            require(!HardwareGate.assess(36, "SM8850", "arm64-v8a", false, 4096).allowed, "32-bit process");
            require(!HardwareGate.assess(36, "SM8850-extra", "arm64-v8a", true, 4096).allowed, "Substring SoC accepted");
            require(!HardwareGate.assess(36, null, "arm64-v8a", true, 4096).allowed, "Missing SoC");
        });
        fixture(() -> {
            for (long page : new long[]{-1, 0, 8192, 16384, 65536})
                require(!HardwareGate.assess(36, "SM8850", "arm64-v8a", true, page).allowed, "Unsafe/unknown vendor page size admitted");
            require(supported().allowed && HardwareGate.assess(35, "SM8750", "arm64-v8a", true, 4096).allowed, "Supported 4K prerequisite rejected");
        });
        fixture(() -> {
            ProbeLifecycle gate = new ProbeLifecycle();
            require(gate.begin(supported(), "cpu") == null, "Background starts are inert");
            gate.enterForeground();
            for (String mode : new String[]{null, "", "auto", "CPU", "Select requested backend"})
                require(gate.begin(supported(), mode) == null, "Implicit mode admitted");
            require(!gate.isBusy(), "Invalid controls acquired ownership");
        });
        fixture(() -> {
            ProbeLifecycle gate = new ProbeLifecycle(); gate.enterForeground();
            ProbeLifecycle.Request first = gate.begin(supported(), "hybrid");
            require(first != null && gate.mayStart(first), "Explicit supported request missing");
            require(gate.begin(supported(), "cpu") == null, "Concurrent request admitted");
            gate.cancel();
            require(first.isCancelled() && !gate.mayStart(first) && !gate.mayDeliver(first), "Queued cancellation lost");
            require(gate.isBusy(), "Cancel prematurely released native ownership");
            gate.finish(first);
            ProbeLifecycle.Request retry = gate.begin(supported(), "cpu");
            require(retry != null && gate.mayStart(retry) && !retry.isCancelled(), "Cancellation leaked into next explicit request");
        });
        fixture(() -> {
            ProbeLifecycle gate = new ProbeLifecycle(); gate.enterForeground();
            ProbeLifecycle.Request first = gate.begin(supported(), "npu");
            gate.leaveForeground(); gate.enterForeground();
            require(!gate.mayStart(first) && !gate.mayDeliver(first), "Background/re-entry revived old request");
            require(gate.begin(supported(), "cpu") == null, "Old native worker still owns cleanup");
            gate.finish(first);
            require(gate.begin(supported(), "cpu") != null, "Fresh explicit request after cleanup rejected");
        });
        fixture(() -> {
            ProbeLifecycle gate = new ProbeLifecycle(); gate.enterForeground();
            ProbeLifecycle.Request old = gate.begin(supported(), "cpu"); gate.finish(old);
            require(gate.mayDeliver(old), "Valid finished result lost");
            ProbeLifecycle.Request replacement = gate.begin(supported(), "npu");
            gate.finish(old);
            require(gate.isBusy() && gate.mayStart(replacement) && !gate.mayDeliver(old), "Late callback stole replacement ownership/result");
        });
        fixture(() -> {
            ProbeLifecycle gate = new ProbeLifecycle(); gate.enterForeground();
            ProbeLifecycle.Request done = gate.begin(supported(), "cpu"); gate.finish(done);
            gate.leaveForeground(); gate.enterForeground();
            require(!gate.mayDeliver(done), "Finished but undelivered output survived background epoch");
        });
        fixture(() -> {
            ProbeLifecycle gate = new ProbeLifecycle(); gate.enterForeground();
            ProbeLifecycle.Request pending = gate.begin(supported(), "cpu"); gate.finish(pending);
            require(gate.mayDeliver(pending), "Pending output disappeared before Cancel");
            gate.cancel();
            require(!gate.mayDeliver(pending), "Visible Cancel failed after worker completion/before UI delivery");
            require(gate.begin(supported(), "npu") != null, "Pending delivery cancellation blocked fresh explicit request");
        });
        fixture(() -> {
            ProcessProbeOwner shared = new ProcessProbeOwner();
            ProbeLifecycle oldScreen = new ProbeLifecycle(); oldScreen.enterForeground();
            ProbeLifecycle.Request old = oldScreen.begin(supported(), "cpu");
            ProcessProbeOwner.Lease oldLease = shared.acquire();
            oldScreen.leaveForeground();
            ProbeLifecycle newScreen = new ProbeLifecycle(); newScreen.enterForeground();
            require(newScreen.begin(supported(), "npu") != null, "Fresh screen admission setup");
            require(shared.acquire() == null, "Rotation admitted overlapping native ownership");
            oldScreen.finish(old); // A UI-local finish alone must not release global ownership.
            require(shared.acquire() == null, "Local lifecycle stole worker-owned process lease");
            shared.release(oldLease);
            ProcessProbeOwner.Lease replacement = shared.acquire();
            require(replacement != null, "No admission after actual old worker release");
            shared.release(oldLease);
            require(shared.isBusy(), "Late old release stole replacement ownership");
            shared.release(replacement);
            require(!shared.isBusy(), "Replacement cleanup did not release ownership");
        });
        fixture(() -> {
            ProcessProbeOwner shared = new ProcessProbeOwner();
            ProcessProbeOwner.Lease uncertainCleanup = shared.acquire();
            shared.quarantine(uncertainCleanup); shared.release(uncertainCleanup);
            require(shared.isBusy() && shared.isQuarantined() && shared.acquire() == null,
                    "Thrown/nonzero cleanup reopened uncertain native ownership");
            require(new ProcessProbeOwner().acquire() != null, "Fresh process simulation inherited quarantine");
        });
        fixture(() -> {
            String[] labels = SyntheticCases.labels(); labels[0] = "Run arbitrary action";
            require(SyntheticCases.count() == 5 && SyntheticCases.at(0).equals("Start focus"), "External labels changed fixed cases");
            require(SyntheticCases.at(4).equals("Send a payment to my friend"), "Historical synthetic scope changed");
            try { SyntheticCases.at(5); throw new AssertionError("Invalid case accepted"); } catch (IllegalArgumentException expected) {}
        });
        System.out.println("{\"passed\":true,\"fixture_groups\":" + checks + ",\"vendor_runtime_accessed\":false,\"model_accessed\":false}");
    }
}
