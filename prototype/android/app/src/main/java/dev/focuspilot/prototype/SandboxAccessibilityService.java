package dev.focuspilot.prototype;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.lang.ref.WeakReference;
import java.util.List;

/** Real ACTION_CLICK proof, limited to the separately armed synthetic own-app window. */
public final class SandboxAccessibilityService extends AccessibilityService {
    private static WeakReference<SandboxAccessibilityService> current=new WeakReference<>(null);
    private final Handler main=new Handler(Looper.getMainLooper());
    private final SandboxActionGate gate=new SandboxActionGate();
    private WeakReference<SandboxAutomationActivity> requester=new WeakReference<>(null);
    private boolean connected;
    private long token;
    private boolean tickQueued;
    private static SandboxAccessibilityService instance(){return current.get();}
    public static boolean connected(){SandboxAccessibilityService service=instance();return service!=null&&service.connected;}
    public static boolean armedFor(SandboxAutomationActivity activity){SandboxAccessibilityService service=instance();return service!=null&&service.requester.get()==activity&&service.gate.armed();}
    public static void arm(SandboxAutomationActivity activity){requireMain();SandboxAccessibilityService service=instance();
        if(service==null||!service.connected){activity.proofStatus("Unavailable: manually enable the sandbox accessibility service in Android Settings first.");return;}service.begin(activity);}
    public static void cancel(SandboxAutomationActivity activity){requireMain();SandboxAccessibilityService service=instance();
        if(service!=null&&service.requester.get()==activity)service.stop("Cancelled or screen left; no more selector actions allowed.");}
    public static void disableForUser(SandboxAutomationActivity activity){requireMain();SandboxAccessibilityService service=instance();
        if(service==null){activity.proofStatus("Service is not connected. Use Android Settings to inspect or disable it.");return;}
        service.stop("User disabled the sandbox service.");service.connected=false;
        try{service.disableSelf();activity.proofStatus("Disable requested. Android Settings is the source of truth for the service permission.");}
        catch(RuntimeException error){activity.proofStatus("Disable could not be requested. The proof is disarmed; use Android Settings to disable the service.");}}
    @Override protected void onServiceConnected(){
        connected=true;current=new WeakReference<>(this);gate.cancel();
        AccessibilityServiceInfo info=getServiceInfo();
        if(info==null)info=new AccessibilityServiceInfo();
        info.packageNames=new String[]{SandboxActionGate.PACKAGE};
        info.eventTypes=AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED|AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
            |AccessibilityEvent.TYPE_VIEW_CLICKED|AccessibilityEvent.TYPE_VIEW_SELECTED;
        info.flags=AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;info.feedbackType=AccessibilityServiceInfo.FEEDBACK_GENERIC;info.notificationTimeout=50;
        setServiceInfo(info); // Capability to retrieve content is declared only in the narrow XML.
    }
    private void begin(SandboxAutomationActivity activity){
        stop(null);
        if(!activity.isSandboxForeground()||!SandboxActionGate.PACKAGE.equals(activity.getPackageName())
            ||!SandboxActionGate.ACTIVITY.equals(activity.getClass().getName())){activity.proofStatus("Arm refused: exact sandbox Activity must be foreground.");return;}
        requester=new WeakReference<>(activity);
        AccessibilityNodeInfo root;
        try{root=ownRoot();}catch(RuntimeException error){stop("Arm refused: the accessibility window API is unavailable.");return;}
        if(root==null){stop("Arm refused: the exact synthetic root is not visible. Try again with this sandbox in front.");return;}
        try{
            long now=SystemClock.uptimeMillis();SandboxActionGate.Context context=context(root,now);
            token=gate.arm(context,now);
            if(token<0){stop("Arm refused: the synthetic window could not be verified.");return;}
            status("ARMED for five seconds · exact own sandbox window only.");queueTick(150);
            final long armedToken=token;
            main.postDelayed(()->{if(token==armedToken&&gate.armed())stop("Expired after five seconds; tap Arm for a new proof.");},SandboxActionGate.TTL_MS);
        }finally{root.recycle();}
    }
    @Override public void onAccessibilityEvent(AccessibilityEvent event){
        if(!gate.armed())return;
        SandboxAutomationActivity activity=requester.get();
        if(activity==null||!activity.isSandboxForeground()){stop("Screen left; selector authorization cancelled.");return;}
        // Configuration filters packages. Never read event text, content descriptions or event source nodes.
        if(event==null||!SandboxActionGate.PACKAGE.contentEquals(event.getPackageName()==null?"":event.getPackageName()))return;
        if(event.getWindowId()>=0&&event.getWindowId()!=gate.windowId()){stop("Window changed; selector authorization cancelled.");return;}
        if(event.getEventType()==AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
            &&!SandboxActionGate.ACTIVITY.contentEquals(event.getClassName()==null?"":event.getClassName())){
            stop("Activity/window changed; no selector action allowed.");return;
        }
        queueTick(100);
    }
    private void queueTick(long delay){if(tickQueued||!gate.armed())return;tickQueued=true;main.postDelayed(()->{tickQueued=false;tick();},delay);}
    private void tick(){
        if(!gate.armed())return;
        AccessibilityNodeInfo root;
        try{root=ownRoot();}catch(RuntimeException error){stop("Own-window retrieval failed; proof cancelled without fallback.");return;}
        if(root==null){stop("Own sandbox root unavailable; no action attempted.");return;}
        try{
            long now=SystemClock.uptimeMillis();SandboxActionGate.Context context=context(root,now);
            if(!gate.validRequest(token,context,now)){stop("Arm is expired, stale or not in the exact foreground window.");return;}
            String selector=gate.expectedSelector();
            if(gate.awaitingPostcondition()){
                String postcondition=gate.step()==SandboxActionGate.Step.OPEN_TASK?SandboxActionGate.PACKAGE+":id/sandbox_task_panel":SandboxActionGate.CHECK_ID;
                AccessibilityNodeInfo node=unique(root,postcondition);
                boolean observed=false;
                if(node!=null){try{observed=node.refresh()&&safeNode(node,root.getWindowId())
                    &&(gate.step()==SandboxActionGate.Step.OPEN_TASK||node.isCheckable()&&node.isChecked());}finally{node.recycle();}}
                if(gate.verifyPostcondition(token,context,selector,observed,SystemClock.uptimeMillis())){
                    if(gate.step()==SandboxActionGate.Step.DONE){status("VERIFIED: accessibility navigation revealed the synthetic panel, then accessibility click checked its checkbox. No product action ran.");main.removeCallbacksAndMessages(null);tickQueued=false;return;}
                    status("Postcondition verified: synthetic task panel is visible.");queueTick(250);
                }else if(gate.armed())queueTick(100);
                else stop("Postcondition verification expired or window changed; no more actions.");
                return;
            }
            AccessibilityNodeInfo target=unique(root,selector);
            if(target==null){stop("Exact selector unavailable or duplicated; no click attempted.");return;}
            try{
                if(!target.refresh()||!safeNode(target,root.getWindowId())||!target.isClickable()
                    ||gate.step()==SandboxActionGate.Step.CHECK_ITEM&&(!target.isCheckable()||target.isChecked())){
                    stop("Synthetic target is stale, unavailable or already changed; no click attempted.");return;
                }
                if(!gate.authorizeClick(token,context,selector,SystemClock.uptimeMillis())){stop("Authorization failed before click; no action attempted.");return;}
                // No coordinates, gestures, direct View reference, performClick or parent-click fallback.
                boolean accepted=target.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                if(!accepted){stop("Accessibility ACTION_CLICK was rejected; no fallback performed.");return;}
                status(gate.step()==SandboxActionGate.Step.OPEN_TASK?"Accessibility click accepted: open synthetic task. Checking actual panel visibility…":
                    "Accessibility click accepted: synthetic checkbox. Checking actual checked state…");queueTick(100);
            }finally{target.recycle();}
        }catch(RuntimeException error){stop("Accessibility API unavailable or interrupted; proof stopped without fallback.");}
        finally{root.recycle();}
    }
    /** Check requester foreground before retrieval; traverse only a matching own-package root. */
    private AccessibilityNodeInfo ownRoot(){
        SandboxAutomationActivity activity=requester.get();
        if(!connected||activity==null||!activity.isSandboxForeground())return null;
        AccessibilityNodeInfo root=getRootInActiveWindow();
        if(root==null)return null;
        if(!root.refresh()||!SandboxActionGate.PACKAGE.contentEquals(root.getPackageName()==null?"":root.getPackageName())||root.isPassword()){
            root.recycle();return null;
        }
        AccessibilityNodeInfo anchor=unique(root,SandboxActionGate.ROOT_ID);boolean valid=false;
        if(anchor!=null){try{valid=anchor.refresh()&&safeNode(anchor,root.getWindowId());}finally{anchor.recycle();}}
        if(!valid){root.recycle();return null;}return root;
    }
    private SandboxActionGate.Context context(AccessibilityNodeInfo root,long snapshotAt){SandboxAutomationActivity activity=requester.get();
        return new SandboxActionGate.Context(SandboxActionGate.PACKAGE,activity==null?"":activity.getClass().getName(),SandboxActionGate.ROOT_ID,
            root.getWindowId(),snapshotAt,activity!=null&&activity.isSandboxForeground(),connected);}
    private static boolean safeNode(AccessibilityNodeInfo node,int window){return node.getWindowId()==window
        &&SandboxActionGate.PACKAGE.contentEquals(node.getPackageName()==null?"":node.getPackageName())&&node.isVisibleToUser()&&node.isEnabled()&&!node.isPassword();}
    private static AccessibilityNodeInfo unique(AccessibilityNodeInfo root,String selector){
        List<AccessibilityNodeInfo> matches=root.findAccessibilityNodeInfosByViewId(selector);
        if(matches==null||matches.isEmpty())return null;
        if(matches.size()!=1){for(AccessibilityNodeInfo node:matches)node.recycle();return null;}
        AccessibilityNodeInfo node=matches.get(0);if(!selector.equals(node.getViewIdResourceName())){node.recycle();return null;}return node;
    }
    private void status(String message){SandboxAutomationActivity activity=requester.get();if(activity!=null&&activity.isSandboxForeground())activity.proofStatus(message);}
    private void stop(String reason){gate.cancel();main.removeCallbacksAndMessages(null);tickQueued=false;if(reason!=null)status(reason);requester.clear();}
    @Override public void onInterrupt(){stop("Service interrupted; arm cancelled.");}
    @Override public boolean onUnbind(Intent intent){connected=false;stop("Service disconnected; arm cancelled.");if(instance()==this)current.clear();return super.onUnbind(intent);}
    @Override public void onDestroy(){connected=false;stop("Service destroyed; arm cancelled.");if(instance()==this)current.clear();super.onDestroy();}
    private static void requireMain(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("Sandbox service controls require main thread");}
}
