"""Prospectively frozen compatible-unit confirmation tools; no Android actions."""
import argparse
import base64
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

sys.dont_write_bytecode = True
TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
DATA = ROOT/'prototype/compatible-data'
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
APP = ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
INTENTS = ('start_focus','pause_focus','alarm','timer','open_app','explain','unknown')


def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


driver = module('compatible_native_driver',ROOT/'prototype/unit-native/run_capture.py')
author = module('compatible_data_contract',DATA/'generate_data.py')


def private(path):
 path=Path(path).resolve()
 if TASK/'build' not in path.parents:raise ValueError('Ignored compatible-eval/build required')
 return path


def canonical(value):
 return author.validate_expected(value)


def raw_canonical(value):
 return author.canonical_raw(value)


def ordered_unit_response(value):
 # JSONL author serialization sorts keys; the runtime schema deliberately fixes
 # intent first, then action-specific slots. Never inherit mapping insertion order.
 author.validate_expected(value,raw=True)
 keys=['intent']
 if value['intent'] in ('start_focus','timer'):keys+=['amount','unit']
 elif value['intent']=='alarm':keys+=['hour','minute']
 elif value['intent']=='open_app':keys+=['app']
 return json.dumps({key:value[key] for key in keys},separators=(',',':'))


def json_file(path):
 return driver.strict_json(Path(path).read_text())


def bind(files,path,expected=None):
 path=Path(path).resolve();actual=driver.sha(path)
 if expected is not None and actual!=expected:raise ValueError('Pinned file changed: '+path.name)
 files[str(path)]=actual
 return actual


def corpus():
 """Called only by explicitly authorized preparation/scoring, never at import."""
 protocol=json_file(TASK/'protocol.json');manifest=json_file(DATA/'corpus-manifest.json')
 gold=DATA/'build/confirmation.jsonl';requests=DATA/'build/confirmation-requests.tsv'
 files={};bind(files,gold,manifest['jsonl_sha256']);bind(files,requests,manifest['requests_sha256'])
 for path,key in [(TASK/'source-freeze.json','source_freeze_sha256'),(TASK/'protocol.json','protocol_sha256'),
                  (TASK/'novelty-exclusions.json','exclusion_bundle_sha256')]:bind(files,path,manifest[key])
 if (manifest.get('before_outputs') is not True or manifest.get('model_gate_oracle_calls')!=0
     or manifest.get('filtered_by_gate_or_oracle') is not False
     or manifest.get('candidate_validator_tests_prompt_outputs_read_by_author') is not False):
  raise ValueError('Prospective unfiltered author provenance required')
 for name,digest in manifest['generic_source_sha256'].items():bind(files,DATA/name,digest)
 rows=[driver.strict_json(line) for line in gold.read_text().splitlines()]
 author.validate_rows(rows,protocol)
 if requests.read_text().splitlines()!=[r['id']+'\t'+r['utterance'] for r in rows]:
  raise ValueError('Exact gold/request ordered inventory required')
 exclusions=json_file(TASK/'novelty-exclusions.json');author.reject_excluded(rows,exclusions)
 for item in exclusions['inventory']:bind(files,ROOT/item['path'],item['sha256'])
 if Counter(r['expected']['intent'] for r in rows)!=manifest['by_intent']:
  raise ValueError('Manifest intent counts differ')
 review=json_file(DATA/'manual-review.json')
 if (review.get('corpus_jsonl_sha256')!=manifest['jsonl_sha256']
     or type(review.get('all_rows_reviewed')) is not int or review['all_rows_reviewed']!=100
     or review.get('before_model_or_gate_outputs') is not True or not review.get('reviewers')):
  raise ValueError('Actual complete manual review before model/gate outputs required')
 independent_path=ROOT/'prototype/compatible-unit/fresh-label-review.json'
 independent=json_file(independent_path)
 if (independent.get('corpus_jsonl_sha256')!=manifest['jsonl_sha256']
     or independent.get('requests_sha256')!=manifest['requests_sha256']
     or type(independent.get('all_rows_reviewed')) is not int or independent['all_rows_reviewed']!=100
     or independent.get('before_model_or_gate_outputs') is not True
     or independent.get('semantic_ambiguities_remaining')!=0):
  raise ValueError('Independent complete final manual label review required')
 bind(files,independent_path)
 clarification_path=DATA/'pre-output-manual-clarification.json'
 clarification=json_file(clarification_path)
 if (clarification.get('current_jsonl_sha256')!=manifest['jsonl_sha256']
     or clarification.get('current_requests_sha256')!=manifest['requests_sha256']
     or clarification.get('before_model_or_gate_outputs') is not True
     or clarification.get('all100_gold_objects_unchanged') is not True):
  raise ValueError('Preserved pre-output semantic clarification provenance required')
 bind(files,clarification_path)
 for path,digest in clarification['archives_sha256'].items():
  if not author.relative_path(path):raise ValueError('Project-relative preserved archive required')
  bind(files,DATA/path,digest)
 audit_path=DATA/'authoring-audit.json';audit=json_file(audit_path)
 if audit.get('frozen_jsonl_sha256')!=manifest['jsonl_sha256'] or audit.get('model_gate_or_oracle_calls')!=0:
  raise ValueError('Final authoring provenance differs')
 bind(files,audit_path)
 source_freeze=json_file(TASK/'source-freeze.json');commit=manifest['source_authorization_commit']
 if not isinstance(commit,str) or len(commit)!=40:raise ValueError('Full author source authorization commit required')
 subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,check=True,capture_output=True,timeout=30)
 for path,digest in source_freeze['files_sha256'].items():
  bind(files,ROOT/path,digest)
  if hashlib.sha256(subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT,timeout=30)).hexdigest()!=digest:
   raise ValueError('Source freeze differs from actual author authorization commit')
 author_path=review.get('author_input_path')
 if not author.relative_path(author_path):raise ValueError('Preserved original author input path required')
 bind(files,ROOT/author_path,manifest['author_input_sha256'])
 for path in [TASK/'source-freeze.json',TASK/'protocol.json',TASK/'design-lock.json',TASK/'novelty-exclusions.json']:
  relative=str(path.relative_to(ROOT))
  if subprocess.check_output(['git','show',commit+':'+relative],cwd=ROOT,timeout=30)!=path.read_bytes():
   raise ValueError('Prospective metadata differs from author source commit')
 for path in [DATA/'corpus-manifest.json',DATA/'manual-review.json',TASK/'source-freeze.json',TASK/'design-lock.json']:
  bind(files,path)
 return rows,protocol,manifest,files


