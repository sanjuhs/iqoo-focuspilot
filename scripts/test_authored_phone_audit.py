import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from audit_deliverables import authored_phone_binding, MODEL_SHA


class AuthoredReportBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.paths=['prototype/phone-guide-proof/reference/phone_task_guide.py','scripts/phone_model_smoke.py','scripts/phone_focus_actions.py']
        for path in self.paths:
            p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# archived source fixture\n')
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'add','--',*self.paths],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Evidence test','-c','user.email=evidence@example.invalid','commit','-qm','Freeze fixture'],check=True)
        commit=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        source='a'*40;apk='b'*64;native='c'*64
        self.manifest={'source_commit':source,'artifacts':[{'bundled_model':False,'sha256':apk,'native_sha256':native}]}
        specs=[('synthetic_goal_saved',{}),('authored_steps_saved',{'count':3,'completed':0,'revision_present':True}),
            ('mark_ui_and_durable_state',{'completed':1}),('undo_ui_and_durable_state',{'completed':0}),
            ('process_restart_recovery',{'exact_record_preserved':True}),('all_steps_completed_ui',{'completed':3,'mark_disabled':True}),
            ('undo_after_complete',{'completed':2}),('replacement_cancel',{'exact_record_preserved':True}),
            ('replacement_confirmed',{'count':2,'completed':0}),('clear_cancel',{'exact_record_preserved':True}),
            ('clear_confirmed',{'task_goal_retained':True}),('clear_process_restart',{'guide_record_absent':True})]
        baseline={'active':False,'observation':False,'points':100,'elapsed_ms':20000}
        self.record={'source_commit':source,'apk_sha256':apk,'native_sha256':native,'model_sha256':MODEL_SHA,
            'research_only':True,'completed':True,'cleanup_verified':True,'empty_goal_restored':True,'guide_record_removed':True,
            'model_inference_performed':False,'permission_or_settings_actions':False,'tts_or_microphone_actions':False,
            'external_app_actions':False,'npu_verified':False,'private_original_text_exported':False,
            'before_checkpoint':baseline,'final_checkpoint':copy.deepcopy(baseline),
            'phases':[{'name':name,'checkpoint_unchanged':True,**extras} for name,extras in specs]}
        self.raw=self.root/'prototype/phone-guide-proof/result.json'
        self.raw.write_text(json.dumps(self.record))
        self.record.update(raw_report_sha256=hashlib.sha256(self.raw.read_bytes()).hexdigest(),harness_source_commit=commit,
            harness_sha256={path:hashlib.sha256((self.root/path).read_bytes()).hexdigest() for path in self.paths})

    def audit(self,record=None): return authored_phone_binding(self.root,self.record if record is None else record,self.manifest)

    def test_good_binding_still_does_not_certify_full_physical_goal(self):
        result=self.audit();self.assertEqual(result['status'],'verified')
        self.assertFalse(result['physical_independently_repeated']);self.assertFalse(result['full_task_guide_complete'])
        self.assertIn('readback',result['remaining'])

    def test_partial_source_reference_cannot_bind_current_app(self):
        record=copy.deepcopy(self.record);record['source_commit']='a'*7
        self.assertEqual(self.audit(record)['status'],'incomplete')

    def test_missing_reordered_duplicate_or_boolean_progress_is_rejected(self):
        for mutation in ('missing','reverse','duplicate','boolean'):
            record=copy.deepcopy(self.record)
            if mutation=='missing':record['phases'].pop()
            elif mutation=='reverse':record['phases'].reverse()
            elif mutation=='duplicate':record['phases'][-1]=record['phases'][0]
            else:record['phases'][2]['completed']=True
            with self.subTest(mutation=mutation):self.assertEqual(self.audit(record)['status'],'incomplete')

    def test_cleanup_failure_and_changed_elapsed_reject_terminal_success(self):
        for field in ('cleanup','elapsed'):
            record=copy.deepcopy(self.record)
            if field=='cleanup':record['cleanup_failure_type']='TimeoutExpired'
            else:record['final_checkpoint']['elapsed_ms']+=1
            with self.subTest(field=field):self.assertEqual(self.audit(record)['status'],'incomplete')

    def test_rehashed_mutable_harness_still_must_match_its_frozen_commit(self):
        path=self.paths[0];(self.root/path).write_text('# different source\n')
        record=copy.deepcopy(self.record);record['harness_sha256'][path]=hashlib.sha256((self.root/path).read_bytes()).hexdigest()
        result=self.audit(record);self.assertEqual(result['status'],'incomplete')
        self.assertFalse(result['checks']['harness_bindings'])

    def test_report_cannot_escape_evidence_inventory_or_disagree_with_raw_bytes(self):
        record=copy.deepcopy(self.record);record['harness_sha256']['../private.py']='d'*64
        self.assertEqual(self.audit(record)['status'],'incomplete')
        self.raw.write_text('{}');self.assertEqual(self.audit()['status'],'incomplete')


if __name__=='__main__':unittest.main()
