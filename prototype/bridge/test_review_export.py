"""Synthetic temporary fixtures only; never reads a user's private export."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import review_export as bridge


def fixture():
    context = {'mapping': 'selected-events-v1', 'budget_ms': 60_000,
               'continuous_limit_ms': 60_000, 'planned_focus_ms': 60_000,
               'goal_sha256': 'abcdef0123456789' * 4}
    record = {'id': 1, 'label': 'ALLOW', 'provenance': 'REAL_OBSERVATION',
              'context': dict(context), 'observed_at_wall_ms': 1000,
              'observed_at_elapsed_ms': 100, 'labeled_at_elapsed_ms': 200,
              'features': [0, .1, .2, .3, .4, .5]}
    return {'schema': 1, 'kind': 'focuspilot-private-summary', 'research_only': True,
            'exported_at_wall_ms': 2000, 'selected_package': 'org.synthetic.selected',
            'settings': dict(context), 'observation_enabled': True,
            'live_matching_enabled': False, 'virtual_points': 95, 'money_moved': False,
            'focus_elapsed_ms': 1000, 'focus_active': False, 'records': [record]}


def payload(data):
    return json.dumps(data).encode('utf-8')


class ExportReviewTests(unittest.TestCase):
    def test_replays_existing_policy_without_training(self):
        data = fixture()
        report = bridge.review(data, bridge.sha(payload(data)))
        model, threshold = bridge.load_existing_policy()
        expected = model.probability(data['records'][0]['features'])
        self.assertEqual(expected, report['groups'][0]['score']['mean'])
        self.assertFalse(report['policy']['retrained'])
        self.assertFalse(report['phone_actions_executed'])
        self.assertFalse(report['officekit_transport_verified'])
        self.assertFalse(report['npu_verified'])

    def test_exact_original_context_grouping_includes_goal_and_all_limits(self):
        data = fixture()
        for index, key in enumerate(('goal_sha256', 'budget_ms', 'continuous_limit_ms', 'planned_focus_ms'), 2):
            row = copy.deepcopy(data['records'][0]); row['id'] = index
            row['context'][key] = ('1' * 64) if key == 'goal_sha256' else 120000
            data['records'].append(row)
        same = copy.deepcopy(data['records'][0]); same['id'] = 6
        data['records'].append(same)
        report = bridge.review(data, bridge.sha(payload(data)))
        self.assertEqual(5, report['context_count'])
        self.assertEqual([2, 1, 1, 1, 1], [g['record_count'] for g in report['groups']])

    def test_report_omits_private_input_fields_and_does_not_claim_accuracy(self):
        data = fixture(); report = bridge.review(data, bridge.sha(payload(data)))
        rendered = json.dumps(report)
        for value in (data['selected_package'], data['settings']['goal_sha256']):
            self.assertNotIn(value, rendered)
        for key in ('goal_sha256', 'selected_package', 'observed_at_wall_ms', 'observed_at_elapsed_ms', 'features', 'focus_elapsed_ms'):
            self.assertNotIn('"' + key + '"', rendered)
        self.assertNotIn('accuracy', report['groups'][0])
        self.assertEqual({'context_index', 'record_count', 'score', 'shadow_nudge_count',
                          'manual_nudge_label_count', 'label_agreement_count'}, set(report['groups'][0]))

    def test_unknown_keys_are_rejected_at_each_nesting_level(self):
        for location in ('top', 'settings', 'record', 'context'):
            data = fixture()
            target = {'top': data, 'settings': data['settings'], 'record': data['records'][0],
                      'context': data['records'][0]['context']}[location]
            target['raw_ui_text'] = 'synthetic secret'
            with self.assertRaises(ValueError): bridge.parse_payload(payload(data))

    def test_duplicate_keys_and_nan_tokens_are_rejected(self):
        raw = payload(fixture())
        for broken in (raw.replace(b'"id": 1', b'"id": 1, "id": 1'),
                       raw.replace(b'"schema": 1', b'"schema": 1, "schema": 1'),
                       raw.replace(b'[0, 0.1', b'[NaN, 0.1'), raw.replace(b'[0, 0.1', b'[Infinity, 0.1')):
            with self.assertRaises(ValueError): bridge.parse_payload(broken)

    def test_byte_limit_is_applied_before_json_parse_and_utf8_is_strict(self):
        with patch.object(bridge.json, 'loads') as parse:
            with self.assertRaises(ValueError): bridge.parse_payload(b'x' * 80001)
            parse.assert_not_called()
        with self.assertRaises(ValueError): bridge.parse_payload(b'\xff')
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'oversized.json'; file.write_bytes(b'x' * 80001)
            with patch.object(bridge, 'parse_payload') as parse:
                with self.assertRaises(ValueError): bridge.read_input(file)
                parse.assert_not_called()

    def test_boolean_numeric_fields_and_unsafe_integers_are_rejected(self):
        for key in ('schema', 'virtual_points', 'exported_at_wall_ms', 'focus_elapsed_ms'):
            data = fixture(); data[key] = True
            with self.assertRaises(ValueError): bridge.validate(data)
        for key in ('id', 'observed_at_elapsed_ms', 'labeled_at_elapsed_ms'):
            for bad in (True, -1, bridge.MAX_INTEGER + 1):
                data = fixture(); data['records'][0][key] = bad
                with self.assertRaises(ValueError): bridge.validate(data)

    def test_six_finite_bounded_features_required(self):
        for bad in (True, float('nan'), float('inf'), 10 ** 1000, -.1, 1.1, '0.5', None):
            data = fixture(); data['records'][0]['features'][0] = bad
            with self.assertRaises(ValueError): bridge.validate(data)
        data = fixture(); data['records'][0]['features'].pop()
        with self.assertRaises(ValueError): bridge.validate(data)

    def test_32_distinct_records_accept_33_or_duplicate_reject(self):
        data = fixture()
        data['records'] = [dict(copy.deepcopy(data['records'][0]), id=index) for index in range(1, 33)]
        self.assertEqual(32, len(bridge.parse_payload(payload(data))['records']))
        data['records'].append(dict(copy.deepcopy(data['records'][0]), id=33))
        with self.assertRaises(ValueError): bridge.validate(data)
        data['records'].pop(); data['records'][1]['id'] = 1
        with self.assertRaises(ValueError): bridge.validate(data)

    def test_flags_provenance_context_and_time_boundaries(self):
        cases = [('research_only', False), ('money_moved', True), ('focus_active', 1), ('virtual_points', 101)]
        for key, value in cases:
            data = fixture(); data[key] = value
            with self.assertRaises(ValueError): bridge.validate(data)
        for key, value in [('provenance', 'SYNTHETIC'), ('observed_at_wall_ms', 2001),
                           ('labeled_at_elapsed_ms', 99), ('labeled_at_elapsed_ms', 15101)]:
            data = fixture(); data['records'][0][key] = value
            with self.assertRaises(ValueError): bridge.validate(data)
        for key, value in [('mapping', 'unknown'), ('goal_sha256', 'raw goal'),
                           ('budget_ms', 59999), ('planned_focus_ms', 0)]:
            data = fixture(); data['records'][0]['context'][key] = value
            with self.assertRaises(ValueError): bridge.validate(data)
        data = fixture(); data['records'][0]['labeled_at_elapsed_ms'] = 15100
        bridge.validate(data)

    def test_expected_hash_detects_modified_transport_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'chosen.json'; raw = payload(fixture()); file.write_bytes(raw)
            _, identity = bridge.read_input(file, bridge.sha(raw)); self.assertEqual(bridge.sha(raw), identity)
            file.write_bytes(raw + b' ')
            with self.assertRaises(ValueError): bridge.read_input(file, identity)

    def test_empty_export_has_no_invented_scores(self):
        data = fixture(); data['records'] = []
        report = bridge.review(data, bridge.sha(payload(data)))
        self.assertEqual([], report['groups']); self.assertEqual(0, report['context_count'])

    def test_changed_policy_identity_blocks_before_import(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bridge, 'ROOT', Path(directory)):
            policy = Path(directory) / 'prototype/policy'; policy.mkdir(parents=True)
            (policy / 'policy.py').write_text('raise Exception("must never execute")')
            with self.assertRaises(ValueError): bridge.load_existing_policy()

    def test_output_only_new_ignored_artifacts_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bridge, 'ROOT', Path(directory)):
            root = Path(directory); (root / 'artifacts').mkdir(); (root / '.gitignore').write_text('artifacts/*\n')
            subprocess.run(['git', 'init', '--quiet', directory], check=True)
            report = {'research_only': True}; target = root / 'artifacts/review.json'
            bridge.write_report(target, report); self.assertEqual(report, json.loads(target.read_text()))
            with self.assertRaises(FileExistsError): bridge.write_report(target, report)
            with self.assertRaises(ValueError): bridge.write_report(root / 'tracked.json', report)
            with self.assertRaises(ValueError): bridge.write_report(root / 'artifacts/.secret', report)
            (root / 'artifacts/link').symlink_to(root.parent)
            with self.assertRaises(ValueError): bridge.write_report(root / 'artifacts/link/escape.json', report)

    def test_cli_failure_does_not_echo_private_path_or_values(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'private-identity.json'; file.write_text('{"raw_goal":"private fixture text"}')
            result = subprocess.run([sys.executable, str(Path(bridge.__file__)), '--input', str(file)], capture_output=True, text=True)
            self.assertEqual(2, result.returncode); self.assertEqual('', result.stdout)
            self.assertNotIn(directory, result.stderr); self.assertNotIn('private fixture', result.stderr)


if __name__ == '__main__':
    unittest.main()
