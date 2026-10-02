"""Freeze manually labelled synthetic data without models, gates or oracle filtering.

Author JSONL belongs exclusively to ignored build/. This source stores the design,
validation and inventory machinery, not the actual authored requests.
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
UTILITY = ROOT / 'prototype/command-gate-v14-confirm/generate_data.py'
spec = importlib.util.spec_from_file_location('previous_inventory', UTILITY)
inventory_util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory_util)
sha = inventory_util.sha
strict_json = inventory_util.strict_json
normalize = inventory_util.normalize
KINDS = inventory_util.KINDS
INTENTS = ('start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown')
FIELDS = {'id', 'family', 'template_id', 'utterance', 'intent', 'expected_kind',
          'hour', 'minute', 'seconds', 'hard_tags', 'boundary_family',
          'counterpart_id', 'oracle_intent'}
COUNTS = {'train': dict.fromkeys(INTENTS, 16),
          'development': dict.fromkeys(INTENTS, 2),
          'confirmation': dict(zip(INTENTS, (10, 8, 8, 10, 6, 8, 50)))}
BOUNDARIES = {'negation', 'compound', 'payment', 'message', 'deletion',
              'unsupported', 'suffix', 'injection', 'conditional', 'quoted',
              'invalid_slot', 'malformed_slot'}
HARD_TAGS = {'pause_preservation', 'current_or_spoken_focus_pause', 'resume_vs_start',
             'spoken_number', 'duration_boundary', 'nudge_cause', 'midnight_noon'}


def read_rows(path):
    return [strict_json(line) for line in Path(path).read_text().splitlines() if line.strip()]


def validate_rows(rows, split):
    if split not in COUNTS or Counter(r.get('intent') for r in rows) != COUNTS[split]:
        raise ValueError('Exact prospectively specified class counts required')
    ids = set()
    for r in rows:
        if set(r) != FIELDS:
            raise ValueError('Exact shared schema required')
        for key in ('id', 'family', 'template_id'):
            if not isinstance(r[key], str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}', r[key]):
                raise ValueError('Bounded identifier required')
        if r['id'] in ids:
            raise ValueError('Duplicate row ID')
        ids.add(r['id'])
        text = r['utterance']
        if not isinstance(text, str) or not text.strip() or len(text) > 500 or any(ord(c) < 32 or ord(c) == 127 or c in '\u2028\u2029' for c in text):
            raise ValueError('Single bounded request required')
        kind = r['expected_kind']
        if kind not in KINDS or KINDS[kind] != r['intent'] or r['oracle_intent'] not in INTENTS:
            raise ValueError('Manual semantic/action labels disagree')
        if kind != 'UNKNOWN' and r['oracle_intent'] != r['intent']:
            raise ValueError('Supported oracle domain must match semantic label')
        if any(type(r[k]) is not int for k in ('hour', 'minute', 'seconds')):
            raise ValueError('Integer slots, not bool, required')
        h, m, s = (r[k] for k in ('hour', 'minute', 'seconds'))
        if kind == 'ALARM':
            good = 0 <= h <= 23 and 0 <= m <= 59 and s == 0
        elif kind in {'START_FOCUS', 'TIMER'}:
            good = h == m == 0 and (0 <= s <= 7200 if kind == 'START_FOCUS' else 1 <= s <= 7200)
        else:
            good = (h, m, s) == (0, 0, 0)
        if not good:
            raise ValueError('Invalid manually specified slots')
        tags = r['hard_tags']
        if not isinstance(tags, list) or any(t not in HARD_TAGS for t in tags) or len(set(tags)) != len(tags):
            raise ValueError('Known unique tags required')
        if ('pause_preservation' in tags) != (kind == 'PAUSE_FOCUS'):
            raise ValueError('Every and only Pause needs preservation tag')
        if 'current_or_spoken_focus_pause' in tags and kind != 'PAUSE_FOCUS':
            raise ValueError('Pause tag on another class')
        if 'resume_vs_start' in tags and kind != 'START_FOCUS':
            raise ValueError('Resume tag on another class')
        if 'nudge_cause' in tags and kind != 'EXPLAIN':
            raise ValueError('Nudge tag on another class')
        if 'duration_boundary' in tags and (kind not in {'START_FOCUS', 'TIMER'} or s not in {1, 7200}):
            raise ValueError('Endpoint tag disagrees with slots')
        if 'midnight_noon' in tags and (kind != 'ALARM' or h not in {0, 12}):
            raise ValueError('Meridian tag disagrees with slots')
        if kind == 'UNKNOWN':
            if tags or r['boundary_family'] not in BOUNDARIES:
                raise ValueError('Unknown boundary must be manually identified')
        elif r['boundary_family']:
            raise ValueError('Supported request has boundary label')
        if split != 'confirmation' and r['counterpart_id']:
            raise ValueError('Only confirmation uses reciprocal pairs')
    inventory_util.reject_overlap(rows, [])
    family_rows = {}
    for r in rows:
        family_rows.setdefault(r['family'], []).append(r)
    if any(len({r['template_id'] for r in group}) != 1 for group in family_rows.values()):
        raise ValueError('Each family must retain its authored template identity')
    if len({group[0]['template_id'] for group in family_rows.values()}) != len(family_rows):
        raise ValueError('Different families cannot alias one template identity')
    if split != 'confirmation':
        if any(len(group) != 2 or len({r['intent'] for r in group}) != 1 for group in family_rows.values()):
            raise ValueError('Train/dev families contain two same-class variants')
        if Counter(group[0]['intent'] for group in family_rows.values()) != dict.fromkeys(INTENTS, 8 if split == 'train' else 1):
            raise ValueError('Required independently authored families per class')
    else:
        by_id = {r['id']: r for r in rows}
        if len(family_rows) != 50 or any(len(group) != 2 for group in family_rows.values()):
            raise ValueError('Fifty two-row confirmation families required')
        for r in rows:
            other = by_id.get(r['counterpart_id'])
            if other is None or other['counterpart_id'] != r['id'] or other['family'] != r['family'] or (r['intent'] == 'unknown') == (other['intent'] == 'unknown'):
                raise ValueError('Reciprocal supported/unknown family pair required')
        targets = Counter(r['expected_kind'] for r in rows if r['intent'] == 'open_app')
        if targets != dict.fromkeys(('OPEN_SETTINGS', 'OPEN_CALCULATOR', 'OPEN_CLOCK'), 2):
            raise ValueError('Approved app target counts required')
        minimum = {'pause_preservation': 8, 'current_or_spoken_focus_pause': 4,
                   'resume_vs_start': 2, 'spoken_number': 8, 'duration_boundary': 4,
                   'nudge_cause': 4, 'midnight_noon': 2}
        for tag, count in minimum.items():
            if sum(tag in r['hard_tags'] for r in rows) < count:
                raise ValueError('Missing predeclared hard coverage: ' + tag)
        present = {r['boundary_family'] for r in rows if r['intent'] == 'unknown'}
        if not BOUNDARIES <= present:
            raise ValueError('Missing predeclared unknown boundary family')
    return rows


def validate_disjoint(splits):
    seen_families, seen_templates, previous = set(), set(), []
    for name, rows in splits.items():
        validate_rows(rows, name)
        families = {r['family'] for r in rows}
        templates = {r['template_id'] for r in rows}
        if families & seen_families or templates & seen_templates:
            raise ValueError('Cross-split authored family/template reuse')
        inventory_util.reject_overlap(rows, previous)
        seen_families.update(families)
        seen_templates.update(templates)
        previous.extend(r['utterance'] for r in rows)


def inventory_sources():
    old = strict_json((ROOT / 'prototype/command-gate-v14-confirm/protocol.json').read_text())
    required = {ROOT / p['path'] for p in old['corpus']['overlap']['actual_available_required_sources']}
    if any(not p.is_file() for p in required):
        raise ValueError('Previously known mandatory exposed inventory missing')
    paths = set(required)
    # All actual prior author attempts, frozen requests and training splits. No model output.
    names = {'train.jsonl', 'valid.jsonl', 'validation.jsonl', 'heldout.jsonl', 'all-cases.jsonl'}
    for folder in (ROOT / 'prototype').glob('*'):
        if folder == TASK or folder.name.startswith('qwen-balanced-'):
            continue
        for p in folder.rglob('*'):
            if p.is_file() and (p.name in names or (p.suffix == '.jsonl' and ('author' in p.name or p.name == 'cases.jsonl')) or p.name.endswith('requests.tsv')):
                paths.add(p)
        for p in folder.glob('test*.py'):
            paths.add(p)
    for folder in ('main', 'test', 'androidTest'):
        paths.update((ROOT / ('prototype/android/app/src/' + folder)).rglob('*.java'))
    for folder in ('command-gate-v14-dev', 'command-gate-v14-runner'):
        paths.update((ROOT / 'prototype' / folder).glob('*.java'))
        paths.update((ROOT / 'prototype' / folder).glob('test*.py'))
    paths.update(TASK.glob('test*.py'))
    inventory, requests = [], []
    for p in sorted(paths):
        values, method = inventory_util.extract_requests(p)
        requests.extend(values)
        inventory.append({'path': str(p.relative_to(ROOT)), 'sha256': sha(p),
                          'text_count': len(values), 'method': method,
                          'previous_required': p in required})
    return inventory, requests


def verify_design_commit(commit):
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Full parent-authorized design-lock commit required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=ROOT,
                   check=True, capture_output=True, timeout=10)
    for name in ('protocol.json', 'design-lock.json', 'README.md'):
        p = ROOT / 'prototype/qwen-balanced-protocol' / name
        committed = subprocess.check_output(['git', 'show', commit + ':' + str(p.relative_to(ROOT))], cwd=ROOT, timeout=10)
        if committed != p.read_bytes():
            raise ValueError('Locked design source changed: ' + name)
    return commit


def freeze(names, design_commit=None):
    if 'confirmation' in names:
        verify_design_commit(design_commit)
    splits = {name: read_rows(BUILD / ('author-' + name + '.jsonl')) for name in names}
    # Already frozen earlier splits remain mandatory exclusion for confirmation.
    for name in ('train', 'development'):
        if name not in splits and (BUILD / (name + '.jsonl')).is_file():
            splits[name] = read_rows(BUILD / (name + '.jsonl'))
    validate_disjoint(splits)
    inventory, previous = inventory_sources()
    for rows in splits.values():
        inventory_util.reject_overlap(rows, previous)
    outputs = {}
    for name in names:
        for extension in ('.jsonl', '-requests.tsv'):
            if (BUILD / (name + extension)).exists():
                raise ValueError('Frozen output already exists: ' + name + extension)
        raw = ''.join(json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n' for r in splits[name]).encode()
        tsv = ''.join(r['id'] + '\t' + r['utterance'] + '\n' for r in splits[name]).encode()
        outputs[name] = (raw, tsv)
    manifest = {'schema': 1, 'synthetic_only': True, 'author_informed_not_blind': True,
                'model_or_gate_calls': 0, 'oracle_filtered': False,
                'normalization': 'Lowercase, replace non-ASCII-alphanumeric runs with space, collapse whitespace; no semantic independence claim',
                'family_rule': 'Manually assigned complete wording families and template identities; no random row split',
                'generator_sha256': sha(__file__), 'inventory_utility_sha256': sha(UTILITY),
                'design_authorization_commit': design_commit, 'inventory': inventory,
                'previous_unique_normalized_requests': len({normalize(t) for t in previous}),
                'splits': {}}
    for name, rows in splits.items():
        raw = outputs[name][0] if name in outputs else (BUILD / (name + '.jsonl')).read_bytes()
        tsv = outputs[name][1] if name in outputs else (BUILD / (name + '-requests.tsv')).read_bytes()
        manifest['splits'][name] = {'rows': len(rows), 'families': len({r['family'] for r in rows}),
            'by_intent': dict(Counter(r['intent'] for r in rows)),
            'jsonl_sha256': hashlib.sha256(raw).hexdigest(), 'requests_sha256': hashlib.sha256(tsv).hexdigest(),
            'hard_tag_counts': dict(Counter(t for r in rows for t in r['hard_tags'])),
            'unknown_boundary_counts': dict(Counter(r['boundary_family'] for r in rows if r['intent'] == 'unknown')),
            'reserved_chat_control_requests': sum('<|' in r['utterance'] or '|>' in r['utterance'] for r in rows)}
    manifest_path = TASK / ('confirmation-manifest.json' if 'confirmation' in names else 'training-manifest.json')
    if manifest_path.exists():
        raise ValueError('Frozen manifest already exists')
    for name, (raw, tsv) in outputs.items():
        (BUILD / (name + '.jsonl')).write_bytes(raw)
        (BUILD / (name + '-requests.tsv')).write_bytes(tsv)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=('training', 'confirmation'), required=True)
    parser.add_argument('--design-commit')
    args = parser.parse_args()
    result = freeze(('train', 'development') if args.stage == 'training' else ('confirmation',), args.design_commit)
    print(json.dumps({'splits': result['splits'], 'inventory_sources': len(result['inventory'])}, indent=2))
