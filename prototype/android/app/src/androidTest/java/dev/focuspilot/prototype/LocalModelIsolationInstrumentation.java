package dev.focuspilot.prototype;

import android.Manifest;
import android.app.Application;
import android.app.Instrumentation;
import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Debug;
import android.os.Process;
import android.os.SystemClock;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import java.io.File;
import java.io.FileInputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONArray;
import org.json.JSONObject;

/** Fixed synthetic JNI diagnostics in the target UID. No UI, actions or preferences. */
public final class LocalModelIsolationInstrumentation extends Instrumentation {
    private static final long MODEL_BYTES=563036064L;
    private static final String MODEL_SHA="57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf";
    private static final Pattern INTENT=Pattern.compile("\\{\"intent\":\"(start_focus|pause_focus|alarm|timer|open_app|explain|unknown)\"\\}");
    private static final String[] REQUESTS={
        "Start focus for 20 seconds", "Stop focus", "Set an alarm for 07:30",
        "Set a five-minute timer", "Open calculator", "Why did you nudge me",
        "Do not open settings", "Start focus and open settings", "Stop focus", "Stop focus"
    };
    private static final String[] EXPECTED_INTENTS={
        "start_focus","pause_focus","alarm","timer","open_app","explain","unknown","unknown","pause_focus","pause_focus"
    };
    private static final ModelCommandGate.Kind[] EXPECTED_KINDS={
        ModelCommandGate.Kind.START_FOCUS, ModelCommandGate.Kind.PAUSE_FOCUS,
        ModelCommandGate.Kind.ALARM, ModelCommandGate.Kind.TIMER,
        ModelCommandGate.Kind.OPEN_CALCULATOR, ModelCommandGate.Kind.EXPLAIN,
        ModelCommandGate.Kind.UNKNOWN, ModelCommandGate.Kind.UNKNOWN,
        ModelCommandGate.Kind.PAUSE_FOCUS, ModelCommandGate.Kind.PAUSE_FOCUS
    };
    private int checks;

    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments);start(); }
    @Override public void onStart() { new Thread(this::diagnostics,"focuspilot-native-diagnostics").start(); }
    private void require(boolean condition,String message) {
        checks++; if(!condition) throw new AssertionError(message);
    }
    private static double milliseconds(long started) { return (SystemClock.elapsedRealtimeNanos()-started)/1000000.0; }
    private static boolean manifestRequestsInternet(Context context) throws Exception {
        PackageInfo info=context.getPackageManager().getPackageInfo(context.getPackageName(),PackageManager.GET_PERMISSIONS);
        if(info.requestedPermissions!=null) for(String permission:info.requestedPermissions)
            if(Manifest.permission.INTERNET.equals(permission)) return true;
        return false;
    }
    private void isolation(JSONObject report) throws Exception {
        Context target=getTargetContext(), test=getContext();
        int uid=Process.myUid(), pid=Process.myPid();
        int permission=target.checkPermission(Manifest.permission.INTERNET,pid,uid);
        JSONObject identity=new JSONObject().put("process_uid",uid).put("process_pid",pid)
            .put("target_package",target.getPackageName()).put("target_application_uid",target.getApplicationInfo().uid)
            .put("process_name",Application.getProcessName()).put("target_process_name",target.getApplicationInfo().processName)
            .put("test_package",test.getPackageName()).put("test_application_uid",test.getApplicationInfo().uid)
            .put("target_manifest_requests_internet",manifestRequestsInternet(target))
            .put("test_manifest_requests_internet",manifestRequestsInternet(test))
            .put("target_context_process_internet_permission",permission);
        report.put("identity",identity);
        require(uid==target.getApplicationInfo().uid,"Instrumentation must run in target application UID");
        require(Application.getProcessName().equals(target.getApplicationInfo().processName),"Instrumentation must run in target main process");
        require(!identity.getBoolean("target_manifest_requests_internet") && !identity.getBoolean("test_manifest_requests_internet"),"Both manifests must omit INTERNET");
        require(permission==PackageManager.PERMISSION_DENIED,"Target process INTERNET permission must be denied");
        JSONObject probe=new JSONObject().put("numeric_destination","192.0.2.1").put("port",9)
            .put("connect_timeout_ms",1000).put("permission_denial_proven",false);
        report.put("socket_probe",probe);
        long started=SystemClock.elapsedRealtimeNanos();
        Throwable denied=null;
        try(Socket socket=new Socket()) {
            // Literal bytes avoid DNS. TEST-NET is diagnostic only; no payload is sent.
            socket.connect(new InetSocketAddress(InetAddress.getByAddress(new byte[]{(byte)192,0,2,1}),9),1000);
        } catch(Exception failure) { denied=failure; }
        probe.put("elapsed_ms",milliseconds(started));
        JSONArray causes=new JSONArray();
        int errno=0;
        Throwable cursor=denied;
        Set<Throwable> visited=java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<Throwable,Boolean>());
        for(int depth=0;cursor!=null && depth<16 && visited.add(cursor);depth++,cursor=cursor.getCause()) {
            JSONObject cause=new JSONObject().put("type",cursor.getClass().getName());
            if(cursor instanceof ErrnoException) {
                int value=((ErrnoException)cursor).errno;cause.put("errno",value);
                if(value==OsConstants.EACCES || value==OsConstants.EPERM) errno=value;
            }
            causes.put(cause);
        }
        probe.put("exception_causes",causes).put("permission_errno",errno)
            .put("permission_denial_proven",errno==OsConstants.EACCES || errno==OsConstants.EPERM);
        require(probe.getBoolean("permission_denial_proven"),"Socket must fail with nested EACCES or EPERM; route, timeout and other errors do not prove isolation");
    }
    private File verifyModel(JSONObject report) throws Exception {
        File file=new File(getTargetContext().getFilesDir(),"qwen35.gguf");
        StructStat before=Os.lstat(file.getAbsolutePath());
        JSONObject model=new JSONObject().put("filename",file.getName()).put("bytes",before.st_size)
            .put("inode",before.st_ino).put("device",before.st_dev).put("links",before.st_nlink)
            .put("regular_file",OsConstants.S_ISREG(before.st_mode));
        report.put("model",model);
        require(OsConstants.S_ISREG(before.st_mode) && !OsConstants.S_ISLNK(before.st_mode),"Canonical model must be a regular non-symlink file");
        require(before.st_size==MODEL_BYTES,"Pinned model size required");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        long started=SystemClock.elapsedRealtimeNanos(), read=0;
        try(FileInputStream stream=new FileInputStream(file)) {
            byte[] buffer=new byte[64*1024];int count;
            while((count=stream.read(buffer))!=-1) {
                read+=count;
                if(read>MODEL_BYTES)throw new AssertionError("Model grew during hashing");
                if(milliseconds(started)>60000)throw new AssertionError("Model verification exceeded 60 seconds");
                digest.update(buffer,0,count);
            }
        }
        StringBuilder sha=new StringBuilder();
        for(byte value:digest.digest())sha.append(String.format(java.util.Locale.US,"%02x",value&255));
        StructStat after=Os.lstat(file.getAbsolutePath());
        model.put("sha256",sha.toString()).put("verified_bytes",read).put("verification_ms",milliseconds(started));
        require(read==MODEL_BYTES && MODEL_SHA.equals(sha.toString()),"Pinned complete model SHA required");
        require(before.st_dev==after.st_dev && before.st_ino==after.st_ino && before.st_size==after.st_size
            && before.st_mtime==after.st_mtime && OsConstants.S_ISREG(after.st_mode),"Model changed during verification");
        return file;
    }
    private static JSONObject pss() throws Exception {
        Debug.MemoryInfo memory=new Debug.MemoryInfo();Debug.getMemoryInfo(memory);
        return new JSONObject().put("total_pss_kib",memory.getTotalPss()).put("native_pss_kib",memory.nativePss)
            .put("dalvik_pss_kib",memory.dalvikPss).put("other_pss_kib",memory.otherPss)
            .put("scope","Whole current instrumented target process; includes test/framework overhead and shared-page attribution");
    }
    private void validateNative(JSONObject result,boolean capture) throws Exception {
        require(result.length()==3 && result.has("text") && result.has("metrics") && result.has("activations"),"Native output envelope must contain text, metrics and activations only");
        require(result.get("text") instanceof String && INTENT.matcher(result.getString("text")).matches(),"Native text must be exact allowed intent-only JSON");
        JSONObject metrics=result.getJSONObject("metrics");
        require(Boolean.TRUE.equals(metrics.get("reached_eos")),"Generation must reach EOS");
        require(Boolean.TRUE.equals(metrics.get("cpu_only")),"Native CPU-only identity required");
        require(Boolean.valueOf(capture).equals(metrics.get("capture_enabled")),"Capture identity must match request");
        for(String key:new String[]{"context_setup_ms","prefill_ms","decode_ms","total_ms"}) {
            Object value=metrics.get(key);
            require(value instanceof Number && Double.isFinite(((Number)value).doubleValue()) && ((Number)value).doubleValue()>=0,"Finite nonnegative native time required: "+key);
        }
        for(String key:new String[]{"prompt_tokens","generated_tokens"}) {
            Object value=metrics.get(key);double number=value instanceof Number?((Number)value).doubleValue():Double.NaN;
            require(Double.isFinite(number) && number==Math.rint(number) && number>0,"Positive integer token count required: "+key);
        }
        JSONArray activations=result.getJSONArray("activations");
        require(activations.length()==(capture?4:0),"Capture-off must have zero summaries; capture-on must have four");
        Set<String> expected=new HashSet<>();java.util.Collections.addAll(expected,"ffn_out-0","ffn_out-11","ffn_out-23","result_norm");
        for(int index=0;index<activations.length();index++) {
            JSONObject activation=activations.getJSONObject(index);
            require(expected.remove(activation.getString("tensor")),"Captured tensor must be expected and unique");
            require(activation.getInt("width")==1024 && activation.getInt("positions_in_chunk")>0,"Captured width and position count required");
            for(String key:new String[]{"mean","rms","min","max"}) {
                Object value=activation.get(key);
                require(value instanceof Number && Double.isFinite(((Number)value).doubleValue()),"Finite activation statistic required: "+key);
            }
            require(activation.getDouble("rms")>=0 && activation.getDouble("min")<=activation.getDouble("max"),"Activation statistics must have valid range");
            JSONArray values=activation.getJSONArray("first_values");require(values.length()==8,"Eight observed values required");
            for(int item=0;item<values.length();item++)require(values.get(item) instanceof Number && Double.isFinite(values.getDouble(item)),"Observed values must be finite");
        }
        require(!capture || expected.isEmpty(),"All four observational tensors required");
    }
    private void diagnostics() {
        Bundle bundle=new Bundle();JSONObject report=new JSONObject();JSONArray requests=new JSONArray();
        LocalModel model=null;
        ScheduledExecutorService deadline=Executors.newSingleThreadScheduledExecutor(runnable->{Thread thread=new Thread(runnable,"focuspilot-native-deadline");thread.setDaemon(true);return thread;});
        boolean passed=false;long started=SystemClock.elapsedRealtimeNanos();
        try {
            report.put("schema","focuspilot.native_isolation.v1").put("fixture_scope","Fixed openly seen synthetic requests; diagnostic only, no held-out accuracy claim")
                .put("actions_executed",false).put("preferences_accessed",false).put("production_singleton_used",false)
                .put("ui_used",false).put("network_settings_changed",false).put("permission_grants_changed",false)
                .put("airplane_mode_claim",false).put("npu_claim",false).put("causal_interpretation_claim",false)
                .put("requests",requests);
            isolation(report);
            File file=verifyModel(report);
            long loadStarted=SystemClock.elapsedRealtimeNanos();model=new LocalModel(file.getAbsolutePath());
            report.put("java_model_load_ms",milliseconds(loadStarted)).put("pss_after_load",pss());
            for(int index=0;index<REQUESTS.length;index++) {
                boolean capture=index==8;
                JSONObject row=new JSONObject().put("id","diagnostic-"+(index+1)).put("request",REQUESTS[index]).put("capture",capture);
                requests.put(row);
                LocalModel current=model;AtomicBoolean timedOut=new AtomicBoolean(false),active=new AtomicBoolean(true);
                // Cancellation is cooperative. The host runner must independently bound the instrumentation process.
                current.prepareGeneration();
                ScheduledFuture<?> cancellation=deadline.schedule(()->{
                    synchronized(current) { if(active.get()) { timedOut.set(true);current.cancel(); } }
                },120,TimeUnit.SECONDS);
                long requestStarted=SystemClock.elapsedRealtimeNanos();String output;
                try { output=current.generatePreparedIntent(REQUESTS[index],capture); }
                finally {
                    synchronized(current) { active.set(false);cancellation.cancel(false); }
                    row.put("java_request_ms",milliseconds(requestStarted)).put("cooperative_timeout",timedOut.get());
                }
                row.put("native_output_json",output);
                JSONObject nativeOutput=new JSONObject(output);row.put("native_output",nativeOutput);
                require(!timedOut.get(),"Request exceeded cooperative 120-second timeout");
                validateNative(nativeOutput,capture);
                Matcher match=INTENT.matcher(nativeOutput.getString("text"));require(match.matches(),"Intent text validates before gating");
                String intent=match.group(1);
                ModelCommandGate.Proposal proposal=ModelCommandGate.validate(intent,REQUESTS[index]);
                int expectedHour=index==2?7:0, expectedMinute=index==2?30:0, expectedSeconds=index==0?20:index==3?300:0;
                row.put("raw_intent",intent).put("gated_kind",proposal.kind.name()).put("gated_hour",proposal.hour)
                    .put("gated_minute",proposal.minute).put("gated_seconds",proposal.seconds)
                    .put("illustrative_expected",new JSONObject().put("intent",EXPECTED_INTENTS[index]).put("kind",EXPECTED_KINDS[index].name())
                        .put("hour",expectedHour).put("minute",expectedMinute).put("seconds",expectedSeconds))
                    .put("raw_intent_matches_illustration",EXPECTED_INTENTS[index].equals(intent))
                    .put("complete_proposal_matches_illustration",proposal.kind==EXPECTED_KINDS[index] && proposal.hour==expectedHour
                        && proposal.minute==expectedMinute && proposal.seconds==expectedSeconds)
                    .put("pss_after_request",pss());
            }
            require(requests.length()==10,"All ten diagnostics completed");
            report.put("semantic_accuracy_is_infrastructure_pass_condition",false);
            passed=true;
        } catch(Throwable error) {
            try { report.put("failure_type",error.getClass().getName()).put("failure",String.valueOf(error.getMessage())); }
            catch(Exception ignored) { }
        } finally {
            deadline.shutdownNow();
            if(model!=null) {
                try { synchronized(model) { model.close(); } report.put("native_closed",true); }
                catch(Throwable error) { passed=false;try { report.put("close_failure_type",error.getClass().getName()); } catch(Exception ignored) { } }
            }
            try { report.put("passed",passed).put("checks",checks).put("java_instrumentation_ms",milliseconds(started)); }
            catch(Exception error) { passed=false; }
        }
        bundle.putBoolean("passed",passed);bundle.putString("report_json",report.toString());
        bundle.putString("stream","Fixed synthetic native isolation diagnostics: "+passed+", "+requests.length()+" requests, "+checks+" checks. No phone action or setting changed.\n");
        finish(passed?-1:0,bundle);
    }
}
