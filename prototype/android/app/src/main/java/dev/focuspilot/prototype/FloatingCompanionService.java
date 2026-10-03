package dev.focuspilot.prototype;

import android.Manifest;
import android.animation.ValueAnimator;
import android.app.AppOpsManager;
import android.app.KeyguardManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.provider.Settings;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.Locale;

/** User-started visual companion. Ask Mira opens the foreground draft screen only. */
public final class FloatingCompanionService extends Service {
    public static final String CHANNEL="floating_mira", SHOW="dev.focuspilot.prototype.SHOW_MIRA",
        HIDE="dev.focuspilot.prototype.HIDE_MIRA", PAUSE="dev.focuspilot.prototype.PAUSE_FROM_MIRA";
    public static final String EXTRA_RETURN_AFTER_UNLOCK="returnAfterUnlock";
    public static volatile boolean running;
    public static volatile boolean waitingForUnlock,returnAfterUnlockActive;
    public static volatile String lastStatus="Hidden · Show is always your choice";
    private static final int ID=42;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private WindowManager windows;
    private WindowManager.LayoutParams layout;
    private LinearLayout bubble;
    private CompanionView mira;
    private TextView focusStatus;
    private Button pauseButton;
    private FocusRepository repository;
    private AppOpsManager ops;
    private boolean attached, receiverRegistered, watchingOps, foreground, ending;
    private int availableWidth, availableHeight;
    private float touchX,touchY;
    private int downX,downY;
    private final CompanionAvailability availability=new CompanionAvailability();
    private long showLease;
    private final BroadcastReceiver screenOff=new BroadcastReceiver(){
        @Override public void onReceive(Context context,Intent intent){
            if(ending || !running)return;
            if(Intent.ACTION_SCREEN_OFF.equals(intent.getAction()))suspendPortrait();
            else if(Intent.ACTION_USER_PRESENT.equals(intent.getAction()))restorePortrait();
        }
    };
    private final AppOpsManager.OnOpChangedListener permissionChange=(op,pkg)->handler.post(()->{
        if(!ending && !Settings.canDrawOverlays(this))end("Overlay permission removed · floating Mira stopped");
    });
    private final Runnable tick=new Runnable(){
        @Override public void run(){
            if(!running || ending)return;
            String blocked=permanentBlockedReason(FloatingCompanionService.this);
            if(blocked!=null){end(blocked);return;}
            if(displayBlockedReason(FloatingCompanionService.this)!=null){suspendPortrait();return;}
            if(availability.isDormant() || !attached)return;
            repository.completeTimedIfDue(); // Own deadline only. Existing-consent accounting can flush usage at completion; no observation is enabled.
            int oldX=layout.x,oldY=layout.y,oldWidth=availableWidth,oldHeight=availableHeight;
            if(!refreshBounds())return;
            if(oldX!=layout.x || oldY!=layout.y || oldWidth!=availableWidth || oldHeight!=availableHeight)updateWindow();
            if(ending || availability.isDormant() || !attached)return;
            updateOwnStatus();
            handler.postDelayed(this,1000);
        }
    };
    public static boolean notificationsAllowed(Context context){
        if(Build.VERSION.SDK_INT>=33 && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return false;
        NotificationManager manager=context.getSystemService(NotificationManager.class);
        if(manager==null || !manager.areNotificationsEnabled())return false;
        NotificationChannel channel=manager.getNotificationChannel(CHANNEL);
        return channel==null || channel.getImportance()!=NotificationManager.IMPORTANCE_NONE;
    }
    /** No grant is inferred from Settings returning, and no prerequisite check starts a service. */
    public static String permanentBlockedReason(Context context){
        if(!Settings.canDrawOverlays(context))return "Overlay permission off · review Android settings first";
        if(!notificationsAllowed(context))return "Floating notifications blocked · allow them in Android settings first";
        if(context.getSharedPreferences("focuspilot_research",MODE_PRIVATE).getBoolean("hideCompanion",false))return "Artwork hidden · unhide Mira before Show";
        return null;
    }
    private static String displayBlockedReason(Context context){
        PowerManager power=context.getSystemService(PowerManager.class);
        KeyguardManager keyguard=context.getSystemService(KeyguardManager.class);
        if(power==null || keyguard==null || !power.isInteractive() || keyguard.isKeyguardLocked())return "Phone asleep or locked · unlock it, then tap Show";
        return null;
    }
    public static String blockedReason(Context context){
        String permanent=permanentBlockedReason(context);
        return permanent!=null?permanent:displayBlockedReason(context);
    }
    @Override public void onCreate(){
        super.onCreate();repository=FocusRepository.get(this);windows=getSystemService(WindowManager.class);
        NotificationChannel channel=new NotificationChannel(CHANNEL,"Floating Mira controls",NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("User-started visual companion with Ask Mira, Pause focus and Hide controls");
        getSystemService(NotificationManager.class).createNotificationChannel(channel);
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        if(intent==null || HIDE.equals(intent.getAction())){end("Mira hidden · focus and usage settings unchanged");return START_NOT_STICKY;}
        if(PAUSE.equals(intent.getAction())){
            if(running && !ending && blockedReason(this)==null)pauseFocus();
            else if(running && !ending && permanentBlockedReason(this)==null && availability.returnAfterUnlockActive()){
                suspendPortrait();lastStatus="Mira waiting for unlock · no focus action taken while locked";
                getSystemService(NotificationManager.class).notify(ID,notification());
            }else end("Floating Mira stopped; no focus action taken");
            return START_NOT_STICKY;
        }
        if(!SHOW.equals(intent.getAction()) || ending){end("Floating Mira stopped");return START_NOT_STICKY;}
        String blocked=permanentBlockedReason(this);
        if(blocked!=null){end(blocked);return START_NOT_STICKY;}
        if(running){
            // Explicit manual recovery only; current reviewed session mode remains frozen.
            if(displayBlockedReason(this)!=null)suspendPortrait();
            else if(availability.isDormant())restorePortrait();
            else lastStatus="Mira is already floating · drag her portrait to move";
            return START_NOT_STICKY;
        }
        blocked=displayBlockedReason(this);
        if(blocked!=null){end(blocked);return START_NOT_STICKY;}
        try{
            if(Build.VERSION.SDK_INT>=34)startForeground(ID,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            else startForeground(ID,notification());
            foreground=true;
            IntentFilter filter=new IntentFilter(Intent.ACTION_SCREEN_OFF);filter.addAction(Intent.ACTION_USER_PRESENT);
            if(Build.VERSION.SDK_INT>=33)registerReceiver(screenOff,filter,Context.RECEIVER_NOT_EXPORTED);
            else registerReceiver(screenOff,filter);
            receiverRegistered=true;
            ops=getSystemService(AppOpsManager.class);
            ops.startWatchingMode(AppOpsManager.OPSTR_SYSTEM_ALERT_WINDOW,getPackageName(),permissionChange);watchingOps=true;
            createBubble();
            if(!refreshBounds())return START_NOT_STICKY;
            blocked=blockedReason(this);
            if(blocked!=null){end(blocked);return START_NOT_STICKY;}
            if(availability.begin(intent.getBooleanExtra(EXTRA_RETURN_AFTER_UNLOCK,false),true,true)!=CompanionAvailability.Effect.ATTACH){end("Mira could not start a new visual session");return START_NOT_STICKY;}
            showLease=availability.lease();returnAfterUnlockActive=availability.returnAfterUnlockActive();waitingForUnlock=false;
            windows.addView(bubble,layout);attached=true;running=true;
            getSystemService(NotificationManager.class).notify(ID,notification());
            lastStatus="Mira floating · drag her portrait · Hide leaves focus unchanged";
            handler.post(tick);
        }catch(RuntimeException error){end("Android could not show Mira · "+error.getClass().getSimpleName()+" · use the in-app companion");}
        return START_NOT_STICKY;
    }
    private void suspendPortrait(){
        if(ending || !running)return;
        String permanent=permanentBlockedReason(this);
        CompanionAvailability.Effect effect=availability.suspend(permanent==null);
        if(effect==CompanionAvailability.Effect.STOP){end(permanent!=null?permanent:"Hidden when the screen turned off or locked · tap Show again");return;}
        handler.removeCallbacks(tick);
        if(mira!=null)mira.setState(CompanionView.State.PAUSED);
        if(attached){attached=false;try{windows.removeViewImmediate(bubble);}catch(RuntimeException ignored){/* Android may already have removed it. */}}
        waitingForUnlock=availability.isDormant();returnAfterUnlockActive=availability.returnAfterUnlockActive();
        lastStatus="Mira available · portrait hidden until unlock · Hide stops this session";
        getSystemService(NotificationManager.class).notify(ID,notification());
    }
    private void restorePortrait(){
        if(ending || !running)return;
        // Permanent prerequisites are checked even if the phone is still locked.
        String permanent=permanentBlockedReason(this);
        if(permanent!=null){end(permanent);return;}
        CompanionAvailability.Effect effect=availability.resume(showLease,true,displayBlockedReason(this)==null);
        if(effect!=CompanionAvailability.Effect.ATTACH)return;
        try{
            // Reuse the original view/layout so position survives; never duplicate windows.
            if(bubble==null || layout==null){end("Mira’s saved window is unavailable · tap Show again");return;}
            if(!refreshBounds())return;
            String blocked=blockedReason(this);if(blocked!=null){
                if(permanentBlockedReason(this)!=null)end(blocked);else suspendPortrait();return;
            }
            if(!attached){windows.addView(bubble,layout);attached=true;}
            waitingForUnlock=false;returnAfterUnlockActive=availability.returnAfterUnlockActive();
            updateOwnStatus();lastStatus="Mira returned after unlock · no voice, model or action started";
            getSystemService(NotificationManager.class).notify(ID,notification());
            handler.removeCallbacks(tick);handler.post(tick);
        }catch(RuntimeException error){end("Android could not restore Mira · tap Show again if you want her");}
    }
    private int dp(int value){return Math.round(value*getResources().getDisplayMetrics().density);}
    @android.annotation.SuppressLint("RtlHardcoded") // Window coordinates are absolute physical TOP/LEFT, independent of text direction.
    private void createBubble(){
        bubble=new LinearLayout(this);bubble.setOrientation(LinearLayout.VERTICAL);bubble.setPadding(dp(8),dp(8),dp(8),dp(8));
        GradientDrawable background=new GradientDrawable();background.setColor(Color.rgb(36,32,49));background.setCornerRadius(dp(22));background.setStroke(dp(1),Color.rgb(203,171,238));bubble.setBackground(background);
        bubble.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
        TextView title=new TextView(this);title.setText("Mira · drag portrait");title.setTextColor(Color.rgb(203,171,238));title.setTextSize(12);title.setGravity(Gravity.CENTER);bubble.addView(title,new LinearLayout.LayoutParams(-1,dp(22)));
        mira=new CompanionView(this);mira.setContentDescription("Mira portrait. Drag to move the floating companion.");bubble.addView(mira,new LinearLayout.LayoutParams(-1,dp(80)));
        mira.setOnTouchListener((view,event)->{
            if(!running || !attached || ending)return true;
            String blocked=blockedReason(this);if(blocked!=null){if(permanentBlockedReason(this)!=null)end(blocked);else suspendPortrait();return true;}
            if(event.getActionMasked()==MotionEvent.ACTION_DOWN){touchX=event.getRawX();touchY=event.getRawY();downX=layout.x;downY=layout.y;return true;}
            if(event.getActionMasked()==MotionEvent.ACTION_MOVE){
                FloatingWindowPosition.Position position=FloatingWindowPosition.drag(downX,downY,Math.round(event.getRawX()-touchX),Math.round(event.getRawY()-touchY),layout.width,layout.height,availableWidth,availableHeight);
                layout.x=position.x;layout.y=position.y;updateWindow();return true;
            }
            if(event.getActionMasked()==MotionEvent.ACTION_UP){view.performClick();return true;}
            return true;
        });
        // Portrait clicks have no action, so a completed drag cannot accidentally open or pause.
        mira.setOnClickListener(v->{});
        focusStatus=new TextView(this);focusStatus.setTextColor(Color.rgb(247,241,250));focusStatus.setTextSize(12);focusStatus.setGravity(Gravity.CENTER);bubble.addView(focusStatus,new LinearLayout.LayoutParams(-1,dp(24)));
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);bubble.addView(row,new LinearLayout.LayoutParams(-1,dp(52)));
        addButton(row,"Ask Mira",v->openAssistant(),true);addButton(row,"Hide",v->end("Mira hidden · focus and usage settings unchanged"),true);
        pauseButton=addButton(bubble,"Pause focus",v->{if(eligibleTap())pauseFocus();},false);
        layout=new WindowManager.LayoutParams(dp(176),dp(250),WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE|WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,PixelFormat.TRANSLUCENT);
        layout.gravity=Gravity.TOP|Gravity.LEFT;layout.x=dp(16);layout.y=dp(80);
        layout.setTitle("FocusPilot floating Mira");
        if(Build.VERSION.SDK_INT>=30){layout.setFitInsetsTypes(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout()|WindowInsets.Type.ime());layout.setFitInsetsSides(WindowInsets.Side.all());}
        updateOwnStatus();
    }
    private Button addButton(LinearLayout parent,String label,View.OnClickListener action,boolean row){
        Button button=new Button(this);button.setText(label);button.setTextSize(12);button.setAllCaps(false);button.setMinWidth(0);button.setMinimumWidth(0);button.setPadding(dp(2),0,dp(2),0);
        button.setTextColor(Color.rgb(22,20,31));GradientDrawable shape=new GradientDrawable();shape.setColor(Color.rgb(203,171,238));shape.setCornerRadius(dp(12));button.setBackground(shape);
        LinearLayout.LayoutParams params=row?new LinearLayout.LayoutParams(0,dp(48),1):new LinearLayout.LayoutParams(-1,dp(48));params.setMargins(dp(2),dp(2),dp(2),dp(2));parent.addView(button,params);button.setOnClickListener(action);return button;
    }
    private void updateOwnStatus(){
        if(mira==null)return;
        boolean active=repository.session.isActive();
        mira.setReduceMotion(repository.prefs.getBoolean("reduceMotion",false)||!ValueAnimator.areAnimatorsEnabled());
        mira.setState(active?CompanionView.State.FOCUS:CompanionView.State.PAUSED);
        String label=active?"Focus active":"Focus paused";
        if(active && repository.session.isTimed()){
            long seconds=(repository.session.remainingMs(SystemClock.elapsedRealtime())+999)/1000;
            label=String.format(Locale.US,"Focus %02d:%02d",seconds/60,seconds%60);
        }
        focusStatus.setText(label);pauseButton.setEnabled(active);
    }
    private boolean eligibleTap(){
        if(!running || !attached || ending)return false;
        String blocked=blockedReason(this);if(blocked!=null){if(permanentBlockedReason(this)!=null)end(blocked);else suspendPortrait();return false;}return true;
    }
    private void pauseFocus(){
        repository.pause("Focus paused from floating Mira");stopService(new Intent(this,FocusMonitorService.class));updateOwnStatus();
        getSystemService(NotificationManager.class).notify(ID,notification());
    }
    private void openAssistant(){
        if(!eligibleTap())return;
        // Explicit tap only: the activity still requires separate Speak/Load/Understand taps.
        // Reuse an existing assistant instance; a repeated tap must not replace its draft.
        try{startActivity(assistantIntent().addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));}
        catch(RuntimeException error){lastStatus="Ask Mira launch failed · use Mira’s notification or app launcher";}
    }
    private Intent assistantIntent(){
        return new Intent(this,LocalModelActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
    }
    private Notification notification(){
        PendingIntent open=PendingIntent.getActivity(this,42,assistantIntent(),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent hide=PendingIntent.getService(this,43,new Intent(this,FloatingCompanionService.class).setAction(HIDE),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent pause=PendingIntent.getService(this,44,new Intent(this,FloatingCompanionService.class).setAction(PAUSE),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder builder=new Notification.Builder(this,CHANNEL).setSmallIcon(R.drawable.ic_notification).setContentTitle(waitingForUnlock?"Mira is available · hidden while locked":"Mira is floating")
            .setContentText(waitingForUnlock?"Portrait returns after unlock. Hide ends this session. Mira’s microphone and model stay idle.":"Tap to Ask Mira. Speak and model understanding start only in the app when you choose.")
            .setContentIntent(open).setOngoing(true).setOnlyAlertOnce(true).setCategory(Notification.CATEGORY_SERVICE);
        if(!waitingForUnlock)builder.addAction(new Notification.Action.Builder(null,"Pause focus",pause).build());
        return builder.addAction(new Notification.Action.Builder(null,"Hide Mira",hide).build()).build();
    }
    private boolean refreshBounds(){
        if(windows==null || layout==null)return false;
        Rect bounds;int left=0,top=0,right=0,bottom=0;
        if(Build.VERSION.SDK_INT>=30){
            android.view.WindowMetrics metrics=windows.getCurrentWindowMetrics();bounds=metrics.getBounds();
            android.graphics.Insets insets=metrics.getWindowInsets().getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout()|WindowInsets.Type.ime());
            left=insets.left;top=insets.top;right=insets.right;bottom=insets.bottom;
        }else{android.util.DisplayMetrics metrics=new android.util.DisplayMetrics();windows.getDefaultDisplay().getMetrics(metrics);bounds=new Rect(0,0,metrics.widthPixels,metrics.heightPixels);}
        availableWidth=Math.max(0,bounds.width()-left-right);availableHeight=Math.max(0,bounds.height()-top-bottom);
        // Do not silently shrink away Stop controls if the usable display cannot hold them.
        if(availableWidth<layout.width || availableHeight<layout.height){end("Mira hidden · display too small for her controls");return false;}
        FloatingWindowPosition.Position position=FloatingWindowPosition.clamp(layout.x,layout.y,layout.width,layout.height,availableWidth,availableHeight);layout.x=position.x;layout.y=position.y;return true;
    }
    private void updateWindow(){
        if(!attached || ending)return;
        String blocked=blockedReason(this);if(blocked!=null){if(permanentBlockedReason(this)!=null)end(blocked);else suspendPortrait();return;}
        try{windows.updateViewLayout(bubble,layout);}catch(RuntimeException error){end("Android removed Mira · tap Show again if you want her");}
    }
    @Override public void onConfigurationChanged(Configuration config){super.onConfigurationChanged(config);if(attached && !ending && refreshBounds())updateWindow();}
    private void end(String reason){
        lastStatus=reason;ending=true;running=false;waitingForUnlock=false;returnAfterUnlockActive=false;availability.stop();cleanup();stopSelf();
    }
    private void cleanup(){
        handler.removeCallbacksAndMessages(null);
        if(mira!=null)mira.setState(CompanionView.State.PAUSED);
        if(attached){attached=false;try{windows.removeViewImmediate(bubble);}catch(RuntimeException ignored){/* Android may have already removed a revoked window. */}}
        bubble=null;mira=null;
        if(receiverRegistered){receiverRegistered=false;unregisterReceiver(screenOff);}
        if(watchingOps){watchingOps=false;ops.stopWatchingMode(permissionChange);}
        if(foreground){foreground=false;stopForeground(STOP_FOREGROUND_REMOVE);}
    }
    @Override public void onDestroy(){if(!ending)lastStatus="Android stopped floating Mira · tap Show to start again";running=false;waitingForUnlock=false;returnAfterUnlockActive=false;availability.stop();ending=true;cleanup();super.onDestroy();}
    @Override public IBinder onBind(Intent intent){return null;}
}
