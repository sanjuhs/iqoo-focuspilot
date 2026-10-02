"""Freeze hand-labelled structured-action DEVELOPMENT data, without inference."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

TASK = Path(__file__).resolve().parent
BUILD = TASK / 'build'
INTENTS = {'start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown'}
COUNTS = {'start_focus': 4, 'pause_focus': 4, 'alarm': 3, 'timer': 3,
          'open_app': 2, 'explain': 2, 'unknown': 6}
APPS = {'settings', 'calculator', 'clock'}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def strict_json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def validate_expected(expected):
    if not isinstance(expected, dict) or expected.get('intent') not in INTENTS:
        raise ValueError('One manually labelled structured intent required')
    intent = expected['intent']
    required = {'intent'}
    if intent in {'start_focus', 'timer'}:
        required.add('duration_seconds')
    elif intent == 'alarm':
        required.update(('hour', 'minute'))
    elif intent == 'open_app':
        required.add('app')
    if set(expected) != required:
        raise ValueError('Exact response shape, no missing or extra slots')
    if intent in {'start_focus', 'timer'}:
        duration = expected['duration_seconds']
        if type(duration) is not int or not (0 <= duration <= 7200 if intent == 'start_focus' else 1 <= duration <= 7200):
            raise ValueError('Exact bounded duration required')
    elif intent == 'alarm':
        if any(type(expected[k]) is not int for k in ('hour', 'minute')) or not 0 <= expected['hour'] <= 23 or not 0 <= expected['minute'] <= 59:
            raise ValueError('Exact valid local wall-clock slots required')
    elif intent == 'open_app' and expected['app'] not in APPS:
        raise ValueError('Allowlisted application required')
    return expected


def normalize(text):
    return ' '.join(re.sub('[^a-z0-9]+', ' ', text.lower()).split())


def validate_rows(rows):
    if len(rows) != 24:
        raise ValueError('Complete 24-row development cohort required')
    ids, texts = set(), set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'utterance', 'expected'}:
            raise ValueError('Exact id/utterance/expected row schema required')
        if not isinstance(row['id'], str) or not re.fullmatch('[A-Za-z0-9_-]{1,64}', row['id']) or row['id'] in ids:
            raise ValueError('Unique bounded identifier required')
        ids.add(row['id'])
        text = row['utterance']
        if not isinstance(text, str) or not text.strip() or len(text.encode('utf-16-le')) // 2 > 500 or any(ord(c) < 32 or ord(c) in (127, 0x2028, 0x2029) for c in text):
            raise ValueError('Bounded single-line request required')
        norm = normalize(text)
        if norm in texts:
            raise ValueError('Within-development normalized duplicate')
        texts.add(norm)
        validate_expected(row['expected'])
    if Counter(r['expected']['intent'] for r in rows) != COUNTS:
        raise ValueError('Exact prospective development intent counts required')
    return rows


def freeze(author_path=None):
    author_path = Path(author_path) if author_path else BUILD / 'author-development.jsonl'
    if author_path.resolve().parent != BUILD.resolve():
        raise ValueError('Raw development data must stay in ignored build/')
    rows = validate_rows([strict_json(line) for line in author_path.read_text().splitlines() if line.strip()])
    outputs = [BUILD / 'development.jsonl', BUILD / 'development-requests.tsv', TASK / 'data-manifest.json']
    if any(path.exists() for path in outputs):
        raise ValueError('Preserve existing authored/frozen development attempt')
    raw = ''.join(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n' for row in rows).encode()
    tsv = ''.join(row['id'] + '\t' + row['utterance'] + '\n' for row in rows).encode()
    manifest = {'schema': 'focuspilot.structured_development_data.v1',
        'scope': 'FIRST_STRUCTURED_ACTION_DEVELOPMENT_FEASIBILITY', 'research_only': True,
        'fresh_confirmation_claim': False, 'blind_claim': False, 'promotion_claim': False,
        'synthetic_only': True, 'author_informed': True, 'model_gate_oracle_calls': 0,
        'candidate_prompt_validator_native_or_model_outputs_read': False,
        'filtered_by_gate_or_oracle': False, 'rows': 24, 'supported': 18, 'unknown': 6,
        'by_intent': dict(Counter(row['expected']['intent'] for row in rows)),
        'app_targets': dict(Counter(row['expected']['app'] for row in rows if row['expected']['intent'] == 'open_app')),
        'source_sha256': {name: sha(TASK / name) for name in ('generate_data.py', 'test_data.py', 'README.md')},
        'author_input_sha256': sha(author_path), 'jsonl_sha256': hashlib.sha256(raw).hexdigest(),
        'requests_sha256': hashlib.sha256(tsv).hexdigest(),
        'gold': 'Independent manual structured objects, complete action slots, strict field sets; object member order does not change gold meaning',
        'development_provenance': 'Prior coverage-failure wording may recur; not excluded against earlier datasets and not an independent accuracy estimate',
        'semantic_notes': ['Start has one untimed zero-duration request, timed spoken requests, a resume and a 7,200-second endpoint',
            'All four Pause requests stop/pause a focus or study session, including current and completed-session context',
            'Alarm covers exact noon, midnight and a manually converted PM time; no date/calendar inference',
            'Timer is a regular countdown, with exact seconds and minute/hour conversions',
            'Ordinary privacy/no-audio-storage preferences alone remain supported',
            'Unknown cases cover compound action, negation, conditional execution, out-of-range duration, destructive capability and additional private capture capability',
            'Explain expected objects establish the intended bounded domain, not actual answer fulfillment'],
        'next_step': 'Parent manual gold review and source freeze before one development capture; no post-output label optimization'}
    for path, payload in zip(outputs[:2], (raw, tsv)):
        with path.open('xb') as f:
            f.write(payload)
    with outputs[2].open('x') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write('\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--author-input')
    args = parser.parse_args()
    result = freeze(args.author_input)
    print(json.dumps({k: result[k] for k in ('rows', 'supported', 'unknown', 'by_intent', 'jsonl_sha256', 'requests_sha256')}, indent=2))
