package dev.focuspilot.prototype;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Development compatibility repair only; no Android execution or action authorization. */
public final class CompatibleUnitCommand {
    public static final String FAST_LOCAL_REQUEST="FAST_LOCAL_REQUEST",CHECKED_MODEL="CHECKED_MODEL",UNKNOWN="UNKNOWN";
    public static final String SYSTEM_PROMPT = UnitCommand.SYSTEM_PROMPT;
    public static final String GRAMMAR = UnitCommand.GRAMMAR;
    private static final String UNIT_WORDS = "seconds?|secs?|minutes?|mins?|hours?|hrs?";
    private static final Pattern SOURCE_UNIT = Pattern.compile("\\b(" + UNIT_WORDS + ")\\b");
    private static final Pattern SOURCE_NUMBER = Pattern.compile("\\b(?:[0-9]+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)\\b");
    // Same finite, trailing inert privacy clauses as StructuredCommand's analysis copy.
    private static final Pattern PRIVACY = Pattern.compile("(?:,? +)(?:(?:without|do not|don't) +(?:uploading|sending|sharing) +(?:my|any|our|this) +(?:data|information)(?: +(?:anywhere|online|to the cloud))?|without +(?:saving|recording|storing) +(?:(?:an|any|my|the) +)?(?:audio|voice)(?: +recording)?|without +recording +anything|with +no +cloud +upload)[.!?]*$");
    private static final Set<String> STATUS_WORDS = new HashSet<>(Arrays.asList((
        "a an the my our this current ongoing active local focus focusing focused concentration concentrating study studying deep work session mode time " +
        "status summary stats overview progress elapsed remaining remainder remains left total accumulated completed complete countdown timer duration " +
        "nudge nudged nudges warning warnings warn warned reminder reminders remind reminded reason cause caused explanation " +
        "explain show display tell me about what what's is how why much long have been i you mira did was to for of in during " +
        "appear appeared happen happened occur occurred issued gave going doing paused running budget points virtual balance usage " +
        "please kindly just can could would will want need like i'd let's us help hey hi hello now").split(" +")));
    private static final Pattern STATUS_TOKEN = Pattern.compile("[a-z]+(?:'[a-z]+)?");
    private static final Pattern STATUS_DOMAIN = Pattern.compile("\\b(?:focus|focusing|focused|concentration|concentrating|study|studying|deep work|work session|nudge|nudged|warning|warn|warned|reminder|remind|reminded)\\b");
    private static final Pattern POSSESSIVE = Pattern.compile("\\b([a-z]+)'s\\b|\\b[a-z]+s'(?= |[.,!?;:]|$)");
    private static final Set<String> NONPERSON_CONTRACTIONS = new HashSet<>(Arrays.asList("what","how","where","when","who","let","it","that","there","here","phone"));
    private static final Pattern OTHER_PERSON = Pattern.compile("\\b(?:he|him|his|she|her|hers|they|them|their|theirs|sister|brother|mother|father|mom|mum|dad|parent|parents|child|children|son|daughter|husband|wife|partner|spouse|aunt|uncle|cousin|grandparent|grandparents|grandfather|grandmother|boss|manager|teacher|student|colleague|coworker|co-worker|friend|client|customer|roommate|neighbor|neighbour|employee|employer)\\b");
    private CompatibleUnitCommand() {}

    public static String renderPrompt(String original) { return UnitCommand.renderPrompt(original); }
    public static String guardReason(String original) {
        String reason=UnitCommand.guardReason(original);if(reason!=null)return reason;
        String source=normalized(original);
        if(OTHER_PERSON.matcher(source).find())return "Another person's state is outside this assistant's local scope";
        Matcher possessive=POSSESSIVE.matcher(source);
        while(possessive.find())
            if(possessive.group(1)==null||!NONPERSON_CONTRACTIONS.contains(possessive.group(1)))
                return "Personal possessive state needs clarification; use your own local phone context";
        return null;
    }

