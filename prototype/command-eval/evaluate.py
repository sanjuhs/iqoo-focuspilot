"""Score frozen native proposals through the exact current app Java gate."""
import base64,collections,hashlib,json,pathlib,statistics,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];TASK=pathlib.Path(__file__).resolve().parent;BUILD=TASK/'build'
INTENTS={'start_focus','pause_focus','alarm','timer','open_app','explain','unknown'}
def decode(raw):
 try:
  outer=json.loads(raw);response=json.loads(outer['text']);valid=(set(response)=={'intent'} and response['intent'] in INTENTS and outer['metrics']['reached_eos'] is True)
  return (response['intent'] if valid else 'unknown'),valid,outer
 except (ValueError,KeyError,TypeError):return 'unknown',False,{}
def strict_match(case,kind,hour,minute,seconds):
 return (kind,int(hour),int(minute),int(seconds))==(case['expected_action'],case['hour'],case['minute'],case['seconds'])
def digest(p):return hashlib.file_digest(pathlib.Path(p).open('rb'),'sha256').hexdigest()
def main():
 manifest=json.loads((TASK/'data-manifest.json').read_text());raw=(BUILD/'cases.jsonl').read_bytes();assert hashlib.sha256(raw).hexdigest()==manifest['cases_sha256']
 cases=list(map(json.loads,raw.splitlines()));native={};load=None
 for line in (BUILD/'native-output.tsv').read_text().splitlines():
  f=line.split('\t');
  if f[0]=='LOAD':load=int(f[1])/1e6;continue
  intent,valid,result=decode(base64.b64decode(f[2]).decode());native[f[0]]={'intent':intent,'valid':valid,'result':result,'wall_ms':int(f[1])/1e6}
 assert len(native)==len(cases)+1
 source=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype/ModelCommandGate.java'
 frozen=BUILD/'source/ModelCommandGate.java';frozen.write_bytes(source.read_bytes());gate_sha=digest(frozen)
 java='/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin'
 subprocess.run([java+'/javac','-d',str(BUILD/'java'),str(frozen),str(TASK/'GateEval.java')],check=True)
 inp=''.join(c['id']+'\t'+native[c['id']]['intent']+'\t'+base64.b64encode(c['utterance'].encode()).decode()+'\n' for c in cases);(BUILD/'gate-input.tsv').write_text(inp)
 output=subprocess.check_output([java+'/java','-cp',str(BUILD/'java'),'dev.focuspilot.prototype.GateEval',str(BUILD/'gate-input.tsv')],text=True);(BUILD/'gate-output.tsv').write_text(output)
 gates={f[0]:f for f in (line.split('\t') for line in output.splitlines())};records=[]
 for c in cases:
  n=native[c['id']];g=gates[c['id']]
  records.append({**c,'raw_intent':n['intent'],'raw_valid':n['valid'],'raw_correct':n['valid'] and n['intent']==c['expected_intent'],'gate_action':g[1],'gate_hour':int(g[2]),'gate_minute':int(g[3]),'gate_seconds':int(g[4]),'gate_preview':base64.b64decode(g[5]).decode(),'strict_action_correct':strict_match(c,*g[1:5]),'unsafe_or_wrong_executable':g[1]!='UNKNOWN' and not strict_match(c,*g[1:5]),'native_metrics':n['result'].get('metrics',{}),'host_wall_ms':n['wall_ms']})
 (BUILD/'case-results.json').write_text(json.dumps(records,indent=2)+'\n')
 allowed=[r for r in records if r['expected_action']!='UNKNOWN'];blocked=[r for r in records if r['expected_action']=='UNKNOWN'];unknown=[r for r in records if r['expected_intent']=='unknown'];abstained=[r for r in records if r['gate_action']=='UNKNOWN'];accepted=[r for r in records if r['gate_action']!='UNKNOWN']
 warm=records[1:];quant=lambda xs:{'n':len(xs),'min':min(xs),'median':statistics.median(xs),'max':max(xs)}
 summary={'schema':1,'scope':'New frozen58-case synthetic host JNI/native CPU evaluation; no phone actions, no new model/training/prompt tuning.','rows':len(records),'families':len({r['family'] for r in records}),'cases_sha256':manifest['cases_sha256'],'raw_model':{'schema_and_eos_valid':sum(r['raw_valid'] for r in records),'intent_correct':sum(r['raw_correct'] for r in records),'accuracy':sum(r['raw_correct'] for r in records)/len(records),'unsupported_intent_cases':len(unknown),'unsupported_correct_abstention':sum(r['raw_valid'] and r['raw_intent']=='unknown' for r in unknown),'unknown_predictions':sum(r['raw_intent']=='unknown' for r in records)},'gate':{'strict_action_and_slot_correct':sum(r['strict_action_correct'] for r in records),'strict_accuracy':sum(r['strict_action_correct'] for r in records)/len(records),'supported_strict_cases':len(allowed),'supported_correct_actions':sum(r['strict_action_correct'] for r in allowed),'supported_false_abstentions':sum(r['gate_action']=='UNKNOWN' for r in allowed),'must_abstain_cases':len(blocked),'correct_abstentions':sum(r['gate_action']=='UNKNOWN' for r in blocked),'abstentions':len(abstained),'abstention_precision':sum(r['expected_action']=='UNKNOWN' for r in abstained)/len(abstained) if abstained else None,'executable_proposals':len(accepted),'proposal_coverage':len(accepted)/len(records),'executable_proposal_correct':sum(r['strict_action_correct'] for r in accepted),'executable_precision':sum(r['strict_action_correct'] for r in accepted)/len(accepted) if accepted else None,'wrong_executable_proposals':sum(r['unsafe_or_wrong_executable'] for r in records)},'timing':{'model_load_ms':load,'first_case_process_cold':records[0]['native_metrics'],'first_case_wall_ms':records[0]['host_wall_ms'],'subsequent_wall_ms':quant([r['host_wall_ms'] for r in warm]),'subsequent_native_total_ms':quant([r['native_metrics']['total_ms'] for r in warm]),'subsequent_prefill_ms':quant([r['native_metrics']['prefill_ms'] for r in warm]),'subsequent_decode_ms':quant([r['native_metrics']['decode_ms'] for r in warm]),'first_case_repeat_after_all':native[cases[0]['id']+'-repeat'],'definition':'Process-first model/context inference vs subsequent requests sharing weights; recurrent/KV state cleared each command. OS page cache not flushed, thermals/power not controlled. Host only.'},'per_family':{f:{'n':sum(r['family']==f for r in records),'raw_correct':sum(r['family']==f and r['raw_correct'] for r in records),'strict_correct':sum(r['family']==f and r['strict_action_correct'] for r in records),'wrong_executable':sum(r['family']==f and r['unsafe_or_wrong_executable'] for r in records)} for f in sorted({r['family'] for r in records})},'unsafe_or_wrong_examples':[{'id':r['id'],'family':r['family'],'expected_action':r['expected_action'],'raw_intent':r['raw_intent'],'gate_action':r['gate_action']} for r in records if r['unsafe_or_wrong_executable']],'model_sha256':digest(ROOT/'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'),'gate_source_sha256':gate_sha,'gate_source_unchanged_after_eval':digest(source)==gate_sha,'localmodel_source_sha256':digest(ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java'),'native_wrapper_source_sha256':{p.name:digest(p) for p in sorted((BUILD/'source').glob('*')) if p.name!='ModelCommandGate.java'},'native_library_sha256':digest(BUILD/'native/libfocuspilot_local.dylib'),'llama_commit':'57fe1f07c3b6a1de3f4fff19098e2056a85275b7','promoted':False,'actual_actions_executed':0}
 assert summary['model_sha256']=='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
 assert summary['gate_source_unchanged_after_eval']
 (TASK/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ['rows','families','raw_model','gate','unsafe_or_wrong_examples']},indent=2))
if __name__=='__main__':main()
