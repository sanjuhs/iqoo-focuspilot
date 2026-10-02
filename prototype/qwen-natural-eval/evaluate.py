"""One original-model capture; compare two frozen whole-request gates, exact slots."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
sys.path.insert(0, str(ROOT / 'prototype/qwen-balanced-native'))
import run_capture as native
import score as scoring


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def verify_source_freeze(path=None):
    freeze = native.strict_json(Path(path or TASK / 'source-freeze.json').read_text())
    for name, expected in freeze['files_sha256'].items():
        selected = (ROOT / name).resolve()
        if not selected.is_relative_to(ROOT) or native.sha(selected) != expected:
            raise ValueError('Prospectively frozen source changed: ' + name)
    return freeze


def qualification(old, new, paired, canonical_eos, process, protocol):
    q = protocol['qualification']
    a, b = old['generated'], new['generated']
    return {
        'exact_denominators': all(r['rows'] == 100 and r['supported_rows'] == 50
                                 and r['unknown_rows'] == 50
                                 for r in (a, b, old['oracle'], new['oracle'])),
        'supported_complete_net_gain_at_least_6': b['supported_complete_proposals']
            - a['supported_complete_proposals'] >= q['supported_complete_net_gain_min'],
        'supported_complete_losses_zero': paired['supported_rows']['gate_loss']
            <= q['supported_complete_losses_max'],
        'supported_per_class_preserved': all(b['per_class'][i]['complete_proposal_correct']
            >= a['per_class'][i]['complete_proposal_correct'] for i in native.INTENTS if i != 'unknown'),
        'pause_preserved': b['per_class']['pause_focus']['complete_proposal_correct']
            >= a['per_class']['pause_focus']['complete_proposal_correct'],
        'wrong_accepts_zero_generated_and_oracle': all(r['wrong_accepts'] == 0
            for r in (a, b, old['oracle'], new['oracle'])),
        'all_unknown_refused_generated_and_oracle': all(r['unknown_refused_by_gate'] == 50
            for r in (a, b, old['oracle'], new['oracle'])),
        'canonical_actual_eos_100': canonical_eos == q['canonical_eos'],
        'runtime_failures_zero': process['exit_code'] == 0 and not process['timed_out']
            and not process.get('error_type') and not process.get('postflight_error_type'),
        'oracle_coverage_preserved': new['oracle']['supported_complete_proposals']
            >= old['oracle']['supported_complete_proposals'],
    }


def prepare(requests, gold, manifest, out):
    frozen = verify_source_freeze()
    out = native.private_path(out)
    candidate = ROOT / 'prototype/qwen-natural-validation/ModelCommandGate.java'
    pins = [TASK / 'evaluate.py', TASK / 'test_evaluate.py', TASK / 'protocol.json',
            TASK / 'design-lock.json', TASK / 'README.md', candidate,
            ROOT / 'prototype/qwen-natural-validation/README.md',
            Path(gold), Path(manifest), TASK / 'source-freeze.json']
    pins.extend(ROOT / name for name in frozen['files_sha256'])
    initial = native.prepare(requests, out, pins)
    lock = native.strict_json(initial.read_text())
    classes = out / 'candidate-java'
    classes.mkdir()
    snapshot = out / 'candidate-source'
    snapshot.mkdir()
    inputs = []
    for src in [candidate, native.APP / 'CommandNumberWords.java', native.TASK / 'CommandGateEval.java']:
        dest = snapshot / src.name
        dest.write_bytes(src.read_bytes())
        inputs.append(dest)
    subprocess.run([str(native.JAVA / 'javac'), '-d', str(classes), *map(str, inputs)],
                   check=True, timeout=30)
    lock['candidate_classes'] = str(classes)
    lock['candidate_gate_sha256'] = native.sha(candidate)
    lock['baseline_gate_sha256'] = native.sha(native.APP / 'ModelCommandGate.java')
    for path in [*inputs, *classes.rglob('*.class')]:
        lock['files_sha256'][str(path)] = native.sha(path)
    path = out / 'comparison-lock.json'
    write(path, lock)
    verify_source_freeze()
    return path


def score(lock_path, capture_dir, gold, out, commit):
    lock_path = native.private_path(lock_path)
    lock = native.strict_json(lock_path.read_text())
    native.verify_lock(lock, commit)
    rows = scoring.read_rows(gold, lock)
    protocol = native.strict_json((TASK / 'protocol.json').read_text())
    from collections import Counter
    if Counter(r['intent'] for r in rows) != protocol['fresh_cohort']['counts']:
        raise ValueError('Exact prospective class denominator required')
    capture_dir = native.private_path(capture_dir)
    process = native.strict_json((capture_dir / 'process.json').read_text())
    if (process['exit_code'] != 0 or process['timed_out'] or process.get('error_type')
            or process.get('postflight_error_type') or process['adapter_sha256'] is not None
            or process['lock_sha256'] != native.sha(lock_path)
            or process['raw_sha256'] != native.sha(capture_dir / 'raw.jsonl')):
        raise ValueError('Successful original-model immutable capture required')
    load, records = native.validate_capture((capture_dir / 'raw.jsonl').read_text(), lock['ids'], False)
    predictions = {r['id']: native.strict_json(r['text'])['intent'] for r in records}
    out = Path(out).resolve()
    if not out.is_relative_to(TASK / 'build') or out.exists():
        raise ValueError('Exclusive ignored scoring output required')
    out.mkdir(parents=True)
    result = {'schema': 'focuspilot.natural_gate_result.v1', 'source_commit': commit,
              'promoted': False, 'research_only': True,
              'scope': 'One unchanged original-model host CPU capture reused by both Java gates; no task executed',
              'lock_sha256': native.sha(lock_path), 'gold_sha256': native.sha(gold),
              'process_sha256': native.sha(capture_dir / 'process.json'),
              'candidate_gate_sha256': lock['candidate_gate_sha256'],
              'baseline_gate_sha256': lock['baseline_gate_sha256'],
              'canonical_actual_eos': len(records), 'load_ms': load['load_ms']}
    for arm, classes in [('baseline', lock['classes']), ('candidate', lock['candidate_classes'])]:
        result[arm] = {}
        for route in ('generated', 'oracle'):
            name = arm + '-' + route
            inp = out / (name + '-input.tsv')
            with inp.open('x') as f:
                for row in rows:
                    pred = predictions[row['id']] if route == 'generated' else row['oracle_intent']
                    f.write(row['id'] + '\t' + pred + '\t' + row['utterance'] + '\n')
            raw = subprocess.check_output([str(native.JAVA / 'java'), '-cp', classes,
                'dev.focuspilot.prototype.CommandGateEval', str(inp)], text=True, timeout=30)
            (out / (name + '-output.tsv')).write_text(raw)
            proposals = {}
            for line in raw.splitlines():
                fields = line.split('\t')
                if len(fields) != 6 or fields[0] in proposals:
                    raise ValueError('Invalid scored gate inventory')
                proposals[fields[0]] = {'kind': fields[1], 'hour': int(fields[2]),
                    'minute': int(fields[3]), 'seconds': int(fields[4])}
            summary, details = scoring.summarize(rows, predictions, proposals)
            result[arm][route] = summary
            write(out / (name + '-details.json'), details)
    a = native.strict_json((out / 'baseline-generated-details.json').read_text())
    b = native.strict_json((out / 'candidate-generated-details.json').read_text())
    result['paired'], details = scoring.paired(a, b)
    write(out / 'paired-details.json', details)
    result['qualification_checks'] = qualification(result['baseline'], result['candidate'],
        result['paired'], len(records), process, protocol)
    result['qualified'] = all(result['qualification_checks'].values())
    result['decision'] = 'QUALIFIED_HOST_GATE_ONLY' if result['qualified'] else 'REJECTED_KEEP_BASELINE'
    native.verify_lock(lock, commit)
    result['private_evidence_sha256'] = {str(p.relative_to(ROOT)): native.sha(p)
        for p in out.iterdir() if p.is_file()}
    write(out / 'result.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for key in ('requests', 'gold', 'manifest', 'out'):
        prep.add_argument('--' + key, required=True)
    s = sub.add_parser('score')
    for key in ('lock', 'capture-dir', 'gold', 'out', 'source-commit'):
        s.add_argument('--' + key, required=True)
    a = p.parse_args()
    if a.command == 'prepare':
        print(prepare(a.requests, a.gold, a.manifest, a.out))
    else:
        print(json.dumps(score(a.lock, a.capture_dir, a.gold, a.out, a.source_commit), indent=2))
