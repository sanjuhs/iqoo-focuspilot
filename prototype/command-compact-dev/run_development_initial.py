"""Actual CPU JNI on already seen 36-case development set; no actions/promotion."""
import argparse, base64, hashlib, importlib.util, json, pathlib, re, statistics, subprocess, time

LAB=pathlib.Path(__file__).resolve().parent
ROOT=LAB.parents[1]
JAVA=pathlib.Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
APP=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
NATIVE=ROOT/'prototype/native/build/host/libfocuspilot_local.dylib'
MODEL=ROOT/'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
MODEL_SHA='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
NATIVE_SHA='2e9fa6676c4d68d0b4119cf13d8176d4d6674939c9361c48883c15cfad2cb156'
MAP={'0':'unknown','1':'start_focus','2':'pause_focus','3':'alarm','4':'timer','5':'open_app','6':'explain'}
PIN={'LocalModel.java':'2f6784c524ca9304fd714b86c04f5b1c3c5deb7e5ff562fbc34ae32c39e51e5d',
     'ModelCommandGate.java':'cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4',
     'CommandNumberWords.java':'e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d'}

def sha(path):
    with pathlib.Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def budget():
    total=sum(p.stat().st_size for p in LAB.rglob('*') if p.is_file())
    if total>10_000_000:raise RuntimeError('Development directory exceeds reserved 10 MB')
    return total
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--round',required=True);parser.add_argument('--candidate',choices=['compact1','compact2'],required=True)
    parser.add_argument('--baseline',action='store_true');args=parser.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,48}',args.round):raise ValueError('Invalid named round')
    out=LAB/'build'/args.round
    if out.exists():raise ValueError('Refuse to overwrite any existing named round')
    assert budget()<9_000_000 and sha(MODEL)==MODEL_SHA and sha(NATIVE)==NATIVE_SHA
    assert all(sha(APP/name)==digest for name,digest in PIN.items())
    generator=ROOT/'prototype/command-v10-dev/generate_corpus.py'
    spec=importlib.util.spec_from_file_location('seen_corpus',generator);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=module.rows();assert len(rows)==36 and sum(r['expected_kind']!='UNKNOWN' for r in rows)==18
    out.mkdir(parents=True);source=out/'source';source.mkdir();classes=out/'java';classes.mkdir()
    identities={}
    for name in PIN:
        payload=(APP/name).read_bytes();(source/name).write_bytes(payload);identities[name]=sha(source/name)
    candidate=LAB/'candidates'/args.candidate/'CompactIntentCandidate.java'
    for original in [candidate,LAB/'CompactRunner.java',LAB/'PromptInventory.java',ROOT/'prototype/command-v10-dev/DevGateEval.java']:
        (source/original.name).write_bytes(original.read_bytes());identities[original.name]=sha(source/original.name)
    requests=out/'requests.tsv';requests.write_text(''.join(r['id']+'\t'+r['utterance']+'\n' for r in rows))
    save(out/'cases.json',rows)
    metadata={'scope':'OPENLY_SEEN_DEVELOPMENT','candidate':args.candidate,'baseline':args.baseline,'model_sha256':MODEL_SHA,'native_sha256':NATIVE_SHA,
      'source_sha256':identities,'runner_sha256':sha(__file__),'corpus_generator_sha256':sha(generator),'requests_sha256':sha(requests),
      'context':1024,'threads':4,'cpu_only':True,'capture_enabled':False,'actions_executed':0,'promoted':False,'timeout_seconds':180}
    save(out/'capture-metadata.json',metadata)
    subprocess.run([str(JAVA/'javac'),'-d',str(classes),*map(str,source.glob('*.java'))],check=True,timeout=30)
    mode='baseline' if args.baseline else 'compact'
    command=[str(JAVA/'java'),'-Djava.library.path='+str(NATIVE.parent),'-cp',str(classes),'dev.focuspilot.prototype.CompactRunner',str(MODEL),str(requests),mode]
    begin=time.monotonic();code=None;timeout=False
    with (out/'model-output.tsv').open('w') as output,(out/'model.log').open('w') as log:
        try:code=subprocess.run(command,stdout=output,stderr=log,timeout=180).returncode
        except subprocess.TimeoutExpired:timeout=True
    metadata.update(exit_code=code,timed_out=timeout,wall_seconds=time.monotonic()-begin,output_sha256=sha(out/'model-output.tsv'))
    save(out/'capture-metadata.json',metadata)
    if code!=0 or timeout:raise RuntimeError('Capture failed; immutable partial evidence retained')
    outputs={};load_ms=None
    for line in (out/'model-output.tsv').read_text().splitlines():
        f=line.split('\t')
        if f[0]=='LOAD':load_ms=int(f[1])/1e6;continue
        assert len(f)==3 and f[0] not in outputs
        raw=json.loads(base64.b64decode(f[2]));m=raw['metrics'];text=raw['text'];intent='unknown';valid=False
        assert m['cpu_only'] and m['capture_enabled'] is False
        if args.baseline:
            try:
                answer=json.loads(text);valid=set(answer)=={'intent'} and answer['intent'] in MAP.values() and m['reached_eos'] is True
                if valid:intent=answer['intent']
            except (KeyError,ValueError,TypeError):pass
        else:
            valid=text in MAP and m['reached_eos'] is True
            if valid:intent=MAP[text]
        outputs[f[0]]={'intent':intent,'format_eos_valid':valid,'metrics':m,'wall_ms':int(f[1])/1e6}
    assert set(outputs)=={r['id'] for r in rows}
    gate_input=out/'gate-input.tsv';gate_input.write_text(''.join(r['id']+'\t'+outputs[r['id']]['intent']+'\t'+r['utterance']+'\n' for r in rows))
    gate=subprocess.check_output([str(JAVA/'java'),'-cp',str(classes),'dev.focuspilot.prototype.DevGateEval',str(gate_input)],text=True,timeout=30)
    (out/'gate-output.tsv').write_text(gate);proposals={}
    for line in gate.splitlines():
        f=line.split('\t');assert len(f)==5 and f[0] not in proposals;proposals[f[0]]=(f[1],int(f[2]),int(f[3]),int(f[4]))
    assert set(proposals)==set(outputs)
    details=[]
    for r in rows:
        actual=proposals[r['id']];expected=(r['expected_kind'],r['hour'],r['minute'],r['seconds']);model=outputs[r['id']]
        details.append(dict(id=r['id'],family=r['family'],expected_intent=r['expected_intent'],model_intent=model['intent'],expected=list(expected),actual=list(actual),
          supported=expected[0]!='UNKNOWN',correct=expected==actual,raw_correct=model['intent']==r['expected_intent'],valid=model['format_eos_valid']))
    supported=[d for d in details if d['supported']];unknown=[d for d in details if not d['supported']]
    native_ms=[outputs[r['id']]['metrics']['total_ms'] for r in rows]
    summary={'round':args.round,'scope':'OPENLY_SEEN_DEVELOPMENT; no holdout, deployment or promotion claim','metadata':metadata,'rows':36,'supported_rows':18,'unsupported_rows':18,
      'raw_correct':sum(d['raw_correct'] for d in details),'supported_raw_correct':sum(d['raw_correct'] for d in supported),
      'unknown_raw_correct':sum(d['model_intent']=='unknown' for d in unknown),'unsupported_model_nonunknown':sum(d['model_intent']!='unknown' for d in unknown),
      'format_eos_valid':sum(d['valid'] for d in details),'supported_action_slot_correct':sum(d['correct'] for d in supported),
      'supported_false_abstentions':sum(d['actual'][0]=='UNKNOWN' for d in supported),'supported_wrong_accepted':sum(d['actual'][0]!='UNKNOWN' and not d['correct'] for d in supported),
      'unsupported_action_false_accepts':sum(d['actual'][0]!='UNKNOWN' for d in unknown),'strict_correct':sum(d['correct'] for d in details),
      'model_load_ms':load_ms,'first_native_ms':native_ms[0],'subsequent_native_ms_median':statistics.median(native_ms[1:]),
      'prompt_tokens_median':statistics.median(outputs[r['id']]['metrics']['prompt_tokens'] for r in rows),
      'generated_tokens_median':statistics.median(outputs[r['id']]['metrics']['generated_tokens'] for r in rows),
      'native_ms_median':statistics.median(native_ms),'wall_ms_median':statistics.median(outputs[r['id']]['wall_ms'] for r in rows),
      'timing_scope':'Sequential host CPU, native fresh KV/recurrent state per request; uncontrolled cache, thermals and OS; no phone/NPU or full action latency.',
      'strict_failures':[d for d in details if not d['correct']], 'raw_failures':[d for d in details if not d['raw_correct']],
      'directory_bytes_after':budget(),'actions_executed':0,'promoted':False}
    assert all(sha(source/name)==digest for name,digest in identities.items())
    save(out/'details.json',details);save(out/'results.json',summary);print(json.dumps(summary,indent=2));budget()

if __name__=='__main__':main()
