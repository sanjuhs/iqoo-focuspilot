package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** Known development fixtures only; not the fresh cohort or Android execution. */
public final class CompatibleActionRouterTest {
    @Test public void editedRequestCannotReviewOldProposal() {
        CompatibleActionRouter.Result old=CompatibleActionRouter.recognize("Open Calculator");
        assertTrue(old.proposal.executable());
        CompatibleActionRouter.Result review=CompatibleActionRouter.review("Open Calculator","Open Settings",null,old.origin);
        assertFalse(review.proposal.executable());
        assertEquals(CompatibleUnitCommand.UNKNOWN,review.origin);
    }
    @Test public void localReviewHasNoModelResponse() {
        String original="Pause the focus session";
        assertTrue(CompatibleActionRouter.review(original,original,null,CompatibleUnitCommand.FAST_LOCAL_REQUEST).proposal.executable());
        assertFalse(CompatibleActionRouter.review(original,original,"{\"intent\":\"pause_focus\"}",CompatibleUnitCommand.FAST_LOCAL_REQUEST).proposal.executable());
    }
    @Test public void checkedReviewRetainsExactQuantityAndUnit() {
        String original="Set a five-minute timer";
        String response="{\"intent\":\"timer\",\"amount\":5,\"unit\":\"minutes\"}";
        CompatibleActionRouter.Result checked=CompatibleActionRouter.review(original,original,response,CompatibleUnitCommand.CHECKED_MODEL);
        assertEquals(ModelCommandGate.Kind.TIMER,checked.proposal.kind);
        assertEquals(300,checked.proposal.seconds);
        assertEquals(CompatibleUnitCommand.CHECKED_MODEL,checked.origin);
        assertFalse(CompatibleActionRouter.review(original,original,"{\"intent\":\"timer\",\"amount\":300,\"unit\":\"seconds\"}",CompatibleUnitCommand.CHECKED_MODEL).proposal.executable());
    }
    @Test public void originalClockAndAppTargetsMustAgree() {
        String original="An alarm at seven thirty PM";
        CompatibleActionRouter.Result checked=CompatibleActionRouter.validate(original,"{\"intent\":\"alarm\",\"hour\":19,\"minute\":30}");
        assertEquals(ModelCommandGate.Kind.ALARM,checked.proposal.kind);
        assertEquals(19,checked.proposal.hour);assertEquals(30,checked.proposal.minute);
        assertFalse(CompatibleActionRouter.validate(original,"{\"intent\":\"alarm\",\"hour\":7,\"minute\":30}").proposal.executable());
        assertFalse(CompatibleActionRouter.validate("Open Calculator","{\"intent\":\"open_app\",\"app\":\"settings\"}").proposal.executable());
    }
    @Test public void unsupportedOrMissingProvenanceCannotReview() {
        String original="Open Calculator";
        for(String origin:new String[]{null,"UNKNOWN","RAW_UNIT_SCHEMA","made_up"})
            assertFalse(CompatibleActionRouter.review(original,original,"{\"intent\":\"open_app\",\"app\":\"calculator\"}",origin).proposal.executable());
        assertFalse(CompatibleActionRouter.review(original,original,null,CompatibleUnitCommand.CHECKED_MODEL).proposal.executable());
        assertFalse(CompatibleActionRouter.recognize("Do not open Clock").proposal.executable());
    }
    @Test public void statusProposalPromisesOnlySnapshot() {
        CompatibleActionRouter.Result result=CompatibleActionRouter.recognize("How much focus time is left?");
        assertEquals(ModelCommandGate.Kind.EXPLAIN,result.proposal.kind);
        assertEquals("Show a current local focus status snapshot.",result.proposal.preview);
    }
}
