package dev.focuspilot.prototype;

/** Candidate pre-event formatter. Reports supplied app facts, never model conclusions/actions. */
public final class FocusStatusSummary {
    public static final long UNKNOWN = -1;
    public static final long MAX_COUNTDOWN_MS = 7_200_000;

    private FocusStatusSummary() {}

    /**
     * Capture these values together on the app's main thread after finalizing any due timer.
     * elapsedMs is accumulated active focus across runs, not this countdown's elapsed time.
     * countdownTotalMs may be UNKNOWN for a legacy checkpoint; new targets record their duration.
     * selectedUsageMs may be UNKNOWN: missing observation must not become an invented zero.
     * recoveredPaused identifies an interrupted process's paused checkpoint, not all pauses.
     */
    public static final class Snapshot {
        public final boolean active, completed, recoveredPaused, observationEnabled, usagePermission;
        public final long elapsedMs, remainingMs, countdownTotalMs, selectedUsageMs, budgetMs;
        public final int virtualPoints;

        public Snapshot(boolean active, boolean completed, boolean recoveredPaused,
                long elapsedMs, long remainingMs, long countdownTotalMs,
                long selectedUsageMs, long budgetMs, int virtualPoints,
                boolean observationEnabled, boolean usagePermission) {
            if (elapsedMs < 0 || remainingMs < UNKNOWN || remainingMs > MAX_COUNTDOWN_MS
                    || countdownTotalMs < UNKNOWN || countdownTotalMs > MAX_COUNTDOWN_MS
                    || selectedUsageMs < UNKNOWN || budgetMs <= 0
                    || virtualPoints < 0 || virtualPoints > 100)
                throw new IllegalArgumentException("Invalid focus summary values");
            if (remainingMs == UNKNOWN && (countdownTotalMs != UNKNOWN || completed))
                throw new IllegalArgumentException("Open-ended focus has no countdown or completion");
            if (countdownTotalMs != UNKNOWN && (countdownTotalMs < 1000 || remainingMs > countdownTotalMs))
                throw new IllegalArgumentException("Recorded countdown total must contain the remainder");
            if (completed && (active || remainingMs != 0) || recoveredPaused && active)
                throw new IllegalArgumentException("Completion and checkpoint recovery must be paused");
            this.active = active; this.completed = completed; this.recoveredPaused = recoveredPaused;
            this.elapsedMs = elapsedMs; this.remainingMs = remainingMs;
            this.countdownTotalMs = countdownTotalMs; this.selectedUsageMs = selectedUsageMs;
            this.budgetMs = budgetMs; this.virtualPoints = virtualPoints;
            this.observationEnabled = observationEnabled; this.usagePermission = usagePermission;
        }

        public boolean hasCountdown() { return remainingMs != UNKNOWN; }
        /** -1 means the original countdown duration was not recorded. */
        public int progressPercent() {
            return countdownTotalMs == UNKNOWN ? -1
                    : (int) ((countdownTotalMs - remainingMs) * 100 / countdownTotalMs);
        }
    }

    public static String format(Snapshot s) {
        if (s == null) throw new IllegalArgumentException("Focus snapshot required");
        StringBuilder out = new StringBuilder("Focus: ");
        out.append(s.completed ? "countdown finished; paused" : s.active ? "active" : "paused");
        out.append(".\nFocused time across sessions: ").append(floorDuration(s.elapsedMs)).append('.');
        if (s.recoveredPaused)
            out.append("\nRecovered your last saved checkpoint as paused. Time since that save is not counted.");
        if (!s.hasCountdown()) {
            out.append(s.active ? "\nNo countdown is set. Focus continues until you pause it."
                    : "\nNo countdown is set. Focus is paused.");
        } else {
            out.append("\nCountdown: ").append(ceilDuration(s.remainingMs)).append(" left.");
            if (s.countdownTotalMs == UNKNOWN) {
                out.append(" The original duration of this saved countdown is unknown.");
            } else {
                out.append(" Total: ").append(floorDuration(s.countdownTotalMs)).append("; progress: ")
                        .append(s.progressPercent()).append("%.");
            }
            if (s.active && s.remainingMs == 0)
                out.append(" The deadline has passed; the app is finishing this countdown.");
        }
        out.append("\nApp usage: ")
                .append(s.selectedUsageMs == UNKNOWN ? "unavailable" : floorDuration(s.selectedUsageMs));
        if (s.selectedUsageMs != UNKNOWN && (!s.active || !s.observationEnabled || !s.usagePermission))
            out.append(" (saved)");
        out.append(". Budget: ").append(floorDuration(s.budgetMs)).append(". Balance: ")
                .append(s.virtualPoints).append("/100 virtual points.");
        out.append("\nUsage observation: ").append(!s.observationEnabled ? "off" : !s.usagePermission
                ? "needs Usage Access" : "on")
                .append(". This is your current status; it does not identify the cause of an earlier reminder.");
        return out.toString();
    }

    private static String floorDuration(long ms) {
        return ms > 0 && ms < 1000 ? "less than 1s" : seconds(ms / 1000);
    }
    private static String ceilDuration(long ms) {
        // Division before addition avoids overflow even for long durations.
        return seconds(ms / 1000 + (ms % 1000 == 0 ? 0 : 1));
    }
    private static String seconds(long total) {
        long h = total / 3600, m = total / 60 % 60, s = total % 60;
        return h > 0 ? h + "h " + m + "m " + s + "s" : m > 0 ? m + "m " + s + "s" : s + "s";
    }
}
