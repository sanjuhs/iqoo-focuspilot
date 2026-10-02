"""Two frozen prompt/gate versions, same actual CPU JNI; executes no action."""
import argparse
import base64
import datetime
import hashlib
import json
import re
from pathlib import Path
import shutil
import statistics
import subprocess
import time

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[1]
BUILD=TASK/'build'
JAVA=Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
INTENTS={'start_focus','pause_focus','alarm','timer','open_app','explain','unknown'}
NAMES=['ModelCommandGate.java','CommandNumberWords.java','LocalModel.java']


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def write_json(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')


def verify_freeze():
    frozen=json.loads((TASK/'freeze-manifest.json').read_text())
    for path,key in [(TASK/'generate_data.py','generator_sha256'),(TASK/'protocol.json','protocol_sha256'),
                     (BUILD/'cases.jsonl','cases_sha256'),(BUILD/'requests.tsv','requests_sha256')]:
        assert sha(path)==frozen[key],f'Frozen bytes changed: {path.name}'
    for name in NAMES:assert sha(BUILD/'v09-source'/name)==frozen['v09_source_sha256'][name]
    rows=[json.loads(line) for line in (BUILD/'cases.jsonl').read_text().splitlines()]
    assert len(rows)==100 and len({r['id'] for r in rows})==100
    return frozen,rows


def strict_score(rows,proposals):
    assert set(proposals)=={r['id'] for r in rows}
    details=[]
    for row in rows:
        expected=(row['expected_kind'],row['hour'],row['minute'],row['seconds'])
        actual=tuple(proposals[row['id']]);details.append(dict(id=row['id'],family=row['family'],expected=expected,
          actual=actual,correct=expected==actual,supported=expected[0]!='UNKNOWN',accepted=actual[0]!='UNKNOWN'))
    supported=[r for r in details if r['supported']];unsupported=[r for r in details if not r['supported']]
    accepted=[r for r in details if r['accepted']]
    summary=dict(rows=len(rows),strict_correct=sum(r['correct'] for r in details),supported_rows=len(supported),
      supported_correct=sum(r['correct'] for r in supported),supported_false_abstentions=sum(not r['accepted'] for r in supported),
      supported_wrong_accepted=sum(r['accepted'] and not r['correct'] for r in supported),
      supported_wrong_slots=sum(r['accepted'] and r['actual'][0]==r['expected'][0] and not r['correct'] for r in supported),
      must_abstain_rows=len(unsupported),correct_abstentions=sum(not r['accepted'] for r in unsupported),
      unsupported_false_accepts=sum(r['accepted'] for r in unsupported),accepted=len(accepted),
      wrong_accepted=sum(not r['correct'] for r in accepted),coverage=len(accepted)/len(rows),
      accepted_precision=sum(r['correct'] for r in accepted)/len(accepted) if accepted else None,actions_executed=0)
    summary['per_family']={family:dict(rows=sum(r['family']==family for r in details),
      correct=sum(r['family']==family and r['correct'] for r in details),
      wrong_accepted=sum(r['family']==family and r['accepted'] and not r['correct'] for r in details))
      for family in sorted({r['family'] for r in details})}
    return summary,details


def paired_gate(previous,current):
    a={r['id']:r for r in previous};b={r['id']:r for r in current};assert set(a)==set(b)
    gains=[r for i,r in b.items() if r['supported'] and r['correct'] and not a[i]['correct']]
    losses=[r for i,r in b.items() if r['supported'] and not r['correct'] and a[i]['correct']]
    return dict(supported_gains=len(gains),supported_losses=len(losses),
      gains_per_family={f:sum(r['family']==f for r in gains) for f in sorted({r['family'] for r in gains})},
      losses_per_family={f:sum(r['family']==f for r in losses) for f in sorted({r['family'] for r in losses})})


def semantic_score(rows,outputs):
    assert set(outputs)=={r['id'] for r in rows}
    supported=[r for r in rows if r['expected_kind']!='UNKNOWN'];unsupported=[r for r in rows if r['expected_kind']=='UNKNOWN']
    summary=dict(rows=len(rows),semantic_correct=sum(outputs[r['id']]['intent']==r['semantic_intent'] for r in rows),
      supported_rows=len(supported),supported_correct=sum(outputs[r['id']]['intent']==r['semantic_intent'] for r in supported),
      unknown_rows=len(unsupported),unknown_correct=sum(outputs[r['id']]['intent']=='unknown' for r in unsupported),
      unknown_nonunknown_proposals=sum(outputs[r['id']]['intent']!='unknown' for r in unsupported),
      schema_and_eos_valid=sum(o['valid'] for o in outputs.values()))
    summary['semantic_accuracy']=summary['semantic_correct']/len(rows)
    summary['per_class']={label:dict(rows=sum(r['semantic_intent']==label for r in rows),
      correct=sum(r['semantic_intent']==label and outputs[r['id']]['intent']==label for r in rows))
      for label in sorted(INTENTS)}
    return summary


def prompt_inventory(rows,version,source_hashes):
    native=ROOT/'prototype/command-eval/build/native/libfocuspilot_local.dylib'
    java_out=BUILD/(version+'-inventory-java');java_out.mkdir(exist_ok=True)
    source=BUILD/(version+'-source/LocalModel.java')
    assert sha(source)==source_hashes['LocalModel.java']
    subprocess.run([str(JAVA/'javac'),'-d',str(java_out),str(source),str(TASK/'PromptInventory.java')],check=True)
    marker='UNIQUE_V10_INVENTORY_REQUEST_314159'
    raw=subprocess.check_output([str(JAVA/'java'),'-Djava.library.path='+str(native.parent),'-cp',str(java_out),
      'dev.focuspilot.prototype.PromptInventory',marker],text=True,timeout=30)
    prompt=base64.b64decode(raw.strip()).decode('utf-8')
    user_turns=re.findall(r'<\|im_start\|>user\n(.*?)<\|im_end\|>',prompt,re.S)
    assert user_turns.count(marker)==1
    examples=[text for text in user_turns if text!=marker]
    method='Actual fixed user chat turns from rendered immutable adapter'
    if version=='v09':
        system=re.search(r'<\|im_start\|>system\n(.*?)<\|im_end\|>',prompt,re.S).group(1)
        prose=system.split('Examples: ',1)[1]
        examples=[text.strip() for text in re.findall(r'([^=]+?)=(?:start_focus|pause_focus|alarm|timer|open_app|explain|unknown)\.(?:\s|$)',prose)]
        assert len(examples)==8
        method='Actual rendered system prose, fixed utterance=intent examples; terminal separator period is not utterance data'
    else:assert len(examples)==13
    exact=[r['id'] for r in rows if r['utterance'] in examples]
    normalized=lambda text:' '.join(text.lower().split())
    normalized_examples={normalized(text) for text in examples}
    normalized_matches=[r['id'] for r in rows if normalized(r['utterance']) in normalized_examples]
    summary=dict(fixed_example_count=len(examples),exact_request_overlap_rows=len(exact),
      case_whitespace_normalized_overlap_rows=len(normalized_matches),heldout_rows_unchanged=len(rows),
      prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),adapter_sha256=sha(source),
      inventory_source_sha256=sha(TASK/'PromptInventory.java'),method=method,generated_tokens=0)
    write_json(BUILD/(version+'-prompt-inventory.json'),dict(summary=summary,examples=examples,
      exact_match_ids=exact,case_whitespace_normalized_match_ids=normalized_matches))
    return summary


