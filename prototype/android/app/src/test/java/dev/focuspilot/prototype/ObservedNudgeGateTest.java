package dev.focuspilot.prototype;

import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;
import static dev.focuspilot.prototype.SelectedAppObservation.Kind.*;

public final class ObservedNudgeGateTest {
    private SelectedAppObservation.Event e(long at,SelectedAppObservation.Kind kind) { return new SelectedAppObservation.Event(at,kind); }
    private ObservationSnapshot snapshot(SelectedAppObservation.Event... events) {
        return new ObservationSnapshot(7,"test.selected",1000,5000,14_000,10_000,4000,2000,0,0,0,
            SelectedAppObservation.aggregate(Arrays.asList(events),1000,5000));
    }
    private boolean eligible(ObservationSnapshot snapshot) { return ObservedNudgeGate.eligible(snapshot,7,14_000,true,true,true); }
    @Test public void currentSelectedForegroundCanNudgeWithoutOptionalNetworkLimits() {
        ObservationSnapshot current=snapshot(e(900,SELECTED_RESUMED));
        assertTrue(current.summary.selectedForeground);assertTrue(eligible(current));
        assertFalse(current.complete()); // Planned/continuous NN limits are intentionally unknown.
        assertTrue(current.summary.selectedMs>2000);
    }
    @Test public void leavingSelectedAppAndScreenOffBlockDespiteCumulativeBudgetOverrun() {
        ObservationSnapshot other=snapshot(e(900,SELECTED_RESUMED),e(4500,OTHER_RESUMED));
        ObservationSnapshot paused=snapshot(e(900,SELECTED_RESUMED),e(4500,SELECTED_PAUSED));
        ObservationSnapshot off=snapshot(e(900,SELECTED_RESUMED),e(4500,SCREEN_OFF));
        for(ObservationSnapshot stopped:new ObservationSnapshot[]{other,paused,off}) {
            assertTrue(stopped.summary.complete);assertTrue(stopped.summary.selectedMs>2000);
            assertFalse(stopped.summary.selectedForeground);assertFalse(eligible(stopped));
        }
    }
    @Test public void confirmedReturnRestoresEligibilityAndPreservesDurationsAndReentries() {
        ObservationSnapshot resumed=snapshot(e(900,SELECTED_RESUMED),e(2000,OTHER_RESUMED),e(4000,SELECTED_RESUMED));
        assertEquals(2000,resumed.summary.selectedMs);assertEquals(1000,resumed.summary.continuousSelectedMs);
        assertEquals(1,resumed.summary.reentries);assertTrue(eligible(resumed));
    }
    @Test public void missingLeadingBoundaryAndFutureResumeNeverEstablishForegroundProof() {
        ObservationSnapshot missing=snapshot(e(2000,SELECTED_RESUMED));
        ObservationSnapshot future=snapshot(e(900,OTHER_RESUMED),e(6000,SELECTED_RESUMED));
        assertFalse(missing.summary.complete);assertFalse(missing.summary.selectedForeground);assertFalse(eligible(missing));
        assertTrue(future.summary.complete);assertFalse(future.summary.selectedForeground);assertFalse(eligible(future));
        assertFalse(eligible(snapshot(e(6000,SELECTED_RESUMED))));
    }
    @Test public void consentPermissionFocusScopeAndQueryTimeAlwaysGateBaseline() {
        ObservationSnapshot current=snapshot(e(900,SELECTED_RESUMED));
        assertFalse(ObservedNudgeGate.eligible(current,7,14_000,false,true,true));
        assertFalse(ObservedNudgeGate.eligible(current,7,14_000,true,false,true));
        assertFalse(ObservedNudgeGate.eligible(current,7,14_000,true,true,false));
        assertFalse(ObservedNudgeGate.eligible(current,8,14_000,true,true,true));
        assertFalse(ObservedNudgeGate.eligible(current,7,13_999,true,true,true));
        assertFalse(ObservedNudgeGate.eligible(current,7,29_001,true,true,true));
        assertTrue(ObservedNudgeGate.eligible(current,7,29_000,true,true,true));
        assertFalse(ObservedNudgeGate.eligible(null,7,14_000,true,true,true));
    }
    @Test public void invalidOrderingOrRestartCannotBeUsedAsCurrentForeground() {
        assertFalse(eligible(snapshot(e(900,SELECTED_RESUMED),e(4000,SCREEN_OFF),e(3000,SELECTED_RESUMED))));
        assertFalse(eligible(snapshot(e(900,SELECTED_RESUMED),e(3000,DEVICE_BOUNDARY))));
    }
    @Test public void clockDiscontinuityBlocksBudgetNudgesWithoutRequiringOptionalLimits() {
        ObservationSnapshot jumped=new ObservationSnapshot(7,"test.selected",1000,9000,14_000,10_000,4000,2000,0,0,0,
            SelectedAppObservation.aggregate(Arrays.asList(e(900,SELECTED_RESUMED)),1000,9000));
        assertTrue(jumped.summary.selectedForeground);assertFalse(jumped.timestampAlignmentValid);assertFalse(eligible(jumped));
    }
}
