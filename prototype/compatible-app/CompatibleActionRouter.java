package dev.focuspilot.prototype;

/** Source-only preparation. Not installed; qualification and app checks remain required. */
public final class CompatibleActionRouter {
    private CompatibleActionRouter() {}
    public static final class Result {
        public final ModelCommandGate.Proposal proposal;
        public final String origin;
        private Result(ModelCommandGate.Proposal proposal, String origin) {
            this.proposal=proposal;this.origin=origin;
        }
    }
    public static Result recognize(String original) {
        return adapt(CompatibleUnitCommand.recognize(original));
    }
    public static Result validate(String original,String response) {
        return adapt(CompatibleUnitCommand.validate(original,response));
    }
    /**
     * Revalidate the original source at action review. No slots come from UI text,
     * and changing the command invalidates the proposal. Caller still owns the
     * foreground/lifecycle/request epoch and explicit confirmation checks.
     */
    public static Result review(String evaluatedOriginal,String currentOriginal,
                                String response,String origin) {
        if(evaluatedOriginal==null||!evaluatedOriginal.equals(currentOriginal))
            return refused("Request changed; understand it again before reviewing.");
        if(CompatibleUnitCommand.FAST_LOCAL_REQUEST.equals(origin)) {
            if(response!=null) return refused("Local request must not carry a model response.");
            return recognize(evaluatedOriginal);
        }
        if(CompatibleUnitCommand.CHECKED_MODEL.equals(origin)&&response!=null)
            return validate(evaluatedOriginal,response);
        return refused("No complete reviewed command is available.");
    }
    private static Result refused(String reason) {
        return new Result(new ModelCommandGate.Proposal(ModelCommandGate.Kind.UNKNOWN,0,0,0,reason),CompatibleUnitCommand.UNKNOWN);
    }
    private static Result adapt(CompatibleUnitCommand.Proposal checked) {
        if(!checked.accepted)return refused(checked.reason);
        final ModelCommandGate.Kind kind;final String preview;
        switch(checked.intent) {
            case "start_focus":
                kind=ModelCommandGate.Kind.START_FOCUS;
                preview=checked.durationSeconds>0?"Start a focus countdown for "+checked.durationSeconds+" seconds.":"Start or resume your local focus session.";
                break;
            case "pause_focus":kind=ModelCommandGate.Kind.PAUSE_FOCUS;preview="Pause focus and stop any active focus monitor.";break;
            case "alarm":kind=ModelCommandGate.Kind.ALARM;preview=String.format(java.util.Locale.ROOT,"Ask Clock to set an alarm at %02d:%02d; verify it in Clock.",checked.hour,checked.minute);break;
            case "timer":kind=ModelCommandGate.Kind.TIMER;preview="Ask Clock to start a regular timer for "+checked.durationSeconds+" seconds; verify it in Clock.";break;
            case "open_app":
                if("settings".equals(checked.app))kind=ModelCommandGate.Kind.OPEN_SETTINGS;
                else if("calculator".equals(checked.app))kind=ModelCommandGate.Kind.OPEN_CALCULATOR;
                else if("clock".equals(checked.app))kind=ModelCommandGate.Kind.OPEN_CLOCK;
                else return refused("App is outside the approved list.");
                preview="Open "+checked.app+"; verify the result on screen.";break;
            case "explain":kind=ModelCommandGate.Kind.EXPLAIN;preview="Show a current local focus status snapshot.";break;
            default:return refused("Unsupported command.");
        }
        return new Result(new ModelCommandGate.Proposal(kind,checked.hour,checked.minute,checked.durationSeconds,preview),checked.origin);
    }
}
