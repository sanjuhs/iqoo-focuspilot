package dev.focuspilot.prototype;

import java.util.Arrays;
import java.util.Collections;
import org.junit.Test;
import static org.junit.Assert.*;
import static dev.focuspilot.prototype.LivePreferencePolicy.Label.*;
import static dev.focuspilot.prototype.SelectedAppObservation.Kind.*;

public final class LivePreferencePolicyTest {
    private final LivePreferenceScope scope=LivePreferenceScope.fromGoal("test.selected",60_000,60_000,60_000,"Write a chapter");
    private final LivePreferencePolicy.Gates enabled=new LivePreferencePolicy.Gates(true,true,true,true,7);
    private ObservationSnapshot observation(long selectedMs) {
        SelectedAppObservation.Summary summary=SelectedAppObservation.aggregate(Arrays.asList(
            new SelectedAppObservation.Event(900,OTHER_RESUMED),new SelectedAppObservation.Event(181_000-selectedMs,SELECTED_RESUMED)),1000,181_000);
        return new ObservationSnapshot(7,"test.selected",1000,181_000,190_000,10_000,120_000,60_000,60_000,60_000,0,summary);
    }
    private LivePreferencePolicy trained(LivePreferencePolicy.Label label) {
        LivePreferencePolicy policy=new LivePreferencePolicy();
        for(long selected:new long[]{10_000,20_000,30_000})policy.save(scope,observation(selected),label,enabled,190_000);
        return policy;
    }
    @Test public void fingerprintIncludesEveryContextEditAndRestoresWithoutGoalText() {
        LivePreferenceScope restored=new LivePreferenceScope(scope.selectedPackage,scope.budgetMs,scope.continuousLimitMs,scope.plannedFocusMs,scope.goalSHA256);
        assertEquals(scope,restored);assertEquals(64,scope.fingerprint().length());assertEquals(64,scope.goalSHA256.length());
        assertNotEquals(scope,LivePreferenceScope.fromGoal("test.other",60_000,60_000,60_000,"Write a chapter"));
        assertNotEquals(scope,LivePreferenceScope.fromGoal("test.selected",60_001,60_000,60_000,"Write a chapter"));
        assertNotEquals(scope,LivePreferenceScope.fromGoal("test.selected",60_000,60_001,60_000,"Write a chapter"));
        assertNotEquals(scope,LivePreferenceScope.fromGoal("test.selected",60_000,60_000,60_001,"Write a chapter"));
        assertNotEquals(scope,LivePreferenceScope.fromGoal("test.selected",60_000,60_000,60_000,"Rest now"));
    }
    @Test public void optOffPermissionConsentPauseAndWrongObservationScopeCannotVetoOrSave() {
        LivePreferencePolicy policy=trained(ALLOW);ObservationSnapshot query=observation(10_000);
        LivePreferencePolicy.Gates[] blocked={new LivePreferencePolicy.Gates(false,true,true,true,7),new LivePreferencePolicy.Gates(true,false,true,true,7),
            new LivePreferencePolicy.Gates(true,true,false,true,7),new LivePreferencePolicy.Gates(true,true,true,false,7),new LivePreferencePolicy.Gates(true,true,true,true,8)};
        for(LivePreferencePolicy.Gates gate:blocked){
            LivePreferencePolicy.Decision decision=policy.evaluate(scope,query,gate,190_000);
            assertEquals(LivePreferencePolicy.Recommendation.BLOCKED,decision.recommendation);assertFalse(decision.canVetoHandSetNudge());
            assertThrows(IllegalArgumentException.class,()->policy.save(scope,query,ALLOW,gate,190_000));
        }
        assertEquals(3,policy.records().size());
    }
    @Test public void staleFutureAndMissingFeaturesAreNeverPersisted() {
        LivePreferencePolicy policy=new LivePreferencePolicy();ObservationSnapshot query=observation(10_000);
        assertThrows(IllegalArgumentException.class,()->policy.save(scope,query,ALLOW,enabled,205_001));
        assertThrows(IllegalArgumentException.class,()->policy.save(scope,query,ALLOW,enabled,189_999));
        ObservationSnapshot missing=new ObservationSnapshot(7,"test.selected",1000,181_000,190_000,10_000,120_000,60_000,60_000,60_000,0,
            SelectedAppObservation.missing("No permission stream"));
        assertThrows(IllegalArgumentException.class,()->policy.save(scope,missing,ALLOW,enabled,190_000));
        assertFalse(policy.evaluate(scope,missing,enabled,190_000).canVetoHandSetNudge());assertTrue(policy.records().isEmpty());
    }
    @Test public void contextSettingsRejectWrongSnapshotAndGoalEditsExcludeOldLabels() {
        LivePreferencePolicy policy=trained(ALLOW);ObservationSnapshot query=observation(10_000);
        LivePreferenceScope budgetEdit=LivePreferenceScope.fromGoal("test.selected",60_001,60_000,60_000,"Write a chapter");
        assertEquals(LivePreferencePolicy.Recommendation.BLOCKED,policy.evaluate(budgetEdit,query,enabled,190_000).recommendation);
        assertThrows(IllegalArgumentException.class,()->policy.save(budgetEdit,query,ALLOW,enabled,190_000));
        LivePreferenceScope goalEdit=LivePreferenceScope.fromGoal("test.selected",60_000,60_000,60_000,"Rest now");
        assertEquals(LivePreferencePolicy.Recommendation.ABSTAIN,policy.evaluate(goalEdit,query,enabled,190_000).recommendation);
    }
    @Test public void emptyAndInsufficientDistinctLabelsAbstain() {
        LivePreferencePolicy policy=new LivePreferencePolicy();ObservationSnapshot query=observation(10_000);
        assertEquals(LivePreferencePolicy.Recommendation.ABSTAIN,policy.evaluate(scope,query,enabled,190_000).recommendation);
        for(int i=0;i<3;i++)policy.save(scope,query,ALLOW,enabled,190_000);
        assertEquals(LivePreferencePolicy.Recommendation.ABSTAIN,policy.evaluate(scope,query,enabled,190_000).recommendation);
    }
    @Test public void exactConflictAndDistantSituationsAbstain() {
        LivePreferencePolicy policy=new LivePreferencePolicy();ObservationSnapshot query=observation(10_000);
        policy.save(scope,query,ALLOW,enabled,190_000);policy.save(scope,query,NUDGE,enabled,190_000);
        policy.save(scope,observation(20_000),ALLOW,enabled,190_000);
        assertEquals(LivePreferencePolicy.Recommendation.ABSTAIN,policy.evaluate(scope,query,enabled,190_000).recommendation);
        assertEquals(LivePreferencePolicy.Recommendation.ABSTAIN,trained(ALLOW).evaluate(scope,observation(180_000),enabled,190_000).recommendation);
    }
    @Test public void allowOnlyVetoesAndNudgeNeverCreatesAnAction() {
        ObservationSnapshot query=observation(10_000);
        LivePreferencePolicy.Decision allow=trained(ALLOW).evaluate(scope,query,enabled,190_000);
        assertTrue(allow.canVetoHandSetNudge());assertFalse(allow.permitsHandSetNudge(true));assertFalse(allow.permitsHandSetNudge(false));
        LivePreferencePolicy.Decision nudge=trained(NUDGE).evaluate(scope,query,enabled,190_000);
        assertEquals(LivePreferencePolicy.Recommendation.NUDGE,nudge.recommendation);assertFalse(nudge.canVetoHandSetNudge());
        assertTrue(nudge.permitsHandSetNudge(true));assertFalse(nudge.permitsHandSetNudge(false));
    }
    @Test public void limitDeletionAndRestorationPreserveProvenanceAndCopies() {
        LivePreferencePolicy policy=new LivePreferencePolicy();
        for(int i=0;i<33;i++)policy.save(scope,observation(10_000+i),ALLOW,enabled,190_000);
        assertEquals(32,policy.records().size());assertEquals(2,policy.records().get(0).id);
        LivePreferencePolicy.Record record=policy.records().get(0);assertEquals("REAL_OBSERVATION",record.provenance);
        double before=record.features()[3];double[] altered=record.features();altered[3]=1;assertEquals(before,record.features()[3],0);
        LivePreferencePolicy restored=new LivePreferencePolicy();restored.restore(policy.records());assertEquals(32,restored.records().size());
        assertTrue(restored.delete(record.id));assertEquals(31,restored.records().size());restored.clear();assertTrue(restored.records().isEmpty());
    }
    @Test public void restoreRejectsSandboxAndMalformedRecordsAllOrNothing() {
        LivePreferencePolicy policy=trained(ALLOW);LivePreferencePolicy.Record record=policy.records().get(0);
        assertThrows(IllegalArgumentException.class,()->new LivePreferencePolicy.Record(1,scope,new double[6],ALLOW,1000,2000,2000,"SYNTHETIC"));
        assertThrows(IllegalArgumentException.class,()->new LivePreferencePolicy.Record(1,scope,new double[]{Double.NaN,0,0,0,0,0},ALLOW,1000,2000,2000,"REAL_OBSERVATION"));
        assertThrows(IllegalArgumentException.class,()->new LivePreferencePolicy.Record(1,scope,new double[6],ALLOW,1000,2000,17_001,"REAL_OBSERVATION"));
        assertThrows(IllegalArgumentException.class,()->policy.restore(Arrays.asList(record,record)));
        assertThrows(IllegalArgumentException.class,()->policy.restore(Collections.nCopies(33,record)));assertEquals(3,policy.records().size());
    }
}
