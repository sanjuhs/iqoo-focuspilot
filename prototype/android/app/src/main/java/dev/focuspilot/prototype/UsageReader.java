package dev.focuspilot.prototype;

import android.app.usage.UsageEvents;
import android.app.usage.UsageStatsManager;
import android.content.Context;
import java.util.ArrayList;

/** Opt-in dashboard/visible-service queries. Never persists raw events or other app identities. */
public final class UsageReader {
    public static long read(Context context, String selectedPackage, long since, long now) {
        if (since <= 0 || now <= since) return 0;
        UsageStatsManager manager = (UsageStatsManager) context.getSystemService(Context.USAGE_STATS_SERVICE);
        if (manager == null) return 0;
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
            else if (type == UsageEvents.Event.SCREEN_NON_INTERACTIVE || (foreground != null && foreground.equals(event.getPackageName()))) foreground = null;
        }
        if (selectedPackage.equals(foreground)) total += Math.max(0, now - cursor);
        return Math.min(total, now - since);
    }
    /** Independent strict observation for the shadow network; legacy budget accounting is unchanged. */
    public static SelectedAppObservation.Summary observe(Context context,String selectedPackage,long since,long now) {
        if(since<=0 || now<since) return SelectedAppObservation.missing("Invalid active observation interval");
        if(!FocusRepository.usageGranted(context)) return SelectedAppObservation.missing("Usage permission unavailable");
        UsageStatsManager manager=(UsageStatsManager)context.getSystemService(Context.USAGE_STATS_SERVICE);
        if(manager==null) return SelectedAppObservation.missing("Usage service unavailable");
        try {
            UsageEvents events=manager.queryEvents(Math.max(0,since-300_000),now);
            if(events==null) return SelectedAppObservation.missing("OS returned no usage stream (possibly locked user)");
            ArrayList<SelectedAppObservation.Event> boundaries=new ArrayList<>();
            UsageEvents.Event event=new UsageEvents.Event();
            while(events.hasNextEvent()) {
                events.getNextEvent(event);
                int type=event.getEventType();
                SelectedAppObservation.Kind kind=null;
                // API29 renamed these values, but the aliases (1/2) are supported on API28.
                if(type==UsageEvents.Event.ACTIVITY_RESUMED) kind=selectedPackage.equals(event.getPackageName())?
                    SelectedAppObservation.Kind.SELECTED_RESUMED:SelectedAppObservation.Kind.OTHER_RESUMED;
                else if(type==UsageEvents.Event.ACTIVITY_PAUSED && selectedPackage.equals(event.getPackageName())) kind=SelectedAppObservation.Kind.SELECTED_PAUSED;
                else if(type==UsageEvents.Event.SCREEN_NON_INTERACTIVE) kind=SelectedAppObservation.Kind.SCREEN_OFF;
                else if(type==UsageEvents.Event.DEVICE_SHUTDOWN || type==UsageEvents.Event.DEVICE_STARTUP) kind=SelectedAppObservation.Kind.DEVICE_BOUNDARY;
                if(kind!=null) boundaries.add(new SelectedAppObservation.Event(event.getTimeStamp(),kind));
            }
            if(!FocusRepository.usageGranted(context)) return SelectedAppObservation.missing("Usage permission changed during query");
            return SelectedAppObservation.aggregate(boundaries,since,now);
        } catch(RuntimeException error) { return SelectedAppObservation.missing("Usage query unavailable: "+error.getClass().getSimpleName()); }
    }
}
