package dev.focuspilot.qualcomm.research;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Process;
import android.system.Os;
import android.system.OsConstants;
import android.view.View;
import android.view.WindowInsets;
import android.widget.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONObject;

/** Private pre-event hardware diagnostic. No model/actions/permissions start automatically. */
public final class ProbeActivity extends Activity {
    private final ProbeLifecycle lifecycle = new ProbeLifecycle();
    private final ProcessProbeOwner processOwner = ProcessProbeOwner.shared();
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());
    private boolean foreground, waitingForOther;
    private final Runnable controlTick = new Runnable() {
        public void run() { if (foreground) { updateControls(); ui.postDelayed(this, 500); } }
    };
    private HardwareGate.Assessment hardware;
    private Spinner compute, request;
    private Button run, cancel;
    private TextView status, output;
    private volatile NativeProbe activeProbe;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        long pageSize = -1;
        try { pageSize = Os.sysconf(OsConstants._SC_PAGESIZE); } catch (Exception ignored) { /* Refuse unknown. */ }
        // Public platform-only checks. Do not construct/access the vendor SDK here.
        hardware = HardwareGate.assess(Build.VERSION.SDK_INT, Build.SOC_MODEL,
                Build.SUPPORTED_ABIS.length == 0 ? "" : Build.SUPPORTED_ABIS[0], Process.is64Bit(), pageSize);
        LinearLayout column = new LinearLayout(this); column.setOrientation(LinearLayout.VERTICAL);
        int padding = dp(20); column.setPadding(padding, padding, padding, padding);
        column.setOnApplyWindowInsetsListener((view, insets) -> {
            android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            view.setPadding(padding + bars.left, padding + bars.top, padding + bars.right, padding + bars.bottom);
            return insets;
        });
        ScrollView scroll = new ScrollView(this); scroll.addView(column); setContentView(scroll);
        addText(column, "GenieX private research probe", 24);
        addText(column, "PRE-EVENT diagnostic, separate from Mira. No phone action executor, microphone, observation, network, services or bundled model. CPU/NPU/hybrid are requested settings, never proof of hardware execution.", 16);
        addText(column, "SoC: " + Build.SOC_MODEL + " · API " + Build.VERSION.SDK_INT + " · pages " + pageSize + "\n" + hardware.reason, 16);
        addText(column, "Model preparation is separate: this package's private files/qwen35.gguf must exactly match the pinned 563,036,064-byte Q4_0 model. Run verifies the entire checksum; nothing is copied/downloaded automatically.", 16);
        compute = new Spinner(this);
        compute.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"Select requested backend", "cpu", "npu", "hybrid"})); column.addView(compute);
        request = new Spinner(this);
        request.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, SyntheticCases.labels()));
        column.addView(request);
        run = new Button(this); run.setText("Run one synthetic request"); column.addView(run);
        cancel = new Button(this); cancel.setText("Cancel and discard result"); column.addView(cancel);
        status = addText(column, "Idle. Select a backend; running is always explicit.", 16);
        output = addText(column, "No observations yet. NPU verification requires correlated executed-operator traces; these profiling values alone are insufficient.", 14);
        output.setTextIsSelectable(true);
        run.setOnClickListener(v -> startExplicit()); cancel.setOnClickListener(v -> cancelExplicit());
        compute.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) { updateControls(); }
            public void onNothingSelected(AdapterView<?> parent) { updateControls(); }
        });
        updateControls();
    }
    @Override protected void onStart() {
        super.onStart(); foreground = true; lifecycle.enterForeground();
        waitingForOther = processOwner.isBusy() && !lifecycle.isBusy();
        if (waitingForOther) status.setText("A previous screen's native worker is still cleaning up. No new run is admitted until it releases its handle.");
        updateControls(); ui.post(controlTick);
    }
    @Override protected void onStop() {
        foreground = false; ui.removeCallbacks(controlTick); lifecycle.leaveForeground(); cancelNative();
        status.setText("Backgrounded: in-flight work was cancelled and its output discarded. Returning never reruns it.");
        super.onStop();
    }
    @Override protected void onDestroy() { cancelNative(); worker.shutdown(); super.onDestroy(); }

    private void startExplicit() {
        String mode = compute.getSelectedItemPosition() == 0 ? null : compute.getSelectedItem().toString();
        ProbeLifecycle.Request ticket = lifecycle.begin(hardware, mode);
        if (ticket == null) { status.setText(hardware.allowed ? "Select an explicit backend and wait for previous cleanup." : hardware.reason); return; }
        ProcessProbeOwner.Lease lease = processOwner.acquire();
        if (lease == null) {
            lifecycle.cancel(); lifecycle.finish(ticket); waitingForOther = true;
            status.setText("Another screen's worker still owns native cleanup. Wait; nothing was initialized.");
            updateControls(); return;
        }
        int selectedCase = request.getSelectedItemPosition();
        status.setText("Checking private model, then requesting " + mode + ". Output is diagnostic only.");
        output.setText("No current result. Requested " + mode + "; NPU execution remains unverified.");
        updateControls();
        worker.execute(() -> {
            JSONObject result = null; String failure = null;
            NativeProbe probe = null;
            try {
                if (!lifecycle.mayStart(ticket)) throw new InterruptedException("Cancelled before worker entry.");
                probe = new NativeProbe(); activeProbe = probe;
                // Covers cancellation between admission and publishing the probe reference.
                if (!lifecycle.mayStart(ticket)) { probe.cancel(); throw new InterruptedException("Cancelled before model initialization."); }
                result = probe.run(getApplicationContext(), mode, selectedCase);
            } catch (Throwable error) { failure = error.getClass().getSimpleName() + ": " + String.valueOf(error.getMessage()); }
            finally {
                activeProbe = null; lifecycle.finish(ticket);
                if (probe != null && probe.requiresQuarantine()) processOwner.quarantine(lease);
                else processOwner.release(lease);
            }
            JSONObject observed = result; String failed = failure;
            runOnUiThread(() -> {
                if (isFinishing() || isDestroyed()) return;
                if (lifecycle.mayDeliver(ticket)) {
                    status.setText(observed == null ? "Probe failed; no actions occurred. " + failed : "Diagnostic completed. Requested backend is not NPU proof; no actions occurred.");
                    if (observed != null) output.setText(observed.toString());
                }
                updateControls();
            });
        });
    }
    private void cancelExplicit() {
        lifecycle.cancel(); cancelNative();
        status.setText("Cancelled; result discarded. Native prefill/model creation may finish before cleanup; no new request starts until that worker releases its handle.");
        updateControls();
    }
    private void cancelNative() {
        NativeProbe probe = activeProbe;
        // stopStream may need the native ownership lock; never block the main thread on it.
        if (probe != null) probe.cancel();
    }
    private void updateControls() {
        if (run == null || compute == null || cancel == null) return;
        boolean busy = lifecycle.isBusy();
        boolean globalBusy = processOwner.isBusy();
        if (processOwner.isQuarantined())
            status.setText("Native cleanup returned an unverified nonzero status or threw. This process is quarantined: restart the app process before any new probe. No actions occurred.");
        if (waitingForOther && !globalBusy && !busy) {
            waitingForOther = false;
            status.setText("Previous worker cleanup finished. Select a backend and explicitly Run; no old output is replayed.");
        }
        run.setEnabled(hardware.allowed && !busy && !globalBusy && compute.getSelectedItemPosition() > 0);
        cancel.setEnabled(busy); compute.setEnabled(!busy && !globalBusy); request.setEnabled(!busy && !globalBusy);
    }
    private TextView addText(LinearLayout parent, String text, int size) {
        TextView view = new TextView(this); view.setText(text); view.setTextSize(size);
        view.setPadding(0, dp(8), 0, dp(8)); parent.addView(view); return view;
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}
