"""Known-wording source-unit regression; preparation has no candidate dependency.

prepare freezes manually labelled old gold and independently parsed quantity/unit
mock replies. evaluate is invoked only after the parent's candidate source freeze.
No model, phone, external API, training or raw-output-based label repair occurs.
"""
import argparse
import base64
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BUILD = TASK / 'build'
KNOWN = ROOT / 'prototype/qwen-natural-validation/build/final-development'
RESULT = ROOT / 'prototype/qwen-natural-validation/development-results.json'
DATA = ROOT / 'prototype/qwen-balanced-data/build'
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
SPLITS = ('train', 'development', 'confirmation-v2')
INTENTS = ('start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown')
WORDS = dict(zip(('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen').split(), range(20)))
WORDS.update(dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), range(20, 100, 10))))
NUMBER_WORDS = set(WORDS) | {'hundred', 'and'}
FACTORS = {'seconds': 1, 'minutes': 60, 'hours': 3600}
SOURCE_NAMES = ('regression.py', 'UnitRegression.java', 'test_regression.py', 'README.md')


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def strict(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def write_new(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, sort_keys=True, indent=2)
        f.write('\n')


def private(path):
    path = Path(path).resolve()
    if BUILD.resolve() not in path.parents:
        raise ValueError('Raw regression data and decisions must remain ignored build/')
    return path


def below_hundred(tokens):
    if len(tokens) == 1 and tokens[0] in WORDS:
        return WORDS[tokens[0]]
    if len(tokens) == 2 and tokens[0] in WORDS and tokens[1] in WORDS and WORDS[tokens[0]] >= 20 and WORDS[tokens[0]] % 10 == 0 and 1 <= WORDS[tokens[1]] <= 9:
        return WORDS[tokens[0]] + WORDS[tokens[1]]
    raise ValueError('Unsupported numeric-word composition')


def number(tokens):
    if len(tokens) == 1 and tokens[0].isdigit():
        return int(tokens[0])
    if 'hundred' not in tokens:
        return below_hundred(tokens)
    if tokens.count('hundred') != 1 or tokens.index('hundred') != 1 or tokens[0] not in WORDS or not 1 <= WORDS[tokens[0]] <= 9:
        raise ValueError('Unsupported hundred phrase')
    tail = tokens[2:]
    if tail and tail[0] == 'and':
        tail = tail[1:]
    return WORDS[tokens[0]] * 100 + (below_hundred(tail) if tail else 0)


def numeric_tail(prefix):
    tokens = re.findall('[a-z]+|[0-9]+', prefix.lower())
    selected = []
    for token in reversed(tokens):
        if token not in NUMBER_WORDS and not token.isdigit():
            break
        selected.insert(0, token)
    # A conjunction before a new numeric quantity belongs to its surrounding clause.
    if selected and selected[0] == 'and':
        selected = selected[1:]
    return selected


def source_quantities(text):
    normalized = text.lower().replace('–', ' ').replace('—', ' ').replace('-', ' ')
    values = []
    for match in re.finditer(r'\b(seconds?|secs?|minutes?|mins?|hours?|hrs?)\b', normalized):
        tokens = numeric_tail(normalized[:match.start()])
        if not tokens:
            continue
        try:
            amount = number(tokens)
        except ValueError:
            continue
        raw_unit = match.group(1)
        unit = 'seconds' if raw_unit.startswith('sec') else 'minutes' if raw_unit.startswith('min') else 'hours'
        values.append({'amount': amount, 'unit': unit, 'seconds': amount * FACTORS[unit],
                       'source_start': match.start(), 'word_number': not (len(tokens) == 1 and tokens[0].isdigit())})
    return values


def source_clock(text):
    lower = text.lower().replace('-', ' ')
    values = []
    for match in re.finditer(r'\b([0-9]{1,2}):([0-9]{2})\b', lower):
        h, m = map(int, match.groups())
        if 0 <= h <= 23 and 0 <= m <= 59:
            values.append((match.start(), h, m))
    for word, hour in (('midnight', 0), ('noon', 12)):
        for match in re.finditer(r'\b' + word + r'\b', lower):
            values.append((match.start(), hour, 0))
    for match in re.finditer(r'\b(am|pm)\b', lower):
        tokens = numeric_tail(lower[:match.start()])
        if not tokens:
            continue
        try:
            hour = number(tokens[:1])
            minute = number(tokens[1:]) if len(tokens) > 1 else 0
        except ValueError:
            continue
        if 1 <= hour <= 12 and 0 <= minute <= 59:
            values.append((match.start(), hour % 12 + (12 if match.group(1) == 'pm' else 0), minute))
    return {'hour': min(values)[1], 'minute': min(values)[2]} if values else None


def source_app(text):
    match = re.search(r'\b(settings|calculator|clock)\b', text.lower())
    return match.group(1) if match else None


def expected_tuple(row):
    return row['expected_kind'], row['hour'], row['minute'], row['seconds']


def source_reply(row, route):
    """One deterministic mock reply per route; only correct gold routes are oracles.

    Wrong/unknown routes use first source quantity, time or app when present. Valid
    fallback slots stress semantic rejection when that source slot is absent.
    No fallback is allowed for supported correct routes: source and manual gold
    must independently agree. Never derive source-unit amounts from gold seconds.
    """
    reply = {'intent': route}
    supported_correct = row['expected_kind'] != 'UNKNOWN' and route == row['intent']
    quantities = source_quantities(row['utterance'])
    if route in {'start_focus', 'timer'}:
        if supported_correct:
            if row['seconds'] == 0 and route == 'start_focus':
                if quantities:
                    raise ValueError('Untimed gold contains numeric duration')
                amount, unit = 0, 'none'
            else:
                if len(quantities) != 1 or quantities[0]['seconds'] != row['seconds']:
                    raise ValueError('Independent source quantity/unit disagrees with manual slots: ' + row['id'])
                amount, unit = quantities[0]['amount'], quantities[0]['unit']
        elif quantities:
            amount, unit = quantities[0]['amount'], quantities[0]['unit']
        else:
            amount, unit = (0, 'none') if route == 'start_focus' else (1, 'seconds')
        reply.update(amount=amount, unit=unit)
    elif route == 'alarm':
        clock = source_clock(row['utterance'])
        if supported_correct and (clock is None or (clock['hour'], clock['minute']) != (row['hour'], row['minute'])):
            raise ValueError('Independent source clock disagrees with manual slots: ' + row['id'])
        reply.update(clock or {'hour': 0, 'minute': 0})
    elif route == 'open_app':
        app = source_app(row['utterance'])
        expected = {'OPEN_SETTINGS': 'settings', 'OPEN_CALCULATOR': 'calculator', 'OPEN_CLOCK': 'clock'}.get(row['expected_kind'])
        if supported_correct and app != expected:
            raise ValueError('Independent source app disagrees with manual target: ' + row['id'])
        reply['app'] = app or 'clock'
    elif route not in {'pause_focus', 'explain', 'unknown'}:
        raise ValueError('Unknown route label')
    return reply


def known_inputs():
    report = strict(RESULT.read_text())
    pinned = {str(RESULT): sha(RESULT)}
    for name in ('known-all-routes.tsv', 'baseline-known-output.tsv'):
        path = KNOWN / name
        if sha(path) != report['raw_artifacts_sha256'][name]:
            raise ValueError('Pinned historical route/output changed')
        pinned[str(path)] = sha(path)
    rows = []
    for split in SPLITS:
        path = DATA / (split + '.jsonl')
        if sha(path) != report['development_data_sha256'][split]:
            raise ValueError('Pinned historical gold changed')
        pinned[str(path)] = sha(path)
        rows.extend((split, strict(line)) for line in path.read_text().splitlines())
    route_lines = [line.split('\t') for line in (KNOWN / 'known-all-routes.tsv').read_text().splitlines()]
    baseline = [line.split('\t') for line in (KNOWN / 'baseline-known-output.tsv').read_text().splitlines()]
    expected = [(f'd{n:03}_{route}', route, row['utterance']) for n, (_, row) in enumerate(rows) for route in INTENTS]
    if route_lines != [list(value) for value in expected] or [r[0] for r in baseline] != [r[0] for r in expected] or any(len(r) != 6 for r in baseline):
        raise ValueError('Historical ordered route inventory differs')
    if len(rows) != 226 or len(expected) != 1582 or sum(row['expected_kind'] != 'UNKNOWN' for _, row in rows) != 158 or sum(r[1] != 'UNKNOWN' for r in baseline) != 80:
        raise ValueError('Historical denominator contract differs')
    return rows, expected, baseline, pinned


def prepare(out):
    out = private(out)
    if out.exists() or (TASK / 'readiness.json').exists():
        raise ValueError('Preserve existing preparation')
    rows, routes, baseline, pinned = known_inputs()
    records, inputs = [], []
    for n, (split, row) in enumerate(rows):
        for j, route in enumerate(INTENTS):
            ident = routes[n * 7 + j][0]
            reply = source_reply(row, route)
            old_fields = baseline[n * 7 + j]
            old_kind_slots = (old_fields[1], *(int(x) for x in old_fields[2:5]))
            if old_kind_slots[0] != 'UNKNOWN' and old_kind_slots != expected_tuple(row):
                raise ValueError('Historical accepted proposal is not manual complete gold')
            records.append({'route_id': ident, 'split': split, 'row_id': row['id'], 'intent': row['intent'],
                'route': route, 'supported': row['expected_kind'] != 'UNKNOWN',
                'correct_route': row['expected_kind'] != 'UNKNOWN' and route == row['intent'],
                'expected_kind_slots': list(expected_tuple(row)), 'old_kind_slots': list(old_kind_slots),
                'reply': reply, 'source_quantities': source_quantities(row['utterance'])})
            encoded = base64.b64encode(json.dumps(reply, separators=(',', ':')).encode()).decode()
            inputs.append(ident + '\t' + encoded + '\t' + row['utterance'] + '\n')
    out.mkdir(parents=True)
    (out / 'unit-input.tsv').write_text(''.join(inputs))
    write_new(out / 'route-gold.json', records)
    readiness = {'schema': 'focuspilot.unit_regression_preparation.v1', 'development_only': True,
        'fresh_confirmation': False, 'candidate_contents_read': False, 'model_calls': 0, 'phone_calls': 0,
        'candidate_calls': 0, 'known_rows': 226, 'routes': 1582, 'supported_correct_routes': 158,
        'actual_prior_accepted': 80, 'unknown_routes': 476, 'supported_wrong_routes': 948,
        'input': str(out / 'unit-input.tsv'), 'gold': str(out / 'route-gold.json'),
        'input_sha256': sha(out / 'unit-input.tsv'), 'gold_sha256': sha(out / 'route-gold.json'),
        'prior_pinned_sha256': pinned,
        'generic_sources_sha256': {name: sha(TASK / name) for name in SOURCE_NAMES},
        'source_unit_policy': 'Parse numeric quantities and units independently from source text; supported correct slots must agree with old manual gold; never divide gold seconds to infer an amount/unit',
        'wrong_route_policy': 'One deterministic mock response per route using first source quantity/time/allowed app where present, valid fallback when absent. Multiple-quantity adversaries use first quantity; this is not exhaustive output safety.',
        'canonical_preservation': 'Compare accepted kind/hour/minute/seconds and approved app mapping; human preview wording may change',
        'timed_supported_unit_counts': dict(Counter(source_reply(row, row['intent'])['unit'] for _, row in rows if row['intent'] in {'start_focus', 'timer'} and row['expected_kind'] != 'UNKNOWN')),
        'limitations': ['Known previously exposed correlated synthetic wording; development only',
                        'Oracle/mock replies are not model predictions or accuracy evidence',
                        'Finite all-intent routes do not cover arbitrary output values',
                        'No Android execution, phone, NPU, fresh/general safety or promotion claim']}
    write_new(TASK / 'readiness.json', readiness)
    return readiness


def evaluate(source_commit, unit_source, structured_source, number_source, out):
    if not re.fullmatch('[0-9a-f]{40}', source_commit):
        raise ValueError('Full explicitly authorized source-freeze commit required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', source_commit, 'HEAD'], cwd=ROOT, check=True, capture_output=True, timeout=10)
    readiness = strict((TASK / 'readiness.json').read_text())
    for name, digest in readiness['generic_sources_sha256'].items():
        if sha(TASK / name) != digest:
            raise ValueError('Prepared generic source changed')
    for path, digest in readiness['prior_pinned_sha256'].items():
        if sha(path) != digest:
            raise ValueError('Pinned historical evidence changed')
    for path, digest in ((readiness['input'], readiness['input_sha256']), (readiness['gold'], readiness['gold_sha256'])):
        if sha(path) != digest:
            raise ValueError('Frozen prepared mock responses/gold changed')
    sources = [Path(p).resolve() for p in (unit_source, structured_source, number_source)]
    if [p.name for p in sources] != ['UnitCommand.java', 'StructuredCommand.java', 'CommandNumberWords.java']:
        raise ValueError('Exact parent-approved Java source identities required')
    bindings = {}
    # Bind the prepared expectations/inputs metadata itself to the authorized
    # commit, without placing its own digest inside that metadata.
    for path in [*sources, *(TASK / name for name in SOURCE_NAMES), TASK / 'readiness.json']:
        relative = str(path.relative_to(ROOT))
        committed = subprocess.check_output(['git', 'show', source_commit + ':' + relative], cwd=ROOT, timeout=10)
        if committed != path.read_bytes():
            raise ValueError('Source changed from authorized commit: ' + relative)
        bindings[relative] = sha(path)
    out = private(out)
    out.mkdir(parents=True, exist_ok=False)
    classes = out / 'classes'; classes.mkdir()
    subprocess.run([str(JAVA / 'javac'), '-d', str(classes), *(str(p) for p in sources), str(TASK / 'UnitRegression.java')], check=True, timeout=30)
    output = out / 'unit-decisions.tsv'
    with output.open('x') as f:
        subprocess.run([str(JAVA / 'java'), '-cp', str(classes), 'dev.focuspilot.prototype.UnitRegression', readiness['input']], stdout=f, check=True, timeout=30)
    gold = strict(Path(readiness['gold']).read_text())
    lines = [line.split('\t') for line in output.read_text().splitlines()]
    if len(lines) != 1582 or [line[0] for line in lines] != [r['route_id'] for r in gold] or any(len(line) != 9 for line in lines):
        raise ValueError('Incomplete/reordered candidate decision inventory')
    counts = {'prior_accepted': 0, 'prior_preserved': 0, 'prior_regressions': 0,
        'supported_oracle_routes': 0, 'supported_oracle_complete': 0, 'supported_oracle_wrong_accepts': 0,
        'unknown_routes': 0, 'unknown_false_accepts': 0,
        'supported_wrong_routes': 0, 'supported_wrong_route_false_accepts': 0}
    details = []
    by_split = {split: {'supported_oracle': 0, 'complete': 0} for split in SPLITS}
    for fields, row in zip(lines, gold):
        if fields[1] not in {'true', 'false'}:
            raise ValueError('Actual acceptance boolean required')
        accepted = fields[1] == 'true'
        proposal = (fields[2], *(int(x) for x in fields[3:6]))
        canonical = strict(base64.b64decode(fields[7]).decode('utf-8'))
        reason = base64.b64decode(fields[8]).decode('utf-8')
        preserved = row['old_kind_slots'][0] == 'UNKNOWN' or (accepted and proposal == tuple(row['old_kind_slots']))
        complete = accepted and proposal == tuple(row['expected_kind_slots'])
        if row['old_kind_slots'][0] != 'UNKNOWN':
            counts['prior_accepted'] += 1; counts['prior_preserved'] += preserved; counts['prior_regressions'] += not preserved
        if row['correct_route']:
            counts['supported_oracle_routes'] += 1; counts['supported_oracle_complete'] += complete
            counts['supported_oracle_wrong_accepts'] += accepted and not complete
            by_split[row['split']]['supported_oracle'] += 1; by_split[row['split']]['complete'] += complete
        elif not row['supported']:
            counts['unknown_routes'] += 1; counts['unknown_false_accepts'] += accepted
        else:
            counts['supported_wrong_routes'] += 1; counts['supported_wrong_route_false_accepts'] += accepted
        details.append({'route_id': row['route_id'], 'row_id': row['row_id'], 'accepted': accepted,
            'proposal': list(proposal), 'canonical': canonical, 'reason': reason,
            'correct_route': row['correct_route'], 'supported': row['supported'],
            'old_accepted_preserved': preserved, 'complete_gold': complete})
    if (counts['prior_accepted'], counts['supported_oracle_routes'], counts['unknown_routes'], counts['supported_wrong_routes']) != (80, 158, 476, 948):
        raise ValueError('Regression denominators changed')
    write_new(out / 'details.json', details)
    result = {'schema': 'focuspilot.unit_known_regression.v1', 'development_only': True,
        'fresh_confirmation': False, 'source_authorization_commit': source_commit, 'model_calls': 0, 'phone_calls': 0,
        'counts': counts, 'by_known_split': by_split,
        'source_sha256': bindings, 'readiness_sha256': sha(TASK / 'readiness.json'),
        'decision_output_sha256': sha(output), 'details_sha256': sha(out / 'details.json'),
        'preservation_and_false_accept_checks_pass': counts['prior_regressions'] == counts['supported_oracle_wrong_accepts'] == counts['unknown_false_accepts'] == counts['supported_wrong_route_false_accepts'] == 0,
        'preview_preservation_required': False, 'promoted': False,
        'limitations': readiness['limitations'] + [readiness['wrong_route_policy']]}
    write_new(out / 'results.json', result)
    write_new(TASK / 'results.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='stage', required=True)
    preparation = sub.add_parser('prepare'); preparation.add_argument('--out', default=str(BUILD / 'prepared'))
    evaluation = sub.add_parser('evaluate')
    for flag in ('source-commit', 'unit-source', 'structured-source', 'number-source', 'out'):
        evaluation.add_argument('--' + flag, required=True)
    a = p.parse_args()
    result = prepare(a.out) if a.stage == 'prepare' else evaluate(a.source_commit, a.unit_source, a.structured_source, a.number_source, a.out)
    print(json.dumps(result, indent=2))