def historical(files):
 path=ROOT/'prototype/compatible-validation/results.json';result=json_file(path);bind(files,path)
 for source,digest in result['source_sha256'].items():bind(files,ROOT/source,digest)
 for source,digest in result['inputs_sha256'].items():bind(files,ROOT/source,digest)
 known=result['known']
 if (known['prior_accepted']!=80 or known['prior_preserved']!=80 or known['prior_regressions']!=0
     or known['supported_oracle_wrong_accepts'] or known['unknown_false_accepts']
     or known['supported_wrong_route_false_accepts'] or known['unknown_routes']!=476
     or known['supported_wrong_routes']!=948):raise ValueError('Current candidate historical preservation evidence required')
 return {key:known[key] for key in known}


def budget(protocol):
 sys.path.insert(0,str(ROOT/'scripts'))
 from package_bundled_apk import project_bytes
 if project_bytes(ROOT)+protocol['storage']['incremental_reserve_bytes']>protocol['storage']['project_cap_bytes']:
  raise ValueError('Prospective output storage reserve exceeds project cap')


def native_budget(files):
 # Both locks pin the same source inventory. Include conservative framing, generated
 # JSON and runtime logs for200 bounded requests, without modifying the old driver.
 existing=sum(p.stat().st_size for p in driver.TASK.rglob('*') if p.is_file())
 lock_bytes=len(json.dumps(files,indent=2).encode())*2+40_000
 reserve=lock_bytes+1_000_000
 if existing+reserve>2_000_000:raise ValueError('Two-arm reserve exceeds immutable native subtree allowance')
 return {'existing_bytes':existing,'two_arm_reserved_bytes':reserve,'cap_bytes':2_000_000}


