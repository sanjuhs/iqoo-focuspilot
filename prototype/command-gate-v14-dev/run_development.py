"""Seen gate-only development; uses prior original-prompt capture, no new inference."""
import argparse,base64,hashlib,importlib.util,json,pathlib,re,subprocess,time
LAB=pathlib.Path(__file__).resolve().parent;ROOT=LAB.parents[1]
APP=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
TEST=ROOT/'prototype/android/app/src/test/java/dev/focuspilot/prototype'
JAVA=pathlib.Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
GATE=ROOT/'prototype/command-v10-confirm/run_evaluation.py'
GATE_SHA='60ad1a6d63ff063fc5e6f9946a89b4cac6a53df626ff24d1e67886425cf6ae2a'
PINS={'ModelCommandGate.java':'cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4','CommandNumberWords.java':'e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d','LocalModel.java':'2f6784c524ca9304fd714b86c04f5b1c3c5deb7e5ff562fbc34ae32c39e51e5d'}
SUITES=['ModelCommandGateTest','NaturalCommandGateTest','ConversationalCommandGateTest','CommandNumberWordsTest','ObservedNudgeGateTest','SandboxActionGateTest']
SUPPORT=['CommandNumberWords','SandboxActionGate','ObservedNudgeGate','ObservationSnapshot','SelectedAppObservation','TrainedPolicy']
JUNIT=pathlib.Path('/Users/sanju/.gradle/caches/modules-2/files-2.1/junit/junit/4.13.2/8ac9e16d933b6fb43bc7f576336b8f4d7eb5ba12/junit-4.13.2.jar')
HAMCREST=pathlib.Path('/Users/sanju/.gradle/caches/modules-2/files-2.1/org.hamcrest/hamcrest-core/1.3/42a25dc3219429f0e5d060061f71acb49bf010a0/hamcrest-core-1.3.jar')
def sha(p):
 with pathlib.Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,v):
 with p.open('x') as stream:stream.write(json.dumps(v,indent=2)+'\n')
def budget():
 size=sum(p.stat().st_size for p in LAB.rglob('*') if p.is_file())
 if size>2_000_000:raise ValueError('Development 2 MB reservation exceeded')
 return size
