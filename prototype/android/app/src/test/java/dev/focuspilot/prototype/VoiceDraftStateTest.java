package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** Lifecycle/epoch behavior is pure Java; these tests do not simulate an ASR service. */
public class VoiceDraftStateTest {
    @Test public void explicitForegroundPermissionAndServiceAreRequired(){
        VoiceDraftState state=new VoiceDraftState();assertEquals(-1,state.begin(true,true));state.resume();
        assertEquals(-1,state.begin(false,true));assertEquals(-1,state.begin(true,false));assertFalse(state.active());
        assertTrue(state.canUnderstand());assertTrue(state.begin(true,true)>0);assertFalse(state.canUnderstand());
    }
    @Test public void partialResultsRemainDraftOnlyAndNeverCompleteAnAction(){
        VoiceDraftState state=new VoiceDraftState();state.resume();long token=state.begin(true,true);
        assertFalse(state.acceptsPartial(token,"open settings"));assertTrue(state.listening(token));
        assertTrue(state.acceptsPartial(token,"open settings"));assertEquals("",state.draft());
        assertTrue(state.processing(token));assertTrue(state.finish(token,"  open settings  "));
        assertEquals("open settings",state.draft());assertEquals(VoiceDraftState.Phase.DRAFT,state.phase());assertTrue(state.canUnderstand());
        assertFalse(state.finish(token,"delete photos"));assertFalse(state.fail(token));assertEquals("open settings",state.draft());
    }
    @Test public void cancellationInvalidatesAllLateCallbacks(){
        VoiceDraftState state=new VoiceDraftState();state.resume();long old=state.begin(true,true);state.listening(old);state.cancel();
        assertFalse(state.finish(old,"set an alarm"));assertFalse(state.fail(old));assertFalse(state.listening(old));
        long next=state.begin(true,true);assertNotEquals(old,next);state.listening(next);
        assertFalse(state.finish(old,"pause focus"));assertTrue(state.finish(next,"start focus"));assertEquals("start focus",state.draft());
    }
    @Test public void backgroundAndDestroyedScreensCannotAcceptOrRestartSpeech(){
        VoiceDraftState state=new VoiceDraftState();state.resume();long token=state.begin(true,true);state.listening(token);state.stop();
        assertFalse(state.finish(token,"start focus"));assertEquals(-1,state.begin(true,true));state.resume();assertTrue(state.canStart());
        state.destroy();state.resume();assertFalse(state.canStart());assertEquals(-1,state.begin(true,true));
    }
    @Test public void modelBusyCancelsVoiceAndExcludesNewRecognition(){
        VoiceDraftState state=new VoiceDraftState();state.resume();long token=state.begin(true,true);state.listening(token);state.setModelBusy(true);
        assertFalse(state.active());assertFalse(state.finish(token,"start focus"));assertEquals(-1,state.begin(true,true));assertFalse(state.canUnderstand());
        state.setModelBusy(false);assertTrue(state.canStart());assertTrue(state.canUnderstand());
    }
    @Test public void malformedAndUnboundedTranscriptsDoNotOverwriteDrafts(){
        VoiceDraftState state=new VoiceDraftState();state.resume();long good=state.begin(true,true);state.listening(good);state.finish(good,"pause focus");
        long token=state.begin(true,true);state.listening(token);
        assertFalse(state.finish(token,null));assertFalse(state.finish(token," "));assertFalse(state.finish(token,"x".repeat(501)));
        assertEquals("pause focus",state.draft());assertTrue(state.fail(token));assertTrue(state.canStart());
    }
    @Test public void oneRecognitionSessionAtATime(){
        VoiceDraftState state=new VoiceDraftState();state.resume();long token=state.begin(true,true);assertEquals(-1,state.begin(true,true));
        state.listening(token);assertEquals(-1,state.begin(true,true));state.processing(token);assertEquals(-1,state.begin(true,true));
        state.cancel();assertTrue(state.canStart());
    }
}