def prepare(out):
 rows,protocol,manifest,files=corpus();old=historical(files);budget(protocol)
 driver.runtime_guard()
 if driver.sha(driver.MODEL)!=driver.MODEL_SHA:raise ValueError('Pinned existing base model required')
 out=private(out);out.mkdir(parents=True,exist_ok=False)
 sources=[APP/name for name in ('LocalModel.java','ModelCommandGate.java','CommandNumberWords.java')]
 sources += [ROOT/'prototype/qwen-balanced-native/Render.java',
  ROOT/'prototype/structured-command/StructuredCommand.java',ROOT/'prototype/unit-command/UnitCommand.java',
  ROOT/'prototype/unit-command/UnitCommandRender.java',ROOT/'prototype/compatible-unit/CompatibleUnitCommand.java',
  ROOT/'prototype/compatible-unit/CompatibleUnitCommandRender.java',TASK/'CompatibleCompare.java']
 snapshots=out/'source';snapshots.mkdir();classes=out/'java';classes.mkdir();copies=[]
 for source in sources:
  copy=snapshots/source.name
  with copy.open('xb') as f:f.write(source.read_bytes())
  copies.append(copy);bind(files,source)
 subprocess.run([str(JAVA/'javac'),'-d',str(classes),*map(str,copies)],check=True,timeout=30)
 requests=DATA/'build/confirmation-requests.tsv'
 prompts={};grammars={}
 jni=ROOT/'prototype/command-eval/build/native/libfocuspilot_local.dylib'
 oldfreeze=json_file(ROOT/'prototype/structured-eval/execution-freeze.json')
 bind(files,jni,'ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e')
 prompts['baseline']=out/'baseline-prompts.tsv';grammars['baseline']=out/'baseline-grammar.gbnf'
 subprocess.run([str(JAVA/'java'),'-Djava.library.path='+str(jni.parent),'-cp',str(classes),
  'dev.focuspilot.prototype.Render',str(requests),str(prompts['baseline']),str(grammars['baseline'])],check=True,timeout=30)
 prompts['candidate']=out/'candidate-prompts.tsv';grammars['candidate']=out/'candidate-grammar.gbnf'
 render=[str(JAVA/'java'),'-cp',str(classes),'dev.focuspilot.prototype.CompatibleUnitCommandRender']
 with prompts['candidate'].open('x') as f:f.write(subprocess.check_output(render+[str(requests)],text=True,timeout=30))
 with grammars['candidate'].open('x') as f:f.write(subprocess.check_output(render+['--grammar'],text=True,timeout=30))
 token_binary=ROOT/'prototype/structured-eval/build/dev-token-preflight/token_count'
 bind(files,token_binary,oldfreeze['token_preflight']['binary_sha256'])
 bind(files,ROOT/'prototype/structured-eval/token_count.cpp',oldfreeze['token_preflight']['source_sha256'])
 bind(files,ROOT/'prototype/structured-eval/execution-freeze.json')
 token_report={}
 for arm in ('baseline','candidate'):
  rendered=driver.prompts(prompts[arm]);driver.grammar(grammars[arm])
  if [i for i,_ in rendered]!=[r['id'] for r in rows]:raise ValueError('Rendered complete100 inventory differs')
  folder=out/(arm+'-token-prompts');folder.mkdir()
  for ident,prompt in rendered:
   with (folder/(ident+'.txt')).open('xb') as f:f.write(prompt.encode())
  token_path=out/(arm+'-tokens.jsonl');stderr=out/(arm+'-token-stderr.log')
  command=[str(token_binary),str(driver.MODEL),str(folder)]
  with token_path.open('x') as stdout,stderr.open('x') as err:
   job=subprocess.run(command,stdout=stdout,stderr=err,timeout=60)
  if job.returncode!=0:raise ValueError('Tokenizer-only preflight failed; preserve outputs')
  counts=[driver.strict_json(line) for line in token_path.read_text().splitlines()]
  if (len(counts)!=100 or [r['id'] for r in counts]!=sorted(r['id'] for r in rows)
      or any(r['within_limit'] is not True or r['generation_called'] is not False or r['vocab_only'] is not True
          or r['add_special'] is not True or r['parse_special'] is not True or r['n_gpu_layers']!=0
          or r['maximum_prompt_tokens']!=896 or type(r['token_count']) is not int or not 1<=r['token_count']<=896 for r in counts)):
   raise ValueError('Actual complete tokenizer-only context budget required')
  token_report[arm]={'rows':100,'minimum':min(r['token_count'] for r in counts),
   'maximum':max(r['token_count'] for r in counts),'exit_code':job.returncode,'generation_called':False,
   'command':command,'counts_sha256':driver.sha(token_path),'counts_path':str(token_path)}
 for path in [*copies,*classes.rglob('*.class'),*out.rglob('*.txt'),*out.glob('*.jsonl'),*out.glob('*.log'),
              TASK/'evaluate.py',TASK/'test_evaluate.py',TASK/'CompatibleCompare.java',TASK/'protocol.json']:
  bind(files,path)
 allowance=native_budget(files);locks={}
 for arm in ('baseline','candidate'):
  locks[arm]=str(driver.prepare(prompts[arm],grammars[arm],
   driver.TASK/('build/compatible-fresh-'+arm+'-lock'),list(files)))
 comparison={'schema':'focuspilot.compatible_comparison_lock.v1','classes':str(classes),
  'rows':100,'ids':[r['id'] for r in rows],'locks':locks,'gold_sha256':manifest['jsonl_sha256'],
  'historical':old,'token_preflight':token_report,'native_subtree_allowance':allowance,'files_sha256':files,
  'scope':'Prepared only; vocabulary-only model load and prompt rendering, no generation or candidate validation/recognition calls.'}
 driver.write_new(out/'comparison-lock.json',comparison)
 return out/'comparison-lock.json'


