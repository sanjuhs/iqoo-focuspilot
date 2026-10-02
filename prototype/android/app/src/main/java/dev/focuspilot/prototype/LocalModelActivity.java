package dev.focuspilot.prototype;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.AlarmClock;
import android.provider.Settings;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.EditText;
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

/** Actual app-process CPU inference and read-only activation observations. */
public final class LocalModelActivity extends Activity {
    private static final String SHA256="57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf";
    private static final long MODEL_BYTES=563036064L;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private volatile LocalModel model;
    private volatile boolean destroyed, busy;
    private volatile boolean foreground;
    private volatile long requestEpoch;
    private LinearLayout root;
    private TextView state,result,activationView;
    private EditText command;
    private Switch capture;
    private Button load,infer,review;
    private String lastOriginal,lastIntent;
    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density*value); }
    private TextView label(String value,int size) { TextView view=new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(Color.rgb(242,236,249)); view.setPadding(0,dp(10),0,dp(10)); root.addView(view); return view; }
    private Button button(String value,View.OnClickListener action) { Button view=new Button(this); view.setText(value); view.setAllCaps(false); root.addView(view,new LinearLayout.LayoutParams(-1,dp(56))); view.setOnClickListener(action); return view; }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        ScrollView scroll=new ScrollView(this); scroll.setBackgroundColor(Color.rgb(26,23,36)); root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(24),dp(18),dp(24),dp(24)); scroll.addView(root);
        scroll.setOnApplyWindowInsetsListener((view,insets)-> {
            if(Build.VERSION.SDK_INT>=30) { android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout()); view.setPadding(bars.left,bars.top,bars.right,bars.bottom); }
            else view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        label("MIRA · LOCAL MODEL LAB",24);
        label("PRE-EVENT RESEARCH · Qwen3.5-0.8B Q4_0 · llama.cpp CPU. Outputs are proposals. No NPU or causal interpretation claim.",14);
        state=label("Model not loaded. A bundled APK can import its pinned model once into private storage. A light APK requires a prepared private model. No downloads or provider keys.",16);
        load=button("Load verified local model",v->load());
        command=new EditText(this); command.setText("Please start a focus session"); command.setTextColor(Color.WHITE); command.setHintTextColor(Color.LTGRAY); command.setSingleLine(false); command.setMaxLines(3); root.addView(command);
        capture=new Switch(this); capture.setText("Capture selected actual activation summaries"); capture.setTextColor(Color.WHITE); root.addView(capture);
        infer=button("Understand command locally",v->infer()); infer.setEnabled(false);
        button("Cancel inference",v->cancelRequest());
        result=label("No command has been evaluated.",16);
        review=button("Review proposed phone action",v->review()); review.setEnabled(false);
        activationView=label("Activation capture is opt-in and observational. No tensors have been captured. It can add latency.",13);
        button("Close model and return",v->finish());
        setContentView(scroll); scroll.requestApplyInsets();
    }
    private void post(Runnable action) { main.post(()->{ if(!destroyed) action.run(); }); }
    private void setBusy(boolean value) { busy=value; load.setEnabled(!value && model==null); infer.setEnabled(!value && model!=null); command.setEnabled(!value); capture.setEnabled(!value); }
    private void load() {
        if(busy || model!=null) return;
        File file=new File(getFilesDir(),"qwen35.gguf");
        final long epoch=++requestEpoch;
        setBusy(true); state.setText("Preparing verified 537 MiB local artifact and loading CPU model… First bundled import can take time; this runs on a worker.");
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
                post(()->{setBusy(false); state.setText(String.format(Locale.US,"LOCAL MODEL LOADED · PRE-EVENT RESEARCH\nQwen3.5-0.8B · Q4_0 · CPU only · context 1024 · 4 threads\n%s\nPrivate-file hash %.0f ms · native load %.0f ms\nNo NPU, cloud or Office Kit backend.",imported?String.format(Locale.US,"Bundled import + SHA verification %.0f ms; copied once into private storage",importMs):"Using existing private model; SHA verified",verifyMs,loadMs));});
            } catch(Throwable error) { post(()->{setBusy(false); state.setText("Load failed: "+safe(error));}); }
        });
    }
    private void infer() {
        if(busy || model==null || !foreground) return;
        final String original=command.getText().toString(); final boolean observe=capture.isChecked();
        if(original.trim().isEmpty() || original.length()>500) { result.setText("Use 1–500 characters."); return; }
        final LocalModel current=model;
        // Preparation happens before submission, so onStop/Cancel cannot be undone by
        // a queued task entering native inference later.
        try { current.prepareGeneration(); }
        catch(RuntimeException error) { result.setText("Could not prepare inference: "+safe(error)); return; }
        final long epoch=++requestEpoch;
        setBusy(true); review.setEnabled(false); lastIntent=null; lastOriginal=null; result.setText("Evaluating locally… Fresh recurrent/attention state for this request.");
        worker.execute(()->{
            try {
                if(!foreground || destroyed || epoch!=requestEpoch) throw new IllegalStateException("Generation cancelled before worker start");
                String raw=current.generatePreparedIntent(original,observe); JSONObject envelope=new JSONObject(raw);
                JSONObject prediction=new JSONObject(envelope.getString("text")); String intent=prediction.getString("intent");
                JSONObject metrics=envelope.getJSONObject("metrics"); JSONArray activations=envelope.getJSONArray("activations");
                if(!metrics.getBoolean("reached_eos")) throw new IllegalStateException("Generation did not complete; no action proposal accepted.");
                ModelCommandGate.Proposal proposal=ModelCommandGate.validate(intent,original);
                String display=String.format(Locale.US,"Model proposal: %s\nIndependent gate: %s\n%s\nCPU total %.0f ms · prefill %.0f ms · decode %.0f ms\nContext setup %.0f ms (reported separately)\n%d prompt tokens · %d generated tokens · capture %s\nNothing executed yet.",intent,proposal.executable()?"REVIEW REQUIRED":"ABSTAIN",proposal.preview,metrics.getDouble("total_ms"),metrics.getDouble("prefill_ms"),metrics.getDouble("decode_ms"),metrics.optDouble("context_setup_ms",0),metrics.getInt("prompt_tokens"),metrics.getInt("generated_tokens"),observe?"on":"off");
                StringBuilder trace=new StringBuilder(observe?"ACTUAL PREFILL TENSOR OBSERVATIONS\nLatest chunk/last position; first 8 values plus vector summary. Association only; no ablation/patching.\n":"Capture disabled; no activation observations.\n");
                for(int i=0;i<activations.length();i++) { JSONObject event=activations.getJSONObject(i); trace.append(String.format(Locale.US,"\n%s · width %d · chunk positions %d\nmean %.5f · RMS %.5f · range %.5f…%.5f\nfirst values %s\n",event.getString("tensor"),event.getInt("width"),event.getInt("positions_in_chunk"),event.getDouble("mean"),event.getDouble("rms"),event.getDouble("min"),event.getDouble("max"),event.getJSONArray("first_values").toString())); }
                if(observe && activations.length()==0) trace.append("No selected tensors observed; do not claim capture succeeded.");
                post(()->{setBusy(false);
                    if(!foreground || epoch!=requestEpoch) { review.setEnabled(false); result.setText("Request cancelled or screen left. Evaluate again before reviewing an action."); return; }
                    lastIntent=intent; lastOriginal=original; result.setText(display); activationView.setText(trace.toString()); review.setEnabled(proposal.executable());});
            } catch(Throwable error) { post(()->{setBusy(false); review.setEnabled(false); result.setText("Inference failed/cancelled: "+safe(error)+"\nNo action executed.");}); }
        });
    }
    private void review() {
        if(lastIntent==null || lastOriginal==null || busy || !foreground) return;
        if(!lastOriginal.equals(command.getText().toString())) { review.setEnabled(false); result.setText("Command changed. Evaluate it again before review."); return; }
        ModelCommandGate.Proposal proposal=ModelCommandGate.validate(lastIntent,lastOriginal);
        if(!proposal.executable()) return;
        final long epoch=requestEpoch;
        new AlertDialog.Builder(this).setTitle("Review local model proposal").setMessage("Your request: "+lastOriginal+"\n\n"+proposal.preview+"\n\nThe small model can misclassify. Confirm only if this is the action you want.")
            .setNegativeButton("Cancel",null).setPositiveButton("Confirm action",(dialog,which)->{
                if(!foreground || epoch!=requestEpoch || lastOriginal==null || !lastOriginal.equals(command.getText().toString())) {
                    result.setText("Request changed or screen left. Evaluate again before confirming an action."); return;
                }
                execute(proposal);
            }).show();
    }
    private void execute(ModelCommandGate.Proposal proposal) {
        review.setEnabled(false);
        try {
            FocusRepository repository=FocusRepository.get(this);
            switch(proposal.kind) {
                case START_FOCUS: repository.start(); result.setText("Focus state is now active. No background monitor was enabled by this action."); break;
                case PAUSE_FOCUS: stopService(new Intent(this,FocusMonitorService.class)); repository.pause("User confirmed pause from local model proposal"); result.setText("Focus paused; foreground monitor stop requested."); break;
                case ALARM: startActivity(new Intent(AlarmClock.ACTION_SET_ALARM).putExtra(AlarmClock.EXTRA_HOUR,proposal.hour).putExtra(AlarmClock.EXTRA_MINUTES,proposal.minute).putExtra(AlarmClock.EXTRA_SKIP_UI,false).putExtra(AlarmClock.EXTRA_MESSAGE,"FocusPilot research test")); result.setText("Clock request launched; actual alarm creation remains unverified."); break;
                case TIMER: startActivity(new Intent(AlarmClock.ACTION_SET_TIMER).putExtra(AlarmClock.EXTRA_LENGTH,proposal.seconds).putExtra(AlarmClock.EXTRA_SKIP_UI,false)); result.setText("Timer request launched; verify the result in Clock."); break;
                case OPEN_SETTINGS: startActivity(new Intent(Settings.ACTION_SETTINGS)); result.setText("Settings launch requested; outcome is verified separately."); break;
                case OPEN_CALCULATOR: startActivity(Intent.makeMainSelectorActivity(Intent.ACTION_MAIN,Intent.CATEGORY_APP_CALCULATOR)); result.setText("Calculator launch requested; outcome is verified separately."); break;
                case OPEN_CLOCK: startActivity(new Intent(AlarmClock.ACTION_SHOW_ALARMS)); result.setText("Clock launch requested; outcome is verified separately."); break;
                case EXPLAIN: result.setText(String.format(Locale.US,"Focus %s · selected app %s · %.1f / %d minutes · %d virtual points. Main dashboard shows policy contributions; the separate Decision Lab explains the synthetic trained network.",repository.session.isActive()?"active":"paused",repository.selectedPackage,repository.usage()/60000.0,repository.budgetMs/60000,repository.ledger.points())); break;
                default: result.setText("Unsupported action. Nothing executed.");
            }
        } catch(RuntimeException error) { result.setText("Android action unavailable: "+safe(error)); }
    }
    private static String safe(Throwable error) { String message=error.getMessage(); return message==null?error.getClass().getSimpleName():message; }
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
    private void cancelRequest() { requestEpoch++; lastIntent=null; lastOriginal=null; if(review!=null) review.setEnabled(false); LocalModel current=model; if(current!=null) { try { current.cancel(); } catch(RuntimeException ignored) {} } }
    @Override protected void onResume() { super.onResume(); foreground=true; }
    @Override protected void onStop() { foreground=false; cancelRequest(); super.onStop(); }
    @Override protected void onDestroy() { destroyed=true; main.removeCallbacksAndMessages(null); LocalModel current=model; if(current!=null) { try { current.cancel(); } catch(RuntimeException ignored) {} } worker.execute(()->{LocalModel loaded=model; model=null; if(loaded!=null) loaded.close();}); worker.shutdown(); super.onDestroy(); }
}
