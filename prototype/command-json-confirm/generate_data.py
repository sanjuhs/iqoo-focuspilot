"""Validate and freeze privately authored synthetic requests; performs no inference.

Raw author rows live in ignored build/author-cases.jsonl, never in this source.
Only hashes/counts/extraction methods are published in corpus-manifest.json.
"""
import ast
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import re

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
DEV = ROOT / 'prototype/command-json-dev'
APP = ROOT / 'prototype/android/app/src/main/java/dev/focuspilot/prototype'
BUILD = TASK / 'build'
AUTHORING_AUTHORIZED_AFTER_COMMIT = '542d9c5afd117fb32b4d3878e37d924a3e840451'
KINDS = {'START_FOCUS': 'start_focus', 'PAUSE_FOCUS': 'pause_focus', 'ALARM': 'alarm',
         'TIMER': 'timer', 'OPEN_SETTINGS': 'open_app', 'OPEN_CALCULATOR': 'open_app',
         'OPEN_CLOCK': 'open_app', 'EXPLAIN': 'explain', 'UNKNOWN': 'unknown'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def strict_json(text):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate JSON key')
            value[key] = item
        return value
    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def normalize(text):
    return ' '.join(re.sub('[^a-z0-9]+', ' ', text.lower()).split())


def validate_rows(rows, protocol):
    contract = protocol['corpus']
    if len(rows) != contract['rows']:
        raise ValueError('Complete 100-row corpus required')
    ids = [r.get('id') for r in rows]
    if any(not isinstance(i, str) or not re.fullmatch('[A-Za-z0-9_-]{1,64}', i) for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Unique bounded IDs required')
    by_id = dict(zip(ids, rows))
    allowed_tags = set(contract['hard_tag_minimum_rows'])
    for row in rows:
        if set(row) != set(contract['row_fields']):
            raise ValueError('Exact protocol fields required')
        text = row['utterance']
        if not isinstance(text, str) or not text.strip() or len(text) > 500 or any(ord(c) < 32 or ord(c) == 127 or c in '\u2028\u2029' for c in text):
            raise ValueError('Bounded nonempty single-line text required')
        if not isinstance(row['family'], str) or not re.fullmatch('[A-Za-z0-9_-]{1,64}', row['family']):
            raise ValueError('Bounded family required')
        kind = row['expected_kind']
        if kind not in KINDS or row['semantic_intent'] != KINDS[kind] or row['oracle_intent'] not in protocol['fixed']['intent_labels']:
            raise ValueError('Semantic/domain/action labels disagree')
        if kind != 'UNKNOWN' and row['oracle_intent'] != row['semantic_intent']:
            raise ValueError('Supported oracle must preserve its semantic intent')
        if any(type(row[key]) is not int for key in ('hour', 'minute', 'seconds')):
            raise ValueError('Exact integer slots required, not bool')
        h, m, s = (row[key] for key in ('hour', 'minute', 'seconds'))
        if kind == 'ALARM':
            if not 0 <= h <= 23 or not 0 <= m <= 59 or s != 0:
                raise ValueError('Invalid alarm slots')
        elif kind in {'START_FOCUS', 'TIMER'}:
            if (h, m) != (0, 0) or not (0 <= s <= 7200 if kind == 'START_FOCUS' else 1 <= s <= 7200):
                raise ValueError('Invalid duration slots')
        elif (h, m, s) != (0, 0, 0):
            raise ValueError('Slotless and unknown rows have zero slots')
        tags = row['hard_tags']
        if not isinstance(tags, list) or any(not isinstance(t, str) or t not in allowed_tags for t in tags) or len(tags) != len(set(tags)):
            raise ValueError('Unique prospective tags required')
        if kind == 'UNKNOWN' and tags:
            raise ValueError('Unknown counterpart has no supported hard tags')
        if ('pause_preservation' in tags) != (kind == 'PAUSE_FOCUS'):
            raise ValueError('Every Pause, and only Pause, has preservation tag')
        if 'current_or_spoken_focus_pause' in tags and kind != 'PAUSE_FOCUS':
            raise ValueError('Pause hard tag on wrong action')
        if 'resume_vs_start' in tags and kind != 'START_FOCUS':
            raise ValueError('Resume tag on wrong action')
        if 'nudge_cause' in tags and kind != 'EXPLAIN':
            raise ValueError('Nudge tag on wrong action')
        if 'duration_boundary' in tags and (kind not in {'START_FOCUS', 'TIMER'} or s not in {1, 7200}):
            raise ValueError('Boundary tag does not match endpoint')
        if 'midnight_noon' in tags and (kind != 'ALARM' or h not in {0, 12}):
            raise ValueError('Meridian tag does not match alarm')
        other = by_id.get(row['counterpart_id'])
        if other is None or other is row or other['counterpart_id'] != row['id'] or other['family'] != row['family'] or (kind == 'UNKNOWN') == (other['expected_kind'] == 'UNKNOWN'):
            raise ValueError('Reciprocal supported/unknown same-family counterpart required')
    if len({r['family'] for r in rows}) != contract['families'] or any(n != 2 for n in Counter(r['family'] for r in rows).values()):
        raise ValueError('Exactly 50 two-row families required')
    supported = [r for r in rows if r['expected_kind'] != 'UNKNOWN']
    if Counter(r['semantic_intent'] for r in supported) != contract['supported_by_intent'] or len(rows) - len(supported) != contract['must_abstain_rows']:
        raise ValueError('Fixed supported/unknown intent balance required')
    targets = Counter(r['expected_kind'] for r in supported if r['semantic_intent'] == 'open_app')
    if targets != {'OPEN_SETTINGS': 2, 'OPEN_CALCULATOR': 2, 'OPEN_CLOCK': 2}:
        raise ValueError('Fixed approved-app target balance required')
    for tag, minimum in contract['hard_tag_minimum_rows'].items():
        if sum(tag in r['hard_tags'] for r in supported) < minimum:
            raise ValueError('Prospective tag minimum missing: ' + tag)
    reject_overlap(rows, [])
    return rows


def java_literals(text):
    values = []
    for raw in re.findall(r'"((?:\\.|[^"\\])*)"', text):
        # Current inventoried Java uses JSON-compatible escapes; fail closed otherwise.
        values.append(strict_json('"' + raw.replace("\\'", "'") + '"'))
    return values


def prompt_examples(texts):
    labels = '|'.join(['start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown'])
    output = []
    for text in texts:
        for match in re.finditer(r'([^=\n.]+?)\s*=\s*(?:' + labels + r')\b', text):
            item = match.group(1).strip()
            if 'Examples:' in item:
                item = item.split('Examples:', 1)[1].strip()
            if item:
                output.append(item)
    return output


def extract_requests(path):
    path = Path(path)
    if path.suffix == '.jsonl':
        rows = [strict_json(line) for line in path.read_text().splitlines() if line.strip()]
        values = [r['utterance'] for r in rows]
        # Training messages can contain additional user requests and seen system examples.
        for row in rows:
            for message in row.get('messages', []):
                if message.get('role') == 'user':
                    values.append(message['content'])
                elif message.get('role') == 'system':
                    values.extend(prompt_examples([message['content']]))
        method = 'JSONL utterance plus user messages/system prompt examples; excludes assistant output'
    elif path.suffix == '.tsv':
        values = []
        col = 2 if path.name == 'prompt-cases.tsv' else 1
        for line in path.read_text().splitlines():
            fields = line.split('\t')
            if len(fields) <= col:
                raise ValueError('Malformed request TSV')
            values.append(fields[col])
        method = 'TSV complete original request column ' + str(col + 1)
    elif path.suffix == '.java':
        source = path.read_text()
        values = java_literals(source)
        values.extend(prompt_examples(values))
        method = 'Conservative decoded Java string literals plus embedded prompt examples; no outputs'
    elif path.suffix == '.py':
        tree = ast.parse(path.read_text())
        values = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
        method = 'Conservative Python AST string literals; no external output files'
    elif path.suffix == '.json':
        data = strict_json(path.read_text())
        if isinstance(data, list):
            values = [r['goal'] if 'goal' in r else r['command'] for r in data]
            method = 'JSON array goal/command fields only'
        else:
            values = data.get('fixed_examples', data.get('examples'))
            method = 'JSON fixed_examples/examples only; ignores result metadata'
    else:
        raise ValueError('Unsupported inventory format')
    if not isinstance(values, list) or (not values and path.suffix not in {'.java', '.py'}) or any(not isinstance(s, str) for s in values):
        raise ValueError('Missing/malformed request inventory')
    return [s for s in values if s.strip()], method


def overlap_inventory(protocol):
    required = protocol['corpus']['overlap']['actual_available_required_sources']
    paths = {}
    for entry in required:
        path = ROOT / entry['path']
        if not path.is_file() or sha(path) != entry['sha256_at_protocol']:
            raise ValueError('Required protocol inventory missing/changed: ' + entry['path'])
        paths[path] = entry['sha256_at_protocol']
    # Request/example sources created after prospective protocol, not model outputs.
    for path in (DEV / 'JsonIntentCandidate.java', DEV / 'candidate.json'):
        paths[path] = None
    dev_requests = sorted((DEV / 'build').glob('*/requests.tsv'))
    if not dev_requests:
        raise ValueError('Missing new candidate development request inventory')
    for path in dev_requests:
        paths[path] = None
    # Include newly completed runner/confirmation generic test fixtures at final freeze.
    for folder in (TASK, ROOT / 'prototype/command-json-runner'):
        for path in folder.glob('test*.py'):
            paths[path] = None
    inventory = []
    previous = []
    for path in sorted(paths):
        if not path.is_file():
            raise ValueError('Missing mandatory overlap inventory')
        values, method = extract_requests(path)
        previous.extend(values)
        inventory.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                          'text_count': len(values), 'method': method,
                          'pinned_at_protocol': paths[path] is not None})
    return inventory, previous


