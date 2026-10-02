import importlib.util
import copy
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('compact_runner', Path(__file__).with_name('run_evaluation.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
MAP = {'0': 'unknown', '1': 'start_focus', '2': 'pause_focus', '3': 'alarm',
       '4': 'timer', '5': 'open_app', '6': 'explain'}


class CaptureValidity(unittest.TestCase):
    def corpus_fixture(self):
        protocol = json.loads((Path(__file__).parents[1] / 'command-compact-confirm/protocol.json').read_text())
        kind_map = {'start_focus': 'START_FOCUS', 'pause_focus': 'PAUSE_FOCUS', 'alarm': 'ALARM', 'timer': 'TIMER', 'explain': 'EXPLAIN'}
        rows = []
        for intent, count in protocol['corpus']['supported_by_intent'].items():
            for index in range(count):
                kind = ['OPEN_SETTINGS', 'OPEN_CALCULATOR', 'OPEN_CLOCK'][index // 2] if intent == 'open_app' else kind_map[intent]
                number = len(rows)
                rows.append({'id': f'x{number}', 'family': f'f{number // 2}', 'utterance': 'Unexecuted validation fixture',
                             'semantic_intent': intent, 'oracle_intent': intent, 'expected_kind': kind,
                             'hour': 8 if kind == 'ALARM' else 0, 'minute': 0,
                             'seconds': 1 if kind == 'TIMER' else 0, 'hard_tags': []})
        rows[0]['hard_tags'] = protocol['corpus']['hard_tags_assigned_before_capture'][:]
        for _ in range(50):
            number = len(rows)
            rows.append({'id': f'x{number}', 'family': f'f{number // 2}', 'utterance': 'Unexecuted unsupported fixture',
                         'semantic_intent': 'unknown', 'oracle_intent': 'unknown', 'expected_kind': 'UNKNOWN',
                         'hour': 0, 'minute': 0, 'seconds': 0, 'hard_tags': []})
        runner.validate_rows(rows, protocol)
        return rows, protocol

    def test_kind_slots_cannot_be_hidden_by_correct_class_counts(self):
        rows, protocol = self.corpus_fixture()
        for kind, key, value in [('ALARM', 'seconds', 1), ('TIMER', 'seconds', 0), ('TIMER', 'hour', 1),
                                 ('START_FOCUS', 'minute', 1), ('PAUSE_FOCUS', 'seconds', 1), ('OPEN_CLOCK', 'hour', 1)]:
            changed = copy.deepcopy(rows)
            next(r for r in changed if r['expected_kind'] == kind)[key] = value
            with self.subTest(kind=kind, key=key), self.assertRaises(ValueError):
                runner.validate_rows(changed, protocol)

    def test_hard_tag_criteria_cannot_be_made_vacuous(self):
        rows, protocol = self.corpus_fixture()
        rows[0]['hard_tags'] = []
        rows[-1]['hard_tags'] = protocol['corpus']['hard_tags_assigned_before_capture'][:]
        with self.assertRaises(ValueError):
            runner.validate_rows(rows, protocol)

    def test_two_row_families_are_enforced_separately_from_total_rows(self):
        rows, protocol = self.corpus_fixture()
        rows[0]['family'] = rows[2]['family']
        with self.assertRaises(ValueError):
            runner.validate_rows(rows, protocol)

    def test_hard_supported_loss_remains_visible_amid_easy_gains(self):
        rows = [{'id': 'hard', 'family': 'f1', 'semantic_intent': 'pause_focus', 'expected_kind': 'PAUSE_FOCUS', 'hard_tags': ['current_focus_pause']},
                {'id': 'easy1', 'family': 'f2', 'semantic_intent': 'alarm', 'expected_kind': 'ALARM', 'hard_tags': []},
                {'id': 'easy2', 'family': 'f3', 'semantic_intent': 'timer', 'expected_kind': 'TIMER', 'hard_tags': []}]
        old = {'hard': {'intent': 'pause_focus', 'valid': True}, 'easy1': {'intent': 'unknown', 'valid': True}, 'easy2': {'intent': 'unknown', 'valid': True}}
        new = {'hard': {'intent': 'unknown', 'valid': True}, 'easy1': {'intent': 'alarm', 'valid': True}, 'easy2': {'intent': 'timer', 'valid': True}}
        previous = [{'id': r['id'], 'correct': r['id'] == 'hard', 'accepted': r['id'] == 'hard'} for r in rows]
        current = [{'id': r['id'], 'correct': r['id'] != 'hard', 'accepted': r['id'] != 'hard'} for r in rows]
        score, details = runner.paired_summary(rows, old, new, previous, current)
        self.assertEqual(2, score['supported_rows']['gate_gain'])
        self.assertEqual(1, score['supported_rows']['gate_loss'])
        self.assertEqual(1, score['hard_supported']['current_focus_pause']['semantic_loss'])
        self.assertEqual(1, score['hard_supported']['current_focus_pause']['gate_loss'])
        self.assertTrue(next(r for r in details if r['id'] == 'hard')['gate_loss'])

    def test_distribution_retains_missing_metrics_and_nearest_rank_p95(self):
        score = runner.distribution([1, 2, 3, None, float('nan')], 5)
        self.assertEqual(3, score['sample_count'])
        self.assertEqual(2, score['missing_or_nonfinite'])
        self.assertEqual(3, score['nearest_rank_p95'])
        self.assertEqual(2, score['median'])

    def test_truncated_valid_digit_does_not_count_as_unknown_success(self):
        intent, valid = runner.decode_intent({'text': '0', 'metrics': {'reached_eos': False}}, 'candidate', MAP)
        row = {'id': 'x', 'expected_kind': 'UNKNOWN', 'semantic_intent': 'unknown'}
        score = runner.semantic_score([row], {'x': {'intent': intent, 'valid': valid}})
        self.assertEqual(0, score['unknown_correct'])
        self.assertEqual(0, score['schema_and_eos_valid'])

    def test_extra_text_or_unmapped_output_cannot_authorize_an_intent(self):
        for text in ('1 ', '1\n', '12', '7', 'start_focus', '{"intent":"start_focus"}'):
            with self.subTest(text=text):
                self.assertEqual(('unknown', False), runner.decode_intent(
                    {'text': text, 'metrics': {'reached_eos': True}}, 'candidate', MAP))

    def test_same_seven_intents_are_preserved_across_formats(self):
        for digit, intent in MAP.items():
            with self.subTest(intent=intent):
                self.assertEqual((intent, True), runner.decode_intent(
                    {'text': digit, 'metrics': {'reached_eos': True}}, 'candidate', MAP))
                self.assertEqual((intent, True), runner.decode_intent(
                    {'text': '{"intent":"' + intent + '"}', 'metrics': {'reached_eos': True}}, 'baseline', MAP))

    def test_baseline_extra_fields_and_invalid_eos_are_refused(self):
        for raw in ({'text': '{"intent":"alarm","hour":7}', 'metrics': {'reached_eos': True}},
                    {'text': '{"intent":"alarm","intent":"timer"}', 'metrics': {'reached_eos': True}},
                    {'text': '{"intent":"alarm"}', 'metrics': {'reached_eos': False}},
                    {'text': '{"intent":"new_tool"}', 'metrics': {'reached_eos': True}}):
            self.assertEqual(('unknown', False), runner.decode_intent(raw, 'baseline', MAP))

    def test_paired_metric_missing_value_does_not_invent_a_delta(self):
        self.assertIsNone(runner.difference(None, 10))
        self.assertIsNone(runner.difference(20, float('inf')))
        self.assertEqual(-2, runner.difference(8, 10))

    def test_missing_or_unexpected_capture_id_refuses_scoring(self):
        row = {'id': 'x', 'expected_kind': 'ALARM', 'semantic_intent': 'alarm'}
        for outputs in ({}, {'y': {'intent': 'alarm', 'valid': True}}):
            with self.assertRaises(ValueError):
                runner.semantic_score([row], outputs)

    def test_valid_format_does_not_turn_wrong_semantics_into_success(self):
        row = {'id': 'x', 'expected_kind': 'PAUSE_FOCUS', 'semantic_intent': 'pause_focus'}
        score = runner.semantic_score([row], {'x': {'intent': 'start_focus', 'valid': True}})
        self.assertEqual(1, score['schema_and_eos_valid'])
        self.assertEqual(0, score['supported_correct'])
        self.assertEqual(0, score['per_class']['pause_focus']['correct'])


if __name__ == '__main__':
    unittest.main()
