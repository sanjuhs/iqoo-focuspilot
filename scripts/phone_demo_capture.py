#!/usr/bin/env python3
"""Explicit own-app, silent synthetic footage; no grants or action confirmation.

Records only after keyboard entry, removes system bars, watches foreground owner,
and requires scoped cleanup before footage can be used by a renderer. Raw/private
captures stay ignored; a separate visual privacy review is still required.
"""
import argparse
import hashlib
import json
import re
import subprocess
import threading
import time
from pathlib import Path

from phone_model_smoke import PACKAGE
from phone_guide_readback import GuideLab, GOAL, assert_test_plan, set_test_field, cleanup, OUTCOMES
from phone_task_guide import (STEPS, PREFIX, preferences, checkpoint, require_empty_test_state,
                             disclosure, wait_preferences)
from phone_readback import permissions, monitor_record_present
from phone_capture_benchmark import trace, request_details
from package_bundled_apk import project_bytes, ROOT


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


class Recorder:
    def __init__(self,lab,name,output):
        self.lab,self.name,self.output=lab,name,output
        self.remote='/sdcard/focuspilot-v012-'+name+'-demo.mp4'
        self.process=None;self.pid=None;self.stop_flag=threading.Event();self.failure=None
    def start(self):
        self.lab.guard()
        existing=subprocess.run(self.lab.base+['shell','pidof','screenrecord'],capture_output=True,text=True)
        if existing.stdout.strip():raise RuntimeError('Existing recorder respected; no capture started')
        if subprocess.run(self.lab.base+['shell','test','-e',self.remote]).returncode==0:
            raise RuntimeError('Existing capture file respected; refusing overwrite')
        self.log=(self.output/(self.name+'-recorder-private.log')).open('xb')
        self.process=subprocess.Popen(self.lab.base+['shell','screenrecord','--size','720x1594',
            '--bit-rate','4000000','--time-limit','90',self.remote],stdout=self.log,stderr=self.log)
        for _ in range(20):
            if self.process.poll() is not None:raise RuntimeError('Recorder ended before capture')
            p=subprocess.run(self.lab.base+['shell','pidof','screenrecord'],capture_output=True,text=True).stdout.strip()
            if re.fullmatch(r'\d+',p):
                cmd=self.lab.adb('shell','cat','/proc/'+p+'/cmdline')
                if self.remote in cmd:self.pid=p;break
            time.sleep(.1)
        if self.pid is None:raise RuntimeError('Owned recorder PID not observed')
        def watch():
            while not self.stop_flag.wait(.5):
                try:self.lab.guard()
                except Exception:
                    self.failure='Own-app foreground lost during capture';self.stop_flag.set();return
        self.thread=threading.Thread(target=watch,daemon=True);self.thread.start()
        self.started=time.monotonic()
    def finish(self):
        self.stop_flag.set()
        if hasattr(self,'thread'):self.thread.join(timeout=10)
        if self.process and self.process.poll() is None and self.pid:
            cmd=self.lab.adb('shell','cat','/proc/'+self.pid+'/cmdline')
            if self.remote not in cmd:raise RuntimeError('Recorder PID ownership changed; not signalled')
            self.lab.adb('shell','kill','-2',self.pid)
            self.process.wait(timeout=15)
        if hasattr(self,'log'):self.log.close()
        if self.failure:raise RuntimeError(self.failure)
        self.lab.guard()
        raw=self.output/(self.name+'-private-raw.mp4')
        if raw.exists():raise RuntimeError('Raw output already exists')
        self.lab.adb('pull',self.remote,str(raw))
        self.lab.adb('shell','rm',self.remote)
        result=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(raw)],text=True))
        streams=result['streams'];video=next(s for s in streams if s['codec_type']=='video')
        if (video['width'],video['height'])!=(720,1594) or any(s['codec_type']=='audio' for s in streams):
            raise RuntimeError('Unexpected capture size/audio; private raw retained, no selected output')
        target=self.output/(self.name+'.mp4')
        subprocess.run(['ffmpeg','-v','error','-n','-i',str(raw),'-vf','crop=720:1400:0:84',
            '-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
        seconds=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(target)],text=True))
        return {'name':self.name,'file':str(target.relative_to(ROOT)),'sha256':sha(target),
                'bytes':target.stat().st_size,'seconds':seconds,'raw_sha256':sha(raw),
                'crop':[720,1400,0,84],'speed':1,'audio_track':False,
                'own_foreground_guard':True,'raw_file_public':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--serial',required=True)
    p.add_argument('--execute-synthetic-own-app-recording',action='store_true');args=p.parse_args()
    if not args.execute_synthetic_own_app_recording:p.error('Explicit recording flag required')
    output=ROOT/'artifacts/v012-phone-demo';output.mkdir(exist_ok=True)
    report_path=output/'record.json'
    if report_path.exists():raise RuntimeError('Recording report exists; refusing repeat overwrite')
    if project_bytes(ROOT)+400_000_000>15_000_000_000:raise RuntimeError('Recording reserve exceeds project budget')
    manifest_path=ROOT/'docs/guidance-readback-artifacts.json';m=json.loads(manifest_path.read_text())
    lab=GuideLab(args.serial);lab.guard();initial=preferences(lab);require_empty_test_state(initial)
    if initial.get('mute',False) or monitor_record_present(lab):raise RuntimeError('Existing mute/monitor respected')
    installed=lab.adb('shell','pm','path',PACKAGE).strip().split('package:',1)[1]
    apk=lab.adb('shell','sha256sum',installed).split()[0]
    a=next((a for a in m['artifacts'] if a['sha256']==apk),None)
    if a is None:raise RuntimeError('Installed APK outside selected manifest')
    model=lab.adb('shell','run-as',PACKAGE,'sha256sum','files/qwen35.gguf').split()[0]
    if model!=m['model']['sha256']:raise RuntimeError('Retained model differs')
    for path,h in m['source_sha256'].items():
        if sha(ROOT/path)!=h or hashlib.sha256(subprocess.check_output(['git','show',m['source_commit']+':'+path])).hexdigest()!=h:
            raise RuntimeError('App source binding differs')
    before=checkpoint(initial);grants=permissions(lab)
    r={'kind':'Current own-app synthetic research recording; silent cropped phone footage',
       'source_commit':m['source_commit'],'apk_sha256':apk,'model_sha256':model,'native_sha256':a['native_sha256'],
       'harness_sha256':sha(Path(__file__)),'manifest_sha256':sha(manifest_path),
       'pre_run_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
       'before_checkpoint':before,'permissions_before':grants,'clips':[],'phases':[],
       'completed':False,'cleanup_verified':False,'visual_privacy_review':False,
       'microphone_started':False,'npu_verified':False,'human_audibility_verified':False,
       'offline_disconnect_verified':False,'action_confirmed':False,'os_settings_changed':False}
    def save():report_path.write_text(json.dumps(r,indent=2)+'\n')
    def phase(name,**extra):
        if checkpoint(preferences(lab))!=before or permissions(lab)!=grants or monitor_record_present(lab):
            raise RuntimeError('Checkpoint/grants/monitor changed')
        r['phases'].append({'name':name,**extra});save();print(name,flush=True)
    created=False;recorder=None;save()
    try:
        lab.adb('shell','am','force-stop',PACKAGE);lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity');lab.guard()
        disclosure(lab,'Choose your task & targets');set_test_field(lab,'content-desc','Focus task',GOAL)
        created=True;lab.tap('Save task & targets');wait_preferences(lab,lambda v:v.get('focusGoal')==GOAL)
        disclosure(lab,'Write or edit my steps');set_test_field(lab,'resource-id',PACKAGE+':id/task_guide_editor','\n'.join(STEPS))
        lab.tap('Save these steps');original=assert_test_plan(preferences(lab));phase('authored_synthetic_guide_saved')
        lab.tap("I've done this step");wait_preferences(lab,lambda v:v.get(PREFIX+'completed')==1)
        lab.tap('Undo last completed step');wait_preferences(lab,lambda v:v.get(PREFIX+'completed')==0)
        restored=assert_test_plan(preferences(lab))
        if {k:v for k,v in restored.items() if k!=PREFIX+'revision'}!={k:v for k,v in original.items() if k!=PREFIX+'revision'}:
            raise RuntimeError('Mark/undo failed guide text/progress restoration')
        if restored[PREFIX+'revision']==original[PREFIX+'revision']:raise RuntimeError('Mark/undo revision was not renewed')
        original=restored
        phase('mark_undo_verified_before_recording',progress_restored=True,revision_renewed=True)
        # Start only after entry; no keyboard or typing suggestions in selected footage.
        lab.find('Speak this step offline');recorder=Recorder(lab,'guide',output);recorder.start()
        time.sleep(1);lab.tap('Speak this step offline');outcome=None
        for _ in range(10):
            values={OUTCOMES[n.get('text','')] for n in lab.nodes() if n.get('text','') in OUTCOMES}
            if values:outcome=next(iter(values));break
        if outcome!='engine_completed_callback':raise RuntimeError('Recorded readback did not reach completion callback')
        time.sleep(2);r['clips'].append(recorder.finish());recorder=None
        if assert_test_plan(preferences(lab))!=original:raise RuntimeError('Recorded readback changed guide')
        phase('recorded_guide_readback_completed',outcome=outcome)
        lab.top();lab.tap('Ask Mira');lab.tap('Load verified local model')
        for _ in range(16):
            if any(n.get('text','').startswith('LOCAL MODEL LOADED') for n in lab.nodes()):break
        else:raise RuntimeError('Model load not observed')
        lab.command('Stop focus');node=lab.find('Capture selected actual activation summaries')
        if node.get('checked')!='true':lab.tap(node.get('text'),scroll=False)
        lab.find('Understand command locally');recorder=Recorder(lab,'model',output);recorder.start()
        time.sleep(1);lab.tap('Understand command locally')
        lab.guard();lab.adb('shell','input','swipe','540','1800','540','1100','250')
        began=time.monotonic();result=None
        while time.monotonic()-began<40:
            for n in lab.nodes():
                text=n.get('text','')
                if text.startswith('Model proposal:'):
                    match=re.search(r'CPU total ([\d.]+) ms · prefill ([\d.]+) ms · decode ([\d.]+) ms',text)
                    if not match:raise RuntimeError('Recorded native timing missing')
                    result={'command':'Stop focus','capture':True,'intent':text.splitlines()[0].split(': ')[1],
                            'gate':text.splitlines()[1].split(': ')[1],'total_ms':float(match[1]),
                            'prefill_ms':float(match[2]),'decode_ms':float(match[3]),'action_executed':False}
            if result:break
        if not result or result['intent']!='pause_focus' or result['gate']!='REVIEW REQUIRED':
            raise RuntimeError('Recorded Qwen request failed; no action confirmed')
        r['typed_model_request']=result;r['request_details']=request_details(lab,True);save();time.sleep(2)
        r['clips'].append(recorder.finish());recorder=None
        # Exact tensor proof is separate from the selected view/cropped movie.
        r['activation_observations']=trace(lab,True)
        if {e['tensor'] for e in r['activation_observations']}!={'ffn_out-0','ffn_out-11','ffn_out-23','result_norm'}:
            raise RuntimeError('Expected finite tensor selection missing')
        phase('recorded_typed_pause_proposal_only',action_confirmed=False)
        r['completed']=True;save()
    except Exception as error:
        r['failure_type']=type(error).__name__;r['failure']=str(error) if isinstance(error,RuntimeError) else 'External operation failed; raw details withheld';save();raise
    finally:
        if recorder:
            try:recorder.finish()
            except Exception:r['recorder_cleanup_failure']=True
        try:
            lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000');lab.guard()
            r.update(cleanup(lab,before,created));r['permissions_after']=permissions(lab)
            r['cleanup_verified']=r['cleanup_verified'] and r['permissions_after']==grants and not monitor_record_present(lab)
        except Exception:r['cleanup_verified']=False
        save()
    if not r['completed'] or not r['cleanup_verified']:raise RuntimeError('Recording or scoped cleanup incomplete')
    print(json.dumps({'completed':True,'cleanup_verified':True,'clips':[(c['name'],c['seconds']) for c in r['clips']]}),flush=True)


if __name__=='__main__':main()
