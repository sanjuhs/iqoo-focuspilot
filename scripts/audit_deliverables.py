#!/usr/bin/env python3
"""Read-only, artifact-based completion audit. No phone, keys, installs or uploads.

Scopes 'verified' to byte/metadata checks, never the whole product. JSON evidence
records are attributed reports, not independent repetitions of hardware behavior.
Optional --live-github uses gh's existing login to read public repo/releases only.
Outputs JSON to stdout; redirect into ignored artifacts/ if desired.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET

MODEL_SHA='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
MODEL_BYTES=563036064
LICENSES={'FocusPilot-MIT.txt':'LICENSE','Qwen3.5-Apache-2.0.txt':'prototype/qwen/LICENSE.Qwen3.5','llama.cpp-MIT.txt':'prototype/native/LICENSE.llama.cpp','KleidiAI-Apache-2.0.txt':'prototype/native/LICENSE.KleidiAI.Apache-2.0.txt','KleidiAI-BSD-3-Clause.txt':'prototype/native/LICENSE.KleidiAI.BSD-3-Clause.txt','KleidiAI-notices.txt':'prototype/native/NOTICE.KleidiAI.txt'}
MANUAL_REQUIREMENTS={
 'offline_disconnected':'Actual airplane-mode/USB-disconnected Qwen execution, with settings state and successful result tied to APK/model hashes',
 'voice_and_clock':'User-permitted actual microphone transcript, local installed ASR/TTS, denied/revoked paths, reviewed alarm and Clock postcondition',
 'floating_companion':'User-granted actual overlay Show/deny/cancel, bounded drag, external touch, screen/lock/permission teardown, notification Hide/Pause, rotation/keyboard and app-stop evidence tied to APK/device',
 'live_focus_monitor':'User-enabled Usage Access/notifications, measured real selected-app boundaries, background notification Stop/revocation/recovery, cooldown/override',
 'live_personalization':'Consented real held-out workflows, baseline comparison, coverage/false nudges and live-policy mapping; toy retrieval is insufficient',
 'iqoo_hardware':'Actual organizer-eligible iQOO device identity, installed APK/model hashes and repeatable local assistant workflow',
 'npu_execution':'Correlated executed HTP operator trace, actual device/backend placement, CPU fallback coverage, outputs/latencies; SDK labels are insufficient',
 'office_kit':'Actual official Office Kit account/device pairing and synthetic file/task handoff outcome with hashes; ADB is insufficient',
 'event_code_eligibility':'Event-window original source history or explicit organizer reuse authorization; pre-event research cannot certify eligibility',
 'application_and_submission':'Authenticated official cutoff, admission/track/team confirmation and final accepted submission receipt',
 'broad_phone_control_iot':'Requested broader approved cross-app/IoT execution with explicit actions/postconditions on real hardware, if retained in final scope',
 'llm_finetuning':'Actual language-model fine-tuning plus immutable held-out regression/export evidence if claimed; tiny synthetic head is a different training result',
}

def digest(stream):
 h=hashlib.sha256()
 while data:=stream.read(1024*1024): h.update(data)
 return h.hexdigest()
def sha(path):
 with path.open('rb') as stream:return digest(stream)
def public_evidence_path(root,path):
 p=Path(path);p=p if p.is_absolute() else root/p
 resolved=p.resolve();base=root.resolve()
 return resolved.is_relative_to(base) and resolved.relative_to(base).parts and resolved.relative_to(base).parts[0] in ('artifacts','docs','prototype','scripts') and all(not part.startswith('.') for part in resolved.relative_to(base).parts)
def read_json(path):
 return json.loads(path.read_text())
def command(args):
 return subprocess.run(list(map(str,args)),check=True,text=True,capture_output=True).stdout

def artifact_identity(path, declared):
 if not path.is_file():return {'status':'missing','path':str(path),'reason':'local artifact unavailable'}
 observed={'bytes':path.stat().st_size,'sha256':sha(path)}
 expected_size=declared.get('bytes',declared.get('size'))
 same=observed['bytes']==expected_size and observed['sha256']==declared.get('sha256')
 return {'status':'verified' if same else 'incomplete','scope':'local byte identity against declared manifest','observed':observed,'declared':{'bytes':expected_size,'sha256':declared.get('sha256')}}

def release_parity(local, assets, name):
 asset=next((a for a in assets if a.get('name')==name),None)
 if asset is None:return {'status':'missing','name':name,'reason':'public release asset absent'}
 d=asset.get('digest')
 if not d:return {'status':'weak_evidence','name':name,'reason':'server does not publish digest; no remote binary downloaded'}
 same=d=='sha256:'+local['sha256'] and asset.get('size')==local['bytes'] and asset.get('state','uploaded')=='uploaded'
 return {'status':'verified' if same else 'incomplete','name':name,'scope':'GitHub server metadata/local hash parity, not remote re-download or device run','server_digest':d,'url':asset.get('browser_download_url')}

def inspect_apk(path, declared, root, aapt=None, signer=None):
 identity=artifact_identity(path,declared); out={'identity':identity,'runtime_verified':False}
 if identity['status']!='verified':return out
 try:
  with ZipFile(path) as apk:
   names=apk.namelist();out['android_payload_present']=all(n in names for n in ('AndroidManifest.xml','classes.dex'))
   native='lib/arm64-v8a/libfocuspilot_local.so'
   out['native_sha256']=digest(apk.open(native)) if native in names else None
   out['native_hash_parity']=out['native_sha256']==declared.get('native_sha256')
   out['licenses']={}
   for name,source in LICENSES.items():
    asset='assets/licenses/'+name
    out['licenses'][name]=asset in names and (root/source).is_file() and digest(apk.open(asset))==sha(root/source)
   weights=[n for n in names if n.endswith('.gguf')]
   out['model_files']=weights; expected_bundle=declared.get('bundled_model',declared.get('containsModel'))
   out['bundle_presence_parity']=bool(weights)==bool(expected_bundle)
   if expected_bundle and len(weights)==1:
    item=apk.getinfo(weights[0]);out['model']={'bytes':item.file_size,'sha256':digest(apk.open(item)),'zip_compression':item.compress_type}
    out['model_hash_parity']=item.file_size==MODEL_BYTES and out['model']['sha256']==MODEL_SHA
   elif expected_bundle:out['model_hash_parity']=False
  if aapt:
   permissions=command([aapt,'dump','permissions',path]);out['permissions']=re.findall(r"uses-permission: name='([^']+)'",permissions)
   out['package_identity']='package: dev.focuspilot.prototype' in permissions;out['internet_absent']=out['package_identity'] and 'android.permission.INTERNET' not in out['permissions'];out['permission_scope']='parsed from packaged APK, not user permission grants'
  else:out['permission_proof']='weak_evidence: aapt2 unavailable; manifest JSON flag not trusted'
  if signer:
   command([signer,'verify',path]);out['signature']='verified cryptographic APK signature; no trusted publisher identity inference'
  else:out['signature']='weak_evidence: apksigner unavailable'
 except (BadZipFile,KeyError,subprocess.CalledProcessError) as e:out['inspection_error']=type(e).__name__
 out['status']='verified' if out.get('android_payload_present') and out.get('native_hash_parity') and all(out.get('licenses',{}).values()) and out.get('bundle_presence_parity') and (not declared.get('bundled_model',declared.get('containsModel')) or out.get('model_hash_parity')) and out.get('internet_absent') and out.get('signature','').startswith('verified') else 'incomplete' if out.get('inspection_error') or out.get('android_payload_present') is False or out.get('native_hash_parity') is False or not all(out.get('licenses',{}).values()) or out.get('bundle_presence_parity') is False or out.get('model_hash_parity') is False or out.get('internet_absent') is False else 'weak_evidence'
 return out

def reports(test_dir, lint_file):
 files=sorted(test_dir.glob('TEST-*.xml'));out={'scope':'host XML reports only; no APK/source digest binding','reports':[],'totals':{'tests':0,'failures':0,'errors':0,'skipped':0}}
 for f in files:
  suite=ET.parse(f).getroot(); counts={k:int(suite.attrib.get(k,0)) for k in out['totals']}
  declared_cases=counts['tests']; actual_cases=len(suite.findall('testcase'))
  child_counts={'failures':len(suite.findall('testcase/failure')),'errors':len(suite.findall('testcase/error')),'skipped':len(suite.findall('testcase/skipped'))}
  out['reports'].append({'file':f.name,'sha256':sha(f),'observed_mtime_utc':datetime.fromtimestamp(f.stat().st_mtime,timezone.utc).isoformat(),'declared_suite_timestamp':suite.attrib.get('timestamp'),'counts':counts,'case_count_parity':declared_cases==actual_cases,'failure_child_parity':all(counts[k]==v for k,v in child_counts.items())})
  for k,v in counts.items():out['totals'][k]+=v
 out['status']='verified' if files and out['totals']['tests']>0 and not(out['totals']['failures']+out['totals']['errors']) and all(x['case_count_parity'] and x['failure_child_parity'] for x in out['reports']) else 'missing' if not files else 'incomplete'
 if lint_file.is_file():
  issues=ET.parse(lint_file).getroot().findall('issue');out['lint']={'sha256':sha(lint_file),'errors':sum(i.attrib.get('severity') in ('Error','Fatal') for i in issues),'warnings':sum(i.attrib.get('severity')=='Warning' for i in issues),'scope':'host lint report only'}
 return out

def synthetic_arithmetic(policy,fewshot,causal):
 hold=policy['holdout']; correct=hold['tp']+hold['tn'];count=sum(hold[k] for k in ('tp','tn','fp','fn'))
 accuracy_ok=all(type(hold[k]) is int and hold[k]>=0 for k in ('tp','tn','fp','fn')) and count==hold['count'] and math.isclose(correct/count,hold['accuracy'],abs_tol=1e-12)
 summaries={}; valid=True
 for name,s in fewshot['summary'].items():
  okay=0<=s['fewshot_correct']<=s['answered']<=s['total'] and 0<=s['baseline_correct']<=s['total'] and s['answered']+s['abstained']==s['total'] and math.isclose(s['answered']/s['total'],s['coverage'],abs_tol=1e-12) and math.isclose(s['fewshot_correct']/s['answered'],s['selective_accuracy'],abs_tol=1e-12)
  valid &= okay;summaries[name]={'coverage':s['coverage'],'answered_accuracy':s['selective_accuracy'],'fewshot_correct':s['fewshot_correct'],'baseline_correct':s['baseline_correct'],'overall_correct_delta':s['fewshot_correct']-s['baseline_correct'],'arithmetic_parity':okay}
 same=causal['holdout']['opposite_patch']['intent_changes'];random=causal['holdout']['random_patch']['intent_changes']
 return {'status':'verified' if accuracy_ok and valid else 'incomplete','scope':'recorded metric arithmetic, not rerun training or real-human accuracy','toy_policy':{'correct':correct,'count':count,'accuracy':hold['accuracy'],'false_nudges':hold['fp'],'misses':hold['fn'],'arithmetic_parity':accuracy_ok},'fewshot':summaries,'causal':{'native_calls':causal['native_calls'],'restore_full_logit_parity_reported':causal['noop_restore_full_logits_parity'],'selected_opposite_intent_changes':same,'random_intent_changes':random,'semantic_steering_advantage_established':False,'phone_replication':False}}

def captions(path, duration):
 if not path.is_file():return {'status':'missing'}
 def seconds(t):
  h,m,s,ms=map(int,re.split('[:,]',t));return 3600*h+60*m+s+ms/1000
 entries=path.read_text().strip().split('\n\n');times=[]
 for block in entries:
  lines=block.splitlines();a,b=lines[1].split(' --> ');times.append((seconds(a),seconds(b)))
 valid=all(0<=a<b<=duration for a,b in times) and all(times[i][1]<=times[i+1][0] for i in range(len(times)-1))
 return {'status':'verified' if valid else 'incomplete','scope':'SRT timing bounds/order only, not transcription accuracy','segments':len(entries),'last_end_seconds':times[-1][1]}

def video_audit(root,metadata,manifest):
 path=root/metadata['video']['file'];out={'identity':artifact_identity(path,metadata['video']),'live_demo':False}
 if out['identity']['status']!='verified':return out
 if shutil.which('ffprobe'):
  probe=json.loads(command(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_name,codec_type,width,height,duration','-of','json',path]));duration=float(probe['format']['duration'])
  video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next((s for s in probe['streams'] if s['codec_type']=='audio'),None)
  out['measured']={'seconds':duration,'resolution':[video['width'],video['height']],'codec':video['codec_name'],'audio_present':audio is not None};out['pitch_duration_pass']=180<=duration<=300;out['metadata_duration_parity']=abs(duration-metadata['video']['seconds'])<.05
  out['captions']=captions(root/'artifacts/pitch-research.srt',duration)
 else:out['metadata_proof']='weak_evidence: ffprobe unavailable'
 if shutil.which('ffmpeg'):
  command(['ffmpeg','-v','error','-xerror','-i',path,'-f','null','-']);out['full_decode']='verified stream decode with ffmpeg; not human visual/audio review'
 bindings={'source_sha256':root/'docs/research-pitch-script.md','renderer_sha256':root/'scripts/render_pitch_video.py','captions_sha256':root/'artifacts/pitch-research.srt','video_sha256':path}
 out['source_hash_bindings']={key:p.is_file() and manifest.get(key)==sha(p) for key,p in bindings.items()}
 asset=manifest.get('avatar_source'); still=manifest.get('phone_still'); observed={}
 for name,ref in [('avatar',asset),('phone_still',still)]:
  p=root/ref if ref else None
  observed[name]=sha(p) if p and public_evidence_path(root,p) and p.is_file() else None
 out['asset_provenance']={'avatar_recorded':asset,'current_asset_sha256':observed,'historical_avatar_hash_recorded':manifest.get('avatar_sha256'),'avatar_authorship':'original vector declared in docs/companion-design.md; not independently proved by hashing','phone_still_kind':'historical research UI screenshot, not live footage','phone_crop_recorded':manifest.get('phone_crop_pixels'),'phone_capture_hash_in_historical_manifest':manifest.get('phone_still_sha256'),'capture_consent_and_visual_privacy_review':'human attestation required; file presence/crop does not self-certify privacy','current_hashes_bind_historical_render_inputs':False}
 return out

def phone_record(record, expected, source_tag=None):
 fields={'apk_sha256':expected['sha256'],'native_sha256':expected['native_sha256'],'model_sha256':MODEL_SHA}
 matches={key:record.get(key)==value for key,value in fields.items()}
 if source_tag:
  ref=record.get('source_commit','');matches['source_attribution_matches_release_tag']=isinstance(ref,str) and 7<=len(ref)<=40 and source_tag.startswith(ref)
 return {'status':'verified' if all(matches.values()) else 'weak_evidence','scope':'reported phone observation identity binding, not independent hardware repetition','bindings':matches,'device':record.get('device'),'backend_reported':record.get('backend'),'source_commit':record.get('source_commit'),'actions_reported':record.get('results'),'physical_offline_proof':False}

def research_bindings(root):
 """Check experiment provenance and counterexamples without replaying inference."""
 policy=read_json(root/'prototype/policy/synthetic-model.json');export=read_json(root/'prototype/policy/java-export-results.json');few=read_json(root/'prototype/personalization/evaluation.json');causal=read_json(root/'prototype/interpretability/summary.json');protocol=read_json(root/'prototype/interpretability/protocol.json')
 java=root/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
 declared={root/'prototype/policy/policy.py':policy['implementation_sha256'],java/'TrainedPolicy.java':export['generated_java_sha256'],root/'prototype/interpretability/probe.cpp':causal['probe_source_sha256'],root/'prototype/interpretability/run.py':causal['runner_source_sha256'],root/'prototype/policy/synthetic-model.json':few['baseline_checkpoint_sha256']}
 for name,h in few['source_sha256'].items():declared[(java if name=='FewShotPolicy.java' else root/'prototype/personalization')/name]=h
 matches={str(p.relative_to(root)):p.is_file() and sha(p)==h for p,h in declared.items()}
 param_hash=hashlib.sha256(json.dumps(policy['parameters'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 parameter_parity=param_hash==policy['parameters_sha256']==export['parameters_sha256']
 model_parity=causal['model_sha256']==protocol['gguf_sha256']==MODEL_SHA
 trials=read_json(root/'prototype/interpretability/intervention-cases.json');controls=[t for t in trials if t['mode'] in ('noop','restore')]
 checks=[t['changed']['full_logits_byte_equal_to_baseline'] and t['changed']['full_logits_fnv64']==t['baseline']['full_logits_fnv64'] and t['changed']['candidate_logits']==t['baseline']['candidate_logits'] and t['changed']['max_full_vocab_logit_delta']==0 for t in controls]
 changes={mode:sum(t['changed']['intent']!=t['baseline']['intent'] for t in trials if t['split']=='holdout' and t['mode']==mode) for mode in ('opposite_patch','random_patch')}
 control_parity=len(controls)==16 and all(checks)
 return {'status':'verified' if all(matches.values()) and parameter_parity and model_parity and control_parity else 'incomplete','scope':'current source/checkpoint identity and recorded trial consistency; no new model training, raw-logit replay or hardware execution','source_hashes':matches,'parameter_hash_parity':parameter_parity,'model_identity_parity':model_parity,'recorded_controls':{'count':len(controls),'parity':control_parity,'raw_full_logits_recomputed':False},'recorded_holdout_intent_changes':changes,'npu_proved':False,'human_productivity_accuracy_proved':False}

def manual_proofs(root, proofs):
 out={}
 for key,need in MANUAL_REQUIREMENTS.items():
  record=proofs.get(key,{}); refs=record.get('artifacts',[]); checks=[]
  for ref in refs:
   p=Path(ref.get('path','')); allowed=not p.is_absolute() and '..' not in p.parts and p.parts and p.parts[0] in ('artifacts','docs','prototype') and all(not part.startswith('.') for part in p.parts)
   okay=allowed and public_evidence_path(root,root/p) and (root/p).is_file() and sha(root/p)==ref.get('sha256')
   checks.append(okay)
  out[key]={'status':'weak_evidence' if refs and all(checks) else 'incomplete','required_proof':need,'proof_bundle_hashes_match':bool(refs and all(checks)),'human_review_required':True,'claim_verified':False}
 return out

def command_confirmation_binding(root):
 """Bind the selected app sources to recorded confirmation, without replaying it."""
 lab=root/'prototype/command-v10-confirm'; frozen=read_json(lab/'freeze-manifest.json')
 result=read_json(lab/'results.json'); metadata=read_json(lab/'experiment-metadata.json')
 java=root/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
 source_matches={name:(java/name).is_file() and sha(java/name)==expected for name,expected in frozen['selected_source_sha256'].items()}
 evidence_matches={
  'results_digest':sha(lab/'results.json')==metadata['results_sha256'],
  'generator_digest':sha(lab/'generate_data.py')==frozen['generator_sha256'],
  'protocol_digest':sha(lab/'protocol.json')==frozen['protocol_sha256'],
  'manifest_matches_result':frozen==result['frozen_manifest'],
  'selected_before_authoring':frozen['selection_locked_before_authoring'] is True,
  'model_identity':result['model']['metadata']['model_sha256']==MODEL_SHA,
  'no_phone_actions':result['actions_executed']==0,
 }
 scores=result['gates']['generated']; selected=scores['selected']; baseline=scores['baseline']
 return {'status':'verified' if all(source_matches.values()) and all(evidence_matches.values()) else 'incomplete',
  'scope':'app-source and recorded synthetic evidence binding; no inference replay, independent sampling or phone outcome proof',
  'source_matches':source_matches,'evidence_matches':evidence_matches,
  'supported_baseline':baseline['supported_correct'],'supported_selected':selected['supported_correct'],
  'supported_total':selected['supported_rows'],'false_abstentions':selected['supported_false_abstentions'],
  'wrong_accepted_observed':selected['wrong_accepted'],'raw_model_correct':result['model']['semantic_correct'],
  'raw_model_total':result['model']['rows'],'unknown_nonunknown_proposals':result['model']['unknown_nonunknown_proposals'],
  'paired':result['paired']['generated'],'physical_verified':False}

class Audit:
 def __init__(self,root):self.root=root;self.result={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'goal_complete':False,'label':'PRE-EVENT RESEARCH; byte/metadata audit cannot certify whole assistant or submission','checks':{},'errors':{}}
 def check(self,key,fn):
  try:self.result['checks'][key]=fn()
  except (OSError,ValueError,KeyError,ET.ParseError,subprocess.CalledProcessError) as e:self.result['errors'][key]=type(e).__name__;self.result['checks'][key]={'status':'missing' if isinstance(e,FileNotFoundError) else 'incomplete','reason':'required evidence unavailable or invalid; see errors'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--live-github',action='store_true');p.add_argument('--manual-proof',type=Path);a=p.parse_args();root=a.root.resolve();audit=Audit(root)
 audit.check('artifact_manifest',lambda:read_json(root/'docs/companion-artifacts.json'));audit.check('native_manifest',lambda:read_json(root/'prototype/native/optimized-build-manifest.json'))
 if audit.result['errors']:
  print(json.dumps(audit.result,indent=2));return
 latest=audit.result['checks'].pop('artifact_manifest');native=audit.result['checks'].pop('native_manifest');repo='sanjuhs/iqoo-focuspilot'
 sdk=Path.home()/'Library/Android/sdk/build-tools/36.0.0';aapt=sdk/'aapt2' if (sdk/'aapt2').is_file() else None;signer=sdk/'apksigner' if (sdk/'apksigner').is_file() else None
 for item in latest['artifacts']:
  audit.check(item['name'],lambda item=item:inspect_apk(root/'artifacts'/item['name'],item,root,aapt,signer))
 audit.check('observed_learning_manifest',lambda:read_json(root/'docs/observed-learning-artifacts.json'))
 v05=audit.result['checks']['observed_learning_manifest']
 if 'artifacts' in v05:
  for item in v05['artifacts']:
   audit.check(item['name'],lambda item=item:inspect_apk(root/'artifacts'/item['name'],item,root,aapt,signer))
  v05_bundle=next(item for item in v05['artifacts'] if item['bundled_model'])
  audit.check('v05_phone_report_binding',lambda:phone_record(read_json(root/'docs/observed-learning-phone.json'),v05_bundle,'9dade07f1c5a3d627e56a06704826d9b83621599'))
 audit.check('command_readiness_manifest',lambda:read_json(root/'docs/command-readiness-artifacts.json'))
 v06=audit.result['checks']['command_readiness_manifest']
 if 'artifacts' in v06:
  for item in v06['artifacts']:
   audit.check(item['name'],lambda item=item:inspect_apk(root/'artifacts'/item['name'],item,root,aapt,signer))
  v06_light=next(item for item in v06['artifacts'] if not item['bundled_model'])
  audit.check('v06_phone_report_binding',lambda:phone_record(read_json(root/'docs/command-readiness-phone.json'),v06_light,v06['source_commit']))
 audit.check('timed_focus_manifest',lambda:read_json(root/'docs/timed-focus-artifacts.json'))
 v07=audit.result['checks']['timed_focus_manifest']
 if 'artifacts' in v07:
  for item in v07['artifacts']:
   audit.check(item['name'],lambda item=item:inspect_apk(root/'artifacts'/item['name'],item,root,aapt,signer))
  v07_light=next(item for item in v07['artifacts'] if not item['bundled_model'])
  if (root/'docs/timed-focus-phone.json').is_file():
   audit.check('v07_phone_report_binding',lambda:phone_record(read_json(root/'docs/timed-focus-phone.json'),v07_light,v07['source_commit']))
  else:audit.result['checks']['v07_phone_report_binding']={'status':'incomplete','reason':'Physical countdown test awaits unlocked own-app foreground; installation and JVM tests do not establish this.'}
 audit.check('natural_commands_manifest',lambda:read_json(root/'docs/natural-commands-artifacts.json'))
 v08=audit.result['checks']['natural_commands_manifest']
 if 'artifacts' in v08:
  for item in v08['artifacts']:
   audit.check(item['name'],lambda item=item:inspect_apk(root/'artifacts'/item['name'],item,root,aapt,signer))
  v08_light=next(item for item in v08['artifacts'] if not item['bundled_model'])
  if (root/'docs/natural-commands-phone.json').is_file():
   audit.check('v08_phone_report_binding',lambda:phone_record(read_json(root/'docs/natural-commands-phone.json'),v08_light,v08['source_commit']))
  else:audit.result['checks']['v08_phone_report_binding']={'status':'incomplete','reason':'Natural-command/countdown physical proof awaits unlocked own-app foreground; host results and installation are insufficient.'}
 audit.check('floating_companion_manifest',lambda:read_json(root/'docs/floating-companion-artifacts.json'))
 v09=audit.result['checks']['floating_companion_manifest']
 if 'artifacts' in v09:
  for item in v09['artifacts']:
   audit.check(item['name'],lambda item=item:inspect_apk(root/'artifacts'/item['name'],item,root,aapt,signer))
  audit.result['checks']['v09_floating_phone_proof']={'status':'incomplete','reason':'Installation, source review and geometry tests do not establish user-granted floating UI, drag/touch, screen/lock/revocation, notification controls or OEM behavior.'}
 audit.check('conversational_commands_manifest',lambda:read_json(root/'docs/conversational-commands-artifacts.json'))
 v10=audit.result['checks']['conversational_commands_manifest']
 if 'artifacts' in v10:
  for item in v10['artifacts']:
   audit.check(item['name'],lambda item=item:inspect_apk(root/'artifacts'/item['name'],item,root,aapt,signer))
  audit.check('v10_confirmation_binding',lambda:command_confirmation_binding(root))
  audit.result['checks']['v10_phone_proof']={'status':'incomplete','reason':'Source-bound synthetic gate confirmation and APK installation do not establish current phone command outcomes, ASR, floating behavior or disconnected execution.'}
 audit.check('native_source_bindings',lambda:{'scope':'current source identity against optimized build manifest; not binary compilation replay','status':'verified' if all((root/'prototype/native'/name).is_file() and sha(root/'prototype/native'/name)==h for name,h in native['sourceSHA256'].items()) else 'incomplete','source_files':{name:(root/'prototype/native'/name).is_file() and sha(root/'prototype/native'/name)==h for name,h in native['sourceSHA256'].items()},'npu':native['npuInference'],'gpu':native['gpuBackends']})
 audit.check('host_reports',lambda:reports(root/'prototype/android/app/build/test-results/testDebugUnitTest',root/'prototype/android/app/build/reports/lint-results-debug.xml'))
 audit.check('pitch',lambda:video_audit(root,read_json(root/'docs/pitch-evidence.json'),read_json(root/'artifacts/pitch-render-manifest.json')))
 audit.check('synthetic_research',lambda:synthetic_arithmetic(read_json(root/'prototype/policy/synthetic-model-results.json'),read_json(root/'prototype/personalization/evaluation.json'),read_json(root/'prototype/interpretability/summary.json')))
 audit.check('research_source_and_control_bindings',lambda:research_bindings(root))
 audit.check('historical_phone_counterexamples',lambda:{'scope':'recorded five-case historical CPU smoke, not current binary benchmark','record_sha256':sha(root/'prototype/native/phone-smoke-optimized.json'),'native_sha256':read_json(root/'prototype/native/phone-smoke-optimized.json')['native_library_sha256'],'current_native_sha256':native['sha256'],'same_binary':read_json(root/'prototype/native/phone-smoke-optimized.json')['native_library_sha256']==native['sha256'],'model_failures_rejected':[{'request':r['command'],'wrong_model_intent':r['intent'],'gate':r['gate'],'action_executed':r['action_executed']} for r in read_json(root/'prototype/native/phone-smoke-optimized.json')['results'] if r['gate']=='ABSTAIN']})
 bundled=next(x for x in latest['artifacts'] if x['bundled_model'])
 audit.check('latest_phone_report_binding',lambda:phone_record(read_json(root/'docs/companion-phone-bound-v04.json'),bundled,'3bcf8a8af6d9e0ad380470afd96f2c6619e93311'))
 audit.check('historical_v04_unbound_phone_record',lambda:phone_record(read_json(root/'docs/companion-integration.json'),bundled))
 audit.check('manual_requirements',lambda:manual_proofs(root,read_json(a.manual_proof) if a.manual_proof else {}))
 if a.live_github:
  def github():
   info=json.loads(command(['gh','api',f'repos/{repo}'])); releases=json.loads(command(['gh','api',f'repos/{repo}/releases'])); findings=[]
   for release in releases:
    for asset in release['assets']:
     name=asset['name']; local=root/('docs' if name.endswith('.json') else 'artifacts')/name
     if local.is_file():findings.append({'tag':release['tag_name'],**release_parity({'bytes':local.stat().st_size,'sha256':sha(local)},release['assets'],name)})
   required={}
   bound=['companion-phone-bound-v04.json'] if (root/'docs/companion-phone-bound-v04.json').is_file() else []
   v07_names=['focuspilot-research-v07-light.apk','focuspilot-research-v07-bundled.apk','timed-focus-artifacts.json']
   if (root/'docs/timed-focus-phone.json').is_file():v07_names.append('timed-focus-phone.json')
   v08_names=['focuspilot-research-v08-light.apk','focuspilot-research-v08-bundled.apk','natural-commands-artifacts.json']
   if (root/'docs/natural-commands-phone.json').is_file():v08_names.append('natural-commands-phone.json')
   for tag,names in {'research-v0.10':['focuspilot-research-v010-light.apk','focuspilot-research-v010-bundled.apk','conversational-commands-artifacts.json'],'research-v0.9':['focuspilot-research-v09-light.apk','focuspilot-research-v09-bundled.apk','floating-companion-artifacts.json'],'research-v0.8':v08_names,'research-v0.7':v07_names,'research-v0.6':['focuspilot-research-v06-light.apk','focuspilot-research-v06-bundled.apk','command-readiness-artifacts.json','command-readiness-phone.json'],'research-v0.5':['focuspilot-research-v05-light.apk','focuspilot-research-v05-bundled.apk','observed-learning-artifacts.json','observed-learning-phone.json'],'research-v0.4':[x['name'] for x in latest['artifacts']]+['companion-artifacts.json','companion-integration.json']+bound,'research-v0.3':['focuspilot-research-light.apk','focuspilot-research-bundled.apk','pitch-research.mp4','pitch-research.srt','pitch-evidence.json','research-artifacts.json']}.items():
    release=next((r for r in releases if r['tag_name']==tag),None);assets=release['assets'] if release else []
    required[tag]={name:any(asset.get('name')==name for asset in assets) for name in names}
   main=json.loads(command(['gh','api',f'repos/{repo}/git/ref/heads/main']))['object']['sha'];head=command(['git','-C',root,'rev-parse','HEAD']).strip();tag=json.loads(command(['gh','api',f'repos/{repo}/git/ref/tags/research-v0.4']))['object']
   return {'public':not info['private'],'license':info['license']['spdx_id'],'url':info['html_url'],'remote_main':main,'local_head':head,'head_parity':main==head,'v04_tag':tag,'assets':findings,'required_asset_presence':required,'scope':'server metadata and committed source refs; uncommitted work is not backed up by head parity'}
  audit.check('github',github)
 else:audit.result['checks']['github']={'status':'incomplete','reason':'not queried; use --live-github for read-only public metadata'}
 print(json.dumps(audit.result,indent=2))
if __name__=='__main__':main()
