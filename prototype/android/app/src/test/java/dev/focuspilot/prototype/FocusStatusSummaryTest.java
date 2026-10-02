package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public final class FocusStatusSummaryTest {
    private static FocusStatusSummary.Snapshot snapshot(boolean active, boolean complete, boolean recovered,
            long elapsed, long remaining, long total) {
        return new FocusStatusSummary.Snapshot(active, complete, recovered, elapsed, remaining, total,
                65_000, 300_000, 95, true, true);
    }
    @Test public void openEndedAnswersElapsedAndAdmitsMissingCountdown() {
        String s = FocusStatusSummary.format(snapshot(true, false, false, 97_331, -1, -1));
        assertTrue(s.contains("Focus: active")); assertTrue(s.contains("1m 37s"));
        assertTrue(s.contains("No countdown is set")); assertTrue(s.contains("95/100 virtual points"));
    }
    @Test public void pausedAndResumedUseSameRemainderNotHistoricalElapsed() {
        FocusStatusSummary.Snapshot paused = snapshot(false, false, false, 9_000_000, 900_000, 1_500_000);
        FocusStatusSummary.Snapshot resumed = snapshot(true, false, false, 9_000_000, 900_000, 1_500_000);
        assertEquals(40, paused.progressPercent()); assertEquals(40, resumed.progressPercent());
        assertTrue(FocusStatusSummary.format(paused).contains("Focus: paused"));
        assertTrue(FocusStatusSummary.format(resumed).contains("15m 0s left. Total: 25m 0s; progress: 40%"));
    }
    @Test public void completedKnownDurationReportsHundredPercent() {
        FocusStatusSummary.Snapshot s = snapshot(false, true, false, 20_000, 0, 20_000);
        assertEquals(100, s.progressPercent());
        assertTrue(FocusStatusSummary.format(s).contains("countdown finished; paused"));
    }
    @Test public void checkpointRecoveryDoesNotInventUnrecordedTimeOrTotal() {
        FocusStatusSummary.Snapshot s = snapshot(false, false, true, 97_331, 5_000, -1);
        assertEquals(-1, s.progressPercent());
        String text = FocusStatusSummary.format(s);
        assertTrue(text.contains("last saved checkpoint as paused"));
        assertTrue(text.contains("original duration of this saved countdown is unknown"));
    }
    @Test public void currentSessionAdapterUsesOneMonotonicReadingAndRecordedTotal() {
        FocusSession session = new FocusSession(); session.restorePaused(90_000);
        session.startTimed(100, 20_000); session.pause(5100); session.start(6100);
        long now = 8100;
        FocusStatusSummary.Snapshot s = snapshot(session.isActive(), session.isCompleted(), false,
                session.elapsed(now), session.remainingMs(now), session.countdownTotalMs());
        assertEquals(97_000, s.elapsedMs); assertEquals(13_000, s.remainingMs);
        assertEquals(35, s.progressPercent());
    }
    @Test public void deadlinePendingAndCompletedAreDistinct() {
        String pending = FocusStatusSummary.format(snapshot(true, false, false, 20_000, 0, 20_000));
        assertTrue(pending.contains("app is finishing this countdown"));
        assertFalse(pending.contains("countdown finished; paused"));
    }
    @Test public void absenceAndSavedUsageRemainHonest() {
        String missing = FocusStatusSummary.format(new FocusStatusSummary.Snapshot(false, false, false,
                0, -1, -1, -1, 60_000, 100, true, false));
        assertTrue(missing.contains("App usage: unavailable"));
        assertTrue(missing.contains("No countdown is set. Focus is paused."));
        assertFalse(missing.contains("continues until"));
        assertTrue(missing.contains("needs Usage Access"));
        String saved = FocusStatusSummary.format(new FocusStatusSummary.Snapshot(false, false, false,
                0, -1, -1, 1000, 60_000, 100, false, true));
        assertTrue(saved.contains("(saved)"));
        assertTrue(saved.contains("does not identify the cause of an earlier reminder"));
    }
    @Test public void longMaximumAndRoundingDoNotOverflow() {
        String text = FocusStatusSummary.format(new FocusStatusSummary.Snapshot(false, false, false,
                Long.MAX_VALUE, 1, 1000, Long.MAX_VALUE, Long.MAX_VALUE, 0, true, true));
        assertTrue(text.contains("2562047788015h 12m 55s"));
        assertTrue(text.contains("Countdown: 1s left"));
        assertTrue(text.contains("progress: 99%"));
    }
    @Test public void corruptOrContradictorySnapshotsAreRejected() {
        invalid(true, true, false, 0, 0, 1000);
        invalid(true, false, true, 0, 1000, 1000);
        invalid(false, true, false, 0, -1, -1);
        invalid(false, false, false, -1, -1, -1);
        invalid(false, false, false, 0, -2, -1);
        invalid(false, false, false, 0, 1000, 999);
        invalid(false, false, false, 0, 7_200_001, -1);
        invalid(false, false, false, 0, -1, 1000);
        try { new FocusStatusSummary.Snapshot(false,false,false,0,-1,-1,-2,60_000,100,false,false);fail(); }
        catch (IllegalArgumentException expected) {}
        try { new FocusStatusSummary.Snapshot(false,false,false,0,-1,-1,0,0,100,false,false);fail(); }
        catch (IllegalArgumentException expected) {}
        try { new FocusStatusSummary.Snapshot(false,false,false,0,-1,-1,0,1000,101,false,false);fail(); }
        catch (IllegalArgumentException expected) {}
        try { FocusStatusSummary.format(null);fail(); } catch (IllegalArgumentException expected) {}
    }
    private static void invalid(boolean active, boolean complete, boolean recovered, long elapsed, long remaining, long total) {
        try { snapshot(active,complete,recovered,elapsed,remaining,total);fail("Corrupt snapshot accepted"); }
        catch (IllegalArgumentException expected) {}
    }
}
