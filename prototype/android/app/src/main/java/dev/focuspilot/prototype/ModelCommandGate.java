package dev.focuspilot.prototype;

import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Model intent is a proposal. Whole original requests and their slots are validated independently. */
public final class ModelCommandGate {
    public enum Kind { START_FOCUS, PAUSE_FOCUS, ALARM, TIMER, OPEN_SETTINGS, OPEN_CALCULATOR, OPEN_CLOCK, EXPLAIN, UNKNOWN }
    public static final class Proposal {
        public final Kind kind;
        /** START_FOCUS: 0 resumes existing focus; 1..7200 replaces its countdown.
         * TIMER: Clock countdown duration. ALARM: hour/minute clock slots. */
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
    private static final Pattern CONDITIONAL = Pattern.compile("\\b(?:if|unless|when|after|before|later)\\b");
    private static final String ARTICLE="(?:(?:a|an|the|my|our|new|this)\\s+)?(?:(?:current|ongoing|active)\\s+)?";
    private static final String DESIRE="(?:i (?:want|need|would like)|i'd like)";
    private static final String FOCUS="(?:focus(?:\\s+(?:mode|session|time))?|concentration(?:\\s+(?:mode|session))?|concentrating|study(?:\\s+session)?|studying|(?:deep work|focused work)(?:\\s+session)?|work session)";
    private static final String NUMBER="(?:[0-9]{1,4}|[a-z]+(?:[ -][a-z]+)*)";
    private static final String DURATION=NUMBER+"\\s*(?:minutes?|mins?|seconds?|secs?)";
    private static final Pattern DURATION_SLOT=Pattern.compile("^("+NUMBER+")\\s*(minutes?|mins?|seconds?|secs?)$");
    // One complete supported form is consumed; slot text is never found as a substring.
    private static final Pattern FOCUS_START=Pattern.compile("^(?:(?:start|begin|resume|activate|enable)\\s+"+ARTICLE+FOCUS+"|(?:focus|concentrate|study)|(?:get back to|return to)\\s+"+ARTICLE+"(?:"+FOCUS+"|work)|put me in focus mode)(?:\\s+for\\s+("+DURATION+"))?$");
    private static final Pattern FOCUS_PREFIX_DURATION=Pattern.compile("^(?:start|begin|resume|activate|enable|"+DESIRE+")\\s+"+ARTICLE+"("+DURATION+")\\s+"+FOCUS+"$");
    private static final Pattern FOCUS_GIVE=Pattern.compile("^give me\\s+"+ARTICLE+"("+DURATION+")(?:\\s+of)?\\s+(?:focus|concentration|study|deep work|focused work)(?:\\s+(?:time|session))?$");
    private static final Pattern FOCUS_PAUSE=Pattern.compile("^(?:(?:pause|stop|end|finish|halt|cancel|abort|suspend)\\s+"+ARTICLE+"(?:"+FOCUS+"|(?:focus|concentration) (?:timer|countdown))|(?:take|"+DESIRE+")\\s+"+ARTICLE+"break from\\s+"+ARTICLE+"(?:"+FOCUS+"|work)|(?:take|give me)\\s+"+ARTICLE+"(?:focus|study|work) break)$");
    private static final Pattern ALARM_REQUEST=Pattern.compile("^(?:(?:set|create|add|schedule|start|"+DESIRE+")\\s+"+ARTICLE+"alarm\\s+(?:(?:at|for)\\s+)?|wake me(?: up)?\\s+(?:at|for)\\s+|alarm\\s+(?:(?:at|for)\\s+)?)(.+)$");
    private static final Pattern ALARM_PREFIX_TIME=Pattern.compile("^(?:set|create|add|schedule)\\s+"+ARTICLE+"(.+)\\s+alarm$");
    private static final Pattern TIMER_REQUEST=Pattern.compile("^(?:(?:set|start|create|begin|"+DESIRE+")\\s+"+ARTICLE+"(?:timer|countdown)|(?:timer|countdown)|count down)\\s+(?:for\\s+)?("+DURATION+")$");
    private static final Pattern TIMER_PREFIX_DURATION=Pattern.compile("^(?:set|start|create|begin|give me)\\s+"+ARTICLE+"("+DURATION+")\\s+(?:timer|countdown)$");
    private static final Pattern APP_REQUEST=Pattern.compile("^(?:open|launch|show|display|go to|bring up|take me to)\\s+"+ARTICLE+"(settings|calculator|clock)(?:\\s+(?:app|application))?$");
    private static final Pattern DIGIT_TIME=Pattern.compile("^([0-9]{1,2}):([0-9]{2})$");
    private static final Pattern MERIDIAN=Pattern.compile("\\s*([ap])\\.?\\s*m\\.?$");
    private static final String FOCUS_INFO="(?:(?:focus|concentration|deep work|focused work|study)\\s+session\\s+overview|focus(?:\\s+(?:mode|session|status|summary|stats|nudge|warning|reminder|overview))?|concentration(?:\\s+(?:session|status|summary|nudge|warning|reminder|overview))?|(?:deep work|focused work)(?:\\s+(?:session|status|summary|overview))?|study\\s+(?:session|status|nudge|warning|reminder|summary|overview))";
    private static final Pattern EXPLAIN_FOCUS=Pattern.compile("^(?:(?:explain|show|display)(?:\\s+me)?\\s+|tell me(?: about)?\\s+|what is\\s+|what's\\s+|how is\\s+)"+ARTICLE+FOCUS_INFO+"$");
    private static final Pattern EXPLAIN_NUDGE=Pattern.compile("^(?:(?:explain )?why did (?:you|mira) (?:nudge|warn|remind) me(?: (?:about|during) (?:my )?focus)?|why was i nudged|(?:explain )?(?:why did|what caused) "+ARTICLE+FOCUS_INFO+"(?: (?:appear|happen|occur))?|explain why "+ARTICLE+FOCUS_INFO+" (?:appeared|happened|occurred))$");
    private static final Pattern EXPLAIN_TIME=Pattern.compile("^(?:how much (?:focus|concentration|study) time (?:is left|remains|have i completed)|how is my focus going)$");
    // Complete focus-domain questions only; no keyword or slot substring extraction.
    private static final Pattern EXPLAIN_DETAIL=Pattern.compile("^(?:explain (?:the )?reason for "+ARTICLE+FOCUS_INFO+"|why was i (?:nudged|warned|reminded) (?:about|during) "+ARTICLE+FOCUS+"|what caused (?:you|mira) to (?:nudge|warn|remind) me (?:about|during) "+ARTICLE+FOCUS+"|(?:tell me|explain) why (?:you|mira) (?:issued|gave) "+ARTICLE+FOCUS_INFO+"|how much time (?:is left|remains) in "+ARTICLE+FOCUS+"|(?:show|display)(?: me)? how long i have been (?:studying|concentrating)|(?:what is|what's) "+ARTICLE+"(?:status|summary|overview) of "+ARTICLE+FOCUS+")$");

