package dev.focuspilot.prototype;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;

/** Optional feature setup. Reading readiness never changes consent, permissions or session state. */
public final class SetupActivity extends Activity {
    private static final int BG=Color.rgb(22,20,31), CARD=Color.rgb(36,32,49),
        INK=Color.rgb(247,241,250), MUTED=Color.rgb(184,174,198), LILAC=Color.rgb(203,171,238);
    private TextView usageStatus,notificationStatus,voiceStatus,modelStatus,sessionStatus,notice,floatingStatus;
    private CompanionView companion;
    private int dp(int value){return (int)(value*getResources().getDisplayMetrics().density);}
    private TextView text(String value,int size,boolean bold){
        TextView view=new TextView(this);view.setText(value);view.setTextSize(size);
        view.setTextColor(bold?INK:MUTED);view.setPadding(0,dp(6),0,dp(6));
        if(bold)view.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return view;
    }
    private LinearLayout card(LinearLayout root,String title){
        LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18),dp(14),dp(18),dp(14));
        GradientDrawable shape=new GradientDrawable();shape.setColor(CARD);shape.setCornerRadius(dp(22));card.setBackground(shape);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2);params.topMargin=dp(16);root.addView(card,params);
        card.addView(text(title,19,true));return card;
    }
    private void button(LinearLayout parent,String label,View.OnClickListener click){
        Button button=new Button(this);button.setText(label);button.setAllCaps(false);button.setTextSize(14);
        button.setTextColor(BG);button.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        GradientDrawable shape=new GradientDrawable();shape.setColor(LILAC);shape.setCornerRadius(dp(14));button.setBackground(shape);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(52));params.topMargin=dp(10);parent.addView(button,params);button.setOnClickListener(click);
    }
    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(BG);
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(22),dp(18),dp(22),dp(24));scroll.addView(root);
        scroll.setOnApplyWindowInsetsListener((view,insets)->{
            if(Build.VERSION.SDK_INT>=30){android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());view.setPadding(bars.left,bars.top,bars.right,bars.bottom);}
            else view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        root.addView(text("Make Mira yours",28,true));
        root.addView(text("Choose the features that help you. Typing and focus sessions work without optional permissions.",16,false));
        companion=new CompanionView(this);root.addView(companion,new LinearLayout.LayoutParams(-1,dp(150)));
        LinearLayout model=card(root,"1 · Ask on your phone");
        modelStatus=text("Checking local model files…",14,false);model.addView(modelStatus);
        button(model,"Ask Mira",v->startActivity(new Intent(this,LocalModelActivity.class)));
        LinearLayout usage=card(root,"2 · Keep your own app budget");
        usageStatus=text("",14,false);usage.addView(usageStatus);
        usage.addView(text("Android Usage Access permits reading app history. Mira reads your selected app only after you separately turn on local usage reading. Choose its budget on the dashboard.",14,false));
        button(usage,"Review Usage Access",v->new AlertDialog.Builder(this).setTitle("Optional selected-app usage")
            .setMessage("Open Android Usage Access and choose FocusPilot if you want app-budget reminders. Returning here does not start observation or a focus session.")
            .setNegativeButton("Cancel",null).setPositiveButton("Open Android settings",(d,w)->open(new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))).show());
        LinearLayout notifications=card(root,"3 · A visible companion session");
        notificationStatus=text("",14,false);notifications.addView(notificationStatus);
        notifications.addView(text("A background focus session needs a visible notification with Stop. Allow notifications if you want it, then start the session explicitly on the dashboard.",14,false));
        button(notifications,"Review notification settings",v->open(new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE,getPackageName())));
        LinearLayout floating=card(root,"Optional · Mira beside your apps");
        floatingStatus=text("",14,false);floating.addView(floatingStatus);
        floating.addView(text("Mira can float beside your apps and show your focus status. Review Android's Display over other apps permission, then review Show on the dashboard when you want her nearby.",14,false));
        floating.addView(text("Keep Mira nearby after I unlock is off by default. Choose it before Show if you want her portrait to return after unlock within that session. She stays hidden while locked. With the choice off, lock or screen-off ends the session. Android may stop either session. Hide ends availability and leaves focus unchanged; voice, model understanding and usage reading stay separate choices.",14,false));
        button(floating,"Review floating permission",v->new AlertDialog.Builder(this).setTitle("Optional floating Mira")
            .setMessage("Android may show a general Display over other apps list. Choose FocusPilot if you want the permission. Returning here starts nothing; visible floating notifications and a separate dashboard Show are also required.")
            .setNegativeButton("Cancel",null).setPositiveButton("Open Android settings",(d,w)->open(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+getPackageName())))).show());
        LinearLayout voice=card(root,"4 · Talk when you choose");
        voiceStatus=text("",14,false);voice.addView(voiceStatus);
        voice.addView(text("Ask Mira requests microphone access only when you tap Speak. You then tap again to start a draft. An installed offline English speech model is also needed. No always-listening microphone.",14,false));
        button(voice,"Try voice in Ask Mira",v->startActivity(new Intent(this,LocalModelActivity.class)));
        button(voice,"Review app permissions",v->open(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,Uri.parse("package:"+getPackageName()))));
        LinearLayout control=card(root,"Optional · Try phone selectors");
        control.addView(text("The research proof can control two invented elements in Mira’s own sandbox. Enable it manually in Android settings only if you want this test, then arm it separately for five seconds.",14,false));
        button(control,"Open selector sandbox",v->startActivity(new Intent(this,SandboxAutomationActivity.class)));
        LinearLayout finish=card(root,"You stay in control");
        sessionStatus=text("",14,false);finish.addView(sessionStatus);
        finish.addView(text("Pause stops decisions. You can revoke permissions in Android settings or delete local focus data and labels on the dashboard. Your points are virtual; no money moves.",14,false));
        notice=text("This screen only checks readiness. It starts no monitoring, microphone or phone action.",14,false);finish.addView(notice);
        button(finish,"Refresh readiness",v->refresh());button(finish,"Back to Mira",v->finish());
        root.addView(text("PRE-EVENT RESEARCH · local phone CPU model. iQOO NPU and Office Kit testing remain separate.",12,false));
        setContentView(scroll);scroll.requestApplyInsets();
    }
    @Override protected void onResume(){super.onResume();refresh();}
    @Override protected void onStop(){if(companion!=null)companion.setState(CompanionView.State.PAUSED);super.onStop();}
    private void refresh(){
        if(usageStatus==null)return;
        FocusRepository repository=FocusRepository.get(this);
        usageStatus.setText((FocusRepository.usageGranted(this)?"Usage Access allowed":"Usage Access off")+" · local usage reading "+(repository.observe?"enabled":"off"));
        notificationStatus.setText(FocusMonitorService.notificationsAllowed(this)?"Notifications available · starting a monitor is still your choice.":"Notifications blocked · background monitoring cannot start.");
        String miraState=!FloatingCompanionService.running?"Mira stopped · Show is your choice":
            FloatingCompanionService.waitingForUnlock?"Mira resting until unlock · Hide ends this session":
            FloatingCompanionService.returnAfterUnlockActive?"Mira nearby · returns after unlock within this session":
            "Mira nearby · lock or screen-off ends this session";
        floatingStatus.setText((Settings.canDrawOverlays(this)?"Overlay permission allowed":"Overlay permission off")+" · "+(FloatingCompanionService.notificationsAllowed(this)?"floating notifications available":"floating notifications blocked")+"\n"+miraState);
        boolean microphone=checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED;
        voiceStatus.setText("Microphone "+(microphone?"allowed":"off")+" · "+(LocalVoiceInput.available(this)?"on-device speech service available; installed English still needs checking.":"on-device speech service unavailable; typing works."));
        File model=new File(getFilesDir(),"qwen35.gguf");
        String readiness=model.isFile()?"A private model copy is present. Ask Mira verifies its checksum before loading.":"No private model copy yet. "+(bundledModelPresent()?"This APK includes one; Ask Mira can import and verify it.":"Install the bundled research APK or prepare the model with the laptop setup script.");
        modelStatus.setText(readiness+" No model is loaded by this setup screen.");
        sessionStatus.setText((repository.session.isActive()?"Focus active":"Focus paused")+" · "+(FocusMonitorService.running?"visible monitor running":"background monitor stopped"));
        android.content.SharedPreferences prefs=getSharedPreferences("focuspilot_research",MODE_PRIVATE);
        companion.setReduceMotion(prefs.getBoolean("reduceMotion",false));companion.setVisibility(prefs.getBoolean("hideCompanion",false)?View.GONE:View.VISIBLE);companion.setState(CompanionView.State.IDLE);
    }
    private boolean bundledModelPresent(){try(android.content.res.AssetFileDescriptor file=getAssets().openFd("qwen35.gguf")){return file.getLength()>0;}catch(java.io.IOException error){return false;}}
    private void open(Intent intent){try{startActivity(intent);}catch(ActivityNotFoundException|SecurityException error){notice.setText("This Android settings screen is unavailable. Open FocusPilot’s app settings manually if you want to change permissions.");}}
}
