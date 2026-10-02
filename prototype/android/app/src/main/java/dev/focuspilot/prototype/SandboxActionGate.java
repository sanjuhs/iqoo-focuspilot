package dev.focuspilot.prototype;

/** Pure one-shot authorization for exactly two synthetic selectors in one foreground window. */
public final class SandboxActionGate {
    public static final String PACKAGE="dev.focuspilot.prototype";
    public static final String ACTIVITY=PACKAGE+".SandboxAutomationActivity";
    public static final String ROOT_ID=PACKAGE+":id/sandbox_proof_root";
    public static final String OPEN_ID=PACKAGE+":id/sandbox_open_task";
    public static final String CHECK_ID=PACKAGE+":id/sandbox_task_checkbox";
    public static final long TTL_MS=5000, MAX_SNAPSHOT_AGE_MS=250;
    public enum Step { DISARMED, OPEN_TASK, CHECK_ITEM, DONE }
    public static final class Context {
        public final String packageName,activityName,rootId;
        public final int windowId;
        public final long snapshotAt;
        public final boolean foreground,connected;
        public Context(String packageName,String activityName,String rootId,int windowId,long snapshotAt,boolean foreground,boolean connected){
            this.packageName=packageName;this.activityName=activityName;this.rootId=rootId;this.windowId=windowId;
            this.snapshotAt=snapshotAt;this.foreground=foreground;this.connected=connected;
        }
    }
    private long epoch,armedAt,expiresAt;
    private int window=-1;
    private Step step=Step.DISARMED;
    private boolean awaitingPostcondition;
    public long arm(Context context,long now){
        cancel();
        if(!validContext(context,now)||now>Long.MAX_VALUE-TTL_MS)return -1;
        armedAt=now;expiresAt=now+TTL_MS;window=context.windowId;step=Step.OPEN_TASK;return epoch;
    }
    public boolean authorizeClick(long token,Context context,String selector,long now){
        if(!validRequest(token,context,now)||awaitingPostcondition)return false;
        if(!expectedSelector().equals(selector)){cancel();return false;}
        awaitingPostcondition=true;return true;
    }
    /** Only observed true postconditions advance the script; failed observations may be retried until expiry. */
    public boolean verifyPostcondition(long token,Context context,String selector,boolean observed,long now){
        if(!validRequest(token,context,now)||!awaitingPostcondition)return false;
        if(!expectedSelector().equals(selector)){cancel();return false;}
        if(!observed)return false;
        awaitingPostcondition=false;
        step=step==Step.OPEN_TASK?Step.CHECK_ITEM:Step.DONE;
        return true;
    }
    public boolean validRequest(long token,Context context,long now){
        if(token!=epoch||!armed())return false; // A stale caller must never cancel a newer arm.
        if(now<armedAt||now>=expiresAt||!validContext(context,now)||context.windowId!=window){cancel();return false;}
        return true;
    }
    private static boolean validContext(Context c,long now){return c!=null&&PACKAGE.equals(c.packageName)&&ACTIVITY.equals(c.activityName)
        &&ROOT_ID.equals(c.rootId)&&c.windowId>=0&&c.foreground&&c.connected&&now>=0&&c.snapshotAt>=0
        &&now>=c.snapshotAt&&now-c.snapshotAt<=MAX_SNAPSHOT_AGE_MS;}
    public void cancel(){epoch++;step=Step.DISARMED;window=-1;awaitingPostcondition=false;}
    public boolean armed(){return step==Step.OPEN_TASK||step==Step.CHECK_ITEM;}
    public Step step(){return step;}
    public boolean awaitingPostcondition(){return awaitingPostcondition;}
    public int windowId(){return window;}
    public String expectedSelector(){return step==Step.OPEN_TASK?OPEN_ID:step==Step.CHECK_ITEM?CHECK_ID:"";}
}
