package dev.focuspilot.qualcomm.research;

import java.util.Locale;

/** Pure prerequisite check. It does not load or reference any vendor SDK class. */
public final class HardwareGate {
    private HardwareGate() {}
    public static final class Assessment {
        public final boolean allowed;
        public final String reason;
        private Assessment(boolean allowed, String reason) { this.allowed = allowed; this.reason = reason; }
    }
    public static Assessment assess(int api, String soc, String abi, boolean process64Bit, long pageSize) {
        if (api < 31) return new Assessment(false, "API 31+ required for the public SoC guard.");
        if (!"arm64-v8a".equals(abi) || !process64Bit)
            return new Assessment(false, "An arm64 process is required.");
        if (pageSize != 4096)
            return new Assessment(false, "This pinned SDK is restricted to 4096-byte pages: its vendor GNU_RELRO layout has an unresolved 16 KiB runtime risk. No SDK/native initialization is permitted.");
        String normalized = soc == null ? "" : soc.trim().toUpperCase(Locale.ROOT);
        if (!normalized.equals("SM8750") && !normalized.equals("SM8850"))
            return new Assessment(false, "This SoC is outside the SDK validated list (SM8750/SM8850). No SDK/native initialization is permitted, including CPU mode.");
        return new Assessment(true, "Prerequisites pass; hardware execution and NPU operator coverage remain unverified.");
    }
    public static boolean explicitMode(String mode) {
        return "cpu".equals(mode) || "npu".equals(mode) || "hybrid".equals(mode);
    }
}
