package dev.focuspilot.prototype;

import java.util.Arrays;
import java.util.Collections;
import org.junit.Test;
import static org.junit.Assert.*;
import static dev.focuspilot.prototype.SelectedAppObservation.Kind.*;

public final class ObservationSnapshotTest {
    private SelectedAppObservation.Event e(long at,SelectedAppObservation.Kind kind) { return new SelectedAppObservation.Event(at,kind); }
    private SelectedAppObservation.Summary active() { return SelectedAppObservation.aggregate(Arrays.asList(e(900,SELECTED_RESUMED)),1000,5000); }
    private ObservationSnapshot snapshot(long continuous,long planned,SelectedAppObservation.Summary summary) {
        return new ObservationSnapshot(7,"test.selected",1000,5000,14_000,10_000,6000,2000,continuous,planned,1,summary);
    }
    @Test public void boundariesClipHistoryAndCountOnlyConfirmedReturns() {
        SelectedAppObservation.Summary s=SelectedAppObservation.aggregate(Arrays.asList(
            e(800,SELECTED_RESUMED),e(1500,SELECTED_PAUSED),e(1500,SELECTED_RESUMED),
            e(2000,OTHER_RESUMED),e(2500,SELECTED_RESUMED),e(2500,SELECTED_RESUMED)),1000,3000);
        assertTrue(s.complete);assertEquals(1500,s.selectedMs);assertEquals(500,s.continuousSelectedMs);assertEquals(1,s.reentries);
    }
    @Test public void screenOffEndsUseAndReentryRequiresObservedResume() {
        SelectedAppObservation.Summary off=SelectedAppObservation.aggregate(Arrays.asList(e(900,SELECTED_RESUMED),e(2000,SCREEN_OFF)),1000,4000);
        assertTrue(off.complete);assertEquals(1000,off.selectedMs);assertEquals(0,off.continuousSelectedMs);assertEquals(0,off.reentries);
        SelectedAppObservation.Summary resumed=SelectedAppObservation.aggregate(Arrays.asList(e(900,SELECTED_RESUMED),e(2000,SCREEN_OFF),e(3000,SELECTED_RESUMED)),1000,4000);
        assertEquals(2000,resumed.selectedMs);assertEquals(1000,resumed.continuousSelectedMs);assertEquals(1,resumed.reentries);
    }
    @Test public void unknownLeadingIntervalIsMissingInsteadOfAZeroProxy() {
        SelectedAppObservation.Summary s=SelectedAppObservation.aggregate(Arrays.asList(e(2000,SELECTED_RESUMED)),1000,5000);
        assertFalse(s.complete);ObservationSnapshot snap=snapshot(2000,3000,s);
        assertTrue(Double.isNaN(snap.features()[0]));assertFalse(snap.complete());
        assertFalse(ObservationSnapshot.shadow(snap,7,14_000,true,true,true).evaluated());
        assertFalse(SelectedAppObservation.aggregate(Collections.emptyList(),1000,5000).complete);
    }
    @Test public void startBoundaryCanEstablishStateButFutureEventsNeverLeak() {
        SelectedAppObservation.Summary s=SelectedAppObservation.aggregate(Arrays.asList(e(1000,SELECTED_RESUMED),e(9000,OTHER_RESUMED)),1000,5000);
        assertTrue(s.complete);assertEquals(4000,s.selectedMs);assertEquals(4000,s.continuousSelectedMs);
        assertFalse(SelectedAppObservation.aggregate(Arrays.asList(e(9000,SELECTED_RESUMED)),1000,5000).complete);
    }
    @Test public void outOfOrderAndDeviceBoundariesBlockRatherThanReorder() {
        assertFalse(SelectedAppObservation.aggregate(Arrays.asList(e(900,SELECTED_RESUMED),e(3000,SCREEN_OFF),e(2000,SELECTED_RESUMED)),1000,5000).complete);
        assertFalse(SelectedAppObservation.aggregate(Arrays.asList(e(900,SELECTED_RESUMED),e(3000,DEVICE_BOUNDARY)),1000,5000).complete);
    }
    @Test public void exactDeclaredMappingsAndHiddenContributionIdentity() {
        ObservationSnapshot snap=snapshot(2000,3000,active());assertTrue(snap.complete());
        assertArrayEquals(new double[]{1,1,0,1,1.0/3,1},snap.features(),1e-12);
        ObservationSnapshot.ShadowTrace trace=ObservationSnapshot.shadow(snap,7,14_000,true,true,true);
        assertTrue(trace.evaluated());double logit=trace.evaluation.outputBias;
        for(double contribution:trace.evaluation.hiddenContributions())logit+=contribution;
        assertEquals(trace.evaluation.logit,logit,1e-12);
    }
    @Test public void openEndedAndUndeclaredContinuousLimitsStayMissing() {
        ObservationSnapshot snap=snapshot(0,0,active());
        assertTrue(Double.isNaN(snap.features()[1]));assertTrue(Double.isNaN(snap.features()[5]));
        assertFalse(snap.complete());assertNull(ObservationSnapshot.shadow(snap,7,14_000,true,true,true).evaluation);
    }
    @Test public void pauseRevocationConsentFreshnessAndSessionChangesAlwaysBlock() {
        ObservationSnapshot snap=snapshot(2000,3000,active());
        assertFalse(ObservationSnapshot.shadow(snap,7,14_000,false,true,true).evaluated());
        assertFalse(ObservationSnapshot.shadow(snap,7,14_000,true,false,true).evaluated());
        assertFalse(ObservationSnapshot.shadow(snap,7,14_000,true,true,false).evaluated());
        assertFalse(ObservationSnapshot.shadow(snap,8,14_000,true,true,true).evaluated());
        assertFalse(ObservationSnapshot.shadow(snap,7,13_999,true,true,true).evaluated());
        assertFalse(ObservationSnapshot.shadow(snap,7,29_001,true,true,true).evaluated());
        assertTrue(ObservationSnapshot.shadow(snap,7,29_000,true,true,true).evaluated());
    }
    @Test public void wallClockJumpAndZeroDurationCannotCreateKnownInputs() {
        ObservationSnapshot jump=new ObservationSnapshot(7,"test.selected",1000,8000,14_000,10_000,6000,2000,2000,3000,0,active());
        assertFalse(jump.complete());assertTrue(Double.isNaN(jump.features()[0]));
        ObservationSnapshot zero=new ObservationSnapshot(7,"test.selected",1000,1000,10_000,10_000,0,2000,2000,3000,0,
            SelectedAppObservation.aggregate(Arrays.asList(e(1000,OTHER_RESUMED)),1000,1000));
        assertFalse(zero.complete());assertTrue(Double.isNaN(zero.features()[3]));
    }
    @Test public void explicitFeedbackNeedsActualFreshNudgeAndResetsWithScope() {
        ScopedNudgeFeedback feedback=new ScopedNudgeFeedback();assertEquals(0,feedback.count());
        assertFalse(feedback.defer(2000,true));feedback.recordActualNudge(3000);
        assertFalse(feedback.defer(2999,true));assertFalse(feedback.defer(3001,false));assertTrue(feedback.defer(3001,true));
        assertFalse(feedback.defer(3002,true));assertEquals(1,feedback.count());
        feedback.recordActualNudge(70_000);assertFalse(feedback.defer(130_001,true));
        feedback.reset();assertEquals(0,feedback.count());assertFalse(feedback.defer(130_001,true));
    }
}
