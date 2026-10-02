"""One original-prompt CPU capture, two locked original-request gates; no actions."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BUILD = TASK / 'build'
CONFIRM = ROOT / 'prototype/command-gate-v14-confirm'
DEV = ROOT / 'prototype/command-gate-v14-dev'
APP_SOURCE = '1eed4348d3d0233d786bcd3b86c05d225ebf8db6'
APP_PATH = 'prototype/android/app/src/main/java/dev/focuspilot/prototype/'
JSON_HELPER = ROOT / 'prototype/command-json-runner/run_evaluation.py'
JSON_HELPER_SHA = 'f5d3bf17f2f379b970ebaeec73db5dcb9db1cff0d0e8dddda587e741a9c6f785'
GATE_HELPER = ROOT / 'prototype/command-v10-confirm/run_evaluation.py'
GATE_HELPER_SHA = '60ad1a6d63ff063fc5e6f9946a89b4cac6a53df626ff24d1e67886425cf6ae2a'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_module(path, digest, name):
    if sha(path) != digest:
        raise ValueError('Shared helper bytes changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_module(JSON_HELPER, JSON_HELPER_SHA, 'v14_json_shared')
semantic_score = shared.semantic_score
paired_summary = shared.paired_summary
distribution = shared.distribution
decode_intent = shared.decode_intent
validate_rows = shared.validate_rows


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def verify_frozen(frozen, checks, source_commit):
    shared.frozen_head(source_commit)
    for path, key in checks:
        if sha(path) != frozen[key]:
            raise ValueError('Frozen source/corpus bytes changed: ' + path.name)
    return shared.verify_runtime_and_inventory(frozen)


def work_budget():
    if sum(p.stat().st_size for p in TASK.rglob('*') if p.is_file()) > 2_000_000:
        raise ValueError('Runner exceeds 2 MB work budget')
    from package_bundled_apk import project_bytes
    if project_bytes(ROOT) + 10_000_000 > 15_000_000_000:
        raise ValueError('Project 10 MB research reservation exceeds 15 GB cap')


def source_snapshots(frozen, candidate):
    pins = frozen['selected_source_sha256']
    if set(pins) != {'LocalModel.java', 'ModelCommandGate.java', 'CommandNumberWords.java'}:
        raise ValueError('Exactly three immutable selected app source pins required')
    if frozen['candidate_number_words_sha256'] != pins['CommandNumberWords.java']:
        raise ValueError('Number-word parser must remain unchanged')
    if sha(candidate) != frozen['candidate_gate_sha256']:
        raise ValueError('Candidate gate bytes changed')
    for arm in ('baseline', 'candidate'):
        folder = BUILD / (arm + '-source')
        folder.mkdir(exist_ok=True)
        for name, digest in pins.items():
            raw = subprocess.check_output(['git', 'show', APP_SOURCE + ':' + APP_PATH + name], cwd=ROOT, timeout=30)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('Immutable app snapshot mismatch')
            if arm == 'candidate' and name == 'ModelCommandGate.java':
                raw = candidate.read_bytes()
            target = folder / name
            if target.exists():
                if target.read_bytes() != raw:
                    raise ValueError('Existing source snapshot changed')
            else:
                with target.open('xb') as stream:
                    stream.write(raw)


def capture(requests, candidate, frozen, checks, source_commit):
    paths = {name: BUILD / ('baseline-model-' + name) for name in
             ('output.tsv', 'metadata.json', 'started.json')}
    log = BUILD / 'baseline-model.log'
    if any(path.exists() for path in (*paths.values(), log)):
        raise ValueError('Existing original-prompt capture retained; no retry')
    classes = BUILD / 'capture-java'
    classes.mkdir(exist_ok=False)
    subprocess.run([str(shared.JAVA / 'javac'), '-d', str(classes),
                    str(BUILD / 'baseline-source/LocalModel.java'), str(TASK / 'Capture.java')],
                   check=True, timeout=30)
    command = [str(shared.JAVA / 'java'), '-Djava.library.path=' + str(shared.NATIVE.parent),
               '-cp', str(classes), 'dev.focuspilot.prototype.Capture', str(shared.MODEL), str(requests)]
    began = time.monotonic()
    utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    job = None
    code = None
    timed_out = False
    failure = None
    print(json.dumps({'phase': 'original_prompt_capture_started', 'utc': utc}), flush=True)
    with paths['output.tsv'].open('x') as output, log.open('x') as error:
        try:
            job = subprocess.Popen(command, stdout=output, stderr=error)
            write_new(paths['started.json'], {'pid': job.pid, 'command': command, 'started_utc': utc,
                      'source_commit': source_commit, 'requests_sha256': sha(requests)})
            code = job.wait(timeout=300)
        except subprocess.TimeoutExpired:
            job.kill()
            job.wait()
            timed_out = True
        except BaseException as problem:
            if job is not None and job.poll() is None:
                job.kill()
                job.wait()
            failure = problem
    record = {'source_commit': source_commit, 'pid': job.pid if job else None,
              'started_utc': utc, 'exit_code': code, 'timed_out': timed_out,
              'error_type': type(failure).__name__ if failure else None,
              'wall_seconds': time.monotonic() - began, 'output_sha256': sha(paths['output.tsv']),
              'log_sha256': sha(log), 'started_record_sha256': sha(paths['started.json']) if paths['started.json'].exists() else None,
              'requests_sha256': sha(requests), 'model_sha256': shared.MODEL_SHA,
              'native_sha256': shared.NATIVE_SHA, 'candidate_source_sha256': sha(candidate),
              'candidate_binding_limit': 'Gate provenance only; candidate gate is not used in native generation.',
              'capture_source_sha256': sha(TASK / 'Capture.java'), 'context': 1024, 'threads': 4,
              'capture_enabled': False, 'cpu_only': True, 'actions_executed': 0,
              'model_adapter_sha256': frozen['selected_source_sha256']['LocalModel.java']}
    write_new(paths['metadata.json'], record)
    print(json.dumps({'phase': 'original_prompt_capture_terminal', 'exit_code': code,
                      'timed_out': timed_out, 'wall_seconds': record['wall_seconds']}), flush=True)
    verify_frozen(frozen, checks, source_commit)
    if code != 0 or failure is not None:
        raise RuntimeError('Incomplete original-prompt capture retained; no reduced denominator or rerun') from failure


def promotion_review(gates, pairs, paired_full, model):
    generated = pairs['generated']
    conditions = {
        'at_least_four_supported_generated_full_proposal_gains': generated['supported_gains'] >= 4,
        'zero_supported_generated_losses': generated['supported_losses'] == 0,
        'zero_supported_oracle_losses': pairs['oracle']['supported_losses'] == 0,
        'zero_wrong_accepts_both_gates_both_routes': all(result['wrong_accepted'] == 0
            for route in gates.values() for result in route.values()),
        'zero_pause_losses_both_routes': all(pair['per_intent']['pause_focus']['gate_loss'] == 0
            for pair in paired_full.values()),
        'no_per_intent_complete_proposal_decline_both_routes': all(
            item['gate_gain'] >= item['gate_loss'] for pair in paired_full.values()
            for item in pair['per_intent'].values()),
        'all_100_original_prompt_schema_and_real_eos_valid': model['schema_and_eos_valid'] == 100,
    }
    return {'conditions': conditions, 'prospective_criteria_met': all(conditions.values()),
            'candidate_promoted': False, 'decision_limit': 'Separate root review required; never automatic app promotion.'}


def augment_gate(summary, details, rows, outputs):
    by_id = {r['id']: r for r in details}
    summary['invalid_output_fallback_abstentions'] = sum(not o['valid'] and not by_id[i]['accepted']
                                                        for i, o in outputs.items())
    summary['wrong_accepted_kinds'] = sum(r['accepted'] and r['actual'][0] != r['expected'][0] for r in details)
    summary['per_intent'] = {intent: {'rows': sum(r['semantic_intent'] == intent for r in rows),
        'correct': sum(r['semantic_intent'] == intent and by_id[r['id']]['correct'] for r in rows),
        'false_abstentions': sum(r['semantic_intent'] == intent and r['expected_kind'] != 'UNKNOWN' and not by_id[r['id']]['accepted'] for r in rows),
        'wrong_accepted': sum(r['semantic_intent'] == intent and by_id[r['id']]['accepted'] and not by_id[r['id']]['correct'] for r in rows)} for intent in sorted(shared.INTENTS)}


def describe_shared_capture(model):
    # The imported reader was written for two prompt arms; this experiment has one.
    model['timing_limit'] = ('Single host CPU original-prompt capture shared by both gates; warmed cache '
                             'and uncontrolled thermals/power. State cleared each request. '
                             'No phone/NPU or native-arm timing comparison.')
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--score-only', action='store_true')
    args = parser.parse_args()
    shared.SOURCE_COMMIT = args.source_commit
    shared.TASK = TASK  # Immutable reused function bodies, isolated output directory.
    shared.BUILD = BUILD
    work_budget()
    frozen = json.loads((CONFIRM / 'freeze-manifest.json').read_text())
    protocol = json.loads((CONFIRM / 'protocol.json').read_text())
    lock = json.loads((CONFIRM / 'selection-lock.json').read_text())
    candidate = DEV / 'ModelCommandGate.java'
    requests = CONFIRM / 'build/requests.tsv'
    cases = CONFIRM / 'build/cases.jsonl'
    checks = [(CONFIRM / 'protocol.json', 'protocol_sha256'),
              (CONFIRM / 'PROTOCOL.md', 'protocol_markdown_sha256'),
              (CONFIRM / 'selection-lock.json', 'selection_lock_sha256'),
              (CONFIRM / 'generate_data.py', 'generator_sha256'),
              (DEV / 'candidate.json', 'candidate_metadata_sha256'), (candidate, 'candidate_gate_sha256'),
              (cases, 'cases_sha256'), (requests, 'requests_sha256'),
              (TASK / 'run_evaluation.py', 'runner_sha256'), (TASK / 'Capture.java', 'capture_source_sha256'),
              (JSON_HELPER, 'json_helper_sha256'), (GATE_HELPER, 'gate_helper_sha256'),
              (shared.SEMANTIC_HELPER, 'semantic_helper_sha256'),
              (GATE_HELPER.parent / 'CommandGateEval.java', 'gate_harness_sha256')]
    paths = verify_frozen(frozen, checks, args.source_commit)
    required = {item['path'] for item in protocol['corpus']['overlap']['actual_available_required_sources']}
    required.update({'prototype/command-gate-v14-dev/ModelCommandGate.java',
                     'prototype/command-gate-v14-dev/CandidateGateTest.java',
                     'prototype/command-gate-v14-dev/build/requests.tsv'})
    if not required.issubset(paths):
        raise ValueError('Required prospective prior/example inventory absent')
    if lock['candidate_source_sha256'] != frozen['candidate_gate_sha256'] \
            or lock['candidate_metadata_sha256'] != frozen['candidate_metadata_sha256'] \
            or lock['candidate_parser_sha256'] != frozen['candidate_number_words_sha256'] \
            or lock['selected_source_sha256'] != frozen['selected_source_sha256'] \
            or lock['protocol_sha256'] != frozen['protocol_sha256'] \
            or lock['protocol_markdown_sha256'] != frozen['protocol_markdown_sha256']:
        raise ValueError('Pre-authoring candidate/protocol/source lock changed')
    rows = [shared.strict_json(line) for line in cases.read_text().splitlines()]
    validate_rows(rows, protocol)
    if requests.read_text() != ''.join(r['id'] + '\t' + r['utterance'] + '\n' for r in rows):
        raise ValueError('Ordered requests differ from frozen cases')
    derived = [CONFIRM / 'results.json', BUILD / 'paired-transitions.json']
    derived += [BUILD / (arm + '-' + route + '-' + suffix)
                for arm in ('baseline', 'candidate') for route in ('generated', 'oracle')
                for suffix in ('input.tsv', 'output.tsv', 'results.json')]
    if any(path.exists() for path in derived):
        raise ValueError('Existing derived evidence retained; no overwrite')
    BUILD.mkdir(exist_ok=args.score_only)
    source_snapshots(frozen, candidate)
    if not args.score_only:
        capture(requests, candidate, frozen, checks, args.source_commit)
    capture_metadata = shared.verified_capture_metadata('baseline', requests, candidate)
    if capture_metadata.get('model_adapter_sha256') != frozen['selected_source_sha256']['LocalModel.java']:
        raise ValueError('Original-prompt capture adapter identity mismatch')
    outputs, model = shared.read_capture('baseline', requests, rows, {}, candidate)
    describe_shared_capture(model)
    gate = load_module(GATE_HELPER, GATE_HELPER_SHA, 'v14_gate_shared')
    gate.BUILD = BUILD
    gate.subprocess = shared.BoundedSubprocess()
    gates = {}; details = {}; pairs = {}; paired_full = {}; transitions = {}
    for route, intents in [('generated', {i: output['intent'] for i, output in outputs.items()}),
                           ('oracle', {r['id']: r['oracle_intent'] for r in rows})]:
        gates[route] = {}; details[route] = {}
        for arm in ('baseline', 'candidate'):
            gates[route][arm], details[route][arm] = gate.evaluate_gate(rows, intents, arm, route)
            route_outputs = outputs if route == 'generated' else {i: {'intent': intent, 'valid': True} for i, intent in intents.items()}
            augment_gate(gates[route][arm], details[route][arm], rows, route_outputs)
        pairs[route] = gate.paired_gate(details[route]['baseline'], details[route]['candidate'])
        paired_full[route], transitions[route] = paired_summary(rows, outputs, outputs,
                        details[route]['baseline'], details[route]['candidate'])
    write_new(BUILD / 'paired-transitions.json', transitions)
    result = {'scope': 'Fresh frozen informed synthetic gate-only host confirmation; one unchanged original-prompt capture shared by both gates.',
              'research_only': True, 'model': model, 'gates': gates, 'paired': pairs,
              'paired_full': paired_full, 'promotion_review': promotion_review(gates, pairs, paired_full, model),
              'private_paired_transitions_sha256': sha(BUILD / 'paired-transitions.json'),
              'frozen_manifest': frozen, 'runner_source_commit': args.source_commit,
              'app_source_commit': APP_SOURCE, 'new_native_captures': 1,
              'raw_semantic_or_native_timing_arm_comparison': False,
              'binding_limit': 'Three referenced Homebrew library bytes; not entire OS or dynamically loaded backend closure.',
              'actions_executed': 0, 'training_performed': False, 'candidate_promoted': False}
    verify_frozen(frozen, checks, args.source_commit)
    source_snapshots(frozen, candidate)
    shared.verified_capture_metadata('baseline', requests, candidate)
    work_budget()
    write_new(CONFIRM / 'results.json', result)
    print(json.dumps({'model': {k: model[k] for k in ('semantic_correct', 'supported_correct', 'schema_and_eos_valid')},
                      'paired': pairs, 'promotion_review': result['promotion_review']}, indent=2))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    main()
