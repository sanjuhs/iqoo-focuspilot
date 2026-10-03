package dev.focuspilot.prototype;

import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Pre-event candidate only. Produces inert proposals for a separate explicit review. */
public final class UnitCommand {
    public static final String SYSTEM_PROMPT = StructuredCommand.SYSTEM_PROMPT
        .replace("start_focus with duration_seconds (0 means start/resume without a new duration; otherwise 1..7200)",
            "start_focus with amount and unit (amount 0 with unit none means start/resume without a new duration)")
        .replace("timer with duration_seconds 1..7200", "timer with positive amount and unit seconds/minutes/hours")
        .replace("Convert explicit seconds/minutes/hours and AM/PM correctly.",
            "Copy the original numeric quantity as an integer and its unit seconds/minutes/hours. Never multiply or convert duration units. Maximum is 7200 seconds, 120 minutes or 2 hours. Convert AM/PM correctly.")
        .replace("\"duration_seconds\":840", "\"amount\":14,\"unit\":\"minutes\"")
        .replace("\"duration_seconds\":300", "\"amount\":5,\"unit\":\"minutes\"");
    public static final String GRAMMAR = grammar();
    private static final String W = "[ \\t\\r\\n]*";
    private static final Pattern DURATION = Pattern.compile(W + "\\{" + W + "\"intent\"" + W + ":" + W
        + "\"(start_focus|timer)\"" + W + "," + W + "\"amount\"" + W + ":" + W
        + "(0|[1-9][0-9]{0,9})" + W + "," + W + "\"unit\"" + W + ":" + W
        + "\"(none|seconds|minutes|hours)\"" + W + "\\}" + W);
    private static final Pattern SOURCE_UNIT = Pattern.compile("\\b(seconds?|secs?|minutes?|mins?|hours?|hrs?)\\b");
    private UnitCommand() {}

    private static String quoted(String text) { return "\"\\\"" + text + "\\\"\""; }
    private static String grammar() {
        StringBuilder rules = new StringBuilder();
        for (String line : StructuredCommand.GRAMMAR.split("\n")) {
            if (line.startsWith("start ::=")) {
                rules.append("start ::= ").append(quoted("intent")).append(" ws \":\" ws ")
                    .append(quoted("start_focus")).append(" ws \",\" ws (untimed | span)\n");
            } else if (line.startsWith("timer ::=")) {
                rules.append("timer ::= ").append(quoted("intent")).append(" ws \":\" ws ")
                    .append(quoted("timer")).append(" ws \",\" ws span\n");
            } else if (!line.startsWith("duration ::=")) rules.append(line).append('\n');
        }
        String amount = quoted("amount") + " ws \":\" ws ";
        String unit = " ws \",\" ws " + quoted("unit") + " ws \":\" ws ";
        rules.append("untimed ::= ").append(amount).append("\"0\"").append(unit).append(quoted("none")).append('\n');
        rules.append("span ::= ").append(amount).append("positive").append(unit).append(quoted("seconds"))
            .append(" | ").append(amount).append("minutes").append(unit).append(quoted("minutes"))
            .append(" | ").append(amount).append("[12]").append(unit).append(quoted("hours")).append('\n');
        rules.append("minutes ::= [1-9] | [1-9][0-9] | \"1\"[01][0-9] | \"120\"\n");
        return rules.toString();
    }

    public static String renderPrompt(String original) {
        // The unchanged renderer performs whole-input bounds/Unicode checks and escaping.
        return StructuredCommand.renderPrompt(original).replace(StructuredCommand.SYSTEM_PROMPT, SYSTEM_PROMPT);
    }
    public static String guardReason(String original) { return StructuredCommand.guardReason(original); }

    public static final class Proposal {
        public final String intent, app, reason, unit;
        public final int hour, minute, durationSeconds, amount;
        public final boolean accepted;
        private final StructuredCommand.Proposal canonical;
        private Proposal(StructuredCommand.Proposal canonical, int amount, String unit, String reason) {
            this.canonical = canonical; this.intent = canonical.intent; this.app = canonical.app;
            this.hour = canonical.hour; this.minute = canonical.minute; this.durationSeconds = canonical.durationSeconds;
            this.accepted = canonical.accepted; this.amount = amount; this.unit = unit; this.reason = reason;
        }
        /** Existing normalized seconds schema; this is not permission to execute. */
        public String canonicalJson() { return canonical.canonicalJson(); }
    }

