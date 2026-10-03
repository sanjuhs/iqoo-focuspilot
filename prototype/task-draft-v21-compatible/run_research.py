"""Frozen, single-attempt Qwen task-guidance experiment; no Android or tools."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = HERE / 'build'
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
MODEL = ROOT / 'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
NATIVE = ROOT / 'prototype/command-eval/build/native/libfocuspilot_local.dylib'
MODEL_SHA = '57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
NATIVE_SHA = 'ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def encoded(text):
    return base64.b64encode(text.encode()).decode()


def run_java(mode, path, **kwargs):
    args = [str(JAVA / 'java'), '-Djava.library.path=' + str(NATIVE.parent),
            '-cp', str(BUILD / 'java'), 'dev.focuspilot.prototype.TaskDraftEval', mode]
    if mode == 'capture':
        args.append(str(MODEL))
    return subprocess.run(args + [str(path)], check=True, **kwargs)


def storage():
    # Logical bytes include ignored artifacts and Git, with known new global cache growth.
    project = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())
    value = {'project_bytes': project, 'new_global_cache_bytes': 218929328,
             'effective_bytes': project + 218929328, 'reservation_bytes': 32000000,
             'limit_bytes': 15000000000}
    if value['effective_bytes'] + value['reservation_bytes'] > value['limit_bytes']:
        raise ValueError('Strict storage budget exceeded')
    return value


def compile_java():
    (BUILD / 'java').mkdir(parents=True, exist_ok=True)
    subprocess.run([str(JAVA / 'javac'), '-d', str(BUILD / 'java'),
                    *map(str, sorted((HERE / 'reference').glob('*.java'))),
                    str(HERE / 'TaskDraftEval.java'), str(HERE / 'TaskDraftBoundaryChecks.java')], check=True)


def freeze():
    if (HERE / 'freeze-manifest.json').exists() or (BUILD / 'output.tsv').exists():
        raise ValueError('Already frozen or attempted; use a new experiment')
    if sha(MODEL) != MODEL_SHA or sha(NATIVE) != NATIVE_SHA:
        raise ValueError('Pinned model/native differs')
    rows = json.loads((HERE / 'cases.json').read_text())
    ids = [r['id'] for r in rows]
    if len(ids) != 32 or len(set(ids)) != len(ids):
        raise ValueError('Require 32 distinct cases')
    if {k: sum(r['kind'] == k for r in rows) for k in ['benign', 'constraint', 'tricky']} != {'benign': 20, 'constraint': 8, 'tricky': 4}:
        raise ValueError('Frozen cohort count differs')
    old_goals = set()
    for sibling in ['task-draft-research', 'task-draft-confirm']:
        old = ROOT / 'prototype' / sibling / 'build/cases.json'
        old_goals.update(' '.join(r['goal'].lower().split()) for r in json.loads(old.read_text()))
    goals = [' '.join(r['goal'].lower().split()) for r in rows]
    if len(set(goals)) != len(goals) or set(goals) & old_goals:
        raise ValueError('Goal duplicates or previous cohort overlap')
    if any(not r['goal'].strip() or len(r['goal'].encode('utf-16-le')) // 2 > 120 for r in rows):
        raise ValueError('Goal bounds differ')
    compile_java()
    (BUILD / 'input.tsv').write_text(''.join(r['id'] + '\t' + encoded(r['goal']) + '\n' for r in rows))
    inventory = run_java('inventory', BUILD / 'input.tsv', capture_output=True, text=True, timeout=30).stdout
    (BUILD / 'inventory.tsv').write_text(inventory)
    rendered = {}
    for line in inventory.splitlines():
        key, data = line.split('\t')
        rendered[key] = hashlib.sha256(base64.b64decode(data)).hexdigest()
    if set(rendered) != set(ids) | {'GRAMMAR'}:
        raise ValueError('Rendered prompt inventory differs')
    dependencies = json.loads((ROOT / 'prototype/task-draft-confirm/native-dependencies.json').read_text())
    for dep in dependencies['dependencies']:
        if sha(dep['link_path']) != dep['sha256']:
            raise ValueError('Existing native dependency changed')
    write(HERE / 'native-dependencies.json', dependencies | {'scope': 'Existing installed dependency identities verified before this capture; no backend-use claim from inventory'})
    sources = [HERE / p for p in ['run_research.py', 'TaskDraftEval.java', 'cases.json', 'protocol.json', 'native-dependencies.json', 'TaskDraftBoundaryChecks.java']]
    sources += sorted((HERE / 'reference').glob('*.java'))
    write(HERE / 'freeze-manifest.json', {
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'frozen_before_inference': True, 'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'files': {str(p.relative_to(HERE)): sha(p) for p in sources},
        'model_sha256': MODEL_SHA, 'native_sha256': NATIVE_SHA,
        'input_sha256': sha(BUILD / 'input.tsv'), 'rendered_sha256': rendered,
        'storage': storage(), 'old_normalized_goal_overlap': 0,
        'deadlines': {'per_request_native_cancel_seconds': 30, 'overall_child_timeout_seconds': 600, 'attempts_per_case': 1},
        'limits': 'Informed synthetic qualitative study, host CPU only, no actions/training/phone/NPU or general accuracy'})
    print('Frozen source, cases, criteria, rendered prompts, runtime and storage before inference.')


def verify(runtime=True):
    f = json.loads((HERE / 'freeze-manifest.json').read_text())
    for p, digest in f['files'].items():
        if sha(HERE / p) != digest:
            raise ValueError('Frozen file changed: ' + p)
    if runtime:
        if sha(MODEL) != f['model_sha256'] or sha(NATIVE) != f['native_sha256']:
            raise ValueError('Model/native differs')
        for dep in json.loads((HERE / 'native-dependencies.json').read_text())['dependencies']:
            if sha(dep['link_path']) != dep['sha256']:
                raise ValueError('Dependency differs')
        compile_java()
        if sha(BUILD / 'input.tsv') != f['input_sha256']:
            raise ValueError('Input differs')
        actual = run_java('inventory', BUILD / 'input.tsv', capture_output=True, text=True, timeout=30).stdout
        hashes = {line.split('\t')[0]: hashlib.sha256(base64.b64decode(line.split('\t')[1])).hexdigest() for line in actual.splitlines()}
        if hashes != f['rendered_sha256']:
            raise ValueError('Rendered prompt/grammar differs')
    return f


def capture():
    verify()
    storage()
    # Marker created before process startup; startup failures cannot authorize a silent rerun.
    write(BUILD / 'capture-attempt.json', {'started_utc': datetime.now(timezone.utc).isoformat(), 'freeze_sha256': sha(HERE / 'freeze-manifest.json')})
    started = time.perf_counter()
    with (BUILD / 'output.tsv').open('x') as out, (BUILD / 'stderr.log').open('x') as err:
        args = [str(JAVA / 'java'), '-Djava.library.path=' + str(NATIVE.parent), '-cp', str(BUILD / 'java'),
                'dev.focuspilot.prototype.TaskDraftEval', 'capture', str(MODEL), str(BUILD / 'input.tsv')]
        process = None
        timeout = False
        failure = None
        code = None
        try:
            process = subprocess.Popen(args, stdout=out, stderr=err)
            write(BUILD / 'live-process.json', {'pid': process.pid})
            print('Live host JNI capture pid=' + str(process.pid), flush=True)
            try:
                code = process.wait(timeout=600)
            except subprocess.TimeoutExpired:
                timeout = True
        except BaseException as error:
            failure = type(error).__name__
            raise
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                code = process.wait()
            out.flush()
            err.flush()
            write(BUILD / 'process-result.json', {'exit_code': code, 'timed_out': timeout,
                  'wrapper_failure_type': failure, 'wall_seconds': time.perf_counter() - started,
                  'output_sha256': sha(BUILD / 'output.tsv'), 'stderr_sha256': sha(BUILD / 'stderr.log')})
    print('Capture terminal, exit=' + str(code), flush=True)


def summarize():
    verify()
    process = json.loads((BUILD / 'process-result.json').read_text())
    if sha(BUILD / 'output.tsv') != process['output_sha256'] or sha(BUILD / 'stderr.log') != process['stderr_sha256']:
        raise ValueError('Raw capture changed')
    rows = json.loads((HERE / 'cases.json').read_text())
    outputs = {}
    load = None
    for line in (BUILD / 'output.tsv').read_text().splitlines():
        fields = line.split('\t')
        if fields[0] == 'LOAD':
            if load is not None:
                raise ValueError('Multiple model loads')
            load = int(fields[1]) / 1e6
            continue
        key, elapsed, status, data = fields
        if key in outputs or key not in {r['id'] for r in rows}:
            raise ValueError('Unknown/duplicate capture case')
        v = {'elapsed_ms': int(elapsed) / 1e6, 'status': status, 'raw': base64.b64decode(data).decode()}
        if status == 'OK':
            v['outer'] = json.loads(v['raw'])
        outputs[key] = v
    (BUILD / 'parser-input.tsv').write_text(''.join(k + '\t' + encoded(v['outer']['text']) + '\n' for k, v in outputs.items() if v['status'] == 'OK'))
    parsed = dict(line.split('\t') for line in run_java('validate', BUILD / 'parser-input.tsv', capture_output=True, text=True, timeout=30).stdout.splitlines())
    for key, value in outputs.items():
        value['schema_verdict'] = parsed.get(key, 'INVALID')
        value['completed'] = value['status'] == 'OK' and value['outer']['metrics']['reached_eos'] is True and value['schema_verdict'] != 'INVALID'
    write(BUILD / 'captured-details.json', outputs)
    metrics = [v['outer']['metrics'] for v in outputs.values() if v['status'] == 'OK']
    complete_capture = (process['exit_code'] == 0 and not process['timed_out']
                        and process['wrapper_failure_type'] is None and load is not None
                        and set(outputs) == {r['id'] for r in rows})
    write(HERE / 'results.json', {
        'complete_capture': complete_capture,
        'expected': len(rows), 'captured': len(outputs), 'completed_eos_and_schema': sum(v['completed'] for v in outputs.values()),
        'explicit_declines': sum(v['completed'] and v['schema_verdict'] == 'DECLINE' for v in outputs.values()),
        'valid_plan_shapes': sum(v['completed'] and v['schema_verdict'].startswith('PLAN_') for v in outputs.values()),
        'model_load_ms': load, 'native_median_ms': statistics.median(m['total_ms'] for m in metrics) if metrics else None,
        'cpu_only_all_true': bool(metrics) and all(m['cpu_only'] is True for m in metrics),
        'capture_disabled_all': bool(metrics) and all(m['capture_enabled'] is False for m in metrics),
        'activations_empty_all': all(not v['outer']['activations'] for v in outputs.values() if v['status'] == 'OK'),
        'process': process, 'details_sha256': sha(BUILD / 'captured-details.json'), 'freeze_sha256': sha(HERE / 'freeze-manifest.json'),
        'qualitative_review': 'Pending; EOS/schema are not evidence of useful guidance', 'actions_executed': 0,
        'scope': 'One informed synthetic host CPU feasibility experiment; selected phone app unchanged'})
    print(json.dumps(json.loads((HERE / 'results.json').read_text())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['freeze', 'verify', 'capture', 'summarize'])
    mode = parser.parse_args().mode
    {'freeze': freeze, 'verify': lambda: print(json.dumps(verify())), 'capture': capture, 'summarize': summarize}[mode]()
