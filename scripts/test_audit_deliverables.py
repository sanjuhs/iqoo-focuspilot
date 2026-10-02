import tempfile,unittest,hashlib,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
from audit_deliverables import artifact_identity,release_parity,inspect_apk,LICENSES,sha,reports,captions,manual_proofs,phone_record,MODEL_SHA,synthetic_arithmetic
from audit_deliverables import command_confirmation_binding

class EvidenceAuditTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def write(self,name,data):
  p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
 def test_identity_detects_tampering_and_missing_file(self):
  p=self.write('artifact',b'good');expected={'bytes':4,'sha256':sha(p)}
  self.assertEqual('verified',artifact_identity(p,expected)['status']);p.write_bytes(b'evil');self.assertEqual('incomplete',artifact_identity(p,expected)['status']);p.unlink();self.assertEqual('missing',artifact_identity(p,expected)['status'])
 def test_release_metadata_needs_digest_size_and_upload_state(self):
  local={'bytes':4,'sha256':'a'*64};asset={'name':'app.apk','size':4,'digest':'sha256:'+'a'*64,'state':'uploaded'}
  self.assertEqual('verified',release_parity(local,[asset],'app.apk')['status']);asset['size']=5;self.assertEqual('incomplete',release_parity(local,[asset],'app.apk')['status']);asset.pop('digest');self.assertEqual('weak_evidence',release_parity(local,[asset],'app.apk')['status']);self.assertEqual('missing',release_parity(local,[],'app.apk')['status'])
 def test_apk_hash_does_not_prove_license_or_native_parity(self):
  for name,source in LICENSES.items():self.write(source,b'original notice')
  apk=self.root/'probe.apk'
  with ZipFile(apk,'w') as z:
   z.writestr('AndroidManifest.xml',b'fixture');z.writestr('classes.dex',b'fixture');z.writestr('lib/arm64-v8a/libfocuspilot_local.so',b'native')
   for name in LICENSES:z.writestr('assets/licenses/'+name,b'tampered notice' if name=='Qwen3.5-Apache-2.0.txt' else b'original notice')
  r=inspect_apk(apk,{'bytes':apk.stat().st_size,'sha256':sha(apk),'native_sha256':'wrong','bundled_model':False},self.root)
  self.assertEqual('verified',r['identity']['status']);self.assertFalse(r['runtime_verified']);self.assertFalse(r['native_hash_parity']);self.assertFalse(r['licenses']['Qwen3.5-Apache-2.0.txt']);self.assertEqual('incomplete',r['status'])
 def test_junit_failures_and_deceptive_case_counts_are_not_passes(self):
  p=self.write('tests/TEST-demo.xml',b'<testsuite tests="2" failures="0" errors="0"><testcase name="one"/></testsuite>')
  self.assertEqual('incomplete',reports(p.parent,self.root/'none')['status']);p.write_text('<testsuite tests="1" failures="1"><testcase name="one"><failure/></testcase></testsuite>');self.assertEqual('incomplete',reports(p.parent,self.root/'none')['status'])
  p.write_text('<testsuite tests="1" failures="0"><testcase name="one"><failure/></testcase></testsuite>');self.assertEqual('incomplete',reports(p.parent,self.root/'none')['status'])
 def test_missing_initial_manifests_return_structured_failure_not_success(self):
  process=subprocess.run([sys.executable,str(Path(__file__).with_name('audit_deliverables.py')),'--root',str(self.root)],text=True,capture_output=True,check=True)
  result=json.loads(process.stdout);self.assertFalse(result['goal_complete']);self.assertEqual('missing',result['checks']['artifact_manifest']['status']);self.assertIn('native_manifest',result['errors'])
 def test_captions_reject_overlap_and_out_of_video_time(self):
  p=self.write('captions.srt',b'1\n00:00:00,000 --> 00:00:02,000\nOne\n\n2\n00:00:01,000 --> 00:00:04,000\nTwo\n')
  self.assertEqual('incomplete',captions(p,3)['status']);p.write_text('1\n00:00:00,000 --> 00:00:02,000\nOne\n');self.assertEqual('verified',captions(p,3)['status'])
 def test_hash_present_manual_proof_never_self_certifies_npu(self):
  p=self.write('artifacts/trace.txt',b'synthetic test fixture')
  proof={'npu_execution':{'verified':True,'artifacts':[{'path':'artifacts/trace.txt','sha256':sha(p)}]}}
  r=manual_proofs(self.root,proof)['npu_execution'];self.assertTrue(r['proof_bundle_hashes_match']);self.assertFalse(r['claim_verified']);self.assertEqual('weak_evidence',r['status']);proof['npu_execution']['artifacts'][0]['path']='../private';self.assertFalse(manual_proofs(self.root,proof)['npu_execution']['proof_bundle_hashes_match'])
 def test_manual_proof_symlinks_cannot_read_outside_evidence_root(self):
  with tempfile.TemporaryDirectory() as outside:
   target=Path(outside)/'private';target.write_bytes(b'fixture')
   link=self.root/'artifacts/link';link.parent.mkdir();link.symlink_to(target)
   r=manual_proofs(self.root,{'npu_execution':{'artifacts':[{'path':'artifacts/link','sha256':sha(target)}]}})
   self.assertFalse(r['npu_execution']['proof_bundle_hashes_match'])
 def test_phone_run_requires_same_apk_native_model_not_labels(self):
  expected={'sha256':'a'*64,'native_sha256':'b'*64};r=phone_record({'backend':'CPU','tests':47},expected);self.assertEqual('weak_evidence',r['status'])
  record={'apk_sha256':'a'*64,'native_sha256':'b'*64,'model_sha256':MODEL_SHA,'backend':'CPU'};r=phone_record(record,expected);self.assertEqual('verified',r['status']);self.assertFalse(r['physical_offline_proof']);record['apk_sha256']='old';self.assertEqual('weak_evidence',phone_record(record,expected)['status'])
 def test_abstention_tradeoff_and_metric_fraud_are_visible(self):
  policy={'holdout':{'tp':2,'tn':2,'fp':1,'fn':0,'count':5,'accuracy':.8}}
  few={'summary':{'fixture':{'total':10,'answered':5,'abstained':5,'fewshot_correct':4,'baseline_correct':7,'coverage':.5,'selective_accuracy':.8}}}
  causal={'holdout':{'opposite_patch':{'intent_changes':0},'random_patch':{'intent_changes':0}},'native_calls':108,'noop_restore_full_logits_parity':True}
  r=synthetic_arithmetic(policy,few,causal);self.assertEqual(-3,r['fewshot']['fixture']['overall_correct_delta']);self.assertFalse(r['causal']['semantic_steering_advantage_established']);few['summary']['fixture']['coverage']=1;self.assertEqual('incomplete',synthetic_arithmetic(policy,few,causal)['status'])
 def test_confirmation_cannot_bind_changed_app_or_changed_result(self):
  repo=Path(__file__).resolve().parents[1];lab=Path('prototype/command-v10-confirm')
  for name in ('freeze-manifest.json','results.json','experiment-metadata.json','generate_data.py','protocol.json'):
   self.write(str(lab/name),(repo/lab/name).read_bytes())
  java=Path('prototype/android/app/src/main/java/dev/focuspilot/prototype')
  for name in json.loads((repo/lab/'freeze-manifest.json').read_text())['selected_source_sha256']:
   self.write(str(java/name),(repo/java/name).read_bytes())
  self.assertEqual('verified',command_confirmation_binding(self.root)['status'])
  self.assertFalse(command_confirmation_binding(self.root)['physical_verified'])
  gate=self.root/java/'ModelCommandGate.java';original=gate.read_bytes();gate.write_bytes(b'changed source')
  self.assertEqual('incomplete',command_confirmation_binding(self.root)['status']);gate.write_bytes(original)
  result=self.root/lab/'results.json';record=json.loads(result.read_text());record['gates']['generated']['selected']['supported_correct']=50;result.write_text(json.dumps(record))
  self.assertEqual('incomplete',command_confirmation_binding(self.root)['status'])
if __name__=='__main__':unittest.main()
