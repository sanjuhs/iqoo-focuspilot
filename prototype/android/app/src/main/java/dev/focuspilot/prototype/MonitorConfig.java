package dev.focuspilot.prototype;

public final class MonitorConfig {
    public static boolean valid(String packageName,long budgetMs) {
        return packageName!=null && packageName.length()<=255 && packageName.matches("[A-Za-z][A-Za-z0-9_]*(?:\\.[A-Za-z][A-Za-z0-9_]*)+") && budgetMs>=60_000 && budgetMs<=7_200_000;
    }
}