    public static Proposal validate(String intent, String original) {
        if(intent==null || original==null || original.trim().isEmpty() || original.length()>500)
            return unknown("A short command is required.");
        for(int i=0;i<original.length();i++) {
            char c=original.charAt(i);
            if(Character.isISOControl(c) || c=='\u2028' || c=='\u2029')
                return unknown("Please give one request on one line.");
        }
        String input=original.toLowerCase(Locale.US).replace('\u2019','\'')
            .replace('\u2010','-').replace('\u2011','-').trim().replaceAll(" +"," ")
            .replaceAll("(?<=[0-9])-(?=[a-z])"," ")
            .replaceAll("(?<=[a-z])-(?=(?:minutes?|mins?|seconds?|secs?)\\b)"," ");
        if(NEGATED.matcher(input).find() || COMPOUND.matcher(input).find())
            return unknown("Negated or multiple requests need clarification.");
        if(CONDITIONAL.matcher(input).find())
            return unknown("Please give one immediate request; conditional steps need clarification.");
        if(input.matches(".*\\b(?:pay|transfer|delete|erase|send|purchase|buy|password)\\b.*"))
            return unknown("This action is outside the phone allowlist.");
        String request=requestBody(input);
        switch(intent) {
            case "start_focus": return startFocus(request);
            case "pause_focus":
                if(!FOCUS_PAUSE.matcher(request).matches())
                    return unknown("Please ask to pause focus, stop your study session or take a study break.");
                return new Proposal(Kind.PAUSE_FOCUS,0,0,0,"Pause focus and stop any active background focus monitor.");
            case "alarm": return alarm(request);
            case "timer": return timer(request);
            case "open_app": {
                Matcher match=APP_REQUEST.matcher(request);
                if(!match.matches()) return unknown("Please ask to open one approved app: Settings, Calculator or Clock.");
                String app=match.group(1);
                Kind kind=app.equals("settings")?Kind.OPEN_SETTINGS:app.equals("calculator")?Kind.OPEN_CALCULATOR:Kind.OPEN_CLOCK;
                return new Proposal(kind,0,0,0,"Open the approved "+app+" app. Outcome is verified separately.");
            }
            case "explain":
                if(!EXPLAIN_FOCUS.matcher(request).matches() && !EXPLAIN_NUDGE.matcher(request).matches() && !EXPLAIN_TIME.matcher(request).matches() && !EXPLAIN_DETAIL.matcher(request).matches())
                    return unknown("Please ask for focus status or an explanation of a focus nudge.");
                return new Proposal(Kind.EXPLAIN,0,0,0,"Show the local focus status and the separate decision inspector.");
            default: return unknown("The model abstained or returned an unsupported intent. Nothing will execute.");
        }
    }

