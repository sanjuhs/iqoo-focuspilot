package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** Known lifecycle/provenance fixtures only; no fresh-data or Android execution. */
public final class CompatibleReviewStateTest {
    @Test public void fastProposalNeedsNoModelResponse() {
        CompatibleReviewState state=new CompatibleReviewState();
        assertTrue(state.offer(1,"Open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        CompatibleReviewState.Snapshot snapshot=state.snapshot();
        assertEquals(CompatibleUnitCommand.FAST_LOCAL_REQUEST,snapshot.origin());
        assertTrue(state.review(snapshot,1,"Open Calculator",true,true).proposal.executable());
    }
    @Test public void replacementAndClearInvalidateOldCallbacks() {
        CompatibleReviewState state=new CompatibleReviewState();
        assertTrue(state.offer(1,"Open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        CompatibleReviewState.Snapshot old=state.snapshot();
        assertTrue(state.offer(2,"Open Settings",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        assertFalse(state.review(old,1,"Open Calculator",true,true).proposal.executable());
        CompatibleReviewState.Snapshot current=state.snapshot();
        state.clear();
        assertFalse(state.consume(current,2,"Open Settings",true,true).proposal.executable());
        assertNull(state.snapshot());
    }
    @Test public void editsEpochBackgroundAndAudioOrVoiceBusyBlockReview() {
        CompatibleReviewState state=new CompatibleReviewState();
        assertTrue(state.offer(1,"Open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        CompatibleReviewState.Snapshot snapshot=state.snapshot();
        assertFalse(state.review(snapshot,1,"Open Settings",true,true).proposal.executable());
        assertFalse(state.review(snapshot,2,"Open Calculator",true,true).proposal.executable());
        assertFalse(state.review(snapshot,1,"Open Calculator",false,true).proposal.executable());
        assertFalse(state.review(snapshot,1,"Open Calculator",true,false).proposal.executable());
    }
    @Test public void consumeIsSingleUseAndRechecksModelSlots() {
        CompatibleReviewState state=new CompatibleReviewState();
        String text="Set a five-minute timer";
        String response="{\"intent\":\"timer\",\"amount\":5,\"unit\":\"minutes\"}";
        assertTrue(state.offer(4,text,response,CompatibleUnitCommand.CHECKED_MODEL));
        CompatibleReviewState.Snapshot snapshot=state.snapshot();
        CompatibleActionRouter.Result confirmed=state.consume(snapshot,4,text,true,true);
        assertEquals(300,confirmed.proposal.seconds);
        assertEquals(CompatibleUnitCommand.CHECKED_MODEL,confirmed.origin);
        assertFalse(state.consume(snapshot,4,text,true,true).proposal.executable());
    }
    @Test public void refusalOrMismatchedOriginCannotLeavePriorProposal() {
        CompatibleReviewState state=new CompatibleReviewState();
        assertTrue(state.offer(1,"Open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        assertFalse(state.offer(2,"Do not open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        assertNull(state.snapshot());
        assertFalse(state.offer(3,"Open Calculator","{\"intent\":\"open_app\",\"app\":\"calculator\"}",CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        assertFalse(state.offer(3,"Open Calculator",null,CompatibleUnitCommand.CHECKED_MODEL));
        assertFalse(state.offer(0,"Open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
    }
    @Test public void failedOldConfirmationDoesNotClearNewProposal() {
        CompatibleReviewState state=new CompatibleReviewState();
        assertTrue(state.offer(1,"Open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        CompatibleReviewState.Snapshot old=state.snapshot();
        assertTrue(state.offer(2,"Open Settings",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST));
        assertFalse(state.consume(old,1,"Open Calculator",true,true).proposal.executable());
        assertTrue(state.review(state.snapshot(),2,"Open Settings",true,true).proposal.executable());
    }
}
