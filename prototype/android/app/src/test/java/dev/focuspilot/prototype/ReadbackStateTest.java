package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** These callback/lifecycle tests do not simulate an Android TTS engine or audibility. */
public class ReadbackStateTest {
    @Test public void readbackRequiresForegroundAndPositiveOwnedToken() {
        ReadbackState state=new ReadbackState();
        assertFalse(state.active());assertEquals(0,state.begin());
        assertFalse(state.owns(0));assertFalse(state.owns(-1));assertFalse(state.finish(0));
        state.resume();long token=state.begin();
        assertTrue(token>0);assertTrue(state.active());assertTrue(state.owns(token));
        assertFalse(state.owns(token+1));assertFalse(state.finish(token+1));
        assertTrue(state.owns(token));
    }

    @Test public void replacingReadbackRejectsOldCompletionWithoutCancellingNewRequest() {
        ReadbackState state=new ReadbackState();state.resume();
        long old=state.begin(), current=state.begin();
        assertTrue(current>old);assertFalse(state.owns(old));assertFalse(state.finish(old));
        assertTrue(state.active());assertTrue(state.owns(current));assertTrue(state.finish(current));
        assertFalse(state.active());assertFalse(state.owns(current));assertFalse(state.finish(current));
    }

    @Test public void stopInvalidatesCallbacksAndResumeDoesNotResurrectReadback() {
        ReadbackState state=new ReadbackState();state.resume();long old=state.begin();state.stop();
        assertFalse(state.active());assertFalse(state.owns(old));assertFalse(state.finish(old));
        assertEquals(0,state.begin());state.resume();
        assertFalse(state.active());assertFalse(state.owns(old));assertFalse(state.finish(old));
        long current=state.begin();assertTrue(current>old);assertTrue(state.owns(current));
        state.resume();assertTrue(state.owns(current));
    }

    @Test public void cancellationAndTerminalCallbacksAreIdempotent() {
        ReadbackState state=new ReadbackState();state.resume();long cancelled=state.begin();
        state.cancel();state.cancel();
        assertFalse(state.active());assertFalse(state.owns(cancelled));assertFalse(state.finish(cancelled));
        long current=state.begin();assertTrue(current>cancelled);
        assertTrue(state.finish(current));assertFalse(state.finish(current));
        state.cancel();assertFalse(state.active());
        long next=state.begin();assertTrue(next>current);assertFalse(state.finish(current));
        assertTrue(state.owns(next));
    }

    @Test public void closingPermanentlyRejectsNewRequestsAndEveryLateCallback() {
        ReadbackState state=new ReadbackState();state.resume();long old=state.begin();
        state.close();state.resume();
        assertFalse(state.active());assertFalse(state.owns(old));assertFalse(state.finish(old));
        assertEquals(0,state.begin());state.stop();state.cancel();state.resume();state.close();
        assertEquals(0,state.begin());assertFalse(state.active());assertFalse(state.finish(old));
        ReadbackState neverStarted=new ReadbackState();neverStarted.close();neverStarted.resume();
        assertEquals(0,neverStarted.begin());
    }

    @Test public void oldEngineEventDeliveredToNewListenerCannotFinishItsReadback() {
        ReadbackState state=new ReadbackState();state.resume();
        long old=state.beginWithUtterance("mira-confirmed-");
        String oldId=state.utteranceId(old);state.cancel();
        long current=state.beginWithUtterance("mira-confirmed-");
        String currentId=state.utteranceId(current);
        assertNotEquals(oldId,currentId);
        // Listener B captures B's token, but the engine delivers stopped utterance A's ID.
        assertFalse(state.finishUtterance(current,oldId));
        assertTrue(state.active());assertTrue(state.ownsUtterance(current,currentId));
        assertTrue(state.finishUtterance(current,currentId));
        assertFalse(state.finishUtterance(current,currentId));assertFalse(state.active());
    }

    @Test public void currentEngineEventDeliveredToOldListenerCannotFinishNewReadback() {
        ReadbackState state=new ReadbackState();state.resume();
        long old=state.beginWithUtterance("mira-confirmed-");String oldId=state.utteranceId(old);
        long current=state.beginWithUtterance("mira-confirmed-");String currentId=state.utteranceId(current);
        // Listener A remains stale even if it is handed B's otherwise valid engine ID.
        assertFalse(state.finishUtterance(old,currentId));
        assertFalse(state.finishUtterance(old,oldId));
        assertNull(state.utteranceId(old));
        assertTrue(state.ownsUtterance(current,currentId));assertTrue(state.active());
        assertTrue(state.finishUtterance(current,currentId));
    }

    @Test public void unknownEngineIdsCannotChangeCurrentReadbackOrConsumeItsTerminal() {
        ReadbackState state=new ReadbackState();state.resume();
        long token=state.beginWithUtterance("mira-confirmed-");String id=state.utteranceId(token);
        for(String unrelated:new String[]{null,"","other-"+token,id+"-extra"}) {
            assertFalse(state.ownsUtterance(token,unrelated));
            assertFalse(state.finishUtterance(token,unrelated));
            assertTrue(state.active());assertEquals(id,state.utteranceId(token));
        }
        assertTrue(state.finishUtterance(token,id));
        assertNull(state.utteranceId(token));assertFalse(state.ownsUtterance(token,id));
        assertFalse(state.finishUtterance(token,id));
    }

    @Test public void cancelledStoppedAndClosedUtterancesNeverResurrectOnLateEvents() {
        ReadbackState state=new ReadbackState();state.resume();
        long cancelled=state.beginWithUtterance("mira-");String cancelledId=state.utteranceId(cancelled);
        state.cancel();state.resume();assertFalse(state.finishUtterance(cancelled,cancelledId));
        assertFalse(state.active());assertNull(state.utteranceId(cancelled));
        long stopped=state.beginWithUtterance("mira-");String stoppedId=state.utteranceId(stopped);
        state.stop();assertEquals(0,state.beginWithUtterance("mira-"));state.resume();
        assertFalse(state.finishUtterance(stopped,stoppedId));assertFalse(state.active());
        long closed=state.beginWithUtterance("mira-");String closedId=state.utteranceId(closed);
        state.close();state.resume();
        assertFalse(state.finishUtterance(cancelled,cancelledId));
        assertFalse(state.finishUtterance(stopped,stoppedId));
        assertFalse(state.finishUtterance(closed,closedId));assertFalse(state.active());
        assertEquals(0,state.beginWithUtterance("mira-"));
    }

    @Test public void genericRequestsStayCompatibleWithoutInheritingAnEngineIdentity() {
        ReadbackState state=new ReadbackState();state.resume();
        long bound=state.beginWithUtterance("mira-");String oldId=state.utteranceId(bound);
        long generic=state.begin();
        assertTrue(generic>bound);assertNull(state.utteranceId(generic));
        assertFalse(state.finishUtterance(generic,oldId));assertFalse(state.finishUtterance(bound,oldId));
        assertTrue(state.owns(generic));assertTrue(state.finish(generic));
        assertFalse(state.finish(generic));
        long next=state.beginWithUtterance("mira-");
        assertTrue(next>generic);assertNotEquals(oldId,state.utteranceId(next));
        assertTrue(state.finishUtterance(next,state.utteranceId(next)));
    }
}
