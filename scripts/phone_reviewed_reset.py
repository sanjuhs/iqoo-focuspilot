#!/usr/bin/env python3
"""Reset synthetic isolated stores only; production UI exercises Keep/Back/Home.

Requires the already unlocked own app, paused observation-off production state,
frozen light/test APK hashes, absent own services and matching pinned model.
Never confirms production Reset, grants permissions, wakes or clears app data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zipfile
from phone_model_smoke import PhoneLab, PACKAGE
from phone_task_guide import preferences, checkpoint
from phone_readback import permissions
from phone_bundled_import import preference_identity, private_file, pinned, services_absent, installed_sha, install, main_screen
from package_bundled_apk import project_bytes, ROOT

TEST_PACKAGE=PACKAGE+'.test'
RUNNER=TEST_PACKAGE+'/dev.focuspilot.prototype.ResetIsolationInstrumentation'
NATIVE='822695ae5ca3467392f48ff04d9eda824f52a5f470ba48264fd457f51881259e'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def snapshot(lab):
    return {'preferences':preference_identity(lab),'checkpoint':checkpoint(preferences(lab)),
            'grants':permissions(lab),'model':private_file(lab,'files/qwen35.gguf'),
            'services_absent':services_absent(lab)}

def require_test_application_absent(lab):
    result=subprocess.run(lab.base+['shell','pm','path',TEST_PACKAGE],text=True,capture_output=True,timeout=20)
    if result.returncode not in (0,1) or result.stderr.strip():raise RuntimeError('Cannot establish test application absence')
    if result.stdout.strip():raise RuntimeError('Existing test application respected; no replacement')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial',required=True);p.add_argument('--light',type=Path,required=True)
    p.add_argument('--test-apk',type=Path,required=True);p.add_argument('--light-sha',required=True)
    p.add_argument('--test-sha',required=True);p.add_argument('--source',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--execute-isolated-reset',action='store_true')
    a=p.parse_args()
    if not a.execute_isolated_reset:p.error('Explicit isolated synthetic reset flag required')
    output=a.output.resolve()
    if not output.is_relative_to(ROOT/'artifacts') or output.exists():raise RuntimeError('New ignored artifact record required')
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if source!=a.source:raise RuntimeError('Current commit differs from frozen source')
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise RuntimeError('Frozen clean worktree required')
    if sha(a.light)!=a.light_sha or sha(a.test_apk)!=a.test_sha:raise RuntimeError('Frozen APK differs')
    with zipfile.ZipFile(a.light) as apk:
        if hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()!=NATIVE:raise RuntimeError('Native differs')
        if any(name.endswith('.gguf') for name in apk.namelist()):raise RuntimeError('Light APK required')
    lab=PhoneLab(a.serial);lab.guard();before=snapshot(lab)
    if before['checkpoint']['active'] or before['checkpoint']['observation'] or not before['services_absent'] or not pinned(before['model']):raise RuntimeError('Paused/off/no services/pinned model required')
    require_test_application_absent(lab)
    if project_bytes(ROOT)+10_000_000>15_000_000_000:raise RuntimeError('Small test record storage reserve exceeds budget')
    record={'kind':'pre-event reviewed reset; isolated real Android repository and production UI cancellation only',
        'source_commit':source,'harness_sha256':sha(Path(__file__)),
        'light_apk':{'sha256':a.light_sha,'bytes':a.light.stat().st_size},
        'test_apk':{'sha256':a.test_sha,'bytes':a.test_apk.stat().st_size},
        'native_sha256':NATIVE,'before':before,'previous_installed_sha256':installed_sha(lab),'phases':[],
        'production_reset_confirmed':False,'permission_grants':0,'model_inference':False,
        'limitations':['Repository reconstruction is same-process persistence, not a process-restart/disk-read test.',
                      'Checklist/live-label sentinels verify key preservation, not full valid-record deserialization.',
                      'Generation-mismatch confirmation is source-reviewed, not physically exercised.',
                      'No microphone, monitoring, disconnected inference, NPU or Office Kit evidence.']}
    try:
        install(lab,a.light,a.light_sha)
        result=subprocess.run(lab.base+['install','-r',str(a.test_apk)],text=True,capture_output=True,timeout=90)
        if result.returncode or 'Success' not in result.stdout:raise RuntimeError('Synthetic test application install failed')
        path=lab.adb('shell','pm','path',TEST_PACKAGE).strip().split('package:',1)[1]
        if lab.adb('shell','sha256sum',path).split()[0]!=a.test_sha:raise RuntimeError('Installed synthetic test APK differs')
        run=subprocess.run(lab.base+['shell','am','instrument','-w',RUNNER],text=True,capture_output=True,timeout=45)
        raw=run.stdout
        required=('INSTRUMENTATION_RESULT: passed=true','INSTRUMENTATION_RESULT: production_singleton_used=false','INSTRUMENTATION_RESULT: isolated_stores=2','INSTRUMENTATION_CODE: -1')
        if run.returncode or not all(value in raw for value in required):raise RuntimeError('Isolated instrumentation did not pass')
        record['instrumentation']=raw
        leftovers=lab.adb('shell','run-as',PACKAGE,'ls','shared_prefs').splitlines()
        if any(name.startswith('reset_isolation_') for name in leftovers):raise RuntimeError('Isolated preference cleanup not established')
        if snapshot(lab)!=before:raise RuntimeError('Production snapshot changed during isolated test')
        record['phases'].append('isolated recovered + active reset; fixture cleanup; production snapshot exact')
        main_screen(lab);lab.top();lab.tap('Reset this session')
        lab.find('Reset your focus session?',False);lab.find('Reset session',False)
        if snapshot(lab)!=before:raise RuntimeError('Opening reset review changed production state')
        lab.tap('Keep session',False)
        if snapshot(lab)!=before:raise RuntimeError('Keep session changed production state')
        record['phases'].append('review and Keep session preserve all production snapshots')
        lab.tap('Reset this session');lab.find('Reset your focus session?',False)
        lab.guard();lab.adb('shell','input','keyevent','KEYCODE_BACK')
        if any(n.get('text')=='Reset your focus session?' for n in lab.nodes()) or snapshot(lab)!=before:raise RuntimeError('Back cancellation failed')
        record['phases'].append('Back cancels review with exact production snapshot')
        lab.tap('Reset this session');lab.find('Reset your focus session?',False)
        lab.guard();lab.adb('shell','input','keyevent','KEYCODE_HOME')
        # No launcher UI dump: return directly to the exact own activity.
        main_screen(lab)
        if any(n.get('text')=='Reset your focus session?' for n in lab.nodes()) or snapshot(lab)!=before:raise RuntimeError('Background review dismissal failed')
        record['phases'].append('Home/background dismisses review; own activity return preserves snapshot')
        record['after']=snapshot(lab);record['installed_sha256']=installed_sha(lab)
        if record['installed_sha256']!=a.light_sha:raise RuntimeError('Current installed light APK differs')
        record['passed']=True
    except Exception as error:
        record['passed']=False;record['failure_type']=type(error).__name__;record['failure']=str(error)
        raise
    finally:
        record['project_bytes_after']=project_bytes(ROOT)
        with output.open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps({'passed':record['passed'],'phases':len(record['phases']),
                      'checkpoint':record['after']['checkpoint'],'record':str(output)},indent=2))

if __name__=='__main__':main()
