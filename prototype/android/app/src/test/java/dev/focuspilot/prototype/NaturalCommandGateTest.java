package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

public final class NaturalCommandGateTest {
    @Test public void spokenDurationsPreserveExactSecondsAcrossFocusAndClock() {
        assertEquals(1500,ModelCommandGate.validate("start_focus","Mira, please help me focus for twenty-five minutes.").seconds);
        assertEquals(7200,ModelCommandGate.validate("start_focus","Begin a one hundred twenty minute work session").seconds);
        assertEquals(45,ModelCommandGate.validate("start_focus","Give me forty-five seconds of concentration").seconds);
        assertEquals(900,ModelCommandGate.validate("timer","Could you set a fifteen-minute timer?").seconds);
        assertEquals(90,ModelCommandGate.validate("timer","Count down for ninety seconds").seconds);
        assertFalse(ModelCommandGate.validate("timer","Set a one hundred twenty one minute timer").executable());
    }
    @Test public void everyToolRejectsPartialSlotsAndUnconsumedTail() {
        String[] timer={"Set a -5 minute timer","Set a +5 minute timer","Set a 1.5 minute timer","Set a 5,5 minute timer","Set a 5 minute timer for 9 seconds","Set a 5 minute timer open calculator","Set a 5 minute timer labelled delete","Set a 5 minute timer at 7:30","Set a 10000 second timer"};
        for(String text:timer)assertFalse(text,ModelCommandGate.validate("timer",text).executable());
        String[] alarms={"Set an alarm at -7:30","Wake me at +7:30 pm","Wake me at 7:30 pm for 5 minutes","Wake me at 7:30 pm repeat daily","Set an alarm at 7:30 pm 8:15 pm","Set an alarm at 7:30. Open calculator","Set an alarm at seven thirty"};
        for(String text:alarms)assertFalse(text,ModelCommandGate.validate("alarm",text).executable());
        assertFalse(ModelCommandGate.validate("start_focus","Start focus please silently open calculator").executable());
        assertFalse(ModelCommandGate.validate("open_app","Open calculator to make a payment").executable());
        assertFalse(ModelCommandGate.validate("open_app","Open settings for 5 minutes").executable());
    }
    @Test public void spokenClockSlotsRequireMeridianAndRemainExact() {
        ModelCommandGate.Proposal morning=ModelCommandGate.validate("alarm","Please wake me up at seven thirty a.m.");
        assertEquals(ModelCommandGate.Kind.ALARM,morning.kind);assertEquals(7,morning.hour);assertEquals(30,morning.minute);
        ModelCommandGate.Proposal night=ModelCommandGate.validate("alarm","Set a nine oh five PM alarm");
        assertEquals(ModelCommandGate.Kind.ALARM,night.kind);assertEquals(21,night.hour);assertEquals(5,night.minute);
        assertEquals(0,ModelCommandGate.validate("alarm","Set an alarm for twelve AM").hour);
        assertEquals(12,ModelCommandGate.validate("alarm","Wake me at twelve o'clock PM").hour);
        assertEquals(23,ModelCommandGate.validate("alarm","Alarm at 23:59").hour);
        assertFalse(ModelCommandGate.validate("alarm","Wake me at thirteen thirty PM").executable());
        assertFalse(ModelCommandGate.validate("alarm","Wake me at seven sixty PM").executable());
        assertFalse(ModelCommandGate.validate("alarm","Wake me at seven twenty five thirty PM").executable());
    }
    @Test public void friendlyReturnsAndBreaksStillRequireMatchingDirection() {
        assertEquals(ModelCommandGate.Kind.START_FOCUS,ModelCommandGate.validate("start_focus","Help me get back to work").kind);
        assertEquals(ModelCommandGate.Kind.START_FOCUS,ModelCommandGate.validate("start_focus","Put me in focus mode").kind);
        assertEquals(ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus","Take a break from studying").kind);
        assertEquals(ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus","Give me a study break").kind);
        assertFalse(ModelCommandGate.validate("start_focus","Take a study break").executable());
        assertFalse(ModelCommandGate.validate("pause_focus","Get back to studying").executable());
        assertFalse(ModelCommandGate.validate("timer","Focus for twenty-five minutes").executable());
        assertFalse(ModelCommandGate.validate("unknown","Start focus for 20 minutes").executable());
        assertFalse(ModelCommandGate.validate("start_focus","Start focus timer").executable());
        assertEquals(ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus","Pause my focus timer").kind);
    }
    @Test public void newWordsNeverRelaxIndependentNegationOrMultiStepChecks() {
        String[] requests={"Never focus for twenty minutes","Get back to work after lunch","Give me a study break then open settings","Set a five-minute timer and start focus","If I ask, take a break from studying","Put me in focus mode without activating focus","\"Put me in focus mode\"","Please say take a study break","Mira, start focus\nPlease open calculator"};
        String[] intents={"start_focus","start_focus","pause_focus","timer","pause_focus","start_focus","start_focus","pause_focus","start_focus"};
        for(int i=0;i<requests.length;i++)assertFalse(requests[i],ModelCommandGate.validate(intents[i],requests[i]).executable());
    }
    @Test public void completeAppAndStatusRequestsRemainBounded() {
        assertEquals(ModelCommandGate.Kind.OPEN_SETTINGS,ModelCommandGate.validate("open_app","Take me to the settings app please").kind);
        assertEquals(ModelCommandGate.Kind.OPEN_CALCULATOR,ModelCommandGate.validate("open_app","Bring up calculator").kind);
        assertEquals(ModelCommandGate.Kind.EXPLAIN,ModelCommandGate.validate("explain","How much focus time is left?").kind);
        assertEquals(ModelCommandGate.Kind.EXPLAIN,ModelCommandGate.validate("explain","Tell me my focus status").kind);
        assertFalse(ModelCommandGate.validate("explain","How much money is left?").executable());
        assertFalse(ModelCommandGate.validate("explain","Show focus status before starting it").executable());
        assertFalse(ModelCommandGate.validate("open_app","Bring up photos").executable());
    }
    @Test public void controlsAndHiddenLineSeparatorsAreRejectedBeforeNormalization() {
        String[] requests={"Start\tfocus","Start focus\u0000","Start focus\u2028open calculator","Set a five minute timer\r"};
        for(String request:requests)assertFalse(request,ModelCommandGate.validate("start_focus",request).executable());
        assertFalse(ModelCommandGate.validate("timer","Set a five minute timer\r").executable());
    }
}
