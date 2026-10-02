package dev.focuspilot.prototype;
import org.junit.Test;
import static org.junit.Assert.*;

public class SandboxActionGateTest {
    private static SandboxActionGate.Context context(long now){return new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.ACTIVITY,SandboxActionGate.ROOT_ID,7,now,true,true);}
    @Test public void onlyTwoOrderedSelectorsAndVerifiedPostconditionsCompleteProof(){
        SandboxActionGate gate=new SandboxActionGate();long token=gate.arm(context(100),100);
        assertTrue(gate.authorizeClick(token,context(150),SandboxActionGate.OPEN_ID,150));
        assertFalse(gate.authorizeClick(token,context(160),SandboxActionGate.OPEN_ID,160));
        assertFalse(gate.verifyPostcondition(token,context(180),SandboxActionGate.OPEN_ID,false,180));
        assertEquals(SandboxActionGate.Step.OPEN_TASK,gate.step());
        assertTrue(gate.verifyPostcondition(token,context(200),SandboxActionGate.OPEN_ID,true,200));
        assertTrue(gate.authorizeClick(token,context(300),SandboxActionGate.CHECK_ID,300));
        assertTrue(gate.verifyPostcondition(token,context(350),SandboxActionGate.CHECK_ID,true,350));
        assertEquals(SandboxActionGate.Step.DONE,gate.step());assertFalse(gate.armed());
        assertFalse(gate.authorizeClick(token,context(400),SandboxActionGate.CHECK_ID,400));
    }
    @Test public void unknownProductOrOutOfOrderSelectorsCannotClick(){
        for(String id:new String[]{SandboxActionGate.CHECK_ID,SandboxActionGate.ROOT_ID,SandboxActionGate.PACKAGE+":id/monitor", "other.app:id/confirm",""}){
            SandboxActionGate gate=new SandboxActionGate();long token=gate.arm(context(100),100);
            assertFalse(gate.authorizeClick(token,context(110),id,110));assertFalse(gate.armed());
        }
    }
    @Test public void missingArmCancelExpiryAndClockReversalBlockClicks(){
        SandboxActionGate gate=new SandboxActionGate();assertFalse(gate.authorizeClick(0,context(100),SandboxActionGate.OPEN_ID,100));
        long token=gate.arm(context(100),100);gate.cancel();assertFalse(gate.authorizeClick(token,context(110),SandboxActionGate.OPEN_ID,110));
        token=gate.arm(context(200),200);assertFalse(gate.authorizeClick(token,context(5200),SandboxActionGate.OPEN_ID,5200));
        token=gate.arm(context(300),300);assertFalse(gate.authorizeClick(token,context(299),SandboxActionGate.OPEN_ID,299));
    }
    @Test public void exactPackageActivityRootAndWindowAreMandatory(){
        SandboxActionGate.Context[] wrong={new SandboxActionGate.Context("com.instagram.android",SandboxActionGate.ACTIVITY,SandboxActionGate.ROOT_ID,7,110,true,true),
            new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.PACKAGE+".LocalModelActivity",SandboxActionGate.ROOT_ID,7,110,true,true),
            new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.ACTIVITY,"unknown_root",7,110,true,true),
            new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.ACTIVITY,SandboxActionGate.ROOT_ID,8,110,true,true)};
        for(SandboxActionGate.Context changed:wrong){SandboxActionGate gate=new SandboxActionGate();long token=gate.arm(context(100),100);
            assertFalse(gate.authorizeClick(token,changed,SandboxActionGate.OPEN_ID,110));assertFalse(gate.armed());}
    }
    @Test public void backgroundPermissionDisconnectAndStaleSnapshotsCancelAuthorization(){
        SandboxActionGate.Context[] wrong={new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.ACTIVITY,SandboxActionGate.ROOT_ID,7,400,false,true),
            new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.ACTIVITY,SandboxActionGate.ROOT_ID,7,400,true,false),
            new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.ACTIVITY,SandboxActionGate.ROOT_ID,7,0,true,true)};
        for(SandboxActionGate.Context changed:wrong){SandboxActionGate gate=new SandboxActionGate();long token=gate.arm(context(100),100);
            assertFalse(gate.authorizeClick(token,changed,SandboxActionGate.OPEN_ID,400));assertFalse(gate.armed());}
    }
    @Test public void staleTokenCannotActOrCancelANewerArm(){
        SandboxActionGate gate=new SandboxActionGate();long old=gate.arm(context(100),100);long fresh=gate.arm(context(200),200);
        assertNotEquals(old,fresh);assertFalse(gate.authorizeClick(old,context(220),SandboxActionGate.OPEN_ID,220));assertTrue(gate.armed());
        assertTrue(gate.authorizeClick(fresh,context(230),SandboxActionGate.OPEN_ID,230));
        assertFalse(gate.verifyPostcondition(old,context(250),SandboxActionGate.OPEN_ID,true,250));
        assertTrue(gate.verifyPostcondition(fresh,context(260),SandboxActionGate.OPEN_ID,true,260));
    }
    @Test public void missingAndMalformedContextCannotArm(){
        SandboxActionGate gate=new SandboxActionGate();assertEquals(-1,gate.arm(null,100));
        assertEquals(-1,gate.arm(new SandboxActionGate.Context(SandboxActionGate.PACKAGE,SandboxActionGate.ACTIVITY,SandboxActionGate.ROOT_ID,-1,100,true,true),100));
        assertEquals(-1,gate.arm(context(Long.MAX_VALUE),Long.MAX_VALUE));assertFalse(gate.armed());
    }
    @Test public void postconditionWithoutClickOrAfterExpiryCannotReportSuccess(){
        SandboxActionGate gate=new SandboxActionGate();long token=gate.arm(context(100),100);
        assertFalse(gate.verifyPostcondition(token,context(120),SandboxActionGate.OPEN_ID,true,120));
        assertEquals(SandboxActionGate.Step.OPEN_TASK,gate.step());
        assertTrue(gate.authorizeClick(token,context(150),SandboxActionGate.OPEN_ID,150));
        assertFalse(gate.verifyPostcondition(token,context(5100),SandboxActionGate.OPEN_ID,true,5100));
        assertFalse(gate.armed());assertEquals(SandboxActionGate.Step.DISARMED,gate.step());
    }
}
