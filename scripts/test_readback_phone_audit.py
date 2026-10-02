import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from audit_deliverables import readback_phone_binding, MODEL_SHA


class ReadbackReportBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.harness=['scripts/phone_readback.py','scripts/phone_model_smoke.py','scripts/phone_focus_actions.py','scripts/phone_task_guide.py']
        self.app=[f'prototype/android/app/src/main/java/dev/focuspilot/prototype/{name}.java' for name in ('SetupActivity','LocalModelActivity','LocalVoiceInput','FocusMonitorService','MainActivity')]
        for name in self.harness+self.app:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# source fixture, not executed\n')
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'add','--',*self.harness,*self.app],check=True)
        self.commit('Freeze fixture sources');app_commit=self.head()
        hashes={name:hashlib.sha256((self.root/name).read_bytes()).hexdigest() for name in self.harness}
        self.protocol_path=self.root/'prototype/readback-proof/protocol.json';self.protocol_path.parent.mkdir(parents=True,exist_ok=True)
        protocol={'prepared_before_physical_run':True,'selected_app_source':app_commit,'apk_sha256':'b'*64,'model_sha256':MODEL_SHA,'harness_sha256':hashes,'declared_tts_outcomes':['engine_completed_callback','offline_voice_unavailable']}
        self.protocol_path.write_text(json.dumps(protocol))
        subprocess.run(['git','-C',str(self.root),'add','--','prototype/readback-proof/protocol.json'],check=True)
        self.commit('Freeze protocol');harness_commit=self.head()
        self.manifest={'source_commit':app_commit,'artifacts':[{'bundled_model':False,'sha256':'b'*64,'native_sha256':'c'*64}]}
        checkpoint={'active':False,'observation':False,'points':100,'elapsed_ms':57331}
        self.record={'source_commit':app_commit,'apk_sha256':'b'*64,'native_sha256':'c'*64,'model_sha256':MODEL_SHA,'research_only':True,'completed':True,'cleanup_verified':True,
            'microphone_started':False,'permissions_or_settings_actions':False,'human_audibility_verified':False,'offline_disconnect_verified':False,'speech_recognition_tested':False,'npu_verified':False,
            'before_checkpoint':checkpoint,'final_checkpoint':copy.deepcopy(checkpoint),'own_monitor_service_record_absent_final':True,
            'phases':[{'name':'monitor_prerequisite_block','checkpoint_unchanged':True,'switch_restored_off':True,'own_service_record_absent':True},
                      {'name':'reviewed_pause_on_already_paused_session','checkpoint_unchanged':True,'action_executed':True,'original_request':'Stop focus'},
                      {'name':'explicit_readback_terminal_ui','checkpoint_unchanged':True,'outcome':'engine_completed_callback','independently_audible':False}],
            'typed_pause_result':{'command':'Stop focus','intent':'pause_focus','gate':'REVIEW REQUIRED','action_executed':True,'confirmation_tapped':True,'already_paused_before_action':True,'capture':False,'total_ms':1804.0,'prefill_ms':855.0,'decode_ms':949.0},
            'tts_outcome':'engine_completed_callback','engine_completion_callback_observed':True}
        self.raw=self.root/'prototype/readback-proof/result.json';self.raw.write_text(json.dumps(self.record))
        self.record.update(harness_source_commit=harness_commit,harness_sha256=hashes,
            app_source_sha256={name:hashlib.sha256((self.root/name).read_bytes()).hexdigest() for name in self.app},
            raw_report_sha256=hashlib.sha256(self.raw.read_bytes()).hexdigest(),protocol_file='prototype/readback-proof/protocol.json',protocol_sha256=hashlib.sha256(self.protocol_path.read_bytes()).hexdigest())

    def commit(self,message):subprocess.run(['git','-C',str(self.root),'-c','user.name=Evidence test','-c','user.email=evidence@example.invalid','commit','-qm',message],check=True)
    def head(self):return subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
    def audit(self,record=None):return readback_phone_binding(self.root,self.record if record is None else record,self.manifest)

    def test_callback_binding_still_does_not_certify_audible_asr_or_offline(self):
        result=self.audit();self.assertEqual(result['status'],'verified')
        for key in ('human_audibility_verified','actual_asr_verified','whole_device_offline_verified','full_voice_monitor_workflow_complete'):self.assertFalse(result[key])

    def test_callback_claim_cannot_replace_missing_or_failure_outcome(self):
        record=copy.deepcopy(self.record);record['tts_outcome']='offline_voice_unavailable'
        result=self.audit(record);self.assertEqual(result['status'],'incomplete');self.assertFalse(result['checks']['callback_classification'])

    def test_human_or_asr_claims_and_changed_elapsed_are_rejected(self):
        for key in ('human_audibility_verified','speech_recognition_tested','elapsed'):
            record=copy.deepcopy(self.record)
            if key=='elapsed':record['final_checkpoint']['elapsed_ms']+=1
            else:record[key]=True
            with self.subTest(key=key):self.assertEqual(self.audit(record)['status'],'incomplete')

    def test_rehashed_protocol_and_harness_cannot_escape_frozen_commit(self):
        (self.root/self.harness[0]).write_text('# different source\n')
        record=copy.deepcopy(self.record);record['harness_sha256'][self.harness[0]]=hashlib.sha256((self.root/self.harness[0]).read_bytes()).hexdigest()
        result=self.audit(record);self.assertEqual(result['status'],'incomplete');self.assertFalse(result['checks']['harness_bindings'])

    def test_reordered_phases_and_fabricated_metrics_are_rejected(self):
        for kind in ('phases','nan','boolean','sum'):
            record=copy.deepcopy(self.record)
            if kind=='phases':record['phases'].reverse()
            elif kind=='nan':record['typed_pause_result']['total_ms']=float('nan')
            elif kind=='boolean':record['typed_pause_result']['decode_ms']=True
            else:record['typed_pause_result']['total_ms']=1
            with self.subTest(kind=kind):self.assertEqual(self.audit(record)['status'],'incomplete')

    def test_raw_report_and_cleanup_failure_cannot_be_ignored(self):
        record=copy.deepcopy(self.record);record['cleanup_failure_type']='TimeoutExpired'
        self.assertEqual(self.audit(record)['status'],'incomplete')
        self.raw.write_text('{}');self.assertEqual(self.audit()['status'],'incomplete')


if __name__=='__main__':unittest.main()