    public static Proposal parseResponse(String output) {
        if (output == null || output.length() > 1024) throw new IllegalArgumentException("Bounded JSON required");
        Matcher match = DURATION.matcher(output);
        if (!match.matches()) {
            StructuredCommand.Proposal parsed = StructuredCommand.parseResponse(output);
            if (parsed.intent.equals("start_focus") || parsed.intent.equals("timer"))
                throw new IllegalArgumentException("Duration requires exact intent, amount, unit keys in that order");
            return new Proposal(parsed, -1, null, parsed.reason);
        }
        String intent = match.group(1), unit = match.group(3);
        long amount = Long.parseLong(match.group(2));
        long seconds;
        if (unit.equals("none")) {
            if (!intent.equals("start_focus") || amount != 0) throw new IllegalArgumentException("Only untimed focus has zero/none");
            seconds = 0;
        } else {
            long multiplier = unit.equals("hours") ? 3600 : unit.equals("minutes") ? 60 : 1;
            // All parsed values are <=10 decimal digits; long multiplication cannot overflow.
            seconds = amount * multiplier;
            if (amount < 1 || seconds < 1 || seconds > 7200) throw new IllegalArgumentException("Duration outside 1..7200 seconds");
        }
        StructuredCommand.Proposal parsed = StructuredCommand.parseResponse("{\"intent\":\"" + intent
            + "\",\"duration_seconds\":" + seconds + "}");
        return new Proposal(parsed, (int) amount, unit, parsed.reason);
    }

    private static Proposal rejected(String reason) {
        return new Proposal(StructuredCommand.parseResponse("{\"intent\":\"unknown\"}"), -1, null, reason);
    }
    public static Proposal validate(String original, String output) {
        String reason = guardReason(original);
        if (reason != null) return rejected(reason);
        final Proposal parsed;
        try { parsed = parseResponse(output); }
        catch (IllegalArgumentException error) { return rejected("Malformed unit response: " + error.getMessage()); }
        // All direction, tool, clock/app, compound and original numeric evidence checks remain unchanged.
        StructuredCommand.Proposal checked = StructuredCommand.validate(original, parsed.canonicalJson());
        if (!checked.accepted) return new Proposal(checked, -1, null, checked.reason);
        if (parsed.unit != null && !parsed.unit.equals("none") && !quantityAgrees(original, parsed.amount, parsed.unit))
            return rejected("Quantity/unit must be copied from the original request");
        return new Proposal(checked, parsed.amount, parsed.unit, checked.reason);
    }

    private static boolean quantityAgrees(String original, int amount, String unit) {
        String source = original.toLowerCase(Locale.ROOT).replace('\u2019', '\'').replace('\u2010', '-')
            .replace('\u2011', '-').trim().replaceAll(" +", " ")
            .replaceAll("(?<=[a-z0-9])-(?=(?:seconds?|secs?|minutes?|mins?|hours?|hrs?)\\b)", " ");
        Matcher units = SOURCE_UNIT.matcher(source);
        if (!units.find()) return false;
        String matched = units.group(1);
        String sourceUnit = matched.startsWith("h") ? "hours" : matched.startsWith("min") ? "minutes" : "seconds";
        if (!sourceUnit.equals(unit)) return false;
        String prefix = source.substring(0, units.start()).trim();
        String[] words = prefix.split(" +");
        int value = -1;
        for (int count = 1; count <= Math.min(4, words.length); count++) {
            StringBuilder slot = new StringBuilder();
            for (int i = words.length - count; i < words.length; i++) {
                if (slot.length() > 0) slot.append(' ');
                slot.append(words[i]);
            }
            String text = slot.toString();
            int candidate = text.matches("[0-9]{1,4}") ? Integer.parseInt(text) : CommandNumberWords.parse(text);
            if (candidate >= 0) value = candidate;
        }
        return value == amount && !units.find();
    }
}
