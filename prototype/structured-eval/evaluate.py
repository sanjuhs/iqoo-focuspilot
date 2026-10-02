"""Development comparison of exact checked action/arguments. Executes no phone tools."""
import argparse
import base64
from collections import Counter
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
APP = ROOT / 'prototype/android/app/src/main/java/dev/focuspilot/prototype'
DATA = ROOT / 'prototype/structured-data'
COMMAND = ROOT / 'prototype/structured-command'
NATIVE = ROOT / 'prototype/structured-native'
spec = importlib.util.spec_from_file_location('structured_driver', NATIVE / 'run_capture.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
INTENTS = {'start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown'}


def shape(value):
    if type(value) is not dict or type(value.get('intent')) is not str or value['intent'] not in INTENTS:
        raise ValueError('Known structured proposal object required')
    intent = value['intent']
    keys = {'intent'}
    if intent in ('start_focus', 'timer'):
        keys.add('duration_seconds')
        n = value.get('duration_seconds')
        if type(n) is not int or not (0 if intent == 'start_focus' else 1) <= n <= 7200:
            raise ValueError('Exact bounded integer duration required')
    elif intent == 'alarm':
        keys.update(('hour', 'minute'))
        for name, maximum in [('hour', 23), ('minute', 59)]:
            if type(value.get(name)) is not int or not 0 <= value[name] <= maximum:
                raise ValueError('Exact bounded clock integer required')
    elif intent == 'open_app':
        keys.add('app')
        if type(value.get('app')) is not str or value['app'] not in {'settings', 'calculator', 'clock'}:
            raise ValueError('Approved app target required')
    if set(value) != keys:
        raise ValueError('Exact proposal field set required')
    return value


def rows():
    manifest = driver.strict_json((DATA / 'data-manifest.json').read_text())
    gold = DATA / 'build/development.jsonl'
    requests = DATA / 'build/development-requests.tsv'
    if driver.sha(gold) != manifest['jsonl_sha256'] or driver.sha(requests) != manifest['requests_sha256']:
        raise ValueError('Manually frozen development corpus differs')
    result = [driver.strict_json(line) for line in gold.read_text().splitlines()]
    if len(result) != 24 or len({r['id'] for r in result}) != 24:
        raise ValueError('Exact complete 24-row inventory required')
    for r in result:
        if set(r) != {'id', 'utterance', 'expected'}:
            raise ValueError('Exact manually labelled row schema required')
        shape(r['expected'])
    emitted = [r['id'] + '\t' + r['utterance'] for r in result]
    if requests.read_text().splitlines() != emitted:
        raise ValueError('Request/gold ordered inventory mismatch')
    counts = Counter(r['expected']['intent'] for r in result)
    protocol = driver.strict_json((TASK / 'protocol.json').read_text())
    if counts != protocol['cohort']['counts'] or counts != manifest['by_intent']:
        raise ValueError('Exact prospective development denominators required')
    return result


def private(path):
    p = Path(path).resolve()
    if not p.is_relative_to(TASK / 'build') or p == TASK / 'build':
        raise ValueError('Ignored structured-eval build output required')
    return p


def prepare(out):
    cohort = rows()
    out = private(out)
    out.mkdir(parents=True, exist_ok=False)
    sources = [APP / n for n in ('LocalModel.java', 'ModelCommandGate.java', 'CommandNumberWords.java')]
    sources += [ROOT / 'prototype/qwen-balanced-native/Render.java', COMMAND / 'StructuredCommand.java',
                COMMAND / 'StructuredCommandRender.java', TASK / 'Compare.java']
    snapshots = out / 'source'; snapshots.mkdir()
    classes = out / 'java'; classes.mkdir()
    copies = []
    for source in sources:
        copy = snapshots / source.name
        copy.write_bytes(source.read_bytes()); copies.append(copy)
    subprocess.run([str(JAVA / 'javac'), '-d', str(classes), *map(str, copies)], check=True, timeout=30)
    requests = DATA / 'build/development-requests.tsv'
    base_prompt, base_grammar = out / 'baseline-prompts.tsv', out / 'baseline-grammar.gbnf'
    jni = ROOT / 'prototype/command-eval/build/native'
    subprocess.run([str(JAVA / 'java'), '-Djava.library.path=' + str(jni), '-cp', str(classes),
                    'dev.focuspilot.prototype.Render', str(requests), str(base_prompt), str(base_grammar)],
                   check=True, timeout=30)
    candidate_prompt, candidate_grammar = out / 'structured-prompts.tsv', out / 'structured-grammar.gbnf'
    command = [str(JAVA / 'java'), '-cp', str(classes), 'dev.focuspilot.prototype.StructuredCommandRender']
    with candidate_prompt.open('x') as f:
        f.write(subprocess.check_output(command + [str(requests)], text=True, timeout=30))
    with candidate_grammar.open('x') as f:
        f.write(subprocess.check_output(command + ['--grammar'], text=True, timeout=30))
    for prompts in (base_prompt, candidate_prompt):
        if [ident for ident, _ in driver.prompts(prompts)] != [r['id'] for r in cohort]:
            raise ValueError('Rendered request inventory differs')
    pins = sources + [p for folder in (TASK, COMMAND, DATA, NATIVE) for p in folder.iterdir()
                      if p.is_file() and p.suffix in ('.java', '.cpp', '.py', '.json', '.md')]
    pins += [DATA / 'build/development.jsonl', requests, *copies, *classes.rglob('*.class'),
             ROOT / 'prototype/command-eval/build/native/libfocuspilot_local.dylib',
             ROOT / 'prototype/native/core.cpp']
    locks = {}
    for arm, prompt, grammar in [('baseline', base_prompt, base_grammar),
                                 ('structured', candidate_prompt, candidate_grammar)]:
        locks[arm] = str(driver.prepare(prompt, grammar, NATIVE / ('build/dev-' + arm + '-lock'), pins))
    record = {'schema': 'focuspilot.structured_comparison_lock.v1', 'classes': str(classes),
              'locks': locks, 'rows': 24, 'gold_sha256': driver.sha(DATA / 'build/development.jsonl')}
    driver.write_new(out / 'comparison-lock.json', record)
    return out / 'comparison-lock.json'


def summarize(cohort, raw, proposals):
    by_class = {i: {'rows': 0, 'raw_intent_correct': 0, 'complete_correct': 0,
                    'wrong_accepts': 0} for i in sorted(INTENTS)}
    result = dict(rows=len(cohort), supported_rows=0, unknown_rows=0, raw_intent_correct=0,
                  supported_complete=0, supported_false_abstentions=0, unknown_model_abstentions=0,
                  unknown_validator_refusals=0, wrong_accepts=0, raw_structured_exact_supported=0)
    details = []
    for row in cohort:
        ident = row['id']; gold = shape(row['expected']); predicted = raw[ident]
        proposal, accepted, reason = proposals[ident]
        shape(proposal)
        if type(accepted) is not bool or accepted != (proposal['intent'] != 'unknown'):
            raise ValueError('Validator acceptance and canonical proposal disagree')
        supported = gold['intent'] != 'unknown'
        exact = proposal == gold
        wrong = accepted and not exact
        intent_correct = predicted.get('intent') == gold['intent']
        by = by_class[gold['intent']]; by['rows'] += 1
        by['raw_intent_correct'] += int(intent_correct)
        by['complete_correct'] += int(exact)
        by['wrong_accepts'] += int(wrong)
        result['raw_intent_correct'] += int(intent_correct)
        result['wrong_accepts'] += int(wrong)
        if supported:
            result['supported_rows'] += 1
            result['supported_complete'] += int(exact and accepted)
            result['supported_false_abstentions'] += int(not accepted)
            try:
                raw_exact = shape(predicted) == gold
            except ValueError:
                raw_exact = False
            result['raw_structured_exact_supported'] += int(raw_exact)
        else:
            result['unknown_rows'] += 1
            result['unknown_model_abstentions'] += int(predicted == {'intent': 'unknown'})
            result['unknown_validator_refusals'] += int(not accepted)
        details.append({'id': ident, 'gold': gold, 'raw': predicted, 'proposal': proposal,
                        'accepted': accepted, 'reason': reason, 'supported': supported,
                        'complete_correct': exact, 'wrong_accept': wrong})
    result['confusion'] = {gold: {pred: sum(r['expected']['intent'] == gold and raw[r['id']].get('intent') == pred for r in cohort) for pred in sorted(INTENTS)} for gold in sorted(INTENTS)}
    result['per_class'] = by_class
    return result, details


def gates(arm, cohort, responses, classes, out):
    input_path = out / (arm + '-input.tsv')
    def encoded(s): return base64.b64encode(s.encode()).decode()
    with input_path.open('x') as f:
        for row in cohort:
            f.write(row['id'] + '\t' + encoded(row['utterance']) + '\t' + encoded(responses[row['id']]) + '\n')
    raw = subprocess.check_output([str(JAVA / 'java'), '-cp', classes,
                                  'dev.focuspilot.prototype.Compare', arm.split('-')[0], str(input_path)],
                                 text=True, timeout=30)
    with (out / (arm + '-output.tsv')).open('x') as f: f.write(raw)
    results = {}
    for line in raw.splitlines():
        fields = line.split('\t')
        if len(fields) != 4 or fields[0] in results or fields[2] not in ('true', 'false'):
            raise ValueError('Strict Java proposal output required')
        results[fields[0]] = (driver.strict_json(base64.b64decode(fields[1], validate=True)),
                              fields[2] == 'true', base64.b64decode(fields[3], validate=True).decode())
    if list(results) != [row['id'] for row in cohort]:
        raise ValueError('Complete ordered Java decision inventory required')
    return results


def score(comparison, baseline_capture, structured_capture, out, commit):
    freeze_path = TASK / 'execution-freeze.json'
    committed = subprocess.check_output(['git', 'show', commit + ':' + str(freeze_path.relative_to(ROOT))],
                                        cwd=ROOT, timeout=30)
    import hashlib
    if hashlib.sha256(committed).hexdigest() != driver.sha(freeze_path):
        raise ValueError('Execution freeze differs from capture commit')
    frozen = driver.strict_json(freeze_path.read_text())
    if (driver.sha(comparison) != frozen['comparison_lock_sha256']
            or driver.sha(DATA / 'build/development.jsonl') != frozen['gold_sha256']):
        raise ValueError('Prospective execution/gold binding differs')
    lock = driver.strict_json(Path(comparison).read_text())
    cohort = rows()
    if lock['rows'] != 24 or lock['gold_sha256'] != driver.sha(DATA / 'build/development.jsonl'):
        raise ValueError('Exact comparison/gold binding required')
    out = private(out); out.mkdir(parents=True, exist_ok=False)
    result = {'schema': 'focuspilot.structured_development_result.v1', 'source_commit': commit,
              'phase': 'development_only', 'phone_promoted': False, 'training_performed': False,
              'comparison_lock_sha256': driver.sha(comparison), 'gold_sha256': lock['gold_sha256'],
              'model_sha256': driver.MODEL_SHA, 'arms': {}, 'private_evidence_sha256': {}}
    details_by_arm = {}
    for arm, capture in [('baseline', baseline_capture), ('structured', structured_capture)]:
        native_lock_path = Path(lock['locks'][arm])
        if driver.sha(native_lock_path) != frozen['native_locks_sha256'][arm]:
            raise ValueError('Prospective native lock differs')
        native_lock = driver.strict_json(native_lock_path.read_text())
        driver.verify_lock(native_lock, commit)
        capture = driver.private_path(capture)
        process = driver.strict_json((capture / 'process.json').read_text())
        if (process['source_commit'] != commit or process['exit_code'] != 0 or process['timed_out'] or process.get('error_type')
                or process.get('postflight_error_type') or process['adapter'] is not False
                or process['lock_sha256'] != driver.sha(native_lock_path)
                or process['raw_sha256'] != driver.sha(capture / 'raw.jsonl')):
            raise ValueError('Immutable complete successful base-model capture required')
        expected_command = [native_lock['binary'], str(driver.MODEL), '-', native_lock['prompts'], native_lock['grammar']]
        if process['command'] != expected_command or process['model_sha256'] != driver.MODEL_SHA or type(process['pid']) is not int or process['pid'] <= 0:
            raise ValueError('Exact model/command/owned process binding required')
        initial = driver.strict_json((capture / 'initial.json').read_text())
        started = driver.strict_json((capture / 'started.json').read_text())
        if initial['pid'] is not None or started['pid'] != process['pid']:
            raise ValueError('Initial and started process identities differ')
        for key in initial:
            if key != 'pid' and (initial[key] != started[key] or initial[key] != process[key]):
                raise ValueError('Immutable process event metadata differs')
        if set(initial) != set(started): raise ValueError('Process event field sets differ')
        for name, key in [('stderr.log', 'stderr_sha256'), ('initial.json', 'initial_sha256'), ('started.json', 'started_sha256')]:
            if process[key] != driver.sha(capture / name): raise ValueError('Capture metadata digest differs')
        for path in capture.iterdir():
            if path.is_file(): result['private_evidence_sha256'][str(path.relative_to(ROOT))] = driver.sha(path)
        load, records = driver.validate_capture((capture / 'raw.jsonl').read_text(), native_lock['ids'])
        raw = {r['id']: driver.strict_json(r['text']) for r in records}
        generated = {r['id']: r['text'] for r in records}
        oracle = {r['id']: json.dumps({'intent': r['expected']['intent']} if arm == 'baseline'
                                     else {'intent': r['expected']['intent'], **r['expected']},
                                     separators=(',', ':')) for r in cohort}
        result['arms'][arm] = {'capture_sha256': driver.sha(capture / 'raw.jsonl'),
                               'process_sha256': driver.sha(capture / 'process.json'),
                               'canonical_json_actual_eos': len(records), 'load_ms': load['load_ms']}
        for route, responses in [('generated', generated), ('oracle', oracle)]:
            proposals = gates(arm + '-' + route, cohort, responses, lock['classes'], out)
            summary, details = summarize(cohort, raw, proposals)
            if arm == 'baseline': summary['raw_structured_exact_supported'] = None
            if route == 'oracle':
                for key in ('raw_intent_correct', 'unknown_model_abstentions', 'raw_structured_exact_supported'):
                    summary[key] = None
                for entry in summary['per_class'].values(): entry['raw_intent_correct'] = None
                summary['confusion'] = None
            result['arms'][arm][route] = summary
            driver.write_new(out / (arm + '-' + route + '-details.json'), details)
            if route == 'generated': details_by_arm[arm] = details
        metrics = [r['metrics'] for r in records]
        result['arms'][arm]['timing'] = {'first_native_ms': metrics[0]['total_ms'],
            'subsequent_median_native_ms': statistics.median(m['total_ms'] for m in metrics[1:]),
            'prompt_tokens_min': min(m['prompt_tokens'] for m in metrics),
            'prompt_tokens_max': max(m['prompt_tokens'] for m in metrics),
            'generated_tokens_min': min(m['generated_tokens'] for m in metrics),
            'generated_tokens_max': max(m['generated_tokens'] for m in metrics)}
        driver.verify_lock(native_lock, commit)
    paired = []
    for a, b in zip(details_by_arm['baseline'], details_by_arm['structured']):
        if a['id'] != b['id']: raise ValueError('Paired ordered inventory required')
        paired.append({'id': a['id'], 'supported': a['supported'],
                       'gain': not a['complete_correct'] and b['complete_correct'],
                       'loss': a['complete_correct'] and not b['complete_correct']})
    result['paired_supported'] = {k: sum(r['supported'] and r[k] for r in paired) for k in ('gain', 'loss')}
    driver.write_new(out / 'paired-details.json', paired)
    for path in out.iterdir():
        if path.is_file(): result['private_evidence_sha256'][str(path.relative_to(ROOT))] = driver.sha(path)
    result['decision'] = 'DEVELOPMENT_DIAGNOSTIC_NO_PHONE_PROMOTION'
    result['limitations'] = driver.strict_json((TASK / 'protocol.json').read_text())['limitations']
    driver.write_new(out / 'result.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='mode', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--out', required=True)
    scoring = sub.add_parser('score')
    for key in ('comparison', 'baseline-capture', 'structured-capture', 'out', 'source-commit'):
        scoring.add_argument('--' + key, required=True)
    a = p.parse_args()
    if a.mode == 'prepare': print(prepare(a.out))
    else: print(json.dumps(score(a.comparison, a.baseline_capture, a.structured_capture,
                                a.out, a.source_commit), indent=2))