def capture_model(frozen,model,version,source_hashes):
    native=ROOT/'prototype/command-eval/build/native/libfocuspilot_local.dylib'
    protocol=json.loads((TASK/'protocol.json').read_text())
    assert sha(model)==protocol['model_sha256'] and sha(native)==protocol['native_sha256']
    source=BUILD/(version+'-source');java_out=BUILD/(version+'-baseline-java');java_out.mkdir(exist_ok=True)
    subprocess.run([str(JAVA/'javac'),'-d',str(java_out),str(source/'LocalModel.java'),str(TASK/'CommandBaseline.java')],check=True)
    output=BUILD/(version+'-model-output.tsv');log=BUILD/(version+'-model.log')
    if output.exists():raise ValueError('Refuse to overwrite model capture; --score-only reviews completed captures')
    started=time.monotonic();start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    command=[str(JAVA/'java'),'-Djava.library.path='+str(native.parent),'-cp',str(java_out),
      'dev.focuspilot.prototype.CommandBaseline',str(model),str(BUILD/'requests.tsv')]
    print(json.dumps(dict(phase='native_capture_started',version=version,utc=start_utc)),flush=True)
    with output.open('w') as out,log.open('w') as err:
        try:job=subprocess.run(command,stdout=out,stderr=err,timeout=300);exit_code=job.returncode
        except subprocess.TimeoutExpired:
            write_json(BUILD/(version+'-model-metadata.json'),dict(exit_code=None,timed_out=True,output_sha256=sha(output)))
            raise
    metadata=dict(exit_code=exit_code,started_utc=start_utc,wall_seconds=time.monotonic()-started,
      model_sha256=sha(model),native_sha256=sha(native),adapter_sha256=source_hashes['LocalModel.java'],
      requests_sha256=frozen['requests_sha256'],output_sha256=sha(output),baseline_source_sha256=sha(TASK/'CommandBaseline.java'),
      cpu_only=True,context=1024,threads=4,capture_enabled=False,actions_executed=0)
    write_json(BUILD/(version+'-model-metadata.json'),metadata)
    print(json.dumps(dict(phase='native_capture_terminal',version=version,exit_code=exit_code,wall_seconds=metadata['wall_seconds'])),flush=True)
    job.check_returncode()


