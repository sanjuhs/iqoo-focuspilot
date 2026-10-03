"""Verify public frozen sources and reviews; check private raw bytes if present.

No model, JNI, phone, training or generation. A successful audit does not qualify
the rejected planner or replace the original measured capture.
"""
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def verify():
    for folder in [ROOT / 'prototype/task-draft-v21', HERE]:
        freeze = load(folder / 'freeze-manifest.json')
        for path, digest in freeze['files'].items():
            if sha(folder / path) != digest:
                raise ValueError('Frozen source differs: ' + path)
        result = load(folder / 'results.json')
        if result['freeze_sha256'] != sha(folder / 'freeze-manifest.json'):
            raise ValueError('Result freeze binding differs')
        for name, digest in [('output.tsv', result['process']['output_sha256']),
                             ('stderr.log', result['process']['stderr_sha256']),
                             ('captured-details.json', result['details_sha256'])]:
            raw = folder / 'build' / name
            if raw.exists() and sha(raw) != digest:
                raise ValueError('Raw capture differs: ' + str(raw))
    initial = load(ROOT / 'prototype/task-draft-v21/results.json')
    if initial['captured'] != 0 or initial['complete_capture'] or initial['model_load_ms'] is not None:
        raise ValueError('Initial refusal record differs')
    result = load(HERE / 'results.json')
    q = load(HERE / 'qualification.json')
    for name, digest in q['bindings'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('Public review/result binding differs: ' + name)
    cases = load(HERE / 'cases.json')
    root = load(HERE / 'root-review.json')
    author = load(HERE / 'author-review.json')
    rows = root['rows']
    indexed = {r['id']: r for r in rows}
    other = {r['id']: r for r in author['case_reviews']}
    expected_ids = {c['id'] for c in cases}
    if len(rows) != 32 or len(indexed) != 32 or set(indexed) != expected_ids or set(other) != expected_ids:
        raise ValueError('Review IDs differ')
    for row in rows:
        for key in ['criterion_met', 'goal_relevant', 'respects_constraints', 'invented_access_or_completion', 'harmful_guidance']:
            if type(row[key]) is not bool or row[key] != other[row['id']][key]:
                raise ValueError('Unresolved or malformed review')
        if not row['reason'].strip():
            raise ValueError('Missing semantic justification')
    counts = {k: {'total': sum(c['kind'] == k for c in cases),
                  'criterion_met': sum(r['kind'] == k and r['criterion_met'] for r in rows),
                  'goal_relevant': sum(r['kind'] == k and r['goal_relevant'] for r in rows)}
              for k in ['benign', 'constraint', 'tricky']}
    if counts != q['counts'] or q['qualified'] or q['decision'] != 'REJECT_FOR_APP_PROMOTION':
        raise ValueError('Qualification decision/counts differ')
    if not result['complete_capture'] or result['captured'] != 32 or result['completed_eos_and_schema'] != 32:
        raise ValueError('Compatible complete-capture record differs')
    raw = HERE / 'build/captured-details.json'
    if raw.exists():
        details = load(raw)
        if set(details) != expected_ids:
            raise ValueError('Raw IDs differ')
        for key, value in details.items():
            m = value['outer']['metrics']
            if not (value['status'] == 'OK' and m['reached_eos'] is True and m['cpu_only'] is True
                    and m['capture_enabled'] is False and value['outer']['activations'] == []):
                raise ValueError('Actual native/EOS/capture scope differs')
            if json.loads(value['outer']['text'])['steps'] != indexed[key]['model_steps']:
                raise ValueError('Public reviewed steps differ from raw output')
        lines = (HERE / 'build/output.tsv').read_text().splitlines()
        if len(lines) != 33 or lines[0].split('\t')[0] != 'LOAD':
            raise ValueError('Original raw transport differs')
        for line in lines[1:]:
            key, elapsed, status, data = line.split('\t')
            if status != details[key]['status'] or base64.b64decode(data).decode() != details[key]['raw']:
                raise ValueError('Raw transport/details differ')
    return {'public_sources_reviews_aggregates_verified': True,
            'private_raw_checked': raw.exists(), 'qualification': 'rejected',
            'scope': 'Source/evidence binding audit only; no new inference or phone proof'}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
