"""Seen development test of copied units; no app/tool execution."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess

TASK=Path(__file__).resolve().parent; ROOT=TASK.parents[1]
JAVA=Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path); value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
old=module('seconds_scoring',ROOT/'prototype/structured-eval/evaluate.py')
driver=module('units_driver',ROOT/'prototype/unit-native/run_capture.py')
UNIT=ROOT/'prototype/unit-command'; DATA=ROOT/'prototype/structured-data'
REFERENCE=ROOT/'prototype/structured-native/build/dev-structured-capture'



def private(path):
 path=Path(path).resolve()
 if TASK/'build' not in path.parents:raise ValueError('Ignored unit-eval/build required')
 return path


def expected_raw(row,labels):
 expected=row['expected']; raw=labels[row['id']]
 if raw.get('intent')!=expected['intent']:raise ValueError('Reviewed intent labels differ')
 if expected['intent'] not in ('start_focus','timer'):
  if raw!=expected:raise ValueError('Nonduration labels differ')
  return dict(raw)
 if set(raw)!={'intent','amount','unit'} or type(raw['amount']) is not int or raw['unit'] not in {'none','seconds','minutes','hours'}:raise ValueError('Strict reviewed unit label required')
 if raw['amount']*{'none':0,'seconds':1,'minutes':60,'hours':3600}[raw['unit']]!=expected['duration_seconds'] or raw['amount']<0 or raw['unit']=='none' and (raw['amount']!=0 or expected['intent']!='start_focus'):raise ValueError('Reviewed unit/canonical label disagreement')
 return dict(raw)


def labels(cohort):
 manifest=driver.strict_json((TASK/'labels-manifest.json').read_text());path=TASK/'build/author-unit-labels.json'
 if driver.sha(path)!=manifest['raw_labels_sha256'] or driver.sha(DATA/'build/development.jsonl')!=manifest['canonical_gold_sha256']:raise ValueError('Reviewed label identities differ')
 value=driver.strict_json(path.read_text())
 if set(value)!={r['id'] for r in cohort}:raise ValueError('Exact24label inventory required')
 for row in cohort:expected_raw(row,value)
 return value


def prepare(out):
 cohort=old.rows(); unit_labels=labels(cohort); driver.runtime_guard()
 if driver.sha(driver.MODEL)!=driver.MODEL_SHA:raise ValueError('Pinned model differs before tokenization')
 out=private(out);out.mkdir(parents=True,exist_ok=False)
 sources=[ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype/CommandNumberWords.java',
          ROOT/'prototype/structured-command/StructuredCommand.java',UNIT/'UnitCommand.java',
          UNIT/'UnitCommandRender.java',TASK/'UnitCompare.java']
 snapshots=out/'source';snapshots.mkdir();classes=out/'java';classes.mkdir()
 copies=[]
 for source in sources:
  target=snapshots/source.name;target.write_bytes(source.read_bytes());copies.append(target)
 subprocess.run([str(JAVA/'javac'),'-d',str(classes),*map(str,copies)],check=True,timeout=30)
 render=[str(JAVA/'java'),'-cp',str(classes),'dev.focuspilot.prototype.UnitCommandRender']
 prompts=out/'unit-prompts.tsv';grammar=out/'unit-grammar.gbnf'
 prompts.write_text(subprocess.check_output(render+[str(DATA/'build/development-requests.tsv')],text=True,timeout=30))
 grammar.write_text(subprocess.check_output(render+['--grammar'],text=True,timeout=30))
 if [r[0] for r in driver.prompts(prompts)]!=[r['id'] for r in cohort]:raise ValueError('Exact24ordered IDs required')
 driver.write_new(out/'raw-unit-labels.json',[{'id':r['id'],'expected_raw':expected_raw(r,unit_labels)} for r in cohort])
 # Verify the original actual-record audit before treating historical data as reference.
 audit=driver.strict_json((ROOT/'prototype/structured-eval/independent-audit.json').read_text())
 for path,digest in audit['files_sha256'].items():
  actual=Path(path) if Path(path).is_absolute() else ROOT/path
  if driver.sha(actual)!=digest:raise ValueError('Historical reference audit binding differs: '+str(actual))
 token_binary=ROOT/'prototype/structured-eval/build/dev-token-preflight/token_count'
 oldfreeze=driver.strict_json((ROOT/'prototype/structured-eval/execution-freeze.json').read_text())
 if driver.sha(token_binary)!=oldfreeze['token_preflight']['binary_sha256']:raise ValueError('Pinned token-only binary differs')
 folder=out/'token-prompts';folder.mkdir()
 for ident,prompt in driver.prompts(prompts):(folder/(ident+'.txt')).write_bytes(prompt.encode())
 with (out/'tokens.jsonl').open('x') as stdout,(out/'token-stderr.log').open('x') as stderr:
  job=subprocess.run([str(token_binary),str(driver.MODEL),str(folder)],stdout=stdout,stderr=stderr,timeout=60)
 if job.returncode!=0:raise ValueError('Token-only preflight failed; preserve outputs')
 counts=[driver.strict_json(line) for line in (out/'tokens.jsonl').read_text().splitlines()]
 if [r['id'] for r in counts]!=sorted(r['id'] for r in cohort) or not all(r['within_limit'] is True and r['generation_called'] is False and 0<r['token_count']<=896 for r in counts):raise ValueError('Actual tokenizer inventory/budget required')
 pins=sources+copies+list(classes.rglob('*.class'))
 pins +=[p for folder in (TASK,UNIT,ROOT/'prototype/unit-native') for p in folder.iterdir() if p.is_file()]
 pins +=[TASK/'build/author-unit-labels.json',DATA/'data-manifest.json',DATA/'manual-review.json',DATA/'build/development.jsonl',DATA/'build/development-requests.tsv',
         ROOT/'prototype/structured-eval/independent-audit.json',ROOT/'prototype/structured-eval/results.json',
         ROOT/'prototype/structured-eval/evaluate.py',token_binary,*out.rglob('*.json'),out/'tokens.jsonl',out/'token-stderr.log',*folder.iterdir(),
         REFERENCE/'raw.jsonl',REFERENCE/'process.json']
 lock=driver.prepare(prompts,grammar,ROOT/'prototype/unit-native/build/dev-lock',pins)
 record={'schema':'focuspilot.unit_comparison_lock.v1','classes':str(classes),'lock':str(lock),'rows':24,
         'gold_sha256':driver.sha(DATA/'build/development.jsonl'),'reference_raw_sha256':driver.sha(REFERENCE/'raw.jsonl'),
         'raw_unit_labels_sha256':driver.sha(out/'raw-unit-labels.json'),'token_count_min':min(r['token_count'] for r in counts),'token_count_max':max(r['token_count'] for r in counts)}
 driver.write_new(out/'comparison-lock.json',record);return out/'comparison-lock.json'


def gates(route,cohort,responses,classes,out):
 encoded=lambda s:base64.b64encode(s.encode()).decode()
 input_path=out/(route+'-input.tsv')
 with input_path.open('x') as f:
  for r in cohort:f.write(r['id']+'\t'+encoded(r['utterance'])+'\t'+encoded(responses[r['id']])+'\n')
 mode='seconds' if route.startswith('seconds') else 'raw' if route=='raw' else 'units'
 raw=subprocess.check_output([str(JAVA/'java'),'-cp',classes,'dev.focuspilot.prototype.UnitCompare',mode,str(input_path)],text=True,timeout=30)
 (out/(route+'-output.tsv')).write_text(raw);values={}
 for line in raw.splitlines():
  parts=line.split('\t')
  if len(parts)!=4 or parts[0] in values or parts[2] not in ('true','false'):raise ValueError('Strict ordered proposal output required')
  proposal=driver.strict_json(base64.b64decode(parts[1],validate=True));old.shape(proposal)
  values[parts[0]]=(proposal,parts[2]=='true',base64.b64decode(parts[3],validate=True).decode())
 if list(values)!=[r['id'] for r in cohort]:raise ValueError('Complete24decision inventory required')
 return values


def assess(candidate,p,criteria):
 return {'net_gain':p['gain']-p['loss']>=criteria['complete_supported_net_gain_minimum'],'losses':p['loss']<=criteria['complete_supported_losses_maximum'],'start':candidate['per_class']['start_focus']['complete_correct']>=criteria['complete_start_minimum'],'wrong_accepts':candidate['wrong_accepts']<=criteria['wrong_accepts_maximum'],'unknown_refusals':candidate['unknown_validator_refusals']==criteria['unknown_validator_refusals_required']}


def score(comparison,capture,out,commit):
 frozen=TASK/'execution-freeze.json'
 committed=subprocess.check_output(['git','show',commit+':'+str(frozen.relative_to(ROOT))],cwd=ROOT)
 if hashlib.sha256(committed).hexdigest()!=driver.sha(frozen):raise ValueError('Committed execution freeze differs')
 freeze=driver.strict_json(frozen.read_text());comparison=Path(comparison)
 if driver.sha(comparison)!=freeze['comparison_lock_sha256']:raise ValueError('Comparison freeze differs')
 lock=driver.strict_json(comparison.read_text()); native_path=Path(lock['lock'])
 if driver.sha(native_path)!=freeze['native_lock_sha256']:raise ValueError('Capture lock differs')
 native=driver.strict_json(native_path.read_text());driver.verify_lock(native,commit)
 cohort=old.rows();unit_labels=labels(cohort)
 if driver.sha(DATA/'build/development.jsonl')!=lock['gold_sha256']:raise ValueError('Canonical labels differ')
 capture=driver.private_path(capture);process=driver.strict_json((capture/'process.json').read_text())
 if process['source_commit']!=commit or process['exit_code']!=0 or process['timed_out'] or process.get('error_type') or process.get('postflight_error_type') or process['adapter'] is not False or process['model_sha256']!=driver.MODEL_SHA or process['lock_sha256']!=driver.sha(native_path):raise ValueError('Complete base-only capture required')
 if type(process['pid']) is not int or process['pid']<=0 or process['command']!=[native['binary'],str(driver.MODEL),'-',native['prompts'],native['grammar']]:raise ValueError('Exact owned command binding required')
 initial=driver.strict_json((capture/'initial.json').read_text());started=driver.strict_json((capture/'started.json').read_text())
 if initial['pid'] is not None or started['pid']!=process['pid'] or set(initial)!=set(started):raise ValueError('Process event identity differs')
 for key in initial:
  if key!='pid' and (initial[key]!=started[key] or initial[key]!=process[key]):raise ValueError('Process event metadata differs')
 for name,key in [('raw.jsonl','raw_sha256'),('stderr.log','stderr_sha256'),('initial.json','initial_sha256'),('started.json','started_sha256')]:
  if driver.sha(capture/name)!=process[key]:raise ValueError('Capture digest differs')
 load,records=driver.validate_capture((capture/'raw.jsonl').read_text(),native['ids'])
 if driver.sha(REFERENCE/'raw.jsonl')!=lock['reference_raw_sha256']:raise ValueError('Historical reference differs')
 _,reference=driver.validate_capture((REFERENCE/'raw.jsonl').read_text(),native['ids'])
 out=private(out);out.mkdir(parents=True,exist_ok=False)
 generated={r['id']:r['text'] for r in records}; seconds={r['id']:r['text'] for r in reference}
 oracle={r['id']:json.dumps(expected_raw(r,unit_labels),separators=(',',':')) for r in cohort}
 raw={r['id']:driver.strict_json(r['text']) for r in records}
 raw_proposals=gates('raw',cohort,generated,lock['classes'],out)
 result={'schema':'focuspilot.unit_development_result.v1','source_commit':commit,'phase':'seen_development_only','phone_promoted':False,'training_performed':False,'model_sha256':driver.MODEL_SHA,'comparison_lock_sha256':driver.sha(comparison),'arms':{}}
 details={}
 for route,responses in [('seconds-generated',seconds),('units-generated',generated),('units-oracle',oracle)]:
  proposals=gates(route,cohort,responses,lock['classes'],out)
  used_raw={r['id']:driver.strict_json(r['text']) for r in reference} if route.startswith('seconds') else raw
  summary,rows=old.summarize(cohort,used_raw,proposals)
  if route.startswith('units'):
   summary['raw_structured_exact_supported']=sum(r['expected']['intent']!='unknown' and raw_proposals[r['id']][0]==r['expected'] for r in cohort)
   summary['raw_copy_unit_exact_supported']=sum(r['expected']['intent']!='unknown' and raw[r['id']]==expected_raw(r,unit_labels) for r in cohort)
  if route.endswith('oracle'):
   for key in ('raw_intent_correct','raw_structured_exact_supported','raw_copy_unit_exact_supported','unknown_model_abstentions','confusion'):summary[key]=None
   for entry in summary['per_class'].values():entry['raw_intent_correct']=None
  result['arms'][route]=summary;details[route]=rows;driver.write_new(out/(route+'-details.json'),rows)
 reference_expected=driver.strict_json((ROOT/'prototype/structured-eval/results.json').read_text())['arms']['structured']['generated']
 if result['arms']['seconds-generated']!=reference_expected:raise ValueError('Historical score replay differs')
 paired=[{'id':a['id'],'supported':a['supported'],'gain':not a['complete_correct'] and b['complete_correct'],'loss':a['complete_correct'] and not b['complete_correct']} for a,b in zip(details['seconds-generated'],details['units-generated'])]
 result['paired_supported']={key:sum(r['supported'] and r[key] for r in paired) for key in ('gain','loss')}
 driver.write_new(out/'paired.json',paired)
 metrics=[r['metrics'] for r in records]
 result['capture']={'rows':24,'canonical_json_actual_eos':24,'load_ms':load['load_ms'],'wrapper_seconds':process['seconds'],'first_native_ms':metrics[0]['total_ms'],'subsequent_median_native_ms':statistics.median(r['total_ms'] for r in metrics[1:]),'prompt_tokens_min':min(r['prompt_tokens'] for r in metrics),'prompt_tokens_max':max(r['prompt_tokens'] for r in metrics),'generated_tokens_min':min(r['generated_tokens'] for r in metrics),'generated_tokens_max':max(r['generated_tokens'] for r in metrics)}
 candidate=result['arms']['units-generated'];p=result['paired_supported'];criteria=driver.strict_json((TASK/'protocol.json').read_text())['development_advance_criteria']
 checks=assess(candidate,p,criteria)
 result['criteria']=checks;result['decision']='ADVANCE_TO_SEPARATE_QUALIFICATION_NOT_PHONE' if all(checks.values()) else 'REJECT_DEVELOPMENT_KEEP_APP'
 result['limitations']=driver.strict_json((TASK/'protocol.json').read_text())['limitations']
 driver.verify_lock(native,commit)
 result['files_sha256']={str(p.relative_to(ROOT)):driver.sha(p) for folder in (out,capture) for p in folder.iterdir() if p.is_file()}
 driver.write_new(out/'result.json',result);return result


if __name__=='__main__':
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
 p=sub.add_parser('prepare');p.add_argument('--out',required=True)
 p=sub.add_parser('score')
 for key in ('comparison','capture','out','source-commit'):p.add_argument('--'+key,required=True)
 a=parser.parse_args()
 if a.mode=='prepare':print(prepare(a.out))
 else:print(json.dumps(score(a.comparison,a.capture,a.out,a.source_commit),indent=2))
