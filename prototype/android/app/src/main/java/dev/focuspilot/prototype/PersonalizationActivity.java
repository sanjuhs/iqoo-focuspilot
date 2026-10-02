package dev.focuspilot.prototype;

import android.app.Activity;
import android.content.SharedPreferences;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.text.InputType;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

/** Local manual-label sandbox. No usage observation, service control, permissions or actions. */
public final class PersonalizationActivity extends Activity {
    private static final int BG=Color.rgb(26,26,36), SURFACE=Color.rgb(42,40,56);
    private static final int TEXT=Color.rgb(244,239,250), MUTED=Color.rgb(192,181,207), ACCENT=Color.rgb(201,183,234);
    private static final String STORE="focuspilot_fewshot_sandbox", KEY="examples_v1";
    private static final String[] LABELS={"Selected-app budget overrun","Continuous-session overrun","Reopen count",
        "Active-focus overlap","Deferred nudges","Elapsed-time overrun"};
    private final FewShotPolicy policy=new FewShotPolicy();
    private final EditText[] inputs=new EditText[6];
    private final Switch[] gates=new Switch[6];
    private TextView status,result,neighbors;
    private LinearLayout savedRows;
    private SharedPreferences preferences;
    private String storageNotice="";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        preferences=getSharedPreferences(STORE,MODE_PRIVATE);load();
        getWindow().setStatusBarColor(BG);getWindow().setNavigationBarColor(BG);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        getWindow().getDecorView().setSystemUiVisibility(0);
        LinearLayout frame=new LinearLayout(this);frame.setOrientation(LinearLayout.VERTICAL);
        frame.setBackgroundColor(BG);frame.setPadding(dp(16),dp(16),dp(16),dp(16));
        frame.setOnApplyWindowInsetsListener((v,insets)->{
            if(Build.VERSION.SDK_INT>=30){Insets b=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                v.setPadding(b.left+dp(16),b.top+dp(12),b.right+dp(16),b.bottom+dp(12));}
            else v.setPadding(insets.getSystemWindowInsetLeft()+dp(16),insets.getSystemWindowInsetTop()+dp(12),
                insets.getSystemWindowInsetRight()+dp(16),insets.getSystemWindowInsetBottom()+dp(12));
            return insets;
        });
        ScrollView scroll=new ScrollView(this);LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(content,new ScrollView.LayoutParams(-1,-2));frame.addView(scroll,new LinearLayout.LayoutParams(-1,-1));
        setContentView(frame);frame.requestApplyInsets();
        button(content,"Back to FocusPilot",()->finish());
        text(content,"Teach your preferences",27,ACCENT,true);
        text(content,"Local few-shot sandbox · pre-event research\nLabel a few invented situations as Allow or Nudge. Similar saved situations can guide a preview. " +
            "No network weights change. Nothing here watches your phone, starts monitoring, sends notifications or moves money.",15,MUTED,false);
        LinearLayout featureCard=card(content);text(featureCard,"Describe a synthetic situation",20,TEXT,true);
        text(featureCard,"Six normalized values from 0 to 1, matching the tiny decision lab. These are manual invented inputs, not measured phone behavior.",14,MUTED,false);
        String[] restored=state==null?null:state.getStringArray("features");
        for(int i=0;i<6;i++){
            text(featureCard,LABELS[i],14,TEXT,true);EditText input=new EditText(this);input.setSingleLine(true);input.setTextColor(TEXT);
            input.setHintTextColor(MUTED);input.setTextSize(16);input.setMinHeight(dp(48));
            input.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL|InputType.TYPE_NUMBER_FLAG_SIGNED);
            input.setContentDescription(LABELS[i]+", manual synthetic value from zero to one");
            input.setText(restored!=null&&restored.length==6?restored[i]:"0.0");featureCard.addView(input);inputs[i]=input;
        }
        button(featureCard,"Save label: Allow",()->saveLabel(FewShotPolicy.Label.ALLOW));
        button(featureCard,"Save label: Nudge",()->saveLabel(FewShotPolicy.Label.NUDGE));
        button(featureCard,"Compare this situation",()->refresh());
        LinearLayout gateCard=card(content);text(gateCard,"Simulated external gates",20,TEXT,true);
        text(gateCard,"These switches simulate prerequisites; they never grant Android permission or start a session. All gates must pass for an actionable sandbox preview. " +
            "The sandbox opens paused with every permission/consent gate off. Saving manual labels remains possible while blocked.",14,MUTED,false);
        String[] gateLabels={"Sandbox paused","Sandbox consent enabled","Simulated required permission available",
            "Simulated focus session active","Simulated observations fresh","Simulated cooldown ready"};
        for(int i=0;i<6;i++){
            Switch toggle=new Switch(this);toggle.setText(gateLabels[i]);toggle.setTextColor(TEXT);toggle.setTextSize(14);toggle.setMinHeight(dp(48));
            toggle.setChecked(state==null?i==0:state.getBoolean("gate"+i,i==0));gateCard.addView(toggle);gates[i]=toggle;
        }
        LinearLayout resultCard=card(content);result=text(resultCard,"",16,TEXT,false);
        neighbors=text(card(content),"",14,TEXT,false);neighbors.setTextIsSelectable(true);
        neighbors.setTypeface(Typeface.MONOSPACE);
        LinearLayout storeCard=card(content);text(storeCard,"Saved only in this app",20,ACCENT,true);
        status=text(storeCard,"",14,MUTED,false);
        text(storeCard,"At most 32 labels; a 33rd replaces the oldest. Each record stores only your six manual numbers and Allow/Nudge label. " +
            "No text, app history or inferred activity is saved. Delete one record below or reset all.",14,MUTED,false);
        button(storeCard,"Delete all saved labels",()->{policy.clear();preferences.edit().remove(KEY).apply();storageNotice="All labels deleted.";refresh();});
        savedRows=new LinearLayout(this);savedRows.setOrientation(LinearLayout.VERTICAL);storeCard.addView(savedRows);
        for(Switch gate:gates) gate.setOnCheckedChangeListener((button,checked)->refresh());
        refresh();
    }
    @Override protected void onSaveInstanceState(Bundle state){
        super.onSaveInstanceState(state);String[] values=new String[6];for(int i=0;i<6;i++){values[i]=inputs[i].getText().toString();state.putBoolean("gate"+i,gates[i].isChecked());}
        state.putStringArray("features",values);
    }
    private double[] readInputs(){
        double[] values=new double[6];for(int i=0;i<6;i++){
            inputs[i].setError(null);try{values[i]=Double.parseDouble(inputs[i].getText().toString().trim());
                if(!Double.isFinite(values[i])||values[i]<0||values[i]>1)throw new NumberFormatException();}
            catch(NumberFormatException error){inputs[i].setError("Use a finite value from 0 to 1");return null;}
        }return values;
    }
    private void saveLabel(FewShotPolicy.Label label){double[] values=readInputs();if(values==null){result.setText("No label saved: check the inputs.");return;}
        policy.add(values,label);persist();storageNotice="Saved your "+label+" label locally.";refresh();}
    private void refresh(){
        if(result==null)return;refreshSavedRows();double[] values=readInputs();
        if(values==null){result.setText("No preview: check the six manual values.");neighbors.setText("");return;}
        FewShotPolicy.Gates external=new FewShotPolicy.Gates(gates[0].isChecked(),gates[1].isChecked(),gates[2].isChecked(),
            gates[3].isChecked(),gates[4].isChecked(),gates[5].isChecked());
        FewShotPolicy.Evaluation evaluation=policy.evaluate(values,external);
        TrainedPolicy.Evaluation baseline=TrainedPolicy.evaluate(values);
        result.setText(String.format(Locale.US,"Personalized preview: %s\n%s\n\nSaved-label nudge vote: %.3f\nUncertainty index: %.3f\n"+
            "Synthetic trained baseline: %.3f → %s\n\nThe vote is not calibrated confidence. No action is executed; external gates always win.",
            evaluation.recommendation,evaluation.reason,evaluation.nudgeVote,evaluation.uncertainty,baseline.score,
            baseline.score>=TrainedPolicy.DEV_THRESHOLD?"Nudge":"Allow"));
        StringBuilder details=new StringBuilder("Matched saved examples\n");
        if(evaluation.neighbors.isEmpty())details.append("No neighbors read while blocked or without labels.\n");
        for(FewShotPolicy.Neighbor n:evaluation.neighbors){
            details.append(String.format(Locale.US,"\n#%d %s · RMS distance %.4f\nVote weight %.4f · nudge contribution %.4f\n",n.id,n.label,n.distance,n.voteWeight,n.nudgeContribution));
            details.append("Saved vector ").append(Arrays.toString(n.features())).append('\n');
            double[] parts=n.squaredDistanceContributions();for(int i=0;i<6;i++)details.append(String.format(Locale.US," %s: distance² +%.5f\n",LABELS[i],parts[i]));
        }
        details.append("\nNudge contributions sum to the displayed vote. Distance² contributions explain numeric similarity, not causal productivity effects.");neighbors.setText(details);
    }
    private void refreshSavedRows(){
        status.setText(policy.examples().size()+" / 32 labels saved locally.\n"+storageNotice);savedRows.removeAllViews();
        for(FewShotPolicy.Example example:policy.examples()){
            text(savedRows,"#"+example.id+" · "+example.label+"\n"+Arrays.toString(example.features()),13,MUTED,false);
            button(savedRows,"Delete label #"+example.id,()->{policy.delete(example.id);persist();storageNotice="Label deleted.";refresh();});
        }
    }
    private void load(){
        String raw=preferences.getString(KEY,null);if(raw==null)return;
        try{if(raw.length()>30000)throw new IllegalArgumentException("Oversized cache");JSONObject envelope=new JSONObject(raw);
            if(envelope.getInt("schema")!=1)throw new IllegalArgumentException("Unknown schema");JSONArray records=envelope.getJSONArray("examples");
            if(records.length()>FewShotPolicy.MAX_EXAMPLES)throw new IllegalArgumentException("Too many records");List<FewShotPolicy.Example> loaded=new ArrayList<>();
            for(int i=0;i<records.length();i++){JSONObject record=records.getJSONObject(i);JSONArray vector=record.getJSONArray("features");
                if(vector.length()!=6)throw new IllegalArgumentException("Wrong feature count");double[] values=new double[6];for(int j=0;j<6;j++)values[j]=vector.getDouble(j);
                loaded.add(new FewShotPolicy.Example(record.getLong("id"),values,FewShotPolicy.Label.valueOf(record.getString("label"))));}
            policy.restore(loaded);
        }catch(Exception error){storageNotice="Saved labels could not be read; the cache was left untouched. Delete all to reset.";}
    }
    private void persist(){
        try{JSONArray records=new JSONArray();for(FewShotPolicy.Example e:policy.examples()){
            JSONObject record=new JSONObject();record.put("id",e.id);record.put("label",e.label.name());JSONArray vector=new JSONArray();for(double v:e.features())vector.put(v);
            record.put("features",vector);records.put(record);}
            JSONObject envelope=new JSONObject();envelope.put("schema",1);envelope.put("examples",records);preferences.edit().putString(KEY,envelope.toString()).apply();
        }catch(Exception error){storageNotice="Labels could not be saved.";}
    }
    private LinearLayout card(LinearLayout parent){LinearLayout v=new LinearLayout(this);v.setOrientation(LinearLayout.VERTICAL);v.setBackgroundColor(SURFACE);
        v.setPadding(dp(14),dp(12),dp(14),dp(12));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,dp(12),0,0);parent.addView(v,p);return v;}
    private TextView text(LinearLayout parent,String value,int size,int color,boolean bold){TextView v=new TextView(this);v.setText(value);v.setTextColor(color);v.setTextSize(size);
        v.setPadding(0,dp(5),0,dp(7));if(bold)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);parent.addView(v,new LinearLayout.LayoutParams(-1,-2));return v;}
    private void button(LinearLayout parent,String title,Runnable action){Button v=new Button(this);v.setText(title);v.setAllCaps(false);v.setTextColor(BG);v.setMinHeight(dp(48));
        v.setBackgroundTintList(ColorStateList.valueOf(ACCENT));v.setOnClickListener(clicked->action.run());parent.addView(v,new LinearLayout.LayoutParams(-1,-2));}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}