def reject_overlap(rows, previous):
    texts = [r['utterance'] for r in rows]
    normalized = [normalize(t) for t in texts]
    if len(set(texts)) != len(texts) or len(set(normalized)) != len(normalized):
        raise ValueError('Within-corpus exact/normalized reuse')
    if set(texts) & set(previous) or set(normalized) & {normalize(t) for t in previous}:
        raise ValueError('Prior/example/development/fixture overlap')


def verify_selection(protocol):
    locked = strict_json((TASK / 'selection-lock.json').read_text())
    files = [(DEV / 'JsonIntentCandidate.java', 'candidate_source_sha256'),
             (DEV / 'candidate.json', 'candidate_metadata_sha256'),
             (TASK / 'protocol.json', 'protocol_sha256'),
             (TASK / 'PROTOCOL.md', 'protocol_markdown_sha256')]
    if any(sha(p) != locked[key] for p, key in files):
        raise ValueError('Candidate/protocol selection lock changed')
    if any(sha(APP / name) != digest for name, digest in locked['selected_source_sha256'].items()):
        raise ValueError('Selected baseline/gate/parser changed')
    metadata = strict_json((DEV / 'candidate.json').read_text())
    if metadata['model_sha256'] != locked['model_sha256'] or metadata['max_tokens'] != 128 or metadata['context'] != 1024 or metadata['threads'] != 4 or metadata['capture_enabled'] is not False or metadata['grammar_sha256'] != locked['grammar_sha256']:
        raise ValueError('Candidate runtime resource mismatch')
    if sha(ROOT / protocol['fixed']['native_path']) != locked['confirmation_native_sha256']:
        raise ValueError('Confirmation native resource mismatch')
    model = ROOT / 'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
    if sha(model) != locked['model_sha256']:
        raise ValueError('Model resource mismatch')
    return locked


