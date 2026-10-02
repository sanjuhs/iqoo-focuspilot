package dev.focuspilot.prototype;

import android.app.Activity;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Separate invented UI for a real, narrowly armed accessibility proof; no product state. */
public final class SandboxAutomationActivity extends Activity {
    private static final int BG=Color.rgb(26,26,36), TEXT=Color.rgb(244,239,250), ACCENT=Color.rgb(201,183,234);
    private final Handler main=new Handler(Looper.getMainLooper());
    private boolean foreground;
    private LinearLayout root,taskPanel;
    private CheckBox taskCheckbox;
    private Button openTask,arm,cancel,disable;
    private TextView connection,outcome,trace;
    private final StringBuilder events=new StringBuilder();
    private int eventCount;
    private final Runnable refresh=new Runnable(){@Override public void run(){if(foreground){refreshConnection();main.postDelayed(this,500);}}};
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(BG);root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
        root.setId(R.id.sandbox_proof_root);root.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);root.setPadding(dp(16),dp(12),dp(16),dp(16));scroll.addView(root);
        scroll.setOnApplyWindowInsetsListener((v,insets)->{
            if(Build.VERSION.SDK_INT>=30){Insets b=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());v.setPadding(b.left,b.top,b.right,b.bottom);}
            else v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());return insets;
        });
        button("Back to Mira",()->finish());
        label("Own-app automation proof",25,true);
        label("PRE-EVENT SYNTHETIC SANDBOX\nA manually armed five-second accessibility script can open the invented task below and check its checkbox. No other app or product action is accessible to this script.",14,false);
        connection=label("Service not connected. Enable it manually in Android Settings if you want to test this proof.",14,false);
        label("Synthetic task · no real data",19,true);
        openTask=button("Open synthetic task",()->{taskPanel.setVisibility(View.VISIBLE);openTask.setEnabled(false);outcome.setText("Synthetic panel opened. Waiting for the checkbox action.");});
        openTask.setId(R.id.sandbox_open_task);
        taskPanel=new LinearLayout(this);taskPanel.setId(R.id.sandbox_task_panel);taskPanel.setOrientation(LinearLayout.VERTICAL);
        taskPanel.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);taskPanel.setVisibility(View.GONE);root.addView(taskPanel);
        taskCheckbox=new CheckBox(this);taskCheckbox.setId(R.id.sandbox_task_checkbox);taskCheckbox.setText("Complete this invented checklist item");taskCheckbox.setTextColor(TEXT);taskCheckbox.setTextSize(15);taskCheckbox.setMinHeight(dp(48));taskPanel.addView(taskCheckbox);
        taskCheckbox.setOnCheckedChangeListener((view,checked)->outcome.setText(checked?"Synthetic checkbox is checked. Service must independently verify the accessibility node before reporting proof success.":"Synthetic checkbox is not checked."));
        outcome=label("Not armed. No selector action has been authorized.",15,true);
        arm=button("Arm one synthetic proof · five seconds",()->{
            resetSynthetic();events.setLength(0);eventCount=0;trace.setText("No accessibility action recorded for this run.");
            SandboxAccessibilityService.arm(this);refreshConnection();
        });
        cancel=button("Cancel armed proof",()->{SandboxAccessibilityService.cancel(this);proofStatus("Cancelled by user. Tap Arm only if you want a new proof.");refreshConnection();});
        button("Reset synthetic task manually",()->{SandboxAccessibilityService.cancel(this);resetSynthetic();proofStatus("Synthetic task reset by explicit user tap. No accessibility proof was run.");});
        button("Open Android Accessibility Settings",()->{
            SandboxAccessibilityService.cancel(this);
            try{startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));}
            catch(RuntimeException error){proofStatus("Accessibility Settings unavailable. Service stays unarmed.");}
        });
        disable=button("Disable sandbox accessibility service",()->{SandboxAccessibilityService.disableForUser(this);refreshConnection();});
        label("Synthetic outcome trace",18,true);trace=label("No proof run yet. This trace stores only fixed script outcomes for this screen, not UI text or app history.",13,false);trace.setTextIsSelectable(true);
        label("Manual enablement only. In Android Accessibility Settings, choose Mira · own-app automation proof, inspect the permission and enable it yourself. Return here and tap Arm. Enabling the service alone never starts automation. Leaving this screen cancels the arm; controls in the focus ledger, monitor and model review are excluded.",13,false);
        setContentView(scroll);scroll.requestApplyInsets();
    }
    private void resetSynthetic(){openTask.setEnabled(true);taskPanel.setVisibility(View.GONE);taskCheckbox.setChecked(false);outcome.setText("Synthetic task reset. No action authorized until a fresh Arm tap.");}
    boolean isSandboxForeground(){return foreground&&hasWindowFocus();}
    void proofStatus(String message){
        if(outcome==null)return;outcome.setText(message);
        if(eventCount>=8){events.setLength(0);eventCount=0;}
        events.append(++eventCount).append(". ").append(message).append('\n');if(trace!=null)trace.setText(events.toString());
        refreshConnection();
    }
    private void refreshConnection(){if(arm==null)return;boolean connected=SandboxAccessibilityService.connected();boolean armed=SandboxAccessibilityService.armedFor(this);
        connection.setText(connected?"Service connected · package filter: own app only. A fresh foreground Arm tap is still required.":"Service not connected. Enable it manually in Android Accessibility Settings to run this optional proof.");
        arm.setEnabled(isSandboxForeground()&&connected&&!armed);cancel.setEnabled(isSandboxForeground()&&armed);disable.setEnabled(isSandboxForeground()&&connected);
    }
    @Override protected void onResume(){super.onResume();foreground=true;main.post(refresh);}
    @Override protected void onPause(){foreground=false;main.removeCallbacks(refresh);SandboxAccessibilityService.cancel(this);super.onPause();}
    @Override public void onWindowFocusChanged(boolean focused){super.onWindowFocusChanged(focused);
        if(!focused&&SandboxAccessibilityService.armedFor(this)){SandboxAccessibilityService.cancel(this);proofStatus("Window focus left the sandbox; arm cancelled.");}
        refreshConnection();
    }
    @Override protected void onDestroy(){foreground=false;main.removeCallbacksAndMessages(null);SandboxAccessibilityService.cancel(this);super.onDestroy();}
    private TextView label(String text,int size,boolean bold){TextView v=new TextView(this);v.setText(text);v.setTextColor(TEXT);v.setTextSize(size);v.setPadding(0,dp(6),0,dp(6));if(bold)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);root.addView(v,new LinearLayout.LayoutParams(-1,-2));return v;}
    private Button button(String title,Runnable action){Button v=new Button(this);v.setText(title);v.setAllCaps(false);v.setTextColor(BG);v.setBackgroundTintList(ColorStateList.valueOf(ACCENT));root.addView(v,new LinearLayout.LayoutParams(-1,dp(48)));v.setOnClickListener(view->action.run());return v;}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}