def read_model(rows,frozen,version,source_hashes):
    metadata=json.loads((BUILD/(version+'-model-metadata.json')).read_text())
    assert metadata['exit_code']==0 and metadata['output_sha256']==sha(BUILD/(version+'-model-output.tsv'))
    assert metadata['requests_sha256']==frozen['requests_sha256'] and metadata['adapter_sha256']==source_hashes['LocalModel.java']
    outputs={};load_ms=None
    for line in (BUILD/(version+'-model-output.tsv')).read_text().splitlines():
        f=line.split('\t')
        if f[0]=='LOAD':load_ms=int(f[1])/1e6;continue
        assert len(f)==3 and f[0] not in outputs
        raw=json.loads(base64.b64decode(f[2]));intent='unknown';valid=False
        try:
            response=json.loads(raw['text']);valid=set(response)=={'intent'} and response['intent'] in INTENTS and raw['metrics']['reached_eos'] is True
            if valid:intent=response['intent']
        except (KeyError,ValueError,TypeError):pass
        outputs[f[0]]=dict(intent=intent,valid=valid,wall_ms=int(f[1])/1e6,metrics=raw['metrics'])
    summary=semantic_score(rows,outputs);timings=[outputs[r['id']]['metrics']['total_ms'] for r in rows]
    summary.update(prompt_tokens_median=statistics.median(o['metrics']['prompt_tokens'] for o in outputs.values()),
      prompt_tokens_min=min(o['metrics']['prompt_tokens'] for o in outputs.values()),
      prompt_tokens_max=max(o['metrics']['prompt_tokens'] for o in outputs.values()),load_ms=load_ms,first_native_ms=timings[0],subsequent_native_ms_median=statistics.median(timings[1:]),
      wall_ms_median=statistics.median(r['wall_ms'] for r in outputs.values()),metadata=metadata,
      timing_limit='Host CPU only. Each version has its own model load, fixed baseline-then-candidate order. First request is not OS-cache-cold; thermals/power uncontrolled. Context reused with state cleared per case. No phone/NPU claim.')
    return outputs,summary


