package dev.focuspilot.prototype;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.Context;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import java.util.Locale;

/** Explicit, visible, user-stoppable focus session. No boot receiver or sticky restart. */
public final class FocusMonitorService extends Service {
    public static final String CHANNEL="focus_session", STOP="dev.focuspilot.prototype.STOP_MONITOR";
    public static volatile boolean running;
    private static final int ID=41;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private FocusRepository repository;
    private final Runnable tick=new Runnable() {
        public void run() {
            if(!running) return;
            if(!repository.observe || !repository.session.isActive() || !FocusRepository.usageGranted(FocusMonitorService.this) || !notificationsAllowed(FocusMonitorService.this)) { stopSession("Monitor stopped: a permission or session prerequisite changed"); return; }
            repository.tick(); ((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).notify(ID,notification()); handler.postDelayed(this,10_000);
        }
    };
    public static boolean notificationsAllowed(Context context) {
        if(Build.VERSION.SDK_INT>=33 && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) return false;
        NotificationManager manager=(NotificationManager)context.getSystemService(Context.NOTIFICATION_SERVICE);
        if(!manager.areNotificationsEnabled()) return false;
        NotificationChannel channel=manager.getNotificationChannel(CHANNEL);
        return channel==null || channel.getImportance()!=NotificationManager.IMPORTANCE_NONE;
    }
    @Override public void onCreate() { super.onCreate(); repository=FocusRepository.get(this); NotificationChannel channel=new NotificationChannel(CHANNEL,"Visible focus session",NotificationManager.IMPORTANCE_LOW); channel.setDescription("Opt-in local app-budget monitor; stop at any time"); ((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(channel); }
    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        if(intent==null || STOP.equals(intent.getAction())) { stopSession("Focus monitor stopped by user"); return START_NOT_STICKY; }
        if(!repository.observe || !FocusRepository.usageGranted(this) || !notificationsAllowed(this)) { stopSession("Monitor could not start: permission missing"); return START_NOT_STICKY; }
        repository.start();
        try {
            if(Build.VERSION.SDK_INT>=34) startForeground(ID,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            else startForeground(ID,notification());
            running=true; repository.log("Visible foreground focus monitor started"); handler.removeCallbacks(tick); handler.post(tick);
        } catch(RuntimeException error) { repository.log("Foreground start rejected by Android: "+error.getClass().getSimpleName()); stopSession("Monitor start rejected; focus paused"); }
        return START_NOT_STICKY;
    }
    private Notification notification() {
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,FocusMonitorService.class).setAction(STOP),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        String value=repository.usage()>repository.budgetMs ? "Your app is over its budget. Take a gentle break?" : "Quietly keeping your chosen app budget in view.";
        return new Notification.Builder(this,CHANNEL).setSmallIcon(dev.focuspilot.prototype.R.drawable.ic_notification).setContentTitle("FocusPilot companion · focus active")
            .setContentText(value).setStyle(new Notification.BigTextStyle().bigText(value+String.format(Locale.US," %d virtual points · no money moves. No microphone or screen capture.",repository.ledger.points())))
            .setContentIntent(open).addAction(new Notification.Action.Builder(null,"Stop focus",stop).build()).setOngoing(true).setOnlyAlertOnce(true).setCategory(Notification.CATEGORY_SERVICE).build();
    }
    private void stopSession(String reason) { running=false; handler.removeCallbacksAndMessages(null); repository.pause(reason); stopForeground(STOP_FOREGROUND_REMOVE); stopSelf(); }
    @Override public void onDestroy() { running=false; handler.removeCallbacksAndMessages(null); repository.pause("Foreground service ended; session paused"); super.onDestroy(); }
    @Override public IBinder onBind(Intent intent) { return null; }
}
