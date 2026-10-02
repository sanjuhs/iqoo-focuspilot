package dev.focuspilot.prototype;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Whitelisted private export. No file, network, Android or repository access. */
public final class FocusDataExport {
    public static final int SCHEMA = 1;
    public static final int MAX_RECORDS = 32;
    public static final int MAX_BYTES = 80_000;
    public static final String MAPPING = "selected-events-v1";
    public static final String PROVENANCE = "REAL_OBSERVATION";
    private static final long DAY_MS = 86_400_000;
    private static final long MAX_TIME = 9_007_199_254_740_991L;
    private FocusDataExport() {}

    public enum Label { ALLOW, NUDGE }

    public static final class Settings {
        public final String selectedPackage, goalSHA256;
        public final long budgetMs, continuousLimitMs, plannedFocusMs;
        public final boolean observationEnabled, liveMatchingEnabled;
        public Settings(String selectedPackage, long budgetMs, long continuousLimitMs,
                        long plannedFocusMs, String goalSHA256,
                        boolean observationEnabled, boolean liveMatchingEnabled) {
            require(selectedPackage != null && selectedPackage.length() <= 255 &&
                    selectedPackage.matches("[A-Za-z][A-Za-z0-9_]*(?:\\.[A-Za-z][A-Za-z0-9_]*)+"), "Invalid selected package");
            require(budgetMs >= 60_000 && budgetMs <= 7_200_000, "Invalid budget");
            require(continuousLimitMs >= 0 && continuousLimitMs <= DAY_MS &&
                    plannedFocusMs >= 0 && plannedFocusMs <= DAY_MS, "Invalid declared limits");
            require(goalSHA256 != null && goalSHA256.matches("[0-9a-f]{64}"), "Goal hash required; no plaintext goal");
            this.selectedPackage = selectedPackage;
            this.budgetMs = budgetMs;
            this.continuousLimitMs = continuousLimitMs;
            this.plannedFocusMs = plannedFocusMs;
            this.goalSHA256 = goalSHA256;
            this.observationEnabled = observationEnabled;
            this.liveMatchingEnabled = liveMatchingEnabled;
        }
    }

    public static final class Record {
        public final long id, observedAtWall, observedAtElapsed, labeledAtElapsed;
        public final Settings context;
        public final Label label;
        private final double[] values;
        public Record(long id, Settings context, double[] features, Label label,
                      long observedAtWall, long observedAtElapsed, long labeledAtElapsed,
                      String provenance) {
            require(id > 0 && id <= MAX_TIME && context != null && label != null, "Invalid record identity/context");
            require(PROVENANCE.equals(provenance), "Only real-observation records may be exported");
            require(context.continuousLimitMs > 0 && context.plannedFocusMs > 0, "Complete live limits required");
            require(observedAtWall > 0 && observedAtWall <= MAX_TIME && observedAtElapsed >= 0 &&
                    labeledAtElapsed <= MAX_TIME && labeledAtElapsed >= observedAtElapsed &&
                    labeledAtElapsed - observedAtElapsed <= 15_000, "Invalid observation/label timestamps");
            require(features != null && features.length == 6, "Six features required");
            values = features.clone();
            for (double value : values) require(Double.isFinite(value) && value >= 0 && value <= 1, "Features must be finite and within 0..1");
            this.id = id;
            this.context = context;
            this.label = label;
            this.observedAtWall = observedAtWall;
            this.observedAtElapsed = observedAtElapsed;
            this.labeledAtElapsed = labeledAtElapsed;
        }
        public double[] features() { return values.clone(); }
    }

    public static final class Snapshot {
        public final long exportedAtWall, focusElapsedMs;
        public final int virtualPoints;
        public final boolean focusActive;
        public final Settings settings;
        private final List<Record> records;
        public Snapshot(long exportedAtWall, Settings settings, int virtualPoints,
                        long focusElapsedMs, boolean focusActive, List<Record> records) {
            require(exportedAtWall > 0 && exportedAtWall <= MAX_TIME && settings != null, "Invalid export time/settings");
            require(virtualPoints >= 0 && virtualPoints <= 100 && focusElapsedMs >= 0 && focusElapsedMs <= MAX_TIME, "Invalid focus/virtual balance");
            require(records != null && records.size() <= MAX_RECORDS, "At most 32 records required");
            Set<Long> ids = new HashSet<>();
            List<Record> copy = new ArrayList<>();
            for (Record record : records) {
                require(record != null && ids.add(record.id), "Null or duplicate record");
                require(settings.selectedPackage.equals(record.context.selectedPackage), "Other app records must be omitted by caller");
                require(record.observedAtWall <= exportedAtWall, "Observation cannot be after export time");
                copy.add(record);
            }
            this.exportedAtWall = exportedAtWall;
            this.settings = settings;
            this.virtualPoints = virtualPoints;
            this.focusElapsedMs = focusElapsedMs;
            this.focusActive = focusActive;
            this.records = Collections.unmodifiableList(copy);
        }
        public List<Record> records() { return records; }
    }

