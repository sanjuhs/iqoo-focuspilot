package dev.focuspilot.qualcomm.research;

import android.content.Context;
import android.os.Build;
import android.os.Looper;
import android.os.Process;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import com.geniex.sdk.GenieXSdk;
import com.geniex.sdk.bean.*;
import com.geniex.sdk.jni.Llm;
import java.io.File;
import java.io.FileInputStream;
import java.security.MessageDigest;
import java.util.Collections;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.json.JSONObject;

/** Derivative of the repository's compile-only GenieXResearchProbe, isolated from Mira.
 * One worker owns create/generate/destroy. Cancel only calls stopStream while ownership
 * is locked; it never destroys a handle concurrently. No actions or automatic fallback.
 */
final class NativeProbe {
    static final long MODEL_BYTES = 563036064L;
    static final String MODEL_SHA = "57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf";
    private final AtomicBoolean cancelled = new AtomicBoolean();
    private final AtomicBoolean cancelDispatched = new AtomicBoolean();
    private final Object ownership = new Object();
    private Llm activeApi;
    private long activeHandle;
    private volatile boolean cleanupUncertain;
    boolean requiresQuarantine() { return cleanupUncertain; }

    void cancel() {
        cancelled.set(true);
        if (!cancelDispatched.compareAndSet(false, true)) return;
        new Thread(() -> {
            synchronized (ownership) {
                if (activeApi != null && activeHandle != 0) activeApi.stopStream(activeHandle);
            }
        }, "geniex-research-cancel").start();
    }
    private void checkCancelled() throws InterruptedException {
        if (cancelled.get() || Thread.currentThread().isInterrupted()) throw new InterruptedException("Cancelled; output discarded.");
    }
    JSONObject run(Context context, String mode, int caseIndex) throws Exception {
        if (Looper.myLooper() == Looper.getMainLooper()) throw new IllegalStateException("Worker required.");
        HardwareGate.Assessment hardware = HardwareGate.assess(Build.VERSION.SDK_INT, Build.SOC_MODEL,
                Build.SUPPORTED_ABIS.length == 0 ? "" : Build.SUPPORTED_ABIS[0], Process.is64Bit(),
                Os.sysconf(OsConstants._SC_PAGESIZE));
        if (!hardware.allowed) throw new IllegalStateException(hardware.reason);
        if (!HardwareGate.explicitMode(mode)) throw new IllegalArgumentException("Explicit backend required.");
        String request = SyntheticCases.at(caseIndex);
        checkCancelled();
        // Fixed own-package location only, never an Intent-supplied/cross-app path.
        File model = new File(context.getFilesDir(), "qwen35.gguf");
        StructStat before = verifyModel(model);
        checkCancelled();

        // MUST remain after all guards: referencing GenieXSdk initializes npu_jni.
        GenieXSdk sdk = GenieXSdk.Companion.getInstance();
        AtomicReference<String> initFailure = new AtomicReference<>();
        sdk.init(context.getApplicationContext(), new GenieXSdk.InitCallback() {
            public void onSuccess() {}
            public void onFailure(String reason) { initFailure.set(reason); }
        });
        if (initFailure.get() != null) throw new IllegalStateException(initFailure.get());
        checkCancelled();
        ModelConfig config = new ModelConfig();
        config.setNCtx(1024); config.setNThreads(4); config.setNThreadsBatch(4);
        config.setNBatch(128); config.setNUBatch(128); config.setNGpuLayers(mode.equals("cpu") ? 0 : -1);
        Llm api = new Llm();
        long handle = api.create(new LlmCreateInput(model.getAbsolutePath(), null, config, "llama_cpp", mode));
        if (handle == 0) throw new IllegalStateException("Native model creation failed. No fallback was attempted.");
        synchronized (ownership) { activeApi = api; activeHandle = handle; }
        JSONObject observation = null;
        try {
            checkCancelled();
            ChatMessage[] messages = {
                new ChatMessage("system", "Research only. Choose exactly one label: start_focus, pause_focus, propose_alarm, abstain. Negated, unsafe or compound requests must abstain. Do not execute anything.", Collections.emptyList(), null, null),
                new ChatMessage("user", request, Collections.emptyList(), null, null)
            };
            LlmApplyChatTemplateOutput template = api.applyChatTemplate(handle, messages, null, false, true);
            if (template == null || template.getFormattedText().isEmpty()) throw new IllegalStateException("Chat template failed.");
            checkCancelled();
            GenerationConfig generation = new GenerationConfig(); generation.setMaxTokens(32);
            SamplerConfig sampler = new SamplerConfig(); sampler.setTemperature(0f); sampler.setSeed(7);
            generation.setSamplerConfig(sampler);
            AtomicReference<LlmGenerateResult> completed = new AtomicReference<>();
            // Synchronous SDK JNI contract; callback collects completion, not actions.
            LlmGenerateResult returned = api.generate(handle, template.getFormattedText(), generation, new LLMTokenCallback() {
                public boolean onToken(String token) { return !cancelled.get(); }
                public void onComplete(LlmGenerateResult result) { completed.set(result); }
            });
            checkCancelled();
            LlmGenerateResult result = completed.get() != null ? completed.get() : returned;
            if (result == null || result.getFullText() == null || result.getProfileData() == null)
                throw new IllegalStateException("No completed native result.");
            ProfilingData profile = result.getProfileData();
            if (!finiteNonnegative(profile.getTtftMs()) || !finiteNonnegative(profile.getPromptTimeMs())
                    || !finiteNonnegative(profile.getDecodeTimeMs()) || profile.getPromptTokens() < 1
                    || profile.getGeneratedTokens() < 0 || profile.getGeneratedTokens() > 32)
                throw new IllegalStateException("Invalid runtime profiling.");
            StructStat after = verifyModel(model);
            if (!sameFile(before, after)) throw new IllegalStateException("Pinned model changed during the run.");
            checkCancelled();
            observation = new JSONObject().put("schema", "focuspilot.geniex_observation.v1")
                    .put("soc", Build.SOC_MODEL).put("requested_compute", mode).put("runtime", "llama_cpp")
                    .put("plugin_version", sdk.getPluginVersion("llama_cpp"))
                    .put("request", request).put("model_sha256", MODEL_SHA).put("model_bytes", MODEL_BYTES)
                    .put("proposal", result.getFullText()).put("ttft_ms", profile.getTtftMs())
                    .put("prompt_ms", profile.getPromptTimeMs()).put("decode_ms", profile.getDecodeTimeMs())
                    .put("prompt_tokens", profile.getPromptTokens()).put("generated_tokens", profile.getGeneratedTokens())
                    .put("npu_verified", false).put("operator_coverage", "UNVERIFIED; requested backend and output are not operator-trace evidence")
                    .put("actions_executed", 0);
            return observation;
        } finally {
            synchronized (ownership) {
                activeHandle = 0; activeApi = null;
                cleanupUncertain = true; // A thrown cleanup must keep admission quarantined.
                int status = api.destroy(handle);
                // Nonzero semantics are undocumented here. Refuse repeat admission
                // conservatively; even zero is not observed hardware-release proof.
                cleanupUncertain = status != 0;
                if (observation != null) observation.put("destroy_return_status", status)
                        .put("destroy_status_semantics", "UNVERIFIED vendor return-code contract; nonzero or thrown cleanup quarantines this process")
                        .put("process_quarantined", cleanupUncertain);
            }
        }
    }
    private boolean finiteNonnegative(double value) { return Double.isFinite(value) && value >= 0; }
    private StructStat verifyModel(File model) throws Exception {
        // Android's legitimate /data/user/0 and /data/data aliases may be parent
        // symlinks. Compare against the trusted canonical own-files parent; lstat
        // below still rejects a symlink at the model leaf itself.
        File trustedTarget = new File(model.getParentFile().getCanonicalFile(), "qwen35.gguf");
        if (!model.getCanonicalFile().equals(trustedTarget)) throw new IllegalArgumentException("Model leaf symlinks are refused.");
        StructStat before = Os.lstat(model.getAbsolutePath());
        if (!OsConstants.S_ISREG(before.st_mode) || before.st_nlink != 1 || before.st_size != MODEL_BYTES)
            throw new IllegalArgumentException("Prepare the pinned qwen35.gguf in this package's private files; no model is bundled.");
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        long bytesRead = 0;
        try (FileInputStream stream = new FileInputStream(model)) {
            byte[] bytes = new byte[65536]; int count;
            while ((count = stream.read(bytes)) != -1) {
                checkCancelled(); bytesRead += count;
                if (bytesRead > MODEL_BYTES) throw new IllegalArgumentException("Model changed while reading.");
                digest.update(bytes, 0, count);
            }
        }
        StringBuilder sha = new StringBuilder();
        for (byte b : digest.digest()) sha.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        StructStat after = Os.lstat(model.getAbsolutePath());
        if (bytesRead != MODEL_BYTES || !MODEL_SHA.equals(sha.toString()) || !sameFile(before, after))
            throw new IllegalArgumentException("Pinned model checksum or stable-file identity failed.");
        return after;
    }
    private static boolean sameFile(StructStat a, StructStat b) {
        return a.st_dev == b.st_dev && a.st_ino == b.st_ino && a.st_size == b.st_size
                && a.st_mtime == b.st_mtime && a.st_ctime == b.st_ctime && a.st_nlink == b.st_nlink
                && a.st_mode == b.st_mode;
    }
}
