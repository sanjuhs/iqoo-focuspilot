package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.List;
import org.junit.Test;
import static org.junit.Assert.*;
import static dev.focuspilot.prototype.SelectedAppObservation.Kind.*;

/** Policy boundary regression: review history is never current foreground authority. */
public final class RetainedForegroundLabelPolicyTest {
    private final LivePreferenceScope scope=LivePreferenceScope.fromGoal("test.selected",60_000,60_000,60_000,"Draft chapter");
    private final LivePreferencePolicy.Gates gates=new LivePreferencePolicy.Gates(true,true,true,true,7);
    private ObservationSnapshot snapshot(long duration,boolean foreground) {
        List<SelectedAppObservation.Event> events=new ArrayList<>();
        events.add(new SelectedAppObservation.Event(900,OTHER_RESUMED));
        events.add(new SelectedAppObservation.Event(181_000-duration,SELECTED_RESUMED));
        if(!foreground)events.add(new SelectedAppObservation.Event(180_999,OTHER_RESUMED));
        return new ObservationSnapshot(7,"test.selected",1000,181_000,190_000,10_000,120_000,60_000,60_000,60_000,0,
            SelectedAppObservation.aggregate(events,1000,181_000));
    }
    @Test public void foregroundReviewLabelsMatchOverrunsThatDashboardZeroContinuityCannot() {
        LivePreferencePolicy dashboardLabels=new LivePreferencePolicy(),retainedLabels=new LivePreferencePolicy();
        for(long duration:new long[]{120_000,130_000,140_000}) {
            dashboardLabels.save(scope,snapshot(duration,false),LivePreferencePolicy.Label.ALLOW,gates,190_001);
            retainedLabels.save(scope,snapshot(duration,true),LivePreferencePolicy.Label.ALLOW,gates,190_001);
        }
        ObservationSnapshot activeOverrun=snapshot(130_000,true);
        assertEquals(LivePreferencePolicy.Recommendation.ABSTAIN,dashboardLabels.evaluate(scope,activeOverrun,gates,190_001).recommendation);
        assertEquals(LivePreferencePolicy.Recommendation.ALLOW,retainedLabels.evaluate(scope,activeOverrun,gates,190_001).recommendation);
    }
    @Test public void reviewingFreshPastForegroundCannotAuthorizeNudgeWhileDashboardIsForeground() {
        ObservationSnapshot retained=snapshot(130_000,true),current=snapshot(130_000,false);
        LivePreferencePolicy labels=new LivePreferencePolicy();
        labels.save(scope,retained,LivePreferencePolicy.Label.ALLOW,gates,195_000);
        assertEquals(1,labels.records().size());
        assertTrue(retained.summary.selectedForeground);assertFalse(current.summary.selectedForeground);
        assertFalse(ObservedNudgeGate.eligible(current,7,195_000,true,true,true));
        assertFalse(new DecisionPolicy().evaluate(130_000,60_000,ObservedNudgeGate.eligible(current,7,195_000,true,true,true),195_000,-1).nudge);
    }
    @Test public void retainedReviewStillRejectsExpiredScopePausedAndRevokedPermission() {
        LivePreferencePolicy labels=new LivePreferencePolicy();ObservationSnapshot retained=snapshot(130_000,true);
        assertThrows(IllegalArgumentException.class,()->labels.save(scope,retained,LivePreferencePolicy.Label.ALLOW,gates,205_001));
        assertThrows(IllegalArgumentException.class,()->labels.save(scope,retained,LivePreferencePolicy.Label.ALLOW,new LivePreferencePolicy.Gates(true,true,true,true,8),195_000));
        assertThrows(IllegalArgumentException.class,()->labels.save(scope,retained,LivePreferencePolicy.Label.ALLOW,new LivePreferencePolicy.Gates(true,true,true,false,7),195_000));
        assertThrows(IllegalArgumentException.class,()->labels.save(scope,retained,LivePreferencePolicy.Label.ALLOW,new LivePreferencePolicy.Gates(true,true,false,true,7),195_000));
        assertTrue(labels.records().isEmpty());
    }
}
