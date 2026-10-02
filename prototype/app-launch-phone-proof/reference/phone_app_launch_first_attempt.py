#!/usr/bin/env python3
"""Reviewed Calculator/Clock launches; never inspect or interact with target UI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import zipfile

from phone_model_smoke import PhoneLab, PACKAGE
from phone_task_guide import checkpoint, preferences
from phone_readback import permissions, monitor_record_present

TOOLS = [
    ('calculator', ['-a','android.intent.action.MAIN','-c','android.intent.category.APP_CALCULATOR']),
    ('clock', ['-a','android.intent.action.SHOW_ALARMS']),
]


def resolve(lab, arguments):
    raw = lab.adb('shell','cmd','package','resolve-activity','--brief',*arguments)
    components = re.findall(r'^([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)$',raw,re.M)
    if len(components)!=1 or components[0].startswith('android/'):
        raise RuntimeError('Approved intent has no unique non-system target; nothing launched')
    return components[0]


def focused_component(lab):
    # Window metadata only. Never dump UI nodes, screenshots or target app contents.
    raw = lab.adb('shell','dumpsys','window')
    line = next((line for line in raw.splitlines() if 'mCurrentFocus=' in line),'')
    match = re.search(r'\s([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)(?:\s|})',line)
    return match[1] if match else None


def assert_unchanged(lab, before, grants):
    if checkpoint(preferences(lab))!=before or permissions(lab)!=grants or monitor_record_present(lab):
        raise RuntimeError('Own focus checkpoint, runtime grants or monitor state changed')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',required=True)
    parser.add_argument('--local-apk',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--execute-reviewed-app-launches',action='store_true')
    args=parser.parse_args()
    if not args.execute_reviewed_app_launches: parser.error('Explicit --execute-reviewed-app-launches required')
    lab=PhoneLab(args.serial);lab.guard()
    manifest_path=Path('docs/task-guide-artifacts.json');manifest=json.loads(manifest_path.read_text())
    source=manifest['source_commit']
    with args.local_apk.open('rb') as stream: apk_sha=hashlib.file_digest(stream,'sha256').hexdigest()
    expected=next((a for a in manifest['artifacts'] if a['sha256']==apk_sha),None)
    if expected is None: raise RuntimeError('Local APK not in current release manifest')
    installed=lab.adb('shell','pm','path',PACKAGE).strip().split('package:',1)[1]
    if lab.adb('shell','sha256sum',installed).split()[0]!=apk_sha: raise RuntimeError('Installed APK differs')
    if lab.adb('shell','run-as',PACKAGE,'sha256sum','files/qwen35.gguf').split()[0]!=manifest['model']['sha256']:
        raise RuntimeError('Private model differs')
    with zipfile.ZipFile(args.local_apk) as apk:
        native_sha=hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()
    if native_sha!=expected['native_sha256']:raise RuntimeError('Packaged native differs')
    sources={}
    for name in ['LocalModelActivity.java','LocalModel.java','ModelCommandGate.java']:
        path='prototype/android/app/src/main/java/dev/focuspilot/prototype/'+name
        data=Path(path).read_bytes()
        if data!=subprocess.check_output(['git','show',source+':'+path]):raise RuntimeError('Current app source differs')
        sources[path]=hashlib.sha256(data).hexdigest()
    before=checkpoint(preferences(lab));grants=permissions(lab)
    if before['active'] or before['observation'] or monitor_record_present(lab):raise RuntimeError('Requires paused/off/no monitor')
    targets={name:resolve(lab,intent) for name,intent in TOOLS}
    report=dict(research_only=True,source_commit=source,source_sha256=sources,apk_sha256=apk_sha,
                model_sha256=manifest['model']['sha256'],native_sha256=native_sha,
                harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                release_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                device={k:lab.adb('shell','getprop',p).strip() for k,p in
                        [('manufacturer','ro.product.manufacturer'),('model','ro.product.model'),
                         ('soc','ro.soc.model'),('api','ro.build.version.sdk')]},
                backend='CPU',before_checkpoint=before,permissions_before=grants,
                resolved_targets=targets,results=[],completed=False,
                target_ui_inspected=False,target_ui_interacted=False,alarm_or_timer_creation_tested=False,
                settings_changed=False,microphone_started=False,npu_verified=False,asr_verified=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        for target,_ in TOOLS:
            lab.top();lab.tap('Ask Mira');lab.tap('Load verified local model')
            for _ in range(16):
                if any(n.get('text','').startswith('LOCAL MODEL LOADED') for n in lab.nodes()):break
                time.sleep(.25)
            else:raise RuntimeError('Model did not load')
            result=lab.run('Open '+target,False)
            result.update(target=target,resolved_component=targets[target],cancel_verified=False,
                          confirmation_tapped=False,target_package_observed=False)
            report['results'].append(result);save()
            if result['intent']!='open_app' or result['gate']!='REVIEW REQUIRED':
                raise RuntimeError('Expected approved app not proposed; no confirmation or fallback')
            preview='Open the approved '+target+' app. Outcome is verified separately.'
            def review():
                lab.tap('Review proposed phone action')
                texts=[n.get('text','') for n in lab.nodes()]
                if not any('Your request: Open '+target+'\n\n'+preview in t for t in texts):
                    raise RuntimeError('Original request or bounded launch preview differs')
            review();lab.tap('Cancel',scroll=False);lab.guard()
            if focused_component(lab)!=PACKAGE+'/.LocalModelActivity':raise RuntimeError('Cancel did not retain own model screen')
            assert_unchanged(lab,before,grants);result['cancel_verified']=True;save()
            review();lab.tap('Confirm action',scroll=False);result['confirmation_tapped']=True;save()
            # From this point, no own-app UI operation until explicit return.
            began=time.monotonic();observed=None
            while time.monotonic()-began<12:
                candidate=focused_component(lab)
                if candidate and candidate.split('/')[0]==targets[target].split('/')[0]:
                    time.sleep(.4)
                    if focused_component(lab)==candidate:observed=candidate;break
                time.sleep(.25)
            if observed is None:raise RuntimeError('Approved target foreground package not observed')
            result.update(action_executed=True,observed_foreground_component=observed,
                          exact_resolved_component_observed=observed==targets[target],target_package_observed=True)
            assert_unchanged(lab,before,grants);save()
            lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000');lab.guard()
            result['returned_to_own_main']=True;save()
            print(json.dumps(result),flush=True)
        report['completed']=True;save()
    except Exception as error:
        report['failure_type']=type(error).__name__
        report['failure']=str(error) if isinstance(error,(RuntimeError,ValueError)) else 'External operation failed; raw output omitted'
        save();raise
    finally:
        try:
            lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000');lab.guard()
            assert_unchanged(lab,before,grants)
            report['final_checkpoint']=checkpoint(preferences(lab));report['permissions_after']=permissions(lab)
            report['cleanup_verified']=True
        except Exception:report['cleanup_verified']=False
        save()
    if not report['cleanup_verified']:raise RuntimeError('Final own-app state not verified')


if __name__=='__main__':main()