def write_new(path, payload):
    with Path(path).open('xb') as stream:
        stream.write(payload)


def generate():
    protocol = strict_json((TASK / 'protocol.json').read_text())
    locked = verify_selection(protocol)
    author = BUILD / 'author-cases.jsonl'
    rows = validate_rows([strict_json(line) for line in author.read_text().splitlines()], protocol)
    inventory, previous = overlap_inventory(protocol)
    reject_overlap(rows, previous)
    cases = b''.join((json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n').encode() for r in rows)
    requests = ''.join(r['id'] + '\t' + r['utterance'] + '\n' for r in rows).encode()
    targets = [BUILD / 'cases.jsonl', BUILD / 'requests.tsv', TASK / 'corpus-manifest.json']
    if any(p.exists() for p in targets):
        raise ValueError('Existing frozen corpus respected; no overwrite')
    projected = sum(p.stat().st_size for p in TASK.rglob('*') if p.is_file()) + len(cases) + len(requests) + 100000
    if projected > protocol['work_budget_bytes']:
        raise ValueError('Corpus work reservation exceeds 2 MB')
    manifest = {'schema': 1, 'scope': 'Fresh informed-author synthetic host confirmation after candidate lock; no model capture/result/promotion',
                'authorized_after_source_commit': AUTHORING_AUTHORIZED_AFTER_COMMIT,
                'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'protocol_sha256': sha(TASK / 'protocol.json'), 'protocol_markdown_sha256': sha(TASK / 'PROTOCOL.md'),
                'selection_lock_sha256': sha(TASK / 'selection-lock.json'),
                'candidate_source_sha256': locked['candidate_source_sha256'],
                'candidate_metadata_sha256': locked['candidate_metadata_sha256'],
                'generator_sha256': sha(Path(__file__)), 'author_cases_sha256': sha(author),
                'cases_sha256': hashlib.sha256(cases).hexdigest(), 'requests_sha256': hashlib.sha256(requests).hexdigest(),
                'selected_source_sha256': locked['selected_source_sha256'],
                'model_sha256': locked['model_sha256'], 'native_sha256': locked['confirmation_native_sha256'],
                'row_count': len(rows), 'families': len({r['family'] for r in rows}),
                'supported_by_intent': dict(Counter(r['semantic_intent'] for r in rows if r['expected_kind'] != 'UNKNOWN')),
                'unknown_rows': sum(r['expected_kind'] == 'UNKNOWN' for r in rows),
                'hard_tag_counts': dict(Counter(t for r in rows for t in r['hard_tags'])),
                'exact_overlap': 0, 'normalized_overlap': 0, 'overlap_inventory': inventory,
                'authoring_note': 'Initial set retained privately; two signed-duration negative rows reworded before capture because ASCII normalization drops sign punctuation. Labels/slots/families retained. No oracle-driven filtering, model outputs or confirmation outcomes used.',
                'authoring_note_sha256': sha(BUILD / 'authoring-note.json'), 'initial_author_cases_sha256': sha(BUILD / 'author-cases-first.jsonl'),
                'pre_capture_overlap_replacement_count': 2,
                'raw_data_private': True, 'model_captures': 0, 'candidate_promoted': False}
    # All content/source/overlap checks finish before any frozen output creation.
    write_new(targets[0], cases)
    write_new(targets[1], requests)
    write_new(targets[2], (json.dumps(manifest, indent=2) + '\n').encode())
    print(json.dumps({'rows': len(rows), 'families': manifest['families'], 'overlap_inventory_count': len(inventory),
                      'cases_sha256': manifest['cases_sha256'], 'requests_sha256': manifest['requests_sha256']}))
    return manifest


if __name__ == '__main__':
    generate()
