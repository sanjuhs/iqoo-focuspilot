package dev.focuspilot.prototype;

/** Hand-set monotonic positive-weight policy; neither a trained network nor an LLM. */
public final class DecisionPolicy {
    public static final long COOLDOWN_MS = 60_000;
    public static final class Result {
        public final double excessContribution, durationContribution, score;
        public final boolean nudge;
        Result(double excess, double duration, boolean eligible) {
            excessContribution = excess; durationContribution = duration;
            score = excess + duration; nudge = eligible && score >= 0.65;
        }
        public String explanation() {
            return String.format(java.util.Locale.US,
                "Excess × 0.80 = %.2f\nDuration × 0.20 = %.2f\nTotal %.2f / threshold 0.65\nPositive weights · hand-set · not trained",
                excessContribution, durationContribution, score);
        }
    }
    public Result evaluate(long usedMs, long budgetMs, boolean active, long now, long lastNudge) {
        if (budgetMs <= 0 || usedMs < 0) throw new IllegalArgumentException("Invalid usage/budget");
        double excess = Math.min(1.0, Math.max(0.0, (double)(usedMs - budgetMs) / budgetMs));
        double duration = Math.min(1.0, (double) usedMs / budgetMs);
        boolean cooled = lastNudge < 0 || (now >= lastNudge && now - lastNudge >= COOLDOWN_MS);
        return new Result(excess * 0.8, duration * 0.2, active && usedMs > budgetMs && cooled);
    }
}
