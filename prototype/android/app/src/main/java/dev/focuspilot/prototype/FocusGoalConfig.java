package dev.focuspilot.prototype;

/** User-declared targets. An empty duration means unknown, never a guessed limit. */
public final class FocusGoalConfig {
    public final String goal;
    public final long plannedMs, continuousMs;
    private FocusGoalConfig(String goal,long plannedMs,long continuousMs) {
        this.goal=goal;this.plannedMs=plannedMs;this.continuousMs=continuousMs;
    }
    public static FocusGoalConfig parse(String goal,String plannedMinutes,String continuousMinutes) {
        String clean=goal==null?"":goal.trim();
        if(clean.length()>120 || clean.codePoints().anyMatch(Character::isISOControl))
            throw new IllegalArgumentException("Use a goal up to 120 characters without control characters.");
        return new FocusGoalConfig(clean,minutes(plannedMinutes),minutes(continuousMinutes));
    }
    private static long minutes(String value) {
        String clean=value==null?"":value.trim();
        if(clean.isEmpty() || clean.equals("0")) return 0;
        if(!clean.matches("[0-9]{1,4}")) throw new IllegalArgumentException("Targets must be whole minutes, 1–1440; leave blank if unknown.");
        int number=Integer.parseInt(clean);
        if(number<1 || number>1440) throw new IllegalArgumentException("Targets must be whole minutes, 1–1440; leave blank if unknown.");
        return number*60_000L;
    }
}
