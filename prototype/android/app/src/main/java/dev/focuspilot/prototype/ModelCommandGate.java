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
    private static final Pattern NEGATED = Pattern.compile("\\b(?:do not|don't|dont|never|not|no|avoid|without|cannot|can't|won't|wouldn't)\\b");
    private static final Pattern COMPOUND = Pattern.compile("\\b(?:and|then|also|or|but)\\b");
    private static final Pattern STOP = Pattern.compile("\\b(?:pause|stop|end|finish|halt|break|cancel|abort|dismiss|snooze|disable|remove|clear|reset|close|turn off)\\b");
    private static final Pattern START = Pattern.compile("\\b(?:start|begin|resume|activate)\\b");
    private static final Pattern CONDITIONAL = Pattern.compile("\\b(?:if|unless|when|after|before|later)\\b");
    private static final Pattern ASSERTION = Pattern.compile("\\b(?:is|was|were|has|have|had|means|meant|said|says|already|yesterday|previously|remaining|left|running|scheduled|ringing|expired|stopped|paused|started|ended|finished|cancelled|canceled|dismissed|snoozed|disabled)\\b");
    private static final String FOCUS_TARGET="(?:focus|concentrate|concentration|concentrating|study|studying|deep work|work session)";
    private static final String ARTICLES="(?:(?:a|an|the|my|our|new|current)\\s+)*";
    private static final Pattern FOCUS_START = Pattern.compile("^(?:(?:start|begin|resume|activate)\\s+"+ARTICLES+FOCUS_TARGET+"\\b|(?:focus|concentrate)(?:[.!?]*$|\\s+(?:for|now|on)\\b)|study(?:[.!?]*$|\\s+for\\b))");
    private static final Pattern FOCUS_PAUSE = Pattern.compile("^(?:pause|stop|end|finish|halt|cancel|abort)\\s+"+ARTICLES+FOCUS_TARGET+"\\b");
    private static final Pattern ALARM_REQUEST = Pattern.compile("^(?:(?:set|create|add|schedule|start)\\s+"+ARTICLES+"alarm\\b|wake\\s+me\\b|alarm\\s+(?:(?:at|for)\\s+)?\\d{1,2}:\\d{2})");
    private static final Pattern TIMER_REQUEST = Pattern.compile("^(?:(?:set|start|create|begin)\\s+"+ARTICLES+"(?:\\d{1,3}\\s*(?:minutes?|mins?|seconds?|secs?)\\s+)?(?:timer|countdown)\\b|(?:timer|countdown)\\s+(?:for\\s+)?\\d{1,3}\\s*(?:minutes?|mins?|seconds?|secs?)\\b)");
    private static final Pattern APP_REQUEST = Pattern.compile("^(?:open|launch|show|go to)\\s+"+ARTICLES+"(?:settings|calculator|clock)\\b");
    private static final Pattern TIME = Pattern.compile("(?<![\\d:])(\\d{1,2}):(\\d{2})(?:\\s*(am|pm))?(?![\\d:])");
    private static final Pattern DURATION = Pattern.compile("\\b(\\d{1,3})\\s*(minutes?|mins?|seconds?|secs?)\\b");

    public static Proposal validate(String intent, String original) {
        if(intent==null || original==null || original.trim().isEmpty() || original.length()>500) return unknown("A short command is required.");
        String input=original.toLowerCase(Locale.US).replace('\u2019','\'').trim().replaceAll("\\s+"," ")
            .replaceAll("(?<=\\d)[-\u2010\u2011](?=[a-z])"," ");
        if(NEGATED.matcher(input).find() || COMPOUND.matcher(input).find()) return unknown("Negated or multiple requests need clarification.");
        if(CONDITIONAL.matcher(input).find() || original.matches("(?s).*[;\\r\\n].*") || input.matches(".*[.!?]\\s+[a-z].*"))
            return unknown("Please give one immediate request; conditional or multiple steps need clarification.");
        if(input.matches(".*\\b(?:pay|transfer|delete|send|purchase|buy|password)\\b.*")) return unknown("This action is outside the phone allowlist.");
        if(input.matches("^(?:what|who|where|when|is|are)\\b.*")) return unknown("This appears to be a question, not an explicit phone action.");
        String request=requestBody(input);
        switch(intent) {
            case "start_focus":
                if(STOP.matcher(input).find()) return unknown("The model proposed starting, but the request asks to stop. Please clarify.");
                if(ASSERTION.matcher(input).find() || !FOCUS_START.matcher(request).find()) return unknown("Please explicitly ask to start focus, for example: Help me start studying.");
                if(input.matches(".*\\b(?:alarm|timer|countdown|settings|calculator|clock)\\b.*")) return unknown("Please choose one action. Say start focus for a focus session.");
                return new Proposal(Kind.START_FOCUS,0,0,0,"Start an open-ended focus session. A requested duration is not implemented here; use a separate timer.");
            case "pause_focus":
                if(START.matcher(input).find() || !STOP.matcher(input).find()) return unknown("The model proposed pausing without an explicit stop request. Please clarify.");
                if(ASSERTION.matcher(input).find() || !FOCUS_PAUSE.matcher(request).find()) return unknown("Please explicitly say pause focus or stop my study session.");
                return new Proposal(Kind.PAUSE_FOCUS,0,0,0,"Pause focus and stop any active background focus monitor.");
            case "alarm": {
                if(STOP.matcher(input).find()) return unknown("I can request a new alarm, but cannot cancel or change existing alarms. Please clarify in Clock.");
                if(ASSERTION.matcher(input).find() || !ALARM_REQUEST.matcher(request).find()) return unknown("Please explicitly ask to set an alarm or wake you at one clock time.");
                Matcher match=TIME.matcher(input);
                if(!match.find()) return unknown("Please specify a clock time such as 7:30 AM or 19:30. Dates and spoken-number times are not supported yet.");
                int hour=Integer.parseInt(match.group(1)), minute=Integer.parseInt(match.group(2)); String meridian=match.group(3);
                if(minute>59 || (meridian==null ? hour>23 : hour<1 || hour>12)) return unknown("Alarm time is outside its valid range.");
                if(meridian!=null) hour=hour%12+(meridian.equals("pm")?12:0);
                if(match.find() || input.matches(".*\\b(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\\b.*")) return unknown("Specify one time without a calendar date for this clock-only action.");
                return new Proposal(Kind.ALARM,hour,minute,0,String.format(Locale.US,"Open Clock with an alarm request for %02d:%02d. Creation is controlled by Clock and remains unverified.",hour,minute));
            }
            case "timer": {
                if(STOP.matcher(input).find()) return unknown("I can request a new timer, but cannot stop or change an existing timer. Please clarify in Clock.");
                if(ASSERTION.matcher(input).find() || !TIMER_REQUEST.matcher(request).find()) return unknown("Please explicitly ask to set a timer, for example: Set a 5 minute timer.");
                Matcher match=DURATION.matcher(input);
                if(!match.find()) return unknown("Specify one duration in digits, such as 5 minutes.");
                int amount=Integer.parseInt(match.group(1)); String unit=match.group(2); int seconds=amount*(unit.startsWith("min")?60:1);
                if(amount<1 || seconds>7200 || match.find()) return unknown("Timer must be a single duration from 1 second to 120 minutes.");
                return new Proposal(Kind.TIMER,0,0,seconds,"Open Clock with a "+seconds+" second timer request. Verify its result in Clock.");
            }
            case "open_app": {
                if(STOP.matcher(input).find() || ASSERTION.matcher(input).find() || !APP_REQUEST.matcher(request).find()) return unknown("Please explicitly ask to open one approved app.");
                int matches=(input.matches(".*\\bsettings\\b.*")?1:0)+(input.matches(".*\\bcalculator\\b.*")?1:0)+(input.matches(".*\\bclock\\b.*")?1:0);
                if(matches!=1) return unknown("Choose one approved app: Settings, Calculator or Clock.");
                Kind kind=input.contains("settings")?Kind.OPEN_SETTINGS:input.contains("calculator")?Kind.OPEN_CALCULATOR:Kind.OPEN_CLOCK;
                return new Proposal(kind,0,0,0,"Open the approved "+kind.name().substring(5).toLowerCase(Locale.US)+" app. Outcome is verified separately.");
            }
            case "explain": return new Proposal(Kind.EXPLAIN,0,0,0,"Show the local focus status and the separate decision inspector.");
            default: return unknown("The model abstained or returned an unsupported intent. Nothing will execute.");
        }
    }
    /** Bounded request wrappers; statements and quoted instructions keep their own head verb. */
    private static String requestBody(String input) {
        String body=input.replaceFirst("^(?:hey\\s+)?mira[,!]?\\s+","");
        body=body.replaceFirst("^please\\s+","");
        body=body.replaceFirst("^(?:(?:can|could|would|will)\\s+you\\s+|i\\s+(?:want|need)\\s+to\\s+|i(?:'d|\\s+would)\\s+like\\s+to\\s+|let(?:'s|\\s+us)\\s+)","");
        body=body.replaceFirst("^please\\s+","").replaceFirst("^help\\s+me\\s+","").replaceFirst("^please\\s+","");
        return body;
    }
}
