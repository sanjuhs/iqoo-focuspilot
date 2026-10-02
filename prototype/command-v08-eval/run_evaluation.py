"""Immutable-request actual JNI/Java validator comparison; no phone actions."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
BUILD = TASK/'build'
INTENTS = {'start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def verify_freeze():
    frozen = json.loads((TASK/'freeze-manifest.json').read_text())
    for path, key in [(TASK/'generate_data.py', 'generator_sha256'),
                      (TASK/'protocol.json', 'protocol_sha256'),
                      (BUILD/'cases.jsonl', 'cases_sha256'),
                      (BUILD/'requests.tsv', 'requests_sha256'),
                      (BUILD/'v07-source/ModelCommandGate.java', 'v07_gate_sha256'),
                      (BUILD/'LocalModel.java', 'adapter_sha256')]:
        assert sha(path) == frozen[key], f'Frozen bytes changed: {path.name}'
    rows = [json.loads(line) for line in (BUILD/'cases.jsonl').read_text().splitlines()]
    assert len(rows) == frozen['rows'] and len({r['id'] for r in rows}) == len(rows)
    return frozen, rows


def strict_score(rows, proposals):
    assert set(proposals) == {r['id'] for r in rows}
    details = []
    for row in rows:
        expected = (row['expected_kind'], row['hour'], row['minute'], row['seconds'])
        actual = tuple(proposals[row['id']])
        details.append({'id': row['id'], 'family': row['family'], 'expected': expected,
                        'actual': actual, 'correct': expected == actual,
                        'supported': expected[0] != 'UNKNOWN', 'accepted': actual[0] != 'UNKNOWN'})
    supported = [d for d in details if d['supported']]
    unsupported = [d for d in details if not d['supported']]
    accepted = [d for d in details if d['accepted']]
    summary = dict(rows=len(rows), strict_correct=sum(d['correct'] for d in details),
                   supported_rows=len(supported), supported_correct=sum(d['correct'] for d in supported),
                   supported_false_abstentions=sum(not d['accepted'] for d in supported),
                   supported_wrong_accepted=sum(d['accepted'] and not d['correct'] for d in supported),
                   must_abstain_rows=len(unsupported), correct_abstentions=sum(not d['accepted'] for d in unsupported),
                   unsupported_false_accepts=sum(d['accepted'] for d in unsupported),
                   accepted=len(accepted), correct_accepted=sum(d['correct'] for d in accepted),
                   wrong_accepted=sum(not d['correct'] for d in accepted), coverage=len(accepted)/len(rows),
                   accepted_precision=sum(d['correct'] for d in accepted)/len(accepted) if accepted else None,
                   actions_executed=0)
    summary['per_family'] = {family: {'rows': sum(d['family']==family for d in details),
                                    'correct': sum(d['family']==family and d['correct'] for d in details),
                                    'wrong_accepted': sum(d['family']==family and d['accepted'] and not d['correct'] for d in details)}
                             for family in sorted({d['family'] for d in details})}
    return summary, details


def capture_model(frozen, model):
    native = ROOT/'prototype/command-eval/build/native/libfocuspilot_local.dylib'
    protocol = json.loads((TASK/'protocol.json').read_text())
    assert sha(model)==protocol['model_sha256'] and sha(native)==protocol['native_sha256']
    java_out = BUILD/'baseline-java'; java_out.mkdir(exist_ok=True)
    subprocess.run([str(JAVA/'javac'), '-d', str(java_out), str(BUILD/'LocalModel.java'),
                    str(TASK/'CommandBaseline.java')], check=True)
    output, log = BUILD/'model-output.tsv', BUILD/'model.log'
    if output.exists():
        raise ValueError('Refuse to overwrite frozen model capture; use --score-only for review')
    start = time.monotonic()
    command = [str(JAVA/'java'), '-Djava.library.path='+str(native.parent), '-cp', str(java_out),
               'dev.focuspilot.prototype.CommandBaseline', str(model), str(BUILD/'requests.tsv')]
    with output.open('w') as out, log.open('w') as err:
        job = subprocess.run(command, stdout=out, stderr=err, timeout=300)
    metadata = {'exit_code':job.returncode, 'wall_seconds':time.monotonic()-start,
                'model_sha256':sha(model), 'native_sha256':sha(native), 'adapter_sha256':frozen['adapter_sha256'],
                'requests_sha256':frozen['requests_sha256'], 'output_sha256':sha(output),
                'baseline_source_sha256':sha(TASK/'CommandBaseline.java'), 'cpu_only':True,
                'context':1024, 'threads':4, 'capture_enabled':False, 'actions_executed':0}
    write_json(BUILD/'model-metadata.json', metadata)
    job.check_returncode()


def read_model(rows, frozen):
    metadata = json.loads((BUILD/'model-metadata.json').read_text())
    assert metadata['exit_code']==0 and metadata['output_sha256']==sha(BUILD/'model-output.tsv')
    assert metadata['requests_sha256']==frozen['requests_sha256'] and metadata['adapter_sha256']==frozen['adapter_sha256']
    outputs = {}; load_ms = None
    for line in (BUILD/'model-output.tsv').read_text().splitlines():
        fields = line.split('\t')
        if fields[0]=='LOAD':
            load_ms = int(fields[1])/1e6
            continue
        assert len(fields)==3 and fields[0] not in outputs
        raw = json.loads(base64.b64decode(fields[2])); intent = 'unknown'; valid = False
        try:
            response = json.loads(raw['text'])
            valid = (set(response)=={'intent'} and response['intent'] in INTENTS
                     and raw['metrics']['reached_eos'] is True)
            if valid: intent = response['intent']
        except (KeyError, ValueError, TypeError):
            pass
        outputs[fields[0]] = {'intent':intent, 'valid':valid, 'wall_ms':int(fields[1])/1e6,
                             'metrics':raw['metrics']}
    assert set(outputs)=={r['id'] for r in rows}
    supported = [r for r in rows if r['expected_kind']!='UNKNOWN']
    unsupported = [r for r in rows if r['expected_kind']=='UNKNOWN']
    timings = [outputs[r['id']]['metrics']['total_ms'] for r in rows]
    summary = {'rows':len(rows), 'schema_and_eos_valid':sum(v['valid'] for v in outputs.values()),
               'supported_rows':len(supported),
               'supported_intent_correct':sum(outputs[r['id']]['intent']==r['oracle_intent'] for r in supported),
               'must_abstain_rows':len(unsupported),
               'unsupported_model_nonunknown_proposals':sum(outputs[r['id']]['intent']!='unknown' for r in unsupported),
               'load_ms':load_ms, 'first_native_ms':timings[0], 'subsequent_native_ms_median':statistics.median(timings[1:]),
               'wall_ms_median':statistics.median(v['wall_ms'] for v in outputs.values()), 'metadata':metadata,
               'timing_limit':'Host CPU only. First request after model load; OS cache and thermals uncontrolled. Subsequent requests reuse context with state cleared. No phone/NPU/cold disk or head acceleration claim.'}
    return outputs, summary


def evaluate_gate(rows, intents, version, source_dir):
    java_out = BUILD/(version+'-java'); java_out.mkdir(exist_ok=True)
    sources = sorted(source_dir.glob('*.java'))
    subprocess.run([str(JAVA/'javac'), '-d', str(java_out), *map(str,sources),
                    str(TASK/'CommandGateEval.java')], check=True)
    input_path = BUILD/(version+'-input.tsv')
    input_path.write_text(''.join(f"{r['id']}\t{intents[r['id']]}\t{r['utterance']}\n" for r in rows))
    raw = subprocess.check_output([str(JAVA/'java'), '-cp', str(java_out),
                                   'dev.focuspilot.prototype.CommandGateEval', str(input_path)], text=True)
    (BUILD/(version+'-output.tsv')).write_text(raw)
    proposals = {}
    for line in raw.splitlines():
        f = line.split('\t'); assert len(f)==6 and f[0] not in proposals
        proposals[f[0]] = (f[1], int(f[2]), int(f[3]), int(f[4]))
    summary, details = strict_score(rows,proposals)
    write_json(BUILD/(version+'-results.json'),details)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate-sha',required=True)
    parser.add_argument('--number-words-sha',required=True)
    parser.add_argument('--score-only',action='store_true')
    parser.add_argument('--model',default=str(ROOT/'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'))
    args = parser.parse_args()
    frozen, rows = verify_freeze()
    source = ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
    candidate = BUILD/'v08-source'; candidate.mkdir(exist_ok=True)
    for name, expected in [('ModelCommandGate.java',args.candidate_sha), ('CommandNumberWords.java',args.number_words_sha)]:
        if args.score_only:
            assert sha(candidate/name)==expected
        else:
            assert sha(source/name)==expected, 'Candidate must be locked before evaluation'
            target = candidate/name
            if target.exists(): assert sha(target)==expected
            else: shutil.copyfile(source/name,target)
    lock={'gate_sha256':args.candidate_sha,'number_words_sha256':args.number_words_sha,
          'dataset_sha256':frozen['cases_sha256'],'runner_sha256':sha(__file__),
          'locked_before_any_eval':True}
    lock_path=BUILD/'candidate-lock.json'
    if lock_path.exists():
        prior=json.loads(lock_path.read_text()); assert prior['gate_sha256']==args.candidate_sha and prior['number_words_sha256']==args.number_words_sha
    else: write_json(lock_path,lock)
    if not args.score_only:
        print('Frozen data verified; starting unchanged JNI baseline once.',flush=True)
        capture_model(frozen,Path(args.model))
    outputs, raw_summary=read_model(rows,frozen)
    result={'schema':1,'frozen_manifest':frozen,'candidate_lock':json.loads(lock_path.read_text()),
            'generated_model':raw_summary,'comparisons':{},'source_sha256':sha(__file__),
            'scope':'Frozen synthetic pre-event host CPU evidence; no model training/prompt change/download/phone actions. Oracle domain intents deliberately challenge unsupported original-text rejection.',
            'actions_executed':0,'candidate_promoted':False}
    for label, intents in [('model',{key:v['intent'] for key,v in outputs.items()}),
                           ('oracle',{r['id']:r['oracle_intent'] for r in rows})]:
        result['comparisons'][label]={}
        for version,directory in [('v07',BUILD/'v07-source'),('v08',candidate)]:
            result['comparisons'][label][version]=evaluate_gate(rows,intents,version+'-'+label,directory)
    write_json(TASK/'results.json',result)
    print(json.dumps({label:{version:{key:values[key] for key in ['strict_correct','supported_correct','wrong_accepted','unsupported_false_accepts','accepted']} for version,values in versions.items()} for label,versions in result['comparisons'].items()},indent=2))


if __name__=='__main__':
    main()
