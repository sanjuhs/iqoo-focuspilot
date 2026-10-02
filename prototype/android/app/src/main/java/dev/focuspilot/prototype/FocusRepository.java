package dev.focuspilot.prototype;

import android.app.AppOpsManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Process;
import android.os.SystemClock;
import org.json.JSONArray;
import java.util.ArrayList;
import java.util.Locale;

/** Single process owner for timer, usage accounting, cooldown and summaries. */
@android.annotation.SuppressLint("StaticFieldLeak") // Only an application context is retained; never an Activity.
public final class FocusRepository {
    private static FocusRepository instance;
    public final FocusSession session = new FocusSession();
    public final VirtualLedger ledger = new VirtualLedger();
    private final DecisionPolicy policy = new DecisionPolicy();
    private final Context context;
    public final SharedPreferences prefs;
    public String selectedPackage;
    public long budgetMs, accumulatedUsage, intervalWall;
    public boolean observe, interrupted;
    public final ArrayList<String> events = new ArrayList<>();
    public static synchronized FocusRepository get(Context context) {
        if(instance == null) instance = new FocusRepository(context.getApplicationContext());
        return instance;
    }
    private FocusRepository(Context context) {
        this.context = context; prefs = context.getSharedPreferences("focuspilot_research", Context.MODE_PRIVATE);
        selectedPackage = prefs.getString("package", "com.instagram.android"); budgetMs = Math.max(60_000, Math.min(7_200_000, prefs.getLong("budget", 300_000)));
        if(!MonitorConfig.valid(selectedPackage,budgetMs)) selectedPackage="com.instagram.android";
        observe = prefs.getBoolean("observe", false);
        session.restorePaused(prefs.getLong("elapsedCheckpoint", 0));
        accumulatedUsage = prefs.getLong("usageCheckpoint", 0);
        ledger.restore(prefs.getInt("points", 100), prefs.getLong("lastNudge", -1), SystemClock.elapsedRealtime());
        interrupted = prefs.getBoolean("activeCheckpoint", false);
        try { JSONArray saved = new JSONArray(prefs.getString("events", "[]")); for(int i=Math.max(0,saved.length()-30);i<saved.length();i++) events.add(saved.getString(i)); } catch(Exception ignored) {}
        if(interrupted) { log("Previous process ended; recovered last checkpoint as paused. Restart explicitly."); }
        persist();
    }
    public static boolean usageGranted(Context context) {
        AppOpsManager ops = (AppOpsManager) context.getSystemService(Context.APP_OPS_SERVICE);
        return ops.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.getPackageName()) == AppOpsManager.MODE_ALLOWED;
    }
    public long usage() {
        if(!observe || !session.isActive() || intervalWall<=0 || !usageGranted(context)) return accumulatedUsage;
        try { return accumulatedUsage + UsageReader.read(context, selectedPackage, intervalWall, System.currentTimeMillis()); }
        catch(SecurityException error) { return accumulatedUsage; }
    }
    public void start() {
        if(!session.isActive()) { intervalWall=System.currentTimeMillis(); session.start(SystemClock.elapsedRealtime()); interrupted=false; log("Focus session started / resumed"); }
        persist();
    }
    public void pause(String reason) {
        if(session.isActive()) { accumulatedUsage=usage(); session.pause(SystemClock.elapsedRealtime()); intervalWall=0; log(reason); }
        persist();
    }
    public void tick() {
        long now=SystemClock.elapsedRealtime();
        DecisionPolicy.Result decision=policy.evaluate(usage(),budgetMs,session.isActive() && observe && usageGranted(context),now,ledger.lastNudge());
        if(ledger.apply(decision,now)) log("LOCAL RULE: budget nudge · −5 virtual points; no money moved");
        persist();
    }
    public void reset() { session.reset(); accumulatedUsage=0; intervalWall=0; ledger.reset(); log("Session reset"); persist(); }
    public void setObservation(boolean enabled) {
        observe=enabled; accumulatedUsage=0; intervalWall=session.isActive() ? System.currentTimeMillis() : 0;
        prefs.edit().putBoolean("observe",enabled).apply(); log(enabled ? "Usage reading enabled locally" : "Usage reading disabled"); persist();
    }
    public void configure(String packageName,long budget) {
        if(!MonitorConfig.valid(packageName,budget)) throw new IllegalArgumentException("Invalid monitor configuration");
        selectedPackage=packageName; budgetMs=budget; accumulatedUsage=0; intervalWall=session.isActive() ? System.currentTimeMillis() : 0;
        prefs.edit().putString("package",packageName).putLong("budget",budget).apply(); log("Budget/settings saved; usage interval restarted"); persist();
    }
    public void log(String value) {
        events.add(new java.text.SimpleDateFormat("HH:mm:ss",Locale.US).format(new java.util.Date())+" · "+value);
        while(events.size()>30) events.remove(0);
        JSONArray saved=new JSONArray(); for(String event:events) saved.put(event); prefs.edit().putString("events",saved.toString()).apply();
    }
    public void persist() {
        prefs.edit().putLong("elapsedCheckpoint",session.elapsed(SystemClock.elapsedRealtime())).putBoolean("activeCheckpoint",session.isActive()).putLong("usageCheckpoint",usage()).putInt("points",ledger.points()).putLong("lastNudge",ledger.lastNudge()).apply();
    }
    public void delete() {
        session.reset(); accumulatedUsage=0; intervalWall=0; observe=false; interrupted=false; ledger.reset(); events.clear(); selectedPackage="com.instagram.android"; budgetMs=300_000; prefs.edit().clear().apply();
    }
}