def validate_process(capture,native_path,native,commit):
 capture=driver.private_path(capture);process=json_file(capture/'process.json')
 if (process['schema']!='focuspilot.unit_native_process.v1' or process['source_commit']!=commit or process['exit_code']!=0 or process['timed_out'] is not False
     or process.get('error_type') or process.get('postflight_error_type') or process['adapter'] is not False
     or process['model_sha256']!=driver.MODEL_SHA or process['lock_sha256']!=driver.sha(native_path)
     or type(process['pid']) is not int or process['pid']<=0 or not 0<process['seconds']<=240
     or process['command']!=[native['binary'],str(driver.MODEL),'-',native['prompts'],native['grammar']]):
  raise ValueError('Exact terminal successful base-only process required')
 claim=json_file(Path(native_path).parent/'capture-claim.json')
 if claim!={'source_commit':commit,'lock_sha256':driver.sha(native_path),'out':str(capture)}:
  raise ValueError('Single exact capture claim required')
 initial=json_file(capture/'initial.json');started=json_file(capture/'started.json')
 if initial['pid'] is not None or started['pid']!=process['pid'] or set(initial)!=set(started):raise ValueError('Exact process event identity required')
 for key in initial:
  if key!='pid' and (initial[key]!=started[key] or initial[key]!=process[key]):raise ValueError('Immutable process event changed')
 for name,key in [('raw.jsonl','raw_sha256'),('stderr.log','stderr_sha256'),('initial.json','initial_sha256'),('started.json','started_sha256')]:
  if driver.sha(capture/name)!=process[key]:raise ValueError('Actual captured file differs')
 summary=json_file(capture/'capture-summary.json')
 if (summary['schema']!='focuspilot.unit_native_capture.v1' or summary['promoted'] is not False
     or summary['rows']!=100 or summary['strict_json_objects_and_actual_eos']!=100
     or summary['raw_sha256']!=process['raw_sha256'] or summary['process_sha256']!=driver.sha(capture/'process.json')
     or summary['stderr_sha256']!=process['stderr_sha256'] or summary['lock_sha256']!=driver.sha(native_path)
     or summary['source_commit']!=commit or summary['model_sha256']!=driver.MODEL_SHA or summary['adapter'] is not False):
  raise ValueError('Complete100 native summary binding required')
 load,records=driver.validate_capture((capture/'raw.jsonl').read_text(),native['ids'])
 if len(records)!=100 or summary['load_ms']!=load['load_ms']:raise ValueError('Exact complete100 native rows required')
 return load,records,process


