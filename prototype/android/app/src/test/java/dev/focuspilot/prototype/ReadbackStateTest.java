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
}
