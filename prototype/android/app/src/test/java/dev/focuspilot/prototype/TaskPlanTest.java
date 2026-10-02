package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import org.junit.Test;
import static org.junit.Assert.*;

public final class TaskPlanTest {
    private static void invalid(Runnable operation) {
        try { operation.run(); fail("Invalid checklist should be rejected"); }
        catch (IllegalArgumentException expected) { }
    }

    @Test public void lineParsingNormalizesWhitespaceWithoutRewritingUserSteps() {
        TaskPlan plan = TaskPlan.parse("\t Read chapter \r\n\r\n Draft\tnotes \n\u00a0Review\u3000");
        assertEquals(Arrays.asList("Read chapter", "Draft notes", "Review"), plan.steps());
        assertEquals("Read chapter", plan.currentStep());
        assertEquals(0, plan.completedCount());
    }

    @Test public void emptyPlansAndNinthStepAreRejected() {
        invalid(() -> TaskPlan.parse(null));
        invalid(() -> TaskPlan.parse("\r\n\t\u00a0\u3000"));
        String eight = "a\nb\nc\nd\ne\nf\ng\nh";
        assertEquals(8, TaskPlan.parse(eight).stepCount());
        invalid(() -> TaskPlan.parse(eight + "\ni"));
    }

    @Test public void originalInputBoundIncludesBlankLines() {
        assertEquals(1, TaskPlan.parse("x" + "\n".repeat(1023)).stepCount());
        invalid(() -> TaskPlan.parse("x" + "\n".repeat(1024)));
    }

    @Test public void unicodeStepLimitCountsUtf16UnitsAndPreservesPairs() {
        String exact = "\uD83D\uDE42".repeat(60);
        assertEquals(exact, TaskPlan.parse(exact).currentStep());
        assertEquals(120, exact.length());
        invalid(() -> TaskPlan.parse(exact + "a"));
        assertEquals("पढ़ना", TaskPlan.parse(" पढ़ना ").currentStep());
    }

    @Test public void invalidUnicodeAndControlsCannotHideInTrimmedText() {
        for (String text : new String[]{"\u0000read", "read\u007f", "read\u0085", "read\u2028next", "\uD800read", "read\uDC00", "read\uD800"})
            invalid(() -> TaskPlan.parse(text));
    }

    @Test public void completingAndUndoingProduceIndependentBoundedProgress() {
        TaskPlan initial = TaskPlan.parse("Read\nWrite");
        TaskPlan first = initial.completeCurrent();
        TaskPlan complete = first.completeCurrent();
        assertEquals("Read", initial.currentStep());
        assertEquals("Write", first.currentStep());
        assertEquals(2, complete.completedCount());
        assertTrue(complete.isComplete());
        assertNull(complete.currentStep());
        assertSame(complete, complete.completeCurrent());
        assertSame(initial, initial.undoCompletion());
        TaskPlan undone = complete.undoCompletion();
        assertEquals("Write", undone.currentStep());
        assertTrue(complete.isComplete());
        assertEquals(0, undone.undoCompletion().completedCount());
    }

    @Test public void restoredProgressIsValidatedRatherThanClamped() {
        TaskPlan done = TaskPlan.fromSteps(Arrays.asList("Read", "Write"), 2);
        assertTrue(done.isComplete());
        assertNull(done.currentStep());
        assertEquals("Write", done.undoCompletion().currentStep());
        assertEquals("Write", TaskPlan.fromSteps(Arrays.asList("Read", "Write"), 1).currentStep());
        invalid(() -> TaskPlan.fromSteps(Collections.singletonList("Read"), -1));
        invalid(() -> TaskPlan.fromSteps(Collections.singletonList("Read"), 2));
    }

    @Test public void restorationRejectsCorruptEntriesAndInputBounds() {
        invalid(() -> TaskPlan.fromSteps(null, 0));
        invalid(() -> TaskPlan.fromSteps(Collections.emptyList(), 0));
        invalid(() -> TaskPlan.fromSteps(Arrays.asList("Read", null), 0));
        invalid(() -> TaskPlan.fromSteps(Collections.singletonList(" \t "), 0));
        invalid(() -> TaskPlan.fromSteps(Collections.singletonList("Read\nWrite"), 0));
        invalid(() -> TaskPlan.fromSteps(Collections.singletonList("a".repeat(121)), 0));
        invalid(() -> TaskPlan.fromSteps(Collections.singletonList(" ".repeat(1024) + "x"), 0));
        invalid(() -> TaskPlan.fromSteps(Collections.singletonList("\uD800"), 0));
        invalid(() -> TaskPlan.fromSteps(Collections.nCopies(9, "Read"), 0));
    }

    @Test public void callerMutationsCannotChangePlanOrExposeMutableSteps() {
        ArrayList<String> authored = new ArrayList<>(Arrays.asList("Read", "Write"));
        TaskPlan plan = TaskPlan.fromSteps(authored, 0);
        authored.set(0, "Changed"); authored.clear();
        assertEquals(Arrays.asList("Read", "Write"), plan.steps());
        try { plan.steps().add("Injected"); fail("Steps must be immutable"); }
        catch (UnsupportedOperationException expected) { }
        try { plan.stepAt(2); fail("Invalid step index must fail"); }
        catch (IndexOutOfBoundsException expected) { }
    }

    @Test public void actionLikeTextRemainsAnAuthoredGuideAndProgressOnly() {
        TaskPlan plan = TaskPlan.parse("Open my notes\nSend the draft after reviewing it");
        TaskPlan next = plan.completeCurrent();
        assertEquals("Send the draft after reviewing it", next.currentStep());
        assertEquals("Open my notes", plan.currentStep());
        assertEquals(2, next.stepCount());
    }
}
