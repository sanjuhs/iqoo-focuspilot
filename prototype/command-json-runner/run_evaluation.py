"""Compare locked JSON candidate and shipped prompts on frozen synthetic data; no actions."""
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
CONFIRM = ROOT / 'prototype/command-json-confirm'
DEV = ROOT / 'prototype/command-json-dev'
BUILD = TASK / 'build'
APP_SOURCE = '1eed4348d3d0233d786bcd3b86c05d225ebf8db6'
APP = 'prototype/android/app/src/main/java/dev/focuspilot/prototype/'
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
NATIVE = ROOT / 'prototype/command-eval/build/native/libfocuspilot_local.dylib'
MODEL = ROOT / 'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
MODEL_SHA = '57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
NATIVE_SHA = 'ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e'
LINKED_LIBRARIES = {
    '/opt/homebrew/opt/llama.cpp/lib/libllama.0.dylib': '2a094b66943b6f6da3eb39cf7360ebd2cef50a864f184bd58a21508ad4ed8668',
    '/opt/homebrew/opt/ggml/lib/libggml.0.dylib': '1c131c59813cb27b2bed388fa27db8647416e74b9fbd5384c22db60db32617d3',
    '/opt/homebrew/opt/ggml/lib/libggml-base.0.dylib': 'c0dcbb8438e3f1ccd40f3a49246c1ea341d813c273bb599448c9766fb2392b56',
}
GATE_HELPER = ROOT / 'prototype/command-v10-confirm/run_evaluation.py'
INTENTS = {'unknown', 'start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


SEMANTIC_HELPER = ROOT / 'prototype/command-compact-runner/run_evaluation.py'
SEMANTIC_HELPER_SHA = '4ef9e7d579049df3648c3eda067ad14a91daf2c34ce049419a2e7339493d37e6'
GATE_HELPER_SHA = '60ad1a6d63ff063fc5e6f9946a89b4cac6a53df626ff24d1e67886425cf6ae2a'


def load_frozen_module(path, expected, name):
    if sha(path) != expected:
        raise ValueError('Shared scorer source changed: ' + path.name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Import unchanged exact shared scoring functions; no inference runs on import.
shared = load_frozen_module(SEMANTIC_HELPER, SEMANTIC_HELPER_SHA, 'json_semantic_shared')
semantic_score = shared.semantic_score
paired_summary = shared.paired_summary
distribution = shared.distribution
finite_metric = shared.finite_metric
difference = shared.difference


def decode_intent(raw, version=None, mapping=None):
    # BOTH JSON arms take the original strict baseline decode path. No digit map.
    intent, valid = shared.decode_intent(raw, 'baseline', {})
    if valid and raw['text'] != json.dumps({'intent': intent}, separators=(',', ':')):
        return 'unknown', False
    return intent, valid


def strict_json(text):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate object key')
            value[key] = item
        return value
    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def require_complete_capture(rows, outputs):
    if len(outputs) != len(rows) or set(outputs) != {r['id'] for r in rows}:
        raise ValueError('Incomplete capture inventory; no partial scoring')
    if list(outputs) != [r['id'] for r in rows]:
        raise ValueError('Emitted capture order differs from frozen requests')
    for output in outputs.values():
        metrics = output['metrics']
        if metrics.get('cpu_only') is not True or metrics.get('capture_enabled') is not False:
            raise ValueError('Actual CPU-only capture-disabled backend required')
        for key in ('total_ms', 'prefill_ms', 'decode_ms', 'context_setup_ms'):
            value = metrics.get(key)
            if finite_metric(value) is None or value < 0:
                raise ValueError('Missing/nonfinite native timing metric')
        for key in ('prompt_tokens', 'generated_tokens'):
            if type(metrics.get(key)) is not int or metrics[key] < 1:
                raise ValueError('Positive native token counts required')
        if type(metrics.get('reached_eos')) is not bool:
            raise ValueError('Real native EOS metric required')


def validate_rows(rows, protocol):
    adapted = json.loads(json.dumps(protocol))
    adapted['corpus']['hard_tags_assigned_before_capture'] = list(protocol['corpus']['hard_tag_minimum_rows'])
    shared.validate_rows(rows, adapted)
    by_id = {row['id']: row for row in rows}
    for row in rows:
        other = by_id.get(row['counterpart_id'])
        if other is None or other['id'] == row['id'] or other['counterpart_id'] != row['id'] \
                or other['family'] != row['family'] \
                or (other['expected_kind'] == 'UNKNOWN') == (row['expected_kind'] == 'UNKNOWN'):
            raise ValueError('Reciprocal same-family supported/negative counterpart required')
    supported = [r for r in rows if r['expected_kind'] != 'UNKNOWN']
    for tag, minimum in protocol['corpus']['hard_tag_minimum_rows'].items():
        if sum(tag in r['hard_tags'] for r in supported) < minimum:
            raise ValueError('Prospective minimum hard tag count missing: ' + tag)


def promotion_review(models, gates, paired):
    supported = paired['supported_rows']
    pause = paired['per_intent']['pause_focus']
    conditions = {
        'at_least_four_supported_complete_gains': supported['gate_gain'] >= 4,
        'zero_all_semantic_losses': paired['all_rows']['semantic_loss'] == 0,
        'zero_supported_complete_gate_losses': supported['gate_loss'] == 0,
        'zero_pause_semantic_and_complete_losses': pause['semantic_loss'] == 0 and pause['gate_loss'] == 0,
        'no_per_intent_semantic_or_complete_decline': all(
            item['semantic_gain'] >= item['semantic_loss'] and item['gate_gain'] >= item['gate_loss']
            for item in paired['per_intent'].values()),
        'zero_wrong_accepts_both_arms': all(gates[arm]['wrong_accepted'] == 0 for arm in ('baseline', 'candidate')),
        'all_100_candidate_schema_and_real_eos_valid': models['candidate']['schema_and_eos_valid'] == 100,
    }
    return {'conditions': conditions, 'prospective_criteria_met': all(conditions.values()),
            'candidate_promoted': False,
            'decision_limit': 'Criteria are necessary only. Independent review required; no automatic app promotion.'}


def frozen_head(source_commit):
    if not re.fullmatch('[0-9a-f]{40}', source_commit):
        raise ValueError('Full frozen source HEAD required')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    changes = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    if actual != source_commit or changes:
        raise ValueError('Clean exact frozen source HEAD required')


def work_budget():
    own = sum(p.stat().st_size for p in TASK.rglob('*') if p.is_file())
    if own > 2_000_000:
        raise ValueError('Runner work exceeds reserved 2 MB')
    from package_bundled_apk import project_bytes
    if project_bytes(ROOT) + 10_000_000 > 15_000_000_000:
        raise ValueError('Project 10 MB research reservation exceeds cap')
    return own


class BoundedSubprocess:
    """Bound shared unchanged scorer's Java compilation and gate subprocesses."""
    def __getattr__(self, name):
        original = getattr(subprocess, name)
        if name not in ('run', 'check_output'):
            return original
        def bounded(*args, **kwargs):
            kwargs.setdefault('timeout', 30)
            return original(*args, **kwargs)
        return bounded


def verify_runtime_and_inventory(frozen):
    """Recheck actual bytes, including ignored inventories, at each execution boundary."""
    if frozen['linked_libraries_sha256'] != LINKED_LIBRARIES:
        raise ValueError('Exactly the three referenced frozen Homebrew library identities required')
    if sha(MODEL) != MODEL_SHA or sha(NATIVE) != NATIVE_SHA:
        raise ValueError('Model/native byte identity changed')
    for path, expected in frozen['linked_libraries_sha256'].items():
        if sha(Path(path)) != expected:
            raise ValueError('Referenced linked-library bytes changed: ' + path)
    paths = set()
    for inventory in frozen['overlap_inventory']:
        path = (ROOT / inventory['path']).resolve()
        if not path.is_relative_to(ROOT) or any(part.startswith('.env') for part in path.parts):
            raise ValueError('Inventory outside declared synthetic research scope')
        relative = str(path.relative_to(ROOT))
        if relative in paths:
            raise ValueError('Duplicate overlap inventory path')
        if sha(path) != inventory['sha256']:
            raise ValueError('Frozen overlap inventory bytes changed: ' + relative)
        paths.add(relative)
    return paths


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


def capture(version, requests, source, candidate, frozen):
    target = BUILD / (version + '-model-output.tsv')
    log = BUILD / (version + '-model.log')
    meta = BUILD / (version + '-model-metadata.json')
    if any(p.exists() for p in (target, log, meta)):
        raise ValueError('Existing capture respected; use --score-only')
    classes = BUILD / (version + '-capture-java')
    classes.mkdir(exist_ok=False)
    subprocess.run([str(JAVA / 'javac'), '-d', str(classes), str(source / 'LocalModel.java'),
                    str(candidate), str(TASK / 'Capture.java')], check=True, timeout=30)
    cmd = [str(JAVA / 'java'), '-Djava.library.path=' + str(NATIVE.parent), '-cp', str(classes),
           'dev.focuspilot.prototype.Capture', str(MODEL), str(requests), version]
    began = time.monotonic()
    utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    job = None
    code = None
    timed_out = False
    failure = None
    started = BUILD / (version + '-model-started.json')
    print(json.dumps({'phase': 'capture_started', 'version': version, 'utc': utc}), flush=True)
    with target.open('x') as output, log.open('x') as error:
        try:
            job = subprocess.Popen(cmd, stdout=output, stderr=error)
            write_new(started, {'pid': job.pid, 'started_utc': utc,
                'command': cmd, 'requests_sha256': sha(requests), 'source_commit': SOURCE_COMMIT})
            code = job.wait(timeout=300)
            timed_out = False
        except subprocess.TimeoutExpired:
            job.kill()
            job.wait()
            code = None
            timed_out = True
        except BaseException as problem:
            if job is not None and job.poll() is None:
                job.kill()
                job.wait()
            failure = problem
    record = {'source_commit': SOURCE_COMMIT, 'pid': job.pid if job is not None else None,
              'error_type': type(failure).__name__ if failure is not None else None,
              'started_utc': utc, 'exit_code': code, 'timed_out': timed_out,
              'wall_seconds': time.monotonic() - began, 'output_sha256': sha(target),
              'requests_sha256': sha(requests), 'model_sha256': MODEL_SHA, 'native_sha256': NATIVE_SHA,
              'candidate_source_sha256': sha(candidate), 'capture_source_sha256': sha(TASK / 'Capture.java'),
              'context': 1024, 'threads': 4, 'capture_enabled': False, 'actions_executed': 0, 'cpu_only': True,
              'log_sha256': sha(log), 'started_record_sha256': sha(started) if started.exists() else None}
    write_new(meta, record)
    print(json.dumps({'phase': 'capture_terminal', 'version': version, 'exit_code': code,
                      'wall_seconds': record['wall_seconds']}), flush=True)
    verify_runtime_and_inventory(frozen)
    frozen_head(SOURCE_COMMIT)
    if code != 0 or failure is not None:
        raise RuntimeError('Incomplete native capture retained; no score or replacement run') from failure


def verified_capture_metadata(version, requests, candidate):
    path = BUILD / (version + '-model-output.tsv')
    meta = json.loads((BUILD / (version + '-model-metadata.json')).read_text())
    if meta.get('source_commit') != SOURCE_COMMIT or meta['exit_code'] != 0 or meta['timed_out'] or meta['output_sha256'] != sha(path) \
            or meta['requests_sha256'] != sha(requests) or meta['candidate_source_sha256'] != sha(candidate) \
            or meta['capture_source_sha256'] != sha(TASK / 'Capture.java') \
            or meta['model_sha256'] != MODEL_SHA or meta['native_sha256'] != NATIVE_SHA or meta.get('cpu_only') is not True \
            or meta.get('context') != 1024 or meta.get('threads') != 4 or meta.get('capture_enabled') is not False \
            or meta.get('log_sha256') != sha(BUILD / (version + '-model.log')) \
            or meta.get('started_record_sha256') != sha(BUILD / (version + '-model-started.json')):
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
            if load is not None or len(f) != 2 or outputs or not f[1].isdigit() or int(f[1]) <= 0:
                raise ValueError('Duplicate or malformed load metric')
            load = int(f[1]) / 1e6
            continue
        if len(f) != 3 or f[0] in outputs or load is None or not f[1].isdigit() or int(f[1]) <= 0:
            raise ValueError('Malformed or duplicate capture row')
        raw = strict_json(base64.b64decode(f[2], validate=True).decode('utf-8'))
        if not isinstance(raw, dict) or set(raw) != {'text', 'activations', 'metrics'} or raw['activations'] != []:
            raise ValueError('Unexpected native envelope or activation capture')
        intent, valid = decode_intent(raw, version, mapping)
        outputs[f[0]] = {'intent': intent, 'valid': valid, 'metrics': raw['metrics'], 'wall_ms': int(f[1]) / 1e6}
    if load is None:
        raise ValueError('Exactly one initial load metric required')
    require_complete_capture(rows, outputs)
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
    fields = ('total_ms', 'prefill_ms', 'decode_ms', 'context_setup_ms', 'prompt_tokens', 'generated_tokens')
    score['descriptive_metrics'] = {name: distribution([o['metrics'].get(name) for o in outputs.values()], len(rows)) for name in fields}
    score['descriptive_metrics']['java_wall_ms'] = distribution([o['wall_ms'] for o in outputs.values()], len(rows))
    score['subsequent_total_ms'] = subsequent
    score['native_total_ms_by_intent'] = {intent: distribution([outputs[r['id']]['metrics']['total_ms']
        for r in rows if r['semantic_intent'] == intent], sum(r['semantic_intent'] == intent for r in rows)) for intent in sorted(INTENTS)}
    score['native_total_ms_by_family'] = {family: distribution([outputs[r['id']]['metrics']['total_ms']
        for r in rows if r['family'] == family], 2) for family in sorted({r['family'] for r in rows})}
    score['native_total_ms_by_hard_tag'] = {tag: distribution([outputs[r['id']]['metrics']['total_ms']
        for r in rows if tag in r['hard_tags']], sum(tag in r['hard_tags'] for r in rows))
        for tag in sorted({t for r in rows for t in r['hard_tags']})}
    score['grouped_timing_limit'] = 'Intent/family/tag distributions include the first request when in that group; first request and overall subsequent distribution are separately reported. Small groups are descriptive only.'
    return outputs, score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score-only', action='store_true')
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args()
    global SOURCE_COMMIT
    SOURCE_COMMIT = args.source_commit
    frozen_head(SOURCE_COMMIT)
    work_budget()
    frozen = json.loads((CONFIRM / 'freeze-manifest.json').read_text())
    protocol = json.loads((CONFIRM / 'protocol.json').read_text())
    lock = json.loads((CONFIRM / 'selection-lock.json').read_text())
    candidate = DEV / 'JsonIntentCandidate.java'
    candidate_meta = DEV / 'candidate.json'
    requests = CONFIRM / 'build/requests.tsv'
    cases = CONFIRM / 'build/cases.jsonl'
    checks = [(CONFIRM / 'protocol.json', 'protocol_sha256'), (CONFIRM / 'generate_data.py', 'generator_sha256'),
              (candidate, 'candidate_source_sha256'), (candidate_meta, 'candidate_metadata_sha256'),
              (requests, 'requests_sha256'), (cases, 'cases_sha256'),
              (TASK / 'run_evaluation.py', 'runner_sha256'), (TASK / 'Capture.java', 'capture_source_sha256'),
              (GATE_HELPER.parent / 'CommandGateEval.java', 'gate_harness_sha256'),
              (CONFIRM / 'selection-lock.json', 'selection_lock_sha256'), (CONFIRM / 'PROTOCOL.md', 'protocol_markdown_sha256'),
              (SEMANTIC_HELPER, 'semantic_helper_sha256'), (GATE_HELPER, 'gate_helper_sha256')]
    for path, key in checks:
        if sha(path) != frozen[key]:
            raise ValueError('Frozen bytes changed: ' + path.name)
    paths = verify_runtime_and_inventory(frozen)
    if not set([item['path'] for item in protocol['corpus']['overlap']['actual_available_required_sources']]).issubset(paths) \
            or 'prototype/command-json-dev/candidate.json' not in paths:
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
    mapping = {}
    metadata = json.loads(candidate_meta.read_text())
    if lock['candidate_source_sha256'] != sha(candidate) or lock['candidate_metadata_sha256'] != sha(candidate_meta) \
            or lock['protocol_sha256'] != sha(CONFIRM / 'protocol.json') \
            or lock['protocol_markdown_sha256'] != sha(CONFIRM / 'PROTOCOL.md') \
            or lock['selected_source_sha256'] != frozen['selected_source_sha256'] \
            or lock['candidate_template_sha256'] != metadata['rendered_marker_prompt_sha256'] \
            or lock['grammar_sha256'] != metadata['grammar_sha256'] \
            or lock['grammar_sha256'] != hashlib.sha256(metadata['grammar'].encode()).hexdigest() \
            or lock['max_tokens'] != 128 or metadata['max_tokens'] != 128 \
            or protocol['fixed']['model_sha256'] != MODEL_SHA \
            or protocol['fixed']['native_sha256'] != NATIVE_SHA:
        raise ValueError('Pre-authoring selection identity changed')
    BUILD.mkdir(exist_ok=args.score_only)
    source = verify_sources(frozen)
    gate = load_frozen_module(GATE_HELPER, GATE_HELPER_SHA, 'json_gate_shared')
    gate.BUILD = BUILD  # Reuse exact scorer with our isolated source/capture directory.
    gate.subprocess = BoundedSubprocess()
    models = {}; details = {}; gates = {}; all_outputs = {}
    if not args.score_only:
        if any((BUILD / (v + suffix)).exists() for v in ('baseline', 'candidate')
               for suffix in ('-model-output.tsv', '-model.log', '-model-metadata.json', '-model-started.json')):
            raise ValueError('Both fresh capture inventories must be absent before any inference')
        for version in ('baseline', 'candidate'):
            capture(version, requests, source, candidate, frozen)
            for path, key in checks:
                if sha(path) != frozen[key]:
                    raise ValueError('Frozen source changed during capture: ' + path.name)
            work_budget()
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
        for name in ('total_ms', 'prefill_ms', 'decode_ms', 'prompt_tokens', 'generated_tokens', 'context_setup_ms')}
    result = {'research_only': True, 'scope': 'Frozen informed synthetic host comparison; not human sampling or phone evidence',
              'frozen_manifest': frozen, 'models': models, 'gates': gates, 'oracle': oracle, 'paired': paired,
              'paired_full': paired_full, 'promotion_review': promotion_review(models, gates, paired_full), 'paired_candidate_minus_baseline_metrics': deltas,
              'private_paired_transitions_sha256': sha(BUILD / 'paired-transitions.json'),
              'runner_sha256': sha(Path(__file__)), 'capture_source_sha256': sha(TASK / 'Capture.java'),
              'shared_gate_scorer_sha256': GATE_HELPER_SHA, 'shared_semantic_scorer_sha256': SEMANTIC_HELPER_SHA, 'app_source_commit': APP_SOURCE, 'runner_source_commit': SOURCE_COMMIT,
              'linked_library_binding_limit': 'Only the three referenced Homebrew libraries are byte-bound; this is not an entire OS or dynamically loaded backend closure identity.',
              'actions_executed': 0, 'training_performed': False, 'candidate_promoted': False}
    frozen_head(SOURCE_COMMIT)
    for path, key in checks:
        if sha(path) != frozen[key]:
            raise ValueError('Frozen source changed before publication')
    verify_runtime_and_inventory(frozen)
    work_budget()
    verify_sources(frozen)
    for arm in ('baseline', 'candidate'):
        verified_capture_metadata(arm, requests, candidate)
    write_new(CONFIRM / 'results.json', result)
    print(json.dumps({'models': {v: {k: r[k] for k in ('semantic_correct', 'supported_correct', 'unknown_correct', 'schema_and_eos_valid', 'subsequent_native_ms_median', 'prompt_tokens_median')} for v, r in models.items()},
                      'gates': {v: {k: r[k] for k in ('supported_correct', 'wrong_accepted', 'supported_false_abstentions')} for v, r in gates.items()}, 'paired': paired}, indent=2))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    main()
