"""Named immutable captures on openly seen development data; never blind evidence."""
import argparse,base64,hashlib,json,pathlib,re,statistics,subprocess,time
from generate_corpus import rows

LAB=pathlib.Path(__file__).resolve().parent
ROOT=LAB.parents[1]
JAVA=pathlib.Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
APP=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
INTENTS={'start_focus','pause_focus','alarm','timer','open_app','explain','unknown'}
MODEL_SHA='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
NATIVE_SHA='2e9fa6676c4d68d0b4119cf13d8176d4d6674939c9361c48883c15cfad2cb156'

def sha(path):
    with pathlib.Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--round',required=True);parser.add_argument('--ref');parser.add_argument('--source-dir',type=pathlib.Path,default=APP)
    parser.add_argument('--model',type=pathlib.Path,default=ROOT/'models/qwen/Qwen3.5-0.8B-Q4_0.gguf');args=parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,64}',args.round):raise ValueError('Invalid round name')
    out=LAB/'build'/args.round;out.mkdir(parents=True,exist_ok=True)
    if (out/'model-output.tsv').exists() or (out/'results.json').exists():raise ValueError('Refuse to overwrite a named capture; choose a new round')
    source=out/'source';source.mkdir(exist_ok=True);identities={}
    for name in ['LocalModel.java','ModelCommandGate.java','CommandNumberWords.java']:
        payload=subprocess.check_output(['git','show',args.ref+':'+str((APP/name).relative_to(ROOT))],cwd=ROOT) if args.ref else (args.source_dir/name).read_bytes()
        destination=source/name
        if destination.exists() and destination.read_bytes()!=payload:raise ValueError('Existing source snapshot changed')
        destination.write_bytes(payload);identities[name]=sha(destination)
    lock={'reference_commit':args.ref,'files':identities,'data_kind':'OPENLY_SEEN_DEVELOPMENT','corpus_generator_sha256':sha(LAB/'generate_corpus.py'),'runner_sha256':sha(__file__)}
    save(out/'source-lock.json',lock)
    cases=rows();assert len(cases)==36 and sum(r['expected_kind']!='UNKNOWN' for r in cases)==18
    save(out/'cases.json',cases);requests=out/'requests.tsv';requests.write_text(''.join(r['id']+'\t'+r['utterance']+'\n' for r in cases))
    native=ROOT/'prototype/native/build/host/libfocuspilot_local.dylib'
    assert sha(args.model)==MODEL_SHA and sha(native)==NATIVE_SHA,'Model/native provenance changed; review before a separately named experiment'
    java_out=out/'java';java_out.mkdir(exist_ok=True)
    subprocess.run([str(JAVA/'javac'),'-d',str(java_out),*map(str,source.glob('*.java')),str(LAB/'DevBaseline.java'),str(LAB/'DevGateEval.java')],check=True)
    command=[str(JAVA/'java'),'-Djava.library.path='+str(native.parent),'-cp',str(java_out),'dev.focuspilot.prototype.DevBaseline',str(args.model),str(requests)]
    begin=time.monotonic();timed_out=False;code=None
    with (out/'model-output.tsv').open('w') as output,(out/'model.log').open('w') as log:
        try:code=subprocess.run(command,stdout=output,stderr=log,timeout=180).returncode
        except subprocess.TimeoutExpired:timed_out=True
    metadata={'exit_code':code,'timed_out':timed_out,'budget_seconds':180,'wall_seconds':time.monotonic()-begin,'model_sha256':MODEL_SHA,'native_sha256':NATIVE_SHA,'source_lock':lock,'requests_sha256':sha(requests),'output_sha256':sha(out/'model-output.tsv'),'cpu_only':True,'capture_enabled':False,'context':1024,'threads':4,'actions_executed':0}
    save(out/'capture-metadata.json',metadata)
    if code!=0 or timed_out:raise RuntimeError('Capture failed; evidence retained without scores')
    outputs={};load_ms=None
    for line in (out/'model-output.tsv').read_text().splitlines():
        fields=line.split('\t')
        if fields[0]=='LOAD':load_ms=int(fields[1])/1e6;continue
        assert len(fields)==3 and fields[0] not in outputs
        raw=json.loads(base64.b64decode(fields[2]));valid=False;intent='unknown'
        try:
            answer=json.loads(raw['text']);valid=set(answer)=={'intent'} and answer['intent'] in INTENTS and raw['metrics']['reached_eos'] is True
            if valid:intent=answer['intent']
        except (KeyError,TypeError,ValueError):pass
        assert raw['metrics']['cpu_only'] and raw['metrics']['capture_enabled'] is False
        outputs[fields[0]]={'intent':intent,'schema_eos_valid':valid,'metrics':raw['metrics'],'wall_ms':int(fields[1])/1e6}
    assert set(outputs)=={r['id'] for r in cases}
    gate_input=out/'gate-input.tsv';gate_input.write_text(''.join(r['id']+'\t'+outputs[r['id']]['intent']+'\t'+r['utterance']+'\n' for r in cases))
    result=subprocess.check_output([str(JAVA/'java'),'-cp',str(java_out),'dev.focuspilot.prototype.DevGateEval',str(gate_input)],text=True)
    (out/'gate-output.tsv').write_text(result);proposals={}
    for line in result.splitlines():
        f=line.split('\t');assert len(f)==5 and f[0] not in proposals;proposals[f[0]]=(f[1],int(f[2]),int(f[3]),int(f[4]))
    assert set(proposals)==set(outputs);details=[]
    for row in cases:
        actual=proposals[row['id']];expected=(row['expected_kind'],row['hour'],row['minute'],row['seconds'])
        details.append({**row,'model':outputs[row['id']],'actual':actual,'strict_correct':actual==expected,'accepted':actual[0]!='UNKNOWN','supported':expected[0]!='UNKNOWN'})
    supported=[d for d in details if d['supported']];blocked=[d for d in details if not d['supported']];accepted=[d for d in details if d['accepted']]
    native_ms=[d['model']['metrics']['total_ms'] for d in details]
    summary={'round':args.round,'scope':'OPENLY_SEEN_DEVELOPMENT: no holdout/generalization/promotion claim','rows':36,'supported_rows':18,'unsupported_rows':18,
        'raw_intent_correct':sum(d['model']['intent']==d['expected_intent'] for d in details),'supported_intent_correct':sum(d['model']['intent']==d['expected_intent'] for d in supported),
        'unsupported_model_nonunknown':sum(d['model']['intent']!='unknown' for d in blocked),'schema_eos_valid':sum(d['model']['schema_eos_valid'] for d in details),
        'strict_correct':sum(d['strict_correct'] for d in details),'supported_action_slot_correct':sum(d['strict_correct'] for d in supported),'unsupported_action_false_accepts':sum(d['accepted'] for d in blocked),
        'supported_wrong_accepted':sum(d['accepted'] and not d['strict_correct'] for d in supported),'supported_false_abstentions':sum(not d['accepted'] for d in supported),'accepted':len(accepted),
        'model_load_ms':load_ms,'first_native_ms':native_ms[0],'subsequent_native_ms_median':statistics.median(native_ms[1:]),'wall_ms_median':statistics.median(d['model']['wall_ms'] for d in details),
        'timing_scope':'Sequential host CPU, cached context with fresh KV/recurrent state each request; uncontrolled OS cache/thermals. No phone/NPU claim.','metadata':metadata,'actions_executed':0,'promoted':False}
    assert all(sha(source/name)==digest for name,digest in identities.items())
    save(out/'details.json',details);save(out/'results.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
