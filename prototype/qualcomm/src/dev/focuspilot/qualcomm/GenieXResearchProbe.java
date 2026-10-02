package dev.focuspilot.qualcomm;

import android.content.Context;
import android.os.Build;
import android.os.Looper;
import com.geniex.sdk.GenieXSdk;
import com.geniex.sdk.jni.Llm;
import com.geniex.sdk.bean.*;
import java.io.File;
import java.io.FileInputStream;
import java.security.MessageDigest;
import java.util.Collections;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

/** Pre-event research adapter, compile checked against GenieX AAR 0.7.0.
 * Not integrated, not device-tested. Uses the pinned JNI API, not coroutine wrappers.
 * No download, phone action, context observation, or automatic backend fallback.
 * Run on one worker thread; cancel may be called from the UI. Native prefill is
 * not guaranteed promptly cancellable; cancellation always suppresses the result.
 */
public final class GenieXResearchProbe {
    public static final String MODEL_SHA256 = "57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf";
    private final AtomicBoolean cancelled = new AtomicBoolean();
    private final AtomicBoolean running = new AtomicBoolean();
    private final Object lifecycle = new Object();
    private Llm nativeApi;
    private long activeHandle;

    public static final class Observation {
        public final String requestedCompute, pluginVersion, proposal, backendProof;
        public final double ttftMs, promptMs, decodeMs;
        public final long promptTokens, generatedTokens;
        Observation(String compute, String version, LlmGenerateResult result) {
            requestedCompute = compute;
            pluginVersion = version;
            proposal = result.getFullText();
            backendProof = "UNVERIFIED: requested compute and successful output do not prove NPU execution";
            ProfilingData p = result.getProfileData();
            ttftMs=p.getTtftMs(); promptMs=p.getPromptTimeMs(); decodeMs=p.getDecodeTimeMs();
            promptTokens=p.getPromptTokens(); generatedTokens=p.getGeneratedTokens();
        }
    }

    public void cancel() {
        cancelled.set(true);
        synchronized (lifecycle) {
            if (nativeApi != null && activeHandle != 0) nativeApi.stopStream(activeHandle);
        }
    }

    public Observation run(Context context, File verifiedGguf, String compute, String syntheticRequest) throws Exception {
        if (Looper.myLooper() == Looper.getMainLooper()) throw new IllegalStateException("Use a worker thread");
        if (!running.compareAndSet(false,true)) throw new IllegalStateException("One probe at a time");
        try {
            if (cancelled.get()) throw new InterruptedException("Cancelled; create a new probe for retry");
            if (Build.VERSION.SDK_INT < 27) throw new IllegalArgumentException("GenieX requires API27+");
            if (compute == null || !(compute.equals("cpu") || compute.equals("npu") || compute.equals("hybrid"))) throw new IllegalArgumentException("Explicit cpu/npu/hybrid only");
            if (syntheticRequest == null || syntheticRequest.length() > 256 || syntheticRequest.trim().isEmpty()) throw new IllegalArgumentException("Request must be 1–256 characters");
            if (!verifiedGguf.isFile() || verifiedGguf.length() != 563036064L || !MODEL_SHA256.equals(sha256(verifiedGguf))) throw new IllegalArgumentException("Selected pinned Q4_0 model checksum/size mismatch");
            GenieXSdk sdk = GenieXSdk.Companion.getInstance();
            AtomicReference<String> initError = new AtomicReference<>();
            sdk.init(context.getApplicationContext(),new GenieXSdk.InitCallback() {
                public void onSuccess() {}
                public void onFailure(String reason) { initError.set(reason); }
            });
            if (initError.get()!=null) throw new IllegalStateException(initError.get());
            if (cancelled.get()) throw new InterruptedException("Cancelled during initialization");
            ModelConfig config = new ModelConfig();
            config.setNCtx(1024); config.setNThreads(4); config.setNThreadsBatch(4);
            config.setNBatch(128); config.setNUBatch(128); config.setNGpuLayers(compute.equals("cpu") ? 0 : -1);
            Llm api = new Llm();
            long handle = api.create(new LlmCreateInput(verifiedGguf.getAbsolutePath(),null,config,"llama_cpp",compute));
            if (handle == 0) throw new IllegalStateException("Native model creation failed; retain existing CPU fallback");
            synchronized (lifecycle) { nativeApi=api; activeHandle=handle; }
            try {
                if (cancelled.get()) throw new InterruptedException("Cancelled during model creation");
                ChatMessage[] messages={new ChatMessage("system","Research only. Choose exactly one label: start_focus, pause_focus, propose_alarm, abstain. Negated, unsafe or compound requests must abstain. Do not execute anything.",Collections.emptyList(),null,null),new ChatMessage("user",syntheticRequest,Collections.emptyList(),null,null)};
                LlmApplyChatTemplateOutput template=api.applyChatTemplate(handle,messages,null,false,true);
                if (template==null || template.getFormattedText().isEmpty()) throw new IllegalStateException("Chat template failed");
                GenerationConfig generation=new GenerationConfig(); generation.setMaxTokens(32);
                SamplerConfig sampler=new SamplerConfig(); sampler.setTemperature(0f); sampler.setSeed(7); generation.setSamplerConfig(sampler);
                AtomicReference<LlmGenerateResult> completed=new AtomicReference<>();
                api.generate(handle,template.getFormattedText(),generation,new LLMTokenCallback() {
                    public boolean onToken(String token) { return !cancelled.get(); }
                    public void onComplete(LlmGenerateResult result) { completed.set(result); }
                });
                if (cancelled.get()) throw new InterruptedException("Cancelled; discard all output");
                LlmGenerateResult result=completed.get();
                if (result==null || result.getProfileData()==null || result.getFullText()==null) throw new IllegalStateException("No completed native result");
                return new Observation(compute,sdk.getPluginVersion("llama_cpp"),result);
            } finally {
                synchronized(lifecycle) { activeHandle=0; nativeApi=null; api.destroy(handle); }
            }
        } finally { running.set(false); }
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try (FileInputStream input=new FileInputStream(file)) {
            byte[] bytes=new byte[65536]; int count;
            while((count=input.read(bytes))!=-1) {
                if(cancelled.get()) throw new InterruptedException("Cancelled during checksum");
                digest.update(bytes,0,count);
            }
        }
        StringBuilder hex=new StringBuilder();
        for(byte b:digest.digest()) hex.append(String.format("%02x",b & 255));
        return hex.toString();
    }
}
