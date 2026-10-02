package dev.focuspilot.prototype;

import android.app.Instrumentation;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.SystemClock;
import java.lang.reflect.Constructor;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/** Runs real repository persistence against exclusively test-owned preferences. */
public final class ResetIsolationInstrumentation extends Instrumentation {
    private int checks;
    private final Set<String> stores=new HashSet<>();
    private final String prefix="reset_isolation_"+UUID.randomUUID().toString().replace("-","")+"_";
    private FocusRepository active;
    private Context isolated;
    private Throwable failure;

    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments);start(); }
    private void require(boolean value,String message) {
        checks++;if(!value)throw new AssertionError(message);
    }
    private FocusRepository repository() throws Exception {
        Constructor<FocusRepository> constructor=FocusRepository.class.getDeclaredConstructor(Context.class);
        constructor.setAccessible(true);return constructor.newInstance(isolated);
    }
    private void mainThread(Runnable action) {
        failure=null;
        runOnMainSync(()->{try{action.run();}catch(Throwable error){failure=error;}});
        if(failure!=null)throw new AssertionError("Isolated repository check failed",failure);
    }
    private FocusRepository create() {
        try{return repository();}catch(Exception error){throw new AssertionError(error);}
    }
    @Override public void onStart() {
        Bundle result=new Bundle();
        try {
            isolated=new ContextWrapper(getTargetContext()) {
                @Override public Context getApplicationContext(){return this;}
                @Override public SharedPreferences getSharedPreferences(String name,int mode) {
                    String owned=prefix+name;
                    if(!stores.contains(owned)) {
                        java.io.File file=new java.io.File(getBaseContext().getApplicationInfo().dataDir,"shared_prefs/"+owned+".xml");
                        if(file.exists() || new java.io.File(file.getPath()+".bak").exists())throw new AssertionError("Existing test store refused");
                        stores.add(owned);
                    }
                    return getBaseContext().getSharedPreferences(owned,mode);
                }
                @Override public android.content.ComponentName startService(Intent intent){throw new AssertionError("Service start forbidden in reset test");}
                @Override public android.content.ComponentName startForegroundService(Intent intent){throw new AssertionError("Foreground service start forbidden in reset test");}
                @Override public boolean stopService(Intent intent){throw new AssertionError("Service stop forbidden in reset test");}
            };
            mainThread(()->{
                SharedPreferences seed=isolated.getSharedPreferences("focuspilot_research",Context.MODE_PRIVATE);
                require(seed.edit().putLong("elapsedCheckpoint",5000).putBoolean("activeCheckpoint",true)
                    .putBoolean("timedCheckpoint",true).putLong("remainingCheckpoint",15000)
                    .putLong("usageCheckpoint",2000).putInt("points",75).putBoolean("observe",true)
                    .putString("focusGoal","Synthetic test task").putString("taskGuide.testSentinel","keep checklist")
                    .putLong("budget",120000).putLong("shadowPlannedFocus",600000).commit(),"Seed committed");
                SharedPreferences labels=isolated.getSharedPreferences(LivePreferenceStore.STORE,Context.MODE_PRIVATE);
                require(labels.edit().putBoolean("enabled",true).putString("testSentinel","keep labels").commit(),"Labels seeded");
                FocusRepository recovered=create();
                require(recovered.interrupted && !recovered.session.isActive(),"Interrupted recovery pauses");
                require(recovered.session.elapsed(SystemClock.elapsedRealtime())==5000 && recovered.session.remainingMs(SystemClock.elapsedRealtime())==15000,"Recovered exact checkpoint");
                recovered.reset();
                require(!recovered.interrupted,"Reset clears interrupted warning");
                require(!recovered.session.isActive() && !recovered.session.isTimed() && !recovered.session.isCompleted(),"Reset clears timer state");
                require(recovered.session.elapsed(SystemClock.elapsedRealtime())==0 && recovered.accumulatedUsage==0 && recovered.intervalWall==0,"Reset clears counters");
                require(recovered.ledger.points()==100,"Reset restores virtual points");
                require(recovered.observe && recovered.budgetMs==120000 && recovered.shadowPlannedFocusMs==600000,"Reset preserves chosen settings");
                require("Synthetic test task".equals(seed.getString("focusGoal","")) && "keep checklist".equals(seed.getString("taskGuide.testSentinel","")),"Reset preserves authored data");
                require(labels.getBoolean("enabled",false) && "keep labels".equals(labels.getString("testSentinel","")),"Reset preserves labels");
                require(seed.edit().commit(),"Pending writes drained");
                FocusRepository restored=create();
                require(restored.observe && !restored.interrupted && !restored.session.isActive() && !restored.session.isTimed() && restored.session.elapsed(SystemClock.elapsedRealtime())==0 && restored.ledger.points()==100,"Reset persists across construction");
                active=restored;active.setObservation(false);active.startTimed(1000);require(active.session.isActive(),"New timed session started");
                active.reset();require(!active.interrupted && !active.session.isActive(),"Active reset pauses and clears recovery");
            });
            SystemClock.sleep(1250);
            mainThread(()->{
                require(!active.session.isActive() && !active.session.isTimed() && !active.session.isCompleted() && active.session.elapsed(SystemClock.elapsedRealtime())==0,"Canceled deadline cannot complete old run");
                require(active.prefs.edit().commit(),"Final writes drained");
                FocusRepository restored=create();
                require(!restored.interrupted && restored.session.elapsed(SystemClock.elapsedRealtime())==0,"Final persisted state remains reset");
            });
            result.putBoolean("passed",true);
        } catch(Throwable error) {
            result.putBoolean("passed",false);result.putString("failure_type",error.getClass().getSimpleName());
            result.putString("failure",error.getMessage());
        } finally {
            try {
                mainThread(()->{
                    if(active!=null)active.reset();
                    for(String name:stores) {
                        if(!name.startsWith(prefix))throw new AssertionError("Unowned cleanup refused");
                        require(getTargetContext().getSharedPreferences(name,Context.MODE_PRIVATE).edit().commit(),"Cleanup writes drained");
                        require(getTargetContext().deleteSharedPreferences(name),"Test-owned preferences removed");
                    }
                });
            } catch(Throwable error) {
                result.putBoolean("passed",false);result.putString("cleanup_failure_type",error.getClass().getSimpleName());
            }
        }
        result.putInt("checks",checks);result.putInt("isolated_stores",stores.size());
        result.putBoolean("production_singleton_used",false);
        result.putString("stream","FocusRepository reset isolation: "+result.getBoolean("passed")+", "+checks+" checks; no production preference store or model access.\n");
        finish(result.getBoolean("passed")?-1:0,result);
    }
}