    /** All-or-nothing renderer. Caller must not open a destination before validation. */
    public static byte[] render(Snapshot snapshot) {
        require(snapshot != null, "Snapshot required");
        StringBuilder json = new StringBuilder(24_000);
        json.append("{\"schema\":").append(SCHEMA)
                .append(",\"kind\":\"focuspilot-private-summary\",\"research_only\":true")
                .append(",\"exported_at_wall_ms\":").append(snapshot.exportedAtWall)
                .append(",\"selected_package\":").append(quote(snapshot.settings.selectedPackage))
                .append(",\"settings\":");
        appendContext(json, snapshot.settings);
        json.append(",\"observation_enabled\":").append(snapshot.settings.observationEnabled)
                .append(",\"live_matching_enabled\":").append(snapshot.settings.liveMatchingEnabled)
                .append(",\"virtual_points\":").append(snapshot.virtualPoints)
                .append(",\"money_moved\":false,\"focus_elapsed_ms\":").append(snapshot.focusElapsedMs)
                .append(",\"focus_active\":").append(snapshot.focusActive)
                .append(",\"records\":[");
        for (int index = 0; index < snapshot.records.size(); index++) {
            Record record = snapshot.records.get(index);
            if (index > 0) json.append(',');
            json.append("{\"id\":").append(record.id)
                    .append(",\"label\":").append(quote(record.label.name()))
                    .append(",\"provenance\":").append(quote(PROVENANCE))
                    .append(",\"context\":");
            appendContext(json, record.context);
            json.append(",\"observed_at_wall_ms\":").append(record.observedAtWall)
                    .append(",\"observed_at_elapsed_ms\":").append(record.observedAtElapsed)
                    .append(",\"labeled_at_elapsed_ms\":").append(record.labeledAtElapsed)
                    .append(",\"features\":[");
            for (int feature = 0; feature < 6; feature++) {
                if (feature > 0) json.append(',');
                json.append(Double.toString(record.values[feature]));
            }
            json.append("]}");
        }
        json.append("]}\n");
        byte[] result = json.toString().getBytes(StandardCharsets.UTF_8);
        require(result.length <= MAX_BYTES, "Export exceeds 80,000 UTF-8 bytes");
        return result;
    }

    private static void appendContext(StringBuilder json, Settings settings) {
        json.append("{\"mapping\":").append(quote(MAPPING))
                .append(",\"budget_ms\":").append(settings.budgetMs)
                .append(",\"continuous_limit_ms\":").append(settings.continuousLimitMs)
                .append(",\"planned_focus_ms\":").append(settings.plannedFocusMs)
                .append(",\"goal_sha256\":").append(quote(settings.goalSHA256)).append('}');
    }

    /** JSON string escaping; internal/package-visible for independent JVM tests. */
    static String quote(String text) {
        require(text != null, "String required");
        StringBuilder quoted = new StringBuilder("\"");
        for (int index = 0; index < text.length(); index++) {
            char c = text.charAt(index);
            if (Character.isHighSurrogate(c)) {
                require(index + 1 < text.length() && Character.isLowSurrogate(text.charAt(index + 1)), "Unpaired Unicode surrogate");
                unicodeEscape(quoted, c); unicodeEscape(quoted, text.charAt(++index));
            } else {
                require(!Character.isLowSurrogate(c), "Unpaired Unicode surrogate");
                switch (c) {
                    case '"': quoted.append("\\\""); break;
                    case '\\': quoted.append("\\\\"); break;
                    case '\b': quoted.append("\\b"); break;
                    case '\f': quoted.append("\\f"); break;
                    case '\n': quoted.append("\\n"); break;
                    case '\r': quoted.append("\\r"); break;
                    case '\t': quoted.append("\\t"); break;
                    default: if (c < 0x20 || c > 0x7e) unicodeEscape(quoted, c); else quoted.append(c);
                }
            }
        }
        return quoted.append('"').toString();
    }
    private static void unicodeEscape(StringBuilder out, char value) {
        out.append("\\u");
        for (int shift = 12; shift >= 0; shift -= 4) out.append("0123456789abcdef".charAt((value >>> shift) & 15));
    }
    private static void require(boolean valid, String reason) {
        if (!valid) throw new IllegalArgumentException(reason);
    }
}
