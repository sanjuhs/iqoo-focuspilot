"""Freeze fresh informed synthetic requests against opaque exclusions; no inference.

This author-facing tool never opens the new candidate grammar or candidate tests.
The parent owns candidate inspection, opaque exclusion creation and source freeze.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BUILD = TASK / 'build'
EVAL = ROOT / 'prototype/qwen-natural-eval'
OLD_VALIDATOR = ROOT / 'prototype/qwen-balanced-data/generate_data.py'
GENERIC_DEPENDENCIES = (OLD_VALIDATOR,
    ROOT / 'prototype/command-gate-v14-confirm/generate_data.py',
    ROOT / 'prototype/qwen-balanced-data/test_data.py')
spec = importlib.util.spec_from_file_location('old_author_contract', OLD_VALIDATOR)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
strict_json, normalize, sha = old.strict_json, old.normalize, old.sha
NORMALIZATION = 'ascii-alnum-lower-v1'
HASH_FIELDS = ('normalized_request_sha256', 'exact_request_sha256', 'family_sha256', 'template_sha256')
SOURCE_FILES = ('generate_data.py', 'test_data.py', 'README.md')


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read_rows(path):
    return [strict_json(line) for line in Path(path).read_text().splitlines() if line.strip()]


def validate_protocol(protocol):
    if protocol.get('schema') != 'focuspilot.natural_gate_protocol.v1' or protocol.get('candidate_source_freeze_before_authoring') is not True:
        raise ValueError('Prospective source-before-authoring protocol required')
    contract = protocol['fresh_cohort']
    if contract['rows'] != 100 or contract['families'] != 50 or contract['rows_per_family'] != 2 or contract['supported'] != 50 or contract['unknown'] != 50:
        raise ValueError('Fixed 100-row reciprocal cohort required')
    if contract['counts'] != old.COUNTS['confirmation']:
        raise ValueError('Exact prospective intent counts required')
    if contract['approved_apps'] != dict.fromkeys(('OPEN_SETTINGS', 'OPEN_CALCULATOR', 'OPEN_CLOCK'), 2):
        raise ValueError('Exact approved-app target counts required')
    if set(contract['unknown_boundaries']) != old.BOUNDARIES:
        raise ValueError('All twelve required unknown boundaries required')
    if set(contract['hard_minimums']) != old.HARD_TAGS or any(type(n) is not int or n < 1 for n in contract['hard_minimums'].values()):
        raise ValueError('Prospective hard-case minimums required')
    return contract


def validate_rows(rows, protocol):
    contract = validate_protocol(protocol)
    # Reuse only the old generic author contract, never its inventory rescanner.
    old.validate_rows(rows, 'confirmation')
    for row in rows:
        if len(row['id']) > 64 or len(row['utterance'].encode('utf-16-le')) // 2 > 500:
            raise ValueError('Native/Android bounded ID and UTF-16 request required')
        if 'midnight_noon' in row['hard_tags'] and (row['hour'], row['minute']) not in {(0, 0), (12, 0)}:
            raise ValueError('Noon/midnight tags require the exact meridian, not only its hour')
    if Counter(r['intent'] for r in rows) != contract['counts']:
        raise ValueError('Prospective class counts differ')
    for tag, minimum in contract['hard_minimums'].items():
        if sum(tag in r['hard_tags'] for r in rows) < minimum:
            raise ValueError('Missing protocol hard-case minimum: ' + tag)
    return rows


def validate_exclusions(bundle):
    if bundle.get('schema') != 'focuspilot.natural_exclusion.v1' or bundle.get('normalization') != NORMALIZATION:
        raise ValueError('Exact opaque exclusion schema and normalization required')
    if not isinstance(bundle.get('source_commit'), str) or not re.fullmatch('[0-9a-f]{40}', bundle['source_commit']):
        raise ValueError('Full inventory provenance commit required')
    for name in HASH_FIELDS:
        values = bundle.get(name)
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not re.fullmatch('[0-9a-f]{64}', v) for v in values) or values != sorted(set(values)):
            raise ValueError('Sorted unique nonempty opaque hashes required: ' + name)
    entries = bundle.get('inventory')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Opaque source inventory metadata required')
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or Path(item['path']).is_absolute() or '..' in Path(item['path']).parts:
            raise ValueError('Project-relative inventory path required')
        if not isinstance(item.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']) or type(item.get('text_count')) is not int or item['text_count'] < 0 or not isinstance(item.get('method'), str):
            raise ValueError('Source hashes/extraction counts/methods required')
    return bundle


def reject_excluded(rows, bundle):
    validate_exclusions(bundle)
    excluded = {key: set(bundle[key]) for key in HASH_FIELDS}
    collisions = []
    for row in rows:
        checks = {'normalized_request_sha256': digest(normalize(row['utterance'])),
                  'exact_request_sha256': digest(row['utterance']),
                  'family_sha256': digest(row['family']),
                  'template_sha256': digest(row['template_id'])}
        if any(value in excluded[key] for key, value in checks.items()):
            collisions.append(row['id'])
    if collisions:
        # Never reveal excluded candidate fixture strings; only report author's IDs.
        raise ValueError('Opaque prior/development exclusion collision IDs: ' + ','.join(collisions))


def verify_authorization(commit, source_freeze, exclusions):
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Full explicitly authorized source-freeze commit required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=ROOT,
                   check=True, capture_output=True, timeout=10)
    source_freeze, exclusions = Path(source_freeze).resolve(), Path(exclusions).resolve()
    if source_freeze != (EVAL / 'source-freeze.json').resolve() or exclusions != (EVAL / 'novelty-exclusions.json').resolve():
        raise ValueError('Parent-owned fixed metadata paths required')
    frozen = strict_json(source_freeze.read_text())
    bindings = frozen.get('files_sha256')
    if not isinstance(bindings, dict) or not bindings or any(not isinstance(k, str) or Path(k).is_absolute() or '..' in Path(k).parts or not isinstance(v, str) or not re.fullmatch('[0-9a-f]{64}', v) for k, v in bindings.items()):
        raise ValueError('Project-relative full source binding map required')
    if not any(k.startswith('prototype/qwen-natural-validation/') and k.endswith('.java') for k in bindings):
        raise ValueError('Parent candidate source bindings required')
    readable = [EVAL / 'protocol.json', EVAL / 'design-lock.json', exclusions,
                *(TASK / name for name in SOURCE_FILES), *GENERIC_DEPENDENCIES]
    for path in readable:
        relative = str(path.relative_to(ROOT))
        if relative not in bindings or sha(path) != bindings[relative]:
            raise ValueError('Readable frozen source binding missing/changed: ' + relative)
    # Compare only metadata/our generic sources/old generic utilities with Git.
    # Candidate bytes remain completely outside this author process.
    for path in [source_freeze, *readable]:
        relative = str(path.relative_to(ROOT))
        committed = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=ROOT, timeout=10)
        if committed != path.read_bytes():
            raise ValueError('Source differs from authoring authorization commit: ' + relative)
    return frozen


def freeze(commit, author_path=None):
    exclusions_path, source_freeze = EVAL / 'novelty-exclusions.json', EVAL / 'source-freeze.json'
    verify_authorization(commit, source_freeze, exclusions_path)
    protocol_path = EVAL / 'protocol.json'
    protocol, bundle = strict_json(protocol_path.read_text()), strict_json(exclusions_path.read_text())
    author_path = Path(author_path) if author_path else BUILD / 'author-confirmation.jsonl'
    if author_path.resolve().parent != BUILD.resolve():
        raise ValueError('Author requests must remain ignored direct build/ inputs')
    rows = validate_rows(read_rows(author_path), protocol)
    reject_excluded(rows, bundle)
    outputs = [BUILD / 'confirmation.jsonl', BUILD / 'confirmation-requests.tsv', TASK / 'corpus-manifest.json']
    if any(path.exists() for path in outputs):
        raise ValueError('Frozen corpus/manifest already exists; preserve every attempt')
    raw = ''.join(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows).encode()
    tsv = ''.join(row['id'] + '\t' + row['utterance'] + '\n' for row in rows).encode()
    manifest = {'schema': 'focuspilot.natural_corpus.v1', 'author_informed_not_blind': True,
        'candidate_grammar_and_tests_read_by_author': False, 'synthetic_only': True,
        'model_gate_oracle_calls': 0, 'oracle_filtered': False, 'before_outputs': True,
        'source_authorization_commit': commit, 'source_freeze_sha256': sha(source_freeze),
        'protocol_sha256': sha(protocol_path), 'exclusion_bundle_sha256': sha(exclusions_path),
        'generic_source_sha256': {name: sha(TASK / name) for name in SOURCE_FILES},
        'generic_dependencies_sha256': {str(p.relative_to(ROOT)): sha(p) for p in GENERIC_DEPENDENCIES},
        'author_input_sha256': sha(author_path), 'rows': len(rows),
        'families': len({r['family'] for r in rows}), 'by_intent': dict(Counter(r['intent'] for r in rows)),
        'approved_app_counts': dict(Counter(r['expected_kind'] for r in rows if r['intent'] == 'open_app')),
        'hard_tag_counts': dict(Counter(tag for r in rows for tag in r['hard_tags'])),
        'unknown_boundary_counts': dict(Counter(r['boundary_family'] for r in rows if r['intent'] == 'unknown')),
        'reserved_chat_control_requests': sum('<|' in r['utterance'] or '|>' in r['utterance'] for r in rows),
        'jsonl_sha256': hashlib.sha256(raw).hexdigest(), 'requests_sha256': hashlib.sha256(tsv).hexdigest(),
        'opaque_exclusion_counts': {key: len(bundle[key]) for key in HASH_FIELDS},
        'exclusion_inventory': bundle['inventory'],
        'family_rule': 'Author manually assigns reciprocal complete wording families; no row/random split',
        'normalization': NORMALIZATION,
        'limitations': ['Informed synthetic author; no blind or population estimate',
                        'Opaque exact/normalized exclusions and prior family IDs do not prove semantic independence',
                        'Manual expected slots are not derived from model, validator or oracle']}
    for path, payload in zip(outputs[:2], (raw, tsv)):
        with path.open('xb') as f: f.write(payload)
    with outputs[2].open('x') as f: json.dump(manifest, f, sort_keys=True, indent=2); f.write('\n')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--authorization-commit', required=True)
    p.add_argument('--author-input')
    a = p.parse_args()
    result = freeze(a.authorization_commit, a.author_input)
    print(json.dumps({key: result[key] for key in ('rows', 'families', 'by_intent', 'jsonl_sha256', 'requests_sha256')}, indent=2))
