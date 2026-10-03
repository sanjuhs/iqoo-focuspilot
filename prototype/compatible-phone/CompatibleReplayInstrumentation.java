package dev.focuspilot.prototype;

import android.app.Instrumentation;
import android.app.Application;
import android.content.pm.ApplicationInfo;
import android.os.Bundle;
import android.os.Process;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

/** Target pure Java parity only. No repository, model, preferences, services, UI or actions. */
public final class CompatibleReplayInstrumentation extends Instrumentation {
    private static final String TARGET="dev.focuspilot.prototype", TEST=TARGET+".test";
    private static final int EXPECTED_REPLAY=300, EXPECTED_REVIEW=8;
    private final List<String> failed=new ArrayList<>();
    private int replayChecks, reviewChecks;
    private String failureType, expectedAssetSha, actualAssetSha;
    private JSONObject metadata;
    private final JSONObject origins=new JSONObject();

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        expectedAssetSha=arguments==null?null:arguments.getString("fixture_sha256");
        start();
    }
    private interface Check { boolean run() throws Exception; }
    private void reviewCheck(String id,Check check) {
        reviewChecks++;
        try { if(!check.run())failed.add("review:"+id); }
        catch(Throwable error) {failed.add("review:"+id); if(failureType==null)failureType=error.getClass().getSimpleName();}
    }
    private static String sha(byte[] bytes) throws Exception {
        StringBuilder hex=new StringBuilder();
        for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))hex.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        return hex.toString();
    }
    private JSONObject fixtures() throws Exception {
        if(expectedAssetSha==null||!expectedAssetSha.matches("[0-9a-f]{64}"))throw new IllegalArgumentException("Frozen fixture SHA required");
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        try(InputStream in=getContext().getAssets().open("compatible-fixtures.json")) {
            byte[] buffer=new byte[8192]; int n;
            while((n=in.read(buffer))!=-1) {if(bytes.size()+n>1_000_000)throw new IllegalArgumentException("Oversized fixtures");bytes.write(buffer,0,n);}
        }
        actualAssetSha=sha(bytes.toByteArray());
        if(!actualAssetSha.equals(expectedAssetSha))throw new IllegalArgumentException("Fixture identity differs");
        JSONObject data=new JSONObject(bytes.toString(StandardCharsets.UTF_8.name()));
        if(!"focuspilot.compatible_replay_fixtures.v1".equals(data.getString("schema"))||data.getInt("rows")!=100||data.getInt("replay_checks")!=300||data.getJSONArray("fixtures").length()!=100)
            throw new IllegalArgumentException("Frozen fixture inventory differs");
        metadata=data;
        return data;
    }
    // Serialize the TARGET gate's actual slots. This does not reimplement request validation.
    private static String canonical(ModelCommandGate.Proposal p) {
        switch(p.kind) {
            case START_FOCUS:return "{\"intent\":\"start_focus\",\"duration_seconds\":"+p.seconds+"}";
            case PAUSE_FOCUS:return "{\"intent\":\"pause_focus\"}";
            case ALARM:return "{\"intent\":\"alarm\",\"hour\":"+p.hour+",\"minute\":"+p.minute+"}";
            case TIMER:return "{\"intent\":\"timer\",\"duration_seconds\":"+p.seconds+"}";
            case OPEN_SETTINGS:return "{\"intent\":\"open_app\",\"app\":\"settings\"}";
            case OPEN_CALCULATOR:return "{\"intent\":\"open_app\",\"app\":\"calculator\"}";
            case OPEN_CLOCK:return "{\"intent\":\"open_app\",\"app\":\"clock\"}";
            case EXPLAIN:return "{\"intent\":\"explain\"}";
            default:return "{\"intent\":\"unknown\"}";
        }
    }
    private static boolean sameSlots(JSONObject actual,JSONObject expected)throws Exception {
        if(actual.length()!=expected.length())return false;
        Iterator<String> keys=expected.keys();
        while(keys.hasNext()) {
            String k=keys.next();if(!actual.has(k))return false;
            Object a=actual.get(k),e=expected.get(k);
            if(e instanceof Number) {
                if(!(a instanceof Integer||a instanceof Long)||!(e instanceof Integer||e instanceof Long)||((Number)a).longValue()!=((Number)e).longValue())return false;
            } else if(!(e instanceof String)||!e.equals(a))return false;
        }
        return true;
    }
    private void replay(JSONObject fixture,String mode)throws Exception {
        replayChecks++;
        String id=fixture.getString("id"),request=fixture.getString("request"),value,origin;
        boolean accepted;
        if("baseline".equals(mode)) {
            JSONObject response=new JSONObject(fixture.getString("baseline_response"));
            if(response.length()!=1)throw new IllegalArgumentException("Baseline response schema");
            ModelCommandGate.Proposal p=ModelCommandGate.validate(response.getString("intent"),request);
            value=canonical(p);accepted=p.executable();origin=accepted?"CHECKED_MODEL":"UNKNOWN";
        } else {
            CompatibleUnitCommand.Proposal p;
            if("product_pipeline".equals(mode)) {
                p=CompatibleUnitCommand.recognize(request);
                if(!p.accepted)p=CompatibleUnitCommand.validate(request,fixture.getString("candidate_response"));
            } else p=CompatibleUnitCommand.validate(request,fixture.getString("candidate_response"));
            value=p.canonicalJson();accepted=p.accepted;origin=p.origin;
            if(!p.source.equals(p.origin))throw new IllegalStateException("Origin aliases differ");
        }
        JSONObject expected=fixture.getJSONObject("expected").getJSONObject(mode);
        if(accepted!=expected.getBoolean("accepted")||!origin.equals(expected.getString("origin"))||!sameSlots(new JSONObject(value),expected.getJSONObject("proposal")))failed.add(mode+":"+id);
        JSONObject counts=origins.optJSONObject(mode);if(counts==null){counts=new JSONObject();origins.put(mode,counts);}
        counts.put(origin,counts.optInt(origin,0)+1);
    }
    private static CompatibleReviewState fastState() {
        CompatibleReviewState s=new CompatibleReviewState();
        if(!s.offer(1,"Open Calculator",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST))throw new AssertionError("Known fast proposal refused");
        return s;
    }
    private void reviewFixtures() {
        reviewCheck("unchanged_inert_review",()->{
            CompatibleReviewState s=fastState();return s.review(s.snapshot(),1,"Open Calculator",true,true).proposal.executable();
        });
        reviewCheck("edited_request_refused",()->{
            CompatibleReviewState s=fastState();return !s.review(s.snapshot(),1,"Open Settings",true,true).proposal.executable();
        });
        reviewCheck("cancel_clears_pending",()->{
            CompatibleReviewState s=fastState();CompatibleReviewState.Snapshot old=s.snapshot();s.clear();return s.snapshot()==null&&!s.consume(old,1,"Open Calculator",true,true).proposal.executable();
        });
        reviewCheck("stale_epoch_refused",()->{
            CompatibleReviewState s=fastState();return !s.review(s.snapshot(),2,"Open Calculator",true,true).proposal.executable();
        });
        reviewCheck("background_and_busy_refused",()->{
            CompatibleReviewState s=fastState();return !s.review(s.snapshot(),1,"Open Calculator",false,true).proposal.executable()&&!s.review(s.snapshot(),1,"Open Calculator",true,false).proposal.executable();
        });
        reviewCheck("old_callback_preserves_replacement",()->{
            CompatibleReviewState s=fastState();CompatibleReviewState.Snapshot old=s.snapshot();
            return s.offer(2,"Open Settings",null,CompatibleUnitCommand.FAST_LOCAL_REQUEST)&&!s.consume(old,1,"Open Calculator",true,true).proposal.executable()&&s.review(s.snapshot(),2,"Open Settings",true,true).proposal.executable();
        });
        reviewCheck("consume_once_without_execution",()->{
            CompatibleReviewState s=fastState();CompatibleReviewState.Snapshot pending=s.snapshot();
            return s.consume(pending,1,"Open Calculator",true,true).proposal.executable()&&!s.consume(pending,1,"Open Calculator",true,true).proposal.executable();
        });
        reviewCheck("checked_model_slots_revalidated",()->{
            CompatibleReviewState s=new CompatibleReviewState();String request="Set a five-minute timer",response="{\"intent\":\"timer\",\"amount\":5,\"unit\":\"minutes\"}";
            return s.offer(3,request,response,CompatibleUnitCommand.CHECKED_MODEL)&&s.review(s.snapshot(),3,request,true,true).proposal.seconds==300&&!s.offer(4,request,"{\"intent\":\"timer\",\"amount\":6,\"unit\":\"minutes\"}",CompatibleUnitCommand.CHECKED_MODEL)&&s.snapshot()==null;
        });
    }
    @Override public void onStart() {
        Bundle result=new Bundle();JSONObject report=new JSONObject();boolean passed=false;
        try {
            if(!TARGET.equals(getTargetContext().getPackageName())||!TEST.equals(getContext().getPackageName()))throw new IllegalStateException("Unexpected package context");
            ApplicationInfo target=getTargetContext().getApplicationInfo();
            if(target.uid!=Process.myUid()||!TARGET.equals(target.processName)||!TARGET.equals(Application.getProcessName()))throw new IllegalStateException("Unexpected target UID/process declaration");
            JSONArray rows=fixtures().getJSONArray("fixtures");
            java.util.HashSet<String> ids=new java.util.HashSet<>();
            for(int i=0;i<rows.length();i++) {
                JSONObject row=rows.getJSONObject(i);String id=row.getString("id");
                if(!id.matches("[a-z0-9_]{1,100}")||!ids.add(id))throw new IllegalArgumentException("Duplicate fixture ID");
                for(String mode:new String[]{"baseline","checked_model","product_pipeline"}) {
                    try {replay(row,mode);}catch(Throwable e){failed.add(mode+":"+id);if(failureType==null)failureType=e.getClass().getSimpleName();}
                }
            }
            reviewFixtures();
            report.put("target_package",getTargetContext().getPackageName());report.put("test_package",getContext().getPackageName());
            report.put("target_uid",target.uid);report.put("process_uid",Process.myUid());report.put("process_pid",Process.myPid());report.put("target_process",target.processName);report.put("actual_process",Application.getProcessName());
            report.put("target_class_names",new JSONArray(new String[]{ModelCommandGate.class.getName(),CompatibleUnitCommand.class.getName(),UnitCommand.class.getName(),StructuredCommand.class.getName(),CommandNumberWords.class.getName(),CompatibleActionRouter.class.getName(),CompatibleReviewState.class.getName()}));
            passed=failed.isEmpty()&&failureType==null&&replayChecks==EXPECTED_REPLAY&&reviewChecks==EXPECTED_REVIEW;
        } catch(Throwable error) {failureType=error.getClass().getSimpleName();}
        try {
            report.put("schema","focuspilot.compatible_android_replay.v1");report.put("passed",passed);
            report.put("fixtures",100);report.put("replay_checks",replayChecks);report.put("expected_replay_checks",EXPECTED_REPLAY);
            report.put("review_checks",reviewChecks);report.put("expected_review_checks",EXPECTED_REVIEW);report.put("checks",replayChecks+reviewChecks);report.put("expected_checks",308);
            report.put("failed_fixture_ids",new JSONArray(failed));report.put("failure_type",failureType==null?JSONObject.NULL:failureType);
            report.put("asset_sha256",actualAssetSha==null?JSONObject.NULL:actualAssetSha);report.put("origins",origins);
            if(metadata!=null){report.put("host_source_commit",metadata.getString("host_source_commit"));report.put("fixture_source_sha256",metadata.getJSONObject("source_sha256"));}
            for(String key:new String[]{"model_accessed","native_model_loaded","production_preferences_accessed","production_singleton_used","services_started","voice_used","ui_started"})report.put(key,false);
            report.put("actions_executed",0);report.put("scope","Already-seen host outputs, target pure Java parity and inert review ownership; no fresh phone model accuracy or UI/action proof");
            result.putString("report_json",report.toString());
        }catch(Throwable error){passed=false;result.putString("stream","Replay report creation failed\n");}
        finish(passed?-1:0,result);
    }
}
