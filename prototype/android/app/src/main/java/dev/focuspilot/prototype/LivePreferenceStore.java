package dev.focuspilot.prototype;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

/** Private manual labels from real complete summaries. Never reads the practice sandbox. */
public final class LivePreferenceStore {
    public static final String STORE="focuspilot_live_preferences";
    private static final String RECORDS="records_v1";
    private final SharedPreferences preferences;
    private final LivePreferencePolicy policy=new LivePreferencePolicy();
    private boolean healthy=true;
    private String notice="";
    public LivePreferenceStore(Context context) {
        preferences=context.getApplicationContext().getSharedPreferences(STORE,Context.MODE_PRIVATE);
        load();
    }
    public boolean enabled() { return healthy&&preferences.getBoolean("enabled",false); }
    public String notice() { return notice; }
    public List<LivePreferencePolicy.Record> records() { return policy.records(); }
    public int scopedCount(LivePreferenceScope scope) {
        int count=0;for(LivePreferencePolicy.Record record:policy.records()) if(record.scope.equals(scope))count++;
        return count;
    }
    public boolean setEnabled(boolean value) {
        if(value&&!healthy){notice="Saved live labels are unreadable. Delete them to reset before enabling.";return false;}
        boolean saved=preferences.edit().putBoolean("enabled",value).commit();
        if(!saved)quarantine();
        notice=saved?(value?"Matched Allow labels may skip budget nudges; unavailable matches use the normal rule.":"Live label matching disabled."):"Could not confirm the preference. Matching is off in this process; reset live labels before enabling.";
        return saved;
    }
    public LivePreferencePolicy.Decision evaluate(LivePreferenceScope scope,ObservationSnapshot snapshot,
            LivePreferencePolicy.Gates gates,long nowElapsed) {
        return policy.evaluate(scope,snapshot,gates,nowElapsed);
    }
    public LivePreferencePolicy.Record save(LivePreferenceScope scope,ObservationSnapshot snapshot,LivePreferencePolicy.Label label,
            LivePreferencePolicy.Gates gates,long nowElapsed) {
        if(!healthy) throw new IllegalArgumentException("Saved live labels are unreadable; reset first.");
        List<LivePreferencePolicy.Record> before=policy.records();
        LivePreferencePolicy.Record record=policy.save(scope,snapshot,label,gates,nowElapsed);
        if(!persist()){policy.restore(before);quarantine();throw new IllegalStateException("Saving could not be confirmed. Matching stays off until you reset live labels.");}
        notice="Saved your real-summary label privately.";return record;
    }
    public boolean delete(long id) {
        List<LivePreferencePolicy.Record> before=policy.records();
        if(!policy.delete(id))return false;
        if(!persist()){policy.restore(before);quarantine();return false;}
        notice="Live label deleted.";return true;
    }
    public boolean clear() {
        if(!preferences.edit().remove(RECORDS).putBoolean("enabled",false).commit()){quarantine();notice="Could not confirm deletion of live labels. Matching is off in this process; retry deletion before enabling.";return false;}
        policy.clear();healthy=true;notice="Live labels deleted; matching switched off.";return true;
    }
    private void load() {
        try {
            String raw=preferences.getString(RECORDS,null);if(raw==null)return;
            if(raw.length()>80_000)throw new IllegalArgumentException("Oversized live cache");
            JSONObject envelope=new JSONObject(raw);
            if(envelope.getInt("schema")!=LivePreferenceScope.SCHEMA)throw new IllegalArgumentException("Unknown schema");
            JSONArray entries=envelope.getJSONArray("records");
            if(entries.length()>LivePreferencePolicy.MAX_RECORDS)throw new IllegalArgumentException("Too many records");
            List<LivePreferencePolicy.Record> loaded=new ArrayList<>();
            for(int i=0;i<entries.length();i++) {
                JSONObject entry=entries.getJSONObject(i),s=entry.getJSONObject("scope");
                if(s.getInt("schema")!=LivePreferenceScope.SCHEMA || !ObservationSnapshot.MAPPING_VERSION.equals(s.getString("mapping")))throw new IllegalArgumentException("Unknown mapping");
                LivePreferenceScope scope=new LivePreferenceScope(s.getString("package"),s.getLong("budget_ms"),s.getLong("continuous_ms"),s.getLong("planned_ms"),s.getString("goal_sha256"));
                if(!scope.fingerprint().equals(s.getString("fingerprint")))throw new IllegalArgumentException("Scope fingerprint differs");
                JSONArray vector=entry.getJSONArray("features");if(vector.length()!=6)throw new IllegalArgumentException("Six features required");
                double[] values=new double[6];for(int j=0;j<6;j++)values[j]=vector.getDouble(j);
                loaded.add(new LivePreferencePolicy.Record(entry.getLong("id"),scope,values,LivePreferencePolicy.Label.valueOf(entry.getString("label")),
                    entry.getLong("observed_wall"),entry.getLong("observed_elapsed"),entry.getLong("labeled_elapsed"),entry.getString("provenance")));
            }
            policy.restore(loaded);
        } catch(Exception error) { healthy=false;policy.clear();notice="Saved live labels are unreadable. Matching stays off; delete live labels to reset. The original cache was left untouched."; }
    }
    private void quarantine() {
        healthy=false;
        preferences.edit().putBoolean("enabled",false).commit();
        notice="Saving could not be confirmed; live matching is disabled in this process. Reset the live cache before enabling again.";
    }
    private boolean persist() {
        try {
            JSONArray records=new JSONArray();
            for(LivePreferencePolicy.Record record:policy.records()) {
                LivePreferenceScope scope=record.scope;
                JSONObject s=new JSONObject().put("schema",scope.schema).put("mapping",scope.mappingVersion)
                    .put("package",scope.selectedPackage).put("budget_ms",scope.budgetMs).put("continuous_ms",scope.continuousLimitMs)
                    .put("planned_ms",scope.plannedFocusMs).put("goal_sha256",scope.goalSHA256).put("fingerprint",scope.fingerprint());
                JSONArray vector=new JSONArray();for(double value:record.features())vector.put(value);
                records.put(new JSONObject().put("id",record.id).put("label",record.label.name()).put("scope",s).put("features",vector)
                    .put("observed_wall",record.observedAtWall).put("observed_elapsed",record.observedAtElapsed)
                    .put("labeled_elapsed",record.labeledAtElapsed).put("provenance",record.provenance));
            }
            JSONObject envelope=new JSONObject().put("schema",LivePreferenceScope.SCHEMA).put("records",records);
            return preferences.edit().putString(RECORDS,envelope.toString()).commit();
        } catch(Exception error) { notice="Live labels could not be saved.";return false; }
    }
}
