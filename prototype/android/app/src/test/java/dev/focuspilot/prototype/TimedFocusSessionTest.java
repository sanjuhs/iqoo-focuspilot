package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public final class TimedFocusSessionTest {
    @Test public void deadlineBoundaryCapsTimeAndCompletesOnlyOnce() {
        FocusSession session=new FocusSession();session.startTimed(1000,20_000);
        assertTrue(session.isTimed());assertEquals(21_000,session.deadlineElapsedMs());
        assertEquals(1,session.remainingMs(20_999));assertFalse(session.completeIfDue(20_999));
        assertEquals(20_000,session.elapsed(50_000));assertEquals(0,session.remainingMs(50_000));
        assertTrue(session.completeIfDue(50_000));assertFalse(session.isActive());assertTrue(session.isCompleted());
        assertFalse(session.completeIfDue(60_000));assertEquals(20_000,session.elapsed(60_000));
    }
    @Test public void pauseAndResumeRetainUnspentTimeWithoutChargingPause() {
        FocusSession session=new FocusSession();session.startTimed(1000,20_000);session.pause(6000);
        assertEquals(5000,session.elapsed(999_000));assertEquals(15_000,session.remainingMs(999_000));assertEquals(-1,session.deadlineElapsedMs());
        session.start(1_000_000);assertEquals(1_015_000,session.deadlineElapsedMs());
        assertFalse(session.completeIfDue(1_014_999));assertTrue(session.completeIfDue(1_015_000));
        assertEquals(20_000,session.elapsed(2_000_000));
    }
    @Test public void explicitTimedReplacementPreservesHistoricalElapsedAndChangesGeneration() {
        FocusSession session=new FocusSession();session.start(1000);session.pause(6000);
        session.startTimed(7000,20_000);long oldGeneration=session.generation();long oldDeadline=session.deadlineElapsedMs();
        session.startTimed(12_000,30_000);
        assertNotEquals(oldGeneration,session.generation());assertEquals(42_000,session.deadlineElapsedMs());
        assertFalse(session.completeIfDue(oldDeadline));assertTrue(session.isActive());
        assertTrue(session.completeIfDue(42_000));assertEquals(40_000,session.elapsed(100_000));
    }
    @Test public void startAfterCompletionBeginsOpenEndedWithoutDiscardingHistory() {
        FocusSession session=new FocusSession();session.startTimed(1000,1000);session.completeIfDue(2000);
        session.start(5000);assertTrue(session.isActive());assertFalse(session.isTimed());assertFalse(session.isCompleted());
        assertEquals(-1,session.remainingMs(6000));assertEquals(2000,session.elapsed(6000));
    }
    @Test public void rollbackCannotReduceObservedProgressOrIncreaseRemainder() {
        FocusSession session=new FocusSession();session.startTimed(1000,10_000);
        assertEquals(4000,session.elapsed(5000));assertEquals(6000,session.remainingMs(5000));
        assertEquals(4000,session.elapsed(2000));assertEquals(6000,session.remainingMs(2000));
        assertFalse(session.completeIfDue(2000));assertTrue(session.completeIfDue(11_000));
    }
    @Test public void checkpointRecoveryIsPausedAndResumesOnlySavedRemainder() {
        FocusSession original=new FocusSession();original.startTimed(1000,20_000);
        FocusSession restored=new FocusSession();restored.restorePaused(original.elapsed(6000),true,original.remainingMs(6000),false);
        assertFalse(restored.isActive());assertTrue(restored.isTimed());assertFalse(restored.isCompleted());
        assertEquals(5000,restored.elapsed(1_000_000));assertEquals(15_000,restored.remainingMs(1_000_000));
        restored.start(2_000_000);assertEquals(2_015_000,restored.deadlineElapsedMs());assertTrue(restored.completeIfDue(2_015_000));
        assertEquals(20_000,restored.elapsed(3_000_000));
        FocusSession finished=new FocusSession();finished.restorePaused(20_000,true,0,true);assertTrue(finished.isCompleted());assertFalse(finished.isActive());
    }
    @Test public void invalidDurationDoesNotMutateExistingRunAndResetInvalidatesGeneration() {
        FocusSession session=new FocusSession();session.startTimed(1000,20_000);long generation=session.generation();
        assertThrows(IllegalArgumentException.class,()->session.startTimed(2000,999));
        assertThrows(IllegalArgumentException.class,()->session.startTimed(2000,7_200_001));
        assertEquals(generation,session.generation());assertEquals(21_000,session.deadlineElapsedMs());
        session.reset();assertNotEquals(generation,session.generation());assertFalse(session.isTimed());assertFalse(session.isActive());assertEquals(0,session.elapsed(5000));
    }
}
