#!/usr/bin/env python3
"""Synthetic authored-step mute/readback checks; no mic, grants or external actions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from phone_model_smoke import PhoneLab, PACKAGE
from phone_task_guide import (STEPS, PREFIX, preferences, checkpoint, guide_record, require_empty_test_state,
                              disclosure, find_attribute, tap_node, wait_preferences)
from phone_readback import permissions, monitor_record_present

OUTCOMES={
    'Mira finished reading aloud.':'engine_completed_callback',
    'Readback failed. Your text is still here.':'engine_error_callback',
    'Readback stopped. Your text is still here.':'stopped',
    'Readback timed out. You can try again when you\'re ready.':'bounded_timeout',
    'Offline readback could not start. Your text is still here.':'engine_start_failed',
    'Offline readback is unavailable. Your text is still here.':'engine_unavailable',
    'Offline voice is not ready or installed. Your text is still here.':'offline_voice_unavailable',
}
MUTED="Mira's voice is muted. Your text is still here."
GOAL='Prepare a short focus demo'


class GuideLab(PhoneLab):
    def find(self,label,scroll=True):
        for _ in range(6):
            node=super().find(label,scroll)
            bounds=list(map(int,re.findall(r'\d+',node.get('bounds',''))))
            center=(bounds[1]+bounds[3])//2
            if 350<=center<=1900:return node
            self.guard()
            if center>1900:self.adb('shell','input','swipe','540','1750','540','1150','250')
            else:self.adb('shell','input','swipe','540','650','540','1250','250')
        raise RuntimeError('Own control could not be positioned clear of fixed overlays')


def assert_test_plan(values):
    record=guide_record(values)
    expected={PREFIX+'schema':1,PREFIX+'count':3,PREFIX+'completed':0,
              PREFIX+'goal':hashlib.sha256(GOAL.encode()).hexdigest()}
    expected.update({PREFIX+'step.'+str(i):step for i,step in enumerate(STEPS)})
    if values.get('focusGoal')!=GOAL or any(record.get(k)!=v for k,v in expected.items()):
        raise RuntimeError('Synthetic guide shape, text, association or progress differs')
    if not isinstance(record.get(PREFIX+'revision'),str) or not record[PREFIX+'revision']:
        raise RuntimeError('Synthetic guide revision missing')
    if any(PREFIX+'step.'+str(i) in record for i in range(3,8)):
        raise RuntimeError('Unexpected retained synthetic step')
    return record


def set_test_field(lab,attribute,name,value):
    if not re.fullmatch(r'[A-Za-z0-9 \n]*',value):raise ValueError('Synthetic ASCII only')
    lab.top()
    for _ in range(6):
        node=find_attribute(lab,attribute,name)
        bounds=list(map(int,re.findall(r'\d+',node.get('bounds',''))))
        # Keep the field clear of this phone's fixed bottom Stop bar and top inset.
        if len(bounds)==4 and 350<=(bounds[1]+bounds[3])//2<=1900:break
        lab.guard();lab.adb('shell','input','swipe','540','1750','540','1100','250')
    else:raise RuntimeError('Synthetic field not safely positioned; no text entered')
    tap_node(lab,node)
    if not any(n.get(attribute)==name and n.get('focused')=='true' for n in lab.nodes()):
        raise RuntimeError('Named synthetic field did not gain focus; no text entered')
    lab.guard();lab.adb('shell','input','keycombination','113','29')
    lab.guard();lab.adb('shell','input','keyevent','KEYCODE_DEL')
    for i,line in enumerate(value.split('\n')):
        if i:lab.guard();lab.adb('shell','input','keyevent','KEYCODE_ENTER')
        if line:lab.guard();lab.adb('shell','input','text',line.replace(' ','%s'))
    lab.guard();lab.adb('shell','input','keyevent','KEYCODE_BACK');lab.top()
    if value and find_attribute(lab,attribute,name).get('text','')!=value:
        raise RuntimeError('Synthetic field readback mismatch; no save')


def cleanup(lab,before,created):
    result={'cleanup_verified':False,'cleanup_scope':'Remove only this synthetic three-step guide, restore empty task and mute false; task-save log entries/zero target keys may remain.'}
    try:
        current=preferences(lab)
        if checkpoint(current)!=before:raise RuntimeError('Changed focus state left untouched')
        if created and current.get('focusGoal')==GOAL:
            if guide_record(current):
                assert_test_plan(current)
                disclosure(lab,'Write or edit my steps');lab.tap('Clear my steps');lab.tap('Clear steps',scroll=False)
            if guide_record(preferences(lab)):raise RuntimeError('Synthetic guide clear not observed')
            disclosure(lab,'Choose your task & targets');set_test_field(lab,'content-desc','Focus task','')
            lab.tap('Save task & targets');wait_preferences(lab,lambda v:v.get('focusGoal','')=='')
        final=preferences(lab)
        result.update(final_checkpoint=checkpoint(final),empty_goal_restored=final.get('focusGoal','')=='',
                      guide_record_removed=not guide_record(final))
        result['cleanup_verified']=(result['final_checkpoint']==before and result['empty_goal_restored']
                                    and result['guide_record_removed'] and final.get('shadowPlannedFocus',0)==0
                                    and final.get('shadowContinuousLimit',0)==0)
    except Exception as error:result['cleanup_failure_type']=type(error).__name__
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--execute-synthetic-guide-readback',action='store_true')
    args=parser.parse_args()
    if not args.execute_synthetic_guide_readback:parser.error('Explicit --execute-synthetic-guide-readback required')
    manifest_path=Path('docs/guidance-readback-artifacts.json');manifest=json.loads(manifest_path.read_text())
    lab=GuideLab(args.serial);lab.guard()
    installed=lab.adb('shell','pm','path',PACKAGE).strip().split('package:',1)[1]
    sha=lab.adb('shell','sha256sum',installed).split()[0]
    artifact=next((a for a in manifest['artifacts'] if a['sha256']==sha),None)
    if artifact is None:raise RuntimeError('Installed APK not in frozen v0.12 manifest')
    if lab.adb('shell','run-as',PACKAGE,'sha256sum','files/qwen35.gguf').split()[0]!=manifest['model']['sha256']:
        raise RuntimeError('Retained Qwen model differs')
    for path,expected in manifest['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise RuntimeError('Current source differs from manifest')
        if hashlib.sha256(subprocess.check_output(['git','show',manifest['source_commit']+':'+path])).hexdigest()!=expected:
            raise RuntimeError('Committed app source differs from manifest')
    initial=preferences(lab);require_empty_test_state(initial);before=checkpoint(initial);grants=permissions(lab)
    if initial.get('mute',False) is not False:raise RuntimeError('Existing mute preference respected; audible test not started')
    if monitor_record_present(lab):raise RuntimeError('Existing monitor left unchanged')
    # Fresh own process removes unsaved editor state; no saved settings or model deletion.
    lab.adb('shell','am','force-stop',PACKAGE)
    lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity');lab.guard()
    if checkpoint(preferences(lab))!=before:raise RuntimeError('Own process restart changed checkpoint')
    report=dict(research_only=True,source_commit=manifest['source_commit'],apk_sha256=sha,
                model_sha256=manifest['model']['sha256'],native_sha256=artifact['native_sha256'],
                harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                before_checkpoint=before,grants_before=grants,initial_mute=False,
                synthetic_goal=GOAL,synthetic_steps=STEPS,phases=[],completed=False,
                human_audibility_verified=False,offline_disconnect_verified=False,microphone_started=False,
                os_permissions_or_settings_changed=False,external_app_action_executed=False,npu_verified=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n')
    def invariant():
        if checkpoint(preferences(lab))!=before or permissions(lab)!=grants or monitor_record_present(lab):
            raise RuntimeError('Focus/grants/monitor changed')
    def phase(name,**details):
        invariant();report['phases'].append(dict(name=name,checkpoint_unchanged=True,**details));save()
    def set_mute(value):
        disclosure(lab,'Companion preferences');node=lab.find('Mute companion voice')
        if (node.get('checked')=='true')!=value:lab.tap('Mute companion voice',scroll=False)
        wait_preferences(lab,lambda v:v.get('mute',False)==value)
    synthetic_created=False;mute_touched=False;save()
    try:
        disclosure(lab,'Choose your task & targets');set_test_field(lab,'content-desc','Focus task',GOAL)
        synthetic_created=True;lab.tap('Save task & targets')
        wait_preferences(lab,lambda v:v.get('focusGoal')==GOAL)
        disclosure(lab,'Write or edit my steps')
        set_test_field(lab,'resource-id',PACKAGE+':id/task_guide_editor','\n'.join(STEPS));lab.tap('Save these steps')
        original_record=assert_test_plan(preferences(lab));phase('synthetic_authored_guide_saved',count=3,completed=0)
        mute_touched=True;set_mute(True);lab.tap('Speak this step offline');lab.find(MUTED)
        if assert_test_plan(preferences(lab))!=original_record:raise RuntimeError('Muted readback changed guide')
        phase('muted_readback_refusal',ui_refusal_observed=True,engine_completion_observed=False)
        set_mute(False);lab.tap('Speak this step offline');report['unmuted_readback_tapped']=True;save()
        began=time.monotonic();outcome=None
        while time.monotonic()-began<35:
            values={OUTCOMES[n.get('text','')] for n in lab.nodes() if n.get('text','') in OUTCOMES}
            if len(values)>1:raise RuntimeError('Conflicting terminal readback states')
            if values:outcome=next(iter(values));break
            time.sleep(.25)
        if outcome is None:raise RuntimeError('No terminal readback outcome observed')
        report['tts_outcome']=outcome;report['engine_completion_callback_observed']=outcome=='engine_completed_callback';save()
        if assert_test_plan(preferences(lab))!=original_record:raise RuntimeError('Readback changed authored record')
        phase('unmuted_readback_terminal_ui',outcome=outcome,guide_record_unchanged=True)
        if outcome!='engine_completed_callback':raise RuntimeError('Readback did not complete; actual outcome preserved')
        lab.top();lab.tap('Ask Mira');lab.tap('Load verified local model')
        for _ in range(16):
            if any(n.get('text','').startswith('LOCAL MODEL LOADED') for n in lab.nodes()):break
            time.sleep(.25)
        else:raise RuntimeError('Pinned model did not load')
        result=lab.run('Stop focus',False);report['typed_model_regression']=result;save()
        if result['intent']!='pause_focus' or result['gate']!='REVIEW REQUIRED':raise RuntimeError('Current typed Pause regression failed; no action confirmed')
        lab.guard();lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000');lab.guard()
        if assert_test_plan(preferences(lab))!=original_record:raise RuntimeError('Model-screen roundtrip changed guide')
        phase('typed_pause_proposal_only',action_confirmed=False,guide_record_unchanged=True)
        report['completed']=True;save()
    except Exception as error:
        report['failure_type']=type(error).__name__
        report['failure']=str(error) if isinstance(error,(RuntimeError,ValueError,AssertionError)) else 'External operation failed; raw UI/output omitted'
        save();raise
    finally:
        try:
            lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000');lab.guard()
            if mute_touched:set_mute(False)
        except Exception:report['mute_cleanup_failed']=True
        report.update(cleanup(lab,before,synthetic_created))
        try:
            report['grants_after']=permissions(lab);report['final_mute']=preferences(lab).get('mute',False)
            report['cleanup_verified']=(report['cleanup_verified'] and report['grants_after']==grants
                                        and report['final_mute'] is False and not monitor_record_present(lab)
                                        and not report.get('mute_cleanup_failed',False))
        except Exception:report['cleanup_verified']=False
        save()
    if not report['cleanup_verified']:raise RuntimeError('Synthetic guide/mute/focus cleanup not verified')
    print(json.dumps({'completed':report['completed'],'tts_outcome':report['tts_outcome'],
                      'cleanup_verified':report['cleanup_verified'],'human_audibility_verified':False}),flush=True)


if __name__=='__main__':main()