    private static Proposal startFocus(String request) {
        Matcher ordinary=FOCUS_START.matcher(request), prefix=FOCUS_PREFIX_DURATION.matcher(request), give=FOCUS_GIVE.matcher(request);
        String duration;
        if(ordinary.matches()) duration=ordinary.group(1);
        else if(prefix.matches()) duration=prefix.group(1);
        else if(give.matches()) duration=give.group(1);
        else return unknown("Ask to start focus, for example: Help me focus for twenty-five minutes. Give one complete request.");
        int seconds=duration==null?0:durationSeconds(duration);
        if(seconds<0) return unknown("Use one whole duration from 1 second to 120 minutes. Fractions, signs, hours and multiple durations need clarification.");
        String preview=seconds==0
            ? "Start or resume focus. A paused countdown resumes; otherwise focus runs until you pause it."
            : "Start a focus countdown for "+seconds+" seconds, replacing any current countdown while preserving elapsed focus time. It stops focus when the app process can run; background timing is not an exact alarm.";
        return new Proposal(Kind.START_FOCUS,0,0,seconds,preview);
    }

    private static Proposal timer(String request) {
        Matcher ordinary=TIMER_REQUEST.matcher(request), prefix=TIMER_PREFIX_DURATION.matcher(request);
        String duration;
        if(ordinary.matches()) duration=ordinary.group(1);
        else if(prefix.matches()) duration=prefix.group(1);
        else return unknown("Ask to set one timer, for example: Set a five-minute timer. Existing timer changes need Clock.");
        int seconds=durationSeconds(duration);
        if(seconds<0) return unknown("Timer must have one whole duration from 1 second to 120 minutes.");
        return new Proposal(Kind.TIMER,0,0,seconds,"Open Clock with a "+seconds+" second timer request. Verify its result in Clock.");
    }