def evaluate_gate(rows,intents,version,route):
    source=BUILD/(version+'-source');java_out=BUILD/(version+'-gate-java');java_out.mkdir(exist_ok=True)
    subprocess.run([str(JAVA/'javac'),'-d',str(java_out),str(source/'ModelCommandGate.java'),
      str(source/'CommandNumberWords.java'),str(TASK/'CommandGateEval.java')],check=True)
    name=version+'-'+route;input_path=BUILD/(name+'-input.tsv')
    input_path.write_text(''.join(f"{r['id']}\t{intents[r['id']]}\t{r['utterance']}\n" for r in rows))
    raw=subprocess.check_output([str(JAVA/'java'),'-cp',str(java_out),'dev.focuspilot.prototype.CommandGateEval',str(input_path)],text=True)
    (BUILD/(name+'-output.tsv')).write_text(raw);proposals={}
    for line in raw.splitlines():
        f=line.split('\t');assert len(f)==6 and f[0] not in proposals
        proposals[f[0]]=(f[1],int(f[2]),int(f[3]),int(f[4]))
    summary,details=strict_score(rows,proposals);write_json(BUILD/(name+'-results.json'),details)
    summary['raw_result_sha256']=sha(BUILD/(name+'-results.json'))
    return summary,details


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-gate-sha',required=True);parser.add_argument('--candidate-numbers-sha',required=True)
    parser.add_argument('--candidate-adapter-sha',required=True);parser.add_argument('--score-only',action='store_true')
    parser.add_argument('--model',default=str(ROOT/'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'));args=parser.parse_args()
    frozen,rows=verify_freeze();source=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
    candidate=BUILD/'v10-source';candidate.mkdir(exist_ok=True)
    hashes=dict(zip(NAMES,[args.candidate_gate_sha,args.candidate_numbers_sha,args.candidate_adapter_sha]))
    for name,expected in hashes.items():
        if args.score_only:assert sha(candidate/name)==expected
        else:
            assert sha(source/name)==expected,'Candidate source must be locked'
            if (candidate/name).exists():assert sha(candidate/name)==expected
            else:shutil.copyfile(source/name,candidate/name)
    lock_path=BUILD/'candidate-lock.json'
    lock=dict(locked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=hashes,
      dataset_sha256=frozen['cases_sha256'],runner_sha256=sha(__file__),locked_before_any_capture=True)
    if lock_path.exists():assert json.loads(lock_path.read_text())['source_sha256']==hashes
    else:write_json(lock_path,lock)
    inventories={version:prompt_inventory(rows,version,source_hashes) for version,source_hashes in [('v09',frozen['v09_source_sha256']),('v10',hashes)]}
    print(json.dumps(dict(phase='prompt_inventory_complete',inventory=inventories)),flush=True)
    if not args.score_only:
        capture_model(frozen,Path(args.model),'v09',frozen['v09_source_sha256'])
        capture_model(frozen,Path(args.model),'v10',hashes)
    outputs={};models={};gates={'generated':{},'oracle':{}};details={}
    for version,source_hashes in [('v09',frozen['v09_source_sha256']),('v10',hashes)]:
        outputs[version],models[version]=read_model(rows,frozen,version,source_hashes)
        for route,intents in [('generated',{k:v['intent'] for k,v in outputs[version].items()}),
                             ('oracle',{r['id']:r['oracle_intent'] for r in rows})]:
            gates[route][version],details[(route,version)]=evaluate_gate(rows,intents,version,route)
    paired={route:paired_gate(details[(route,'v09')],details[(route,'v10')]) for route in ['generated','oracle']}
    paired['semantic']=dict(gained=sum(outputs['v10'][r['id']]['intent']==r['semantic_intent'] and outputs['v09'][r['id']]['intent']!=r['semantic_intent'] for r in rows),
      lost=sum(outputs['v10'][r['id']]['intent']!=r['semantic_intent'] and outputs['v09'][r['id']]['intent']==r['semantic_intent'] for r in rows))
    result=dict(schema=1,scope='Blind frozen pre-event synthetic host CPU evidence; no actions or training. Generated end-to-end comparison changes prompt+gate together; oracle comparison isolates validators.',
      frozen_manifest=frozen,candidate_lock=json.loads(lock_path.read_text()),prompt_inventory=inventories,models=models,gates=gates,paired=paired,
      source_sha256=sha(__file__),actions_executed=0,candidate_promoted=False)
    write_json(TASK/'results.json',result)
    print(json.dumps(dict(models={v:{k:m[k] for k in ['semantic_correct','supported_correct','unknown_correct','schema_and_eos_valid']} for v,m in models.items()},
      gates={r:{v:{k:m[k] for k in ['strict_correct','supported_correct','wrong_accepted','unsupported_false_accepts','supported_wrong_slots']} for v,m in d.items()} for r,d in gates.items()},paired=paired),indent=2))


if __name__=='__main__':main()
