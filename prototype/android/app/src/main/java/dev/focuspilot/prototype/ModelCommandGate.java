package dev.focuspilot.prototype;

import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Model intent is a proposal. This independent gate validates original text slots. */
public final class ModelCommandGate {
    public enum Kind { START_FOCUS, PAUSE_FOCUS, ALARM, TIMER, OPEN_SETTINGS, OPEN_CALCULATOR, OPEN_CLOCK, EXPLAIN, UNKNOWN }
    public static final class Proposal {
        public final Kind kind;
        public final int hour, minute, seconds;
        public final String preview;
        Proposal(Kind kind, int hour, int minute, int seconds, String preview) {
            this.kind=kind; this.hour=hour; this.minute=minute; this.seconds=seconds; this.preview=preview;
        }
        public boolean executable() { return kind!=Kind.UNKNOWN; }
    }
    private static Proposal unknown(String reason) { return new Proposal(Kind.UNKNOWN,0,0,0,reason); }
    private static final Pattern NEGATED = Pattern.compile("\\b(?:do not|don't|dont|never|not)\\b");
    private static final Pattern COMPOUND = Pattern.compile("\\b(?:and|then|also)\\b");
    private static final Pattern STOP = Pattern.compile("\\b(?:pause|stop|end|finish|halt|break)\\b");
    private static final Pattern START = Pattern.compile("\\b(?:start|begin|resume|activate)\\b");
    private static final Pattern TIME = Pattern.compile("(?<![\\d:])(\\d{1,2}):(\\d{2})(?:\\s*(am|pm))?(?![\\d:])");
    private static final Pattern DURATION = Pattern.compile("\\b(\\d{1,3})\\s*(minutes?|mins?|seconds?|secs?)\\b");

    public static Proposal validate(String intent, String original) {
        if(intent==null || original==null || original.trim().isEmpty() || original.length()>500) return unknown("A short command is required.");
        String input=original.toLowerCase(Locale.US).replace('\u2019','\'').trim();
        if(NEGATED.matcher(input).find() || COMPOUND.matcher(input).find()) return unknown("Negated or multiple requests need clarification.");
        if(input.matches(".*\\b(?:pay|transfer|delete|send|purchase|buy|password)\\b.*")) return unknown("This action is outside the phone allowlist.");
        if(input.matches("^(?:what|who|where|when|is|are)\\b.*")) return unknown("This appears to be a question, not an explicit phone action.");
        switch(intent) {
            case "start_focus":
                if(STOP.matcher(input).find()) return unknown("The model proposed starting, but the request asks to stop. Please clarify.");
                if(!input.matches(".*\\b(?:focus|concentrate|concentration|study|deep work|work session)\\b.*")) return unknown("No explicit focus request found. Please say start focus.");
                return new Proposal(Kind.START_FOCUS,0,0,0,"Start an open-ended focus session. A requested duration is not implemented here; use a separate timer.");
            case "pause_focus":
                if(START.matcher(input).find() || !STOP.matcher(input).find()) return unknown("The model proposed pausing without an explicit stop request. Please clarify.");
                if(!input.matches(".*\\b(?:focus|concentration|study|work session)\\b.*")) return unknown("No explicit focus request found. Please say pause focus.");
                return new Proposal(Kind.PAUSE_FOCUS,0,0,0,"Pause focus and stop any active background focus monitor.");
            case "alarm": {
                if(!input.matches(".*\\b(?:alarm|wake me)\\b.*")) return unknown("No explicit alarm request found.");
                Matcher match=TIME.matcher(input);
                if(!match.find()) return unknown("Please specify a clock time such as 7:30 AM or 19:30. Dates and spoken-number times are not supported yet.");
                int hour=Integer.parseInt(match.group(1)), minute=Integer.parseInt(match.group(2)); String meridian=match.group(3);
                if(minute>59 || (meridian==null ? hour>23 : hour<1 || hour>12)) return unknown("Alarm time is outside its valid range.");
                if(meridian!=null) hour=hour%12+(meridian.equals("pm")?12:0);
                if(match.find() || input.matches(".*\\b(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\\b.*")) return unknown("Specify one time without a calendar date for this clock-only action.");
                return new Proposal(Kind.ALARM,hour,minute,0,String.format(Locale.US,"Open Clock with an alarm request for %02d:%02d. Creation is controlled by Clock and remains unverified.",hour,minute));
            }
            case "timer": {
                if(!input.matches(".*\\b(?:timer|countdown)\\b.*")) return unknown("No explicit timer request found.");
                Matcher match=DURATION.matcher(input);
                if(!match.find()) return unknown("Specify one duration in digits, such as 5 minutes.");
                int amount=Integer.parseInt(match.group(1)); String unit=match.group(2); int seconds=amount*(unit.startsWith("min")?60:1);
                if(amount<1 || seconds>7200 || match.find()) return unknown("Timer must be a single duration from 1 second to 120 minutes.");
                return new Proposal(Kind.TIMER,0,0,seconds,"Open Clock with a "+seconds+" second timer request. Verify its result in Clock.");
            }
            case "open_app": {
                if(!input.matches(".*\\b(?:open|launch|show|go to)\\b.*")) return unknown("No explicit app-opening request found.");
                int matches=(input.contains("settings")?1:0)+(input.contains("calculator")?1:0)+(input.contains("clock")?1:0);
                if(matches!=1) return unknown("Choose one approved app: Settings, Calculator or Clock.");
                Kind kind=input.contains("settings")?Kind.OPEN_SETTINGS:input.contains("calculator")?Kind.OPEN_CALCULATOR:Kind.OPEN_CLOCK;
                return new Proposal(kind,0,0,0,"Open the approved "+kind.name().substring(5).toLowerCase(Locale.US)+" app. Outcome is verified separately.");
            }
            case "explain": return new Proposal(Kind.EXPLAIN,0,0,0,"Show the local focus status and the separate decision inspector.");
            default: return unknown("The model abstained or returned an unsupported intent. Nothing will execute.");
        }
    }
}
