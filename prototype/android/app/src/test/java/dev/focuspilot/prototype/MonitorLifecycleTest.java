package dev.focuspilot.prototype;
import org.junit.Test;
import static org.junit.Assert.*;

public class MonitorLifecycleTest {
    @Test public void monitorConfigurationRejectsMalformedAndUnboundedInputs() {
        assertTrue(MonitorConfig.valid("com.instagram.android",60_000));
        assertFalse(MonitorConfig.valid("com.instagram.android",0));
        assertFalse(MonitorConfig.valid("com.instagram.android",7_200_001));
        assertFalse(MonitorConfig.valid("com.app;other",60_000));
        assertFalse(MonitorConfig.valid(null,60_000));
    }
    @Test public void everyPermissionAndVisibleStartAreRequired() {
        for(int mask=0;mask<16;mask++) assertEquals(mask==15,MonitorGate.canStart((mask&1)!=0,(mask&2)!=0,(mask&4)!=0,(mask&8)!=0));
    }
    @Test public void coldCheckpointRestoresPausedAndResumeExcludesInterruptedTime() {
        FocusSession original=new FocusSession(); original.start(100); long checkpoint=original.elapsed(5100);
        FocusSession restored=new FocusSession(); restored.restorePaused(checkpoint);
        assertFalse(restored.isActive()); assertEquals(5000,restored.elapsed(999_999));
        restored.start(1_000_000); assertEquals(6000,restored.elapsed(1_001_000));
    }
    @Test public void ledgerCheckpointPreservesCooldownAndBounds() {
        VirtualLedger ledger=new VirtualLedger(); ledger.restore(95,5000,7000);
        DecisionPolicy policy=new DecisionPolicy();
        assertFalse(ledger.apply(policy.evaluate(120_000,60_000,true,10_000,ledger.lastNudge()),10_000));
        assertTrue(ledger.apply(policy.evaluate(120_000,60_000,true,65_000,ledger.lastNudge()),65_000)); assertEquals(90,ledger.points());
        ledger.restore(1000,999_999,100); assertEquals(100,ledger.points()); assertEquals(-1,ledger.lastNudge());
    }
}
