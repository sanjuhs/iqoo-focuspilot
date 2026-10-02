package dev.focuspilot.prototype;

import org.junit.Test;
import java.util.Arrays;
import java.util.Collections;
import static org.junit.Assert.*;

public class FewShotPolicyTest {
    private static final FewShotPolicy.Gates OPEN=new FewShotPolicy.Gates(false,true,true,true,true,true);
    private static double[] vector(double n){double[] x=new double[6];Arrays.fill(x,n);return x;}
    @Test public void noExamplesAndDistantExamplesAbstain(){
        FewShotPolicy policy=new FewShotPolicy();assertEquals(FewShotPolicy.Recommendation.ABSTAIN,policy.evaluate(vector(0),OPEN).recommendation);
        policy.add(vector(0),FewShotPolicy.Label.NUDGE);
        assertEquals(FewShotPolicy.Recommendation.ABSTAIN,policy.evaluate(vector(1),OPEN).recommendation);
    }
    @Test public void allExternalGatesOverrideExactNudge(){
        FewShotPolicy policy=new FewShotPolicy();policy.add(vector(0.8),FewShotPolicy.Label.NUDGE);
        FewShotPolicy.Gates[] blocked={new FewShotPolicy.Gates(true,true,true,true,true,true),new FewShotPolicy.Gates(false,false,true,true,true,true),
            new FewShotPolicy.Gates(false,true,false,true,true,true),new FewShotPolicy.Gates(false,true,true,false,true,true),
            new FewShotPolicy.Gates(false,true,true,true,false,true),new FewShotPolicy.Gates(false,true,true,true,true,false)};
        for(FewShotPolicy.Gates gates:blocked){FewShotPolicy.Evaluation result=policy.evaluate(vector(0.8),gates);
            assertEquals(FewShotPolicy.Recommendation.BLOCKED,result.recommendation);assertTrue(result.neighbors.isEmpty());}
        assertEquals(FewShotPolicy.Recommendation.NUDGE,policy.evaluate(vector(0.8),OPEN).recommendation);
    }
    @Test public void exactConflictsCannotHideBehindTopThree(){
        FewShotPolicy policy=new FewShotPolicy();for(int i=0;i<3;i++)policy.add(vector(0.2),FewShotPolicy.Label.NUDGE);
        policy.add(vector(0.2),FewShotPolicy.Label.ALLOW);
        assertEquals(FewShotPolicy.Recommendation.ABSTAIN,policy.evaluate(vector(0.2),OPEN).recommendation);
    }
    @Test public void uncertainNeighborVotesAbstain(){
        FewShotPolicy policy=new FewShotPolicy();policy.add(vector(0.4),FewShotPolicy.Label.ALLOW);policy.add(vector(0.6),FewShotPolicy.Label.NUDGE);
        FewShotPolicy.Evaluation result=policy.evaluate(vector(0.5),OPEN);
        assertEquals(FewShotPolicy.Recommendation.ABSTAIN,result.recommendation);assertEquals(0.5,result.nudgeVote,1e-12);
    }
    @Test public void exactAllowOverridesNearbyNudgesWithoutMutatingNetwork(){
        FewShotPolicy policy=new FewShotPolicy();policy.add(vector(0.75),FewShotPolicy.Label.ALLOW);policy.add(vector(0.74),FewShotPolicy.Label.NUDGE);
        double baseline=TrainedPolicy.evaluate(vector(0.75)).score;
        assertEquals(FewShotPolicy.Recommendation.ALLOW,policy.evaluate(vector(0.75),OPEN).recommendation);
        assertEquals(baseline,TrainedPolicy.evaluate(vector(0.75)).score,0);
    }
    @Test public void explanationContributionsAndCopiesAreExact(){
        FewShotPolicy policy=new FewShotPolicy();double[] input=vector(0.2);FewShotPolicy.Example example=policy.add(input,FewShotPolicy.Label.NUDGE);
        input[0]=1;assertEquals(0.2,example.features()[0],0);
        policy.add(vector(0.3),FewShotPolicy.Label.ALLOW);FewShotPolicy.Evaluation result=policy.evaluate(vector(0.21),OPEN);
        double sum=0,weights=0;for(FewShotPolicy.Neighbor n:result.neighbors){sum+=n.nudgeContribution;weights+=n.voteWeight;
            double squares=0;for(double p:n.squaredDistanceContributions())squares+=p;
            assertEquals(n.distance*n.distance,squares,1e-12);double[] copy=n.features();copy[0]=100;assertTrue(n.features()[0]<=1);}
        assertEquals(result.nudgeVote,sum,1e-12);assertEquals(1,weights,1e-12);
        assertThrows(UnsupportedOperationException.class,()->result.neighbors.clear());
    }
    @Test public void boundsEvictionDeleteAndAtomicRestore(){
        FewShotPolicy policy=new FewShotPolicy();for(int i=0;i<33;i++)policy.add(vector(i/33.0),FewShotPolicy.Label.ALLOW);
        assertEquals(32,policy.examples().size());assertEquals(2,policy.examples().get(0).id);
        assertTrue(policy.delete(2));assertFalse(policy.delete(2));
        FewShotPolicy.Example duplicate=new FewShotPolicy.Example(8,vector(0),FewShotPolicy.Label.NUDGE);
        assertThrows(IllegalArgumentException.class,()->policy.restore(Arrays.asList(duplicate,duplicate)));
        assertEquals(31,policy.examples().size());policy.restore(Collections.singletonList(duplicate));assertEquals(9,policy.add(vector(0),FewShotPolicy.Label.ALLOW).id);
        policy.clear();assertTrue(policy.examples().isEmpty());
    }
    @Test public void malformedDataCannotCreateLabelsOrVotes(){
        FewShotPolicy policy=new FewShotPolicy();assertThrows(IllegalArgumentException.class,()->policy.add(null,FewShotPolicy.Label.ALLOW));
        assertThrows(IllegalArgumentException.class,()->policy.add(new double[5],FewShotPolicy.Label.ALLOW));
        for(double invalid:new double[]{-0.1,1.1,Double.NaN,Double.POSITIVE_INFINITY}){
            double[] x=vector(0);x[3]=invalid;assertThrows(IllegalArgumentException.class,()->policy.add(x,FewShotPolicy.Label.ALLOW));}
        assertThrows(IllegalArgumentException.class,()->policy.add(vector(0),null));
        assertThrows(IllegalArgumentException.class,()->policy.evaluate(vector(0),null));assertTrue(policy.examples().isEmpty());
    }
}
