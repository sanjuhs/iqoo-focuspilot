package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** Real coordinator/request-state transitions; no Android engine, audio or audibility is simulated. */
public class ReadbackInitializationTest {
    @Test public void cancelThenExplicitRetryWaitsForSameEngineAndReceivesCompletionOnce() {
        ReadbackState requests=new ReadbackState();requests.resume();
        ReadbackInitialization engine=new ReadbackInitialization();
        long a=requests.beginWithUtterance("mira-");
        assertEquals(ReadbackInitialization.Admission.START_ENGINE,engine.request(a));
        long epoch=engine.engineEpoch();requests.cancel();engine.cancelRequests();
        long b=requests.beginWithUtterance("mira-");
        assertEquals(ReadbackInitialization.Admission.WAIT,engine.request(b));
        assertEquals(epoch,engine.engineEpoch());
        long ready=engine.complete(epoch,true);
        assertEquals(b,ready);assertTrue(requests.owns(ready));assertFalse(requests.owns(a));
        assertEquals(0,engine.complete(epoch,true));
        assertTrue(requests.finishUtterance(b,requests.utteranceId(b)));
    }

    @Test public void cancelledRequestWithoutReplacementNeverReadsWhenEngineBecomesReady() {
        ReadbackState requests=new ReadbackState();requests.resume();
        ReadbackInitialization engine=new ReadbackInitialization();
        long a=requests.beginWithUtterance("mira-");engine.request(a);long epoch=engine.engineEpoch();
        requests.cancel();engine.cancelRequests();
        assertEquals(0,engine.complete(epoch,true));assertFalse(requests.active());
        // Ready state is reusable only after another explicit foreground request.
        long b=requests.beginWithUtterance("mira-");
        assertEquals(ReadbackInitialization.Admission.SPEAK,engine.request(b));
        assertTrue(requests.owns(b));
    }

    @Test public void cancellingLatestWaiterDoesNotFallBackToTheOriginalRequest() {
        ReadbackInitialization engine=new ReadbackInitialization();
        engine.request(1);long epoch=engine.engineEpoch();engine.request(2);
        engine.cancelRequest(1); // A's late timeout must not cancel explicitly pending B.
        assertEquals(2,engine.complete(epoch,true));
        ReadbackInitialization cancelled=new ReadbackInitialization();
        cancelled.request(1);long otherEpoch=cancelled.engineEpoch();cancelled.request(2);
        cancelled.cancelRequest(2);
        assertEquals(0,cancelled.complete(otherEpoch,true));
    }

    @Test public void backgroundAndDestroyClearWaitersWithoutRestartingOrDeliveringSpeech() {
        ReadbackState requests=new ReadbackState();requests.resume();
        ReadbackInitialization engine=new ReadbackInitialization();
        long a=requests.beginWithUtterance("mira-");engine.request(a);long epoch=engine.engineEpoch();
        requests.stop();engine.cancelRequests();
        assertEquals(0,engine.complete(epoch,true));requests.resume();assertFalse(requests.active());
        assertFalse(requests.finishUtterance(a,"mira-"+a));
        ReadbackInitialization destroyed=new ReadbackInitialization();
        destroyed.request(1);long destroyedEpoch=destroyed.engineEpoch();destroyed.close();
        assertFalse(destroyed.ownsInitialization(destroyedEpoch));
        assertEquals(0,destroyed.complete(destroyedEpoch,true));
        assertEquals(ReadbackInitialization.Admission.REJECT,destroyed.request(2));
    }

    @Test public void FailedOrTimedOutEngineCanRetryAndItsLateCallbackCannotPoisonReplacement() {
        ReadbackInitialization engine=new ReadbackInitialization();
        engine.request(1);long old=engine.engineEpoch();
        assertEquals(1,engine.complete(old,false));assertFalse(engine.ownsInitialization(old));
        assertEquals(ReadbackInitialization.Admission.START_ENGINE,engine.request(2));
        long replacement=engine.engineEpoch();assertTrue(replacement>old);
        assertEquals(0,engine.complete(old,true));assertEquals(0,engine.complete(old,false));
        assertTrue(engine.ownsInitialization(replacement));assertEquals(2,engine.complete(replacement,true));
        assertEquals(0,engine.complete(replacement,false));
        assertEquals(ReadbackInitialization.Admission.SPEAK,engine.request(3));
    }

    @Test public void invalidRequestsDoNotReplaceAValidPendingRequest() {
        ReadbackInitialization engine=new ReadbackInitialization();
        assertEquals(ReadbackInitialization.Admission.REJECT,engine.request(0));
        assertEquals(ReadbackInitialization.Admission.REJECT,engine.request(-1));
        assertEquals(0,engine.engineEpoch());
        engine.request(7);long epoch=engine.engineEpoch();
        assertEquals(ReadbackInitialization.Admission.REJECT,engine.request(0));
        assertEquals(7,engine.complete(epoch,true));
    }
}
