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
}
