package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * A private, user-entered task guide. Steps are text, not LLM-generated commands.
 * Completing a step records the user's progress; it executes no external phone action.
 * This immutable value has no Android, persistence, permission or model dependencies.
 */
public final class TaskPlan {
    public static final int MAX_STEPS = 8;
    public static final int MAX_STEP_CHARS = 120;
    public static final int MAX_INPUT_CHARS = 1024;

    private final List<String> steps;
    private final int completedCount;

    private TaskPlan(List<String> steps, int completedCount) {
        this.steps = Collections.unmodifiableList(new ArrayList<>(steps));
        this.completedCount = completedCount;
    }

    /** Parses one step per line; blank lines are ignored and tabs become spaces. */
    public static TaskPlan parse(String input) {
        if (input == null || input.length() > MAX_INPUT_CHARS)
            throw new IllegalArgumentException("Use a checklist of at most 1024 characters.");
        validateText(input, true);
        List<String> parsed = new ArrayList<>();
        for (String line : input.split("\\r\\n|\\r|\\n", -1)) {
            String step = normalize(line);
            if (step.isEmpty()) continue;
            validateStep(step);
            if (parsed.size() == MAX_STEPS)
                throw new IllegalArgumentException("Use at most eight steps.");
            parsed.add(step);
        }
        if (parsed.isEmpty()) throw new IllegalArgumentException("Enter at least one step.");
        return new TaskPlan(parsed, 0);
    }

    /**
     * Restores explicitly supplied steps and progress with the same bounds.
     * Null/blank entries, embedded line breaks and invalid progress are rejected;
     * restoration never drops an entry or silently clamps corrupt progress.
     */
    public static TaskPlan fromSteps(List<String> steps, int completedCount) {
        if (steps == null || steps.isEmpty() || steps.size() > MAX_STEPS)
            throw new IllegalArgumentException("A checklist needs one to eight steps.");
        if (completedCount < 0 || completedCount > steps.size())
            throw new IllegalArgumentException("Checklist progress is invalid.");
        List<String> copy = new ArrayList<>(steps.size());
        long inputChars = steps.size() - 1;
        for (String raw : steps) {
            if (raw == null) throw new IllegalArgumentException("A checklist step is missing.");
            inputChars += raw.length();
            if (inputChars > MAX_INPUT_CHARS)
                throw new IllegalArgumentException("Use a checklist of at most 1024 characters.");
            validateText(raw, false);
            String step = normalize(raw);
            validateStep(step);
            copy.add(step);
        }
        return new TaskPlan(copy, completedCount);
    }

    public int completedCount() { return completedCount; }
    public int stepCount() { return steps.size(); }
    public String stepAt(int index) { return steps.get(index); }
    public List<String> steps() { return steps; }
    public boolean isComplete() { return completedCount == steps.size(); }
    public String currentStep() { return isComplete() ? null : steps.get(completedCount); }
    public TaskPlan completeCurrent() {
        return isComplete() ? this : new TaskPlan(steps, completedCount + 1);
    }
    public TaskPlan undoCompletion() {
        return completedCount == 0 ? this : new TaskPlan(steps, completedCount - 1);
    }

    private static void validateStep(String step) {
        if (step.isEmpty() || step.length() > MAX_STEP_CHARS)
            throw new IllegalArgumentException("Each step needs one to 120 characters.");
    }

    private static void validateText(String text, boolean allowLines) {
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (Character.isHighSurrogate(c)) {
                if (i + 1 >= text.length() || !Character.isLowSurrogate(text.charAt(i + 1)))
                    throw new IllegalArgumentException("Checklist text contains invalid Unicode.");
                i++;
            } else if (Character.isLowSurrogate(c)) {
                throw new IllegalArgumentException("Checklist text contains invalid Unicode.");
            } else if (c == '\t' || (allowLines && (c == '\n' || c == '\r'))) {
                continue;
            } else if (Character.isISOControl(c) || c == '\u2028' || c == '\u2029') {
                throw new IllegalArgumentException("Use plain checklist text without control characters.");
            }
        }
    }

    private static String normalize(String value) {
        String text = value.replace('\t', ' ');
        int start = 0, end = text.length();
        while (start < end && isSpace(text.codePointAt(start)))
            start += Character.charCount(text.codePointAt(start));
        while (end > start && isSpace(text.codePointBefore(end)))
            end -= Character.charCount(text.codePointBefore(end));
        return text.substring(start, end);
    }

    private static boolean isSpace(int codePoint) {
        return Character.isWhitespace(codePoint) || Character.isSpaceChar(codePoint);
    }
}
