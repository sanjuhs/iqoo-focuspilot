"""Score frozen native observations against independent labels and selected Java slots."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import subprocess
import run_capture as runner


def read_rows(path,lock):
 if str(Path(path).resolve()) not in lock['files_sha256']: raise ValueError('Gold corpus must be prospectively pinned in native lock')
 if runner.sha(path)!=lock['files_sha256'][str(Path(path).resolve())]: raise ValueError('Frozen gold corpus changed')
 rows=[runner.strict_json(line) for line in Path(path).read_text().splitlines()]
 requests=runner.requests(lock['requests'])
 if [(r['id'],r['utterance']) for r in rows]!=requests: raise ValueError('Gold/request ordered inventory differs')
 for row in rows:
  if row['intent'] not in runner.INTENTS or row['oracle_intent'] not in runner.INTENTS: raise ValueError('Invalid manual intent')
  for key in ('hour','minute','seconds'):
   if type(row[key]) is not int or row[key]<0: raise ValueError('Invalid manual slot')
  if (row['intent']=='unknown')!=(row['expected_kind']=='UNKNOWN'): raise ValueError('Manual unknown labels disagree')
 return rows


def summarize(rows,predictions,proposals):
 if list(predictions)!=[r['id'] for r in rows] or list(proposals)!=list(predictions): raise ValueError('Exact scored inventory required')
 supported=[r for r in rows if r['expected_kind']!='UNKNOWN']
 details=[]
 for r in rows:
  p=proposals[r['id']]
  correct=(p['kind'],p['hour'],p['minute'],p['seconds'])==(r['expected_kind'],r['hour'],r['minute'],r['seconds'])
  details.append({'id':r['id'],'intent':r['intent'],'family':r['family'],'hard_tags':r['hard_tags'],
   'supported':r['expected_kind']!='UNKNOWN','semantic_correct':predictions[r['id']]==r['intent'],
   'complete_proposal_correct':correct,'accepted':p['kind']!='UNKNOWN','wrong_accept':p['kind']!='UNKNOWN' and not correct,
   'prediction':predictions[r['id']],'kind':p['kind'],'hour':p['hour'],'minute':p['minute'],'seconds':p['seconds']})
 labels=sorted(runner.INTENTS)
 counts={'rows':len(rows),'supported_rows':len(supported),'unknown_rows':len(rows)-len(supported),
 'semantic_correct':sum(d['semantic_correct'] for d in details),
 'supported_semantic_correct':sum(d['supported'] and d['semantic_correct'] for d in details),
 'unknown_model_abstentions':sum(not d['supported'] and d['prediction']=='unknown' for d in details),
 'supported_complete_proposals':sum(d['supported'] and d['complete_proposal_correct'] for d in details),
 'supported_false_abstentions':sum(d['supported'] and not d['accepted'] for d in details),
 'unknown_refused_by_gate':sum(not d['supported'] and not d['accepted'] for d in details),
 'wrong_accepts':sum(d['wrong_accept'] for d in details),
 'per_class':{label:{'rows':sum(d['intent']==label for d in details),
 'semantic_correct':sum(d['intent']==label and d['semantic_correct'] for d in details),
 'complete_proposal_correct':sum(d['intent']==label and d['complete_proposal_correct'] for d in details)} for label in labels},
 'confusion':{label:{pred:sum(d['intent']==label and d['prediction']==pred for d in details) for pred in labels} for label in labels}}
 return counts,details


def score(lock_path,capture_dir,data_path,out,source_commit):
 lock_path=runner.private_path(lock_path)
 lock=runner.strict_json(Path(lock_path).read_text());runner.verify_lock(lock,source_commit)
 rows=read_rows(data_path,lock);capture_dir=Path(capture_dir)
 process=runner.strict_json((capture_dir/'process.json').read_text())
 if process['exit_code']!=0 or process['timed_out'] or process.get('postflight_error_type') or process['lock_sha256']!=runner.sha(lock_path) or process['raw_sha256']!=runner.sha(capture_dir/'raw.jsonl'): raise ValueError('Successful immutable complete capture required')
 load,records=runner.validate_capture((capture_dir/'raw.jsonl').read_text(),lock['ids'],bool(process['adapter_sha256']))
 predictions={r['id']:runner.strict_json(r['text'])['intent'] for r in records}
 out=runner.private_path(out);out.mkdir(parents=True,exist_ok=False)
 summary={'schema':'focuspilot.balanced_native_score.v1','source_commit':source_commit,'lock_sha256':runner.sha(lock_path),
 'capture_process_sha256':runner.sha(capture_dir/'process.json'),'gold_sha256':runner.sha(data_path),'load_ms':load['load_ms'],
 'semantic_metric_origin':'Raw native predictions in both generated and oracle routes',
 'scope':'Fresh-context host CPU research; synthetic heldout; no adapter promotion, phone/NPU or general safety claim','promoted':False}
 for route in ('generated','oracle'):
  input_path=out/(route+'-gate.tsv')
  with input_path.open('x') as f:
   for row in rows: f.write(row['id']+'\t'+(predictions[row['id']] if route=='generated' else row['oracle_intent'])+'\t'+row['utterance']+'\n')
  output_path=out/(route+'-gate-output.tsv')
  with output_path.open('x') as f:
   subprocess.run([str(runner.JAVA/'java'),'-cp',lock['classes'],'dev.focuspilot.prototype.CommandGateEval',str(input_path)],stdout=f,check=True,timeout=30)
  proposals={}
  for line in output_path.read_text().splitlines():
   fields=line.split('\t')
   if len(fields)!=6 or fields[0] in proposals: raise ValueError('Invalid gate record')
   proposals[fields[0]]={'kind':fields[1],'hour':int(fields[2]),'minute':int(fields[3]),'seconds':int(fields[4])}
  scored,details=summarize(rows,predictions,proposals)
  runner.write_new(out/(route+'-details.json'),details);summary[route]=scored
 def timing(selected,key):
  values=[r['metrics'][key] for r in selected]
  return {'sample_count':len(values),'median_ms':statistics.median(values) if values else None,'min_ms':min(values) if values else None,'max_ms':max(values) if values else None}
 summary['timings']={key:{'first_ms':records[0]['metrics'][key],'subsequent':timing(records[1:],key)} for key in ('context_setup_ms','prefill_ms','decode_ms','total_ms')}
 runner.verify_lock(lock,source_commit)
 runner.write_new(out/'summary.json',summary);return summary


def paired(baseline,candidate):
 if [r['id'] for r in baseline]!=[r['id'] for r in candidate]: raise ValueError('Paired ordered inventory differs')
 transitions=[]
 for a,b in zip(baseline,candidate):
  if any(a[k]!=b[k] for k in ('id','intent','family','hard_tags','supported')): raise ValueError('Paired manual metadata differs')
  transitions.append({'id':a['id'],'intent':a['intent'],'supported':a['supported'],'hard_tags':a['hard_tags'],
   'semantic_gain':b['semantic_correct'] and not a['semantic_correct'],'semantic_loss':a['semantic_correct'] and not b['semantic_correct'],
   'gate_gain':b['complete_proposal_correct'] and not a['complete_proposal_correct'],'gate_loss':a['complete_proposal_correct'] and not b['complete_proposal_correct'],
   'baseline_wrong_accept':a['wrong_accept'],'candidate_wrong_accept':b['wrong_accept']})
 keys=('semantic_gain','semantic_loss','gate_gain','gate_loss','baseline_wrong_accept','candidate_wrong_accept')
 counts=lambda values:{key:sum(r[key] for r in values) for key in keys}
 return {'all_rows':counts(transitions),'supported_rows':counts([r for r in transitions if r['supported']]),
 'per_intent':{label:counts([r for r in transitions if r['intent']==label]) for label in sorted(runner.INTENTS)},
 'hard_supported':{tag:counts([r for r in transitions if r['supported'] and tag in r['hard_tags']]) for tag in sorted({tag for r in transitions for tag in r['hard_tags']})}},transitions


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--lock',required=True);p.add_argument('--capture-dir',required=True);p.add_argument('--data',required=True);p.add_argument('--out',required=True);p.add_argument('--source-commit',required=True);a=p.parse_args()
 print(json.dumps(score(a.lock,a.capture_dir,a.data,a.out,a.source_commit),indent=2))