def serial_processes(baseline,candidate):
 def started(process):
  value=datetime.datetime.fromisoformat(process['started_utc'])
  if value.utcoffset()!=datetime.timedelta(0):raise ValueError('Actual UTC process start required')
  seconds=process['seconds']
  if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=240:
   raise ValueError('Bounded process elapsed time required')
  return value
 first=started(baseline);second=started(candidate)
 if baseline['pid']==candidate['pid'] or first+datetime.timedelta(seconds=baseline['seconds'])>second:
  raise ValueError('Baseline must complete before distinct candidate process starts')


def gates(mode,rows,responses,classes,out):
 path=out/(mode+'-input.tsv');encode=lambda s:base64.b64encode(s.encode()).decode()
 with path.open('x') as f:
  for row in rows:f.write(row['id']+'\t'+encode(row['utterance'])+'\t'+encode(responses[row['id']])+'\n')
 stdout=subprocess.check_output([str(JAVA/'java'),'-cp',classes,'dev.focuspilot.prototype.CompatibleCompare',mode,str(path)],text=True,timeout=30)
 with (out/(mode+'-output.tsv')).open('x') as f:f.write(stdout)
 result={}
 for line in stdout.splitlines():
  fields=line.split('\t')
  if len(fields)!=5 or fields[0] in result or fields[2] not in ('true','false'):raise ValueError('Exact Java decision frame required')
  value=canonical(driver.strict_json(base64.b64decode(fields[1],validate=True)))
  accepted=fields[2]=='true';origin=fields[3]
  if accepted!=(value['intent']!='unknown'):raise ValueError('Accepted canonical action differs')
  if mode=='raw_unit':
   if origin!='RAW_UNIT_SCHEMA':raise ValueError('Raw conversion origin required')
  elif origin not in ('FAST_LOCAL_REQUEST','CHECKED_MODEL','UNKNOWN') or (origin=='UNKNOWN')==accepted:
   raise ValueError('Explicit proposal provenance differs')
  if mode!='product_pipeline' and origin=='FAST_LOCAL_REQUEST':raise ValueError('Fast recognition outside product route')
  result[fields[0]]={'proposal':value,'accepted':accepted,'origin':origin,
   'reason':base64.b64decode(fields[4],validate=True).decode()}
 if list(result)!=[r['id'] for r in rows]:raise ValueError('Complete ordered Java decision inventory required')
 return result


def summarize(rows,raw,proposals):
 if list(raw)!=[r['id'] for r in rows] or list(proposals)!=list(raw):raise ValueError('Exact scoring inventory required')
 counts={'rows':len(rows),'supported_rows':0,'unknown_rows':0,'supported_complete':0,
  'supported_false_abstentions':0,'unknown_model_abstentions':0,'unknown_validator_refusals':0,
  'wrong_accepts':0,'raw_intent_correct':0}
 by={i:{'rows':0,'complete_correct':0,'raw_intent_correct':0,'wrong_accepts':0} for i in INTENTS}
 details=[]
 for row in rows:
  ident=row['id'];gold=canonical(row['expected']);decision=proposals[ident];p=canonical(decision['proposal'])
  if type(decision['accepted']) is not bool or decision['accepted']!=(p['intent']!='unknown'):raise ValueError('Canonical acceptance differs')
  supported=gold['intent']!='unknown';exact=p==gold;accepted=decision['accepted'];wrong=accepted and not exact
  intent_correct=raw[ident].get('intent')==gold['intent'];bucket=by[gold['intent']]
  bucket['rows']+=1;bucket['complete_correct']+=int(exact);bucket['raw_intent_correct']+=int(intent_correct);bucket['wrong_accepts']+=int(wrong)
  counts['wrong_accepts']+=int(wrong);counts['raw_intent_correct']+=int(intent_correct)
  if supported:counts['supported_rows']+=1;counts['supported_complete']+=int(exact and accepted);counts['supported_false_abstentions']+=int(not accepted)
  else:counts['unknown_rows']+=1;counts['unknown_model_abstentions']+=int(raw[ident]=={'intent':'unknown'});counts['unknown_validator_refusals']+=int(not accepted)
  details.append({'id':ident,'family':row['family'],'gold':gold,'raw':raw[ident],**decision,
   'supported':supported,'complete_correct':exact,'wrong_accept':wrong})
 counts['per_class']=by
 counts['raw_confusion']={i:{j:sum(r['expected']['intent']==i and raw[r['id']].get('intent')==j for r in rows) for j in INTENTS} for i in INTENTS}
 counts['origin_counts']={origin:sum(d['origin']==origin for d in details) for origin in ('FAST_LOCAL_REQUEST','CHECKED_MODEL','UNKNOWN')}
 return counts,details


