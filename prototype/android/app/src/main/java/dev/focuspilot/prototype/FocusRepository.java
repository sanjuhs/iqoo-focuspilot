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
    /** Explicit user limits; zero means unknown, never an inferred default. */
    public long shadowContinuousLimitMs, shadowPlannedFocusMs;
    public boolean observe, interrupted;
    private long shadowScopeId, shadowSinceWall, shadowStartedElapsed, focusActiveStartedElapsed;
    private final ScopedNudgeFeedback shadowFeedback=new ScopedNudgeFeedback();
    private ObservationSnapshot latestSnapshot;
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
        shadowContinuousLimitMs=validShadowLimit(prefs.getLong("shadowContinuousLimit",0));
        shadowPlannedFocusMs=validShadowLimit(prefs.getLong("shadowPlannedFocus",0));
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
        if(!session.isActive()) { intervalWall=System.currentTimeMillis(); focusActiveStartedElapsed=SystemClock.elapsedRealtime(); session.start(focusActiveStartedElapsed); interrupted=false; beginShadowScope(); log("Focus session started / resumed"); }
        persist();
    }
    public void pause(String reason) {
        if(session.isActive()) { accumulatedUsage=usage(); session.pause(SystemClock.elapsedRealtime()); intervalWall=0; invalidateShadowScope(); log(reason); }
        persist();
    }
    public void tick() {
        long now=SystemClock.elapsedRealtime();
        DecisionPolicy.Result decision=policy.evaluate(usage(),budgetMs,session.isActive() && observe && usageGranted(context),now,ledger.lastNudge());
        boolean nudged=ledger.apply(decision,now);
        if(nudged) log("LOCAL RULE: budget nudge · −5 virtual points; no money moved");
        refreshShadowObservation();
        if(nudged && shadowSinceWall>0) shadowFeedback.recordActualNudge(now);
        persist();
    }
    public void reset() { session.reset(); accumulatedUsage=0; intervalWall=0; ledger.reset(); invalidateShadowScope(); log("Session reset"); persist(); }
    public void setObservation(boolean enabled) {
        observe=enabled; accumulatedUsage=0; intervalWall=session.isActive() ? System.currentTimeMillis() : 0;
        beginShadowScope();
        prefs.edit().putBoolean("observe",enabled).apply(); log(enabled ? "Usage reading enabled locally" : "Usage reading disabled"); persist();
    }
    public void configure(String packageName,long budget) {
        if(!MonitorConfig.valid(packageName,budget)) throw new IllegalArgumentException("Invalid monitor configuration");
        selectedPackage=packageName; budgetMs=budget; accumulatedUsage=0; intervalWall=session.isActive() ? System.currentTimeMillis() : 0;
        shadowContinuousLimitMs=0;shadowPlannedFocusMs=0;
        prefs.edit().remove("shadowContinuousLimit").remove("shadowPlannedFocus").apply();beginShadowScope();
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
        session.reset(); accumulatedUsage=0; intervalWall=0; observe=false; interrupted=false; ledger.reset(); events.clear(); selectedPackage="com.instagram.android"; budgetMs=300_000;
        shadowContinuousLimitMs=0;shadowPlannedFocusMs=0;invalidateShadowScope();prefs.edit().clear().apply();
    }
    private static long validShadowLimit(long value) { return value>=0 && value<=86_400_000?value:0; }
    /** Saves declared limits only. No model weights, observed vectors or event stream are saved. */
    public void configureShadowLimits(long continuousMs,long plannedFocusMs) {
        if(validShadowLimit(continuousMs)!=continuousMs || validShadowLimit(plannedFocusMs)!=plannedFocusMs)
            throw new IllegalArgumentException("Shadow limits must be 0 (unknown) or at most 24 hours");
        shadowContinuousLimitMs=continuousMs;shadowPlannedFocusMs=plannedFocusMs;
        prefs.edit().putLong("shadowContinuousLimit",continuousMs).putLong("shadowPlannedFocus",plannedFocusMs).apply();
        beginShadowScope();
    }
    private void invalidateShadowScope() {
        shadowScopeId++;shadowSinceWall=0;shadowStartedElapsed=0;latestSnapshot=null;shadowFeedback.reset();
    }
    private void beginShadowScope() {
        invalidateShadowScope();
        if(observe && session.isActive() && usageGranted(context)) {
            shadowSinceWall=System.currentTimeMillis();shadowStartedElapsed=SystemClock.elapsedRealtime();
        }
    }
    /** Called by existing visible dashboard/service ticks, with the existing consent gates. */
    public void refreshShadowObservation() {
        if(!observe || !session.isActive() || !usageGranted(context)) { if(shadowSinceWall>0) invalidateShadowScope();return; }
        if(shadowSinceWall<=0) beginShadowScope();
        long nowWall=System.currentTimeMillis(), nowElapsed=SystemClock.elapsedRealtime();
        SelectedAppObservation.Summary summary=UsageReader.observe(context,selectedPackage,shadowSinceWall,nowWall);
        latestSnapshot=new ObservationSnapshot(shadowScopeId,selectedPackage,shadowSinceWall,nowWall,nowElapsed,shadowStartedElapsed,
            focusActiveStartedElapsed>0?Math.max(0,nowElapsed-focusActiveStartedElapsed):-1,budgetMs,
            shadowContinuousLimitMs,shadowPlannedFocusMs,shadowFeedback.count(),summary);
    }
    /** Fresh in-memory summary only; may contain NaN/missing features. Never triggers an OS query. */
    public ObservationSnapshot latestObservation() {
        long now=SystemClock.elapsedRealtime();
        if(!observe || !session.isActive() || !usageGranted(context)) { if(shadowSinceWall>0) invalidateShadowScope();return null; }
        if(latestSnapshot==null || latestSnapshot.scopeId!=shadowScopeId ||
            now<latestSnapshot.observedAtElapsed || now-latestSnapshot.observedAtElapsed>ObservationSnapshot.MAX_AGE_MS) return null;
        return latestSnapshot;
    }
    /** Exact trained-network trace if all six inputs are fresh and present. NEVER applies ledger/actions. */
    public ObservationSnapshot.ShadowTrace shadowDecision() {
        boolean permission=usageGranted(context), active=session.isActive();
        if((!observe || !permission || !active) && shadowSinceWall>0) invalidateShadowScope();
        return ObservationSnapshot.shadow(latestSnapshot,shadowScopeId,SystemClock.elapsedRealtime(),observe,permission,active);
    }
    /** Explicit feedback, at most once for an actual nudge in this scope within 60 seconds. */
    public boolean userDeferredNudge() {
        long now=SystemClock.elapsedRealtime();
        if(!shadowFeedback.defer(now,observe && session.isActive() && usageGranted(context) && shadowSinceWall>0)) return false;
        latestSnapshot=null;
        return true;
    }
}
