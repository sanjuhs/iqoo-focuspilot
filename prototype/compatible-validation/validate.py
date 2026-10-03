"""Freeze/replay exact historical development proposals; no model or phone calls."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BUILD = TASK/'build'
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
REG = ROOT/'prototype/unit-regression'
UNIT = ROOT/'prototype/unit-eval'
CAPTURE = ROOT/'prototype/unit-native/build/dev-capture'
GOLD = ROOT/'prototype/structured-data/build/development.jsonl'
KNOWN_PINS = {
 'readiness.json':'a9cd71d7fa41a75117d3cda4a8fbc4844235b8268f406a8fbeec134dd0ab4165',
 'build/prepared/unit-input.tsv':'c6cbcb62e0605abdf1b1c9ecda0c82056f2cae35bfb873a5247462ec286f4b94',
 'build/prepared/route-gold.json':'81fc546cedc75bb642958c9b174804d85c6d2dfbc13a345fe71419c82051dcc6',
}
UNIT_AUDIT_SHA = '5c6d2d49bc691d1effc37b04a81bbcc7c191ab08301395ecbd40e8fbfb0df47a'
GOLD_SHA = 'b8ca8a201971dd7c25267866cf1e80f3c116d9ab48060337d09f5f5acb95ddb5'
NAMES = ('validate.py','CompatibleRegression.java','test_validation.py','README.md','protocol.json','.gitignore')
DEPENDENCIES = (
 ROOT/'prototype/compatible-unit/CompatibleUnitCommand.java',
 ROOT/'prototype/unit-command/UnitCommand.java',
 ROOT/'prototype/structured-command/StructuredCommand.java',
 ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype/CommandNumberWords.java',
 ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype/ModelCommandGate.java',
)


def sha(path):
 with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def strict(text):
 def unique(pairs):
  out = {}
  for key,value in pairs:
   if key in out: raise ValueError('Duplicate JSON key')
   out[key] = value
  return out
 return json.loads(text,object_pairs_hook=unique,
  parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def write_new(path,value):
 with Path(path).open('x') as f: json.dump(value,f,indent=2);f.write('\n')


def private(path):
 path = Path(path).resolve()
 if BUILD.resolve() not in path.parents: raise ValueError('Ignored compatible-validation/build output required')
 return path


def canonical_tuple(value):
 if type(value) is not dict or type(value.get('intent')) is not str: raise ValueError('Canonical object required')
 intent = value['intent']; keys = {'intent'}; h=m=s=0
 kinds = {'start_focus':'START_FOCUS','pause_focus':'PAUSE_FOCUS','alarm':'ALARM',
          'timer':'TIMER','explain':'EXPLAIN','unknown':'UNKNOWN'}
 if intent in ('start_focus','timer'):
  keys.add('duration_seconds');s=value.get('duration_seconds')
  if type(s) is not int or not (0 if intent=='start_focus' else 1)<=s<=7200: raise ValueError('Bounded integer duration required')
 elif intent=='alarm':
  keys.update(('hour','minute'));h=value.get('hour');m=value.get('minute')
  if type(h) is not int or not 0<=h<=23 or type(m) is not int or not 0<=m<=59: raise ValueError('Bounded integer time required')
 elif intent=='open_app':
  keys.add('app');app=value.get('app');apps={'settings':'OPEN_SETTINGS','calculator':'OPEN_CALCULATOR','clock':'OPEN_CLOCK'}
  if type(app) is not str or app not in apps: raise ValueError('Approved app required')
  kind=apps[app]
 elif intent not in kinds: raise ValueError('Known intent required')
 if set(value)!=keys: raise ValueError('Exact canonical fields required')
 return [kind if intent=='open_app' else kinds[intent],h,m,s]


def pinned_unit_records():
 audit_path = UNIT/'independent-audit.json'
 if sha(audit_path)!=UNIT_AUDIT_SHA: raise ValueError('Original unit audit changed')
 audit = strict(audit_path.read_text()); files={str(audit_path):UNIT_AUDIT_SHA}
 selected=[GOLD,UNIT/'build/dev-scoring/result.json',UNIT/'build/dev-scoring/units-generated-details.json',
           *(CAPTURE/name for name in ('raw.jsonl','process.json','initial.json','started.json','stderr.log','capture-summary.json'))]
 for path in selected:
  digest=audit['files_sha256'][str(path.relative_to(ROOT))]
  if sha(path)!=digest: raise ValueError('Original unit evidence changed')
  files[str(path)]=digest
 if sha(GOLD)!=GOLD_SHA: raise ValueError('Original development gold changed')
 gold=[strict(line) for line in GOLD.read_text().splitlines()]
 capture=[strict(line) for line in (CAPTURE/'raw.jsonl').read_text().splitlines()]
 load=capture.pop(0); process=strict((CAPTURE/'process.json').read_text())
 if load['adapter'] is not False or process['exit_code']!=0 or process['timed_out'] or process['model_sha256']!=audit['verified']['model_sha256']:
  raise ValueError('Original completed base-only capture required')
 if len(gold)!=24 or len(capture)!=24 or [r['id'] for r in gold]!=[r['id'] for r in capture]: raise ValueError('Original complete24 inventory required')
 for row in capture:
  if row['metrics']['reached_eos'] is not True: raise ValueError('Original actual EOS required')
 prior=strict((UNIT/'build/dev-scoring/units-generated-details.json').read_text())
 if [r['id'] for r in prior]!=[r['id'] for r in gold] or sum(r['accepted'] for r in prior)!=12:
  raise ValueError('Original12accepted development identity required')
 return gold,capture,prior,files


def prepare(out):
 if (TASK/'readiness.json').exists(): raise ValueError('Existing preparation preserved')
 out=private(out)
 if out.exists(): raise ValueError('Existing preparation directory preserved')
 files={}
 for name,digest in KNOWN_PINS.items():
  path=REG/name
  if sha(path)!=digest: raise ValueError('Original known-regression preparation changed')
  files[str(path)]=digest
 known=strict((REG/'readiness.json').read_text())
 for path,digest in known['prior_pinned_sha256'].items():
  if sha(path)!=digest: raise ValueError('Pinned historical original changed')
  files[path]=digest
 original_gold=strict((REG/'build/prepared/route-gold.json').read_text())
 if len(original_gold)!=1582 or sum(r['correct_route'] for r in original_gold)!=158 or sum(r['old_kind_slots'][0]!='UNKNOWN' for r in original_gold)!=80:
  raise ValueError('Original known denominators required')
 gold,capture,prior,unit_files=pinned_unit_records();files.update(unit_files)
 out.mkdir(parents=True,exist_ok=False)
 dev_input=out/'development-input.tsv';dev_gold=out/'development-gold.json'
 rows=[]
 with dev_input.open('x') as f:
  for g,r,p in zip(gold,capture,prior):
   if g['id']!=r['id'] or g['expected']!=p['gold']: raise ValueError('Original gold/prior slots differ')
   f.write(g['id']+'\t'+base64.b64encode(r['text'].encode()).decode()+'\t'+g['utterance']+'\n')
   rows.append({'route_id':g['id'],'expected_kind_slots':canonical_tuple(g['expected']),
    'expected_canonical':g['expected'],'supported':g['expected']['intent']!='unknown',
    'prior_accepted':p['accepted'],'prior_kind_slots':canonical_tuple(p['proposal'])})
 write_new(dev_gold,rows)
 files.update({str(dev_input):sha(dev_input),str(dev_gold):sha(dev_gold)})
 ready={'schema':'focuspilot.compatible_validation_readiness.v1','phase':'prepared_no_candidate_calls',
  'candidate_calls':0,'candidate_contents_read':False,'model_calls':0,'phone_calls':0,'fresh_confirmation':False,
  'known_input':str(REG/'build/prepared/unit-input.tsv'),'known_gold':str(REG/'build/prepared/route-gold.json'),
  'development_input':str(dev_input),'development_gold':str(dev_gold),
  'known_rows':226,'known_routes':1582,'prior_accepted':80,'supported_oracle_routes':158,
  'unknown_routes':476,'supported_wrong_routes':948,'development_rows':24,'development_supported':18,
  'development_prior_accepted':12,'files_sha256':files,
  'checker_sources_sha256':{name:sha(TASK/name) for name in NAMES},
  'candidate_dependencies_expected':[str(p.relative_to(ROOT)) for p in DEPENDENCIES],
  'labels':'Exact original route-gold reused. Development kind/slot tuples are a representation of unchanged original canonical gold; no relabel or new utterances.',
  'scope':strict((TASK/'protocol.json').read_text())['scope']}
 write_new(TASK/'readiness.json',ready)
 return ready


def decisions(text,gold):
 lines=[line.split('\t') for line in text.splitlines()]
 if len(lines)!=len(gold) or [r[0] for r in lines]!=[r['route_id'] for r in gold] or any(len(r)!=10 for r in lines):
  raise ValueError('Complete ordered decision inventory required')
 out=[]
 for fields,row in zip(lines,gold):
  if fields[1] not in ('true','false'): raise ValueError('Acceptance boolean required')
  accepted=fields[1]=='true';proposal=[fields[2],*map(int,fields[3:6])]
  canonical=strict(base64.b64decode(fields[7],validate=True).decode())
  if canonical_tuple(canonical)!=proposal or accepted!=(proposal[0]!='UNKNOWN'):
   raise ValueError('Canonical action/slots/acceptance disagree')
  app=canonical.get('app','')
  if fields[6]!=app: raise ValueError('Approved app identity differs')
  if fields[9] not in ('FAST_LOCAL_REQUEST','CHECKED_MODEL','UNKNOWN') or (fields[9]=='UNKNOWN')==accepted:
   raise ValueError('Explicit origin and acceptance disagree')
  out.append({'route_id':row['route_id'],'accepted':accepted,'proposal':proposal,'canonical':canonical,
   'reason':base64.b64decode(fields[8],validate=True).decode(),'origin':fields[9],
   'complete':accepted and proposal==row['expected_kind_slots']})
 return out


def summarize_known(gold,actual):
 counts=dict(prior_accepted=0,prior_preserved=0,prior_regressions=0,supported_oracle_routes=0,
  supported_oracle_complete=0,supported_oracle_wrong_accepts=0,unknown_routes=0,
  unknown_false_accepts=0,supported_wrong_routes=0,supported_wrong_route_false_accepts=0)
 for g,a in zip(gold,actual):
  if g['old_kind_slots'][0]!='UNKNOWN':
   kept=a['accepted'] and a['proposal']==g['old_kind_slots'];counts['prior_accepted']+=1
   counts['prior_preserved']+=int(kept);counts['prior_regressions']+=int(not kept)
  if g['correct_route']:
   counts['supported_oracle_routes']+=1;counts['supported_oracle_complete']+=int(a['complete'])
   counts['supported_oracle_wrong_accepts']+=int(a['accepted'] and not a['complete'])
  elif not g['supported']:counts['unknown_routes']+=1;counts['unknown_false_accepts']+=int(a['accepted'])
  else:counts['supported_wrong_routes']+=1;counts['supported_wrong_route_false_accepts']+=int(a['accepted'])
 if [counts[k] for k in ('prior_accepted','supported_oracle_routes','unknown_routes','supported_wrong_routes')]!=[80,158,476,948]:
  raise ValueError('Known denominator mismatch')
 return counts


def summarize_development(gold,actual):
 counts=dict(rows=len(gold),supported_rows=0,supported_complete=0,unknown_rows=0,unknown_refused=0,
  wrong_accepts=0,prior_accepted=0,prior_preserved=0,gains=0,losses=0)
 for g,a in zip(gold,actual):
  supported=g['supported'];counts['supported_rows']+=int(supported);counts['unknown_rows']+=int(not supported)
  counts['supported_complete']+=int(supported and a['complete']);counts['unknown_refused']+=int(not supported and not a['accepted'])
  counts['wrong_accepts']+=int(a['accepted'] and a['proposal']!=g['expected_kind_slots'])
  if g['prior_accepted']:
   counts['prior_accepted']+=1;counts['prior_preserved']+=int(a['accepted'] and a['proposal']==g['prior_kind_slots'])
  before=g['prior_accepted'] and g['prior_kind_slots']==g['expected_kind_slots']
  counts['gains']+=int(supported and not before and a['complete']);counts['losses']+=int(supported and before and not a['complete'])
 if [counts[k] for k in ('rows','supported_rows','unknown_rows','prior_accepted')]!=[24,18,6,12]:raise ValueError('Development denominator mismatch')
 return counts


def evaluate(source_commit,out):
 if not re.fullmatch(r'[a-f0-9]{40}',source_commit) or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=source_commit:
  raise ValueError('Exact common frozen HEAD required')
 ready=strict((TASK/'readiness.json').read_text()); bindings={}
 for path,digest in ready['files_sha256'].items():
  if sha(path)!=digest:raise ValueError('Frozen original input changed')
 for name,digest in ready['checker_sources_sha256'].items():
  if sha(TASK/name)!=digest:raise ValueError('Prepared checker source changed')
 for path in [*DEPENDENCIES,*(TASK/name for name in NAMES),TASK/'readiness.json']:
  relative=str(path.relative_to(ROOT));current=path.read_bytes()
  if subprocess.check_output(['git','show',source_commit+':'+relative],cwd=ROOT)!=current:raise ValueError('Source differs from common freeze')
  bindings[relative]=sha(path)
 out=private(out)
 if out.exists():raise ValueError('Existing evaluation preserved')
 claim=Path(ready['development_input']).parent/'evaluation-claim.json'
 write_new(claim,{'source_commit':source_commit,'readiness_sha256':sha(TASK/'readiness.json'),'out':str(out)})
 out.mkdir(parents=True,exist_ok=False);classes=out/'classes';classes.mkdir()
 subprocess.run([str(JAVA/'javac'),'-d',str(classes),*map(str,DEPENDENCIES),str(TASK/'CompatibleRegression.java')],check=True,timeout=30)
 results={};details={}
 for name in ('known','development','pipeline'):
  dataset='development' if name=='pipeline' else name
  input_path=Path(ready[dataset+'_input']);gold=strict(Path(ready[dataset+'_gold']).read_text());output=out/(name+'-decisions.tsv')
  with output.open('x') as f:subprocess.run([str(JAVA/'java'),'-cp',str(classes),'dev.focuspilot.prototype.CompatibleRegression',name,str(input_path)],stdout=f,check=True,timeout=30)
  actual=decisions(output.read_text(),gold);details[name]=actual
  if name!='pipeline' and any(r['origin']=='FAST_LOCAL_REQUEST' for r in actual):raise ValueError('Model-validator replay must not use fast recognition')
  results[name]=summarize_known(gold,actual) if name=='known' else summarize_development(gold,actual)
  if name=='pipeline':
   results[name]['origin_counts']={origin:sum(r['origin']==origin for r in actual) for origin in ('FAST_LOCAL_REQUEST','CHECKED_MODEL','UNKNOWN')}
  write_new(out/(name+'-details.json'),actual)
 known=results['known'];dev=results['development'];pipe=results['pipeline'];criteria=strict((TASK/'protocol.json').read_text())['criteria']
 checks={'all80_preserved':known['prior_preserved']==criteria['prior_80_preserved'],
  'all476_unknown_refused':known['unknown_false_accepts']==criteria['unknown_false_accepts'],
  'all948_wrong_routes_refused':known['supported_wrong_route_false_accepts']==criteria['supported_wrong_route_false_accepts'],
  'no_wrong_oracle':known['supported_oracle_wrong_accepts']==criteria['supported_oracle_wrong_accepts'],
  'all12_development_accepted_preserved':dev['prior_preserved']==criteria['prior_development_accepted_preserved'],
  'all6_development_unknown_refused':dev['unknown_refused']==criteria['development_unknown_refusals'],
  'no_development_wrong_accepts':dev['wrong_accepts']==criteria['development_wrong_accepts'],
  'pipeline_all12_prior_preserved':pipe['prior_preserved']==criteria['prior_development_accepted_preserved'],
  'pipeline_all6_unknown_refused':pipe['unknown_refused']==criteria['development_unknown_refusals'],
  'pipeline_no_wrong_accepts':pipe['wrong_accepts']==criteria['development_wrong_accepts']}
 # Preserve inputs and source identity through the complete pure-Java run.
 for path,digest in ready['files_sha256'].items():
  if sha(path)!=digest:raise ValueError('Original input changed during replay')
 for path,digest in bindings.items():
  if sha(ROOT/path)!=digest:raise ValueError('Frozen source changed during replay')
 if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=source_commit:raise ValueError('HEAD changed during replay')
 result={'schema':'focuspilot.compatible_validation_result.v1','source_commit':source_commit,
  'phase':'seen_development_validator_repair','known':known,'development':dev,'pipeline':pipe,'criteria':checks,
  'decision':'ELIGIBLE_FOR_SEPARATE_FRESH_QUALIFICATION_NOT_PHONE' if all(checks.values()) else 'REJECT_DEVELOPMENT_KEEP_APP',
  'model_calls':0,'phone_calls':0,'fresh_confirmation':False,'promoted':False,
  'readiness_sha256':sha(TASK/'readiness.json'),'source_sha256':bindings,
  'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in out.rglob('*') if p.is_file()},
  'limitations':strict((TASK/'protocol.json').read_text())['limitations']}
 write_new(out/'results.json',result)
 return result


if __name__=='__main__':
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
 prep=sub.add_parser('prepare');prep.add_argument('--out',required=True)
 run=sub.add_parser('evaluate');run.add_argument('--source-commit',required=True);run.add_argument('--out',required=True)
 args=parser.parse_args()
 print(json.dumps(prepare(args.out) if args.mode=='prepare' else evaluate(args.source_commit,args.out),indent=2))
