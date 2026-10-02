package dev.focuspilot.prototype;

/** Bounded editable text only. A handoff grants no recording, inference or action. */
public final class CommandDraftHandoff {
    public static final String EXTRA_DRAFT = "dev.focuspilot.prototype.COMMAND_DRAFT";
    public static final int MAX_CHARS = 500;

    private CommandDraftHandoff() { }

    /** Preserves the exact text; invalid or overlong requests are never truncated. */
    public static String validatedDraft(String text) {
        if (!restorableEdit(text) || text.codePoints().allMatch(c -> Character.isWhitespace(c) || Character.isSpaceChar(c)))
            throw new IllegalArgumentException("Enter a command draft of 1–500 characters first.");
        return text;
    }

    /** Recreation always prefers edits, including deliberate emptiness, over old Intent data. */
    public static String initialDraft(String incoming, String restored, boolean recreated) {
        if (recreated) return restorableEdit(restored) ? restored : "";
        return incoming == null ? null : validatedDraft(incoming);
    }

    /** Empty unfinished edits can be restored. Oversize/corrupt state is rejected whole. */
    public static boolean restorableEdit(String text) {
        if (text == null || text.length() > MAX_CHARS) return false;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (Character.isHighSurrogate(c)) {
                if (i + 1 >= text.length() || !Character.isLowSurrogate(text.charAt(i + 1))) return false;
                i++;
            } else if (Character.isLowSurrogate(c) || (Character.isISOControl(c) && c != '\t' && c != '\r' && c != '\n')) {
                return false;
            }
        }
        return true;
    }
}
