"""Explicitly seen development wording only; isolated Java validators, never model/tools."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[1]
APP=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
TESTS=ROOT/'prototype/android/app/src/test/java/dev/focuspilot/prototype'
JAVA=Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
JUNIT=Path('/Users/sanju/.gradle/caches/modules-2/files-2.1/junit/junit/4.13.2/8ac9e16d933b6fb43bc7f576336b8f4d7eb5ba12/junit-4.13.2.jar')
HAMCREST=Path('/Users/sanju/.gradle/caches/modules-2/files-2.1/org.hamcrest/hamcrest-core/1.3/42a25dc3219429f0e5d060061f71acb49bf010a0/hamcrest-core-1.3.jar')
BASE_SHA='b4b04604b42920ed41186a5b0d20cba40302e4a41f6091055cdf92cc7dbe3c15'
NUMBER_SHA='e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d'
BASE_REF='1eb2fb55bf0322237bce0bc04942cb0d6652ddcc'
DATA_SHA={'train':'be020b76800398126d0fdabf48c277269a56da1d5980ab78e5a11bd1380191d1','development':'aaa8064ddfe5a2746c1df195050b7df9315af18883a2de1f5d93f5eae9034e6d','confirmation-v2':'1ec1fbd3633d399f1dcb4c462a18d395741cda582244c818c0763273ca8f6883'}
INTENTS=('start_focus','pause_focus','alarm','timer','open_app','explain','unknown')
TEST_NAMES=('NaturalValidatorTest','ModelCommandGateTest','ConversationalCommandGateTest','NaturalCommandGateTest','CandidateGateTest','CommandNumberWordsTest')


def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
 out=Path(args.out).resolve()
 if (TASK/'build').resolve() not in out.parents:raise ValueError('Outputs must remain in ignored task build')
 out.mkdir(parents=True,exist_ok=False)
 if sha(APP/'CommandNumberWords.java')!=NUMBER_SHA:raise ValueError('Selected number parser changed')
 baseline=out/'ModelCommandGate.java'
 raw=subprocess.check_output(['git','show',BASE_REF+':prototype/android/app/src/main/java/dev/focuspilot/prototype/ModelCommandGate.java'],cwd=ROOT,timeout=30)
 if hashlib.sha256(raw).hexdigest()!=BASE_SHA:raise ValueError('Pinned original source changed')
 baseline.write_bytes(raw)
 helper=ROOT/'prototype/command-v10-confirm/CommandGateEval.java'
 classes={arm:out/(arm+'-classes') for arm in ('baseline','candidate')}
 for arm in classes:
  classes[arm].mkdir()
  gate=baseline if arm=='baseline' else TASK/'ModelCommandGate.java'
  subprocess.run([str(JAVA/'javac'),'-d',str(classes[arm]),str(gate),str(APP/'CommandNumberWords.java'),str(helper)],check=True,timeout=30)
 test_sources=[TASK/'NaturalValidatorTest.java']+[TESTS/(name+'.java') for name in TEST_NAMES[1:]]
 subprocess.run([str(JAVA/'javac'),'-cp',str(classes['candidate'])+':'+str(JUNIT),'-d',str(classes['candidate']),*[str(p) for p in test_sources]],check=True,timeout=30)
 tests=subprocess.run([str(JAVA/'java'),'-cp',':'.join(map(str,(classes['candidate'],JUNIT,HAMCREST))),
 'org.junit.runner.JUnitCore',*['dev.focuspilot.prototype.'+name for name in TEST_NAMES]],text=True,capture_output=True,check=True,timeout=30)
 (out/'junit.txt').write_text(tests.stdout+tests.stderr)
 if 'OK (59 tests)' not in tests.stdout:raise ValueError('Expected targeted59 methods')
 rows=[];data={}
 for split,digest in DATA_SHA.items():
  path=ROOT/'prototype/qwen-balanced-data/build'/(split+'.jsonl')
  if sha(path)!=digest:raise ValueError('Known development corpus changed')
  part=[json.loads(line) for line in path.read_text().splitlines()]
  data[split]=part;rows.extend((split,row) for row in part)
 proposals=out/'known-all-routes.tsv';lookup={}
 with proposals.open('x') as stream:
  for n,(split,row) in enumerate(rows):
   for intent in INTENTS:
    ident=f'd{n:03}_{intent}';lookup[ident]=(split,row,intent)
    stream.write(ident+'\t'+intent+'\t'+row['utterance']+'\n')
 arms={}
 for arm in classes:
  output=out/(arm+'-known-output.tsv')
  with output.open('x') as stream:
   subprocess.run([str(JAVA/'java'),'-cp',str(classes[arm]),'dev.focuspilot.prototype.CommandGateEval',str(proposals)],stdout=stream,check=True,timeout=30)
  values={}
  for line in output.read_text().splitlines():
   fields=line.split('\t')
   if len(fields)!=6 or fields[0] in values:raise ValueError('Invalid gate output')
   values[fields[0]]=(fields[1],int(fields[2]),int(fields[3]),int(fields[4]),fields[5])
  if list(values)!=list(lookup):raise ValueError('Incomplete development inventory')
  arms[arm]=values
 oldaccepted=0;regressions=[];unknownchecks=0;unknownaccepted=[];wrongroute=[];remaining=[]
 counts={s:{'supported_rows':0,'baseline_correct':0,'candidate_correct':0,'gains':0,'losses':0,'unknown_rows':0} for s in data}
 for ident,(split,row,intent) in lookup.items():
  old=arms['baseline'][ident];new=arms['candidate'][ident]
  if old[0]!='UNKNOWN':
   oldaccepted+=1
   if old!=new:regressions.append(ident)
  expected=(row['expected_kind'],row['hour'],row['minute'],row['seconds'])
  if row['expected_kind']=='UNKNOWN':
   unknownchecks+=1
   if new[0]!='UNKNOWN':unknownaccepted.append(ident)
  elif intent!=row['intent'] and new[0]!='UNKNOWN':wrongroute.append(ident)
  if intent==row['intent']:
   if row['expected_kind']=='UNKNOWN':counts[split]['unknown_rows']+=1
   else:
    a=old[:4]==expected;b=new[:4]==expected;counts[split]['supported_rows']+=1
    counts[split]['baseline_correct']+=a;counts[split]['candidate_correct']+=b
    counts[split]['gains']+=b and not a;counts[split]['losses']+=a and not b
    if not b:remaining.append(row['id'])
 if regressions or unknownaccepted or wrongroute:raise ValueError('Development restriction/regression failure')
 summary={'schema':'focuspilot.natural_validation_dev.v1','verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'development_only':True,'fresh_confirmation':False,'model_calls':0,'phone_actions':0,'known_rows':len(rows),'all_intent_routes':len(lookup),
 'old_accepted_routes_preserved_kind_slots_preview':oldaccepted,'old_accepted_regressions':len(regressions),
 'required_unknown_all_route_checks':unknownchecks,'required_unknown_wrong_accepts':len(unknownaccepted),
 'supported_wrong_model_route_accepts':len(wrongroute),'by_known_split':counts,'candidate_source_sha256':sha(TASK/'ModelCommandGate.java'),
 'baseline_source_sha256':BASE_SHA,'number_parser_sha256':NUMBER_SHA,'development_data_sha256':DATA_SHA,
 'raw_artifacts_sha256':{p.name:sha(p) for p in (proposals,out/'baseline-known-output.tsv',out/'candidate-known-output.tsv',out/'junit.txt')},
 'targeted_junit_tests_passed':59,'source_and_dependencies_sha256':{str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):sha(p) for p in [TASK/'run_development.py',helper,*test_sources,JUNIT,HAMCREST]},
 'limitations':'Previously observed synthetic wording, development only. Original without guard and semicolon multi-clause restriction remain. No model, phone or general safety claim.'}
 (out/'remaining-development-ids.json').write_text(json.dumps(remaining,indent=2)+'\n')
 (out/'development-results.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
