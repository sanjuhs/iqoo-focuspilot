import tempfile,unittest,hashlib,json,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
from audit_deliverables import artifact_identity,release_parity,inspect_apk,LICENSES,sha,reports,captions,manual_proofs,phone_record,MODEL_SHA,synthetic_arithmetic
from audit_deliverables import command_confirmation_binding,current_pitch_audit,CURRENT_PITCH_RENDER_COMMIT,CURRENT_PITCH_APP_COMMIT,task_guide_source_binding
from unittest.mock import patch

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
 def current_pitch_fixture(self):
  source=self.write('docs/current-research-pitch-script.md',b'original narration')
  renderer=self.write('scripts/render_current_pitch.py',b'original renderer')
  policy_source=self.write('prototype/policy/policy.py',b'original policy')
  policy=self.write('prototype/policy/synthetic-model.json',json.dumps({'implementation_sha256':sha(policy_source)}).encode())
  gate=self.write('prototype/android/app/src/main/java/dev/focuspilot/prototype/ModelCommandGate.java',b'gate')
  adapter=self.write('prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java',b'adapter')
  narrative=self.write('docs/narrative.md',b'historical research')
  metrics=self.write('prototype/current-pitch/metrics.json',json.dumps({'current_app':{'source_commit':CURRENT_PITCH_APP_COMMIT,'gate_sha256':sha(gate),'prompt_adapter_sha256':sha(adapter)},'policy':{'checkpoint_sha256':sha(policy)},'sources':{'docs/narrative.md':{'sha256':sha(narrative),'source_commit':CURRENT_PITCH_APP_COMMIT}}}).encode())
  video=self.write('artifacts/pitch-current.mp4',b'video fixture')
  subtitle=self.write('artifacts/pitch-current.srt',b'1\n00:00:00,000 --> 00:00:02,000\nResearch\n')
  manifest={'app_source_commit':CURRENT_PITCH_APP_COMMIT,'source_sha256':sha(source),'renderer_sha256':sha(renderer),'metrics_sha256':sha(metrics),'policy_source_sha256':sha(policy_source),'policy_checkpoint_sha256':sha(policy),'video_sha256':sha(video),'captions_sha256':sha(subtitle),'evidence_bindings':{'docs/narrative.md':{'sha256':sha(narrative),'recorded_commit':CURRENT_PITCH_APP_COMMIT}},'phone_capture_used':False,'phone_actions_executed':0,'human_complete_audio_review':False,'seconds':200,'resolution':[1920,1080],'fps':24,'caption_segments':1}
  manifest_file=self.write('docs/current-pitch-render-manifest.json',json.dumps(manifest).encode())
  metadata={'render_source_commit':CURRENT_PITCH_RENDER_COMMIT,'app_source_commit':CURRENT_PITCH_APP_COMMIT,'source':str(source.relative_to(self.root)),'renderer':str(renderer.relative_to(self.root)),'metrics':str(metrics.relative_to(self.root)),'checks':{'seconds':200,'resolution':[1920,1080],'fps':24,'video_codec':'h264','audio_codec':'aac','audio_video_drift_seconds':0,'caption_segments':1,'full_decode':'reported previous pass','human_complete_audio_review':False,'live_phone_recording':False,'phone_capture_used':False,'phone_actions_executed':0,'npu_verified':False,'office_kit_verified':False}}
  for key,path in [('video',video),('captions',subtitle),('render_manifest',manifest_file)]:metadata[key]={'file':str(path.relative_to(self.root)),'bytes':path.stat().st_size,'sha256':sha(path)}
  self.write('docs/current-pitch-evidence.json',json.dumps(metadata).encode())
  frozen={CURRENT_PITCH_RENDER_COMMIT+':'+str(path.relative_to(self.root)):path.read_text() for path in (source,renderer,metrics,policy_source,policy)}
  frozen.update({CURRENT_PITCH_APP_COMMIT+':'+str(path.relative_to(self.root)):path.read_text() for path in (gate,adapter,narrative)})
  probe={'format':{'duration':'200.0'},'streams':[{'codec_type':'video','codec_name':'h264','width':1920,'height':1080,'duration':'200','avg_frame_rate':'24/1'},{'codec_type':'audio','codec_name':'aac','duration':'200'}]}
  def fake_command(args):
   if args[0]=='git':return frozen[args[-1]]
   if args[0]=='ffprobe':return json.dumps(probe)
   raise AssertionError('Unexpected process (decode replay is forbidden): '+str(args))
  return metadata,manifest,probe,fake_command
 def pitch_call(self,metadata,manifest,fake_command,probe_available=True):
  with patch('audit_deliverables.command',side_effect=fake_command),patch('audit_deliverables.shutil.which',return_value='/fixture/ffprobe' if probe_available else None):return current_pitch_audit(self.root,metadata,manifest)
 def test_current_pitch_binds_commits_and_attributes_prior_qa_without_live_proof(self):
  metadata,manifest,probe,runner=self.current_pitch_fixture();result=self.pitch_call(metadata,manifest,runner)
  self.assertEqual('verified',result['status']);self.assertEqual('attributed_report',result['prior_decode_qa']['status']);self.assertFalse(result['prior_decode_qa']['independently_repeated']);self.assertFalse(result['human_complete_audio_review_verified']);self.assertFalse(result['live_demo']);self.assertFalse(result['npu_verified'])
  metadata['app_source_commit']=CURRENT_PITCH_RENDER_COMMIT
  with patch('audit_deliverables.source_commit_binding',return_value=True):self.assertEqual('incomplete',self.pitch_call(metadata,manifest,runner)['status'])
 def test_current_pitch_rejects_missing_renderer_changed_narration_and_metric_binding(self):
  metadata,manifest,probe,runner=self.current_pitch_fixture();renderer=self.root/'scripts/render_current_pitch.py';original=renderer.read_bytes();renderer.unlink()
  result=self.pitch_call(metadata,manifest,runner);self.assertEqual('incomplete',result['status']);self.assertFalse(result['source_hash_bindings']['renderer_sha256']);renderer.write_bytes(original)
  source=self.root/'docs/current-research-pitch-script.md';original=source.read_bytes();source.write_bytes(b'changed narration')
  self.assertEqual('incomplete',self.pitch_call(metadata,manifest,runner)['status']);source.write_bytes(original)
  manifest['metrics_sha256']='0'*64
  self.assertEqual('incomplete',self.pitch_call(metadata,manifest,runner)['status'])
 def test_current_pitch_rejects_measured_stream_and_caption_mismatch(self):
  metadata,manifest,probe,runner=self.current_pitch_fixture();probe['streams'].pop()
  self.assertEqual('incomplete',self.pitch_call(metadata,manifest,runner)['status'])
  probe['streams'].append({'codec_type':'audio','codec_name':'aac','duration':'200'})
  subtitle=self.root/'artifacts/pitch-current.srt';subtitle.write_text('1\n00:03:19,000 --> 00:03:21,000\nLate\n')
  metadata['captions'].update(bytes=subtitle.stat().st_size,sha256=sha(subtitle));manifest['captions_sha256']=sha(subtitle)
  mf=self.root/'docs/current-pitch-render-manifest.json';mf.write_text(json.dumps(manifest));metadata['render_manifest'].update(bytes=mf.stat().st_size,sha256=sha(mf))
  result=self.pitch_call(metadata,manifest,runner);self.assertEqual('incomplete',result['status']);self.assertEqual('incomplete',result['captions']['status'])
 def test_task_guide_cannot_bind_changed_source_to_frozen_build(self):
  repo=Path(__file__).resolve().parents[1];commit='e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a'
  names=['prototype/android/app/src/main/java/dev/focuspilot/prototype/'+name for name in ('TaskPlan.java','TaskGuidePanel.java','MainActivity.java')]+['prototype/android/app/build.gradle','prototype/android/app/src/main/res/values/task_guide_resources.xml','prototype/android/app/src/test/java/dev/focuspilot/prototype/TaskPlanTest.java']
  frozen={};hashes={}
  for name in names:
   p=self.write(name,(repo/name).read_bytes());hashes[name]=sha(p);frozen[commit+':'+name]=p.read_text()
  manifest={'source_commit':commit,'source_sha256':hashes}
  with patch('audit_deliverables.command',side_effect=lambda args:frozen[args[-1]]):
   r=task_guide_source_binding(self.root,manifest);self.assertEqual('verified',r['status']);self.assertFalse(r['physical_verified'])
   (self.root/names[1]).write_bytes(b'changed guide')
   self.assertEqual('incomplete',task_guide_source_binding(self.root,manifest)['status'])
 def test_signed_apk_wrong_version_cannot_pass_declared_release(self):
  for name,source in LICENSES.items():self.write(source,b'notice')
  p=self.root/'fixture.apk'
  with ZipFile(p,'w') as z:
   z.writestr('AndroidManifest.xml',b'manifest');z.writestr('classes.dex',b'dex');z.writestr('lib/arm64-v8a/libfocuspilot_local.so',b'native')
   for name in LICENSES:z.writestr('assets/licenses/'+name,b'notice')
  declared={'bytes':p.stat().st_size,'sha256':sha(p),'native_sha256':hashlib.sha256(b'native').hexdigest(),'bundled_model':False,'version_code':11,'version_name':'guide'}
  version=11
  def tools(args):
   if 'permissions' in args:return 'package: dev.focuspilot.prototype'
   if 'badging' in args:return "package: name='dev.focuspilot.prototype' versionCode='"+str(version)+"' versionName='guide'"
   return ''
  with patch('audit_deliverables.command',side_effect=tools):
   self.assertEqual('verified',inspect_apk(p,declared,self.root,'aapt','signer')['status'])
   version=10;r=inspect_apk(p,declared,self.root,'aapt','signer');self.assertEqual('incomplete',r['status']);self.assertFalse(r['version_parity'])
if __name__=='__main__':unittest.main()
