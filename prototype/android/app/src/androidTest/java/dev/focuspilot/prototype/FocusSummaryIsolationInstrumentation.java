package dev.focuspilot.prototype;

import android.app.Instrumentation;
import android.os.Bundle;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

/** Fixed-clock, in-memory checks against installed target classes; no repository or app data. */
public final class FocusSummaryIsolationInstrumentation extends Instrumentation {
    private static final int EXPECTED_CHECKS = 12;
    private int checks;
    private String failureType;
    private final List<String> failed = new ArrayList<>();

    private interface Check { boolean run(); }

    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments); start(); }

    private void expect(String id, Check check) {
        checks++;
        try {
            if (!check.run()) failed.add(id);
        } catch (Throwable failure) {
            failed.add(id);
            if (failureType == null) failureType = failure.getClass().getSimpleName();
        }
    }

    private static FocusStatusSummary.Snapshot summary(FocusSession session, long now) {
        return new FocusStatusSummary.Snapshot(session.isActive(), session.isCompleted(), false,
                session.elapsed(now), session.remainingMs(now), session.countdownTotalMs(),
                FocusStatusSummary.UNKNOWN, 300_000, 100, false, false);
    }

    private void fixtures() {
        expect("timed_target_recorded", () -> {
            FocusSession s = new FocusSession(); s.startTimed(1000, 20_000);
            return s.isActive() && s.countdownTotalMs() == 20_000 && s.remainingMs(1000) == 20_000;
        });
        expect("pause_preserves_target_and_remainder", () -> {
            FocusSession s = new FocusSession(); s.startTimed(1000, 20_000); s.pause(6000);
            return !s.isActive() && s.countdownTotalMs() == 20_000
                    && s.remainingMs(50_000) == 15_000 && s.elapsed(50_000) == 5000;
        });
        expect("resume_progress_excludes_pause_and_history", () -> {
            FocusSession s = new FocusSession(); s.restorePaused(90_000);
            s.startTimed(1000, 20_000); s.pause(6000); s.start(10_000);
            FocusStatusSummary.Snapshot snap = summary(s, 12_000);
            return snap.active && snap.elapsedMs == 97_000 && snap.remainingMs == 13_000
                    && snap.countdownTotalMs == 20_000 && snap.progressPercent() == 35;
        });
        expect("replacement_preserves_history_records_new_target", () -> {
            FocusSession s = new FocusSession(); s.restorePaused(90_000);
            s.startTimed(1000, 20_000); s.startTimed(6000, 10_000);
            return s.countdownTotalMs() == 10_000 && s.remainingMs(6000) == 10_000
                    && s.elapsed(6000) == 95_000 && summary(s, 6000).progressPercent() == 0;
        });
        expect("completion_keeps_target_and_reports_full_progress", () -> {
            FocusSession s = new FocusSession(); s.startTimed(1000, 20_000);
            boolean due = s.completeIfDue(50_000);
            FocusStatusSummary.Snapshot snap = summary(s, 50_000);
            return due && !snap.active && snap.completed && snap.elapsedMs == 20_000
                    && snap.remainingMs == 0 && snap.countdownTotalMs == 20_000
                    && snap.progressPercent() == 100;
        });
        expect("new_open_ended_run_clears_completed_target", () -> {
            FocusSession s = new FocusSession(); s.startTimed(1000, 2000);
            s.completeIfDue(5000); s.start(6000);
            FocusStatusSummary.Snapshot snap = summary(s, 7000);
            return snap.active && !snap.completed && !snap.hasCountdown()
                    && snap.countdownTotalMs == -1 && snap.progressPercent() == -1 && snap.elapsedMs == 3000;
        });
        expect("reset_clears_target_and_history", () -> {
            FocusSession s = new FocusSession(); s.startTimed(1000, 20_000); s.pause(6000); s.reset();
            return !s.isActive() && !s.isCompleted() && !s.isTimed()
                    && s.countdownTotalMs() == -1 && s.elapsed(50_000) == 0;
        });
        expect("legacy_recovery_preserves_remainder_unknown_target", () -> {
            FocusSession s = new FocusSession(); s.startTimed(0, 20_000);
            s.restorePaused(90_000, true, 5000, false);
            FocusStatusSummary.Snapshot snap = summary(s, 10_000);
            return !snap.active && !snap.completed && snap.elapsedMs == 90_000 && snap.remainingMs == 5000
                    && snap.countdownTotalMs == -1 && snap.progressPercent() == -1
                    && FocusStatusSummary.format(snap).contains("original duration of this saved countdown is unknown");
        });
        expect("recorded_target_recovers_paused_progress", () -> {
            FocusSession s = new FocusSession(); s.restorePaused(90_000, true, 5000, false, 20_000);
            FocusStatusSummary.Snapshot snap = summary(s, 10_000);
            return !snap.active && snap.remainingMs == 5000 && snap.elapsedMs == 90_000
                    && snap.countdownTotalMs == 20_000 && snap.progressPercent() == 75;
        });
        expect("malformed_target_drops_only_optional_metadata", () -> {
            for (long target : new long[]{-1, 0, 999, 4999, 7_200_001, Long.MAX_VALUE}) {
                FocusSession s = new FocusSession(); s.restorePaused(90_000, true, 5000, false, target);
                if (s.isActive() || s.isCompleted() || !s.isTimed() || s.countdownTotalMs() != -1
                        || s.elapsed(1000) != 90_000 || s.remainingMs(1000) != 5000) return false;
            }
            return true;
        });
        expect("target_validation_precedes_completed_normalization", () -> {
            FocusSession s = new FocusSession(); s.restorePaused(90_000, true, 5000, true, 1000);
            return !s.isActive() && s.isCompleted() && s.remainingMs(1000) == 0
                    && s.countdownTotalMs() == -1 && s.elapsed(1000) == 90_000;
        });
        expect("summary_admits_usage_and_past_cause_limits", () -> {
            FocusStatusSummary.Snapshot missing = new FocusStatusSummary.Snapshot(false, false, false,
                    90_000, -1, -1, -1, 300_000, 100, true, false);
            FocusStatusSummary.Snapshot saved = new FocusStatusSummary.Snapshot(false, false, false,
                    90_000, -1, -1, 5000, 300_000, 95, false, false);
            String absent = FocusStatusSummary.format(missing), old = FocusStatusSummary.format(saved);
            return absent.contains("App usage: unavailable") && absent.contains("needs Usage Access")
                    && absent.contains("No countdown is set. Focus is paused.")
                    && old.contains("App usage: 5s (saved)") && old.contains("95/100 virtual points")
                    && old.contains("does not identify the cause of an earlier reminder");
        });
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            fixtures();
            if (checks != EXPECTED_CHECKS) throw new AssertionError("Unexpected summary fixture inventory");
        } catch (Throwable failure) {
            if (failureType == null) failureType = failure.getClass().getSimpleName();
        }
        boolean passed = failureType == null && failed.isEmpty() && checks == EXPECTED_CHECKS;
        result.putBoolean("passed", passed);
        result.putInt("checks", checks);
        result.putString("failure_type", failureType);
        try {
            JSONObject report = new JSONObject();
            report.put("schema", "focuspilot.focus_summary_isolation.v1");
            report.put("passed", passed);
            report.put("checks", checks);
            report.put("expected_checks", EXPECTED_CHECKS);
            report.put("failed_fixture_ids", new JSONArray(failed));
            report.put("failure_type", failureType == null ? JSONObject.NULL : failureType);
            report.put("session_class", FocusSession.class.getName());
            report.put("summary_class", FocusStatusSummary.class.getName());
            report.put("scope", "Installed target pure classes; fixed synthetic clocks and in-memory objects only; no persistence, process recovery, UI, permission or model proof");
            report.put("actions_executed", 0);
            report.put("model_accessed", false);
            report.put("production_preferences_accessed", false);
            report.put("production_singleton_used", false);
            report.put("services_started", false);
            result.putString("report_json", report.toString());
            result.putString("stream", report.toString() + "\n");
        } catch (Throwable failure) {
            passed = false;
            result.putBoolean("passed", false);
            result.putString("failure_type", failure.getClass().getSimpleName());
            result.putString("stream", "Summary fixture report creation failed; checks=" + checks + "\n");
        }
        finish(passed ? -1 : 0, result);
    }
}
