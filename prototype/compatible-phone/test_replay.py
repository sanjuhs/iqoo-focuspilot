"""Local contracts and cleanup simulations only; never invokes ADB or model inference."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

import generate_fixtures as gen
import phone_replay as phone


class FixtureGenerationTests(unittest.TestCase):
    def corpus(self, folder):
        folder=folder.resolve()
        def save(path,value,jsonl=False):
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(('\n'.join(json.dumps(v) for v in value)+'\n') if jsonl else json.dumps(value))
        gold=folder/'gold.jsonl';scoring=folder/'scoring';base=folder/'baseline';candidate=folder/'candidate';audit=folder/'audit.json'
        rows=[{'id':f'fixture_{i}','utterance':f'Inert example {i}','expected':{'intent':'unknown'}} for i in range(100)]
        save(gold,rows,True)
        result={'rows':100,'gold_sha256':gen.sha(gold),'source_commit':'a'*40};save(scoring/'result.json',result)
        pins={str(gold):gen.sha(gold)}
        for directory in (base,candidate):
            records=[{'phase':'load'}]+[{'id':r['id'],'text':'{"intent":"unknown"}','metrics':{'reached_eos':True,'capture_enabled':False}} for r in rows]
            save(directory/'raw.jsonl',records,True)
            save(directory/'process.json',{'exit_code':0,'timed_out':False,'raw_sha256':gen.sha(directory/'raw.jsonl')})
            for name in ('raw.jsonl','process.json'):pins[str(directory/name)]=gen.sha(directory/name)
        for mode in gen.MODES:
            decisions=[{'id':r['id'],'gold':r['expected'],'raw':{'intent':'unknown'},'proposal':{'intent':'unknown'},'accepted':False,'origin':'UNKNOWN'} for r in rows]
            save(scoring/(mode+'-details.json'),decisions);pins[str(scoring/(mode+'-details.json'))]=gen.sha(scoring/(mode+'-details.json'))
        sources={}
        for name in gen.SOURCE_PATHS:
            path=folder/(name+'.java');path.write_text('synthetic source '+name);sources[name]=path;pins[str(path)]=gen.sha(path)
        save(audit,{'verified':True,'actual_result_sha256':gen.sha(scoring/'result.json'),'files_sha256':pins})
        return gold,base,candidate,scoring,audit,sources

    def test_full_seen_fixture_contract_is_reproducible(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.corpus(Path(d));text,manifest=gen.build(*args)
            self.assertEqual((text,manifest),gen.build(*args))
            payload=gen.strict(text);self.assertEqual(100,len(payload['fixtures']));self.assertEqual(300,manifest['replay_checks'])
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),manifest['asset_sha256'])
            self.assertEqual('UNKNOWN',payload['fixtures'][0]['expected']['product_pipeline']['origin'])

    def test_changed_capture_or_audit_identity_refused(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.corpus(Path(d));path=args[2]/'raw.jsonl';path.write_text(path.read_text().replace('unknown','timer',1))
            with self.assertRaisesRegex(ValueError,'not bound'):gen.build(*args)
        with tempfile.TemporaryDirectory() as d:
            args=self.corpus(Path(d));a=gen.load(args[4]);a['actual_result_sha256']='0'*64;args[4].write_text(json.dumps(a))
            with self.assertRaisesRegex(ValueError,'not bound'):gen.build(*args)

    def test_audited_decision_still_must_match_gold_and_actual_response(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.corpus(Path(d));path=args[3]/'baseline-details.json';rows=gen.load(path);rows[0]['gold']={'intent':'pause_focus'};path.write_text(json.dumps(rows))
            audit=gen.load(args[4]);audit['files_sha256'][str(path)]=gen.sha(path);args[4].write_text(json.dumps(audit))
            with self.assertRaisesRegex(ValueError,'gold/acceptance'):gen.build(*args)

    def test_manifest_rebuild_rejects_changed_generator_or_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.corpus(Path(d));_,manifest=gen.build(*args)
            self.assertEqual(manifest,phone.verify_fixture_manifest(manifest,args))
            altered=dict(manifest);altered['generator_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'generator'):phone.verify_fixture_manifest(altered,args)
            altered=dict(manifest);altered['input_sha256']=dict(manifest['input_sha256']);altered['input_sha256']['fabricated']='0'*64
            with self.assertRaisesRegex(ValueError,'rebuilt'):phone.verify_fixture_manifest(altered,args)
            path=args[3]/'result.json';value=gen.load(path);value['rows']=99;path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'not bound'):phone.verify_fixture_manifest(manifest,args)

    def test_strict_json_and_slot_types(self):
        for text in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):gen.strict(text)
        for value in ({'intent':'timer','duration_seconds':True},{'intent':'timer','duration_seconds':1.0},
                      {'intent':'unknown','hour':0},{'intent':'alarm','hour':24,'minute':0}):
            with self.assertRaises(ValueError):gen.canonical(value)


class PhoneHarnessTests(unittest.TestCase):
    def report(self):
        r={'schema':'focuspilot.compatible_android_replay.v1','passed':True,'fixtures':100,'replay_checks':300,
           'expected_replay_checks':300,'review_checks':8,'expected_review_checks':8,'checks':308,'expected_checks':308,
           'failed_fixture_ids':[],'failure_type':None,'asset_sha256':'1'*64,'fixture_source_sha256':{},
           'target_package':phone.PACKAGE,'test_package':phone.TEST_PACKAGE,'target_process':phone.PACKAGE,
           'actual_process':phone.PACKAGE,'target_class_names':phone.CLASS_NAMES,'actions_executed':0,
           'host_source_commit':'a'*40,'target_uid':10001,'process_uid':10001,'process_pid':42,
           'origins':{'baseline':{'CHECKED_MODEL':4,'UNKNOWN':96},'checked_model':{'CHECKED_MODEL':18,'UNKNOWN':82},
                     'product_pipeline':{'FAST_LOCAL_REQUEST':4,'CHECKED_MODEL':15,'UNKNOWN':81}}}
        for key in ('model_accessed','native_model_loaded','production_preferences_accessed','production_singleton_used','services_started','voice_used','ui_started'):r[key]=False
        return r
    def raw(self,r):return 'INSTRUMENTATION_RESULT: report_json='+json.dumps(r)+'\nINSTRUMENTATION_CODE: -1\n'

    def test_requires_exact_finished_counts_identity_and_inertness(self):
        r=self.report();self.assertTrue(phone.fixture_report(self.raw(r),'1'*64,{})['passed'])
        changes={'replay_checks':299,'checks':True,'process_uid':10002,'model_accessed':True,'asset_sha256':'2'*64,
                 'origins':{'product_pipeline':{'CHECKED_MODEL':19}}}
        for key,value in changes.items():
            altered=dict(r);altered[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):phone.fixture_report(self.raw(altered),'1'*64,{})
        for raw in (self.raw(r)+self.raw(r),self.raw(r).replace('INSTRUMENTATION_CODE: -1','INSTRUMENTATION_CODE: 0'),self.raw(r)+'INSTRUMENTATION_CODE: 0\n'):
            with self.assertRaises(ValueError):phone.fixture_report(raw,'1'*64,{})

    def test_restore_only_exact_known_original_or_run_owned_test(self):
        lab=Mock();path=Path('ignored-original.apk')
        with patch.object(phone,'test_sha',side_effect=['new',phone.RESTORE_TEST_SHA]),patch.object(phone,'replace_test') as replace:
            phone.restore_test(lab,'new',path);replace.assert_called_once_with(lab,path,phone.RESTORE_TEST_SHA)
        with patch.object(phone,'test_sha',return_value='unknown'),patch.object(phone,'replace_test') as replace:
            with self.assertRaisesRegex(RuntimeError,'Unknown'):phone.restore_test(lab,'new',path)
            replace.assert_not_called()

    def test_timeout_restores_test_and_checks_protected_state(self):
        before={'protected':'same'};lab=SimpleNamespace(base=['never-adb']);a=SimpleNamespace(light=Path('new.apk'),light_sha='new-app',test_apk=Path('test.apk'),test_sha='new-test',restore_test_apk=Path('original.apk'),asset_sha='1'*64,source_hashes={},host_commit='a'*40)
        record={'passed':False}
        with patch.object(phone,'installed_sha',side_effect=[phone.PREVIOUS_APP_SHA,'new-app']),patch.object(phone,'test_sha',return_value=phone.RESTORE_TEST_SHA),patch.object(phone,'snapshot',return_value=before),patch.object(phone,'install'),patch.object(phone,'replace_test'),patch.object(phone,'restore_test') as restore,patch.object(phone.subprocess,'run',side_effect=subprocess.TimeoutExpired('owned instrument',45)):
            phone.execute(lab,a,record,before)
        self.assertFalse(record['passed']);self.assertTrue(record['original_test_restored']);self.assertTrue(record['protected_state_unchanged']);restore.assert_called_once()
        self.assertEqual('TimeoutExpired',record['failure_type'])

    def test_manifest_rejects_missing_or_foreign_runner_at_inspection_boundary(self):
        badging="package: name='dev.focuspilot.prototype.test' versionCode='' versionName=''\n"
        tree='  E: instrumentation (line=2)\n    A: android:name(0x01010003)="dev.focuspilot.prototype.CompatibleReplayInstrumentation"\n    A: android:targetPackage(0x01010021)="dev.focuspilot.prototype"\n  E: application (line=3)\n    A: android:name(0x01010003)="elsewhere"\n'
        self.assertEqual([{'name':phone.PACKAGE+'.CompatibleReplayInstrumentation','targetPackage':phone.PACKAGE}],phone.manifest_info(badging,tree)['instrumentation'])
        with self.assertRaises(ValueError):phone.manifest_info('invalid',tree)

    def test_dex_class_ownership_uses_definitions_not_string_mentions(self):
        # One genuine definition plus another descriptor present only as a string reference.
        strings=[b'Ldev/focuspilot/prototype/Actual;',b'Ldev/focuspilot/prototype/ReferenceOnly;']
        data=bytearray(112+8+4+32);data[:8]=b'dex\n035\0'
        struct.pack_into('<III',data,32,0,112,0x12345678);struct.pack_into('<IIII',data,56,2,112,1,120);struct.pack_into('<II',data,96,1,124)
        struct.pack_into('<I',data,120,0);struct.pack_into('<I',data,124,0)
        for i,value in enumerate(strings):struct.pack_into('<I',data,112+4*i,len(data));data.extend(bytes([len(value)])+value+b'\0')
        struct.pack_into('<I',data,32,len(data));self.assertEqual([strings[0].decode()],phone.dex_classes(bytes(data)))
        struct.pack_into('<I',data,124,2)
        with self.assertRaises(ValueError):phone.dex_classes(bytes(data))


if __name__=='__main__':unittest.main()
