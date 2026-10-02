#!/usr/bin/env python3
"""Explicit reviewed 20-second own-app model countdown test; no OS permissions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from phone_model_smoke import PhoneLab, PACKAGE
from phone_focus_actions import MODEL_SHA


def checkpoint(lab):
    root=ET.fromstring(lab.adb('shell','run-as',PACKAGE,'cat','shared_prefs/focuspilot_research.xml'))
    state={'activeCheckpoint':'false','observe':'false','points':'100','elapsedCheckpoint':'0'}
    for node in root:
        if node.get('name') in state:state[node.get('name')]=node.get('value')
    return state


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',required=True)
    parser.add_argument('--local-apk',type=Path,required=True)
    parser.add_argument('--expected-apk-sha256',required=True)
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--execute-reviewed-countdown',action='store_true')
    parser.add_argument('--spoken-duration',action='store_true',help='Type a synthetic English-number duration; this does not test speech recognition')
    args=parser.parse_args()
    if not args.execute_reviewed_countdown:parser.error('This test starts focus; explicitly pass --execute-reviewed-countdown')
    if not re.fullmatch('[0-9a-f]{64}',args.expected_apk_sha256) or not re.fullmatch('[0-9a-f]{40}',args.source_commit):parser.error('Full artifact/source identities required')
    with args.local_apk.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=args.expected_apk_sha256:raise RuntimeError('Local APK mismatch; no phone action')
    with zipfile.ZipFile(args.local_apk) as apk:native=hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()
    lab=PhoneLab(args.serial);lab.adb('shell','input','keyevent','KEYCODE_WAKEUP');lab.guard()
    installed=lab.adb('shell','pm','path',PACKAGE).strip().split('package:',1)[1]
    observed=lab.adb('shell','sha256sum',installed).split()[0]
    model=lab.adb('shell','run-as',PACKAGE,'sha256sum','files/qwen35.gguf').split()[0]
    if observed!=digest or model!=MODEL_SHA:raise RuntimeError('Installed APK/model mismatch; no phone action')
    before=checkpoint(lab)
    if before['activeCheckpoint']!='false' or before['observe']!='false':raise RuntimeError('Requires already paused focus and observation off; existing session left unchanged')
    report={'research_only':True,'source_commit':args.source_commit,'apk_sha256':digest,'native_sha256':native,
      'model_sha256':model,'backend':'CPU/KleidiAI I8MM','native_identity_scope':'Library from local APK matching installed APK SHA256',
      'device':{name:lab.adb('shell','getprop',prop).strip() for name,prop in [('manufacturer','ro.product.manufacturer'),('model','ro.product.model'),('soc','ro.soc.model'),('api','ro.build.version.sdk')]},
      'typed_synthetic_test':True,'requested_seconds':20,'permissions_changed':False,'offline_disconnect_verified':False,'npu_verified':False,'results':[]}
    def save():
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    try:
        lab.top();lab.tap('Ask Mira');lab.tap('Load verified local model')
        for _ in range(16):
            if any(n.get('text','').startswith('LOCAL MODEL LOADED') for n in lab.nodes()):break
            time.sleep(.25)
        else:raise RuntimeError('Model did not load')
        request='Start focus for twenty seconds' if args.spoken_duration else 'Start focus for 20 seconds'
        report['synthetic_request']=request
        report['speech_recognition_tested']=False
        result=lab.run(request)
        report['results'].append(result);save()
        if result['intent']!='start_focus' or result['gate']!='REVIEW REQUIRED':raise RuntimeError('Unexpected model/gate proposal; never confirmed')
        lab.tap('Review proposed phone action')
        # Inspect only our own synthetic review dialog, and never confirm dropped duration.
        if not any('Start a focus countdown for 20 seconds' in n.get('text','') for n in lab.nodes()):raise RuntimeError('Review did not preserve requested duration; no confirmation')
        began=time.monotonic();lab.tap('Confirm action',scroll=False)
        active=checkpoint(lab)
        if active['activeCheckpoint']!='true' or active['observe']!='false' or active['points']!=before['points']:raise RuntimeError('Initial focus postcondition failed')
        result['action_executed']=True;result['active_after_confirmation']=True;save()
        while time.monotonic()-began<35:
            current=checkpoint(lab)
            if current['activeCheckpoint']=='false':break
            time.sleep(.5)
        else:raise RuntimeError('Countdown did not complete within process-live test window')
        delta=int(current['elapsedCheckpoint'])-int(before['elapsedCheckpoint'])
        report.update(auto_paused_without_user_stop=True,elapsed_checkpoint_delta_ms=delta,
            virtual_points_unchanged=current['points']==before['points'],observation_remained_off=current['observe']=='false')
        if delta!=20_000 or not report['virtual_points_unchanged'] or not report['observation_remained_off']:raise RuntimeError('Countdown deadline/accounting invariant failed')
        report['completed']=True;save();print(json.dumps(report),flush=True)
    finally:
        lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000');lab.guard()
        if checkpoint(lab)['activeCheckpoint']=='true':lab.tap('Stop focus',scroll=False)
        report['final_focus_paused']=checkpoint(lab)['activeCheckpoint']=='false';save()

if __name__=='__main__':main()
