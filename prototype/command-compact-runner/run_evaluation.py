"""Compare locked compact and shipped prompts on frozen synthetic data; no actions."""
import argparse
import base64
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
CONFIRM = ROOT / 'prototype/command-compact-confirm'
DEV = ROOT / 'prototype/command-compact-dev'
BUILD = TASK / 'build'
APP_SOURCE = '24f10b62a4a62c22ad6db90ac6339f29e2426dbd'
APP = 'prototype/android/app/src/main/java/dev/focuspilot/prototype/'
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
NATIVE = ROOT / 'prototype/command-eval/build/native/libfocuspilot_local.dylib'
MODEL = ROOT / 'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
MODEL_SHA = '57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
NATIVE_SHA = 'ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e'
GATE_HELPER = ROOT / 'prototype/command-v10-confirm/run_evaluation.py'
GATE_HELPER_SHA = hashlib.sha256(subprocess.check_output(
    ['git', 'show', APP_SOURCE + ':prototype/command-v10-confirm/run_evaluation.py'], cwd=ROOT)).hexdigest()
INTENTS = {'unknown', 'start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def decode_intent(raw, version, mapping):
    """Malformed or truncated output abstains but never counts as semantic success."""
    intent = 'unknown'
    valid = False
    if raw.get('metrics', {}).get('reached_eos') is not True:
        return intent, valid
    text = raw.get('text')
    if version == 'candidate':
        if isinstance(text, str) and re.fullmatch('[0-6]', text) and text in mapping:
            intent = mapping[text]
            valid = intent in INTENTS
    else:
        try:
            def unique_object(pairs):
                value = {}
                for key, item in pairs:
                    if key in value:
                        raise ValueError('Duplicate response object key')
                    value[key] = item
                return value
            parsed = json.loads(text, object_pairs_hook=unique_object)
            valid = isinstance(parsed, dict) and set(parsed) == {'intent'} and parsed['intent'] in INTENTS
            if valid:
                intent = parsed['intent']
        except (TypeError, ValueError, KeyError):
            pass
    return intent, valid


def validate_rows(rows, protocol):
    contract = protocol['corpus']
    if len(rows) != contract['rows'] or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Exactly 100 unique frozen rows required')
    families = Counter(r['family'] for r in rows)
    if len(families) != contract['families'] or set(families.values()) != {contract['rows_per_family']}:
        raise ValueError('Frozen two-row family structure differs')
    supported = [r for r in rows if r['expected_kind'] != 'UNKNOWN']
    if len(supported) != contract['supported_rows'] or dict(Counter(r['semantic_intent'] for r in supported)) != contract['supported_by_intent']:
        raise ValueError('Prospective supported class counts differ')
    opens = Counter(r['expected_kind'] for r in supported if r['semantic_intent'] == 'open_app')
    if opens != Counter({'OPEN_SETTINGS': 2, 'OPEN_CALCULATOR': 2, 'OPEN_CLOCK': 2}):
        raise ValueError('Prospective approved-open target counts differ')
    kinds = {'START_FOCUS': 'start_focus', 'PAUSE_FOCUS': 'pause_focus', 'ALARM': 'alarm',
             'TIMER': 'timer', 'EXPLAIN': 'explain', 'OPEN_SETTINGS': 'open_app',
             'OPEN_CALCULATOR': 'open_app', 'OPEN_CLOCK': 'open_app', 'UNKNOWN': 'unknown'}
    for r in rows:
        if set(r) != set(contract['row_fields']) or r['semantic_intent'] != kinds.get(r['expected_kind']) \
                or r['oracle_intent'] not in INTENTS or not isinstance(r['hard_tags'], list) \
                or any(not isinstance(t, str) for t in r['hard_tags']):
            raise ValueError('Frozen row schema or semantic/kind label differs')
        if any(type(r[k]) is not int for k in ('hour', 'minute', 'seconds')) \
                or not 0 <= r['hour'] <= 23 or not 0 <= r['minute'] <= 59 or not 0 <= r['seconds'] <= 7200:
            raise ValueError('Frozen expected slots outside bounded contract')
        if r['expected_kind'] == 'UNKNOWN' and (r['hour'], r['minute'], r['seconds']) != (0, 0, 0):
            raise ValueError('Unsupported expectation must have zero slots')
        kind = r['expected_kind']
        if kind == 'ALARM' and r['seconds'] != 0 \
                or kind in ('START_FOCUS', 'TIMER') and (r['hour'] != 0 or r['minute'] != 0) \
                or kind == 'TIMER' and r['seconds'] < 1 \
                or kind in ('PAUSE_FOCUS', 'EXPLAIN', 'OPEN_SETTINGS', 'OPEN_CALCULATOR', 'OPEN_CLOCK') and (r['hour'], r['minute'], r['seconds']) != (0, 0, 0):
            raise ValueError('Frozen kind-specific slots differ from contract')
    tags = {t for r in supported for t in r['hard_tags']}
    if not set(contract['hard_tags_assigned_before_capture']).issubset(tags):
        raise ValueError('Required prospective supported hard tags absent')


def semantic_score(rows, outputs):
    if set(outputs) != {r['id'] for r in rows}:
        raise ValueError('Incomplete or unexpected capture IDs; refuse scoring')
    correct = lambda r: outputs[r['id']]['valid'] and outputs[r['id']]['intent'] == r['semantic_intent']
    supported = [r for r in rows if r['expected_kind'] != 'UNKNOWN']
    unknown = [r for r in rows if r['expected_kind'] == 'UNKNOWN']
    result = {'rows': len(rows), 'semantic_correct': sum(correct(r) for r in rows),
            'supported_rows': len(supported), 'supported_correct': sum(correct(r) for r in supported),
            'unknown_rows': len(unknown), 'unknown_correct': sum(correct(r) for r in unknown),
            'schema_and_eos_valid': sum(o['valid'] for o in outputs.values()),
            'per_class': {label: {'rows': sum(r['semantic_intent'] == label for r in rows),
                                  'correct': sum(r['semantic_intent'] == label and correct(r) for r in rows)}
                          for label in sorted(INTENTS)}}
    result['invalid_outputs'] = sum(not o['valid'] for o in outputs.values())
    result['eos_truncations'] = sum(o.get('metrics', {}).get('reached_eos') is not True for o in outputs.values())
    result['confusion'] = {label: {prediction: sum(r['semantic_intent'] == label and
        (outputs[r['id']]['intent'] if outputs[r['id']]['valid'] else 'INVALID') == prediction for r in rows)
        for prediction in sorted(INTENTS | {'INVALID'})} for label in sorted(INTENTS)}
    return result


def distribution(values, expected):
    observed = sorted(v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v))
    return {'sample_count': len(observed), 'missing_or_nonfinite': expected - len(observed),
            'median': statistics.median(observed) if observed else None,
            'nearest_rank_p95': observed[math.ceil(.95 * len(observed)) - 1] if observed else None,
            'min': observed[0] if observed else None, 'max': observed[-1] if observed else None}


