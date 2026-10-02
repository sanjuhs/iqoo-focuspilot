package dev.focuspilot.prototype;

import org.junit.Test;
import static org.junit.Assert.*;

/** Focused complete-form regression tests; openly seen development fixtures. */
public final class CandidateGateTest {
    private static final String[] INTENTS={"start_focus","pause_focus","alarm","timer","open_app","explain"};
    private static void blocked(String... requests) {
        for(String request:requests)for(String intent:INTENTS)
            assertFalse(request+" / "+intent,ModelCommandGate.validate(intent,request).executable());
    }
    @Test public void nounRequestsAndFocusedWorkKeepExactWholeDuration() {
        ModelCommandGate.Proposal a=ModelCommandGate.validate("start_focus","I want a 17 minute concentration session, please.");
        assertEquals(ModelCommandGate.Kind.START_FOCUS,a.kind);assertEquals(1020,a.seconds);
        assertEquals(37,ModelCommandGate.validate("start_focus","Give me thirty seven seconds of focused work").seconds);
        assertEquals(ModelCommandGate.Kind.START_FOCUS,ModelCommandGate.validate("start_focus","Return to my concentration session").kind);
        blocked("I need concentration","I want a concentration session","I want a 17 minute concentration session for 20 seconds", "I want a 17 minute concentration session starting tomorrow");
    }
    @Test public void qualifiedTargetsAndConcentrationCountdownKeepPauseDirection() {
        String[] requests={"Pause my active study session","Suspend the ongoing work session","End our current deep work session","Cancel my concentration countdown"};
        for(String text:requests) {
            assertEquals(text,ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus",text).kind);
            assertFalse(text,ModelCommandGate.validate("start_focus",text).executable());
            assertFalse(text,ModelCommandGate.validate("timer",text).executable());
        }
        blocked("Cancel my cooking countdown","Stop the alarm while I study","Pause my study session for 20 minutes");
    }
    @Test public void personalBreakFormsCannotBecomeStartsOrTimers() {
        String[] requests={"Let me take a break from my concentration session", "I need a break from deep work now please", "I'd like a break from my work session"};
        for(String text:requests) {
            assertEquals(text,ModelCommandGate.Kind.PAUSE_FOCUS,ModelCommandGate.validate("pause_focus",text).kind);
            assertFalse(ModelCommandGate.validate("start_focus",text).executable());
            assertFalse(ModelCommandGate.validate("timer",text).executable());
        }
        blocked("Describe how to take a break from my work session", "I need a break from focus later", "Let me take a break from my work session open Clock");
    }
    @Test public void desireClockRequestsPreserveIndependentNumberParserAndSlots() {
        ModelCommandGate.Proposal a=ModelCommandGate.validate("alarm","I need an alarm for six forty one PM");
        assertEquals(ModelCommandGate.Kind.ALARM,a.kind);assertEquals(18,a.hour);assertEquals(41,a.minute);
        assertEquals(83,ModelCommandGate.validate("timer","I'd like a timer for 83 seconds").seconds);
        assertEquals(120,ModelCommandGate.validate("timer","I would like a timer for two minutes").seconds);
        blocked("I 'd like a timer for 83 seconds", "I would like a timer for +83 seconds", "I need an alarm for six forty one", "I need an alarm for six forty one PM repeat daily", "I want a timer for 12 minutes 8 seconds");
    }
    @Test public void appDisplayStillUsesOnlyThreeApprovedWholeTargets() {
        assertEquals(ModelCommandGate.Kind.OPEN_CLOCK,ModelCommandGate.validate("open_app","I want you to display my Clock application please").kind);
        blocked("Display my bank application", "Display my Clock application for payment", "Display my Clock application for 5 minutes", "Display my Clock application; open settings");
        assertFalse(ModelCommandGate.validate("explain","Display my Clock application").executable());
    }
    @Test public void reasonQuestionsRemainBoundedToLocalFocusNudges() {
        String[] requests={"Explain the reason for our study warning", "Why was I reminded during my active focus session?", "What caused Mira to warn me about concentration?", "Tell me why Mira gave my focus warning"};
        for(String text:requests)assertEquals(text,ModelCommandGate.Kind.EXPLAIN,ModelCommandGate.validate("explain",text).kind);
        blocked("Why was I warned?", "What caused you to remind me?", "Explain the reason for my bank warning", "Why was I warned during my flight?", "Tell me why Mira issued my payment warning", "Tell me why Mira gave my focus warning and open Calculator");
    }
    @Test public void statusQuestionsAndStudyDurationConsumeWholeFocusDomain() {
        String[] requests={"How much time remains in my focused work session?", "Show me how long I have been concentrating", "Display our concentration session overview", "What is the summary of my ongoing study session?"};
        for(String text:requests)assertEquals(text,ModelCommandGate.Kind.EXPLAIN,ModelCommandGate.validate("explain",text).kind);
        blocked("How much time remains in my cooking session?", "Show me how long my colleague has been studying", "Display our concentration session overview at 7 PM", "What is the summary of my study session and start it");
    }
    @Test public void newFormsCannotConsumeNegationConditionsQuotesOrUnrelatedTails() {
        blocked("I do not want a 17 minute concentration session", "Never display the Clock app", "If I ask I need a break from focus", "I need an alarm for 6:41 PM after dinner", "Say I'd like a timer for 83 seconds", "Translate \"I need a break from focus\"", "\"Display my Clock app\"", "I stopped my current work session yesterday", "Show how long I have been studying. Open settings", "I need a break from concentration\nopen clock");
    }
    @Test public void correctSemanticRouteStillCannotBeOverriddenByAnotherModelIntent() {
        String[][] pairs={{"start_focus","I want a 17 minute concentration session"},{"pause_focus","Let me take a break from my work session"},{"alarm","I need an alarm for 6:41 PM"},{"timer","I'd like a timer for 83 seconds"},{"open_app","Display my Clock app"},{"explain","What is the status of my concentration session"}};
        for(String[] pair:pairs)for(String intent:INTENTS)if(!intent.equals(pair[0]))assertFalse(pair[1]+" / "+intent,ModelCommandGate.validate(intent,pair[1]).executable());
        for(String[] pair:pairs)assertFalse(ModelCommandGate.validate("unknown",pair[1]).executable());
    }
    @Test public void slotsCannotDiscardSignsFractionsOrSecondArgumentsInNewNounForms() {
        blocked("I want a 0 second focus session", "I want a -17 minute concentration session", "I want a 1.5 minute concentration session", "I want a 17 minute concentration session for 83 seconds", "I need an alarm for 99:99", "I need an alarm for 6:41 PM 7:42 PM", "I'd like a timer for 7201 seconds", "I'd like a timer for half a minute", "I would like a timer for 17 minutes at 6:41 PM");
    }
}
