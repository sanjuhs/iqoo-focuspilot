package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** Whole-request usability regressions; not held-out model or Android action evidence. */
public final class ConversationalCommandGateTest {
    @Test public void politeCommasKeepTheCompleteFocusDuration() {
        ModelCommandGate.Proposal proposal=ModelCommandGate.validate("start_focus","Hello, Mira, kindly focus for sixteen minutes, please.");
        assertEquals(ModelCommandGate.Kind.START_FOCUS,proposal.kind);assertEquals(960,proposal.seconds);
        assertEquals(ModelCommandGate.Kind.START_FOCUS,ModelCommandGate.validate("start_focus","Please, could you just resume my focus session for me?").kind);
        assertEquals(ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus","Hey, pause my concentration session, please!").kind);
    }
    @Test public void completePersonalRequestAndApplicationSuffixAreSupported() {
        assertEquals(ModelCommandGate.Kind.OPEN_CALCULATOR,ModelCommandGate.validate("open_app","Can you kindly open the calculator application, please?").kind);
        assertEquals(ModelCommandGate.Kind.OPEN_CLOCK,ModelCommandGate.validate("open_app","I'd like you to open the clock application for me.").kind);
        assertEquals(ModelCommandGate.Kind.OPEN_SETTINGS,ModelCommandGate.validate("open_app","I need you to open settings now please").kind);
        assertEquals(ModelCommandGate.Kind.EXPLAIN,ModelCommandGate.validate("explain","Please, would you show my focus summary for me?").kind);
    }
    @Test public void politenessDoesNotChangeExactClockOrTimerSlots() {
        ModelCommandGate.Proposal alarm=ModelCommandGate.validate("alarm","I'd like you to set an alarm at twelve thirty AM for me.");
        assertEquals(ModelCommandGate.Kind.ALARM,alarm.kind);assertEquals(0,alarm.hour);assertEquals(30,alarm.minute);
        ModelCommandGate.Proposal timer=ModelCommandGate.validate("timer","Kindly set a timer for seventy seconds, please.");
        assertEquals(ModelCommandGate.Kind.TIMER,timer.kind);assertEquals(70,timer.seconds);
        assertFalse(ModelCommandGate.validate("alarm","Please, wake me at twelve thirty for me").executable());
        assertFalse(ModelCommandGate.validate("timer","Please, set a timer for zero seconds for me").executable());
    }
    @Test public void wrappersCannotHideNegationConditionsOrAnotherAction() {
        String[] requests={"Please, do not start focus for me","I'd like you to never start focus","Kindly open settings for me later","Open calculator for me, open clock","Hello, Mira, focus for five minutes then stop focus","Can you please open settings for me if I ask?","Please, start focus for me without activating it"};
        for(String request:requests)for(String intent:new String[]{"start_focus","pause_focus","alarm","timer","open_app","explain"})assertFalse(request+" / "+intent,ModelCommandGate.validate(intent,request).executable());
    }
    @Test public void arbitrarySuffixesAndQuotedOrMentionedCommandsRemainUnconsumed() {
        String[] requests={"Start focus for 5 minutes for my study","Start focus for me for five minutes","Please, say start focus for me","Could you just explain how to start focus","Please, \"start focus\"","Open the calculator application for me to pay someone","Open calculator for me for 5 minutes","Please, set a five minute timer repeat daily"};
        for(String request:requests)for(String intent:new String[]{"start_focus","timer","open_app"})assertFalse(request+" / "+intent,ModelCommandGate.validate(intent,request).executable());
    }
    @Test public void wrongIntentOrUnsupportedApplicationStillAbstains() {
        assertFalse(ModelCommandGate.validate("start_focus","Please, pause my focus session for me").executable());
        assertFalse(ModelCommandGate.validate("pause_focus","Please, start a focus session for me").executable());
        assertFalse(ModelCommandGate.validate("alarm","Please, open the clock application for me").executable());
        assertFalse(ModelCommandGate.validate("open_app","Please, open the photos application for me").executable());
        assertFalse(ModelCommandGate.validate("unknown","Please, open the calculator application for me").executable());
        assertFalse(ModelCommandGate.validate("timer","Kindly focus for seventy seconds for me").executable());
    }
}
