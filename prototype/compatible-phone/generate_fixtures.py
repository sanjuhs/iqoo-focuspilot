#!/usr/bin/env python3
"""Build ignored Android replay assets from already audited host captures, never validators."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MODES = ('baseline', 'checked_model', 'product_pipeline')
SOURCE_PATHS = {
    'ModelCommandGate': 'prototype/android/app/src/main/java/dev/focuspilot/prototype/ModelCommandGate.java',
    'CommandNumberWords': 'prototype/android/app/src/main/java/dev/focuspilot/prototype/CommandNumberWords.java',
    'StructuredCommand': 'prototype/structured-command/StructuredCommand.java',
    'UnitCommand': 'prototype/unit-command/UnitCommand.java',
    'CompatibleUnitCommand': 'prototype/compatible-unit/CompatibleUnitCommand.java',
}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def strict(text):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('Duplicate JSON key')
            out[key] = value
        return out
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def load(path):
    return strict(Path(path).read_text(encoding='utf-8'))


def canonical(value):
    if type(value) is not dict or value.get('intent') not in (
            'start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown'):
        raise ValueError('Invalid canonical intent')
    intent = value['intent']; keys = {'intent'}
    if intent in ('start_focus', 'timer'):
        keys.add('duration_seconds'); n = value.get('duration_seconds')
        if type(n) is not int or not (0 if intent == 'start_focus' else 1) <= n <= 7200:
            raise ValueError('Invalid canonical duration')
    elif intent == 'alarm':
        keys |= {'hour', 'minute'}
        if any(type(value.get(k)) is not int or not 0 <= value[k] <= cap
               for k, cap in (('hour', 23), ('minute', 59))):
            raise ValueError('Invalid canonical alarm')
    elif intent == 'open_app':
        keys.add('app')
        if value.get('app') not in ('settings', 'calculator', 'clock'):
            raise ValueError('Invalid canonical app')
    if set(value) != keys:
        raise ValueError('Unexpected canonical slot')
    return value


def ignored_new(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT) or path.exists():
        raise ValueError('New project-local ignored output required')
    if subprocess.run(['git', 'check-ignore', '-q', str(path)], cwd=ROOT).returncode:
        raise ValueError('Raw fixtures/output must be ignored by Git')
    return path


def build(gold_path, baseline_dir, candidate_dir, scoring_dir, audit_path, sources):
    """All expectations come from audited decisions. No target or host gate is called."""
    gold_path = Path(gold_path); scoring_dir = Path(scoring_dir); audit_path = Path(audit_path)
    audit = load(audit_path); result_path = scoring_dir / 'result.json'; result = load(result_path)
    if audit.get('verified') is not True or audit.get('actual_result_sha256') != sha(result_path):
        raise ValueError('Actual result is not bound by successful independent audit')
    if result.get('gold_sha256') != sha(gold_path) or result.get('rows') != 100:
        raise ValueError('Frozen 100-row gold identity differs')
    bindings = audit['files_sha256']; pins = {}
    def pin(path, audited=True):
        path = Path(path).resolve(); digest = sha(path)
        key = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        if audited and bindings.get(key) != digest:
            raise ValueError('Input not bound by independent audit: ' + key)
        pins[key] = digest
        return digest
    pin(gold_path); pin(result_path, False); pin(audit_path, False)
    rows = [strict(line) for line in gold_path.read_text(encoding='utf-8').splitlines()]
    ids = [r['id'] for r in rows]
    if len(ids) != 100 or len(set(ids)) != 100 or any(not re.fullmatch('[a-z0-9_]{1,100}', i) for i in ids):
        raise ValueError('Exact unique bounded fixture IDs required')
    captures = {}
    for arm, directory in (('baseline', baseline_dir), ('candidate', candidate_dir)):
        directory = Path(directory); raw_path = directory / 'raw.jsonl'; pin(raw_path)
        process = load(directory / 'process.json'); pin(directory / 'process.json')
        if process.get('exit_code') != 0 or process.get('timed_out') is not False or process.get('raw_sha256') != sha(raw_path):
            raise ValueError('Capture did not complete with matching raw identity')
        raw = [strict(s) for s in raw_path.read_text(encoding='utf-8').splitlines()]
        if not raw or raw[0].get('phase') != 'load' or [r['id'] for r in raw[1:]] != ids:
            raise ValueError('Capture inventory differs')
        if any(r['metrics'].get('reached_eos') is not True or r['metrics'].get('capture_enabled') is not False for r in raw[1:]):
            raise ValueError('Actual EOS/capture-off required')
        captures[arm] = {r['id']: r['text'] for r in raw[1:]}
    details = {}
    for mode in MODES:
        path = scoring_dir / (mode + '-details.json'); pin(path); values = load(path)
        if [r['id'] for r in values] != ids:
            raise ValueError('Decision inventory differs')
        details[mode] = values
    source_hashes = {name: pin(path) for name, path in sources.items() if name not in ('CompatibleActionRouter', 'CompatibleReviewState')}
    for name in ('CompatibleActionRouter', 'CompatibleReviewState'):
        if name in sources:
            source_hashes[name] = pin(sources[name], False)
    fixtures = []
    for index, row in enumerate(rows):
        request = row['utterance']
        if type(request) is not str or not 0 < len(request.encode('utf-16-le')) // 2 <= 500:
            raise ValueError('Bounded inert request required')
        expected = {}
        for mode in MODES:
            decision = details[mode][index]; proposal = canonical(decision['proposal'])
            if decision['gold'] != canonical(row['expected']) or type(decision['accepted']) is not bool:
                raise ValueError('Audited gold/acceptance differs')
            raw = strict(captures['baseline' if mode == 'baseline' else 'candidate'][row['id']])
            if decision['raw'] != raw:
                raise ValueError('Decision raw response differs from actual capture')
            origin = decision['origin']
            if origin not in ('FAST_LOCAL_REQUEST', 'CHECKED_MODEL', 'UNKNOWN') or (origin == 'UNKNOWN') != (not decision['accepted']):
                raise ValueError('Audited proposal origin differs')
            expected[mode] = {'proposal': proposal, 'accepted': decision['accepted'], 'origin': origin}
        fixtures.append({'id': row['id'], 'request': request, 'gold': canonical(row['expected']),
                         'baseline_response': captures['baseline'][row['id']],
                         'candidate_response': captures['candidate'][row['id']], 'expected': expected})
    payload = {'schema': 'focuspilot.compatible_replay_fixtures.v1', 'host_source_commit': result['source_commit'],
               'rows': 100, 'replay_checks': 300, 'source_sha256': source_hashes, 'input_sha256': pins,
               'fixtures': fixtures}
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n'
    if len(text.encode()) > 1_000_000:
        raise ValueError('Fixture payload too large')
    manifest = {'schema': 'focuspilot.compatible_replay_asset_manifest.v1', 'rows': 100,
                'replay_checks': 300, 'host_source_commit': result['source_commit'],
                'asset_sha256': hashlib.sha256(text.encode()).hexdigest(), 'asset_bytes': len(text.encode()),
                'generator_sha256': sha(Path(__file__)), 'source_sha256': source_hashes, 'input_sha256': pins,
                'scope': 'Already-seen synthetic host captures replayed through target pure Java; no new inference or accuracy sample'}
    return text, manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('gold', 'baseline', 'candidate', 'scoring', 'audit', 'output', 'manifest'):
        p.add_argument('--' + key, required=True, type=Path)
    p.add_argument('--router-source', type=Path)
    p.add_argument('--review-source', type=Path)
    a = p.parse_args(); out = ignored_new(a.output); manifest = ignored_new(a.manifest)
    sources = {k: ROOT / v for k, v in SOURCE_PATHS.items()}
    if bool(a.router_source) != bool(a.review_source):
        p.error('Both review-state source identities are required together')
    if a.router_source:
        sources.update(CompatibleActionRouter=a.router_source, CompatibleReviewState=a.review_source)
    text, record = build(a.gold, a.baseline, a.candidate, a.scoring, a.audit, sources)
    out.parent.mkdir(parents=True, exist_ok=True); manifest.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as f: f.write(text)
    with manifest.open('x', encoding='utf-8') as f: json.dump(record, f, indent=2); f.write('\n')
    print(json.dumps({'rows': 100, 'replay_checks': 300, 'asset_sha256': record['asset_sha256']}))

if __name__ == '__main__': main()