def finite_metric(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def difference(candidate, baseline):
    a = finite_metric(candidate); b = finite_metric(baseline)
    return a - b if a is not None and b is not None else None


def paired_summary(rows, baseline_outputs, candidate_outputs, baseline_details, candidate_details):
    """Preserve semantic/gated hard regressions rather than masking them by totals."""
    a = {r['id']: r for r in baseline_details}; b = {r['id']: r for r in candidate_details}
    if set(a) != set(b) or set(a) != {r['id'] for r in rows}:
        raise ValueError('Paired gate inventory mismatch')
    transitions = []
    for r in rows:
        i = r['id']
        old_semantic = baseline_outputs[i]['valid'] and baseline_outputs[i]['intent'] == r['semantic_intent']
        new_semantic = candidate_outputs[i]['valid'] and candidate_outputs[i]['intent'] == r['semantic_intent']
        transitions.append({'id': i, 'family': r['family'], 'intent': r['semantic_intent'],
                            'supported': r['expected_kind'] != 'UNKNOWN', 'hard_tags': r['hard_tags'],
                            'semantic_gain': bool(new_semantic and not old_semantic),
                            'semantic_loss': bool(old_semantic and not new_semantic),
                            'gate_gain': bool(b[i]['correct'] and not a[i]['correct']),
                            'gate_loss': bool(a[i]['correct'] and not b[i]['correct']),
                            'baseline_wrong_accept': bool(a[i]['accepted'] and not a[i]['correct']),
                            'candidate_wrong_accept': bool(b[i]['accepted'] and not b[i]['correct'])})
    def counts(selected):
        return {key: sum(r[key] for r in selected) for key in ('semantic_gain', 'semantic_loss', 'gate_gain', 'gate_loss',
                                                             'baseline_wrong_accept', 'candidate_wrong_accept')}
    tags = sorted({t for r in transitions for t in r['hard_tags']})
    summary = {'all_rows': counts(transitions), 'supported_rows': counts([r for r in transitions if r['supported']]),
               'per_intent': {i: counts([r for r in transitions if r['intent'] == i]) for i in sorted(INTENTS)},
               'per_family': {f: counts([r for r in transitions if r['family'] == f]) for f in sorted({r['family'] for r in rows})},
               'hard_supported': {t: counts([r for r in transitions if r['supported'] and t in r['hard_tags']]) for t in tags}}
    return summary, transitions


def verify_sources(frozen):
    """Use exact selected app snapshots; never modify the Android source tree."""
    source = BUILD / 'selected-source'
    source.mkdir(parents=True, exist_ok=True)
    if set(frozen['selected_source_sha256']) != {'ModelCommandGate.java', 'CommandNumberWords.java', 'LocalModel.java'}:
        raise ValueError('Exactly three selected source snapshots required')
    for name, expected in frozen['selected_source_sha256'].items():
        raw = subprocess.check_output(['git', 'show', APP_SOURCE + ':' + APP + name], cwd=ROOT)
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Frozen selected source mismatch: ' + name)
        target = source / name
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError('Existing source snapshot respected: ' + name)
        else:
            target.write_bytes(raw)
    return source


def capture(version, requests, source, candidate):
    target = BUILD / (version + '-model-output.tsv')
    log = BUILD / (version + '-model.log')
    meta = BUILD / (version + '-model-metadata.json')
    if any(p.exists() for p in (target, log, meta)):
        raise ValueError('Existing capture respected; use --score-only')
    classes = BUILD / 'java'
    classes.mkdir(exist_ok=True)
    subprocess.run([str(JAVA / 'javac'), '-d', str(classes), str(source / 'LocalModel.java'),
                    str(candidate), str(TASK / 'CompactCapture.java')], check=True)
    cmd = [str(JAVA / 'java'), '-Djava.library.path=' + str(NATIVE.parent), '-cp', str(classes),
           'dev.focuspilot.prototype.CompactCapture', str(MODEL), str(requests), version]
    began = time.monotonic()
    utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(json.dumps({'phase': 'capture_started', 'version': version, 'utc': utc}), flush=True)
    with target.open('x') as output, log.open('x') as error:
        try:
            job = subprocess.run(cmd, stdout=output, stderr=error, timeout=300)
            code = job.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            code = None
            timed_out = True
    record = {'started_utc': utc, 'exit_code': code, 'timed_out': timed_out,
              'wall_seconds': time.monotonic() - began, 'output_sha256': sha(target),
              'requests_sha256': sha(requests), 'model_sha256': MODEL_SHA, 'native_sha256': NATIVE_SHA,
              'candidate_source_sha256': sha(candidate), 'capture_source_sha256': sha(TASK / 'CompactCapture.java'),
              'context': 1024, 'threads': 4, 'capture_enabled': False, 'actions_executed': 0}
    write_new(meta, record)
    print(json.dumps({'phase': 'capture_terminal', 'version': version, 'exit_code': code,
                      'wall_seconds': record['wall_seconds']}), flush=True)
    if code != 0:
        raise RuntimeError('Incomplete native capture retained; no score or replacement run')


def verified_capture_metadata(version, requests, candidate):
    path = BUILD / (version + '-model-output.tsv')
    meta = json.loads((BUILD / (version + '-model-metadata.json')).read_text())
    if meta['exit_code'] != 0 or meta['timed_out'] or meta['output_sha256'] != sha(path) \
            or meta['requests_sha256'] != sha(requests) or meta['candidate_source_sha256'] != sha(candidate) \
            or meta['capture_source_sha256'] != sha(TASK / 'CompactCapture.java') \
            or meta['model_sha256'] != MODEL_SHA or meta['native_sha256'] != NATIVE_SHA:
        raise ValueError('Capture provenance or completion mismatch')
    return meta


def read_capture(version, requests, rows, mapping, candidate):
    path = BUILD / (version + '-model-output.tsv')
    meta = verified_capture_metadata(version, requests, candidate)
    outputs = {}
    load = None
    for line in path.read_text().splitlines():
        f = line.split('\t')
        if f[0] == 'LOAD':
            if load is not None or len(f) != 2:
                raise ValueError('Duplicate or malformed load metric')
            load = int(f[1]) / 1e6
            continue
        if len(f) != 3 or f[0] in outputs:
            raise ValueError('Malformed or duplicate capture row')
        raw = json.loads(base64.b64decode(f[2], validate=True))
        intent, valid = decode_intent(raw, version, mapping)
        outputs[f[0]] = {'intent': intent, 'valid': valid, 'metrics': raw['metrics'], 'wall_ms': int(f[1]) / 1e6}
    score = semantic_score(rows, outputs)
    timings = [outputs[r['id']]['metrics'].get('total_ms') for r in rows]
    prompts = distribution([o['metrics'].get('prompt_tokens') for o in outputs.values()], len(rows))
    subsequent = distribution(timings[1:], len(rows) - 1)
    score.update(load_ms=load, first_native_ms=finite_metric(timings[0]), subsequent_native_ms_median=subsequent['median'],
                 prompt_tokens_median=prompts['median'],
                 prompt_tokens_min=prompts['min'],
                 prompt_tokens_max=prompts['max'],
                 metadata=meta,
                 timing_limit='Host CPU, separate baseline then candidate loads; state cleared each request. No OS-cache-cold, controlled thermal/power, phone, NPU or complete action latency claim.')
    fields = ('total_ms', 'prefill_ms', 'decode_ms', 'prompt_tokens', 'generated_tokens')
    score['descriptive_metrics'] = {name: distribution([o['metrics'].get(name) for o in outputs.values()], len(rows)) for name in fields}
    score['descriptive_metrics']['java_wall_ms'] = distribution([o['wall_ms'] for o in outputs.values()], len(rows))
    score['subsequent_total_ms'] = subsequent
    return outputs, score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score-only', action='store_true')
    args = parser.parse_args()
    frozen = json.loads((CONFIRM / 'freeze-manifest.json').read_text())
    protocol = json.loads((CONFIRM / 'protocol.json').read_text())
    lock = json.loads((TASK / 'selection-lock.json').read_text())
    candidate = DEV / 'CompactIntentCandidate.java'
    candidate_meta = DEV / 'candidate.json'
    requests = CONFIRM / 'build/requests.tsv'
    cases = CONFIRM / 'build/cases.jsonl'
    checks = [(CONFIRM / 'protocol.json', 'protocol_sha256'), (CONFIRM / 'generate_data.py', 'generator_sha256'),
              (candidate, 'candidate_source_sha256'), (candidate_meta, 'candidate_metadata_sha256'),
              (requests, 'requests_sha256'), (cases, 'cases_sha256'),
              (TASK / 'run_evaluation.py', 'runner_sha256'), (TASK / 'CompactCapture.java', 'capture_source_sha256'),
              (GATE_HELPER.parent / 'CommandGateEval.java', 'gate_harness_sha256'),
              (TASK / 'selection-lock.json', 'selection_lock_sha256'), (CONFIRM / 'PROTOCOL.md', 'protocol_markdown_sha256')]
    for path, key in checks:
        if sha(path) != frozen[key]:
            raise ValueError('Frozen bytes changed: ' + path.name)
    inventories = frozen['overlap_inventory']
    paths = set()
    for inventory in inventories:
        path = (ROOT / inventory['path']).resolve()
        if not path.is_relative_to(ROOT) or any(part.startswith('.env') for part in path.parts):
            raise ValueError('Inventory outside declared synthetic research scope')
        if sha(path) != inventory['sha256']:
            raise ValueError('Frozen overlap inventory changed')
        paths.add(str(path.relative_to(ROOT)))
    if not set(protocol['corpus']['overlap']['required_prior_paths']).issubset(paths) \
            or 'prototype/command-compact-dev/candidate.json' not in paths:
        raise ValueError('Required prior/example overlap inventory absent')
    derived = [CONFIRM / 'results.json', BUILD / 'paired-transitions.json']
    derived.extend(BUILD / ('selected-' + route + '-' + suffix)
                   for route in ('baseline', 'candidate', 'oracle')
                   for suffix in ('input.tsv', 'output.tsv', 'results.json'))
    if any(path.exists() for path in derived):
        raise ValueError('Existing derived evidence respected; use a separate scratch reproduction')
    if sha(MODEL) != MODEL_SHA or sha(NATIVE) != NATIVE_SHA or sha(GATE_HELPER) != GATE_HELPER_SHA:
        raise ValueError('Model/runtime/shared scorer identity mismatch')
    rows = [json.loads(line) for line in cases.read_text().splitlines()]
    validate_rows(rows, protocol)
    if requests.read_text() != ''.join(r['id'] + '\t' + r['utterance'] + '\n' for r in rows):
        raise ValueError('Request/case inventory mismatch')
    mapping = json.loads(candidate_meta.read_text())['digit_to_intent']
    if mapping != protocol['fixed']['candidate_digit_map']:
        raise ValueError('Candidate digit map differs from prospectively locked protocol')
    if lock['candidate_source_sha256'] != sha(candidate) or lock['candidate_metadata_sha256'] != sha(candidate_meta) \
            or lock['protocol_sha256'] != sha(CONFIRM / 'protocol.json') \
            or lock['selected_source_sha256'] != frozen['selected_source_sha256']:
        raise ValueError('Pre-authoring selection identity changed')
    BUILD.mkdir(exist_ok=True)
    from package_bundled_apk import project_bytes
    if project_bytes(ROOT) + 10_000_000 > 15_000_000_000:
        raise ValueError('Research storage reservation exceeds project cap')
    source = verify_sources(frozen)
    spec = importlib.util.spec_from_file_location('frozen_gate_scoring', GATE_HELPER)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    gate.BUILD = BUILD  # Reuse exact scorer with our isolated source/capture directory.
    models = {}; details = {}; gates = {}; all_outputs = {}
    if not args.score_only:
        if any((BUILD / (v + suffix)).exists() for v in ('baseline', 'candidate')
               for suffix in ('-model-output.tsv', '-model.log', '-model-metadata.json')):
            raise ValueError('Both fresh capture inventories must be absent before any inference')
        for version in ('baseline', 'candidate'):
            capture(version, requests, source, candidate)
    for version in ('baseline', 'candidate'):
        verified_capture_metadata(version, requests, candidate)
    for version in ('baseline', 'candidate'):
        outputs, models[version] = read_capture(version, requests, rows, mapping, candidate)
        all_outputs[version] = outputs
    for version in ('baseline', 'candidate'):
        outputs = all_outputs[version]
        gates[version], details[version] = gate.evaluate_gate(rows, {k: o['intent'] for k, o in outputs.items()}, 'selected', version)
        accepted = {r['id']: r['accepted'] for r in details[version]}
        gates[version]['invalid_output_fallback_abstentions'] = sum(not o['valid'] and not accepted[i] for i, o in outputs.items())
        by_id = {r['id']: r for r in details[version]}
        gates[version]['wrong_accepted_kinds'] = sum(r['accepted'] and r['actual'][0] != r['expected'][0] for r in details[version])
        gates[version]['per_intent'] = {intent: {'rows': sum(r['semantic_intent'] == intent for r in rows),
            'correct': sum(r['semantic_intent'] == intent and by_id[r['id']]['correct'] for r in rows),
            'false_abstentions': sum(r['semantic_intent'] == intent and r['expected_kind'] != 'UNKNOWN' and not by_id[r['id']]['accepted'] for r in rows),
            'wrong_accepted': sum(r['semantic_intent'] == intent and by_id[r['id']]['accepted'] and not by_id[r['id']]['correct'] for r in rows)} for intent in sorted(INTENTS)}
    oracle, _ = gate.evaluate_gate(rows, {r['id']: r['oracle_intent'] for r in rows}, 'selected', 'oracle')
    paired = gate.paired_gate(details['baseline'], details['candidate'])
    paired_full, transitions = paired_summary(rows, all_outputs['baseline'], all_outputs['candidate'], details['baseline'], details['candidate'])
    write_new(BUILD / 'paired-transitions.json', transitions)
    deltas = {name: distribution([difference(all_outputs['candidate'][r['id']]['metrics'].get(name),
        all_outputs['baseline'][r['id']]['metrics'].get(name)) for r in rows], len(rows))
        for name in ('total_ms', 'prefill_ms', 'decode_ms', 'prompt_tokens', 'generated_tokens')}
    result = {'research_only': True, 'scope': 'Frozen informed synthetic host comparison; not human sampling or phone evidence',
              'frozen_manifest': frozen, 'models': models, 'gates': gates, 'oracle': oracle, 'paired': paired,
              'paired_full': paired_full, 'paired_candidate_minus_baseline_metrics': deltas,
              'private_paired_transitions_sha256': sha(BUILD / 'paired-transitions.json'),
              'runner_sha256': sha(Path(__file__)), 'capture_source_sha256': sha(TASK / 'CompactCapture.java'),
              'shared_scorer_sha256': GATE_HELPER_SHA, 'app_source_commit': APP_SOURCE,
              'actions_executed': 0, 'training_performed': False, 'candidate_promoted': False}
    write_new(CONFIRM / 'results.json', result)
    print(json.dumps({'models': {v: {k: r[k] for k in ('semantic_correct', 'supported_correct', 'unknown_correct', 'schema_and_eos_valid', 'subsequent_native_ms_median', 'prompt_tokens_median')} for v, r in models.items()},
                      'gates': {v: {k: r[k] for k in ('supported_correct', 'wrong_accepted', 'supported_false_abstentions')} for v, r in gates.items()}, 'paired': paired}, indent=2))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    main()
