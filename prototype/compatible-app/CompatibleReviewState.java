package dev.focuspilot.prototype;

/** In-memory proposal ownership only. Never records audio, loads a model or acts. */
public final class CompatibleReviewState {
    public static final class Snapshot {
        private final long epoch;
        private final String original, response, origin;
        private Snapshot(long epoch, String original, String response, String origin) {
            this.epoch=epoch;this.original=original;this.response=response;this.origin=origin;
        }
        public String original() { return original; }
        public String origin() { return origin; }
    }
    private Snapshot pending;

    /** Store only a complete independently revalidated proposal with its actual origin. */
    public boolean offer(long epoch,String original,String response,String origin) {
        clear();
        if(epoch<=0||!CompatibleActionRouter.review(original,original,response,origin).proposal.executable())return false;
        pending=new Snapshot(epoch,original,response,origin);
        return true;
    }
    public Snapshot snapshot() { return pending; }
    public void clear() { pending=null; }
    public boolean owns(Snapshot snapshot,long currentEpoch,String currentText,
                        boolean foreground,boolean idle) {
        return snapshot!=null&&pending==snapshot&&snapshot.epoch==currentEpoch&&
            foreground&&idle&&snapshot.original.equals(currentText);
    }
    /** Both opening review and confirming must check lifecycle and revalidate source. */
    public CompatibleActionRouter.Result review(Snapshot snapshot,long currentEpoch,
                                               String currentText,boolean foreground,boolean idle) {
        if(!owns(snapshot,currentEpoch,currentText,foreground,idle))
            return CompatibleActionRouter.review(null,currentText,null,null);
        return CompatibleActionRouter.review(snapshot.original,currentText,snapshot.response,snapshot.origin);
    }
    /** Consume before execution; a duplicate callback cannot confirm a second action. */
    public CompatibleActionRouter.Result consume(Snapshot snapshot,long currentEpoch,
                                                String currentText,boolean foreground,boolean idle) {
        CompatibleActionRouter.Result result=review(snapshot,currentEpoch,currentText,foreground,idle);
        if(pending==snapshot)clear();
        return result;
    }
}