    private static int durationSeconds(String duration) {
        Matcher match=DURATION_SLOT.matcher(duration);
        if(!match.matches()) return -1;
        String number=match.group(1).trim();
        int amount=number.matches("[0-9]{1,4}")?Integer.parseInt(number):CommandNumberWords.parse(number);
        if(amount<1) return -1;
        int seconds=amount*(match.group(2).startsWith("min")?60:1);
        return seconds<=7200?seconds:-1;
    }

    private static Proposal alarm(String request) {
        Matcher ordinary=ALARM_REQUEST.matcher(request), prefix=ALARM_PREFIX_TIME.matcher(request);
        String time;
        if(ordinary.matches()) time=ordinary.group(1);
        else if(prefix.matches()) time=prefix.group(1);
        else return unknown("Ask to set an alarm at one time. Existing alarm changes need Clock.");
        int[] slots=clockTime(time);
        if(slots==null) return unknown("Use one clock time, such as 7:30 PM or seven thirty PM. Spoken times need AM or PM; dates, fractions and multiple times need clarification.");
        return new Proposal(Kind.ALARM,slots[0],slots[1],0,String.format(Locale.US,
            "Open Clock with an alarm request for %02d:%02d. Creation is controlled by Clock and remains unverified.",slots[0],slots[1]));
    }

    /** Colon times use 24-hour notation when unmarked; other times require a meridian. */
    private static int[] clockTime(String value) {
        String time=value.trim(); Matcher meridian=MERIDIAN.matcher(time); String period=null;
        if(meridian.find()) { period=meridian.group(1); time=time.substring(0,meridian.start()).trim(); }
        Matcher digits=DIGIT_TIME.matcher(time);
        int hour=-1, minute=-1;
        if(digits.matches()) {
            hour=Integer.parseInt(digits.group(1)); minute=Integer.parseInt(digits.group(2));
        } else if(period!=null) {
            String hourOnly=time.replaceFirst(" o'clock$","");
            int number=CommandNumberWords.parse(hourOnly);
            if(number>=1 && number<=12) { hour=number; minute=0; }
            else {
                // Every split is checked; accept only a unique valid hour/minute pair.
                for(int index=0;index<time.length();index++) {
                    if(time.charAt(index)!=' ') continue;
                    int h=CommandNumberWords.parse(time.substring(0,index));
                    String minuteText=time.substring(index+1);
                    int m=CommandNumberWords.parse(minuteText);
                    if(m<0 && minuteText.matches("(?:oh|zero) (?:one|two|three|four|five|six|seven|eight|nine)"))
                        m=CommandNumberWords.parse(minuteText.substring(minuteText.indexOf(' ')+1));
                    if(h<1 || h>12 || m<0 || m>59) continue;
                    if(hour!=-1 && (hour!=h || minute!=m)) return null;
                    hour=h; minute=m;
                }
            }
        }
        if(minute<0 || minute>59 || hour<0 || (period==null?hour>23:hour<1 || hour>12)) return null;
        if(period!=null) hour=hour%12+(period.equals("p")?12:0);
        return new int[]{hour,minute};
    }

    /** Only complete, explicitly enumerated conversational wrappers are removed. */
    private static String requestBody(String input) {
        String body=input.replaceFirst("[.!?]+$","").trim();
        body=body.replaceFirst("^(?:(?:hey|hi|hello)[,]? +)?mira[,!]? +","");
        body=body.replaceFirst("^(?:hey|hi|hello)[,]? +","");
        body=politePrefix(body);
        body=body.replaceFirst("^(?:(?:can|could|would|will) you +|i (?:want|need)(?: you)? to +|i(?:'d| would) like(?: you)? to +|let(?:'s| us| me) +)","");
        body=politePrefix(body).replaceFirst("^help me +","");
        body=politePrefix(body);
        // These suffixes carry no action/argument. Everything else must match the complete tool form.
        body=body.replaceFirst("(?:,? +(?:please|now|for me)){1,2}$","").trim();
        return body;
    }
    private static String politePrefix(String body) {
        return body.replaceFirst("^(?:(?:please|kindly)[,]? +|just +)","");
    }
}