    public static final class Proposal {
        public final String intent, app, reason, unit;
        public final int hour, minute, durationSeconds, amount;
        public final boolean accepted;
        /** Provenance only. FAST is a deterministic source parser, never a Qwen prediction. */
        public final String origin, source;
        /** Diagnostic route only, never proof of model correctness or consent. */
        public final String validationRoute;
        private final UnitCommand.Proposal canonical;
        private Proposal(UnitCommand.Proposal canonical, String reason, String route, String origin) {
            this.canonical=canonical;this.intent=canonical.intent;this.app=canonical.app;
            this.hour=canonical.hour;this.minute=canonical.minute;this.durationSeconds=canonical.durationSeconds;
            this.amount=canonical.amount;this.unit=canonical.unit;this.accepted=canonical.accepted;
            this.reason=reason;this.validationRoute=route;this.origin=origin;this.source=origin;
        }
        public String canonicalJson() { return canonical.canonicalJson(); }
    }
    public static Proposal parseResponse(String output) {
        UnitCommand.Proposal parsed=UnitCommand.parseResponse(output);
        return new Proposal(parsed,parsed.reason,"schema_only",UNKNOWN);
    }
    private static Proposal rejected(String reason) {
        return new Proposal(UnitCommand.parseResponse("{\"intent\":\"unknown\"}"),reason,"rejected",UNKNOWN);
    }
    public static Proposal validate(String original,String output) {
        String guard=guardReason(original);if(guard!=null)return rejected(guard);
        final UnitCommand.Proposal parsed;
        try { parsed=UnitCommand.parseResponse(output); }
        catch(IllegalArgumentException error) { return rejected("Malformed unit response: "+error.getMessage()); }
        if(!parsed.accepted)return new Proposal(parsed,parsed.reason,"model_abstention",UNKNOWN);
        if(parsed.unit!=null&&!quantityAgrees(original,parsed.amount,parsed.unit))
            return rejected("Quantity/unit must be copied from the original request");
        if(parsed.intent.equals("explain")&&!boundedStatusRequest(original))
            return rejected("Explain is limited to the local focus status and policy context");
        ModelCommandGate.Proposal selected=ModelCommandGate.validate(parsed.intent,original);
        if(selected.executable()&&slotsAgree(parsed,selected))
            return new Proposal(parsed,"Selected gate preserves this complete request; explicit action review required","selected_gate",CHECKED_MODEL);
        UnitCommand.Proposal checked=UnitCommand.validate(original,output);
        return new Proposal(checked,checked.reason,checked.accepted?"unit":"rejected",checked.accepted?CHECKED_MODEL:UNKNOWN);
    }
    /**
     * Pure System 1 source recognition. Unknown means eligible to ask a model later,
     * not permission to infer automatically. No recording, model call or action occurs.
     */
    public static Proposal recognize(String original) {
        String guard=guardReason(original);if(guard!=null)return rejected(guard);
        UnitCommand.Proposal unique=null;int matches=0;
        for(String intent:new String[]{"start_focus","pause_focus","alarm","timer","open_app","explain","unknown"}) {
            ModelCommandGate.Proposal selected=ModelCommandGate.validate(intent,original);
            if(!selected.executable())continue;
            if(intent.equals("explain")&&!boundedStatusRequest(original))continue;
            UnitCommand.Proposal parsed=selectedResponse(original,intent,selected);
            if(parsed==null||!slotsAgree(parsed,selected))continue;
            if(++matches>1)return rejected("More than one complete local tool request needs clarification");
            unique=parsed;
        }
        if(unique==null)return rejected("No unambiguous complete local request; a separate model review may help");
        return new Proposal(unique,"Recognized locally from the complete request; explicit action review required","fast_local",FAST_LOCAL_REQUEST);
    }
    private static UnitCommand.Proposal selectedResponse(String original,String intent,ModelCommandGate.Proposal selected) {
        String response="{\"intent\":\""+intent+"\"";
        if(intent.equals("start_focus")||intent.equals("timer")) {
            String unit="none";int amount=0;
            if(selected.seconds!=0) {
                Matcher units=SOURCE_UNIT.matcher(normalized(original));if(!units.find())return null;
                String word=units.group(1);unit=word.startsWith("h")?"hours":word.startsWith("min")?"minutes":"seconds";
                int multiplier=unit.equals("hours")?3600:unit.equals("minutes")?60:1;
                if(selected.seconds%multiplier!=0)return null;
                amount=selected.seconds/multiplier;
            }
            if(!quantityAgrees(original,amount,unit))return null;
            response+=",\"amount\":"+amount+",\"unit\":\""+unit+"\"";
        } else if(intent.equals("alarm"))response+=",\"hour\":"+selected.hour+",\"minute\":"+selected.minute;
        else if(intent.equals("open_app")) {
            String app=selected.kind==ModelCommandGate.Kind.OPEN_SETTINGS?"settings":
                selected.kind==ModelCommandGate.Kind.OPEN_CALCULATOR?"calculator":
                selected.kind==ModelCommandGate.Kind.OPEN_CLOCK?"clock":null;
            if(app==null)return null;response+=",\"app\":\""+app+"\"";
        }
        try{return UnitCommand.parseResponse(response+"}");}
        catch(IllegalArgumentException error){return null;}
    }
    private static boolean slotsAgree(UnitCommand.Proposal p,ModelCommandGate.Proposal g) {
        ModelCommandGate.Kind expected;
        switch(p.intent) {
            case "start_focus":expected=ModelCommandGate.Kind.START_FOCUS;break;
            case "pause_focus":expected=ModelCommandGate.Kind.PAUSE_FOCUS;break;
            case "alarm":expected=ModelCommandGate.Kind.ALARM;break;
            case "timer":expected=ModelCommandGate.Kind.TIMER;break;
            case "open_app":expected=p.app.equals("settings")?ModelCommandGate.Kind.OPEN_SETTINGS:
                p.app.equals("calculator")?ModelCommandGate.Kind.OPEN_CALCULATOR:ModelCommandGate.Kind.OPEN_CLOCK;break;
            case "explain":expected=ModelCommandGate.Kind.EXPLAIN;break;
            default:return false;
        }
        return g.kind==expected&&g.hour==p.hour&&g.minute==p.minute&&g.seconds==p.durationSeconds;
    }
    private static String normalized(String original) {
        return original.toLowerCase(Locale.ROOT).replace('\u2019','\'').replace('\u2010','-').replace('\u2011','-')
            .trim().replaceAll(" +"," ")
            .replaceAll("(?<=[a-z0-9])-(?=(?:"+UNIT_WORDS+")\\b)"," ")
            // Preserve the selected gate's accepted contiguous digit/unit slots, e.g. 17minutes.
            .replaceAll("(?<=[0-9])(?=(?:"+UNIT_WORDS+")\\b)"," ");
    }
    /** Provenance: UnitCommand.quantityAgrees, with explicit untimed and digit/unit-boundary checks. */
    private static boolean quantityAgrees(String original,int amount,String unit) {
        String source=normalized(original);Matcher units=SOURCE_UNIT.matcher(source);
        if(unit.equals("none"))return amount==0&&!units.find()&&!SOURCE_NUMBER.matcher(source).find();
        if(!units.find())return false;
        String matched=units.group(1);
        String sourceUnit=matched.startsWith("h")?"hours":matched.startsWith("min")?"minutes":"seconds";
        if(!sourceUnit.equals(unit))return false;
        String prefix=source.substring(0,units.start()).trim();String[] words=prefix.split(" +");int value=-1;
        for(int count=1;count<=Math.min(4,words.length);count++) {
            StringBuilder slot=new StringBuilder();
            for(int i=words.length-count;i<words.length;i++){if(slot.length()>0)slot.append(' ');slot.append(words[i]);}
            String text=slot.toString();
            int candidate=text.matches("[0-9]{1,4}")?Integer.parseInt(text):CommandNumberWords.parse(text);
            if(candidate>=0)value=candidate;
        }
        return value==amount&&!units.find();
    }
    /** Every lexical token must belong to this bounded local status vocabulary. */
    private static boolean boundedStatusRequest(String original) {
        String source=PRIVACY.matcher(normalized(original)).replaceFirst("");
        if(!STATUS_DOMAIN.matcher(source).find())return false;
        Matcher tokens=STATUS_TOKEN.matcher(source);int end=0,count=0;
        while(tokens.find()) {
            if(!source.substring(end,tokens.start()).matches("[ .,!?;:-]*"))return false;
            if(!STATUS_WORDS.contains(tokens.group()))return false;
            end=tokens.end();count++;
        }
        return count>0&&source.substring(end).matches("[ .,!?;:-]*");
    }
}
