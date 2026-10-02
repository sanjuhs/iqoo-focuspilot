package dev.focuspilot.prototype;

import java.util.List;

/** Pure timestamp aggregation. Other apps are reduced to an anonymous boundary. */
public final class SelectedAppObservation {
    public enum Kind { SELECTED_RESUMED, SELECTED_PAUSED, OTHER_RESUMED, SCREEN_OFF, DEVICE_BOUNDARY }
    public static final class Event {
        public final long at;
        public final Kind kind;
        public Event(long at,Kind kind) { this.at=at;this.kind=kind; }
    }
    public static final class Summary {
        public final boolean complete;
        public final String missingReason;
        public final long selectedMs, continuousSelectedMs;
        /** Foreground reentries after an earlier observed entry, not Android launches. */
        public final int reentries;
        private Summary(boolean complete,String reason,long selected,long continuous,int reentries) {
            this.complete=complete;missingReason=reason;selectedMs=selected;continuousSelectedMs=continuous;this.reentries=reentries;
        }
    }
    private SelectedAppObservation() {}
    public static Summary missing(String reason) { return new Summary(false,reason,0,0,0); }
    public static Summary aggregate(List<Event> events,long since,long now) {
        if(events==null || since<=0 || now<since) return missing("Usage query unavailable or invalid interval");
        boolean known=false, selected=false, entered=false, leftSelected=false, leadingGap=false;
        long cursor=since, runStart=since, total=0, previous=Long.MIN_VALUE;
        int reentries=0;
        for(Event event:events) {
            if(event==null || event.kind==null) return missing("Malformed usage boundary");
            if(event.at>now) continue; // Never infer from a future event, including its order.
            if(event.at<previous) return missing("OS boundaries arrived out of order");
            previous=event.at;
            if(event.kind==Kind.DEVICE_BOUNDARY && event.at>=since) return missing("Device restart/shutdown crosses observation scope");
            if(event.at<since) {
                known=true; selected=event.kind==Kind.SELECTED_RESUMED;
                entered=selected;runStart=since;continue;
            }
            if(!known && event.at>since) leadingGap=true;
            if(known && selected) total+=Math.max(0,event.at-cursor);
            cursor=event.at;
            if(event.kind==Kind.SELECTED_RESUMED) {
                if(!selected) { if(entered && leftSelected) reentries++; entered=true;leftSelected=false;runStart=event.at; }
                selected=true;
            } else {
                if(entered && (event.kind==Kind.OTHER_RESUMED || event.kind==Kind.SCREEN_OFF)) leftSelected=true;
                selected=false;
            }
            known=true;
        }
        if(!known) return missing("No observed boundary establishes state at scope start");
        if(selected) total+=Math.max(0,now-cursor);
        return new Summary(!leadingGap,leadingGap?"Unobserved leading interval; complete totals/reentries unavailable":null,
            Math.min(total,now-since),selected?Math.max(0,now-runStart):0,reentries);
    }
}
