package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public final class ModelCommandGateTest {
    @Test public void originalTimeBoundsOverrideModelIntent() {
        assertEquals(ModelCommandGate.Kind.ALARM,ModelCommandGate.validate("alarm","Please wake me at 7:30 pm").kind);
        assertEquals(19,ModelCommandGate.validate("alarm","Please wake me at 7:30 pm").hour);
        assertFalse(ModelCommandGate.validate("alarm","alarm 99:99").executable());
        assertFalse(ModelCommandGate.validate("alarm","alarm tomorrow at 7:30 am").executable());
        assertFalse(ModelCommandGate.validate("alarm","alarm 7:30 or 8:30").executable());
        assertFalse(ModelCommandGate.validate("alarm","wake me at seven").executable());
    }
    @Test public void unknownNegationConsequencesAndMultipleActionsAbstain() {
        assertFalse(ModelCommandGate.validate("open_app","Do not open settings").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Start focus and delete photos").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Transfer money").executable());
        assertFalse(ModelCommandGate.validate("start_focus","What is the capital of France?").executable());
        assertFalse(ModelCommandGate.validate("invented_tool","Open settings").executable());
        assertFalse(ModelCommandGate.validate("open_app","Open settings or calculator").executable());
    }
    @Test public void timerAndApprovedAppsAreBounded() {
        assertEquals(300,ModelCommandGate.validate("timer","Set a 5 minute timer").seconds);
        assertFalse(ModelCommandGate.validate("timer","Set a 0 minute timer").executable());
        assertFalse(ModelCommandGate.validate("timer","Set a 121 minute timer").executable());
        assertFalse(ModelCommandGate.validate("timer","Set a five minute timer").executable());
        assertEquals(ModelCommandGate.Kind.OPEN_CALCULATOR,ModelCommandGate.validate("open_app","Launch calculator").kind);
        assertFalse(ModelCommandGate.validate("open_app","Open banking").executable());
    }
    @Test public void wrongModelDirectionOrToolIsRejectedIndependently() {
        assertFalse(ModelCommandGate.validate("start_focus","Pause focus").executable());
        assertFalse(ModelCommandGate.validate("pause_focus","Start a focus session").executable());
        assertFalse(ModelCommandGate.validate("pause_focus","I need concentration").executable());
        assertEquals(ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus","Stop focus").kind);
        assertFalse(ModelCommandGate.validate("alarm","A meeting at 7:30 pm").executable());
        assertFalse(ModelCommandGate.validate("timer","Focus for 5 minutes").executable());
        assertFalse(ModelCommandGate.validate("open_app","Tell me about calculator").executable());
        assertFalse(ModelCommandGate.validate("open_app","Don’t open settings").executable());
    }
    @Test public void explicitNaturalRequestsKeepTheirActionAndSlots() {
        String[] starts={"Please start a focus session", "Can you help me start studying?", "I'd like to begin my study session", "I want to focus for 20 minutes", "Help me focus", "Focus for twenty minutes", "Mira, please resume deep work", "Please help me concentrate"};
        for(String request:starts)assertEquals(request,ModelCommandGate.Kind.START_FOCUS,ModelCommandGate.validate("start_focus",request).kind);
        assertEquals(ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus","Could you please stop my study session?").kind);
        assertEquals(ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus","Cancel my focus session").kind);
        assertEquals(19,ModelCommandGate.validate("alarm","Can you please set an alarm at 7:30 PM?").hour);
        assertEquals(300,ModelCommandGate.validate("timer","Please help me set a 5-minute timer").seconds);
        assertEquals(ModelCommandGate.Kind.OPEN_SETTINGS,ModelCommandGate.validate("open_app","Could you please open settings?").kind);
    }
    @Test public void cancellationCannotBecomeCreationUnderWrongModelIntents() {
        String[] alarmCancels={"Cancel the alarm at 7:30", "Stop my alarm at 7:30", "Dismiss the 7:30 alarm", "Snooze my alarm at 7:30", "Turn off the alarm at 7:30", "Remove my alarm at 7:30", "Please reset the alarm at 7:30"};
        for(String request:alarmCancels)assertFalse(request,ModelCommandGate.validate("alarm",request).executable());
        String[] timerStops={"Cancel the 5 minute timer", "Stop the timer for 5 minutes", "Pause my 5 minute countdown", "Disable the timer for 5 minutes", "Clear the 5 minute timer", "Reset the 5 minute timer"};
        for(String request:timerStops)assertFalse(request,ModelCommandGate.validate("timer",request).executable());
        assertFalse(ModelCommandGate.validate("start_focus","Cancel focus").executable());
        assertFalse(ModelCommandGate.validate("open_app","Stop opening calculator").executable());
        assertFalse(ModelCommandGate.validate("pause_focus","Stop the timer while I study").executable());
    }
    @Test public void mentionsStatementsQuotesAndHowToQuestionsDoNotAct() {
        String[] mentions={"I need concentration", "Focus problems", "My focus has improved", "I will start studying tomorrow", "Yesterday I started a focus session", "Can you explain how to start focus?", "Please say start focus", "Start focus is the name of my project", "I like study sessions"};
        for(String request:mentions)assertFalse(request,ModelCommandGate.validate("start_focus",request).executable());
        assertFalse(ModelCommandGate.validate("alarm","My alarm is set for 7:30").executable());
        assertFalse(ModelCommandGate.validate("alarm","An alarm rings at 7:30").executable());
        assertFalse(ModelCommandGate.validate("timer","My timer has 5 minutes remaining").executable());
        assertFalse(ModelCommandGate.validate("timer","Timer for 5 minutes is running").executable());
        assertFalse(ModelCommandGate.validate("open_app","I open calculator every morning").executable());
    }
    @Test public void conditionalAndMultipleStepRequestsNeedClarification() {
        assertFalse(ModelCommandGate.validate("start_focus","Start focus if I open Instagram").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Start focus after lunch").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Start focus or open banking").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Start focus; open settings").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Start focus. Open settings.").executable());
        assertFalse(ModelCommandGate.validate("timer","Set a 5 minute timer\nopen calculator").executable());
        assertFalse(ModelCommandGate.validate("alarm","Avoid setting the alarm at 7:30").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Please start focus without activating it").executable());
    }
}