def paired(before,after,semantic=False):
 if [r['id'] for r in before]!=[r['id'] for r in after]:raise ValueError('Exact paired inventory required')
 details=[];by={i:{'gain':0,'loss':0} for i in INTENTS if i!='unknown'}
 for a,b in zip(before,after):
  if a['gold']!=b['gold'] or a['supported']!=b['supported']:raise ValueError('Paired gold differs')
  old=a['raw'].get('intent')==a['gold']['intent'] if semantic else a['complete_correct']
  new=b['raw'].get('intent')==b['gold']['intent'] if semantic else b['complete_correct']
  gain=not old and new;loss=old and not new
  if a['supported']:by[a['gold']['intent']]['gain']+=int(gain);by[a['gold']['intent']]['loss']+=int(loss)
  details.append({'id':a['id'],'supported':a['supported'],'gain':gain,'loss':loss})
 result={'supported_gain':sum(r['supported'] and r['gain'] for r in details),
  'supported_loss':sum(r['supported'] and r['loss'] for r in details),'per_supported_class':by}
 if semantic:result['same_intent_all_rows']=sum(a['raw'].get('intent')==b['raw'].get('intent') for a,b in zip(before,after))
 return result,details


def qualify(protocol,history,arms,pipeline_pair):
 q=protocol['qualification'];base=arms['baseline'];checked=arms['checked_model'];pipeline=arms['product_pipeline']
 checks={'historical_preserved':history['prior_preserved']==q['historical_80_preserved'] and history['prior_regressions']==0,
  'historical_wrong_accepts':history['unknown_false_accepts']+history['supported_wrong_route_false_accepts']==q['historical_unknown_and_wrong_route_accepts'] and history['supported_oracle_wrong_accepts']==0,
  'pipeline_net_gain':pipeline_pair['supported_gain']-pipeline_pair['supported_loss']>=q['pipeline_supported_net_gain_minimum'],
  'pipeline_losses':pipeline_pair['supported_loss']<=q['pipeline_supported_losses_maximum'],
  'pipeline_per_class':q['pipeline_per_supported_class_decline_allowed'] or all(pipeline['per_class'][i]['complete_correct']>=base['per_class'][i]['complete_correct'] for i in INTENTS if i!='unknown'),
  'pipeline_start':pipeline['per_class']['start_focus']['complete_correct']>=q['pipeline_start_complete_minimum'],
  'checked_wrong_accepts':checked['wrong_accepts']<=q['checked_model_wrong_accepts_maximum'],
  'pipeline_wrong_accepts':pipeline['wrong_accepts']<=q['pipeline_wrong_accepts_maximum'],
  'checked_unknown_refusals':checked['unknown_validator_refusals']==q['checked_model_unknown_refusals_required'],
  'pipeline_unknown_refusals':pipeline['unknown_validator_refusals']==q['pipeline_unknown_refusals_required'],
  'oracle_coverage':not q['candidate_oracle_at_least_baseline'] or arms['candidate_oracle']['supported_complete']>=arms['baseline_oracle']['supported_complete']}
 return checks