class Bounded:
 def __getattr__(self,name):
  fn=getattr(subprocess,name)
  if name not in ['run','check_output']:return fn
  def call(*args,**kwargs):kwargs.setdefault('timeout',30);return fn(*args,**kwargs)
  return call
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--round',required=True);args=parser.parse_args()
 if not re.fullmatch('[a-z0-9-]{1,48}',args.round):raise ValueError('Valid unique round required')
 out=LAB/'build'/args.round
 if out.exists():raise ValueError('Existing development round preserved')
 assert budget()<1_200_000 and sha(GATE)==GATE_SHA
 assert all(sha(APP/name)==digest for name,digest in PINS.items())
 old=ROOT/'prototype/command-json-runner/build';cases_path=ROOT/'prototype/command-json-confirm/build/cases.jsonl'
 rows=[json.loads(line) for line in cases_path.read_text().splitlines()]
 assert len(rows)==100 and len({r['id'] for r in rows})==100
 meta=json.loads((old/'baseline-model-metadata.json').read_text());assert meta['exit_code']==0 and not meta['timed_out'] and meta['output_sha256']==sha(old/'baseline-model-output.tsv')
 assert meta['source_commit']=='1f36dfdd635d3b94c26a307d968673587eaf598c' and meta['model_sha256']=='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
 intents={}
 for line in (old/'baseline-model-output.tsv').read_text().splitlines():
  fields=line.split('\t')
  if fields[0]=='LOAD':continue
  raw=json.loads(base64.b64decode(fields[2],validate=True));answer=json.loads(raw['text'])
  assert raw['text']=='{"intent":"'+answer['intent']+'"}' and set(answer)=={'intent'} and raw['metrics']['reached_eos'] is True and raw['metrics']['cpu_only'] is True and raw['metrics']['capture_enabled'] is False
  assert fields[0] not in intents;intents[fields[0]]=answer['intent']
 assert list(intents)==[r['id'] for r in rows]
 out.mkdir(parents=True);snap=out/'snapshot';snap.mkdir();identities={}
 originals=[LAB/'ModelCommandGate.java',LAB/'CandidateGateTest.java',pathlib.Path(__file__),GATE,GATE.parent/'CommandGateEval.java',*[APP/(name+'.java') for name in SUPPORT],*[TEST/(name+'.java') for name in SUITES]]
 for p in originals:
  target=snap/p.name;target.write_bytes(p.read_bytes());identities[p.name]=sha(target)
 # Source and test identities are retained before gate compilation/evaluation.
 save(out/'freeze.json',{'candidate_sha256':sha(LAB/'ModelCommandGate.java'),'candidate_tests_sha256':sha(LAB/'CandidateGateTest.java'),'snapshot_sha256':identities,'original_source_sha256':PINS,'cases_sha256':sha(cases_path),'old_capture_sha256':meta['output_sha256'],'old_capture_metadata_sha256':sha(old/'baseline-model-metadata.json'),'old_capture_source_commit':meta['source_commit'],'junit_sha256':sha(JUNIT),'hamcrest_sha256':sha(HAMCREST),'scope':'NOW_SEEN_DEVELOPMENT; original-prompt capture reused; no new model call','actions_executed':0,'promoted':False})
 # Run every current *GateTest and unchanged number-parser suite against candidate.
 classes=out/'tests-java';classes.mkdir();cp=str(JUNIT)+':'+str(HAMCREST)
 subprocess.run([str(JAVA/'javac'),'-cp',cp,'-d',str(classes),str(snap/'ModelCommandGate.java'),str(snap/'CandidateGateTest.java'),*[str(snap/(name+'.java')) for name in SUPPORT+SUITES]],check=True,timeout=30)
 begin=time.monotonic();test=subprocess.run([str(JAVA/'java'),'-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore',*['dev.focuspilot.prototype.'+name for name in SUITES+['CandidateGateTest']]],text=True,capture_output=True,timeout=30)
 (out/'tests-stdout.txt').write_text(test.stdout);(out/'tests-stderr.txt').write_text(test.stderr)
 save(out/'tests-terminal.json',{'exit_code':test.returncode,'wall_seconds':time.monotonic()-begin,'stdout_sha256':sha(out/'tests-stdout.txt'),'stderr_sha256':sha(out/'tests-stderr.txt'),'suite_names':SUITES+['CandidateGateTest']})
 if test.returncode:raise RuntimeError('Regression test failure preserved; no reduced suite scoring')
 match=re.search(r'OK \((\d+) tests\)',test.stdout);assert match
 spec=importlib.util.spec_from_file_location('gate_shared',GATE);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate);gate.BUILD=out;gate.subprocess=Bounded()
 versions={}
 for version in ['baseline','candidate']:
  target=out/(version+'-source');target.mkdir()
  (target/'ModelCommandGate.java').write_bytes((APP/'ModelCommandGate.java' if version=='baseline' else snap/'ModelCommandGate.java').read_bytes())
  (target/'CommandNumberWords.java').write_bytes((snap/'CommandNumberWords.java').read_bytes())
  assert sha(target/'CommandNumberWords.java')==PINS['CommandNumberWords.java']
  versions[version]={}
  for route,routes in [('generated',intents),('oracle',{r['id']:r['oracle_intent'] for r in rows})]:
   summary,details=gate.evaluate_gate(rows,routes,version,route);versions[version][route]={'summary':summary,'details':details}
 paired={route:gate.paired_gate(versions['baseline'][route]['details'],versions['candidate'][route]['details']) for route in ['generated','oracle']}
 for p,digest in identities.items():assert sha(snap/p)==digest
 assert sha(LAB/'ModelCommandGate.java')==identities['ModelCommandGate.java'] and sha(LAB/'CandidateGateTest.java')==identities['CandidateGateTest.java']
 aggregate={'scope':'Same now-seen prior100 informed synthetic cases; gate-only development, not a fresh holdout','candidate_sha256':identities['ModelCommandGate.java'],'candidate_tests_sha256':identities['CandidateGateTest.java'],'frozen_snapshot_sha256':identities,'freeze_sha256':sha(out/'freeze.json'),'old_native_capture_sha256':meta['output_sha256'],'old_native_capture_source_commit':meta['source_commit'],'corpus_sha256':sha(cases_path),'model_sha256':meta['model_sha256'],'native_sha256':meta['native_sha256'],'tests':{'count':int(match.group(1)),'exit_code':test.returncode,'suite_names':SUITES+['CandidateGateTest'],'terminal_record_sha256':sha(out/'tests-terminal.json')},'gates':{v:{route:values['summary'] for route,values in routes.items()} for v,routes in versions.items()},'paired':paired,'per_intent':{},'new_inference_calls':0,'training_performed':False,'actions_executed':0,'candidate_promoted':False,'directory_bytes':budget()}
 for route in ['generated','oracle']:
  aggregate['per_intent'][route]={}
  for intent in ['start_focus','pause_focus','alarm','timer','open_app','explain','unknown']:
   ids={r['id'] for r in rows if r['semantic_intent']==intent}
   aggregate['per_intent'][route][intent]={'rows':len(ids),**{v:sum(d['correct'] for d in versions[v][route]['details'] if d['id'] in ids) for v in versions}}
 save(out/'results.json',aggregate);print(json.dumps({'tests':aggregate['tests'],'gates':{v:{route:{k:s['summary'][k] for k in ['supported_correct','supported_false_abstentions','wrong_accepted','unsupported_false_accepts']} for route,s in routes.items()} for v,routes in versions.items()},'paired':paired},indent=2));budget()
if __name__=='__main__':main()
