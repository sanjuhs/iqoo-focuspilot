package dev.focuspilot.prototype;

import android.app.usage.UsageEvents;
import android.app.usage.UsageStatsManager;
import android.content.Context;

/** Queries OS history only during visible dashboard refreshes; never stores raw app events. */
public final class UsageReader {
    public static long read(Context context, String selectedPackage, long since, long now) {
        if (since <= 0 || now <= since) return 0;
        UsageStatsManager manager = (UsageStatsManager) context.getSystemService(Context.USAGE_STATS_SERVICE);
        UsageEvents events = manager.queryEvents(Math.max(0, since - 300_000), now);
        if (events == null) return 0;
        UsageEvents.Event event = new UsageEvents.Event();
        String foreground = null;
        long cursor = since, total = 0;
        while (events.hasNextEvent()) {
            events.getNextEvent(event);
            int type = event.getEventType();
            if (type != UsageEvents.Event.ACTIVITY_RESUMED && type != UsageEvents.Event.ACTIVITY_PAUSED
                    && type != UsageEvents.Event.SCREEN_NON_INTERACTIVE) continue;
            long timestamp = event.getTimeStamp();
            if (timestamp >= since) {
                if (selectedPackage.equals(foreground)) total += Math.max(0, timestamp - cursor);
                cursor = timestamp;
            }
            if (type == UsageEvents.Event.ACTIVITY_RESUMED) foreground = event.getPackageName();
            else if (type == UsageEvents.Event.SCREEN_NON_INTERACTIVE || event.getPackageName().equals(foreground)) foreground = null;
        }
        if (selectedPackage.equals(foreground)) total += Math.max(0, now - cursor);
        return Math.min(total, now - since);
    }
}
