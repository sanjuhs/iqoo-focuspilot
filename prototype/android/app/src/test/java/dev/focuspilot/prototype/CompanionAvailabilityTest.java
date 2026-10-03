package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public final class CompanionAvailabilityTest {
    @Test public void protectedSignalsNeverStartAnUnchosenSession() {
        CompanionAvailability state = new CompanionAvailability();
        assertEquals(CompanionAvailability.Effect.NONE, state.resume(state.lease(), true, true));
        assertEquals(CompanionAvailability.Effect.NONE, state.suspend(true));
        assertFalse(state.isRunning());
        assertEquals(CompanionAvailability.Effect.NONE, state.begin(true, false, true));
        assertEquals(CompanionAvailability.Effect.NONE, state.begin(true, true, false));
        assertFalse(state.returnAfterUnlockActive());
    }
    @Test public void defaultShowStopsInsteadOfReturningOnUnlock() {
        CompanionAvailability state = new CompanionAvailability();
        assertEquals(CompanionAvailability.Effect.ATTACH, state.begin(false, true, true));
        long lease = state.lease();
        assertEquals(CompanionAvailability.Effect.STOP, state.suspend(true));
        assertEquals(CompanionAvailability.Effect.NONE, state.resume(lease, true, true));
        assertFalse(state.isRunning());
    }
    @Test public void explicitPersistentSessionDetachesAndNeedsActualUnlockedState() {
        CompanionAvailability state = new CompanionAvailability(); state.begin(true, true, true);
        long lease = state.lease();
        assertEquals(CompanionAvailability.Effect.DETACH, state.suspend(true));
        assertTrue(state.isRunning()); assertTrue(state.isDormant());
        assertEquals(CompanionAvailability.Effect.NONE, state.resume(lease, true, false));
        assertTrue(state.isDormant());
        assertEquals(CompanionAvailability.Effect.ATTACH, state.resume(lease, true, true));
        assertFalse(state.isDormant()); assertTrue(state.returnAfterUnlockActive());
    }
    @Test public void revokedPrerequisitesPreventResurrectionAfterRegrant() {
        CompanionAvailability state = new CompanionAvailability(); state.begin(true, true, true);
        long lease = state.lease(); state.suspend(true);
        assertEquals(CompanionAvailability.Effect.STOP, state.resume(lease, false, true));
        assertEquals(CompanionAvailability.Effect.NONE, state.resume(lease, true, true));
        assertFalse(state.isRunning());
    }
    @Test public void hideCancelsDormantSessionAndStaleUnlockCannotTouchReplacement() {
        CompanionAvailability state = new CompanionAvailability(); state.begin(true, true, true);
        long oldLease = state.lease(); state.suspend(true); state.stop();
        assertEquals(CompanionAvailability.Effect.NONE, state.resume(oldLease, true, true));
        state.begin(true, true, true); state.suspend(true);
        assertEquals(CompanionAvailability.Effect.NONE, state.resume(oldLease, true, true));
        assertTrue(state.isDormant());
        assertEquals(CompanionAvailability.Effect.ATTACH, state.resume(state.lease(), true, true));
    }
    @Test public void repeatedSignalsDoNotAttachDuplicateWindows() {
        CompanionAvailability state = new CompanionAvailability(); state.begin(true, true, true);
        long lease = state.lease();
        assertEquals(CompanionAvailability.Effect.DETACH, state.suspend(true));
        assertEquals(CompanionAvailability.Effect.NONE, state.suspend(true));
        assertEquals(CompanionAvailability.Effect.ATTACH, state.resume(lease, true, true));
        assertEquals(CompanionAvailability.Effect.NONE, state.resume(lease, true, true));
    }
    @Test public void repeatedShowCannotUpgradeCurrentSessionMode() {
        CompanionAvailability state = new CompanionAvailability(); state.begin(false, true, true);
        assertEquals(CompanionAvailability.Effect.NONE, state.begin(true, true, true));
        assertFalse(state.returnAfterUnlockActive());
        assertEquals(CompanionAvailability.Effect.STOP, state.suspend(true));
        state.begin(true, true, true); state.suspend(true);
        assertEquals(CompanionAvailability.Effect.NONE, state.begin(false, true, true));
        assertTrue(state.returnAfterUnlockActive());
    }
    @Test public void permanentRevocationAtScreenOffStopsPersistentSession() {
        CompanionAvailability state = new CompanionAvailability(); state.begin(true, true, true);
        assertEquals(CompanionAvailability.Effect.STOP, state.suspend(false));
        assertFalse(state.isRunning()); assertFalse(state.returnAfterUnlockActive());
        assertEquals(CompanionAvailability.Effect.NONE, state.stop());
    }
}