def score(comparison,baseline_capture,candidate_capture,out,commit):
 comparison=private(comparison);freeze_path=TASK/'execution-freeze.json'
 if subprocess.check_output(['git','show',commit+':'+str(freeze_path.relative_to(ROOT))],cwd=ROOT,timeout=30)!=freeze_path.read_bytes():
  raise ValueError('Committed prospective execution freeze differs')
 freeze=json_file(freeze_path);lock=json_file(comparison)
 if driver.sha(comparison)!=freeze['comparison_lock_sha256']:raise ValueError('Prospective comparison lock differs')
 rows,protocol,manifest,files=corpus();history=historical(files)
 if lock['schema']!='focuspilot.compatible_comparison_lock.v1' or lock['rows']!=100 or lock['ids']!=[r['id'] for r in rows] or lock['gold_sha256']!=manifest['jsonl_sha256'] or freeze['gold_sha256']!=lock['gold_sha256']:
  raise ValueError('Exact prospectively reviewed100 cohort required')
 for path,digest in lock['files_sha256'].items():bind(files,path,digest)
 out=private(out)
 if out.exists():raise ValueError('Existing scoring attempt preserved')
 driver.write_new(comparison.parent/'scoring-claim.json',{'source_commit':commit,'comparison_lock_sha256':driver.sha(comparison),'out':str(out)})
 out.mkdir(parents=True,exist_ok=False)
 captures={};raw={};texts={};native_locks={};processes={}
 for arm,capture in [('baseline',baseline_capture),('candidate',candidate_capture)]:
  native_path=Path(lock['locks'][arm]);bind(files,native_path,freeze['native_locks_sha256'][arm])
  native=json_file(native_path);driver.verify_lock(native,commit);native_locks[arm]=native
  if native['ids']!=lock['ids']:raise ValueError('Paired native100 inventory differs')
  load,records,process=validate_process(capture,native_path,native,commit)
  processes[arm]=process
  tokens={r['id']:r['token_count'] for r in [driver.strict_json(line) for line in Path(lock['token_preflight'][arm]['counts_path']).read_text().splitlines()]}
  if len(tokens)!=100 or any(r['metrics']['prompt_tokens']!=tokens[r['id']] for r in records):raise ValueError('Actual prompt counts differ from token-only preflight')
  raw[arm]={r['id']:driver.strict_json(r['text']) for r in records};texts[arm]={r['id']:r['text'] for r in records}
  for value in raw[arm].values():
   if arm=='baseline':
    if set(value)!={'intent'} or value['intent'] not in INTENTS:raise ValueError('Exact original intent JSON required')
   else:raw_canonical(value)
  m=[r['metrics'] for r in records]
  captures[arm]={'rows':100,'canonical_json_actual_eos':100,'model_sha256':driver.MODEL_SHA,
   'pid':process['pid'],'wrapper_seconds':process['seconds'],'load_ms':load['load_ms'],
   'first_native_ms':m[0]['total_ms'],'subsequent_median_native_ms':statistics.median(r['total_ms'] for r in m[1:]),
   'prompt_tokens_min':min(r['prompt_tokens'] for r in m),'prompt_tokens_max':max(r['prompt_tokens'] for r in m),
   'generated_tokens_min':min(r['generated_tokens'] for r in m),'generated_tokens_max':max(r['generated_tokens'] for r in m)}
  for path in Path(capture).iterdir():
   if path.is_file():bind(files,path)
 serial_processes(processes['baseline'],processes['candidate'])
 # Source-bound old and new grammar arms remain separate, even for locally recognized requests.
 oracle_base={r['id']:json.dumps({'intent':r['expected']['intent']},separators=(',',':')) for r in rows}
 oracle_candidate={r['id']:ordered_unit_response(r['expected_raw']) for r in rows}
 converted=gates('raw_unit',rows,texts['candidate'],lock['classes'],out)
 if any(converted[r['id']]['proposal']!=raw_canonical(raw['candidate'][r['id']]) for r in rows):raise ValueError('Java/Python unit conversion differs')
 arms={};details={}
 routes=[('baseline',texts['baseline'],'baseline'),('checked_model',texts['candidate'],'candidate'),
  ('product_pipeline',texts['candidate'],'candidate'),('baseline_oracle',oracle_base,'baseline'),
  ('candidate_oracle',oracle_candidate,'candidate')]
 for mode,responses,arm in routes:
  proposals=gates(mode,rows,responses,lock['classes'],out);summary,detail=summarize(rows,raw[arm],proposals)
  if mode.endswith('oracle'):
   summary['raw_intent_correct']=None;summary['unknown_model_abstentions']=None;summary['raw_confusion']=None
   for entry in summary['per_class'].values():entry['raw_intent_correct']=None
  for entry in detail:
   fast=entry['origin']=='FAST_LOCAL_REQUEST'
   entry['response_source']='ORACLE' if mode.endswith('oracle') else 'FAST_LOCAL_SOURCE' if fast else 'CAPTURED_MODEL'
   entry['raw_source']='CAPTURED_MODEL'
   entry['validation_response']=None if fast else driver.strict_json(responses[entry['id']])
  arms[mode]=summary;details[mode]=detail;driver.write_new(out/(mode+'-details.json'),detail)
 checked_pair,checked_detail=paired(details['baseline'],details['checked_model'])
 pipeline_pair,pipeline_detail=paired(details['baseline'],details['product_pipeline'])
 semantic_pair,semantic_detail=paired(details['baseline'],details['checked_model'],semantic=True)
 for name,value in [('checked_model',checked_detail),('product_pipeline',pipeline_detail),('raw_semantic',semantic_detail)]:
  driver.write_new(out/(name+'-paired.json'),value)
 raw_stats={'candidate_raw_quantity_unit_exact_supported':sum(r['expected']['intent']!='unknown' and raw['candidate'][r['id']]==r['expected_raw'] for r in rows),
  'candidate_raw_canonical_exact_supported':sum(r['expected']['intent']!='unknown' and converted[r['id']]['proposal']==r['expected'] for r in rows),
  'baseline_supported_raw_intent_correct':sum(r['expected']['intent']!='unknown' and raw['baseline'][r['id']]['intent']==r['expected']['intent'] for r in rows),
  'candidate_supported_raw_intent_correct':sum(r['expected']['intent']!='unknown' and raw['candidate'][r['id']]['intent']==r['expected']['intent'] for r in rows)}
 checks=qualify(protocol,history,arms,pipeline_pair)
 checks.update(actual_eos=all(c['canonical_json_actual_eos']==protocol['qualification']['canonical_json_actual_eos_per_arm'] for c in captures.values()),runtime_failures=protocol['qualification']['runtime_failures']==0)
 for arm,native in native_locks.items():driver.verify_lock(native,commit)
 for path,digest in lock['files_sha256'].items():bind(files,path,digest)
 bind(files,comparison);bind(files,freeze_path)
 for path in out.iterdir():
  if path.is_file():bind(files,path)
 result={'schema':'focuspilot.compatible_confirmation_result.v1','source_commit':commit,
  'phase':'prospective_informed_synthetic_confirmation','model_sha256':driver.MODEL_SHA,
  'model_captures':captures,'comparison_lock_sha256':driver.sha(comparison),'execution_freeze_sha256':driver.sha(freeze_path),
  'gold_sha256':manifest['jsonl_sha256'],'rows':100,'supported_rows':50,'unknown_rows':50,
  'arms':arms,'raw_model_statistics':raw_stats,'paired_checked_model':checked_pair,
  'paired_product_pipeline':pipeline_pair,'paired_raw_semantic':semantic_pair,'historical':history,
  'qualification':checks,'decision':'QUALIFIED_COMBINED_PIPELINE_PENDING_ANDROID' if all(checks.values()) else 'REJECT_KEEP_APP',
  'promoted':False,'training_performed':False,'phone_calls':0,'capture_all100_even_if_fast_local':True,
  'files_sha256':{str(Path(path).relative_to(ROOT)) if Path(path).is_relative_to(ROOT) else path:digest for path,digest in files.items()},
  'limitations':protocol['limitations']}
 driver.write_new(out/'result.json',result)
 return result


if __name__=='__main__':
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
 p=sub.add_parser('prepare');p.add_argument('--out',required=True)
 p=sub.add_parser('score')
 for key in ('comparison','baseline-capture','candidate-capture','out','source-commit'):p.add_argument('--'+key,required=True)
 args=parser.parse_args()
 if args.mode=='prepare':print(prepare(args.out))
 else:print(json.dumps(score(args.comparison,args.baseline_capture,args.candidate_capture,args.out,args.source_commit),indent=2))
