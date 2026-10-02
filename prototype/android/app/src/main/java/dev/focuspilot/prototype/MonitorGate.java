package dev.focuspilot.prototype;

/** All product prerequisites must hold before an explicit visible-screen start. */
public final class MonitorGate {
    public static boolean canStart(boolean visible, boolean optedIn, boolean usageAccess, boolean notifications) {
        return visible && optedIn && usageAccess && notifications;
    }
}
