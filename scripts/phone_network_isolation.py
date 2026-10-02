#!/usr/bin/env python3
"""Synthetic Qwen probe in installed app process; private raw tensors stay ignored.

Replaces only an exactly pinned test APK, restores it after the run, and never
changes the user-facing APK, network settings, grants, preferences or model.
Instrumentation restarts/injects the paused target process. No activity is opened.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile
from phone_model_smoke import PhoneLab, PACKAGE
from phone_readback import permissions
from phone_task_guide import preferences, checkpoint
from phone_bundled_import import preference_identity, private_file, pinned, services_absent, installed_sha
from package_bundled_apk import ROOT, project_bytes, verified_certificate

APP_SHA='33c0f61cc60b6186bd9a091d9021ba3feb5cc4e8a46a30b58fc8ca34cb218a7b'
ORIGINAL_TEST_SHA='b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b'
NATIVE_SHA='822695ae5ca3467392f48ff04d9eda824f52a5f470ba48264fd457f51881259e'
TEST_PACKAGE=PACKAGE+'.test'
RUNNER=TEST_PACKAGE+'/dev.focuspilot.prototype.LocalModelIsolationInstrumentation'

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def test_sha(lab):
    paths=lab.adb('shell','pm','path',TEST_PACKAGE).strip().splitlines()
    if len(paths)!=1 or not paths[0].startswith('package:/data/app/'):raise RuntimeError('Exact installed test APK path required')
    return lab.adb('shell','sha256sum',paths[0].removeprefix('package:')).split()[0]

def restore_mode(original,current,candidate):
    if current==original:return 'already_restored'
    if current==candidate:return 'restore'
    raise RuntimeError('Unknown installed test APK retained; restoration refused')

def snapshot(lab):
    return {'preferences':preference_identity(lab),'checkpoint':checkpoint(preferences(lab)),
            'grants':permissions(lab),'model':private_file(lab,'files/qwen35.gguf'),
            'services_absent':services_absent(lab),'installed_app_sha256':installed_sha(lab)}

def install_test(lab,path,expected):
    run=subprocess.run(lab.base+['install','-r',str(path)],text=True,capture_output=True,timeout=90)
    if run.returncode or 'Success' not in run.stdout or test_sha(lab)!=expected:raise RuntimeError('Test APK replacement failed')

def instrumentation_entries(tree):
    entries=[];current=None;indent=-1
    for line in tree.splitlines():
        stripped=line.lstrip();depth=len(line)-len(stripped)
        if stripped.startswith('E:'):
            if current is not None and depth<=indent:entries.append(current);current=None
            if stripped.startswith('E: instrumentation '):current={};indent=depth
        elif current is not None:
            match=re.search(r'A: android:(name|targetPackage)\([^)]*\)="([^"]+)"',stripped)
            if match:
                if match[1] in current:raise RuntimeError('Duplicate instrumentation identity attribute')
                current[match[1]]=match[2]
    if current is not None:entries.append(current)
    return entries

def require_package(path,sdk,expected,runner=None):
    badging=subprocess.check_output([str(sdk/'aapt'),'dump','badging',str(path)],text=True)
    match=re.search(r"^package: name='([^']+)'",badging,re.M)
    if not match or match[1]!=expected:raise RuntimeError('Frozen package identity differs; nothing installed')
    if runner:
        tree=subprocess.check_output([str(sdk/'aapt'),'dump','xmltree',str(path),'AndroidManifest.xml'],text=True)
        entries=instrumentation_entries(tree)
        if sum(entry.get('name')==runner and entry.get('targetPackage')==PACKAGE for entry in entries)!=1:
            raise RuntimeError('Exact registered runner and target package required')

def parse_raw(raw):
    lines=[line.removeprefix('INSTRUMENTATION_RESULT: report_json=') for line in raw.splitlines()
           if line.startswith('INSTRUMENTATION_RESULT: report_json=')]
    if len(lines)!=1:raise RuntimeError('One complete structured runner report required')
    report=json.loads(lines[0])
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial',required=True);p.add_argument('--test-apk',type=Path,required=True)
    p.add_argument('--test-sha',required=True);p.add_argument('--source',required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--execute-synthetic-native-probe',action='store_true')
    a=p.parse_args()
    if not a.execute_synthetic_native_probe:p.error('Explicit synthetic native probe flag required')
    out=a.output_dir.resolve()
    if not out.is_relative_to(ROOT/'artifacts') or out.exists() or not out.parent.is_dir():raise RuntimeError('New ignored artifact directory in existing parent required')
    if subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=a.source or subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise RuntimeError('Frozen clean source commit required')
    original=ROOT/'artifacts/focuspilot-research-v013-reset-test.apk'
    if sha(original)!=ORIGINAL_TEST_SHA or sha(a.test_apk)!=a.test_sha or a.test_sha==ORIGINAL_TEST_SHA:raise RuntimeError('Exact original and distinct frozen candidate test APKs required')
    if sha(ROOT/'artifacts/focuspilot-research-v013-reset-light.apk')!=APP_SHA:raise RuntimeError('Frozen user-facing APK differs')
    sdk=Path.home()/'Library/Android/sdk/build-tools/36.0.0'
    require_package(original,sdk,TEST_PACKAGE,'dev.focuspilot.prototype.ResetIsolationInstrumentation')
    require_package(a.test_apk,sdk,TEST_PACKAGE,'dev.focuspilot.prototype.LocalModelIsolationInstrumentation')
    require_package(ROOT/'artifacts/focuspilot-research-v013-reset-light.apk',sdk,PACKAGE)
    certificates=[verified_certificate(sdk/'apksigner',path) for path in [original,a.test_apk,ROOT/'artifacts/focuspilot-research-v013-reset-light.apk']]
    if len(set(certificates))!=1:raise RuntimeError('Candidate test signing identity differs')
    for path in [original,a.test_apk,ROOT/'artifacts/focuspilot-research-v013-reset-light.apk']:
        requested=subprocess.check_output([str(sdk/'aapt'),'dump','permissions',str(path)],text=True)
        if 'android.permission.INTERNET' in requested:raise RuntimeError('Network permission present in frozen package')
        subprocess.run([str(sdk/'apksigner'),'verify',str(path)],check=True,capture_output=True)
    with zipfile.ZipFile(ROOT/'artifacts/focuspilot-research-v013-reset-light.apk') as app:
        if hashlib.sha256(app.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()!=NATIVE_SHA:raise RuntimeError('Frozen native differs')
    lab=PhoneLab(a.serial);before=snapshot(lab)
    if before['installed_app_sha256']!=APP_SHA or not pinned(before['model']) or not before['services_absent'] or before['checkpoint']['active'] or before['checkpoint']['observation']:raise RuntimeError('Pinned paused/off app and model with absent services required')
    if test_sha(lab)!=ORIGINAL_TEST_SHA:raise RuntimeError('Existing different test APK respected')
    if project_bytes(ROOT)+25_000_000>15_000_000_000:raise RuntimeError('Small capture reserve exceeds strict budget')
    out.mkdir()
    record={'kind':'Synthetic network-denied app-process native inference; not full offline workflow or airplane proof',
            'source_commit':a.source,'harness_sha256':sha(Path(__file__)),
            'candidate_test_apk':{'sha256':a.test_sha,'bytes':a.test_apk.stat().st_size},
            'original_test_apk_sha256':ORIGINAL_TEST_SHA,'before':before,'native_sha256':NATIVE_SHA,
            'network_settings_changed':False,'ui_or_phone_actions':False,'permission_grants':0,
            'instrumentation_restarts_target_process':True,'passed':False,'phases':[]}
    # Create a reviewable initial record before any device mutation.
    status=out/'status.json'
    def save():status.write_text(json.dumps(record,indent=2)+'\n')
    save()
    try:
        install_test(lab,a.test_apk,a.test_sha);record['phases'].append('exact candidate test APK installed');save()
        try:
            run=subprocess.run(lab.base+['shell','am','instrument','-r','-w',RUNNER],text=True,capture_output=True,timeout=150)
        except subprocess.TimeoutExpired as error:
            partial=error.stdout or b''
            (out/'runner-timeout.txt').write_bytes(partial if isinstance(partial,bytes) else partial.encode())
            raise RuntimeError('Native instrumentation timed out; target stopped before guarded test restoration') from error
        (out/'runner-raw.txt').write_text(run.stdout)
        (out/'runner-stderr.txt').write_text(run.stderr)
        report=parse_raw(run.stdout)
        (out/'runner-report.json').write_text(json.dumps(report,indent=2)+'\n')
        record['raw_report_sha256']=sha(out/'runner-report.json')
        record['raw_stdout_sha256']=sha(out/'runner-raw.txt');record['raw_stderr_sha256']=sha(out/'runner-stderr.txt')
        if run.returncode or report.get('passed') is not True or 'INSTRUMENTATION_CODE: -1' not in run.stdout:raise RuntimeError('Structured native probe did not pass; raw evidence retained privately')
        record['phases'].append('native probe completed; actual permission/socket and model results retained');save()
        pid=report.get('identity',{}).get('process_pid')
        if isinstance(pid,int) and pid>0:
            logs=lab.adb('shell','logcat','-d','--pid='+str(pid),'-s','FocusPilotBackend:I','*:S')
            (out/'backend-log.txt').write_text(logs)
            record['backend_log_sha256']=sha(out/'backend-log.txt')
            record['kleidiai_lines']=[line for line in logs.splitlines() if 'kleidiai:' in line]
        record['after_inference']=snapshot(lab)
        if record['after_inference']!=before:raise RuntimeError('Protected production snapshot changed after inference')
        record['passed']=True
    except Exception as error:
        record['failure_type']=type(error).__name__;record['failure']=str(error)
        raise
    finally:
        try:
            # am instrument may have timed out while native work is still alive.
            # Stop only the known paused own package before removing that runner.
            if snapshot(lab)!=before:raise RuntimeError('Production state changed concurrently; process stop and restoration refused')
            mode=restore_mode(ORIGINAL_TEST_SHA,test_sha(lab),a.test_sha)
            lab.adb('shell','am','force-stop',PACKAGE)
            if mode=='restore':install_test(lab,original,ORIGINAL_TEST_SHA)
            record['restored_test_sha256']=test_sha(lab)
            record['after_restoration']=snapshot(lab)
            if record['restored_test_sha256']!=ORIGINAL_TEST_SHA or record['after_restoration']!=before:raise RuntimeError('Restoration identities not exact')
            record['phases'].append('original test APK and protected production snapshot exact');record['restored']=True
        except Exception as error:
            record['passed']=False;record['restored']=False;record['restoration_failure_type']=type(error).__name__
            record['restoration_failure']=str(error)
        record['project_bytes_after']=project_bytes(ROOT);save()
    if record['passed'] is not True:raise RuntimeError('Probe or restoration incomplete')
    print(json.dumps({'passed':True,'restored':True,'phases':len(record['phases']),'checkpoint':record['after_restoration']['checkpoint'],'private_record':str(status)},indent=2))

if __name__=='__main__':main()
