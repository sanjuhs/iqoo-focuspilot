package dev.focuspilot.prototype;

import android.app.Activity;
import android.Manifest;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.AlarmClock;
import android.provider.Settings;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Staged fast local proposals and explicit Qwen CPU fallback; never automatic actions. */
public final class LocalModelActivity extends Activity {
    private static final String SAVED_COMMAND_DRAFT="mira.editableCommandDraft", SAVED_DRAFT_DISCARDED="mira.discardedInvalidEdit";
    private static final String SHA256="57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf";
    private static final long MODEL_BYTES=563036064L;
    private static final int VOICE_PERMISSION=731;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private volatile LocalModel model;
    private volatile boolean destroyed, busy;
    private volatile boolean foreground;
    private volatile long requestEpoch;
    private LinearLayout root;
    private TextView state,result,activationView,modelStatus,responseDetails;
    private LinearLayout diagnostics;
    private final java.util.List<Button> examples=new java.util.ArrayList<>();
    private EditText command;
    private Switch capture;
    private Button load,infer,review,cancelInference;
    private final CompatibleReviewState pendingReview=new CompatibleReviewState();
    private AlertDialog reviewDialog;
    private long busyEpoch;
    private final VoiceDraftState voiceDraft=new VoiceDraftState();
    private LocalVoiceInput voice;
    private SharedPreferences companionPrefs;
    private CompanionView companion;
    private TextView companionMessage,voiceStatus;
    private Button speak,finishVoice,cancelVoice,readback,stopSpeaking;
    private TextToSpeech tts;
    private boolean offlineReadbackReady;
    private final ReadbackState readbackState=new ReadbackState();
    private final ReadbackInitialization readbackInitialization=new ReadbackInitialization();
    private String confirmedFocusText;
    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density*value); }
    private TextView label(String value,int size) { TextView view=new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(Color.rgb(242,236,249)); view.setPadding(0,dp(10),0,dp(10)); root.addView(view); return view; }
    private Button button(String value,View.OnClickListener action) {
        Button view=new Button(this);view.setText(value);view.setAllCaps(false);view.setTextSize(14);
        view.setTypeface(android.graphics.Typeface.DEFAULT,android.graphics.Typeface.BOLD);
        boolean primary=value.equals("Understand command locally")||value.equals("Review proposed phone action");
        view.setTextColor(primary?Color.rgb(22,20,31):Color.rgb(203,171,238));
        android.graphics.drawable.GradientDrawable shape=new android.graphics.drawable.GradientDrawable();
        shape.setColor(primary?Color.rgb(203,171,238):Color.rgb(29,58,62));shape.setCornerRadius(dp(14));view.setBackground(shape);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(52));params.topMargin=dp(8);root.addView(view,params);
        view.setOnClickListener(action);return view;
    }
    /** Examples only replace the editable draft; the existing watcher invalidates old reviews. */
    private void example(LinearLayout row,String title,String draft) {
        Button view=new Button(this);view.setText(title);view.setAllCaps(false);
        view.setTextColor(Color.rgb(203,171,238));view.setTextSize(13);
        view.setContentDescription("Edit request to "+draft+". No command runs.");
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-2,dp(48));params.rightMargin=dp(8);
        row.addView(view,params);examples.add(view);
        view.setOnClickListener(v->{
            if(!foreground||destroyed||busy||readbackState.active()||voiceDraft.active())return;
            command.setText(draft);command.setSelection(command.length());
        });
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        String initialDraft=null;
        String draftNotice=null;
        try {
            initialDraft=CommandDraftHandoff.initialDraft(saved==null?getIntent().getStringExtra(CommandDraftHandoff.EXTRA_DRAFT):null,
                saved==null?null:saved.getString(SAVED_COMMAND_DRAFT),saved!=null);
            if(saved!=null)draftNotice=saved.getBoolean(SAVED_DRAFT_DISCARDED,false)?"An invalid or overlong edit was discarded whole. Enter a fresh draft; nothing executed.":"Your editable draft was restored. Tap Understand command locally when ready; no proposal or action review was restored.";
            else if(initialDraft!=null)draftNotice="Draft received for editing only. Review these words, then tap Understand command locally. Nothing recorded, inferred or executed automatically.";
        } catch(RuntimeException invalid) {
            initialDraft="";draftNotice="The incoming draft was invalid or over 500 characters and was not imported. Type a fresh request; nothing executed.";
        }
        ScrollView scroll=new ScrollView(this); scroll.setBackgroundColor(Color.rgb(26,23,36)); root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(24),dp(18),dp(24),dp(24)); scroll.addView(root);
        scroll.setOnApplyWindowInsetsListener((view,insets)-> {
            if(Build.VERSION.SDK_INT>=30) { android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout()); view.setPadding(bars.left,bars.top,bars.right,bars.bottom); }
            else view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        label("Ask Mira",24);
        label("PRE-EVENT RESEARCH",12);
        companionPrefs=getSharedPreferences("focuspilot_research",MODE_PRIVATE);
        companion=new CompanionView(this);root.addView(companion,new LinearLayout.LayoutParams(-1,dp(120)));
        companionMessage=label("Ready when you are. One small task, reviewed together.",17);
        command=new EditText(this); command.setText(initialDraft==null?"":initialDraft); command.setSaveEnabled(false); command.setTextColor(Color.WHITE); command.setHintTextColor(Color.LTGRAY); command.setSingleLine(false); command.setMaxLines(3); root.addView(command);
        command.setPadding(dp(12),dp(10),dp(12),dp(10));
        android.graphics.drawable.GradientDrawable draftShape=new android.graphics.drawable.GradientDrawable();
        draftShape.setColor(Color.rgb(36,32,49));draftShape.setCornerRadius(dp(12));command.setBackground(draftShape);
        command.setContentDescription("Editable command draft. Review voice transcription here before pressing Understand.");
        command.setHint("Start focus, set a timer, or open an app");
        HorizontalScrollView suggestions=new HorizontalScrollView(this);suggestions.setHorizontalScrollBarEnabled(false);
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);suggestions.addView(row);root.addView(suggestions);
        example(row,"Focus 25 min","Start focus for 25 minutes");
        example(row,"Timer 5 min","Set a five-minute timer");
        example(row,"Pause focus","Stop focus");
        label("Examples fill your draft. Understand creates a proposal; Review lets you confirm it.",13);
        voiceStatus=label("Type a request or speak using an installed on-device speech service.",14);
        speak=button("Speak to Mira · on-device",v->requestVoice());
        finishVoice=button("Finish voice draft",v->{if(voice!=null)voice.finishListening();});
        cancelVoice=button("Cancel voice",v->{if(voice!=null)voice.cancel();voiceStatus.setText("Voice cancelled. Your existing draft stays editable.");});
        infer=button("Understand command locally",v->infer()); infer.setEnabled(false);
        cancelInference=button("Cancel inference",v->{cancelRequest();if(voice!=null)voice.cancel();stopReadback();result.setText("Request cancelled. Nothing executed.");updateControls();});
        result=label("Your next small step starts here.",16);
        if(draftNotice!=null)result.setText(draftNotice);
        review=button("Review proposed phone action",v->review()); review.setEnabled(false);
        readback=button("Read confirmed focus status",v->readConfirmedFocus());readback.setEnabled(false);
        stopSpeaking=button("Stop readback",v->{stopReadback();voiceStatus.setText("Readback stopped. Your confirmed status remains on screen.");});
        modelStatus=label("Quick commands are ready · Qwen is not loaded",14);
        load=button("Load verified local model",v->load());
        label("For a request quick checks cannot understand, load Qwen on this phone and tap Understand again. Loading does not run your draft.",13);
        button("Model & activation details",v->{
            boolean open=diagnostics.getVisibility()!=View.VISIBLE;
            diagnostics.setVisibility(open?View.VISIBLE:View.GONE);
            ((Button)v).setText(open?"Hide model & activation details":"Model & activation details");
        });
        diagnostics=new LinearLayout(this);diagnostics.setOrientation(LinearLayout.VERTICAL);root.addView(diagnostics);
        state=new TextView(this);state.setTextSize(14);state.setTextColor(Color.rgb(242,236,249));
        state.setText("Fast local checks are ready without a model. Optional Qwen3.5-0.8B Q4_0 uses CPU. No NPU or causal interpretation result is established.");diagnostics.addView(state);
        responseDetails=new TextView(this);responseDetails.setTextSize(13);responseDetails.setTextColor(Color.rgb(242,236,249));
        responseDetails.setText("No Qwen response recorded for this draft.");diagnostics.addView(responseDetails);
        capture=new Switch(this);capture.setText("Capture actual Qwen activation summaries");capture.setTextColor(Color.WHITE);diagnostics.addView(capture);
        activationView=new TextView(this);activationView.setTextSize(13);activationView.setTextColor(Color.rgb(242,236,249));
        activationView.setText("Activation capture is opt-in and observational. No tensors have been captured. It can add latency.");diagnostics.addView(activationView);
        diagnostics.setVisibility(View.GONE);
        button("Close model and return",v->finish());
        voice=new LocalVoiceInput(this,voiceDraft,new LocalVoiceInput.Listener(){
            @Override public void onStatus(String message){if(!destroyed)voiceStatus.setText(message);}
            @Override public void onDraft(String text){if(!destroyed&&foreground){cancelRequest();command.setText(text);result.setText("Voice draft only. Review it above, then tap Understand command locally. Nothing executed.");}}
            @Override public void onChanged(){if(!destroyed)updateControls();}
        });
        command.addTextChangedListener(new TextWatcher(){
            @Override public void beforeTextChanged(CharSequence text,int start,int count,int after){}
            @Override public void onTextChanged(CharSequence text,int start,int before,int count){}
            @Override public void afterTextChanged(Editable text){
                if(destroyed)return;
                cancelRequest();stopReadback();
                result.setText("Draft changed. Tap Understand again before reviewing an action.");
                updateControls();
            }
        });
        updateControls();
        setContentView(scroll); scroll.requestApplyInsets();
    }
    private void post(Runnable action) { main.post(()->{ if(!destroyed) action.run(); }); }
    private void setBusy(boolean value) {
        busy=value;voiceDraft.setModelBusy(value);
        if(value){if(voice!=null)voice.cancel();stopReadback();}
        updateControls();
    }
    private void beginWork(long epoch){busyEpoch=epoch;setBusy(true);}
    /** An old worker may release its own busy flag, but cannot replace newer UI state. */
    private boolean finishWork(long epoch){
        if(busyEpoch!=epoch)return false;
        busyEpoch=0;setBusy(false);
        return !destroyed&&foreground&&epoch==requestEpoch;
    }
    private boolean reviewIdle(){return !destroyed&&!busy&&!readbackState.active()&&voiceDraft.canUnderstand();}
    private void updateControls(){
        boolean recording=voiceDraft.active();
        if(load==null)return;
        load.setEnabled(foreground&&!destroyed&&!busy&&!recording&&!readbackState.active()&&model==null);
        infer.setEnabled(foreground&&!destroyed&&!busy&&!readbackState.active()&&voiceDraft.canUnderstand());
        command.setEnabled(!busy&&!recording&&!readbackState.active());capture.setEnabled(!busy&&!recording&&!readbackState.active());
        speak.setEnabled(foreground&&!busy&&!recording&&!readbackState.active());
        finishVoice.setEnabled(foreground&&voiceDraft.phase()==VoiceDraftState.Phase.LISTENING);
        cancelVoice.setEnabled(recording);
        finishVoice.setVisibility(recording?View.VISIBLE:View.GONE);
        cancelVoice.setVisibility(recording?View.VISIBLE:View.GONE);
        cancelInference.setVisibility(busy?View.VISIBLE:View.GONE);
        for(Button example:examples)example.setEnabled(foreground&&!destroyed&&!busy&&!recording&&!readbackState.active());
        readback.setEnabled(foreground&&!busy&&!recording&&!readbackState.active()&&confirmedFocusText!=null);
        review.setEnabled(pendingReview.owns(pendingReview.snapshot(),requestEpoch,command.getText().toString(),foreground,reviewIdle()));
        review.setVisibility(review.isEnabled()?View.VISIBLE:View.GONE);
        readback.setVisibility(confirmedFocusText!=null?View.VISIBLE:View.GONE);
        stopSpeaking.setEnabled(foreground&&!destroyed&&readbackState.active());
        stopSpeaking.setVisibility(readbackState.active()?View.VISIBLE:View.GONE);
        modelStatus.setText(model!=null?"Qwen3.5-0.8B Q4_0 loaded · CPU on this phone":busy?"Preparing Qwen on this phone…":"Quick commands are ready · Qwen is not loaded");
        for(int i=0;i<root.getChildCount();i++) if(root.getChildAt(i) instanceof Button) root.getChildAt(i).setAlpha(root.getChildAt(i).isEnabled()?1f:0.45f);
        companion.setReduceMotion(companionPrefs.getBoolean("reduceMotion",false));
        companion.setVisibility(companionPrefs.getBoolean("hideCompanion",false)?View.GONE:View.VISIBLE);
        companion.setState(!foreground?CompanionView.State.PAUSED:recording?CompanionView.State.LISTEN:busy?CompanionView.State.FOCUS:CompanionView.State.IDLE);
        companionMessage.setText(recording?"I'm listening locally. Your words become a draft for you to review.":busy?"One moment. I'm thinking on your phone.":"Ready when you are. One small task, reviewed together.");
    }
    private void requestVoice(){
        if(!foreground||destroyed||busy||readbackState.active()||voiceDraft.active())return;
        cancelRequest();
        if(!LocalVoiceInput.available(this)){voiceStatus.setText("On-device speech is unavailable here. Type your command; no cloud fallback is used.");return;}
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            voiceStatus.setText("Android will ask for microphone access. This is optional; typing works without it.");
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},VOICE_PERMISSION);return;
        }
        voice.start();
    }
    @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] grants){
        super.onRequestPermissionsResult(requestCode,permissions,grants);
        if(requestCode!=VOICE_PERMISSION||destroyed||!foreground)return;
        voiceStatus.setText(grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED?
            "Microphone permission granted. Tap Speak to Mira when you want to start a local draft.":
            "Microphone permission denied. Voice stays off; type your command instead.");
        updateControls();
    }
    private void load() {
        if(!foreground || destroyed || busy || model!=null || voiceDraft.active() || readbackState.active()) return;
        File file=new File(getFilesDir(),"qwen35.gguf");
        cancelRequest();
        final long epoch=requestEpoch;
        beginWork(epoch); state.setText("Preparing verified 537 MiB local artifact and loading CPU model… First bundled import can take time; this runs on a worker.");
        worker.execute(()->{
            long began=System.nanoTime();
            try {
                ensureLoadActive(epoch);
                boolean imported=importBundledIfMissing(file,epoch);
                long importedAt=System.nanoTime();
                if(file.length()!=MODEL_BYTES) throw new IllegalStateException("Model file size does not match pinned artifact.");
                // A streamed import already verified the full artifact before publication.
                // Existing private files are independently rehashed on every load.
                if(!imported && !SHA256.equals(hash(file,epoch))) throw new IllegalStateException("Model SHA-256 differs; refusing load.");
                ensureLoadActive(epoch);
                long verified=System.nanoTime(); LocalModel loaded=new LocalModel(file.getAbsolutePath());
                if(destroyed || !foreground || epoch!=requestEpoch) { loaded.close(); throw new IllegalStateException("Model preparation cancelled"); }
                model=loaded; double verifyMs=(verified-importedAt)/1e6, importMs=(importedAt-began)/1e6, loadMs=(System.nanoTime()-verified)/1e6;
                post(()->{if(!finishWork(epoch))return; state.setText(String.format(Locale.US,"LOCAL MODEL LOADED · PRE-EVENT RESEARCH\nQwen3.5-0.8B · Q4_0 · CPU only · context 1024 · 4 threads\n%s\nPrivate-file hash %.0f ms · native load %.0f ms\nNo NPU, cloud or Office Kit backend.",imported?String.format(Locale.US,"Bundled import + SHA verification %.0f ms; copied once into private storage",importMs):"Using existing private model; SHA verified",verifyMs,loadMs));});
            } catch(Throwable error) { post(()->{if(!finishWork(epoch))return; state.setText("Load failed: "+safe(error));result.setText("Qwen could not load. Quick commands still work. Open model details for the reason.");}); }
        });
    }
    private void infer() {
        if(busy || destroyed || !foreground || !voiceDraft.canUnderstand() || readbackState.active()) return;
        final String original=command.getText().toString(); final boolean observe=capture.isChecked();
        clearProposal();
        final long epoch=++requestEpoch;
        if(original.trim().isEmpty() || original.length()>500) { result.setText("Use 1–500 characters.");updateControls();return; }
        final CompatibleActionRouter.Result fast=CompatibleActionRouter.recognize(original);
        if(fast.proposal.executable()) {
            if(pendingReview.offer(epoch,original,null,fast.origin)) {
                result.setText("FAST LOCAL · complete request checked\nREVIEW REQUIRED\n"+fast.proposal.preview+"\nNo Qwen inference ran. Nothing executed yet.");
                activationView.setText("Fast local proposal. No model inference or activation capture occurred.");
            }
            updateControls();return;
        }
        final LocalModel current=model;
        if(current==null) {
            result.setText("Fast local checks could not verify this request. Manually load the verified Qwen model, then tap Understand again to request one inference. Nothing executed.");
            activationView.setText("No model inference ran. No activations are retained.");
            updateControls();return;
        }
        // Preparation precedes submission: Cancel/onStop cannot be undone by a queued worker.
        try { current.prepareGeneration(); }
        catch(RuntimeException error) { result.setText("Could not prepare Qwen inference: "+safe(error));updateControls();return; }
        beginWork(epoch);
        result.setText("QWEN CPU · explicit fallback for this Understand request… Fresh recurrent/attention state.");
        worker.execute(()->{
            try {
                if(!foreground || destroyed || epoch!=requestEpoch) throw new IllegalStateException("Generation cancelled before worker start");
                String raw=current.generatePreparedUnitCommand(original,observe); JSONObject envelope=new JSONObject(raw);
                final String response=envelope.getString("text");
                JSONObject metrics=envelope.getJSONObject("metrics"); JSONArray activations=envelope.getJSONArray("activations");
                if(!metrics.getBoolean("reached_eos")) throw new IllegalStateException("Generation did not complete; no action proposal accepted.");
                final CompatibleActionRouter.Result checked=CompatibleActionRouter.validate(original,response);
                String display=String.format(Locale.US,"QWEN CPU · model response %s\nIndependent full-slot gate: %s\n%s\nCPU total %.0f ms · prefill %.0f ms · decode %.0f ms\nContext setup %.0f ms (reported separately)\n%d prompt tokens · %d generated tokens · capture %s\nNothing executed yet.",response,checked.proposal.executable()?"REVIEW REQUIRED":"ABSTAIN",checked.proposal.preview,metrics.getDouble("total_ms"),metrics.getDouble("prefill_ms"),metrics.getDouble("decode_ms"),metrics.optDouble("context_setup_ms",0),metrics.getInt("prompt_tokens"),metrics.getInt("generated_tokens"),observe?"on":"off");
                StringBuilder trace=new StringBuilder(observe?"ACTUAL QWEN PREFILL TENSOR OBSERVATIONS\nLatest chunk/last position; first 8 values plus vector summary. Association only; no ablation/patching.\n":"Qwen capture disabled; no activation observations.\n");
                for(int i=0;i<activations.length();i++) { JSONObject event=activations.getJSONObject(i); trace.append(String.format(Locale.US,"\n%s · width %d · chunk positions %d\nmean %.5f · RMS %.5f · range %.5f…%.5f\nfirst values %s\n",event.getString("tensor"),event.getInt("width"),event.getInt("positions_in_chunk"),event.getDouble("mean"),event.getDouble("rms"),event.getDouble("min"),event.getDouble("max"),event.getJSONArray("first_values").toString())); }
                if(observe && activations.length()==0) trace.append("No selected tensors observed; do not claim capture succeeded.");
                post(()->{
                    if(!finishWork(epoch))return;
                    if(!original.equals(command.getText().toString())){clearProposal();updateControls();return;}
                    result.setText((checked.proposal.executable()?"Qwen + safety check · review your next step":"Safety check needs a clearer request")+"\n"+checked.proposal.preview+"\nNothing executed yet.");
                    responseDetails.setText(display);
                    if(checked.proposal.executable()&&pendingReview.offer(epoch,original,response,checked.origin))
                        activationView.setText(trace.toString());
                    else {pendingReview.clear();activationView.setText("The safety check refused this proposal. No retained activation display or executable proposal.");}
                    updateControls();
                });
            } catch(Throwable error) { post(()->{
                if(!finishWork(epoch))return;
                clearProposal();result.setText("Qwen inference failed/cancelled: "+safe(error)+"\nNo action executed.");updateControls();
            }); }
        });
    }
    private void review() {
        final CompatibleReviewState.Snapshot snapshot=pendingReview.snapshot();
        CompatibleActionRouter.Result checked=pendingReview.review(snapshot,requestEpoch,command.getText().toString(),foreground,reviewIdle());
        if(!checked.proposal.executable())return;
        String title=CompatibleUnitCommand.FAST_LOCAL_REQUEST.equals(snapshot.origin())?"Review fast local proposal":"Review Qwen proposal";
        reviewDialog=new AlertDialog.Builder(this).setTitle(title)
            .setMessage("Your request: "+snapshot.original()+"\n\n"+checked.proposal.preview+"\n\nConfirm only if this is the action you want. Nothing has executed yet.")
            .setNegativeButton("Cancel",(dialog,which)->{cancelRequest();result.setText("Proposal cancelled. Nothing executed.");updateControls();})
            .setOnCancelListener(dialog->{cancelRequest();result.setText("Proposal cancelled. Nothing executed.");updateControls();})
            .setPositiveButton("Confirm action",(dialog,which)->{
                CompatibleActionRouter.Result confirmed=pendingReview.consume(snapshot,requestEpoch,command.getText().toString(),foreground,reviewIdle());
                reviewDialog=null;
                if(!confirmed.proposal.executable()) {
                    result.setText("Request changed, audio started or screen left. Understand again before confirming an action.");updateControls();return;
                }
                requestEpoch++;
                execute(confirmed.proposal);
            }).create();
        reviewDialog.show();
    }
    private void execute(ModelCommandGate.Proposal proposal) {
        review.setEnabled(false);
        try {
            FocusRepository repository=FocusRepository.get(this);
            switch(proposal.kind) {
                case START_FOCUS:
                    if(proposal.seconds>0) repository.startTimed(proposal.seconds*1000L); else repository.start();
                    result.setText(proposal.seconds>0?"Timed focus is active for "+proposal.seconds+" seconds. It pauses at the countdown deadline while the app process can run. No background monitor was enabled.":repository.session.isTimed()?"Your paused focus countdown has resumed. No background monitor was enabled.":"Focus state is now active. No background monitor was enabled by this action.");
                    confirmedFocusText=proposal.seconds>0?"You confirmed timed focus for "+proposal.seconds+" seconds. One gentle step at a time.":"You confirmed a focus session. One gentle step at a time.";break;
                case PAUSE_FOCUS: stopService(new Intent(this,FocusMonitorService.class)); repository.pause("User confirmed pause from reviewed command"); result.setText("Focus paused; foreground monitor stop requested.");confirmedFocusText="You confirmed a pause. Take a gentle breath.";break;
                case ALARM: startActivity(new Intent(AlarmClock.ACTION_SET_ALARM).putExtra(AlarmClock.EXTRA_HOUR,proposal.hour).putExtra(AlarmClock.EXTRA_MINUTES,proposal.minute).putExtra(AlarmClock.EXTRA_SKIP_UI,false).putExtra(AlarmClock.EXTRA_MESSAGE,"FocusPilot research test")); result.setText("Clock request launched; actual alarm creation remains unverified."); break;
                case TIMER: startActivity(new Intent(AlarmClock.ACTION_SET_TIMER).putExtra(AlarmClock.EXTRA_LENGTH,proposal.seconds).putExtra(AlarmClock.EXTRA_SKIP_UI,false)); result.setText("Timer request launched; verify the result in Clock."); break;
                case OPEN_SETTINGS: startActivity(new Intent(Settings.ACTION_SETTINGS)); result.setText("Settings launch requested; outcome is verified separately."); break;
                case OPEN_CALCULATOR: startActivity(Intent.makeMainSelectorActivity(Intent.ACTION_MAIN,Intent.CATEGORY_APP_CALCULATOR)); result.setText("Calculator launch requested; outcome is verified separately."); break;
                case OPEN_CLOCK: startActivity(new Intent(AlarmClock.ACTION_SHOW_ALARMS)); result.setText("Clock launch requested; outcome is verified separately."); break;
                case EXPLAIN:
                    repository.completeTimedIfDue();
                    long now=android.os.SystemClock.elapsedRealtime();
                    long usage=repository.usage();
                    FocusStatusSummary.Snapshot snapshot=new FocusStatusSummary.Snapshot(
                        repository.session.isActive(),repository.session.isCompleted(),repository.interrupted,
                        repository.session.elapsed(now),repository.session.remainingMs(now),repository.session.countdownTotalMs(),
                        usage<0?FocusStatusSummary.UNKNOWN:usage,repository.budgetMs,repository.ledger.points(),
                        repository.observe,FocusRepository.usageGranted(this));
                    String summary=FocusStatusSummary.format(snapshot);
                    result.setText(summary);
                    confirmedFocusText="At the time you reviewed this focus snapshot: "+summary;
                    break;
                default: result.setText("Unsupported action. Nothing executed.");
            }
            updateControls();
        } catch(RuntimeException error) { result.setText("Android action unavailable: "+safe(error)); }
    }
    private static String safe(Throwable error) { String message=error.getMessage(); return message==null?error.getClass().getSimpleName():message; }
    private void readConfirmedFocus(){
        if(!foreground||destroyed||busy||voiceDraft.active()||readbackState.active()||confirmedFocusText==null)return;
        if(companionPrefs.getBoolean("mute",false)){voiceStatus.setText("Companion voice is muted. Your confirmed status remains on screen.");return;}
        final long token=readbackState.beginWithUtterance("mira-confirmed-");
        if(token==0)return;
        updateControls();
        main.postDelayed(()->{
            if(readbackState.owns(token)){
                if(tts!=null){try{tts.stop();}catch(RuntimeException ignored){}}
                finishReadback(token,"Offline readback timed out. Nothing else is blocked; your status remains on screen.");
            }
        },20000);
        ReadbackInitialization.Admission admission=readbackInitialization.request(token);
        if(admission==ReadbackInitialization.Admission.SPEAK){speakConfirmed(token);return;}
        if(admission==ReadbackInitialization.Admission.REJECT){finishReadback(token,"Offline readback could not start. Your status remains on screen.");return;}
        voiceStatus.setText("Checking an installed offline companion voice…");
        if(admission==ReadbackInitialization.Admission.WAIT)return;
        final long engineEpoch=readbackInitialization.engineEpoch();
        // Initialization belongs to the engine, so a cancelled A can be replaced
        // by an explicit B. This separate bound also retires an engine that never responds.
        main.postDelayed(()->finishReadbackInitialization(engineEpoch,false,
            "Offline voice initialization timed out. Tap Read again for a new attempt."),20_000);
        try{
            tts=new TextToSpeech(this,code->post(()->finishReadbackInitialization(engineEpoch,
                code==TextToSpeech.SUCCESS,"No installed offline English TTS voice is ready. Nothing was spoken.")));
        }catch(RuntimeException error){finishReadbackInitialization(engineEpoch,false,
            "Offline readback could not start. Tap Read again for a new attempt.");}
    }
    private void finishReadbackInitialization(long engineEpoch,boolean initialized,String failureMessage){
        if(destroyed || !readbackInitialization.ownsInitialization(engineEpoch))return;
        boolean ready=false;
        if(initialized && tts!=null){
            try{
                if(tts.getVoices()!=null)for(Voice candidate:tts.getVoices()){
                    if(!candidate.isNetworkConnectionRequired()&&candidate.getLocale().getLanguage().equals("en")
                            &&tts.setVoice(candidate)==TextToSpeech.SUCCESS){ready=true;break;}
                }
            }catch(RuntimeException ignored){/* A failed engine can be retried only on a new explicit request. */}
        }
        offlineReadbackReady=ready;
        long waiting=readbackInitialization.complete(engineEpoch,ready);
        if(!ready){
            TextToSpeech failed=tts;tts=null;
            if(failed!=null){try{failed.shutdown();}catch(RuntimeException ignored){}}
        }
        if(waiting>0){
            if(ready)speakConfirmed(waiting);
            else finishReadback(waiting,failureMessage);
        }
    }
    private void speakConfirmed(long token){
        if(!readbackState.owns(token)||companionPrefs.getBoolean("mute",false)){
            finishReadback(token,"Readback stopped. Your status remains on screen.");return;
        }
        if(!offlineReadbackReady||tts==null){finishReadback(token,"No installed offline English TTS voice is ready. Nothing was spoken.");return;}
        try{
        if(tts.setOnUtteranceProgressListener(new UtteranceProgressListener(){
            @Override public void onStart(String id){}
            @Override public void onDone(String id){post(()->finishReadbackUtterance(token,id,"Confirmed focus status read with an installed offline voice."));}
            @Override public void onError(String id){post(()->finishReadbackUtterance(token,id,"Offline readback failed. The status remains on screen."));}
            @Override public void onStop(String id,boolean interrupted){post(()->finishReadbackUtterance(token,id,"Offline readback stopped. The status remains on screen."));}
        })==TextToSpeech.ERROR){
            finishReadback(token,"Offline readback could not register its listener. Your status remains on screen.");return;
        }
        if(tts.speak(confirmedFocusText,TextToSpeech.QUEUE_FLUSH,null,readbackState.utteranceId(token))==TextToSpeech.ERROR)
            finishReadback(token,"Offline readback could not start. The status remains on screen.");
        else voiceStatus.setText("Reading only the confirmed focus status. No microphone is active.");
        }catch(RuntimeException unavailable){finishReadback(token,"Offline readback is unavailable here. Your status remains on screen.");}
    }
    private void finishReadbackUtterance(long token,String id,String message){if(!readbackState.finishUtterance(token,id))return;voiceStatus.setText(message);updateControls();}
    private void finishReadback(long token,String message){if(!readbackState.finish(token))return;readbackInitialization.cancelRequest(token);voiceStatus.setText(message);updateControls();}
    private void stopReadback(){readbackState.cancel();readbackInitialization.cancelRequests();if(tts!=null){try{tts.stop();}catch(RuntimeException ignored){}}if(!destroyed)updateControls();}
    private void ensureLoadActive(long epoch) {
        if(destroyed || !foreground || epoch!=requestEpoch || Thread.currentThread().isInterrupted())
            throw new IllegalStateException("Model preparation cancelled");
    }
    /** Stream to a unique private temp file; publish only a complete checksummed asset. */
    private boolean importBundledIfMissing(File destination,long epoch) throws Exception {
        if(destination.exists()) return false; // Existing private files are never replaced by import.
        InputStream asset;
        try { asset=getAssets().open("qwen35.gguf",android.content.res.AssetManager.ACCESS_STREAMING); }
        catch(FileNotFoundException missing) { throw new IllegalStateException("No bundled model in this light APK. Install the bundled debug APK, or prepare the pinned qwen35.gguf in app-private files with scripts/prepare_phone.py."); }
        File temporary=null;
        try(InputStream source=asset) {
            ensureLoadActive(epoch);
            temporary=File.createTempFile("qwen35-import-",".tmp",getFilesDir());
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            long copied=0;byte[] buffer=new byte[1048576];
            try(FileOutputStream target=new FileOutputStream(temporary)) {
                int count;
                while((count=source.read(buffer))!=-1) {
                    ensureLoadActive(epoch);copied+=count;
                    if(copied>MODEL_BYTES) throw new IOException("Bundled model exceeds the pinned size; import refused.");
                    digest.update(buffer,0,count);target.write(buffer,0,count);
                }
                target.flush();target.getFD().sync();
            }
            if(copied!=MODEL_BYTES || !SHA256.equals(hex(digest.digest())))
                throw new IOException("Bundled model size or SHA-256 differs; import refused.");
            ensureLoadActive(epoch);
            if(destination.exists()) return false;
            Files.move(temporary.toPath(),destination.toPath(),StandardCopyOption.ATOMIC_MOVE);
            return true;
        } finally { if(temporary!=null && temporary.exists()) temporary.delete(); }
    }
    private String hash(File file,long epoch) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");byte[] bytes=new byte[1048576];
        try(FileInputStream stream=new FileInputStream(file)) { int count;while((count=stream.read(bytes))!=-1) {ensureLoadActive(epoch);digest.update(bytes,0,count);} }
        return hex(digest.digest());
    }
    private static String hex(byte[] digest) {StringBuilder out=new StringBuilder();for(byte value:digest)out.append(String.format(Locale.US,"%02x",value&255));return out.toString();}
    private void clearProposal(){
        pendingReview.clear();confirmedFocusText=null;
        if(reviewDialog!=null){reviewDialog.dismiss();reviewDialog=null;}
        if(review!=null)review.setEnabled(false);
        if(responseDetails!=null)responseDetails.setText("No Qwen response retained for this draft.");
        if(activationView!=null)activationView.setText("No retained activation observations. Only actual Qwen inference can capture tensors.");
    }
    private void cancelRequest() {
        requestEpoch++;clearProposal();
        LocalModel current=model;if(current!=null){try{current.cancel();}catch(RuntimeException ignored){}}
    }
    @Override protected void onSaveInstanceState(Bundle out) {
        String edited=command==null?"":command.getText().toString();
        boolean valid=CommandDraftHandoff.restorableEdit(edited);
        out.putString(SAVED_COMMAND_DRAFT,valid?edited:"");out.putBoolean(SAVED_DRAFT_DISCARDED,!valid);
        super.onSaveInstanceState(out);
    }
    @Override protected void onResume() { super.onResume(); foreground=true;voiceDraft.resume();readbackState.resume();updateControls(); }
    @Override protected void onStop() { foreground=false;readbackState.stop();voiceDraft.stop();if(voice!=null)voice.cancel();stopReadback();cancelRequest();updateControls();super.onStop(); }
    @Override protected void onDestroy() { destroyed=true;readbackState.close();readbackInitialization.close();cancelRequest();if(voice!=null)voice.close();stopReadback();if(tts!=null)tts.shutdown();main.removeCallbacksAndMessages(null); LocalModel current=model; if(current!=null) { try { current.cancel(); } catch(RuntimeException ignored) {} } worker.execute(()->{LocalModel loaded=model; model=null; if(loaded!=null) loaded.close();}); worker.shutdown(); super.onDestroy(); }
}
