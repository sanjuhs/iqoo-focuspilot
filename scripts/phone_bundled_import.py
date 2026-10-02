#!/usr/bin/env python3
"""Reversible selected-v0.12 missing-model import with retained app data.

Preserve the original model by rename, never clear/uninstall/grant, and restore
the exact light package. Only verified run-owned imported bytes may be removed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile

from phone_model_smoke import PhoneLab, PACKAGE
from phone_task_guide import preferences, checkpoint, require_empty_test_state
from phone_readback import permissions
from phone_focus_recovery import APP_SOURCE, APK_SHA, NATIVE_SHA
from phone_focus_actions import MODEL_SHA
from package_bundled_apk import project_bytes, ROOT

BUNDLE_SHA='8fb78f14311ddec0c92357f95d13603a19b009a5add399a05e6284894c0ba088'
MODEL_BYTES=563036064
CANONICAL='files/qwen35.gguf'
STORES=('focuspilot_research','focuspilot_live_preferences','focuspilot_fewshot_sandbox')


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def private_file(lab,path):
    def test(flag):
        r=subprocess.run(lab.base+['shell','run-as',PACKAGE,'test',flag,path],capture_output=True,timeout=20)
        if r.returncode not in (0,1):raise RuntimeError('Cannot determine private-file state')
        return r.returncode==0
    if test('-L'):raise RuntimeError('Private test path is a symlink; left unchanged')
    if not test('-e'):return {'exists':False}
    if not test('-f'):raise RuntimeError('Private test path is not a regular file')
    size,inode,links=map(int,lab.adb('shell','run-as',PACKAGE,'stat','-c','%s:%i:%h',path).strip().split(':'))
    return {'exists':True,'bytes':size,'inode':inode,'links':links,
            'sha256':lab.adb('shell','run-as',PACKAGE,'sha256sum',path).split()[0]}


def pinned(info):
    return info.get('exists') and info.get('bytes')==MODEL_BYTES and info.get('sha256')==MODEL_SHA and info.get('links')==1


def restoration_mode(original,preserved,current,imported):
    """Refuse mutations unless the original and run-owned import are exact."""
    if not preserved.get('exists') and current==original:
        return 'already_restored'  # Preservation rename failed or was a no-op.
    if preserved!=original:
        raise RuntimeError('Protected original not intact; unknown files retained')
    if not current.get('exists'):
        return 'restore'
    if current!=imported or not pinned(current) or current['inode']==original['inode']:
        raise RuntimeError('Restoration target is not the recorded run-owned import; all files retained')
    return 'hold_then_restore'


def main_is_focused(window):
    focus=next((line for line in window.splitlines() if 'mCurrentFocus=' in line),'')
    component=re.search(r'(?:^|\s)'+re.escape(PACKAGE)+r'/([^\s}]+)',focus)
    return bool(component and component[1] in ('.MainActivity',PACKAGE+'.MainActivity'))


def preference_identity(lab):
    result={}
    for store in STORES:
        name='shared_prefs/'+store+'.xml'
        r=subprocess.run(lab.base+['shell','run-as',PACKAGE,'test','-f',name],capture_output=True,timeout=20)
        if r.returncode==1:result[store]={'exists':False};continue
        if r.returncode:raise RuntimeError('Cannot inspect named own preference store')
        tree=ET.fromstring(lab.adb('shell','run-as',PACKAGE,'cat',name))
        def item(n):return [n.tag,sorted(n.attrib.items()),n.text or '',[item(c) for c in n]]
        canonical=sorted([item(n) for n in tree],key=lambda n:dict(n[1]).get('name',''))
        result[store]={'exists':True,'semantic_sha256':hashlib.sha256(json.dumps(canonical,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()}
    return result


def services_absent(lab):
    raw=lab.adb('shell','dumpsys','activity','services',PACKAGE)
    return not re.search(re.escape(PACKAGE)+r'/(?:\.|'+re.escape(PACKAGE)+r'\.)(?:FocusMonitorService|FloatingCompanionService)\b',raw)


def installed_sha(lab):
    path=lab.adb('shell','pm','path',PACKAGE).strip().split('package:',1)[1]
    return lab.adb('shell','sha256sum',path).split()[0]


def install(lab,path,expected):
    r=subprocess.run(lab.base+['install','-r',str(path)],capture_output=True,text=True,timeout=180)
    if r.returncode or 'Success' not in r.stdout:raise RuntimeError('Own research package replacement failed; raw installer output suppressed')
    if installed_sha(lab)!=expected:raise RuntimeError('Installed package differs from selected artifact')


def main_screen(lab):
    lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity')
    lab.guard()  # No wake or keyguard bypass.


def load_model(lab):
    lab.top();lab.tap('Ask Mira');lab.tap('Load verified local model')
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        for n in lab.nodes():
            text=n.get('text','')
            if text.startswith('LOCAL MODEL LOADED'):return text
            if text.startswith('Load failed:'):raise RuntimeError('Local model load failed; model/runtime details remain on own screen')
        time.sleep(.25)
    raise RuntimeError('No successful model-load status within test window')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',required=True)
    parser.add_argument('--light-apk',type=Path,required=True)
    parser.add_argument('--bundled-apk',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--execute-retained-data-import',action='store_true')
    args=parser.parse_args()
    if not args.execute_retained_data_import:parser.error('Explicit retained-data import flag required')
    args.output=args.output.resolve()
    try:args.output.relative_to(ROOT/'artifacts')
    except ValueError:raise RuntimeError('Record must remain in ignored artifacts')
    if args.output.exists():raise RuntimeError('Existing evidence respected')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise RuntimeError('Commit harness and keep worktree clean')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if sha(args.light_apk)!=APK_SHA or sha(args.bundled_apk)!=BUNDLE_SHA:raise RuntimeError('Selected local APK identity mismatch')
    for path in (args.light_apk,args.bundled_apk):
        with zipfile.ZipFile(path) as z:
            if hashlib.sha256(z.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()!=NATIVE_SHA:raise RuntimeError('Selected native mismatch')
    with zipfile.ZipFile(args.bundled_apk) as z:
        entry=z.getinfo('assets/qwen35.gguf')
        if entry.file_size!=MODEL_BYTES or entry.compress_type!=zipfile.ZIP_STORED:raise RuntimeError('Bundled asset layout differs')
        with z.open(entry) as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=MODEL_SHA:raise RuntimeError('Bundled model differs')
    space=project_bytes(ROOT)
    if space+1_000_000>15_000_000_000:raise RuntimeError('Record reservation exceeds project cap')
    lab=PhoneLab(args.serial);lab.guard()
    if not main_is_focused(lab.adb('shell','dumpsys','window')):
        raise RuntimeError('Own MainActivity must be in front before this reversible test')
    require_empty_test_state(preferences(lab))
    if installed_sha(lab)!=APK_SHA:raise RuntimeError('Requires selected light installation before test')
    if not services_absent(lab):raise RuntimeError('Existing own service respected')
    before=checkpoint(preferences(lab));prefs_before=preference_identity(lab);grants=permissions(lab)
    free_kb=int(lab.adb('shell','df','-k','/data').splitlines()[-1].split()[3])
    if free_kb*1024<4_000_000_000:raise RuntimeError('Insufficient phone reserve for bundle/import/staging')
    nonce=uuid.uuid4().hex[:16]
    backup='files/qwen35-preserved-'+nonce+'.gguf'
    held='files/qwen35-import-check-'+nonce+'.gguf'
    original=private_file(lab,CANONICAL)
    if not pinned(original) or private_file(lab,backup)['exists'] or private_file(lab,held)['exists']:
        raise RuntimeError('Original model or unique backup precondition differs')
    report={'research_only':True,'scope':'Missing-model bundled import on retained app data; not a clean reinstall',
            'app_source_commit':APP_SOURCE,'harness_commit':commit,'harness_sha256':sha(Path(__file__)),
            'light_apk_sha256':APK_SHA,'bundled_apk_sha256':BUNDLE_SHA,'native_sha256':NATIVE_SHA,
            'model_sha256':MODEL_SHA,'backend':'CPU; current-run kernel selection not captured',
            'historical_pinned_native_backend':'KleidiAI I8MM; see earlier optimized CPU evidence','before':before,
            'preference_identity_before':prefs_before,'runtime_grants_before':grants,
            'original_model':original,'owned_backup_basename':Path(backup).name,'owned_hold_basename':Path(held).name,
            'phone_free_bytes_before':free_kb*1024,'project_bytes_before':space,
            'permissions_or_settings_actions':False,'app_data_cleared':False,'app_uninstalled':False,
            'separate_gguf_transfer':False,'offline_disconnect_verified':False,'npu_verified':False,
            'phases':[],'completed':False,
            'device':{name:lab.adb('shell','getprop',prop).strip() for name,prop in
                      [('manufacturer','ro.product.manufacturer'),('model','ro.product.model'),('soc','ro.soc.model'),('api','ro.build.version.sdk')]}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n')
    def phase(name,**details):
        if checkpoint(preferences(lab))!=before or permissions(lab)!=grants or not services_absent(lab):
            raise RuntimeError('Own state/grant/service invariant changed')
        report['phases'].append({'name':name,'checkpoint_unchanged':True,**details});save()
        print(json.dumps({'phase':name,**details}),flush=True)
    save()
    try:
        lab.guard()
        if not main_is_focused(lab.adb('shell','dumpsys','window')):
            raise RuntimeError('MainActivity changed before preservation; no test begun')
    except Exception:
        report['failure']='Foreground precondition changed; no test mutations or cleanup actions begun'
        save();raise
    try:
        lab.adb('shell','am','force-stop',PACKAGE)
        if private_file(lab,CANONICAL)!=original:raise RuntimeError('Original model changed before preservation')
        report['preservation_attempted']=True;save()
        lab.adb('shell','run-as',PACKAGE,'mv','-n',CANONICAL,backup)
        if private_file(lab,backup)!=original or private_file(lab,CANONICAL)['exists']:raise RuntimeError('Original model preservation not confirmed')
        phase('original_model_preserved',canonical_absent=True,no_model_copy=True)
        report['bundle_install_attempted']=True;save();install(lab,args.bundled_apk,BUNDLE_SHA)
        if private_file(lab,CANONICAL)['exists'] or private_file(lab,backup)!=original:raise RuntimeError('Model appeared before explicit bundled Load')
        phase('bundled_package_installed',installed_apk_sha256=BUNDLE_SHA,private_model_absent_before_load=True)
        main_screen(lab);report['load_attempted']=True;save();status=load_model(lab)
        imported=private_file(lab,CANONICAL)
        if not pinned(imported) or imported['inode']==original['inode'] or private_file(lab,backup)!=original:
            raise RuntimeError('New imported model or preserved original differs')
        report['imported_model']=imported;save()
        match=re.search(r'Bundled import \+ SHA verification ([\d.]+) ms; copied once into private storage',status)
        native=re.search(r'Private-file hash ([\d.]+) ms · native load ([\d.]+) ms',status)
        if not match or not native:raise RuntimeError('Actual imported branch not observed')
        phase('asset_import_and_cpu_load',import_and_sha_ms=float(match[1]),private_file_hash_ms=float(native[1]),native_load_ms=float(native[2]),independent_imported_file_verified=True)
        result=lab.run('Stop focus',capture=False,wake_display=False)
        if result['intent']!='pause_focus' or result['gate']!='REVIEW REQUIRED':raise RuntimeError('Expected unconfirmed Pause not proposed')
        phase('typed_pause_proposal_only',model_result=result)
        # A second load proves existing-file reuse without another import.
        lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000');lab.guard()
        status=load_model(lab)
        if 'Using existing private model; SHA verified' not in status or private_file(lab,CANONICAL)!=imported:
            raise RuntimeError('Second load did not preserve/reuse imported file')
        phase('second_load_reuses_imported_model',same_imported_inode_and_sha=True)
        report['completed']=True;save()
    except Exception as error:
        report['failure_type']=type(error).__name__
        report['failure']=str(error) if isinstance(error,(RuntimeError,ValueError)) else 'External operation failed; raw private output suppressed'
        save();raise
    finally:
        try:
            lab.adb('shell','am','force-stop',PACKAGE)
            preserved=private_file(lab,backup)
            if report.get('preservation_attempted'):
                current=private_file(lab,CANONICAL)
                mode=restoration_mode(original,preserved,current,report.get('imported_model'))
                report['restoration_mode']=mode;save()
                if mode=='hold_then_restore':
                    if private_file(lab,held)['exists']:
                        raise RuntimeError('Unexpected restoration target; all files retained')
                    lab.adb('shell','run-as',PACKAGE,'mv','-n',CANONICAL,held)
                    if private_file(lab,held)!=current or private_file(lab,CANONICAL)['exists']:
                        raise RuntimeError('Owned import hold not confirmed; files retained')
                if mode!='already_restored':
                    lab.adb('shell','run-as',PACKAGE,'mv','-n',backup,CANONICAL)
                if private_file(lab,CANONICAL)!=original or private_file(lab,backup)['exists']:
                    raise RuntimeError('Original restoration not confirmed')
                held_file=private_file(lab,held)
                if held_file['exists']:
                    if held_file!=report.get('imported_model') or not pinned(held_file) or held_file['inode']==original['inode']:
                        raise RuntimeError('Unexpected owned hold; left intact')
                    lab.adb('shell','run-as',PACKAGE,'rm',held)
                    if private_file(lab,held)['exists']:raise RuntimeError('Owned test copy cleanup not confirmed')
            if installed_sha(lab)!=APK_SHA:install(lab,args.light_apk,APK_SHA)
            main_screen(lab)
            final=checkpoint(preferences(lab));prefs_after=preference_identity(lab)
            report.update(final=final,preference_identity_after=prefs_after,runtime_grants_after=permissions(lab),
                          restored_light_apk_sha256=installed_sha(lab),restored_original_model=private_file(lab,CANONICAL))
            report['cleanup_verified']=(final==before and prefs_after==prefs_before and permissions(lab)==grants
                and services_absent(lab) and report['restored_light_apk_sha256']==APK_SHA
                and report['restored_original_model']==original and not private_file(lab,backup)['exists']
                and not private_file(lab,held)['exists'])
            save()
            if not report['cleanup_verified']:raise RuntimeError('Restoration invariant failed; preserve evidence')
        except Exception as error:
            report['cleanup_verified']=False
            report['restoration_failure']=str(error) if isinstance(error,(RuntimeError,ValueError)) else 'Restoration interrupted; original retained if not restored'
            save();raise


if __name__=='__main__':main()
