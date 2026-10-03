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
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import java.util.Iterator;
import java.util.zip.ZipFile;
import java.nio.charset.StandardCharsets;
import android.util.Base64;
import org.json.JSONArray;
import org.json.JSONObject;

/** Fixed synthetic JNI diagnostics in the target UID. No UI, actions or preferences. */
public final class PageNativeIsolationInstrumentation extends Instrumentation {
    private static final long MODEL_BYTES=563036064L;
    private static final String MODEL_SHA="57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf";
    private static final String NATIVE_SHA="675f2142a2c35b9c0260dc43944db09c3bb570a63c9f49a27e47625f7b98152e";
    private static final long WATCHDOG_MS=120000L;
    private static final String[] REQUESTS={
        "Start focus for 20 seconds", "Stop focus", "Set an alarm for 07:30",
        "Set a five-minute timer", "Open calculator", "Do not open settings"
    };
    private static final String[] EXPECTED_RAW={
        "{\"intent\":\"start_focus\",\"amount\":20,\"unit\":\"seconds\"}",
        "{\"intent\":\"pause_focus\"}", "{\"intent\":\"alarm\",\"hour\":7,\"minute\":30}",
        "{\"intent\":\"timer\",\"amount\":5,\"unit\":\"minutes\"}",
        "{\"intent\":\"open_app\",\"app\":\"calculator\"}", "{\"intent\":\"unknown\"}"
    };
    private Bundle arguments;
    private final AtomicBoolean timedOut=new AtomicBoolean(false);
    private boolean modelUnsafe;
    private int checks;

    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments);this.arguments=arguments;start(); }
    @Override public void onStart() { new Thread(this::diagnostics,"focuspilot-unit-native-diagnostics").start(); }
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
        require("dev.focuspilot.prototype".equals(target.getPackageName())&&"dev.focuspilot.prototype.test".equals(test.getPackageName()),"Exact target/test package context required");
        require(uid==target.getApplicationInfo().uid,"Instrumentation must run in target application UID");
        require(Application.getProcessName().equals(target.getApplicationInfo().processName),"Instrumentation must run in target main process");
        require(!identity.getBoolean("target_manifest_requests_internet") && !identity.getBoolean("test_manifest_requests_internet"),"Both manifests must omit INTERNET");
        require(permission==PackageManager.PERMISSION_DENIED,"Target process INTERNET permission must be denied");
        JSONObject probe=new JSONObject().put("api","android.system.Os.socket")
            .put("family",OsConstants.AF_INET).put("family_name","AF_INET")
            .put("type",OsConstants.SOCK_STREAM).put("type_name","SOCK_STREAM")
            .put("protocol",OsConstants.IPPROTO_TCP).put("protocol_name","IPPROTO_TCP")
            .put("connect_attempted",false).put("dns_used",false).put("payload_sent",false)
            .put("socket_creation_succeeded",false).put("returned_fd_closed",false)
            .put("socket_creation_denied",false).put("permission_denial_proven",false);
        report.put("socket_probe",probe);
        long started=SystemClock.elapsedRealtimeNanos();
        FileDescriptor socket=null;
        ErrnoException denied=null;
        try {
            // Socket creation only: no connection, address, DNS lookup or payload.
            socket=Os.socket(OsConstants.AF_INET,OsConstants.SOCK_STREAM,OsConstants.IPPROTO_TCP);
        } catch(ErrnoException failure) { denied=failure; }
        finally {
            probe.put("elapsed_ms",milliseconds(started));
            if(socket!=null) {
                // An unexpectedly returned descriptor is owned only by this probe.
                probe.put("socket_creation_succeeded",true);
                Os.close(socket);
                probe.put("returned_fd_closed",true);
            }
        }
        int errno=denied==null?0:denied.errno;
        boolean creationDenied=denied!=null && (errno==OsConstants.EACCES || errno==OsConstants.EPERM);
        probe.put("exception_type",denied==null?JSONObject.NULL:denied.getClass().getName())
            .put("attempted_function","socket")
            .put("exception_message",denied==null?JSONObject.NULL:denied.getMessage())
            .put("permission_errno",errno).put("socket_creation_denied",creationDenied)
            .put("permission_denial_proven",creationDenied);
        require(socket==null && creationDenied,"Direct Os.socket creation must fail with EACCES or EPERM before model access");
    }
    private File verifyModel(JSONObject report,String key) throws Exception {
        File file=new File(getTargetContext().getFilesDir(),"qwen35.gguf");
        StructStat before=Os.lstat(file.getAbsolutePath());
        JSONObject model=new JSONObject().put("filename",file.getName()).put("bytes",before.st_size)
            .put("inode",before.st_ino).put("device",before.st_dev).put("links",before.st_nlink)
            .put("regular_file",OsConstants.S_ISREG(before.st_mode)).put("mtime",before.st_mtime);
        report.put(key,model);
        require(OsConstants.S_ISREG(before.st_mode) && !OsConstants.S_ISLNK(before.st_mode),"Canonical model must be a regular non-symlink file");
        require(before.st_size==MODEL_BYTES&&before.st_nlink==1,"Pinned model size and single link required");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        long started=SystemClock.elapsedRealtimeNanos(), read=0;
        try(FileInputStream stream=new FileInputStream(file)) {
            byte[] buffer=new byte[64*1024];int count;
            while((count=stream.read(buffer))!=-1) {
                read+=count;
                if(read>MODEL_BYTES)throw new AssertionError("Model grew during hashing");
                if(timedOut.get()||milliseconds(started)>60000)throw new AssertionError("Model verification exceeded watchdog or 60 seconds");
                digest.update(buffer,0,count);
            }
        }
        StringBuilder sha=new StringBuilder();
        for(byte value:digest.digest())sha.append(String.format(java.util.Locale.US,"%02x",value&255));
        StructStat after=Os.lstat(file.getAbsolutePath());
        model.put("sha256",sha.toString()).put("verified_bytes",read).put("verification_ms",milliseconds(started));
        require(read==MODEL_BYTES && MODEL_SHA.equals(sha.toString()),"Pinned complete model SHA required");
        require(before.st_dev==after.st_dev && before.st_ino==after.st_ino && before.st_size==after.st_size
            && before.st_mtime==after.st_mtime && before.st_nlink==after.st_nlink && OsConstants.S_ISREG(after.st_mode),"Model changed during verification");
        return file;
    }
    private static JSONObject pss() throws Exception {
        Debug.MemoryInfo memory=new Debug.MemoryInfo();Debug.getMemoryInfo(memory);
        return new JSONObject().put("total_pss_kib",memory.getTotalPss()).put("native_pss_kib",memory.nativePss)
            .put("dalvik_pss_kib",memory.dalvikPss).put("other_pss_kib",memory.otherPss)
            .put("scope","Whole current instrumented target process; includes test/framework overhead and shared-page attribution");
    }
    private UnitCommand.Proposal validateNative(JSONObject result,boolean capture) throws Exception {
        require(result.length()==3 && result.has("text") && result.has("metrics") && result.has("activations"),"Native output envelope must contain text, metrics and activations only");
        require(result.get("text") instanceof String,"Native text must be a string");
        UnitCommand.Proposal parsed=UnitCommand.parseResponse(result.getString("text"));
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
            require(Double.isFinite(number) && number==Math.rint(number) && number>0 && number<=(key.equals("prompt_tokens")?896:127),"Positive bounded integer token count required: "+key);
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
        return parsed;
    }
    private static String sha(byte[] value) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(value));
    }
    private static String hex(byte[] bytes) {
        StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return out.toString();
    }
    private String requiredSha(String key) {
        String value=arguments==null?null:arguments.getString(key);
        require(value!=null&&value.matches("[0-9a-f]{64}"),"Full explicit SHA required: "+key);return value;
    }
    private void sourceBindings(JSONObject report) throws Exception {
        String commit=arguments==null?null:arguments.getString("source_commit");
        require(commit!=null&&commit.matches("[0-9a-f]{40}"),"Full source commit required");
        String encoded=arguments.getString("declared_source_sha256_b64");
        require(encoded!=null&&encoded.length()<=16000&&encoded.matches("[A-Za-z0-9+/]*={0,2}"),"Bounded standard Base64 source map required");
        JSONObject sources=new JSONObject(new String(Base64.decode(encoded,Base64.NO_WRAP),StandardCharsets.UTF_8));
        require(sources.length()>0&&sources.length()<=32,"Bounded source pin inventory required");
        Iterator<String> keys=sources.keys();Set<String> filenames=new HashSet<>();
        while(keys.hasNext()) {
            String path=keys.next();require(path.matches("prototype/[A-Za-z0-9_./-]+\\.java")&&!path.contains(".."),"Public source path required");
            require(sources.get(path) instanceof String&&sources.getString(path).matches("[0-9a-f]{64}"),"Full source pin required");
            filenames.add(path.substring(path.lastIndexOf('/')+1));
        }
        for(String name:new String[]{"LocalModel.java","CompatibleUnitCommand.java","UnitCommand.java","StructuredCommand.java","ModelCommandGate.java","CommandNumberWords.java","PageNativeIsolationInstrumentation.java"})
            require(filenames.contains(name),"Selected source pin missing: "+name);
        report.put("source_commit",commit).put("declared_source_sha256",sources)
            .put("source_binding_scope","Caller-supplied frozen build source attribution, not original Java hashes recovered from DEX");
        require(MODEL_SHA.equals(requiredSha("expected_model_sha256")),"Selected model pin must remain unchanged");
        require(NATIVE_SHA.equals(requiredSha("expected_native_sha256")),"Selected native pin must remain unchanged");
    }
    private JSONObject apkIdentity() throws Exception {
        File file=new File(getTargetContext().getApplicationInfo().sourceDir);
        StructStat before=Os.lstat(file.getAbsolutePath());
        require(OsConstants.S_ISREG(before.st_mode)&&before.st_size>0&&before.st_size<20000000,"Regular bounded light target APK required");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");long read=0;
        try(FileInputStream stream=new FileInputStream(file)) {
            byte[] buffer=new byte[65536];int n;while((n=stream.read(buffer))!=-1){if(timedOut.get())throw new AssertionError("Overall watchdog expired");read+=n;digest.update(buffer,0,n);}
        }
        String appSha=hex(digest.digest());require(appSha.equals(requiredSha("expected_app_sha256")),"Exact installed target APK required");
        MessageDigest nativeDigest=MessageDigest.getInstance("SHA-256");long nativeRead=0;
        try(ZipFile apk=new ZipFile(file)) {
            java.util.zip.ZipEntry entry=apk.getEntry("lib/arm64-v8a/libfocuspilot_local.so");require(entry!=null,"Selected arm64 native entry required");
            java.util.Enumeration<? extends java.util.zip.ZipEntry> entries=apk.entries();Set<String> names=new HashSet<>();
            while(entries.hasMoreElements()){String name=entries.nextElement().getName();require(names.add(name)&&!name.endsWith(".gguf"),"Unique light APK payload required");}
            try(java.io.InputStream stream=apk.getInputStream(entry)) {
                byte[] buffer=new byte[65536];int n;while((n=stream.read(buffer))!=-1){nativeRead+=n;if(timedOut.get()||nativeRead>64000000)throw new AssertionError("Native verification bound");nativeDigest.update(buffer,0,n);}
            }
        }
        String nativeSha=hex(nativeDigest.digest());require(NATIVE_SHA.equals(nativeSha),"Actual selected APK native SHA required");
        StructStat after=Os.lstat(file.getAbsolutePath());
        require(before.st_dev==after.st_dev&&before.st_ino==after.st_ino&&before.st_size==after.st_size&&before.st_mtime==after.st_mtime&&read==before.st_size,"Target APK changed during hashing");
        return new JSONObject().put("sha256",appSha).put("native_sha256",nativeSha).put("bytes",read).put("inode",before.st_ino).put("device",before.st_dev).put("mtime",before.st_mtime)
            .put("native_bytes",nativeRead).put("native_entry","lib/arm64-v8a/libfocuspilot_local.so");
    }
    private static boolean same(JSONObject a,JSONObject b) throws Exception {
        if(a.length()!=b.length())return false;Iterator<String> keys=a.keys();
        while(keys.hasNext()){String key=keys.next();if(!b.has(key)||!a.get(key).equals(b.get(key)))return false;}return true;
    }
    private void checked(JSONObject row,String key,CompatibleUnitCommand.Proposal proposal,JSONObject expected) throws Exception {
        JSONObject canonical=new JSONObject(proposal.canonicalJson());boolean matches=same(canonical,expected);
        row.put(key,new JSONObject().put("canonical",canonical).put("accepted",proposal.accepted).put("origin",proposal.origin).put("reason",proposal.reason).put("matches_illustration",matches));
        if(proposal.accepted&&!matches)modelUnsafe=true;
        require(!proposal.accepted||matches,"Accepted proposal has incorrect complete canonical slots");
        require(proposal.origin.equals(proposal.source),"Actual origin aliases must agree");
        require(proposal.accepted?(proposal.origin.equals(CompatibleUnitCommand.FAST_LOCAL_REQUEST)||proposal.origin.equals(CompatibleUnitCommand.CHECKED_MODEL)):proposal.origin.equals(CompatibleUnitCommand.UNKNOWN),"Origin must match acceptance");

    }
    private void diagnostics() {
        Bundle bundle=new Bundle();JSONObject report=new JSONObject();JSONArray rows=new JSONArray();
        LocalModel model=null;Object ownership=new Object();AtomicReference<LocalModel> current=new AtomicReference<>();AtomicBoolean watchdogActive=new AtomicBoolean(true);
        ScheduledExecutorService deadline=Executors.newSingleThreadScheduledExecutor(runnable->{Thread thread=new Thread(runnable,"focuspilot-unit-deadline");thread.setDaemon(true);return thread;});
        ScheduledFuture<?> watchdog=deadline.schedule(()->{synchronized(ownership){if(watchdogActive.get()){timedOut.set(true);LocalModel active=current.get();if(active!=null)active.cancel();}}},WATCHDOG_MS,TimeUnit.MILLISECONDS);
        boolean passed=false;int completed=0;long started=SystemClock.elapsedRealtimeNanos();
        try {
            report.put("schema","focuspilot.native_page_isolation.v1").put("requests",rows).put("request_count",6).put("watchdog_ms",WATCHDOG_MS)
                .put("fixture_scope","Six fixed openly seen synthetic requests, one sequential attempt each; descriptive diagnostic, not fresh accuracy")
                .put("actions_executed",0).put("preferences_accessed",false).put("production_preferences_accessed",false).put("production_singleton_used",false)
                .put("services_started",false).put("ui_used",false).put("voice_used",false).put("network_settings_changed",false).put("permission_grants_changed",false)
                .put("airplane_mode_claim",false).put("npu_claim",false).put("causal_interpretation_claim",false)
                .put("semantic_accuracy_is_infrastructure_pass_condition",false);
            sourceBindings(report);isolation(report);
            long pageSize=Os.sysconf(OsConstants._SC_PAGESIZE);
            report.put("page_size_bytes",pageSize).put("installed_app_source_commit","caaf5246116ad02144f8bf0a4d92ce8053bf8275");
            require(pageSize>0,"Actual process page size required");
            require(pageSize==4096,"This planned Nothing regression requires the observed4096-byte page-size environment");
            JSONObject apkBefore=apkIdentity();report.put("apk_before",apkBefore).put("installed_apk_sha256",apkBefore.getString("sha256")).put("native_sha256",NATIVE_SHA);
            File file=verifyModel(report,"model_before");long loadStarted=SystemClock.elapsedRealtimeNanos();
            require(!timedOut.get(),"Overall watchdog expired before model load");
            model=new LocalModel(file.getAbsolutePath());
            synchronized(ownership){current.set(model);require(!timedOut.get(),"Overall watchdog expired during model initialization");}
            report.put("model_loaded",true).put("java_model_load_ms",milliseconds(loadStarted)).put("pss_after_load",pss());
            for(int index=0;index<REQUESTS.length;index++) {
                boolean capture=index==1;String request=REQUESTS[index];JSONObject row=new JSONObject().put("id","native-unit-"+(index+1)).put("request",request).put("capture",capture);
                rows.put(row);
                row.put("prompt_sha256",sha(CompatibleUnitCommand.renderPrompt(request).getBytes(StandardCharsets.UTF_8)))
                    .put("grammar_sha256",sha(CompatibleUnitCommand.GRAMMAR.getBytes(StandardCharsets.UTF_8)));
                // Same submitting worker prepares before entry. Lock excludes a watchdog cancel→prepare reset race.
                synchronized(ownership){
                    require(!timedOut.get(),"Overall watchdog expired before request");model.prepareGeneration();
                    if(timedOut.get()||milliseconds(started)>=WATCHDOG_MS){timedOut.set(true);model.cancel();throw new AssertionError("Overall watchdog expired during preparation");}
                }
                long requestStarted=SystemClock.elapsedRealtimeNanos();String output;
                try{output=model.generatePreparedUnitCommand(request,capture);}
                finally{row.put("java_request_ms",milliseconds(requestStarted));}
                row.put("native_output_json",output);JSONObject nativeOutput=new JSONObject(output);row.put("native_output",nativeOutput);
                require(!timedOut.get(),"Overall cooperative watchdog expired");
                UnitCommand.Proposal parsed=validateNative(nativeOutput,capture);JSONObject raw=new JSONObject(nativeOutput.getString("text")),expectedRaw=new JSONObject(EXPECTED_RAW[index]);
                JSONObject expected=new JSONObject(UnitCommand.parseResponse(EXPECTED_RAW[index]).canonicalJson());
                row.put("illustrative_expected_raw",expectedRaw).put("illustrative_expected",expected).put("raw_canonical",new JSONObject(parsed.canonicalJson()))
                    .put("raw_intent_matches_illustration",parsed.intent.equals(expectedRaw.getString("intent")))
                    .put("raw_full_slots_match_illustration",same(raw,expectedRaw)).put("canonical_slots_match_illustration",same(new JSONObject(parsed.canonicalJson()),expected));
                CompatibleUnitCommand.Proposal checkedModel=CompatibleUnitCommand.validate(request,nativeOutput.getString("text"));
                CompatibleUnitCommand.Proposal fast=CompatibleUnitCommand.recognize(request);
                checked(row,"checked_model",checkedModel,expected);checked(row,"fast_local",fast,expected);checked(row,"product_pipeline",fast.accepted?fast:checkedModel,expected);
                row.put("pss_after_request",pss());completed++;
            }
            require(completed==6,"All six native diagnostics must complete");
            passed=true;
        }catch(Throwable error){try{report.put("failure_type",error.getClass().getName()).put("failure",String.valueOf(error.getMessage()));}catch(Exception ignored){}}
        finally {
            synchronized(ownership){current.set(null);if(model!=null){try{model.close();report.put("model_closed",true);}catch(Throwable error){passed=false;try{report.put("close_failure_type",error.getClass().getName());}catch(Exception ignored){}}}}
            if(passed)try {
                verifyModel(report,"model_after");JSONObject before=report.getJSONObject("model_before"),after=report.getJSONObject("model_after");
                for(String key:new String[]{"filename","bytes","inode","device","links","regular_file","mtime","sha256","verified_bytes"})require(before.get(key).equals(after.get(key)),"Pinned model identity changed: "+key);
                JSONObject apkAfter=apkIdentity();report.put("apk_after",apkAfter);require(same(report.getJSONObject("apk_before"),apkAfter),"Installed target/native identity changed");
            }catch(Throwable error){passed=false;try{report.put("postflight_failure_type",error.getClass().getName()).put("postflight_failure",String.valueOf(error.getMessage()));}catch(Exception ignored){}}
            synchronized(ownership){
                if(milliseconds(started)>=WATCHDOG_MS)timedOut.set(true);
                watchdogActive.set(false);passed=passed&&!timedOut.get()&&!modelUnsafe;
            }
            watchdog.cancel(false);deadline.shutdownNow();
            try{report.put("passed",passed).put("checks",checks).put("completed_request_count",completed).put("watchdog_triggered",timedOut.get()).put("model_unsafe",modelUnsafe)
                .put("model_closed",report.optBoolean("model_closed",false)).put("java_instrumentation_ms",milliseconds(started));if(!report.has("failure_type"))report.put("failure_type",JSONObject.NULL);}
            catch(Exception error){passed=false;}
        }
        bundle.putBoolean("passed",passed);bundle.putString("report_json",report.toString());
        bundle.putString("stream","Fixed synthetic unit native isolation: "+passed+", "+completed+" completed requests. No action or setting changed.\n");
        finish(passed?-1:0,bundle);
    }
}
