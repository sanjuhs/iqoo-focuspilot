"""Pure report and ownership/failure-path tests; no ADB, model or APK execution."""
import copy
import json
import struct
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import phone_probe as probe

COMMIT='a'*40
SOURCES={'prototype/example.java':'b'*64}
CONTRACTS=[{'prompt_sha256':str(i)*64,'grammar_sha256':'f'*64} for i in range(6)]
BEFORE={'model':{'inode':123},'checkpoint':{'active':False,'observation':False},'services_absent':True}
NEW_SHA='c'*64


def valid_report():
    r={'schema':'focuspilot.native_page_isolation.v1','passed':True,'request_count':6,
       'completed_request_count':6,'watchdog_ms':120000,'watchdog_triggered':False,'model_unsafe':False,
       'model_closed':True,'model_loaded':True,'actions_executed':0,'failure_type':None,
       'source_commit':COMMIT,'declared_source_sha256':SOURCES,'installed_app_source_commit':probe.APP_SOURCE,'page_size_bytes':4096,'installed_apk_sha256':probe.APP_SHA,
       'native_sha256':probe.NATIVE,'checks':88,'java_model_load_ms':250,'java_instrumentation_ms':5000}
    for key in ('preferences_accessed','production_preferences_accessed','production_singleton_used',
                'services_started','ui_used','voice_used','network_settings_changed','permission_grants_changed',
                'airplane_mode_claim','npu_claim','causal_interpretation_claim','semantic_accuracy_is_infrastructure_pass_condition'):
        r[key]=False
    r['identity']={'target_package':probe.PACKAGE,'test_package':probe.TEST_PACKAGE,'process_name':probe.PACKAGE,
                   'target_process_name':probe.PACKAGE,'target_manifest_requests_internet':False,'test_manifest_requests_internet':False,
                   'target_context_process_internet_permission':-1,'process_uid':10000,'target_application_uid':10000,
                   'test_application_uid':10001,'process_pid':12}
    r['socket_probe']={'api':'android.system.Os.socket','family':2,'type':1,'protocol':6,
                       'connect_attempted':False,'dns_used':False,'payload_sent':False,'socket_creation_succeeded':False,
                       'returned_fd_closed':False,'socket_creation_denied':True,'permission_denial_proven':True,
                       'attempted_function':'socket','exception_type':'android.system.ErrnoException','permission_errno':13,'elapsed_ms':.5}
    m={'filename':'qwen35.gguf','bytes':probe.MODEL_BYTES,'verified_bytes':probe.MODEL_BYTES,
       'sha256':probe.MODEL_SHA,'links':1,'regular_file':True,'inode':123,'device':4,'mtime':12345,'verification_ms':.5}
    r['model_before']=m;r['model_after']=copy.deepcopy(m)
    apk={'sha256':probe.APP_SHA,'native_sha256':probe.NATIVE,'native_entry':'lib/arm64-v8a/libfocuspilot_local.so',
         'bytes':8000000,'inode':5,'device':4,'native_bytes':5000000}
    r['apk_before']=apk;r['apk_after']=copy.deepcopy(apk)
    r['requests']=[]
    for i,request in enumerate(probe.REQUESTS):
        gold=probe.canonical(probe.RAW_GOLD[i]);accepted=i!=5
        native={'text':json.dumps(probe.RAW_GOLD[i],separators=(',',':')),
                'metrics':{'reached_eos':True,'cpu_only':True,'capture_enabled':i==1,
                           'context_setup_ms':1.,'prefill_ms':10.,'decode_ms':20.,'total_ms':31.,
                           'prompt_tokens':380,'generated_tokens':20},'activations':[]}
        if i==1:
            native['activations']=[{'tensor':name,'width':1024,'positions_in_chunk':1,'mean':0.,'rms':1.,'min':-2.,'max':2.,'first_values':[0.]*8} for name in sorted(probe.TENSORS)]
        def checked(origin):
            return {'canonical':copy.deepcopy(gold),'accepted':accepted,'origin':origin if accepted else 'UNKNOWN',
                    'reason':'synthetic parser fixture','matches_illustration':True}
        fast=checked('FAST_LOCAL_REQUEST');model=checked('CHECKED_MODEL')
        row={'id':'native-unit-'+str(i+1),'request':request,'capture':i==1,**CONTRACTS[i],
             'illustrative_expected_raw':copy.deepcopy(probe.RAW_GOLD[i]),'illustrative_expected':copy.deepcopy(gold),
             'java_request_ms':32.,'native_output':native,'native_output_json':json.dumps(native),
             'raw_canonical':copy.deepcopy(gold),'raw_intent_matches_illustration':True,
             'raw_full_slots_match_illustration':True,'canonical_slots_match_illustration':True,
             'checked_model':model,'fast_local':fast,'product_pipeline':copy.deepcopy(fast)}
        r['requests'].append(row)
    return r


