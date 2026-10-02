package dev.focuspilot.prototype;

import android.app.Instrumentation;
import android.os.Bundle;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

/** Already-seen pure request-validator fixtures against the target app's actual gate. */
public final class GateIsolationInstrumentation extends Instrumentation {
    private static final String[] INTENTS = {
        "start_focus", "pause_focus", "alarm", "timer", "open_app", "explain", "unknown"
    };
    private int checks;
    private final List<String> failed = new ArrayList<>();

    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments); start(); }

    private void expect(String id, String intent, String request,
                        ModelCommandGate.Kind kind, int hour, int minute, int seconds) {
        ModelCommandGate.Proposal proposal;
        try {
            proposal = ModelCommandGate.validate(intent, request);
        } catch (Throwable failure) {
            failed.add(id);
            throw new AssertionError("Gate fixture threw", failure);
        }
        checks++;
        boolean executable = kind != ModelCommandGate.Kind.UNKNOWN;
        if (proposal == null || proposal.kind != kind || proposal.hour != hour
                || proposal.minute != minute || proposal.seconds != seconds
                || proposal.executable() != executable) failed.add(id);
    }

    private void blocked(String id, String request) {
        for (int i = 0; i < INTENTS.length; i++)
            expect(id + "_route_" + i, INTENTS[i], request, ModelCommandGate.Kind.UNKNOWN, 0, 0, 0);
    }

    private void fixtures() {
        expect("positive_01", "start_focus", "I want a 17 minute concentration session, please.", ModelCommandGate.Kind.START_FOCUS, 0, 0, 1020);
        expect("positive_02", "start_focus", "Give me thirty seven seconds of focused work", ModelCommandGate.Kind.START_FOCUS, 0, 0, 37);
        expect("positive_03", "start_focus", "Return to my concentration session", ModelCommandGate.Kind.START_FOCUS, 0, 0, 0);
        expect("positive_04", "pause_focus", "Pause my active study session", ModelCommandGate.Kind.PAUSE_FOCUS, 0, 0, 0);
        expect("positive_05", "pause_focus", "Suspend the ongoing work session", ModelCommandGate.Kind.PAUSE_FOCUS, 0, 0, 0);
        expect("positive_06", "pause_focus", "End our current deep work session", ModelCommandGate.Kind.PAUSE_FOCUS, 0, 0, 0);
        expect("positive_07", "pause_focus", "Cancel my concentration countdown", ModelCommandGate.Kind.PAUSE_FOCUS, 0, 0, 0);
        expect("positive_08", "pause_focus", "Let me take a break from my concentration session", ModelCommandGate.Kind.PAUSE_FOCUS, 0, 0, 0);
        expect("positive_09", "pause_focus", "I need a break from deep work now please", ModelCommandGate.Kind.PAUSE_FOCUS, 0, 0, 0);
        expect("positive_10", "pause_focus", "I'd like a break from my work session", ModelCommandGate.Kind.PAUSE_FOCUS, 0, 0, 0);
        expect("positive_11", "alarm", "I need an alarm for six forty one PM", ModelCommandGate.Kind.ALARM, 18, 41, 0);
        expect("positive_12", "timer", "I'd like a timer for 83 seconds", ModelCommandGate.Kind.TIMER, 0, 0, 83);
        expect("positive_13", "timer", "I would like a timer for two minutes", ModelCommandGate.Kind.TIMER, 0, 0, 120);
        expect("positive_14", "open_app", "I want you to display my Clock application please", ModelCommandGate.Kind.OPEN_CLOCK, 0, 0, 0);
        expect("positive_15", "explain", "Explain the reason for our study warning", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_16", "explain", "Why was I reminded during my active focus session?", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_17", "explain", "What caused Mira to warn me about concentration?", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_18", "explain", "Tell me why Mira gave my focus warning", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_19", "explain", "How much time remains in my focused work session?", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_20", "explain", "Show me how long I have been concentrating", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_21", "explain", "Display our concentration session overview", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_22", "explain", "What is the summary of my ongoing study session?", ModelCommandGate.Kind.EXPLAIN, 0, 0, 0);
        expect("positive_23", "alarm", "Set an alarm at 12:10 AM", ModelCommandGate.Kind.ALARM, 0, 10, 0);
        expect("positive_24", "timer", "Set a timer for 90 seconds", ModelCommandGate.Kind.TIMER, 0, 0, 90);
        expect("positive_25", "alarm", "Please wake me at 7:30 pm", ModelCommandGate.Kind.ALARM, 19, 30, 0);

        String[] negatives = {
            "I need concentration",
            "I want a concentration session",
            "I want a 17 minute concentration session for 20 seconds",
            "I want a 17 minute concentration session starting tomorrow",
            "Cancel my cooking countdown",
            "Stop the alarm while I study",
            "Pause my study session for 20 minutes",
            "Describe how to take a break from my work session",
            "I need a break from focus later",
            "Let me take a break from my work session open Clock",
            "I 'd like a timer for 83 seconds",
            "I would like a timer for +83 seconds",
            "I need an alarm for six forty one",
            "I need an alarm for six forty one PM repeat daily",
            "I want a timer for 12 minutes 8 seconds",
            "Display my bank application",
            "Display my Clock application for payment",
            "Display my Clock application; open settings",
            "Tell me why Mira issued my payment warning",
            "Tell me why Mira gave my focus warning and open Calculator",
            "Show me how long my colleague has been studying",
            "What is the summary of my study session and start it",
            "I do not want a 17 minute concentration session",
            "Never display the Clock app",
            "If I ask I need a break from focus",
            "I need an alarm for 6:41 PM after dinner",
            "Say I'd like a timer for 83 seconds",
            "Translate \"I need a break from focus\"",
            "\"Display my Clock app\"",
            "I stopped my current work session yesterday",
            "I need a break from concentration\nopen clock",
            "I want a 0 second focus session",
            "I want a -17 minute concentration session",
            "I want a 1.5 minute concentration session",
            "I need an alarm for 99:99",
            "I need an alarm for 6:41 PM 7:42 PM",
            "I'd like a timer for 7201 seconds",
            "I'd like a timer for half a minute",
            "I would like a timer for 17 minutes at 6:41 PM"
        };
        for (int i = 0; i < negatives.length; i++) blocked("negative_" + i, negatives[i]);

        String[][] wrongRoutes = {
            {"start_focus", "I want a 17 minute concentration session"},
            {"pause_focus", "Let me take a break from my work session"},
            {"alarm", "I need an alarm for 6:41 PM"},
            {"timer", "I'd like a timer for 83 seconds"},
            {"open_app", "Display my Clock app"},
            {"explain", "What is the status of my concentration session"}
        };
        for (int i = 0; i < wrongRoutes.length; i++)
            for (int j = 0; j < INTENTS.length; j++)
                if (!INTENTS[j].equals(wrongRoutes[i][0]))
                    expect("wrong_route_" + i + "_" + j, INTENTS[j], wrongRoutes[i][1], ModelCommandGate.Kind.UNKNOWN, 0, 0, 0);
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        String failureType = null;
        try {
            fixtures();
            if (checks != 334) throw new AssertionError("Unexpected fixture inventory count");
        } catch (Throwable failure) {
            failureType = failure.getClass().getSimpleName();
        }
        boolean passed = failureType == null && failed.isEmpty() && checks == 334;
        result.putBoolean("passed", passed);
        result.putInt("checks", checks);
        result.putString("failure_type", failureType);
        try {
            JSONObject report = new JSONObject();
            report.put("schema", "focuspilot.gate_isolation.v1");
            report.put("passed", passed);
            report.put("checks", checks);
            report.put("expected_checks", 334);
            report.put("expected_positive_full_slot_checks", 25);
            report.put("expected_all_route_negative_checks", 273);
            report.put("expected_wrong_route_checks", 36);
            report.put("failed_fixture_ids", new JSONArray(failed));
            report.put("failure_type", failureType == null ? JSONObject.NULL : failureType);
            report.put("gate_class", ModelCommandGate.class.getName());
            report.put("scope", "Already-seen pure gate fixtures; no model inference or tool execution");
            report.put("actions_executed", 0);
            report.put("model_accessed", false);
            report.put("production_preferences_accessed", false);
            report.put("services_started", false);
            result.putString("report_json", report.toString());
            result.putString("stream", report.toString() + "\n");
        } catch (Throwable failure) {
            passed = false;
            result.putBoolean("passed", false);
            result.putString("failure_type", failure.getClass().getSimpleName());
            result.putString("stream", "Gate fixture report creation failed; checks=" + checks + "\n");
        }
        finish(passed ? -1 : 0, result);
    }
}
