#!/usr/bin/env python3
"""Selected own-app export: two cancellation branches and optional local test save.

Only exact research defaults/empty labels are accepted. Provider XML stays in memory;
no directory entries, account text, payload or UI capture enters the public record.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

from phone_model_smoke import PhoneLab, PACKAGE, own_interactive_foreground
from phone_task_guide import preferences, checkpoint, require_empty_test_state
from phone_readback import permissions, monitor_record_present
from phone_focus_recovery import APP_SOURCE, APK_SHA

PROVIDER='com.google.android.documentsui'
COMPONENT=PROVIDER+'/com.android.documentsui.picker.PickActivity'
FILENAME='focuspilot-v012-export-test-20261003.json'
REMOTE='/sdcard/Download/'+FILENAME
ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def require_research_defaults(lab):
    p=preferences(lab);require_empty_test_state(p)
    if p.get('package','com.instagram.android')!='com.instagram.android' or p.get('budget',300000)!=300000:
        raise RuntimeError('Nondefault selected app/budget left unchanged')
    store='shared_prefs/focuspilot_live_preferences.xml'
    exists=subprocess.run(lab.base+['shell','run-as',PACKAGE,'test','-f',store],capture_output=True)
    if exists.returncode:
        if exists.returncode!=1: raise RuntimeError('Cannot determine live-label store state')
        return
    xml=ET.fromstring(lab.adb('shell','run-as',PACKAGE,'cat',store))
    for n in xml:
        if n.get('name')=='enabled' and n.get('value')!='false': raise RuntimeError('Existing matching left unchanged')
        if n.get('name')=='records_v1':
            records=json.loads(n.text)['records']
            if records: raise RuntimeError('Existing private labels left unchanged')


class Picker:
    def __init__(self,lab): self.lab=lab
    def guard(self):
        window=self.lab.adb('shell','dumpsys','window')
        activity=self.lab.adb('shell','dumpsys','activity','activities')
        if not own_interactive_foreground(window,activity,PROVIDER): raise RuntimeError('Expected unlocked document picker not in front')
        focus=next((line for line in window.splitlines() if 'mCurrentFocus=' in line),'')
        if COMPONENT not in focus: raise RuntimeError('Unexpected document-provider activity')
    def nodes(self):
        self.guard()
        temporary='/data/local/tmp/focuspilot-export-picker.xml'
        try:
            self.lab.adb('shell','uiautomator','dump',temporary)
            xml=ET.fromstring(self.lab.adb('shell','cat',temporary));self.guard()
            return [n for n in xml.iter('node') if n.get('package')==PROVIDER]
        finally:self.lab.adb('shell','rm','-f',temporary)
    def tap_node(self,n):
        xy=list(map(int,re.findall(r'\d+',n.get('bounds',''))))
        if len(xy)!=4 or xy[3]-xy[1]<25: raise RuntimeError('Picker control has unusable bounds')
        self.guard();self.lab.adb('shell','input','tap',str((xy[0]+xy[2])//2),str((xy[1]+xy[3])//2))
    def metadata(self):
        nodes=self.nodes()
        return {'resource_ids':sorted({n.get('resource-id') for n in nodes if n.get('resource-id')}),
                'known_controls':[{'resource_id':n.get('resource-id'),'class':n.get('class'),
                                   'text':n.get('text') if n.get('text') in ('Save','SAVE','Downloads') else '',
                                   'description':n.get('content-desc') if n.get('content-desc') in ('Show roots','Navigate up') else ''}
                                  for n in nodes if n.get('text') in ('Save','SAVE','Downloads') or n.get('content-desc') in ('Show roots','Navigate up')],
                'default_filename_editor_observed':any(n.get('class')=='android.widget.EditText' and n.get('text')=='focuspilot-private-summary.json' for n in nodes)}
    def save_local(self):
        # Navigate only fixed system controls. Unrelated file rows are never chosen.
        nodes=self.nodes()
        menu=next((n for n in nodes if n.get('content-desc') in ('Show roots','Navigate up')),None)
        if menu is None: raise RuntimeError('Local-storage navigation control not identified')
        self.tap_node(menu)
        nodes=self.nodes()
        downloads=next((n for n in nodes if n.get('text')=='Downloads' and n.get('resource-id','').endswith('/title')),None)
        if downloads is None: raise RuntimeError('Local Downloads root not identified; no destination chosen')
        self.tap_node(downloads)
        nodes=self.nodes()
        filename=next((n for n in nodes if n.get('class')=='android.widget.EditText' and n.get('text')=='focuspilot-private-summary.json'),None)
        if filename is None: raise RuntimeError('Expected synthetic filename editor not identified')
        self.tap_node(filename)
        self.lab.adb('shell','input','keycombination','113','29')
        self.lab.adb('shell','input','text',FILENAME)
        self.lab.adb('shell','input','keyevent','KEYCODE_BACK')
        nodes=self.nodes()
        if not any(n.get('class')=='android.widget.EditText' and n.get('text')==FILENAME for n in nodes):
            raise RuntimeError('Test filename readback mismatch; no save')
        save=next((n for n in nodes if n.get('text','').casefold()=='save' and n.get('enabled')=='true'),None)
        if save is None: raise RuntimeError('Enabled Save control not identified')
        self.tap_node(save)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',required=True)
    parser.add_argument('--local-apk',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--execute-export-test',action='store_true')
    parser.add_argument('--save-local',action='store_true')
    args=parser.parse_args()
    if not args.execute_export_test: parser.error('Explicit --execute-export-test required')
    args.output=args.output.resolve()
    try:args.output.relative_to(ROOT/'artifacts')
    except ValueError:raise RuntimeError('Evidence output must stay in ignored artifacts')
    if args.output.exists(): raise RuntimeError('Existing evidence respected')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(): raise RuntimeError('Commit harness first')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if digest(args.local_apk)!=APK_SHA: raise RuntimeError('Local selected APK mismatch')
    lab=PhoneLab(args.serial);lab.guard()
    apk=lab.adb('shell','pm','path',PACKAGE).strip().split('package:',1)[1]
    if lab.adb('shell','sha256sum',apk).split()[0]!=APK_SHA: raise RuntimeError('Installed selected APK mismatch')
    resolved=lab.adb('shell','cmd','package','resolve-activity','--brief','-a','android.intent.action.CREATE_DOCUMENT','-c','android.intent.category.OPENABLE','-t','application/json')
    if resolved.splitlines()[-1].strip()!=COMPONENT: raise RuntimeError('Unexpected document picker; no UI action')
    require_research_defaults(lab)
    before=checkpoint(preferences(lab));grants=permissions(lab)
    if monitor_record_present(lab): raise RuntimeError('Existing monitor left unchanged')
    if subprocess.run(lab.base+['shell','test','-e',REMOTE],capture_output=True).returncode!=1:
        raise RuntimeError('Existing test destination or uncertain absence; no overwrite')
    report={'research_only':True,'app_source_commit':APP_SOURCE,'apk_sha256':APK_SHA,
            'harness_commit':commit,'harness_sha256':digest(Path(__file__)),
            'document_picker_component':COMPONENT,'before':before,'runtime_grants_before':grants,
            'zero_saved_live_labels_precondition':True,'default_settings_empty_goal':True,
            'office_kit_verified':False,'npu_verified':False,'permissions_changed':False,
            'device':{name:lab.adb('shell','getprop',prop).strip() for name,prop in
                      [('manufacturer','ro.product.manufacturer'),('model','ro.product.model'),
                       ('soc','ro.soc.model'),('api','ro.build.version.sdk')]},
            'phases':[],'completed':False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def record(): args.output.write_text(json.dumps(report,indent=2)+'\n')
    def phase(name,**details):
        lab.guard()
        if checkpoint(preferences(lab))!=before: raise RuntimeError('Focus checkpoint changed')
        report['phases'].append({'name':name,'checkpoint_unchanged':True,**details});record()
        print(json.dumps({'phase':name,**details}),flush=True)
    def review():
        lab.top();lab.tap('Export my focus summary')
        if not any(n.get('text')=='Export your private summary?' for n in lab.nodes()): raise RuntimeError('Expected export review absent')
    record();picker=Picker(lab)
    try:
        review();lab.tap('Cancel',scroll=False)
        if any(n.get('text')=='Export your private summary?' for n in lab.nodes()):
            raise RuntimeError('Cancelled export review still open')
        phase('export_review_cancel',review_closed=True)
        review();lab.tap('Choose destination',scroll=False);picker.guard()
        report['picker_control_metadata']=picker.metadata();record()
        # Back cancels the exact picker we launched; no directory content inspected/exported.
        picker.guard();lab.adb('shell','input','keyevent','KEYCODE_BACK');lab.guard()
        lab.top();lab.find('Export cancelled or expired. No summary was written.')
        phase('document_picker_cancel',returned_to_own_app=True)
        if args.save_local:
            review();lab.tap('Choose destination',scroll=False);picker.save_local();lab.guard()
            lab.top();lab.find('Private summary exported to your chosen destination. It is outside app-data deletion.')
            data=lab.adb('shell','cat',REMOTE).encode('utf-8')
            if len(data)>80000: raise RuntimeError('Actual test export oversized')
            payload=json.loads(data)
            if payload['records']!=[] or payload['focus_active'] or payload['observation_enabled'] or payload['money_moved']:
                raise RuntimeError('Unexpected actual export state; payload kept private')
            if payload['focus_elapsed_ms']!=before['elapsed_ms'] or payload['virtual_points']!=before['points']:
                raise RuntimeError('Actual export checkpoint mismatch')
            source_hash=lab.adb('shell','sha256sum',REMOTE).split()[0]
            if hashlib.sha256(data).hexdigest()!=source_hash: raise RuntimeError('Read/source checksum mismatch')
            private=ROOT/'artifacts'/FILENAME
            if private.exists(): raise RuntimeError('Existing local private export respected')
            with private.open('xb') as output:output.write(data)
            aggregate=ROOT/'artifacts'/'phone-export-bridge-review-v012.json'
            if aggregate.exists(): raise RuntimeError('Existing aggregate respected')
            subprocess.run(['python3',str(ROOT/'prototype/bridge/review_export.py'),'--input',str(private),
                            '--expected-sha256',source_hash,'--output',str(aggregate)],cwd=ROOT,check=True,capture_output=True)
            replay=json.loads(aggregate.read_text())
            report['private_payload_public']=False
            phase('local_document_saved_and_received',bytes=len(data),source_sha256=source_hash,
                  received_sha256=digest(private),transport='ADB read of exact new local test file; not Office Kit',
                  zero_records=True,bridge_report_sha256=digest(aggregate),bridge_completed=True)
            # Retain only these exact test copies; never delete or inspect other phone files.
            report['test_phone_copy_retained']=True
            report['bridge_actual_report_scope']=list(replay.keys())
        report['completed']=True;record()
    except Exception as error:
        report['failure_type']=type(error).__name__
        report['failure']=str(error) if isinstance(error,(RuntimeError,ValueError)) else 'External operation failed; private values suppressed'
        record();raise
    finally:
        try:
            # If still in our exact picker, cancel it before returning to own app.
            try:picker.guard()
            except RuntimeError:pass
            else:lab.adb('shell','input','keyevent','KEYCODE_BACK')
            lab.guard();require_research_defaults(lab)
            final=checkpoint(preferences(lab));report['final']=final
            report['runtime_grants_after']=permissions(lab)
            report['cleanup_verified']=final==before and permissions(lab)==grants and not monitor_record_present(lab)
            if not report['cleanup_verified']: raise RuntimeError('Cleanup invariant failed')
            record()
        except Exception:
            report['cleanup_verified']=False;record();raise


if __name__=='__main__':main()
