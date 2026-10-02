package dev.focuspilot.prototype;

import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;
import static dev.focuspilot.prototype.SelectedAppObservation.Kind.*;

/** Regression at the boundary between observations, preferences and the virtual ledger. */
public class BudgetPersonalizationIntegrationTest {
    private final LivePreferenceScope scope=LivePreferenceScope.fromGoal("test.selected",60_000,60_000,60_000,"Draft");
    private ObservationSnapshot snapshot(long selectedMs,boolean stillSelected) {
        long nowWall=181_000;
        java.util.List<SelectedAppObservation.Event> events=new java.util.ArrayList<>();
        events.add(new SelectedAppObservation.Event(900,OTHER_RESUMED));
        events.add(new SelectedAppObservation.Event(nowWall-selectedMs,SELECTED_RESUMED));
        if(!stillSelected)events.add(new SelectedAppObservation.Event(nowWall,OTHER_RESUMED));
        return new ObservationSnapshot(7,"test.selected",1000,nowWall,190_000,10_000,120_000,60_000,60_000,60_000,0,
            SelectedAppObservation.aggregate(events,1000,nowWall));
    }
    @Test public void leavingDistractingAppStopsRepeatedChargesAfterCooldown() {
        DecisionPolicy rule=new DecisionPolicy();VirtualLedger ledger=new VirtualLedger();
        ObservationSnapshot selected=snapshot(130_000,true);
        assertTrue(ledger.apply(rule.evaluate(130_000,60_000,ObservedNudgeGate.eligible(selected,7,190_000,true,true,true),190_000,ledger.lastNudge()),190_000));
        assertEquals(95,ledger.points());
        ObservationSnapshot left=snapshot(130_000,false);
        DecisionPolicy.Result next=rule.evaluate(130_000,60_000,ObservedNudgeGate.eligible(left,7,190_000,true,true,true),250_001,ledger.lastNudge());
        assertFalse(next.nudge);assertFalse(ledger.apply(next,250_001));assertEquals(95,ledger.points());
    }
    @Test public void exactAllowPreferenceSkipsAnOtherwiseEligibleBudgetCharge() {
        LivePreferencePolicy policy=new LivePreferencePolicy();LivePreferencePolicy.Gates gates=new LivePreferencePolicy.Gates(true,true,true,true,7);
        for(long duration:new long[]{120_000,130_000,140_000})policy.save(scope,snapshot(duration,true),LivePreferencePolicy.Label.ALLOW,gates,190_000);
        ObservationSnapshot query=snapshot(130_000,true);VirtualLedger ledger=new VirtualLedger();
        DecisionPolicy.Result base=new DecisionPolicy().evaluate(130_000,60_000,ObservedNudgeGate.eligible(query,7,190_000,true,true,true),190_000,-1);
        assertTrue(base.nudge);
        LivePreferencePolicy.Decision learned=policy.evaluate(scope,query,gates,190_000);
        assertEquals(LivePreferencePolicy.Recommendation.ALLOW,learned.recommendation);
        if(learned.permitsHandSetNudge(base.nudge))ledger.apply(base,190_000);
        assertEquals(100,ledger.points());assertEquals(-1,ledger.lastNudge());
    }
    @Test public void nudgeLabelsCannotChargeBelowBudgetOrDuringCooldown() {
        LivePreferencePolicy policy=new LivePreferencePolicy();LivePreferencePolicy.Gates gates=new LivePreferencePolicy.Gates(true,true,true,true,7);
        for(long duration:new long[]{10_000,20_000,30_000})policy.save(scope,snapshot(duration,true),LivePreferencePolicy.Label.NUDGE,gates,190_000);
        LivePreferencePolicy.Decision learned=policy.evaluate(scope,snapshot(20_000,true),gates,190_000);
        assertEquals(LivePreferencePolicy.Recommendation.NUDGE,learned.recommendation);
        DecisionPolicy rule=new DecisionPolicy();
        assertFalse(learned.permitsHandSetNudge(rule.evaluate(20_000,60_000,true,190_000,-1).nudge));
        assertFalse(learned.permitsHandSetNudge(rule.evaluate(130_000,60_000,true,190_000,189_999).nudge));
    }
}
