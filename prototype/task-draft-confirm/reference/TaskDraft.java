package dev.focuspilot.prototype;

import java.util.ArrayList;
import java.util.List;
import java.util.HashSet;
import java.util.Locale;

/**
 * A review-only, local model draft contract, separate from command authorization.
 * Parsing creates unsaved checklist text with zero progress; it executes no action.
 * Structure is validated here, not truth, usefulness or safety of model suggestions.
 * The caller must also require actual EOS and bind the exact goal/revision to review.
 */
public final class TaskDraft {
    public static final int MAX_GOAL_CHARS = 120;
    public static final int MAX_OUTPUT_CHARS = 1024;
    public static final int MAX_NEW_TOKENS = 128;
    public static final int GENERATED_STEP_CHAR_LIMIT = 80;
    public static final String SYSTEM_PROMPT = "Turn the user's productivity goal into a draft checklist. "
        + "Output only JSON: {\"steps\":[\"first step\",\"second step\",\"third step\"]}. "
        + "Use exactly three different short, practical steps, each at most 80 characters. Respect the user's constraints. "
        + "If details or access are missing, make the first step collect the needed details; do not invent them. "
        + "Suggest steps the user can take; never claim anything was accessed or completed. "
        + "Only harmful requests or requests unrelated to productivity should return {\"steps\":[]}.\n"
        + "Example goal: Prepare tomorrow's presentation\n"
        + "Example output: {\"steps\":[\"Choose the audience and main message\",\"Outline three key points\",\"Rehearse and check the slides\"]}\n"
        + "Example goal: Plan study time without using Instagram\n"
        + "Example output: {\"steps\":[\"List the subjects and available time\",\"Choose one short study block\",\"Put Instagram aside and review progress\"]}\n"
        + "Example goal: Steal my coworker's password\nExample output: {\"steps\":[]}";
    /** Exactly three bounded JSON strings, or an explicit empty-array decline.
     * Unicode and valid JSON escapes are allowed; the parser independently checks
     * decoded UTF-16/controls and rejects decline, malformed or unusable content. */
    public static final String GRAMMAR = "root ::= \"{\\\"steps\\\":[\" (step \",\" step \",\" step)? \"]}\"\nstep ::= \"\\\"\" json-char{1,80} \"\\\"\"\njson-char ::= [^\"\\\\\\x00-\\x1F\\x7F-\\x9F\\u2028\\u2029] | \"\\\\\" ([\"\\\\/bfnrt] | \"u\" [0-9a-fA-F]{4})\n";

    private TaskDraft() { }

    /** Returns the exact supplied identity; validation never trims a saved goal. */
    public static String validatedGoal(String goal) {
        if (goal == null || goal.isEmpty() || goal.length() > MAX_GOAL_CHARS)
            throw new IllegalArgumentException("Save a task of one to 120 characters first.");
        boolean nonblank = false;
        for (int i = 0; i < goal.length(); i++) {
            char c = goal.charAt(i);
            if (Character.isHighSurrogate(c)) {
                if (i + 1 >= goal.length() || !Character.isLowSurrogate(goal.charAt(i + 1)))
                    throw new IllegalArgumentException("The task contains invalid Unicode.");
                nonblank = true; i++;
            } else if (Character.isLowSurrogate(c) || Character.isISOControl(c)
                    || c == '\u2028' || c == '\u2029') {
                throw new IllegalArgumentException("Use a saved task on one plain text line.");
            } else if (!Character.isWhitespace(c) && !Character.isSpaceChar(c)) {
                nonblank = true;
            }
        }
        if (!nonblank) throw new IllegalArgumentException("Save a nonblank task first.");
        return goal;
    }

    public static String renderPrompt(String goal) {
        String data = validatedGoal(goal).replace("<|", "< | ").replace("|>", " | >");
        return "<|im_start|>system\n" + SYSTEM_PROMPT + "<|im_end|>\n<|im_start|>user\nGoal: "
            + data + "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n";
    }

    /** Rejects declines and every shape except one object with three valid steps. */
    public static TaskPlan parseOutput(String text) {
        if (text == null || text.isEmpty() || text.length() > MAX_OUTPUT_CHARS)
            throw new IllegalArgumentException("The model did not provide a bounded checklist draft.");
        JsonReader reader = new JsonReader(text);
        reader.expect('{');
        if (!"steps".equals(reader.string())) throw reader.invalid();
        reader.expect(':'); reader.expect('[');
        List<String> steps = new ArrayList<>(3);
        for (int i = 0; i < 3; i++) {
            if (i > 0) reader.expect(',');
            steps.add(reader.string());
        }
        reader.expect(']'); reader.expect('}'); reader.whitespace();
        if (reader.index != text.length()) throw reader.invalid();
        TaskPlan plan=TaskPlan.fromSteps(steps,0);
        HashSet<String> distinct=new HashSet<>();
        for(String step:plan.steps())if(!distinct.add(step.toLowerCase(Locale.ROOT)))throw reader.invalid();
        return plan;
    }

    /** A full-string JSON reader for this single bounded schema, not a JSON search. */
    private static final class JsonReader {
        private final String text;
        private int index;
        JsonReader(String text) { this.text = text; }
        IllegalArgumentException invalid() {
            return new IllegalArgumentException("No usable three-step draft. Review or write your own checklist.");
        }
        void whitespace() {
            while (index < text.length()) {
                char c = text.charAt(index);
                if (c != ' ' && c != '\t' && c != '\r' && c != '\n') break;
                index++;
            }
        }
        void expect(char expected) {
            whitespace();
            if (index >= text.length() || text.charAt(index++) != expected) throw invalid();
        }
        String string() {
            expect('"'); StringBuilder decoded = new StringBuilder();
            while (index < text.length()) {
                char c = text.charAt(index++);
                if (c == '"') return decoded.toString();
                if (c < 0x20) throw invalid();
                if (c != '\\') { decoded.append(c); continue; }
                if (index == text.length()) throw invalid();
                switch (text.charAt(index++)) {
                    case '"': decoded.append('"'); break;
                    case '\\': decoded.append('\\'); break;
                    case '/': decoded.append('/'); break;
                    case 'b': decoded.append('\b'); break;
                    case 'f': decoded.append('\f'); break;
                    case 'n': decoded.append('\n'); break;
                    case 'r': decoded.append('\r'); break;
                    case 't': decoded.append('\t'); break;
                    case 'u':
                        if (text.length() - index < 4) throw invalid();
                        int value = 0;
                        for (int i = 0; i < 4; i++) {
                            char digit = text.charAt(index++);
                            int hex = digit >= '0' && digit <= '9' ? digit - '0'
                                : digit >= 'a' && digit <= 'f' ? digit - 'a' + 10
                                : digit >= 'A' && digit <= 'F' ? digit - 'A' + 10 : -1;
                            if (hex < 0) throw invalid();
                            value = value * 16 + hex;
                        }
                        decoded.append((char) value); break;
                    default: throw invalid();
                }
            }
            throw invalid();
        }
    }
}
