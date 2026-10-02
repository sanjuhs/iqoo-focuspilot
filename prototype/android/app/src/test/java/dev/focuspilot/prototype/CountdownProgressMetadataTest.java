package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** Target provenance checks; no Android persistence or physical-device claim. */
public final class CountdownProgressMetadataTest {
    @Test public void replacementRecordsNewTargetWithoutDiscardingHistory() {
        FocusSession session=new FocusSession();session.restorePaused(90_000);
        session.startTimed(1000,20_000);session.startTimed(6000,10_000);
        assertEquals(10_000,session.countdownTotalMs());assertEquals(10_000,session.remainingMs(6000));
        assertEquals(95_000,session.elapsed(6000));
    }
    @Test public void pauseResumePreservesOriginalTargetAndExcludesPausedTime() {
        FocusSession session=new FocusSession();session.startTimed(1000,20_000);session.pause(6000);
        assertEquals(20_000,session.countdownTotalMs());assertEquals(15_000,session.remainingMs(50_000));
        session.start(51_000);assertEquals(20_000,session.countdownTotalMs());
        assertEquals(13_000,session.remainingMs(53_000));assertEquals(7_000,session.elapsed(53_000));
    }
    @Test public void completionRetainsTargetButExplicitNewOpenEndedRunClearsIt() {
        FocusSession session=new FocusSession();session.startTimed(1000,2000);
        assertTrue(session.completeIfDue(9000));assertEquals(2000,session.countdownTotalMs());
        assertEquals(0,session.remainingMs(9000));session.start(10_000);
        assertEquals(-1,session.countdownTotalMs());assertFalse(session.isTimed());
        assertFalse(session.isCompleted());assertEquals(3000,session.elapsed(11_000));
    }
    @Test public void resetClearsTargetAndInvalidNewDurationKeepsExistingTarget() {
        FocusSession session=new FocusSession();session.startTimed(100,1000);
        try {session.startTimed(200,999);fail();}catch(IllegalArgumentException expected){}
        assertEquals(1000,session.countdownTotalMs());session.reset();
        assertEquals(-1,session.countdownTotalMs());assertEquals(0,session.elapsed(1000));
    }
    @Test public void legacyRecoveryNeverInfersTargetFromAccumulatedFocus() {
        FocusSession session=new FocusSession();session.startTimed(0,20_000);
        session.restorePaused(900_000,true,5000,false);
        assertEquals(-1,session.countdownTotalMs());assertEquals(5000,session.remainingMs(9000));
        assertFalse(session.isActive());session.start(10_000);
        assertEquals(-1,session.countdownTotalMs());assertEquals(4000,session.remainingMs(11_000));
        session.restorePaused(900_000);assertEquals(-1,session.countdownTotalMs());assertFalse(session.isTimed());
    }
    @Test public void validTargetRecoversPausedAndCompletedStates() {
        FocusSession session=new FocusSession();session.restorePaused(900_000,true,5000,false,20_000);
        assertEquals(20_000,session.countdownTotalMs());assertFalse(session.isActive());
        assertEquals(5000,session.remainingMs(1000));session.start(2000);session.completeIfDue(7000);
        assertEquals(20_000,session.countdownTotalMs());assertTrue(session.isCompleted());
        session.restorePaused(905_000,true,0,true,20_000);
        assertEquals(20_000,session.countdownTotalMs());assertTrue(session.isCompleted());assertFalse(session.isActive());
    }
    @Test public void malformedTargetDiscardsOnlyMetadataUsingOriginalSavedRemainder() {
        for(long total:new long[]{Long.MIN_VALUE,-1,0,999,4999,7_200_001,Long.MAX_VALUE}) {
            FocusSession session=new FocusSession();session.restorePaused(90_000,true,5000,false,total);
            assertEquals(-1,session.countdownTotalMs());assertEquals(5000,session.remainingMs(1000));
            assertEquals(90_000,session.elapsed(1000));assertFalse(session.isActive());assertFalse(session.isCompleted());
        }
        FocusSession completed=new FocusSession();completed.restorePaused(90_000,true,5000,true,1000);
        assertEquals(-1,completed.countdownTotalMs());assertEquals(0,completed.remainingMs(0));assertTrue(completed.isCompleted());
    }
    @Test public void targetCannotMakeMalformedOrOpenEndedRecoveryTimed() {
        FocusSession session=new FocusSession();session.restorePaused(1000,false,5000,false,20_000);
        assertEquals(-1,session.countdownTotalMs());assertFalse(session.isTimed());
        session.restorePaused(1000,true,7_200_001,true,7_200_000);
        assertEquals(-1,session.countdownTotalMs());assertFalse(session.isTimed());assertFalse(session.isCompleted());
        session.restorePaused(1000,true,7_200_000,false,7_200_000);
        assertEquals(7_200_000,session.countdownTotalMs());
    }
}
