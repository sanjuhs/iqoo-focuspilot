"""Freeze informed synthetic unit-contract confirmation data without inference.

Candidate sources, prompts, fixtures and outputs are deliberately not read.
Only root-owned protocol/provenance metadata and this generic tool are readable.
Authoring requires a separate explicit parent authorization after source freeze.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BUILD = TASK / 'build'
EVAL = ROOT / 'prototype/compatible-eval'
SOURCE_FILES = ('generate_data.py', 'test_data.py', 'README.md')
INTENTS = ('start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown')
COUNTS = dict(zip(INTENTS, (9, 9, 8, 8, 8, 8, 50)))
APPS = {'settings', 'calculator', 'clock'}
APP_COUNTS = {'settings': 3, 'calculator': 3, 'clock': 2}
FACTORS = {'seconds': 1, 'minutes': 60, 'hours': 3600}
BOUNDARY_COUNTS = {'negation': 5, 'compound': 5, 'conditional': 4, 'quoted': 4,
    'foreign_topic': 5, 'privacy_capture': 4, 'destructive': 4, 'messaging': 3,
    'payments': 3, 'malformed_argument': 5, 'unsupported_target': 4, 'third_party': 4}
BOUNDARIES = set(BOUNDARY_COUNTS)
HARD_MINIMUMS = {'unit_minutes': 8, 'unit_seconds': 4, 'unit_hours': 2,
    'spoken_number': 8, 'untimed_start': 2, 'am_pm': 4, 'clock_24h': 2}
FIELDS = {'id', 'family', 'template_id', 'utterance', 'expected', 'expected_raw',
          'hard_tags', 'boundary_family', 'counterpart_id'}
NORMALIZATION = 'ascii-alnum-lower-v1'
HASH_FIELDS = ('normalized_request_sha256', 'exact_request_sha256',
               'family_sha256', 'template_sha256')


def strict_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize(text):
    return ' '.join(re.sub('[^a-z0-9]+', ' ', text.lower()).split())


def valid_hash(value, length=64):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def relative_path(value):
    return isinstance(value, str) and bool(value) and not Path(value).is_absolute() and '..' not in Path(value).parts


def identifier(value, maximum=80):
    return isinstance(value, str) and re.fullmatch('[A-Za-z0-9_-]{1,' + str(maximum) + '}', value) is not None


def positive_minima(value, names=None):
    if not isinstance(value, dict) or not value or (names is not None and set(value) != names):
        raise ValueError('Prospective coverage minima required')
    if any(not isinstance(k, str) or not re.fullmatch('[a-z][a-z0-9_]{0,63}', k)
           or type(v) is not int or not 1 <= v <= 50 for k, v in value.items()):
        raise ValueError('Bounded tag names and positive integer minima required')


def validate_protocol(protocol):
    if not isinstance(protocol, dict) or protocol.get('schema') != 'focuspilot.compatible_unit_protocol.v1' or protocol.get('candidate_source_freeze_before_authoring') is not True:
        raise ValueError('Explicit prospective source-before-authoring protocol required')
    c = protocol.get('fresh_cohort')
    if not isinstance(c, dict):
        raise ValueError('Fresh cohort contract required')
    for key, wanted in {'rows': 100, 'families': 50, 'rows_per_family': 2, 'supported': 50, 'unknown': 50}.items():
        if type(c.get(key)) is not int or c[key] != wanted:
            raise ValueError('Fixed 100-row reciprocal cohort required')
    if c.get('counts') != COUNTS or any(type(v) is not int for v in c['counts'].values()):
        raise ValueError('Exact prospective 9/9/8/8/8/8/50 counts required')
    apps = c.get('approved_apps')
    if not isinstance(apps, dict) or apps != APP_COUNTS or any(type(v) is not int for v in apps.values()):
        raise ValueError('Exact root-approved Settings3/Calculator3/Clock2 counts required')
    positive_minima(c.get('hard_minimums'), set(HARD_MINIMUMS))
    positive_minima(c.get('unknown_boundaries'), BOUNDARIES)
    if c['hard_minimums'] != HARD_MINIMUMS or c['unknown_boundaries'] != BOUNDARY_COUNTS:
        raise ValueError('Exact root-approved prospective hard minima and boundary counts required')
    return c


def validate_expected(expected, raw=False):
    if not isinstance(expected, dict) or expected.get('intent') not in INTENTS:
        raise ValueError('Exact manually labelled intent required')
    intent = expected['intent']
    fields = {'intent'}
    if intent in {'start_focus', 'timer'}:
        fields.update(('amount', 'unit') if raw else ('duration_seconds',))
    elif intent == 'alarm':
        fields.update(('hour', 'minute'))
    elif intent == 'open_app':
        fields.add('app')
    if set(expected) != fields:
        raise ValueError('No missing, extra or irrelevant expected slots')
    if intent in {'start_focus', 'timer'}:
        if raw:
            amount, unit = expected['amount'], expected['unit']
            if type(amount) is not int or not isinstance(unit, str):
                raise ValueError('Integer source quantity and exact unit required')
            if amount == 0 and unit == 'none' and intent == 'start_focus':
                seconds = 0
            elif unit in FACTORS and amount > 0:
                seconds = amount * FACTORS[unit]
            else:
                raise ValueError('Zero/none allowed only for untimed start; otherwise one positive source quantity/unit')
        else:
            seconds = expected['duration_seconds']
        if type(seconds) is not int or not (0 <= seconds <= 7200 if intent == 'start_focus' else 1 <= seconds <= 7200):
            raise ValueError('Duration outside manually labelled bounded contract')
    elif intent == 'alarm':
        if type(expected['hour']) is not int or type(expected['minute']) is not int or not 0 <= expected['hour'] <= 23 or not 0 <= expected['minute'] <= 59:
            raise ValueError('Valid local wall-clock hour/minute required')
    elif intent == 'open_app':
        if not isinstance(expected['app'], str) or expected['app'] not in APPS:
            raise ValueError('Exact allowlisted app required')
    return expected


def canonical_raw(raw):
    """Unit arithmetic only: does not parse requests, query a gate or derive gold."""
    validate_expected(raw, raw=True)
    if raw['intent'] not in {'start_focus', 'timer'}:
        return dict(raw)
    seconds = 0 if raw['unit'] == 'none' else raw['amount'] * FACTORS[raw['unit']]
    return {'intent': raw['intent'], 'duration_seconds': seconds}


def validate_rows(rows, protocol):
    c = validate_protocol(protocol)
    if not isinstance(rows, list) or len(rows) != c['rows']:
        raise ValueError('Complete prospective cohort required')
    ids, texts, families, templates = {}, set(), defaultdict(list), {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError('Exact generic author row schema required')
        for key in ('id', 'family', 'template_id', 'counterpart_id'):
            if not identifier(row[key], 64 if key in {'id', 'counterpart_id'} else 80):
                raise ValueError('Bounded row and family identifiers required')
        if row['id'] in ids:
            raise ValueError('Duplicate row ID')
        ids[row['id']] = row
        text = row['utterance']
        if not isinstance(text, str) or not text.strip() or any(ord(ch) < 32 or ord(ch) in (127, 0x2028, 0x2029) for ch in text):
            raise ValueError('Nonempty single-line UTF-8 request required')
        try:
            text.encode('utf-8')
            units = len(text.encode('utf-16-le')) // 2
        except UnicodeEncodeError as error:
            raise ValueError('Valid Unicode scalar request required') from error
        norm = normalize(text)
        if units > 500 or not norm or norm in texts:
            raise ValueError('Bounded Android request with unique nonempty normalized wording required')
        texts.add(norm)
        expected = validate_expected(row['expected'])
        if canonical_raw(row['expected_raw']) != expected:
            raise ValueError('Independently labelled canonical and source-unit gold disagree')
        tags = row['hard_tags']
        if not isinstance(tags, list) or any(not isinstance(t, str) or not re.fullmatch('[a-z][a-z0-9_]{0,63}', t) for t in tags) or len(tags) != len(set(tags)):
            raise ValueError('Unique bounded hard tags required')
        boundary = row['boundary_family']
        if expected['intent'] == 'unknown':
            if not isinstance(boundary, str) or boundary not in BOUNDARIES:
                raise ValueError('Manually assigned unknown boundary required')
        elif boundary != '':
            raise ValueError('Supported rows have no unknown boundary')
        # Generic tag consistency only. Semantic source wording is manually reviewed.
        if any(t in tags for t in ('pause_preservation', 'current_or_spoken_focus_pause')) and expected['intent'] != 'pause_focus':
            raise ValueError('Pause tags require pause gold')
        if 'resume_vs_start' in tags and expected['intent'] != 'start_focus':
            raise ValueError('Resume tag requires start gold')
        if 'nudge_cause' in tags and expected['intent'] != 'explain':
            raise ValueError('Nudge cause tag requires explain gold')
        if 'duration_boundary' in tags and (expected['intent'] not in {'start_focus', 'timer'} or expected['duration_seconds'] not in {1, 7200}):
            raise ValueError('Duration endpoint tag requires one or 7200 seconds')
        if 'midnight_noon' in tags and (expected['intent'] != 'alarm' or (expected['hour'], expected['minute']) not in {(0, 0), (12, 0)}):
            raise ValueError('Meridian tag requires exact noon/midnight gold')
        for tag, unit in (('unit_minutes', 'minutes'), ('unit_seconds', 'seconds'), ('unit_hours', 'hours')):
            if tag in tags and (expected['intent'] not in {'start_focus', 'timer'} or row['expected_raw']['unit'] != unit):
                raise ValueError('Source-unit tag must match supported source-unit gold')
        if 'untimed_start' in tags and (expected['intent'] != 'start_focus' or expected['duration_seconds'] != 0):
            raise ValueError('Untimed-start tag requires zero/none start gold')
        if any(t in tags for t in ('am_pm', 'clock_24h')) and expected['intent'] != 'alarm':
            raise ValueError('Clock notation tags require alarm gold')
        if 'am_pm' in tags and 'clock_24h' in tags:
            raise ValueError('Source clock notation tags are mutually exclusive')
        if 'spoken_number' in tags and expected['intent'] not in {'start_focus', 'timer', 'alarm'}:
            raise ValueError('Spoken-number tag requires supported duration or alarm gold')
        family, template = row['family'], row['template_id']
        families[family].append(row)
        if template in templates and templates[template] != family:
            raise ValueError('Template cannot alias multiple paired families')
        templates[template] = family
    if Counter(r['expected']['intent'] for r in rows) != c['counts']:
        raise ValueError('Exact prospective intent counts differ')
    if len(families) != 50 or len(templates) != 50:
        raise ValueError('Exactly fifty distinct complete paired wording families/templates required')
    for pair in families.values():
        if len(pair) != 2 or len({r['template_id'] for r in pair}) != 1 or sum(r['expected']['intent'] == 'unknown' for r in pair) != 1:
            raise ValueError('One supported plus one unknown row per complete paired family required')
        a, b = pair
        if a['counterpart_id'] != b['id'] or b['counterpart_id'] != a['id']:
            raise ValueError('Counterpart IDs must be reciprocal within each pair')
    apps = Counter(r['expected']['app'] for r in rows if r['expected']['intent'] == 'open_app')
    if apps != c['approved_apps']:
        raise ValueError('Exact prospective app counts differ')
    for tag, minimum in c['hard_minimums'].items():
        if sum(tag in r['hard_tags'] for r in rows if r['expected']['intent'] != 'unknown') < minimum:
            raise ValueError('Missing prospective hard minimum: ' + tag)
    boundaries = Counter(r['boundary_family'] for r in rows if r['expected']['intent'] == 'unknown')
    if boundaries != c['unknown_boundaries']:
        raise ValueError('Exact prospective unknown boundary counts differ')
    return rows


def validate_exclusions(bundle):
    if not isinstance(bundle, dict) or bundle.get('schema') != 'focuspilot.natural_exclusion.v1' or bundle.get('normalization') != NORMALIZATION or not valid_hash(bundle.get('source_commit'), 40):
        raise ValueError('Exact opaque exclusion schema/normalization/full provenance commit required')
    for key in HASH_FIELDS:
        values = bundle.get(key)
        if not isinstance(values, list) or not values or any(not valid_hash(v) for v in values) or values != sorted(set(values)):
            raise ValueError('Sorted unique nonempty full exclusion hashes required: ' + key)
    inventory = bundle.get('inventory')
    if not isinstance(inventory, list) or not inventory:
        raise ValueError('Opaque inventory metadata required')
    for item in inventory:
        if not isinstance(item, dict) or not relative_path(item.get('path')) or not valid_hash(item.get('sha256')) or type(item.get('text_count')) is not int or item['text_count'] < 0 or not isinstance(item.get('method'), str) or not item['method']:
            raise ValueError('Project-relative inventory path/hash/count/method required')
    return bundle


def reject_excluded(rows, bundle):
    validate_exclusions(bundle)
    excluded = {key: set(bundle[key]) for key in HASH_FIELDS}
    collisions = []
    for row in rows:
        hashes = {'normalized_request_sha256': digest(normalize(row['utterance'])),
                  'exact_request_sha256': digest(row['utterance']),
                  'family_sha256': digest(row['family']), 'template_sha256': digest(row['template_id'])}
        if any(value in excluded[key] for key, value in hashes.items()):
            collisions.append(row['id'])
    if collisions:
        raise ValueError('Opaque overlap in own authored IDs: ' + ','.join(collisions))


def verify_authorization(commit):
    if not valid_hash(commit, 40):
        raise ValueError('Full explicitly authorized source-freeze commit required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=ROOT,
                   check=True, capture_output=True, timeout=10)
    freeze_path = EVAL / 'source-freeze.json'
    frozen = strict_json(freeze_path.read_text())
    bindings = frozen.get('files_sha256')
    if not isinstance(bindings, dict) or not bindings or any(not relative_path(k) or not valid_hash(v) for k, v in bindings.items()):
        raise ValueError('Parent-owned complete source binding map required')
    # Root verifies candidate bytes. Author reads only listed metadata and own sources.
    readable = [EVAL / 'protocol.json', EVAL / 'design-lock.json', EVAL / 'novelty-exclusions.json',
                *(TASK / name for name in SOURCE_FILES)]
    if not any(k.endswith('.java') and not k.startswith('prototype/compatible-data/') for k in bindings):
        raise ValueError('Parent candidate source hash binding required')
    for path in readable:
        relative = str(path.relative_to(ROOT))
        if bindings.get(relative) != sha(path):
            raise ValueError('Readable source binding missing/changed: ' + relative)
    for path in [freeze_path, *readable]:
        relative = str(path.relative_to(ROOT))
        committed = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=ROOT, timeout=10)
        if committed != path.read_bytes():
            raise ValueError('Readable source differs from authorized commit: ' + relative)
    return frozen


def read_rows(path):
    return [strict_json(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def private_input(path):
    path = Path(path)
    if BUILD.is_symlink() or path.is_symlink() or path.resolve().parent != BUILD.resolve() or path.suffix != '.jsonl':
        raise ValueError('Author input must remain a real direct ignored build/*.jsonl file')
    return path


def freeze(commit, author_path=None):
    verify_authorization(commit)
    author_path = private_input(author_path or BUILD / 'author-confirmation.jsonl')
    protocol_path, exclusions_path = EVAL / 'protocol.json', EVAL / 'novelty-exclusions.json'
    protocol, bundle = strict_json(protocol_path.read_text()), strict_json(exclusions_path.read_text())
    rows = validate_rows(read_rows(author_path), protocol)
    reject_excluded(rows, bundle)
    outputs = [BUILD / 'confirmation.jsonl', BUILD / 'confirmation-requests.tsv', TASK / 'corpus-manifest.json']
    if any(path.exists() or path.is_symlink() for path in outputs):
        raise ValueError('Existing frozen inputs/manifest must remain unchanged')
    raw = ''.join(json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows).encode('utf-8')
    tsv = ''.join(r['id'] + '\t' + r['utterance'] + '\n' for r in rows).encode('utf-8')
    manifest = {'schema': 'focuspilot.compatible_unit_corpus.v1', 'synthetic_only': True,
        'author_informed_not_blind': True, 'population_estimate': False,
        'candidate_validator_tests_prompt_outputs_read_by_author': False,
        'model_gate_oracle_calls': 0, 'filtered_by_gate_or_oracle': False, 'before_outputs': True,
        'source_authorization_commit': commit, 'source_freeze_sha256': sha(EVAL / 'source-freeze.json'),
        'protocol_sha256': sha(protocol_path), 'exclusion_bundle_sha256': sha(exclusions_path),
        'generic_source_sha256': {name: sha(TASK / name) for name in SOURCE_FILES},
        'author_input_sha256': sha(author_path), 'jsonl_sha256': hashlib.sha256(raw).hexdigest(),
        'requests_sha256': hashlib.sha256(tsv).hexdigest(), 'rows': len(rows), 'families': 50,
        'by_intent': dict(Counter(r['expected']['intent'] for r in rows)),
        'approved_app_counts': dict(Counter(r['expected']['app'] for r in rows if r['expected']['intent'] == 'open_app')),
        'source_unit_counts': dict(Counter(r['expected_raw']['unit'] for r in rows if r['expected']['intent'] in {'start_focus', 'timer'})),
        'hard_tag_counts': dict(Counter(t for r in rows for t in r['hard_tags'])),
        'supported_hard_tag_counts': dict(Counter(t for r in rows if r['expected']['intent'] != 'unknown' for t in r['hard_tags'])),
        'unknown_boundary_counts': dict(Counter(r['boundary_family'] for r in rows if r['expected']['intent'] == 'unknown')),
        'reserved_chat_control_requests': sum('<|' in r['utterance'] or '|>' in r['utterance'] for r in rows),
        'opaque_exclusion_counts': {key: len(bundle[key]) for key in HASH_FIELDS},
        'exclusion_inventory': bundle['inventory'], 'normalization': NORMALIZATION,
        'gold_contract': 'Independent manual canonical seconds and exact source quantity/unit, strict slots; arithmetic consistency only',
        'manual_review_required_before_inference': True,
        'limitations': ['Informed synthetic author, not blinded or population representative',
            'Hash novelty and unique family IDs do not establish semantic independence',
            'Privacy/no-recording constraints alone are legitimate; unknown needs an actual unsupported/ambiguous/negated/malformed demand',
            'Generic arithmetic validation cannot prove source wording semantics; parent reviews every gold object before inference']}
    for path, payload in zip(outputs[:2], (raw, tsv)):
        with path.open('xb') as stream:
            stream.write(payload)
    with outputs[2].open('x') as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
        stream.write('\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization-commit', required=True)
    parser.add_argument('--author-input')
    args = parser.parse_args()
    result = freeze(args.authorization_commit, args.author_input)
    print(json.dumps({key: result[key] for key in ('rows', 'families', 'by_intent', 'jsonl_sha256', 'requests_sha256')}, indent=2))
