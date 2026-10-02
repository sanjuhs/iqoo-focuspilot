package dev.focuspilot.prototype;

/** Pure state gate: recognition may create drafts, never execute commands or start a model. */
public final class VoiceDraftState {
    public enum Phase { IDLE, CHECKING, LISTENING, PROCESSING, DRAFT }
    private boolean visible, destroyed, modelBusy;
    private long epoch;
    private Phase phase=Phase.IDLE;
    private String draft="";
    public void resume() { if(!destroyed) visible=true; }
    public void stop() { visible=false;cancel(); }
    public void destroy() { destroyed=true;visible=false;cancel(); }
    public void setModelBusy(boolean busy) { modelBusy=busy;if(busy)cancel(); }
    public boolean canStart() { return visible&&!destroyed&&!modelBusy&&!active(); }
    public boolean canUnderstand() { return visible&&!destroyed&&!modelBusy&&!active(); }
    public long begin(boolean permission,boolean onDeviceAvailable) {
        if(!permission||!onDeviceAvailable||!canStart()) return -1;
        epoch++;phase=Phase.CHECKING;return epoch;
    }
    public boolean accepts(long token) { return token==epoch&&visible&&!destroyed&&!modelBusy&&active(); }
    public boolean listening(long token) { if(!accepts(token)||phase!=Phase.CHECKING)return false;phase=Phase.LISTENING;return true; }
    public boolean processing(long token) { if(!accepts(token)||phase!=Phase.LISTENING)return false;phase=Phase.PROCESSING;return true; }
    public boolean acceptsPartial(long token,String text) { return accepts(token)&&phase!=Phase.CHECKING&&validDraft(text); }
    public boolean finish(long token,String text) {
        if(!acceptsPartial(token,text))return false;
        draft=text.trim();phase=Phase.DRAFT;epoch++;return true;
    }
    public boolean fail(long token) { if(!accepts(token))return false;phase=Phase.IDLE;epoch++;return true; }
    public void cancel() { epoch++;phase=Phase.IDLE; }
    public boolean active() { return phase==Phase.CHECKING||phase==Phase.LISTENING||phase==Phase.PROCESSING; }
    public Phase phase() { return phase; }
    public String draft() { return draft; }
    private static boolean validDraft(String text) { return text!=null&&!text.trim().isEmpty()&&text.length()<=500; }
}
