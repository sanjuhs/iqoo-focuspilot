#!/usr/bin/env python3
"""One guarded v19 -> v20 own-app replacement. No UI/wake/grants/inference.

Run from the repository root. Read-only full protected snapshot and APK checks
precede the single non-streamed install; preserve exact test package and data.
Raw snapshots stay in ignored artifacts, only scoped summary becomes public.
"""
import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from phone_model_smoke import PhoneLab,PACKAGE
from phone_reviewed_reset import snapshot
from phone_bundled_import import installed_sha,pinned
OLD='cb6cdb68af46d5cd476b5fca00a9375223ce69ad7bde5b641cd3ec0c8daef13f'
NEW='e128bd1986bad10ff00f385a22f0a1b70ac696ab7c42a547e65717a1d8789239'
TEST='b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b'
APK=ROOT/'artifacts/focuspilot-research-v020-mira-availability-light.apk'
RAW=ROOT/'artifacts/mira-availability-phone-install-v20-private.json'
PUBLIC=ROOT/'docs/mira-availability-phone-install-v20.json'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def test_sha(lab):
    paths=lab.adb('shell','pm','path',PACKAGE+'.test').strip().splitlines()
    if len(paths)!=1 or not paths[0].startswith('package:/data/app/'):raise RuntimeError('Original test identity unavailable')
    return lab.adb('shell','sha256sum',paths[0].removeprefix('package:')).split()[0]
def main():
    if sys.argv[1:]!=['--execute-own-v20-update']:raise RuntimeError('Explicit own-app update flag required')
    if RAW.exists() or PUBLIC.exists():raise RuntimeError('Existing record; no retry or overwrite')
    if sha(APK)!=NEW:raise RuntimeError('Frozen new APK differs')
    lab=PhoneLab('00162357R003362')
    if lab.adb('get-state').strip()!='device':raise RuntimeError('Authorized phone required')
    before=snapshot(lab)
    expected=json.loads((ROOT/'artifacts/native-page-v19-install.json').read_text())
    baseline=expected.get('after')
    if baseline is None:raise RuntimeError('Prior protected baseline unavailable')
    if before!=baseline or installed_sha(lab)!=OLD or test_sha(lab)!=TEST or not pinned(before['model']) or before['checkpoint']['active'] or before['checkpoint']['observation'] or not before['services_absent']:
        raise RuntimeError('Known paused protected v19 baseline differs; mutation refused')
    record={'schema':'focuspilot.mira_availability_install_private.v1','source_commit':subprocess.check_output(['git','rev-parse','81287b2'],cwd=ROOT,text=True).strip(),'harness_sha256':sha(Path(__file__)),'old_apk_sha256':OLD,'apk_sha256':NEW,'before':before,'attempts':1,'ui_used':False,'phone_woken':False,'permission_changes':0,'model_inference':False,'passed':False}
    start=time.monotonic()
    try:
        run=subprocess.run(lab.base+['install','--no-streaming','-r',str(APK)],text=True,capture_output=True,timeout=180)
        record['install_client']={'elapsed_ms':round((time.monotonic()-start)*1000),'exit_code':run.returncode}
        record['after']=snapshot(lab);record['installed_target_sha256']=installed_sha(lab)
        record['original_test_unchanged']=test_sha(lab)==TEST
        record['protected_state_unchanged']=record['after']==before
        record['target_installed']=record['installed_target_sha256']==NEW
        record['passed']=run.returncode==0 and 'Success' in run.stdout and all(record[k] for k in ('original_test_unchanged','protected_state_unchanged','target_installed'))
        if not record['passed']:raise RuntimeError('Installation/postcondition failed; no retry')
    except Exception as error:
        record['failure_type']=type(error).__name__
        raise
    finally:
        with RAW.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
        public={k:v for k,v in record.items() if k not in ('before','after')}
        public.update(schema='focuspilot.mira_availability_install.v1',private_record_sha256=sha(RAW),protected_scope='Three named preference-store semantic hashes/checkpoint; canonical model full SHA/bytes/inode/links; microphone/notification grants; own monitor/floating service absence; exact original test APK.',checkpoint=before['checkpoint'],physical_lock_unlock_verified=False,npu_verified=False)
        with PUBLIC.open('x') as f:json.dump(public,f,indent=2);f.write('\n')
    print(json.dumps({'passed':record['passed'],'target_installed':record['target_installed'],'protected_state_unchanged':record['protected_state_unchanged']}))
if __name__=='__main__':main()
