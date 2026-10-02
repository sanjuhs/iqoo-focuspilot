package dev.focuspilot.prototype;

import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Bounded deterministic fallback parser. Unknown commands abstain. */
public final class CommandParser {
    public enum Kind { START, PAUSE, ALARM, UNKNOWN }
    public static final class Command {
        public final Kind kind;
        public final int hour, minute;
        Command(Kind kind, int hour, int minute) { this.kind = kind; this.hour = hour; this.minute = minute; }
    }
    private static final Pattern ALARM = Pattern.compile("(?:set (?:an? )?)?alarm(?: (?:for|at))? (\\d{1,2})(?::(\\d{2}))?(?: (am|pm))?");
    public Command parse(String input) {
        if (input == null || input.length() > 120) return new Command(Kind.UNKNOWN, 0, 0);
        String value = input.trim().toLowerCase(Locale.US).replaceAll("\\s+", " ");
        if (value.matches("(?:start|resume)(?: focus| session)?|focus")) return new Command(Kind.START, 0, 0);
        if (value.matches("(?:pause|stop)(?: focus| session)?")) return new Command(Kind.PAUSE, 0, 0);
        Matcher match = ALARM.matcher(value);
        if (match.matches()) {
            int hour = Integer.parseInt(match.group(1));
            int minute = match.group(2) == null ? 0 : Integer.parseInt(match.group(2));
            String meridian = match.group(3);
            if (minute > 59 || (meridian == null ? hour > 23 : hour < 1 || hour > 12)) return new Command(Kind.UNKNOWN, 0, 0);
            if (meridian != null) hour = hour % 12 + (meridian.equals("pm") ? 12 : 0);
            return new Command(Kind.ALARM, hour, minute);
        }
        return new Command(Kind.UNKNOWN, 0, 0);
    }
}
