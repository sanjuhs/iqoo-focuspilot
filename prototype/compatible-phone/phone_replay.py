#!/usr/bin/env python3
"""Explicit v16→v17 pure Android validator replay; no UI/model/grants or actions.

Installs own frozen target/test APKs, preserves full protected state, and restores
only the exact known original test APK. The new target remains installed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from phone_model_smoke import PhoneLab, PACKAGE
from phone_reviewed_reset import snapshot, NATIVE
from phone_bundled_import import pinned, installed_sha, install
from package_bundled_apk import project_bytes, verified_certificate
import generate_fixtures as gen
from generate_fixtures import sha, strict, ignored_new

PREVIOUS_APP_SHA='1f25c95c7d58d354e55675778fc975768049495be20a05bf7cd709423b73218b'
RESTORE_TEST_SHA='b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b'
TEST_PACKAGE=PACKAGE+'.test'
RUNNER=TEST_PACKAGE+'/dev.focuspilot.prototype.CompatibleReplayInstrumentation'
CLASS_NAMES=[PACKAGE+'.'+name for name in ('ModelCommandGate','CompatibleUnitCommand','UnitCommand','StructuredCommand','CommandNumberWords','CompatibleActionRouter','CompatibleReviewState')]


def test_sha(lab):
    paths=lab.adb('shell','pm','path',TEST_PACKAGE).strip().splitlines()
    if len(paths)!=1 or not re.fullmatch(r'package:/data/app/[^\s]+/base\.apk',paths[0]):
        raise RuntimeError('Exact existing single test APK required; left unchanged')
    value=lab.adb('shell','sha256sum',paths[0][8:]).split()[0]
    if not re.fullmatch('[0-9a-f]{64}',value):raise RuntimeError('Installed test SHA unavailable')
    return value


def replace_test(lab,path,expected):
    run=subprocess.run(lab.base+['install','-r',str(path)],text=True,capture_output=True,timeout=90)
    if run.returncode or 'Success' not in run.stdout or test_sha(lab)!=expected:
        raise RuntimeError('Own test APK replacement failed')


def restore_test(lab,new_sha,original_path):
    """Never overwrite an unknown current package, even after a failed install."""
    current=test_sha(lab)
    if current==new_sha:replace_test(lab,original_path,RESTORE_TEST_SHA)
    elif current!=RESTORE_TEST_SHA:raise RuntimeError('Unknown test APK left intact; restoration refused')
    if test_sha(lab)!=RESTORE_TEST_SHA:raise RuntimeError('Original test APK restoration unverified')


def fixture_report(raw,asset_sha,source_hashes,host_commit=None):
    prefix='INSTRUMENTATION_RESULT: report_json='
    lines=[line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)]
    codes=[line for line in raw.splitlines() if line.startswith('INSTRUMENTATION_CODE:')]
    if len(lines)!=1 or codes!=['INSTRUMENTATION_CODE: -1']:
        raise ValueError('One final successful instrument report required')
    r=strict(lines[0])
    exact={'schema':'focuspilot.compatible_android_replay.v1','passed':True,'fixtures':100,
           'replay_checks':300,'expected_replay_checks':300,'review_checks':8,'expected_review_checks':8,
           'checks':308,'expected_checks':308,'failed_fixture_ids':[],'failure_type':None,
           'asset_sha256':asset_sha,'fixture_source_sha256':source_hashes,
           'target_package':PACKAGE,'test_package':TEST_PACKAGE,'target_process':PACKAGE,
           'actual_process':PACKAGE,'target_class_names':CLASS_NAMES,'actions_executed':0}
    for key,value in exact.items():
        if type(r.get(key)) is not type(value) or r.get(key)!=value:raise ValueError('Replay identity/count differs: '+key)
    for key in ('model_accessed','native_model_loaded','production_preferences_accessed',
                'production_singleton_used','services_started','voice_used','ui_started'):
        if r.get(key) is not False:raise ValueError('Impure replay: '+key)
    if (type(r.get('target_uid')) is not int or r['target_uid']<=0 or
            type(r.get('process_uid')) is not int or r['process_uid']!=r['target_uid'] or
            type(r.get('process_pid')) is not int or r['process_pid']<=0):
        raise ValueError('Target process UID/PID identity missing')
    if not re.fullmatch('[0-9a-f]{40}',r.get('host_source_commit','')) or (host_commit is not None and r['host_source_commit']!=host_commit):raise ValueError('Frozen host source attribution differs')
    expected={'baseline':{'CHECKED_MODEL':4,'UNKNOWN':96},
              'checked_model':{'CHECKED_MODEL':18,'UNKNOWN':82},
              'product_pipeline':{'FAST_LOCAL_REQUEST':4,'CHECKED_MODEL':15,'UNKNOWN':81}}
    if r.get('origins')!=expected:raise ValueError('Frozen actual origin aggregates differ')
    return r


def tool(command):
    r=subprocess.run(list(map(str,command)),text=True,capture_output=True,timeout=60)
    if r.returncode:raise RuntimeError('SDK inspection failed: '+Path(command[0]).name)
    return r.stdout


def manifest_info(badging,tree):
    match=re.search(r"^package: name='([^']+)' versionCode='([^']*)' versionName='([^']*)'",badging,re.M)
    if not match:raise ValueError('APK package/version missing')
    value={'package':match[1],'version_code':match[2],'version_name':match[3]}
    value['permissions']=re.findall(r"^uses-permission(?:-sdk-\d+)?: name='([^']+)'",badging,re.M)
    instrument=[];current=None;indent=0
    for line in tree.splitlines():
        if re.match(r'\s*E: ',line):
            level=len(line)-len(line.lstrip())
            if current is not None and level<=indent:instrument.append(current);current=None
            if re.match(r'\s*E: instrumentation\b',line):current={};indent=level
        elif current is not None:
            m=re.search(r'android:(name|targetPackage)\([^)]*\)="([^"]+)"',line)
            if m:current[m[1]]=m[2]
    if current is not None:instrument.append(current)
    value['instrumentation']=instrument
    return value


def dex_classes(data):
    """Read only standard DEX class definitions (not arbitrary string references)."""
    if len(data)<112 or data[:8] not in [b'dex\n'+v+b'\0' for v in (b'035',b'037',b'038',b'039',b'040')]:
        raise ValueError('Unsupported DEX header')
    size,header,endian=struct.unpack_from('<III',data,32)
    if size!=len(data) or header!=112 or endian!=0x12345678:raise ValueError('Invalid DEX layout')
    string_count,string_offset,type_count,type_offset=struct.unpack_from('<IIII',data,56)
    class_count,class_offset=struct.unpack_from('<II',data,96)
    def at(offset):
        if offset<0 or offset+4>len(data):raise ValueError('DEX index outside data')
        return struct.unpack_from('<I',data,offset)[0]
    out=[]
    for i in range(class_count):
        type_index=at(class_offset+32*i)
        if type_index>=type_count:raise ValueError('Invalid class type index')
        string_index=at(type_offset+4*type_index)
        if string_index>=string_count:raise ValueError('Invalid class descriptor index')
        offset=at(string_offset+4*string_index)
        # Descriptor strings are ASCII; skip at most five ULEB128 UTF16-length bytes.
        for _ in range(5):
            if offset>=len(data):raise ValueError('Truncated DEX string')
            byte=data[offset];offset+=1
            if byte<128:break
        else:raise ValueError('Malformed DEX string length')
        end=data.find(b'\0',offset)
        if end<0:raise ValueError('Unterminated DEX descriptor')
        out.append(data[offset:end].decode('ascii'))
    return out


def apk_classes(apk):
    names=[n for n in apk.namelist() if re.fullmatch(r'classes(?:[2-9][0-9]*)?\.dex',n)]
    if not names:raise ValueError('APK has no conventional DEX payload')
    out=[]
    for name in names:out.extend(dex_classes(apk.read(name)))
    return out


def inspect_apks(light,test,restore,tools,asset_sha):
    certs=[verified_certificate(tools/'apksigner',p) for p in (light,test,restore)]
    if len(set(certs))!=1:raise ValueError('Own APK public signing certificates differ')
    infos=[manifest_info(tool([tools/'aapt','dump','badging',p]),tool([tools/'aapt','dump','xmltree',p,'AndroidManifest.xml'])) for p in (light,test,restore)]
    if infos[0]['package']!=PACKAGE or infos[0]['version_code']!='17' or infos[0]['version_name']!='0.17-system-one-research':
        raise ValueError('Exact new v17 target required')
    if any(i['package']!=TEST_PACKAGE for i in infos[1:]):raise ValueError('Own test package required')
    expected={'name':PACKAGE+'.CompatibleReplayInstrumentation','targetPackage':PACKAGE}
    if infos[1]['instrumentation']!=[expected]:raise ValueError('Only selected pure replay runner may be registered')
    if 'android.permission.INTERNET' in infos[0]['permissions'] or any(i['permissions'] for i in infos[1:]):
        raise ValueError('No Internet target or new test permissions allowed')
    with zipfile.ZipFile(light) as z:
        if len(z.namelist())!=len(set(z.namelist())) or any(n.endswith('.gguf') for n in z.namelist()):raise ValueError('Unique light payload required')
        if hashlib.sha256(z.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()!=NATIVE:raise ValueError('Selected native differs')
        target_classes=apk_classes(z)
    with zipfile.ZipFile(test) as z:
        if len(z.namelist())!=len(set(z.namelist())) or hashlib.sha256(z.read('assets/compatible-fixtures.json')).hexdigest()!=asset_sha:
            raise ValueError('Exact generated test assets required')
        if any(n.endswith('.gguf') or n.startswith('lib/') for n in z.namelist()):raise ValueError('Pure test must have no native/model payload')
        test_classes=apk_classes(z)
    descriptors=['L'+n.replace('.','/')+';' for n in CLASS_NAMES]
    if any(target_classes.count(n)!=1 or n in test_classes for n in descriptors):raise ValueError('Validators must be defined once by target APK, never duplicated in test APK')
    if test_classes.count('Ldev/focuspilot/prototype/CompatibleReplayInstrumentation;')!=1:raise ValueError('Selected runner not defined exactly once in test APK')
    tool([tools/'zipalign','-c','-P','16','4',light])
    return {'public_certificate_sha256':certs[0],'manifests':infos,'native_sha256':NATIVE,
            'target_alignment':'zipalign -c -P 16 4 passed','model_payload_present':False,
            'target_class_definitions':descriptors,'test_defines_target_validators':False,
            'class_identity_limit':'DEX class ownership verified; original Java source hashes are frozen build attribution, not recoverable DEX source hashes'}


def execute(lab,a,record,before):
    """Mutation boundary; callers must complete all frozen local/device preflights first."""
    try:
        # Close the inspection/install race as far as a single-user ADB harness can.
        if installed_sha(lab)!=PREVIOUS_APP_SHA or test_sha(lab)!=RESTORE_TEST_SHA or snapshot(lab)!=before:
            raise RuntimeError('Protected baseline changed before replacement')
        install(lab,a.light,a.light_sha)
        if snapshot(lab)!=before:raise RuntimeError('Production snapshot changed during upgrade')
        if test_sha(lab)!=RESTORE_TEST_SHA:raise RuntimeError('Original test identity changed before replacement')
        replace_test(lab,a.test_apk,a.test_sha)
        run=subprocess.run(lab.base+['shell','am','instrument','-r','-w','-e','fixture_sha256',a.asset_sha,RUNNER],text=True,capture_output=True,timeout=45)
        record['instrumentation']=run.stdout
        if run.returncode:raise RuntimeError('Instrumentation process failed')
        record['report']=fixture_report(run.stdout,a.asset_sha,a.source_hashes,a.host_commit)
        if snapshot(lab)!=before or installed_sha(lab)!=a.light_sha:raise RuntimeError('Protected state or target identity changed')
        record['passed']=True
    except Exception as error:
        record['failure_type']=type(error).__name__;record['failure']=str(error)
    finally:
        try:
            restore_test(lab,a.test_sha,a.restore_test_apk)
            record['original_test_restored']=True
            record['after']=snapshot(lab);record['protected_state_unchanged']=record['after']==before
            record['installed_app_sha256']=installed_sha(lab)
            if not record['protected_state_unchanged'] or record['installed_app_sha256']!=a.light_sha:record['passed']=False
        except Exception as error:
            record['passed']=False;record['cleanup_failure_type']=type(error).__name__;record['cleanup_failure']=str(error)
    return record


def verify_fixture_manifest(manifest,inputs=None):
    """Rebuild inert asset bytes from hash-verified audit inputs; no Java/model calls."""
    if manifest.get('generator_sha256')!=sha(Path(__file__).with_name('generate_fixtures.py')):
        raise ValueError('Fixture generator source identity differs')
    if inputs is None:
        sources={name:ROOT/path for name,path in gen.SOURCE_PATHS.items()}
        sources.update({name:ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'/f'{name}.java'
                        for name in ('CompatibleActionRouter','CompatibleReviewState')})
        inputs=(ROOT/'prototype/compatible-data/build/confirmation.jsonl',
                ROOT/'prototype/unit-native/build/compatible-fresh-baseline-capture',
                ROOT/'prototype/unit-native/build/compatible-fresh-candidate-capture',
                ROOT/'prototype/compatible-eval/build/scoring',
                ROOT/'prototype/compatible-unit/fresh-result-audit.json',sources)
    text,rebuilt=gen.build(*inputs)
    if rebuilt!=manifest or hashlib.sha256(text.encode()).hexdigest()!=manifest.get('asset_sha256'):
        raise ValueError('Manifest is not the exact rebuilt independently audited asset')
    return rebuilt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('serial','source','light-sha','test-sha'):p.add_argument('--'+k,required=True)
    for k in ('light','test-apk','restore-test-apk','fixture-manifest','output'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--tools',type=Path,default=Path.home()/'Library/Android/sdk/build-tools/36.0.0')
    p.add_argument('--execute-own-compatible-fixtures',action='store_true');a=p.parse_args()
    if not a.execute_own_compatible_fixtures:p.error('Explicit own-app replay flag required')
    if not re.fullmatch('[0-9a-f]{40}',a.source) or any(not re.fullmatch('[0-9a-f]{64}',s) for s in (a.light_sha,a.test_sha)):p.error('Full source/APK identities required')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=a.source or subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise RuntimeError('Exact clean committed source required')
    out=ignored_new(a.output)
    if not out.is_relative_to(ROOT/'artifacts'):raise ValueError('Private phone report must be ignored artifacts')
    for path,expected in ((a.light,a.light_sha),(a.test_apk,a.test_sha),(a.restore_test_apk,RESTORE_TEST_SHA)):
        if sha(path)!=expected:raise ValueError('Frozen local APK identity differs')
    manifest=strict(a.fixture_manifest.read_text())
    if manifest.get('schema')!='focuspilot.compatible_replay_asset_manifest.v1' or manifest.get('rows')!=100 or manifest.get('replay_checks')!=300:raise ValueError('Fixture manifest differs')
    verify_fixture_manifest(manifest)
    a.asset_sha=manifest['asset_sha256'];a.source_hashes=manifest['source_sha256'];a.host_commit=manifest['host_source_commit']
    if not re.fullmatch('[0-9a-f]{64}',a.asset_sha) or set(a.source_hashes)!={n.rsplit('.',1)[1] for n in CLASS_NAMES}:raise ValueError('All target helper source pins required')
    for name,digest in a.source_hashes.items():
        if sha(ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'/f'{name}.java')!=digest:raise ValueError('Target copied source differs from generated fixtures')
    inspection=inspect_apks(a.light,a.test_apk,a.restore_test_apk,a.tools,a.asset_sha)
    if project_bytes(ROOT)+20_000_000>15_000_000_000:raise RuntimeError('Replay reserve exceeds project cap')
    lab=PhoneLab(a.serial);before=snapshot(lab)
    if before['checkpoint']['active'] is not False or before['checkpoint']['observation'] is not False or not before['services_absent'] or not pinned(before['model']) or installed_sha(lab)!=PREVIOUS_APP_SHA or test_sha(lab)!=RESTORE_TEST_SHA:raise RuntimeError('Exact paused/off/pinned v16/original-test baseline required')
    helpers={name:sha(ROOT/'scripts'/name) for name in ('phone_model_smoke.py','phone_reviewed_reset.py','phone_bundled_import.py','phone_task_guide.py','phone_readback.py','package_bundled_apk.py')}
    record={'schema':'focuspilot.compatible_phone_replay.v1','source_commit':a.source,'harness_sha256':sha(Path(__file__)),
            'helper_sha256':helpers,'generator_sha256':sha(Path(__file__).with_name('generate_fixtures.py')),'fixture_manifest_sha256':sha(a.fixture_manifest),
            'asset_sha256':a.asset_sha,'target_source_sha256':a.source_hashes,'before':before,'previous_app_sha256':PREVIOUS_APP_SHA,
            'light_apk_sha256':a.light_sha,'test_apk_sha256':a.test_sha,'restore_test_apk_sha256':RESTORE_TEST_SHA,
            'apk_inspection':inspection,'passed':False,'original_test_restored':False,'permission_grants':0,'ui_started':False,'phone_woken':False,'model_inference':False,
            'scope':'Already-seen host outputs through installed target pure classes; not new phone model accuracy, native timing, UI/ASR or actions'}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f:json.dump(record,f,indent=2)
    try:execute(lab,a,record,before)
    finally:record['project_logical_bytes_after']=project_bytes(ROOT);out.write_text(json.dumps(record,indent=2)+'\n')
    if not record['passed'] or not record['original_test_restored']:raise RuntimeError('Replay or protected restoration incomplete; consult ignored record')
    print(json.dumps({'passed':True,'protected_state_unchanged':True,'original_test_restored':True}))

if __name__=='__main__':main()