def envelope(r,code=-1):
    return 'INSTRUMENTATION_RESULT: report_json='+json.dumps(r)+'\nINSTRUMENTATION_CODE: '+str(code)+'\n'


class ReportTests(unittest.TestCase):
    def validate(self,r): return probe.validate_report(envelope(r),COMMIT,SOURCES,CONTRACTS,BEFORE)
    def test_valid_report_is_not_accuracy_requirement(self):
        r=valid_report();self.validate(r)
        # A safe unknown/refusal on a supported request does not fabricate success.
        row=r['requests'][0];n=row['native_output'];n['text']='{"intent":"unknown"}'
        row['native_output_json']=json.dumps(n);row['raw_canonical']={'intent':'unknown'}
        for key in ('raw_intent_matches_illustration','raw_full_slots_match_illustration','canonical_slots_match_illustration'): row[key]=False
        row['checked_model']={'canonical':{'intent':'unknown'},'accepted':False,'origin':'UNKNOWN','reason':'refused','matches_illustration':False}
        self.validate(r)
    def test_wrong_accepted_full_slots_is_unsafe(self):
        r=valid_report();r['requests'][0]['checked_model']['canonical']['duration_seconds']=21
        with self.assertRaises(probe.UnsafeReport): self.validate(r)
    def test_boolean_slot_not_integer(self):
        r=valid_report();r['requests'][2]['checked_model']['canonical']['hour']=True
        with self.assertRaises(probe.UnsafeReport): self.validate(r)
    def test_each_binding_and_process_permission_checked(self):
        mutations=[lambda r:r.update(source_commit='e'*40),lambda r:r.update(declared_source_sha256={}),
                   lambda r:r.update(installed_apk_sha256='e'*64),lambda r:r['requests'][3].update(prompt_sha256='e'*64),
                   lambda r:r['requests'][3].update(grammar_sha256='e'*64),lambda r:r['identity'].update(process_uid=55),
                   lambda r:r['identity'].update(target_context_process_internet_permission=0),
                   lambda r:r['socket_probe'].update(connect_attempted=True),lambda r:r['model_after'].update(inode=999),
                   lambda r:r['model_after'].update(mtime=54321),lambda r:r.update(page_size_bytes=16384),lambda r:r.update(installed_app_source_commit='e'*40),lambda r:r.update(java_instrumentation_ms=120000)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                r=valid_report();mutation(r)
                with self.assertRaises(ValueError):self.validate(r)
    def test_eos_token_timing_activation_and_order_bounds(self):
        def native_change(r,key,value):
            row=r['requests'][0];row['native_output']['metrics'][key]=value;row['native_output_json']=json.dumps(row['native_output'])
        for key,value in (('reached_eos',False),('generated_tokens',128),('prompt_tokens',True),('prompt_tokens',897),('prefill_ms',-1),('total_ms',float('nan'))):
            with self.subTest(key=key):
                r=valid_report();native_change(r,key,value)
                with self.assertRaises(ValueError):self.validate(r)
        r=valid_report();r['requests'].reverse()
        with self.assertRaises(ValueError):self.validate(r)
        r=valid_report();row=r['requests'][1];row['native_output']['activations'][0]['width']=512;row['native_output_json']=json.dumps(row['native_output'])
        with self.assertRaises(ValueError):self.validate(r)
    def test_one_terminal_report_and_no_duplicate_keys(self):
        r=valid_report()
        for raw in (envelope(r,0),envelope(r)+envelope(r),envelope(r).replace('"passed": true','"passed": true, "passed": true')):
            with self.assertRaises(ValueError):probe.validate_report(raw,COMMIT,SOURCES,CONTRACTS,BEFORE)


class ProtocolTests(unittest.TestCase):
    def test_protocol_matches_independent_manual_slots_and_bounds(self):
        protocol=probe.strict((probe.ROOT/'prototype/native-page-phone/protocol.json').read_text())
        sources={probe.JAVA_BASE+n+'.java':probe.sha(probe.ROOT/(probe.JAVA_BASE+n+'.java')) for n in ('LocalModel','CompatibleUnitCommand')}
        probe.verify_protocol(protocol,sources)
        for mutate in (lambda p:p['requests'][3]['expected'].update(duration_seconds=301),
                       lambda p:p['requests'][1].update(capture=False),
                       lambda p:p['native_calls'].update(maximum_actual_prompt_tokens=897),
                       lambda p:p['selected_target'].update(app_source_commit='e'*40),
                       lambda p:p['deadlines_and_cleanup'].update(host_instrumentation_timeout_seconds=151),
                       lambda p:p['deadlines_and_cleanup'].update(initial_test_install_client_timeout_seconds=46),
                       lambda p:p['deadlines_and_cleanup'].update(test_restore_install_client_timeout_seconds=181),
                       lambda p:p['deadlines_and_cleanup'].update(original_test_restore_non_streamed=False)):
            p=copy.deepcopy(protocol);mutate(p)
            with self.assertRaises(ValueError):probe.verify_protocol(p,sources)


class FakeLab:
    base=['adb','-s','fake']
    def __init__(self):self.sha=probe.RESTORE_SHA;self.commands=[]
    def adb(self,*args):self.commands.append(args);return ''


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.lab=FakeLab();self.attempts=[]
        self.addCleanup(patch.stopall)
        patch.object(probe,'installed_sha',return_value=probe.APP_SHA).start()
        patch.object(probe,'page_size',return_value=4096).start()
    def sha(self,lab):return lab.sha
    def test_install_timeout_observed_owned_is_accepted_once(self):
        calls=[]
        def run(command,timeout):
            calls.append(command);self.lab.sha=NEW_SHA
            return {'returncode':-9,'timed_out':True,'stdout':'','stderr':''}
        with patch.object(probe.replay,'test_sha',self.sha):
            result=probe.replace_test(self.lab,Path('/own-test.apk'),NEW_SHA,{probe.RESTORE_SHA},self.attempts,run)
        self.assertEqual(len(calls),1);self.assertNotIn('--no-streaming',calls[0]);self.assertTrue(result['owned_install_verified']);self.assertTrue(result['timed_out'])
    def test_restore_timeout_observed_original_is_cleanup_success(self):
        self.lab.sha=NEW_SHA;calls=[];timeouts=[]
        def run(command,timeout):
            calls.append(command);timeouts.append(timeout);self.lab.sha=probe.RESTORE_SHA
            return {'returncode':-9,'timed_out':True,'stdout':'','stderr':''}
        with patch.object(probe.replay,'test_sha',self.sha):
            result=probe.restore_test(self.lab,NEW_SHA,Path('/original.apk'),self.attempts,run)
        self.assertEqual(len(calls),1);self.assertIn('--no-streaming',calls[0]);self.assertEqual(timeouts,[180]);self.assertTrue(result['owned_install_verified'])
    def test_unknown_current_test_is_never_overwritten(self):
        self.lab.sha='f'*64
        with patch.object(probe.replay,'test_sha',self.sha),patch.object(probe,'polled') as run:
            with self.assertRaises(RuntimeError):probe.restore_test(self.lab,NEW_SHA,Path('/original.apk'),self.attempts,run)
            run.assert_not_called()
    def test_unsuccessful_install_no_retry(self):
        calls=[]
        def run(command,timeout):calls.append(command);return {'returncode':1,'timed_out':True,'stdout':'','stderr':''}
        with patch.object(probe.replay,'test_sha',self.sha):
            with self.assertRaises(RuntimeError):probe.replace_test(self.lab,Path('/own.apk'),NEW_SHA,{probe.RESTORE_SHA},self.attempts,run)
        self.assertEqual(len(calls),1);self.assertFalse(self.attempts[0]['owned_install_verified'])
    def test_execute_timeout_stops_only_target_then_restores(self):
        a=types.SimpleNamespace(test_apk=Path('/new.apk'),test_sha=NEW_SHA,restore_test_apk=Path('/original.apk'),source=COMMIT,source_hashes=SOURCES,contracts=CONTRACTS)
        record={'install_attempts':[],'restore_attempts':[]};calls=[]
        def run(command,timeout):
            calls.append(command)
            if 'install' in command:
                self.lab.sha=NEW_SHA if command[-1]=='/new.apk' else probe.RESTORE_SHA
                return {'returncode':-9,'timed_out':True,'stdout':'','stderr':''}
            return {'returncode':-9,'timed_out':True,'stdout':'','stderr':''}
        with patch.object(probe.replay,'test_sha',self.sha),patch.object(probe,'installed_sha',return_value=probe.APP_SHA),patch.object(probe,'snapshot',return_value=copy.deepcopy(BEFORE)):
            probe.execute(self.lab,a,record,BEFORE,run)
        self.assertFalse(record['passed']);self.assertTrue(record['original_test_restored']);self.assertTrue(record['protected_state_unchanged'])
        self.assertEqual(self.lab.commands,[('shell','am','force-stop',probe.PACKAGE)])
        self.assertEqual(sum('install' in c for c in calls),2)
        self.assertFalse(any('/target.apk' in c for c in calls));self.assertEqual([c[-1] for c in calls if 'install' in c],['/new.apk','/original.apk'])
    def test_success_with_restore_client_timeout_still_passes(self):
        a=types.SimpleNamespace(test_apk=Path('/new.apk'),test_sha=NEW_SHA,restore_test_apk=Path('/original.apk'),source=COMMIT,source_hashes=SOURCES,contracts=CONTRACTS)
        record={'install_attempts':[],'restore_attempts':[]}
        def run(command,timeout):
            if 'install' in command:
                self.lab.sha=NEW_SHA if command[-1]=='/new.apk' else probe.RESTORE_SHA
                return {'returncode':-9,'timed_out':True,'stdout':'','stderr':''}
            return {'returncode':0,'timed_out':False,'stdout':envelope(valid_report()),'stderr':''}
        with patch.object(probe.replay,'test_sha',self.sha),patch.object(probe,'installed_sha',return_value=probe.APP_SHA),patch.object(probe,'snapshot',return_value=copy.deepcopy(BEFORE)):
            probe.execute(self.lab,a,record,BEFORE,run)
        self.assertTrue(record['passed']);self.assertEqual(self.lab.commands,[])
        self.assertEqual(record['verified_completed_native_generations'],6);self.assertEqual(record['reported_completed_request_count'],6)
    def test_failed_partial_report_preserves_reported_completions(self):
        a=types.SimpleNamespace(test_apk=Path('/new.apk'),test_sha=NEW_SHA,restore_test_apk=Path('/original.apk'),source=COMMIT,source_hashes=SOURCES,contracts=CONTRACTS)
        record={'install_attempts':[],'restore_attempts':[],'verified_completed_native_generations':0}
        partial=valid_report();partial.update(passed=False,completed_request_count=3);partial['requests']=partial['requests'][:3]
        def run(command,timeout):
            if 'install' in command:
                self.lab.sha=NEW_SHA if command[-1]=='/new.apk' else probe.RESTORE_SHA
                return {'returncode':0,'timed_out':False,'stdout':'Success','stderr':''}
            return {'returncode':0,'timed_out':False,'stdout':envelope(partial,0),'stderr':''}
        with patch.object(probe.replay,'test_sha',self.sha),patch.object(probe,'installed_sha',return_value=probe.APP_SHA),patch.object(probe,'snapshot',return_value=copy.deepcopy(BEFORE)):
            probe.execute(self.lab,a,record,BEFORE,run)
        self.assertFalse(record['passed']);self.assertEqual(record['verified_completed_native_generations'],0)
        self.assertEqual(record['reported_completed_request_count'],3);self.assertTrue(record['original_test_restored'])
    def test_changed_target_identity_refuses_force_stop(self):
        a=types.SimpleNamespace(test_apk=Path('/new.apk'),test_sha=NEW_SHA,restore_test_apk=Path('/original.apk'),source=COMMIT,source_hashes=SOURCES,contracts=CONTRACTS)
        record={'install_attempts':[],'restore_attempts':[]};reads=iter([probe.APP_SHA,'f'*64,'f'*64,'f'*64])
        def run(command,timeout):
            if 'install' in command:self.lab.sha=NEW_SHA if command[-1]=='/new.apk' else probe.RESTORE_SHA
            return {'returncode':-9,'timed_out':True,'stdout':'','stderr':''}
        with patch.object(probe.replay,'test_sha',self.sha),patch.object(probe,'installed_sha',side_effect=lambda lab:next(reads)),patch.object(probe,'snapshot',return_value=copy.deepcopy(BEFORE)):
            probe.execute(self.lab,a,record,BEFORE,run)
        self.assertFalse(record['passed']);self.assertEqual(self.lab.commands,[]);self.assertEqual(record['force_stop_failure_type'],'RuntimeError')


class ElfAndPageBoundaryTests(unittest.TestCase):
    @staticmethod
    def elf():
        # Metadata-only ELF64 fixture: one load and one aligned RELRO header.
        value=bytearray(64+56*2);value[:6]=b'\x7fELF\x02\x01'
        struct.pack_into('<H',value,18,183);struct.pack_into('<Q',value,32,64)
        struct.pack_into('<HH',value,54,56,2)
        struct.pack_into('<IIQQQQQQ',value,64,1,5,0,0,0,0,32768,16384)
        struct.pack_into('<IIQQQQQQ',value,120,0x6474e552,4,0,0x4100,0,0,0x3f00,1)
        return value
    def test_aligned_metadata_and_boundary_rejections(self):
        result=probe.elf_layout(self.elf());self.assertTrue(result['structural_16k_alignment'])
        self.assertFalse(result['runtime_16k_environment_claim'])
        self.assertEqual(result['relro_segments'][0]['end'],0x8000)
        cases=[]
        value=self.elf();struct.pack_into('<Q',value,64+48,4096);cases.append(('4KiB load',value))
        value=self.elf();struct.pack_into('<Q',value,64+16,1);cases.append(('incongruent load',value))
        value=self.elf();struct.pack_into('<Q',value,120+40,0x3eff);cases.append(('unaligned RELRO',value))
        value=self.elf();struct.pack_into('<H',value,18,62);cases.append(('wrong ABI',value))
        value=self.elf();value[0]=0;cases.append(('bad magic',value))
        value=self.elf();struct.pack_into('<HH',value,54,55,2);cases.append(('nonstandard headers',value))
        cases.extend([('truncated header',b'\x7fELF'),('truncated program table',self.elf()[:-1])])
        for label,value in cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):probe.elf_layout(value)
    def test_actual_host_page_size_only_reads_exact_getconf(self):
        for text in ('16384\n','0\n','4096junk','4096\n16384',''):
            lab=FakeLab();lab.adb=lambda *args:text
            with self.subTest(text=text):
                with self.assertRaises(RuntimeError):probe.page_size(lab)
        lab=FakeLab()
        def read(*args):lab.commands.append(args);return '4096\n'
        lab.adb=read;self.assertEqual(probe.page_size(lab),4096)
        self.assertEqual(lab.commands,[('shell','getconf','PAGE_SIZE')])
    def test_wrong_host_page_preflight_makes_no_mutation(self):
        lab=FakeLab()
        def read(*args):lab.commands.append(args);return '16384\n'
        lab.adb=read
        a=types.SimpleNamespace(test_apk=Path('/new.apk'),test_sha=NEW_SHA,restore_test_apk=Path('/original.apk'),source=COMMIT,source_hashes=SOURCES,contracts=CONTRACTS)
        record={'install_attempts':[],'restore_attempts':[]}
        with patch.object(probe.replay,'test_sha',return_value=probe.RESTORE_SHA),patch.object(probe,'installed_sha',return_value=probe.APP_SHA),patch.object(probe,'snapshot',return_value=copy.deepcopy(BEFORE)),patch.object(probe,'polled') as run:
            probe.execute(lab,a,record,BEFORE,run);run.assert_not_called()
        self.assertFalse(record['passed']);self.assertEqual(record['install_attempts'],[])
        self.assertTrue(record['original_test_restored'])
        self.assertTrue(all(command==('shell','getconf','PAGE_SIZE') for command in lab.commands))


class PollTests(unittest.TestCase):
    def test_deadline_kills_client_and_uses_short_poll(self):
        class Process:
            returncode=None
            def poll(self):return self.returncode
            def kill(self):self.returncode=-9
            def wait(self,timeout):self.wait_timeout=timeout;return self.returncode
        process=Process();ticks=iter([0,0,1,1]);sleeps=[]
        result=probe.polled(['fake'],.5,popen=lambda *a,**k:process,clock=lambda:next(ticks),pause=sleeps.append)
        self.assertTrue(result['timed_out']);self.assertEqual(process.wait_timeout,1);self.assertEqual(sleeps,[.1])


if __name__=='__main__':unittest.main()
