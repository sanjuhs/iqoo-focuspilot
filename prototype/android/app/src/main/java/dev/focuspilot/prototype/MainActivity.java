package dev.focuspilot.prototype;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.AppOpsManager;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Process;
import android.os.SystemClock;
import android.provider.AlarmClock;
import android.provider.Settings;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import org.json.JSONArray;
import java.util.ArrayList;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int BG = Color.rgb(22,20,31), CARD = Color.rgb(36,32,49), TEAL = Color.rgb(203,171,238), WHITE = Color.rgb(247,241,250), MUTED = Color.rgb(184,174,198);
    private final Handler handler = new Handler(Looper.getMainLooper());
    private FocusSession session;
    private FocusRepository repository;
    private final DecisionPolicy policy = new DecisionPolicy();
    private VirtualLedger ledger;
    private final VirtualLedger demoLedger = new VirtualLedger();
    private final CommandParser parser = new CommandParser();
    private SharedPreferences prefs;
    private LinearLayout root;
    private TextView timer, sessionLabel, usageLabel, pointsLabel, trace, status, logView, speechState, monitorStatus, companionMessage, goalLabel, shadowTrace;
    private CompanionView companion;
    private Button sessionButton, heroFocusButton;
    private EditText commandInput, packageInput, budgetInput, goalInput, plannedInput, continuousInput;
    private Switch observeSwitch;
    private String monitoredPackage;
    private long budgetMs;
    private boolean observe, visible, simulated, listening, offlineVoiceReady;
    private boolean muted, reduceMotion, hideCompanion, updatingMonitor;
    private long celebrateUntil;
    private Switch monitorSwitch;
    private LocalVoiceInput voiceInput;
    private final VoiceDraftState voiceDraft=new VoiceDraftState();
    private TextToSpeech tts;
    private final ArrayList<String> events = new ArrayList<>();
    private final Runnable refreshTask = new Runnable() {
        @Override public void run() { if (visible) { refresh(); handler.postDelayed(this, 5000); } }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        repository=FocusRepository.get(this); prefs=repository.prefs; session=repository.session; ledger=repository.ledger;
        monitoredPackage=repository.selectedPackage; budgetMs=repository.budgetMs; observe=repository.observe;
        muted=prefs.getBoolean("mute",false); reduceMotion=prefs.getBoolean("reduceMotion",false); hideCompanion=prefs.getBoolean("hideCompanion",false);
        try { JSONArray saved = new JSONArray(prefs.getString("events", "[]")); for (int i=0; i<saved.length(); i++) events.add(saved.getString(i)); } catch (Exception ignored) {}
        buildUi();
        voiceInput=new LocalVoiceInput(this,voiceDraft,new LocalVoiceInput.Listener() {
            public void onStatus(String value) { showStatus(value.startsWith("Voice draft ready.") ? "Voice draft ready. Review it, then tap Run command. Nothing executed." : value); }
            public void onDraft(String value) { commandInput.setText(value); }
            public void onChanged() { listening=voiceDraft.active(); if(visible) refresh(); }
        });
        tts = new TextToSpeech(this, result -> {
            if (result == TextToSpeech.SUCCESS && tts != null && tts.getVoices() != null) {
                for (Voice voice : tts.getVoices()) {
                    if (!voice.isNetworkConnectionRequired() && voice.getLocale().getLanguage().equals("en")) {
                        offlineVoiceReady = tts.setVoice(voice) == TextToSpeech.SUCCESS; break;
                    }
                }
            }
        });
    }
    private int dp(float value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private GradientDrawable rounded(int color, int radius) { GradientDrawable shape = new GradientDrawable(); shape.setColor(color); shape.setCornerRadius(dp(radius)); return shape; }
    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        view.setPadding(0, dp(4), 0, dp(4)); return view;
    }
    private LinearLayout card(String title) {
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(20),dp(18),dp(20),dp(18)); box.setBackground(rounded(CARD,22));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1,-2); lp.bottomMargin=dp(14); root.addView(box,lp);
        box.addView(text(title,12,TEAL,true)); return box;
    }
    private Button button(String label, LinearLayout parent, View.OnClickListener action, boolean primary) {
        Button button = new Button(this); button.setText(label); button.setAllCaps(false); button.setTextSize(14); button.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        button.setTextColor(primary ? BG : TEAL); button.setBackground(rounded(primary ? TEAL : Color.rgb(29,58,62),14));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1,dp(50)); lp.topMargin=dp(10); parent.addView(button,lp); button.setOnClickListener(action); return button;
    }
    private EditText input(String hint, String value, LinearLayout parent) {
        EditText input = new EditText(this); input.setText(value); input.setHint(hint); input.setTextColor(WHITE); input.setHintTextColor(MUTED); input.setTextSize(15); input.setSingleLine(true);
        input.setPadding(dp(12),dp(8),dp(12),dp(8)); input.setBackground(rounded(Color.rgb(9,27,31),10));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(48)); lp.topMargin=dp(8); parent.addView(input,lp); return input;
    }
    private void preferenceToggle(LinearLayout parent,String label,boolean checked,java.util.function.Consumer<Boolean> change) {
        Switch toggle=new Switch(this); toggle.setText(label); toggle.setTextColor(WHITE); toggle.setMinHeight(dp(48)); toggle.setChecked(checked); parent.addView(toggle);
        toggle.setOnCheckedChangeListener((view,value) -> change.accept(value));
    }
    private LinearLayout disclosure(LinearLayout parent,String label) {
        LinearLayout details=new LinearLayout(this); details.setOrientation(LinearLayout.VERTICAL); details.setVisibility(View.GONE);
        Button toggle=button(label+" ▾",parent,null,false);
        toggle.setOnClickListener(view -> { boolean opening=details.getVisibility()!=View.VISIBLE; details.setVisibility(opening ? View.VISIBLE : View.GONE); toggle.setText(label+(opening ? " ▴" : " ▾")); toggle.setContentDescription(label+(opening ? ", expanded" : ", collapsed")); });
        toggle.setContentDescription(label+", collapsed"); parent.addView(details); return details;
    }
    private Button heroAction(String label,LinearLayout row,View.OnClickListener action,boolean primary) {
        Button actionButton=new Button(this); actionButton.setText(label); actionButton.setAllCaps(false); actionButton.setTextSize(14); actionButton.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        actionButton.setTextColor(primary ? BG : TEAL); actionButton.setBackground(rounded(primary ? TEAL : Color.rgb(29,58,62),14));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(50),1); lp.setMargins(dp(3),dp(8),dp(3),dp(8)); row.addView(actionButton,lp); actionButton.setOnClickListener(action); return actionButton;
    }
    private void buildUi() {
        LinearLayout screen=new LinearLayout(this); screen.setOrientation(LinearLayout.VERTICAL); screen.setBackgroundColor(BG);
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(BG);
        screen.setOnApplyWindowInsetsListener((view,insets) -> {
            if(Build.VERSION.SDK_INT>=30) {
                android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                view.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            } else {
                view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(20),dp(16),dp(20),dp(20)); scroll.addView(root);
        root.addView(text("FOCUSPILOT",12,TEAL,true)); root.addView(text("A little focus, with Mira.",25,WHITE,true));
        root.addView(text("PRE-EVENT RESEARCH",10,Color.rgb(249,204,130),true));
        LinearLayout friend=card("YOUR QUIET COMPANION");
        companion=new CompanionView(this); companion.setReduceMotion(reduceMotion); friend.addView(companion,new LinearLayout.LayoutParams(-1,dp(170))); companion.setVisibility(hideCompanion ? View.GONE : View.VISIBLE);
        LinearLayout heroActions=new LinearLayout(this); heroActions.setOrientation(LinearLayout.HORIZONTAL); friend.addView(heroActions);
        heroAction("Ask Mira",heroActions,v -> startActivity(new Intent(this,LocalModelActivity.class)),true);
        heroFocusButton=heroAction("Start focus",heroActions,v -> toggleFocus(),false);
        companionMessage=text("Ready when you are. One gentle step at a time.",16,WHITE,true); friend.addView(companionMessage);
        LinearLayout preferences=disclosure(friend,"Companion preferences");
        preferences.addView(text("Make Mira feel right for you. Hiding her artwork keeps your focus controls available.",13,MUTED,false));
        preferenceToggle(preferences,"Reduce motion",reduceMotion,value -> { reduceMotion=value; prefs.edit().putBoolean("reduceMotion",value).apply(); companion.setReduceMotion(value); });
        preferenceToggle(preferences,"Mute companion voice",muted,value -> { muted=value; prefs.edit().putBoolean("mute",value).apply(); if(value && tts!=null) tts.stop(); });
        preferenceToggle(preferences,"Hide companion artwork",hideCompanion,value -> { hideCompanion=value; prefs.edit().putBoolean("hideCompanion",value).apply(); companion.setVisibility(value ? View.GONE : View.VISIBLE); });
        LinearLayout focus = card("YOUR FOCUS SESSION");
        sessionLabel = text("Ready when you are",20,WHITE,true); focus.addView(sessionLabel);
        timer = text("00:00",52,WHITE,true); focus.addView(timer);
        goalLabel=text("One task at a time.",16,WHITE,true); focus.addView(goalLabel);
        LinearLayout goals=disclosure(focus,"Choose your task & targets");
        goals.addView(text("Your task stays private on this phone. Optional targets help explain usage; the session runs until you pause it. Leave a target blank when you haven't chosen one.",13,MUTED,false));
        goals.addView(text("What would you like to work on?",13,WHITE,false));
        goalInput=input("One small task",prefs.getString("focusGoal",""),goals);
        goalInput.setContentDescription("Focus task");
        goalInput.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(120)});
        goals.addView(text("Planned focus minutes · optional",13,WHITE,false));
        plannedInput=input("Blank = no target",limitText(repository.shadowPlannedFocusMs),goals); plannedInput.setInputType(2);
        plannedInput.setContentDescription("Planned focus minutes");
        goals.addView(text("Continuous selected-app minutes · optional",13,WHITE,false));
        continuousInput=input("Blank = no target",limitText(repository.shadowContinuousLimitMs),goals); continuousInput.setInputType(2);
        continuousInput.setContentDescription("Continuous selected-app minutes");
        button("Save task & targets",goals,v -> saveGoal(),true);
        sessionButton = button("Start focus",focus,v -> toggleFocus(),true);
        button("Reset this session",focus,v -> resetSession(),false);
        LinearLayout monitor=card("STAY WITH ME · OPT-IN BACKGROUND FOCUS");
        monitorStatus=text("Monitor stopped",18,WHITE,true); monitor.addView(monitorStatus);
        monitor.addView(text("Continue one app-budget session when this app is closed, using a visible notification with Stop. Turn on usage reading, grant Usage Access, and allow notifications first. No always-listening microphone or screen capture. Android/OEM power rules can stop it.",13,MUTED,false));
        monitorSwitch=new Switch(this); monitorSwitch.setText("Keep this focus session in the background"); monitorSwitch.setTextColor(WHITE); monitor.addView(monitorSwitch);
        monitorSwitch.setOnCheckedChangeListener((view,enabled) -> { if(updatingMonitor) return; if(enabled) enableMonitor(); else { stopMonitor("Focus monitor stopped by user"); refresh(); } });
        LinearLayout usage = card("AWARENESS · YOU CHOOSE THE BOUNDARY");
        usageLabel = text("Usage reading is off",18,WHITE,true); usage.addView(usageLabel);
        usage.addView(text("Reads only the selected app's OS usage history. Normally the dashboard reads it; the separately enabled visible monitor can check in the background. No screenshots or screen control.",13,MUTED,false));
        observeSwitch = new Switch(this); observeSwitch.setText("Opt in to local usage reading"); observeSwitch.setTextColor(WHITE); observeSwitch.setChecked(observe); usage.addView(observeSwitch);
        observeSwitch.setOnCheckedChangeListener((view,enabled) -> { if(!enabled) stopMonitor("Observation disabled; monitor stopped"); observe=enabled; repository.setObservation(enabled); simulated=false; refresh(); });
        button("Open Android Usage Access",usage,v -> {
            new AlertDialog.Builder(this).setTitle("Optional usage permission").setMessage("Android grants access to usage history. FocusPilot reads only your selected app and stores local summaries. A separate opt-in foreground monitor can continue with a visible Stop notification. You can turn either off or revoke access in Android settings.")
            .setNegativeButton("Cancel",null).setPositiveButton("Open settings",(d,w) -> { try { startActivity(new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)); } catch(ActivityNotFoundException error) { showStatus("Usage Access settings unavailable on this device."); } }).show();
        },false);
        packageInput=input("App package",monitoredPackage,usage); budgetInput=input("Budget in minutes (1–120)",String.valueOf(budgetMs/60_000),usage); budgetInput.setInputType(2);
        button("Save app & budget",usage,v -> saveSettings(),false);
        LinearLayout decision=card("FAST DECISION · VISIBLE REASONING");
        pointsLabel=text("100 virtual points",26,WHITE,true); decision.addView(pointsLabel);
        decision.addView(text("Simulated accountability only. No money moves.\n60-second nudge cooldown; pause always overrides.",13,MUTED,false));
        trace=text("Hand-set positive weights. No trained model.",14,MUTED,false); decision.addView(trace);
        button("Try simulated over-budget state",decision,v -> { simulated=true; demoLedger.reset(); log("SIMULATED state: selected app at twice its budget"); companion.setState(CompanionView.State.NUDGE); refresh(); },false);
        button("Return to real session state",decision,v -> { simulated=false; showStatus("Simulation cleared."); refresh(); },false);
        LinearLayout shadow=disclosure(decision,"Explain observed state · research");
        shadow.addView(text("The tiny trained network can inspect six measured inputs here. It was trained on synthetic labels; its score is uncalibrated and changes no actions or points. Missing inputs block evaluation.",13,MUTED,false));
        shadowTrace=text("Paused · no observation",13,MUTED,false); shadow.addView(shadowTrace);
        button("Defer the latest real nudge",shadow,v -> {
            boolean saved=repository.userDeferredNudge();
            showStatus(saved ? "Feedback noted for this observation scope. No points refunded or actions changed." : "No fresh real nudge to defer. Practice nudges do not count.");
            refresh();
        },false);
        LinearLayout commands=card("ASK FOR A SMALL NEXT STEP");
        commands.addView(text("Quick shortcuts: start focus, pause, or set an alarm. These use a predictable parser. Ask Mira opens the local model for more natural requests, with a review before actions.",13,MUTED,false));
        commandInput=input("Try: alarm 7:30 pm", "",commands); commandInput.setInputType(1);
        button("Run command",commands,v -> execute(commandInput.getText().toString()),true);
        speechState=text("Voice: checking on-device availability",13,MUTED,false); commands.addView(speechState);
        button("Push to talk / stop",commands,v -> microphone(),false);
        button("Speak focus status offline",commands,v -> speak(session.isActive() ? "Your focus session is active. One task at a time." : "Your session is paused. Start when you are ready."),false);
        status=text("Ready. All data stays in this app.",14,TEAL,false); commands.addView(status);
        LinearLayout model=card("LOCAL MODEL · LABORATORY");
        model.addView(text("Qwen3.5-0.8B · on-request CPU lab",20,WHITE,true));
        model.addView(text("Load the checksummed local model, understand a short command and review its proposed action. The model can make mistakes; every action is separately validated and confirmed. Actual tensor observations are optional research tools.",13,MUTED,false));
        button("Open local command model",model,v -> startActivity(new Intent(this,LocalModelActivity.class)),true);
        button("Explore trained decision sandbox",model,v -> startActivity(new Intent(this,PolicyLabActivity.class)),false);
        button("Teach Mira · few-shot sandbox",model,v -> startActivity(new Intent(this,PersonalizationActivity.class)),false);
        LinearLayout facts=card("BEHIND THE COMPANION");
        LinearLayout researchFacts=disclosure(facts,"Build and research facts");
        researchFacts.addView(text("Quick commands use a deterministic fallback. Ask Mira opens on-request Qwen3.5-0.8B CPU inference in the model lab; its load state, backend and measurements are shown there. Weights are prepared separately. Recurring nudges use hand-set rules; the separate trained 65-parameter sandbox uses synthetic data. NPU, causal LLM interpretation, Accessibility, overlay and Office Kit remain unverified.",13,MUTED,false));
        LinearLayout history=card("LOCAL EVENT TRAIL");
        logView=text("No events yet",13,MUTED,false); history.addView(logView);
        button("Delete focus data & saved examples",history,v -> new AlertDialog.Builder(this).setTitle("Delete FocusPilot data?").setMessage("Clears saved settings, event history and few-shot labels, stops the session and disables observation. The downloaded model stays installed. Android permissions can be revoked separately in system settings.").setNegativeButton("Cancel",null).setPositiveButton("Delete",(d,w) -> deleteData()).show(),false);
        root.addView(text("RESEARCH BUILD · 0.4\nNo real money moves. You choose when to pause.",12,MUTED,false));
        screen.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout safetyBar=new LinearLayout(this); safetyBar.setOrientation(LinearLayout.VERTICAL); safetyBar.setPadding(dp(20),0,dp(20),dp(8)); safetyBar.setBackgroundColor(BG);
        button("Stop focus",safetyBar,v -> pauseFocus(),false);
        screen.addView(safetyBar,new LinearLayout.LayoutParams(-1,-2));
        setContentView(screen); screen.requestApplyInsets(); renderLogs();
    }
    @Override protected void onResume() { super.onResume(); visible=true; voiceDraft.resume(); handler.removeCallbacks(refreshTask); handler.post(refreshTask); }
    @Override protected void onStop() { visible=false; handler.removeCallbacks(refreshTask); voiceDraft.stop(); if(voiceInput!=null) voiceInput.cancel(); listening=false; if(tts!=null) tts.stop(); super.onStop(); }
    @Override protected void onDestroy() { handler.removeCallbacksAndMessages(null); if(voiceInput!=null) voiceInput.close(); if(tts!=null) tts.shutdown(); super.onDestroy(); }
    private boolean usageGranted() { return FocusRepository.usageGranted(this); }
    private long realUsage() { return repository.usage(); }
    private void refresh() {
        if(timer==null) return;
        repository.tick();
        long now=SystemClock.elapsedRealtime(), duration=session.elapsed(now), usage=realUsage();
        timer.setText(String.format(Locale.US,"%02d:%02d",duration/60_000,(duration/1000)%60));
        String goal=prefs.getString("focusGoal","");
        goalLabel.setText(goal.isEmpty() ? "One task at a time." : "Your task · "+goal);
        sessionLabel.setText(session.isActive() ? "In your focus zone" : "Paused · you're in control"); sessionButton.setText(session.isActive() ? "Pause focus" : "Start / resume focus");
        heroFocusButton.setText(session.isActive() ? "Pause focus" : "Start focus");
        usageLabel.setText(!observe ? "Usage reading is off" : !usageGranted() ? "Usage Access needed" : String.format(Locale.US,"%.1f / %d min · %s",usage/60_000.0,budgetMs/60_000,monitoredPackage));
        VirtualLedger current=simulated ? demoLedger : ledger;
        DecisionPolicy.Result result=policy.evaluate(simulated ? budgetMs*2 : usage,budgetMs,simulated || (session.isActive() && observe && usageGranted()),now,current.lastNudge());
        if(simulated && current.apply(result,now)) log("SIMULATED: budget nudge · −5 virtual points");
        pointsLabel.setText(current.points()+" virtual points"+(simulated ? " · SANDBOX" : ""));
        trace.setText((simulated ? "SIMULATED INPUT · 2× budget\n" : "REAL USAGE SUMMARY\n")+result.explanation()+"\n"+(current.lastNudge()>=0 && now-current.lastNudge()<DecisionPolicy.COOLDOWN_MS ? "Cooldown active" : "Ready to evaluate"));
        renderShadow();
        speechState.setText(LocalVoiceInput.available(this) ? "On-device speech service available · language model may be missing" : "Offline voice unavailable here · type a command");
        setMonitorChecked(FocusMonitorService.running);
        monitorStatus.setText(FocusMonitorService.running ? "Visible monitor running · notification has Stop" : "Monitor stopped · dashboard-only checking");
        CompanionView.State mood=listening ? CompanionView.State.LISTEN : simulated ? CompanionView.State.NUDGE : !session.isActive() ? CompanionView.State.PAUSED : now<celebrateUntil ? CompanionView.State.CELEBRATE : usage>budgetMs ? CompanionView.State.NUDGE : CompanionView.State.FOCUS;
        companion.setState(mood);
        companionMessage.setText(repository.interrupted ? "That session was interrupted. I've kept the last checkpoint paused; restart whenever you're ready." : listening ? "I'm listening. No rush — one small request." : simulated ? "Practice mode: let's take a tiny break together. These are virtual points." : !session.isActive() ? "Rest is part of focus, too. I'll be here when you're ready." : usage>budgetMs ? "You've reached your own app limit. Want to return to what matters?" : "You've got this. Let's make space for one good thing.");
        renderLogs();
    }
    private void startFocus() { repository.start(); simulated=false; celebrateUntil=SystemClock.elapsedRealtime()+1600; refresh(); handler.postDelayed(() -> { if(visible) refresh(); },1600); }
    private void pauseFocus() { if(voiceInput!=null) voiceInput.cancel(); listening=false; if(tts!=null) tts.stop(); stopMonitor("Focus paused · monitor and decision actions stopped"); simulated=false; refresh(); }
    private void toggleFocus() { if(session.isActive()) pauseFocus(); else startFocus(); }
    private void resetSession() { stopMonitor("Session reset; monitor stopped"); repository.reset(); simulated=false; refresh(); }
    private void setMonitorChecked(boolean checked) { updatingMonitor=true; monitorSwitch.setChecked(checked); updatingMonitor=false; }
    private void enableMonitor() {
        setMonitorChecked(false);
        if(!visible || !observe || !usageGranted()) { showStatus("To start the visible monitor, turn on usage reading and grant Usage Access first."); return; }
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) { requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},12); return; }
        if(!MonitorGate.canStart(visible,observe,usageGranted(),FocusMonitorService.notificationsAllowed(this))) { showStatus("Monitor needs visible notifications. Enable them in Android app settings, then try again."); return; }
        try {
            repository.start(); startForegroundService(new Intent(this,FocusMonitorService.class).setAction("START")); simulated=false;
            showStatus("Starting visible focus monitor. Its notification always offers Stop."); handler.postDelayed(() -> { if(visible) refresh(); },500);
        } catch(RuntimeException error) { repository.pause("Android rejected foreground start"); showStatus("Android could not start monitoring. Session paused; no hidden fallback."); }
    }
    private void stopMonitor(String reason) { stopService(new Intent(this,FocusMonitorService.class)); repository.pause(reason); setMonitorChecked(false); }
    private void saveSettings() {
        String value=packageInput.getText().toString().trim(); int minutes;
        try { minutes=Integer.parseInt(budgetInput.getText().toString()); } catch(Exception error) { showStatus("Enter a budget from 1 to 120 minutes."); return; }
        if(!MonitorConfig.valid(value,minutes*60_000L)) { showStatus("Use an Android app package and a 1–120 minute budget."); return; }
        stopMonitor("Settings changed; monitor/session paused for review"); monitoredPackage=value; budgetMs=minutes*60_000L;
        repository.configure(value,budgetMs); plannedInput.setText(""); continuousInput.setText(""); simulated=false; showStatus("Settings saved. Optional explanation targets cleared for the new app/budget. Restart focus/monitor when ready."); refresh();
    }
    private static String limitText(long milliseconds) { return milliseconds<=0 ? "" : String.valueOf(milliseconds/60_000); }
    private void saveGoal() {
        FocusGoalConfig value;
        try { value=FocusGoalConfig.parse(goalInput.getText().toString(),plannedInput.getText().toString(),continuousInput.getText().toString()); }
        catch(IllegalArgumentException error) { showStatus(error.getMessage()); return; }
        stopMonitor("Task/targets changed; focus paused for review");
        prefs.edit().putString("focusGoal",value.goal).apply();
        repository.configureShadowLimits(value.continuousMs,value.plannedMs);
        goalInput.setText(value.goal); simulated=false;
        showStatus("Task and declared targets saved privately. Restart focus when ready; targets don't stop it automatically."); refresh();
    }
    private void renderShadow() {
        ObservationSnapshot.ShadowTrace shadow=repository.shadowDecision();
        if(!shadow.evaluated()) { shadowTrace.setText("SHADOW · NO ACTIONS\nUnavailable: "+shadow.blockedReason); return; }
        TrainedPolicy.Evaluation evaluation=shadow.evaluation;
        StringBuilder details=new StringBuilder(String.format(Locale.US,"SHADOW · NO ACTIONS\nUncalibrated synthetic-teacher score: %.4f\n",evaluation.score));
        String[] names=TrainedPolicy.featureNames(); double[] features=evaluation.features(),drops=evaluation.featureAblationDrops();
        for(int i=0;i<names.length;i++) details.append(String.format(Locale.US,"%s: %.3f · zeroing changes score by %.4f\n",names[i].replace('_',' '),features[i],drops[i]));
        details.append(String.format(Locale.US,"Exact hidden contributions to logit (bias %.4f):\n",evaluation.outputBias));
        double[] contributions=evaluation.hiddenContributions();
        for(int i=0;i<contributions.length;i++) details.append(String.format(Locale.US,"h%d %.4f%s",i,contributions[i],i==contributions.length-1 ? "" : " · "));
        shadowTrace.setText(details.toString());
    }
    private void execute(String input) {
        if(!voiceDraft.canUnderstand()) { showStatus("Finish or stop voice before running a reviewed command."); return; }
        CommandParser.Command command=parser.parse(input);
        if(command.kind==CommandParser.Kind.START) { startFocus(); showStatus("Focus session active."); }
        else if(command.kind==CommandParser.Kind.PAUSE) { pauseFocus(); showStatus("Focus session paused."); }
        else if(command.kind==CommandParser.Kind.ALARM) {
            String formatted=String.format(Locale.US,"%02d:%02d",command.hour,command.minute);
            new AlertDialog.Builder(this).setTitle("Request alarm for "+formatted+"?").setMessage("Open your Clock app with this alarm request. The Clock app controls whether it creates or reuses an alarm; FocusPilot cannot verify creation.")
                .setNegativeButton("Cancel",(d,w) -> showStatus("Alarm request cancelled."))
                .setPositiveButton("Open Clock",(d,w) -> {
                    Intent intent=new Intent(AlarmClock.ACTION_SET_ALARM).putExtra(AlarmClock.EXTRA_HOUR,command.hour).putExtra(AlarmClock.EXTRA_MINUTES,command.minute).putExtra(AlarmClock.EXTRA_MESSAGE,"FocusPilot task").putExtra(AlarmClock.EXTRA_SKIP_UI,false);
                    try { startActivity(intent); log("Alarm request handed to Clock: "+formatted+" · outcome unverified"); }
                    catch(ActivityNotFoundException error) { showStatus("No compatible Clock app found."); }
                }).show();
        } else showStatus("Try “start focus”, “pause”, or “alarm 7:30 pm”. Unknown commands are not executed.");
    }
    private void microphone() {
        if(voiceDraft.active()) {
            if(voiceDraft.phase()==VoiceDraftState.Phase.LISTENING) voiceInput.finishListening();
            else { voiceInput.cancel(); showStatus("Voice cancelled. Type a request or tap again to retry."); }
            return;
        }
        if(!LocalVoiceInput.available(this)) { showStatus("On-device speech is unavailable. Type your command; no cloud fallback is used."); return; }
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED) { requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},11); return; }
        if(tts!=null) tts.stop();
        voiceInput.start();
    }
    @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] results) {
        super.onRequestPermissionsResult(requestCode,permissions,results);
        if(requestCode==11 && results.length>0 && results[0]==PackageManager.PERMISSION_GRANTED && visible) showStatus("Microphone permission granted. Tap Push to talk when you want to start a local draft.");
        else if(requestCode==11) showStatus("Microphone not allowed. Typed commands still work.");
        if(requestCode==12 && results.length>0 && results[0]==PackageManager.PERMISSION_GRANTED && visible) enableMonitor();
        else if(requestCode==12) showStatus("Notifications not allowed. Background monitor stays off; the dashboard still works.");
    }
    private void speak(String value) { if(voiceDraft.active()) { showStatus("Finish or cancel voice input before speaking a status."); return; } if(muted) { showStatus("Companion voice is muted. "+value); return; } if(offlineVoiceReady && tts!=null) tts.speak(value,TextToSpeech.QUEUE_FLUSH,null,"focuspilot-status"); else showStatus("Offline text-to-speech voice is not ready or installed. "+value); }
    private void showStatus(String value) { if(status!=null) status.setText(value); }
    private void log(String value) {
        repository.log(value); renderLogs();
    }
    private void renderLogs() { if(logView==null) return; StringBuilder output=new StringBuilder(); for(int i=repository.events.size()-1;i>=0;i--) output.append(repository.events.get(i)).append("\n\n"); logView.setText(repository.events.isEmpty() ? "No events yet · up to 30 summaries stored" : output.toString().trim()); }
    private void deleteData() {
        stopMonitor("Local data deleted; monitor stopped"); simulated=false; demoLedger.reset();
        observe=false; observeSwitch.setChecked(false); repository.delete();
        getSharedPreferences("focuspilot_fewshot_sandbox",MODE_PRIVATE).edit().clear().apply();
        monitoredPackage="com.instagram.android"; budgetMs=300_000; packageInput.setText(monitoredPackage); budgetInput.setText("5");
        goalInput.setText(""); plannedInput.setText(""); continuousInput.setText("");
        renderLogs(); refresh(); showStatus("Focus data and saved examples deleted. Model remains installed; observation off.");
    }
}
