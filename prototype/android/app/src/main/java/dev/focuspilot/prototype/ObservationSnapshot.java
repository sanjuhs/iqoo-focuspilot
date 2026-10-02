package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Ephemeral selected-app summary and explicit feature validity. Never persisted. */
public final class ObservationSnapshot {
    public static final String MAPPING_VERSION="selected-events-v1";
    public static final long MAX_AGE_MS=15_000;
    public static final int REENTRY_SCALE=5, DEFER_SCALE=3;
    public final long scopeId, observedAtElapsed, sinceWall, observedAtWall;
    public final String selectedPackage;
    public final SelectedAppObservation.Summary summary;
    private final double[] values=new double[6];
    private final List<String> missing;
    public ObservationSnapshot(long scopeId,String selectedPackage,long sinceWall,long nowWall,long nowElapsed,
            long scopeStartedElapsed,long activeFocusElapsed,long budgetMs,long continuousLimitMs,long plannedFocusMs,
            int explicitDeferrals,SelectedAppObservation.Summary summary) {
        this.scopeId=scopeId;this.selectedPackage=selectedPackage;this.sinceWall=sinceWall;
        observedAtWall=nowWall;observedAtElapsed=nowElapsed;this.summary=summary;
        java.util.Arrays.fill(values,Double.NaN);
        List<String> absent=new ArrayList<>();
        long span=nowElapsed-scopeStartedElapsed;
        boolean clockValid=span>=0 && Math.abs((nowWall-sinceWall)-span)<=2_000;
        boolean complete=summary!=null && summary.complete && clockValid;
        if(!clockValid) absent.add("Wall/monotonic clock changed across observation scope");
        if(summary==null || !summary.complete) absent.add(summary==null?"No selected-app observation":summary.missingReason);
        if(complete && budgetMs>0) values[0]=overrun(summary.selectedMs,budgetMs);
        else absent.add("selected_app_budget_overrun missing");
        if(complete && continuousLimitMs>0) values[1]=overrun(summary.continuousSelectedMs,continuousLimitMs);
        else absent.add("continuous_session_overrun: requires complete events and an explicit continuous-app limit");
        if(complete) values[2]=Math.min(1,summary.reentries/(double)REENTRY_SCALE);
        else absent.add("reopen_count missing");
        if(complete && span>0) values[3]=Math.min(1,summary.selectedMs/(double)span);
        else absent.add("active_focus_overlap: observation interval has no proven duration");
        if(explicitDeferrals>=0) values[4]=Math.min(1,explicitDeferrals/(double)DEFER_SCALE);
        else absent.add("deferred_nudges: feedback scope unavailable");
        if(plannedFocusMs>0 && activeFocusElapsed>=0) values[5]=overrun(activeFocusElapsed,plannedFocusMs);
        else absent.add("elapsed_time_overrun: current focus is open-ended; explicit planned duration required");
        missing=Collections.unmodifiableList(absent);
    }
    public List<String> missingReasons() { return missing; }
    /** Missing entries remain NaN. They must never be passed to the trained network. */
    public double[] features() { return values.clone(); }
    public boolean complete() { return missing.isEmpty(); }
    private static double overrun(long observed,long limit) { return Math.max(0,Math.min(1,(observed-limit)/(double)limit)); }

    public static final class ShadowTrace {
        public static final String MODE="SHADOW · NO ACTIONS";
        public final ObservationSnapshot observation;
        public final TrainedPolicy.Evaluation evaluation;
        public final String blockedReason;
        private ShadowTrace(ObservationSnapshot observation,TrainedPolicy.Evaluation evaluation,String reason) {
            this.observation=observation;this.evaluation=evaluation;blockedReason=reason;
        }
        public boolean evaluated() { return evaluation!=null; }
    }
    public static ShadowTrace shadow(ObservationSnapshot snapshot,long expectedScope,long nowElapsed,
            boolean consent,boolean permission,boolean activeFocus) {
        String reason=!consent?"Observation consent disabled":!permission?"Usage permission unavailable":!activeFocus?"Focus paused":
            snapshot==null?"No fresh observation":snapshot.scopeId!=expectedScope?"Observation belongs to another scope":
            nowElapsed<snapshot.observedAtElapsed || nowElapsed-snapshot.observedAtElapsed>MAX_AGE_MS?"Observation stale":
            !snapshot.complete()?String.join("; ",snapshot.missingReasons()):null;
        return new ShadowTrace(snapshot,reason==null?TrainedPolicy.evaluate(snapshot.features()):null,reason);
    }
}
