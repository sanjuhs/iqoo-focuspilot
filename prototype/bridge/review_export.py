#!/usr/bin/env python3
"""Explicit offline summary review. No discovery, network, phone actions or retraining."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 80_000
MAX_RECORDS = 32
MAX_INTEGER = 9_007_199_254_740_991
POLICY_SOURCE_SHA = '52810b9e0d982d3d04cd611bb9b908ce0d69c8fde77069055d594d8ad5ce178c'
CHECKPOINT_SHA = '6924de782bd52944d5bf87352f9a7dd0bc1e4e0518bcd5ba04f9ea6fcffb67b8'
TOP_KEYS = {'schema', 'kind', 'research_only', 'exported_at_wall_ms', 'selected_package',
            'settings', 'observation_enabled', 'live_matching_enabled', 'virtual_points',
            'money_moved', 'focus_elapsed_ms', 'focus_active', 'records'}
CONTEXT_KEYS = {'mapping', 'budget_ms', 'continuous_limit_ms', 'planned_focus_ms', 'goal_sha256'}
RECORD_KEYS = {'id', 'label', 'provenance', 'context', 'observed_at_wall_ms',
               'observed_at_elapsed_ms', 'labeled_at_elapsed_ms', 'features'}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def invalid_constant(value: str) -> None:
    raise ValueError('Nonfinite JSON number')


def exact_keys(value: object, keys: set[str], message: str) -> None:
    require(type(value) is dict and set(value) == keys, message)


def integer(value: object, minimum: int = 0, maximum: int = MAX_INTEGER) -> bool:
    return type(value) is int and minimum <= value <= maximum


def context(value: object, complete: bool = False) -> tuple:
    exact_keys(value, CONTEXT_KEYS, 'Unknown or incomplete context fields')
    require(value['mapping'] == 'selected-events-v1', 'Unknown feature mapping')
    require(integer(value['budget_ms'], 60_000, 7_200_000), 'Invalid budget')
    minimum = 1 if complete else 0
    require(integer(value['continuous_limit_ms'], minimum, 86_400_000) and
            integer(value['planned_focus_ms'], minimum, 86_400_000), 'Invalid declared limits')
    require(type(value['goal_sha256']) is str and
            re.fullmatch('[0-9a-f]{64}', value['goal_sha256']) is not None, 'Invalid goal hash')
    # Exact context identity is deliberately never serialized to output.
    return tuple(value[key] for key in sorted(CONTEXT_KEYS))


def validate(data: object) -> dict:
    exact_keys(data, TOP_KEYS, 'Unknown or incomplete export fields')
    require(integer(data['schema'], 1, 1) and data['kind'] == 'focuspilot-private-summary', 'Unknown export schema/kind')
    require(data['research_only'] is True and data['money_moved'] is False, 'Research/virtual-money flags required')
    for name in ('observation_enabled', 'live_matching_enabled', 'focus_active'):
        require(type(data[name]) is bool, 'Invalid boolean setting')
    require(integer(data['exported_at_wall_ms'], 1) and integer(data['focus_elapsed_ms']), 'Invalid export/session time')
    require(integer(data['virtual_points'], 0, 100), 'Invalid virtual balance')
    package = data['selected_package']
    require(type(package) is str and len(package) <= 255 and
            re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+', package) is not None, 'Invalid selected package')
    context(data['settings'])
    records = data['records']
    require(type(records) is list and len(records) <= MAX_RECORDS, 'At most 32 records required')
    seen = set()
    for record in records:
        exact_keys(record, RECORD_KEYS, 'Unknown or incomplete record fields')
        require(integer(record['id'], 1) and record['id'] not in seen, 'Invalid or duplicate record ID')
        seen.add(record['id'])
        require(record['label'] in ('ALLOW', 'NUDGE') and type(record['label']) is str, 'Invalid label')
        require(record['provenance'] == 'REAL_OBSERVATION', 'Only real-observation provenance supported')
        context(record['context'], complete=True)
        wall, elapsed, labeled = (record[key] for key in
                                 ('observed_at_wall_ms', 'observed_at_elapsed_ms', 'labeled_at_elapsed_ms'))
        require(integer(wall, 1, data['exported_at_wall_ms']) and integer(elapsed) and
                integer(labeled) and 0 <= labeled - elapsed <= 15_000, 'Invalid observation/label time')
        values = record['features']
        require(type(values) is list and len(values) == 6 and
                all(type(v) in (int, float) and 0 <= v <= 1 and math.isfinite(v) for v in values),
                'Six finite features within 0..1 required')
    return data


def parse_payload(payload: bytes) -> dict:
    require(type(payload) is bytes and len(payload) <= MAX_BYTES, 'Input exceeds 80,000 bytes')
    try:
        decoded = payload.decode('utf-8', errors='strict')
        data = json.loads(decoded, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError('Invalid UTF-8/JSON export') from error
    return validate(data)


def read_input(path: Path, expected_sha: str | None = None) -> tuple[dict, str]:
    require(stat.S_ISREG(path.stat().st_mode), 'Input must be one regular file')
    require(path.stat().st_size <= MAX_BYTES, 'Input exceeds 80,000 bytes')
    with path.open('rb') as stream:
        payload = stream.read(MAX_BYTES + 1)
    require(len(payload) <= MAX_BYTES, 'Input exceeds 80,000 bytes')
    observed_sha = sha(payload)
    if expected_sha is not None:
        require(re.fullmatch('[0-9a-f]{64}', expected_sha) is not None and expected_sha == observed_sha,
                'Input checksum does not match expected SHA256')
    return parse_payload(payload), observed_sha


def load_existing_policy():
    """Reuse the pinned implementation; refuse changed code/checkpoint before import."""
    directory = ROOT / 'prototype/policy'
    require(sha((directory / 'policy.py').read_bytes()) == POLICY_SOURCE_SHA, 'Policy implementation identity changed')
    checkpoint = (directory / 'synthetic-model.json').read_bytes()
    require(sha(checkpoint) == CHECKPOINT_SHA, 'Policy checkpoint identity changed')
    # Import only this trusted repository file, never a module from the input directory.
    import importlib.util
    spec = importlib.util.spec_from_file_location('focuspilot_bridge_existing_policy', directory / 'policy.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    artifact = json.loads(checkpoint)
    require(artifact['schema'] == 'focuspilot.synthetic-positive-policy.v1' and
            artifact['features'] == list(module.FEATURES) and
            module.canonical_hash(artifact['parameters']) == artifact['parameters_sha256'] and
            artifact['implementation_sha256'] == POLICY_SOURCE_SHA, 'Invalid policy checkpoint metadata')
    threshold = artifact['training']['threshold']
    require(type(threshold) in (int, float) and math.isfinite(threshold) and 0 <= threshold <= 1, 'Invalid policy threshold')
    return module.PositiveNetwork(artifact['parameters']), threshold


def review(data: dict, input_sha: str) -> dict:
    validate(data)
    require(type(input_sha) is str and re.fullmatch('[0-9a-f]{64}', input_sha) is not None, 'Input SHA256 required')
    model, threshold = load_existing_policy()
    groups = {}
    for record in data['records']:
        identity = context(record['context'], complete=True)
        groups.setdefault(identity, []).append(record)
    aggregates = []
    for index, records in enumerate(groups.values(), start=1):
        scores = [model.probability(record['features']) for record in records]
        proposed_nudges = [score >= threshold for score in scores]
        aggregates.append({'context_index': index, 'record_count': len(records),
                           'score': {'minimum': min(scores), 'maximum': max(scores), 'mean': sum(scores) / len(scores)},
                           'shadow_nudge_count': sum(proposed_nudges),
                           'manual_nudge_label_count': sum(record['label'] == 'NUDGE' for record in records),
                           'label_agreement_count': sum(proposed == (record['label'] == 'NUDGE')
                                                        for proposed, record in zip(proposed_nudges, records))})
    return {'schema': 1, 'kind': 'focuspilot-laptop-shadow-review', 'research_only': True,
            'input_sha256': input_sha, 'record_count': len(data['records']), 'context_count': len(groups),
            'provenance': 'input declares REAL_OBSERVATION; not independently attested',
            'policy': {'implementation_sha256': POLICY_SOURCE_SHA, 'checkpoint_sha256': CHECKPOINT_SHA,
                       'threshold': threshold, 'backend': 'standard-library Python CPU', 'retrained': False},
            'groups': aggregates, 'phone_actions_executed': False, 'officekit_transport_verified': False,
            'npu_verified': False,
            'limitations': 'Shadow replay of synthetic-trained policy, not live permission/cooldown gates, calibrated risk, held-out human accuracy or transport proof. Aggregate scores remain private.'}


def write_report(path: Path, report: dict) -> None:
    """Only explicit ignored artifacts destination; never overwrite an existing file."""
    resolved = path.resolve()
    artifacts = (ROOT / 'artifacts').resolve()
    require(resolved.is_relative_to(artifacts) and resolved != artifacts and
            all(not part.startswith('.') for part in resolved.relative_to(artifacts).parts),
            'Output must be inside ignored artifacts/')
    ignored = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '--quiet', '--', str(resolved)],
                             capture_output=True, check=False)
    require(ignored.returncode == 0, 'Output must be ignored by Git')
    require(resolved.parent.is_dir(), 'Output parent directory must already exist')
    payload = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    require(len(payload) < 80_000, 'Report exceeds byte limit')
    with resolved.open('xb') as stream:
        stream.write(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='One explicitly chosen private summary; no discovery')
    parser.add_argument('--expected-sha256', help='Optional previously recorded payload SHA256; integrity only')
    parser.add_argument('--output', type=Path, help='Optional new report under ignored artifacts/; otherwise stdout')
    args = parser.parse_args()
    try:
        data, input_sha = read_input(args.input, args.expected_sha256)
        report = review(data, input_sha)
        if args.output:
            require(args.output.resolve() != args.input.resolve(), 'Output cannot overwrite input')
            write_report(args.output, report)
        else:
            print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, OverflowError, TypeError) as error:
        # Do not echo paths, JSON values, app identity, raw vectors or provider errors.
        print('Review failed: invalid/unavailable input, changed policy identity, or unsafe output destination.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
