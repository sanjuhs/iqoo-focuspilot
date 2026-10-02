package dev.focuspilot.prototype;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** Private user-authored steps. Completion never executes or verifies a phone task. */
public final class TaskGuidePanel extends LinearLayout {
    private static final String PREFIX="taskGuide.";
    private static final int WHITE=Color.rgb(247,241,250), MUTED=Color.rgb(184,174,198), LILAC=Color.rgb(203,171,238);
    private final Activity activity;
    private final SharedPreferences prefs;
    private final Supplier<String> goal;
    private final Consumer<String> status, speak;
    private final Runnable stopSpeech;
    private final TextView progress, nextStep, speechFeedback;
    private final EditText editor;
    private final Button complete, undo, read;
    private TaskPlan plan;
    private String savedGoal="", renderedRevision="";
    private boolean corrupt;

    public TaskGuidePanel(Activity activity,SharedPreferences prefs,Supplier<String> goal,
                          Consumer<String> status,Consumer<String> speak,Runnable stopSpeech) {
        super(activity);this.activity=activity;this.prefs=prefs;this.goal=goal;this.status=status;this.speak=speak;this.stopSpeech=stopSpeech;
        setOrientation(VERTICAL);
        progress=label("One small step at a time.",14,MUTED,false);addView(progress);
        nextStep=label("Choose a task above, then write your own steps.",18,WHITE,true);addView(nextStep);
        complete=action("I've done this step",v->advance(false),true);
        undo=action("Undo last completed step",v->advance(true),false);
        read=action("Speak this step offline",v->readStep(),false);
        speechFeedback=label("Read a step when you're ready. Voice stays off until you tap.",13,MUTED,false);
        speechFeedback.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);addView(speechFeedback);
        action("Stop readback",v->stopSpeech.run(),false);
        LinearLayout details=new LinearLayout(activity);details.setOrientation(VERTICAL);details.setVisibility(GONE);
        Button toggle=action("Write or edit my steps ▾",v->{boolean open=details.getVisibility()!=VISIBLE;details.setVisibility(open?VISIBLE:GONE);((Button)v).setText("Write or edit my steps"+(open?" ▴":" ▾"));v.setContentDescription("Write or edit my steps, "+(open?"expanded":"collapsed"));},false);
        toggle.setContentDescription("Write or edit my steps, collapsed");addView(details);
        details.addView(label("Your steps stay on this phone. One per line, up to 8 steps of 120 characters. You decide when each is done; Mira does not verify or execute it. These are your words, not an AI-generated plan.",13,MUTED,false));
        editor=new EditText(activity);editor.setId(R.id.task_guide_editor);editor.setTextColor(WHITE);editor.setHintTextColor(MUTED);editor.setTextSize(15);
        editor.setHint("Open my notes\nDraft three points\nReview the draft");editor.setContentDescription("My task steps, one per line");
        editor.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        editor.setMinLines(3);editor.setMaxLines(8);editor.setPadding(dp(12),dp(8),dp(12),dp(8));
        GradientDrawable background=new GradientDrawable();background.setColor(Color.rgb(9,27,31));background.setCornerRadius(dp(10));editor.setBackground(background);
        details.addView(editor,new LayoutParams(-1,-2));
        addAction("Save these steps",details,v->save(),true);
        addAction("Clear my steps",details,v->clear(),false);
        reload(true);refresh();
    }
    private int dp(int value){return Math.round(value*getResources().getDisplayMetrics().density);}
    public void showSpeechFeedback(String value){speechFeedback.setText(value);}
    private TextView label(String value,int size,int color,boolean bold){TextView text=new TextView(activity);text.setText(value);text.setTextSize(size);text.setTextColor(color);text.setPadding(0,dp(4),0,dp(4));if(bold)text.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return text;}
    private Button action(String value,View.OnClickListener listener,boolean primary){return addAction(value,this,listener,primary);}
    private Button addAction(String value,LinearLayout parent,View.OnClickListener listener,boolean primary){
        Button button=new Button(activity);button.setText(value);button.setAllCaps(false);button.setTextSize(14);button.setTextColor(primary?Color.rgb(22,20,31):LILAC);
        GradientDrawable background=new GradientDrawable();background.setColor(primary?LILAC:Color.rgb(29,58,62));background.setCornerRadius(dp(14));button.setBackground(background);
        LayoutParams params=new LayoutParams(-1,dp(50));params.topMargin=dp(8);parent.addView(button,params);button.setOnClickListener(listener);return button;
    }
    private static String hash(String value){
        try{byte[] digest=MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));StringBuilder text=new StringBuilder();for(byte b:digest)text.append(String.format(java.util.Locale.US,"%02x",b&255));return text.toString();}
        catch(NoSuchAlgorithmException impossible){throw new IllegalStateException("SHA-256 unavailable",impossible);}
    }
    private String revision(){try{return prefs.getString(PREFIX+"revision","");}catch(ClassCastException invalid){return "invalid";}}
    private void reload(boolean replaceEditor){
        plan=null;corrupt=false;savedGoal="";renderedRevision=revision();
        try{
            if(!prefs.contains(PREFIX+"schema")){if(!renderedRevision.isEmpty())corrupt=true;return;}
            int count=prefs.getInt(PREFIX+"count",0);
            if(prefs.getInt(PREFIX+"schema",0)!=1||count<1||count>TaskPlan.MAX_STEPS||renderedRevision.isEmpty()||renderedRevision.equals("invalid"))throw new IllegalArgumentException();
            savedGoal=prefs.getString(PREFIX+"goal","");if(savedGoal==null||!savedGoal.matches("[0-9a-f]{64}"))throw new IllegalArgumentException();
            ArrayList<String> steps=new ArrayList<>();for(int i=0;i<count;i++)steps.add(prefs.getString(PREFIX+"step."+i,null));
            plan=TaskPlan.fromSteps(steps,prefs.getInt(PREFIX+"completed",-1));
        }catch(IllegalArgumentException|ClassCastException invalid){plan=null;corrupt=true;}
        finally{if(replaceEditor){StringBuilder text=new StringBuilder();if(plan!=null)for(String step:plan.steps()){if(text.length()>0)text.append('\n');text.append(step);}editor.setText(text.toString());}}
    }
    private boolean currentScope(){String current=goal.get();return plan!=null&&current!=null&&!current.trim().isEmpty()&&savedGoal.equals(hash(current));}
    public void refresh(){
        if(!renderedRevision.equals(revision()))reload(false);
        boolean scoped=currentScope();
        progress.setText(corrupt?"Saved steps are unavailable. Clear them or save a new plan.":plan==null?"One small step at a time.":!scoped?"These saved steps belong to a different task. Save them again only if they fit this task.":plan.completedCount()+" / "+plan.stepCount()+" steps completed by you");
        nextStep.setText(!scoped?"Choose your task, then write or review its steps.":plan.isComplete()?"You finished your plan. Take a moment to breathe.":"Next · "+plan.currentStep());
        complete.setEnabled(scoped&&!plan.isComplete());undo.setEnabled(scoped&&plan.completedCount()>0);read.setEnabled(scoped&&!plan.isComplete());
    }
    private boolean reviewedState(String reviewRevision,String reviewGoal){
        boolean same=reviewRevision.equals(revision())&&reviewGoal.equals(hash(goal.get()));
        if(!same){reload(false);refresh();status.accept("The task or saved plan changed. Review the current steps and try again.");}return same;
    }
    private boolean persist(TaskPlan value,String scope){
        stopSpeech.run();
        SharedPreferences.Editor change=prefs.edit();for(int i=0;i<TaskPlan.MAX_STEPS;i++)change.remove(PREFIX+"step."+i);
        change.putInt(PREFIX+"schema",1).putInt(PREFIX+"count",value.stepCount()).putInt(PREFIX+"completed",value.completedCount()).putString(PREFIX+"goal",scope).putString(PREFIX+"revision",UUID.randomUUID().toString());
        for(int i=0;i<value.stepCount();i++)change.putString(PREFIX+"step."+i,value.stepAt(i));
        boolean saved=change.commit();reload(false);refresh();if(!saved)status.accept("Saving the steps to phone storage could not be confirmed. Review them and retry; recovery may use the previous plan.");return saved;
    }
    private void save(){
        reload(false);
        String current=goal.get();if(current==null||current.trim().isEmpty()){status.accept("Save your task above before adding its steps.");return;}
        final TaskPlan requested;try{requested=TaskPlan.parse(editor.getText().toString());}catch(IllegalArgumentException invalid){status.accept(invalid.getMessage());return;}
        final String reviewRevision=revision(),reviewGoal=hash(current);
        Runnable write=()->{if(!reviewedState(reviewRevision,reviewGoal))return;if(persist(requested,reviewGoal))status.accept("Your steps are saved privately. Mark each done when you finish; no focus or phone action started.");};
        if(plan!=null||corrupt)new AlertDialog.Builder(activity).setTitle("Replace your saved steps?").setMessage("This replaces the saved plan and resets its completed steps. It does not change focus, monitoring or points.").setNegativeButton("Cancel",null).setPositiveButton("Replace steps",(d,w)->write.run()).show();else write.run();
    }
    private void advance(boolean backwards){
        if(!renderedRevision.equals(revision())){reload(false);refresh();status.accept("The saved plan changed. Review this step before marking it done.");return;}
        if(!currentScope()){refresh();status.accept("Review and save steps for your current task first.");return;}
        TaskPlan next=backwards?plan.undoCompletion():plan.completeCurrent();if(next==plan)return;
        if(persist(next,savedGoal))status.accept(backwards?"Last step restored. You can take it at your own pace.":next.isComplete()?"Your plan is complete. Focus stays under your control.":"Step marked done. Your next step is ready.");
    }
    private void readStep(){
        if(!renderedRevision.equals(revision())){reload(false);refresh();status.accept("The saved plan changed. Review the current step before reading it aloud.");return;}
        if(!currentScope()||plan.currentStep()==null){refresh();status.accept("Review a step for your current task first.");return;}
        speak.accept(plan.currentStep());
    }
    private void clear(){
        final String reviewed=revision();new AlertDialog.Builder(activity).setTitle("Clear your saved steps?").setMessage("Delete this private plan and its completion marks. Your task, focus session and model stay available.").setNegativeButton("Cancel",null).setPositiveButton("Clear steps",(d,w)->{
            if(!reviewed.equals(revision())){reload(false);refresh();status.accept("The saved plan changed. Review it before clearing.");return;}
            SharedPreferences.Editor change=prefs.edit();for(String key:prefs.getAll().keySet())if(key.startsWith(PREFIX))change.remove(key);
            stopSpeech.run();boolean saved=change.commit();reload(true);refresh();status.accept(saved?"Saved steps cleared.":"Clearing saved steps could not be confirmed. Retry before relying on deletion.");
        }).show();
    }
    /** Existing all-data deletion clears the common preference file, then resets this editor. */
    public void afterDataDeletion(){stopSpeech.run();reload(true);refresh();}
    public void taskChanged(){stopSpeech.run();refresh();}
}
