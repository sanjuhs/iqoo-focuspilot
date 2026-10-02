"""Gate-only confirmation failure tests; no inference or real corpus data."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('gate_v14_runner', Path(__file__).with_name('run_evaluation.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
gate = runner.load_module(runner.GATE_HELPER, runner.GATE_HELPER_SHA, 'v14_gate_test')


def toy_row(identifier='a', kind='TIMER', intent='timer', seconds=30):
    return dict(id=identifier, family='toy', expected_kind=kind, semantic_intent=intent,
                hour=0, minute=0, seconds=seconds, hard_tags=['toy'])


class ScoringTests(unittest.TestCase):
    def test_single_capture_reporting_replaces_inherited_two_load_description(self):
        model = {'timing_limit': 'Host CPU, separate baseline then candidate loads',
                 'first_native_ms': 9, 'subsequent_total_ms': {'median': 2}}
        runner.describe_shared_capture(model)
        self.assertIn('Single host CPU original-prompt capture shared by both gates', model['timing_limit'])
        self.assertNotIn('separate baseline then candidate loads', str(model))
        self.assertEqual(9, model['first_native_ms'])
        self.assertEqual({'median': 2}, model['subsequent_total_ms'])

    def test_same_semantic_prediction_does_not_hide_complete_slot_regression(self):
        rows = [toy_row()]
        _, old = gate.strict_score(rows, {'a': ('TIMER', 0, 0, 30)})
        new_score, new = gate.strict_score(rows, {'a': ('TIMER', 0, 0, 300)})
        outputs = {'a': {'intent': 'timer', 'valid': True}}
        paired, _ = runner.paired_summary(rows, outputs, outputs, old, new)
        self.assertEqual(0, paired['all_rows']['semantic_loss'])
        self.assertEqual(1, paired['supported_rows']['gate_loss'])
        self.assertEqual(1, new_score['supported_wrong_slots'])
        self.assertEqual(1, new_score['wrong_accepted'])

    def test_unknown_invalid_fallback_never_counts_raw_semantic_success(self):
        row = toy_row(kind='UNKNOWN', intent='unknown', seconds=0)
        raw = {'text': '{"intent":"unknown"}', 'metrics': {'reached_eos': False}}
        intent, valid = runner.decode_intent(raw)
        score = runner.semantic_score([row], {'a': {'intent': intent, 'valid': valid}})
        self.assertEqual(0, score['semantic_correct'])
        gate_score, details = gate.strict_score([row], {'a': ('UNKNOWN', 0, 0, 0)})
        runner.augment_gate(gate_score, details, [row], {'a': {'intent': intent, 'valid': valid}})
        self.assertEqual(1, gate_score['invalid_output_fallback_abstentions'])
        self.assertEqual(1, gate_score['correct_abstentions'])

    def test_duplicate_json_or_noncanonical_serialization_abstains(self):
        for text in ('{"intent":"timer","intent":"unknown"}', '{ "intent": "timer" }', '4'):
            self.assertEqual(('unknown', False), runner.decode_intent({'text': text, 'metrics': {'reached_eos': True}}))

    def test_missing_ids_and_order_mismatch_refuse_confirmation(self):
        with self.assertRaises(ValueError):
            runner.semantic_score([toy_row()], {})
        with self.assertRaises(ValueError):
            runner.shared.require_complete_capture([toy_row('a'), toy_row('b')], {'b': {}, 'a': {}})


class PromotionTests(unittest.TestCase):
    def setUp(self):
        zero = dict(semantic_gain=0, semantic_loss=0, gate_gain=0, gate_loss=0,
                    baseline_wrong_accept=0, candidate_wrong_accept=0)
        self.gates = {route: {arm: {'wrong_accepted': 0} for arm in ('baseline', 'candidate')}
                      for route in ('generated', 'oracle')}
        self.pairs = {'generated': {'supported_gains': 4, 'supported_losses': 0},
                      'oracle': {'supported_gains': 0, 'supported_losses': 0}}
        self.full = {route: {'per_intent': {intent: dict(zero) for intent in runner.shared.INTENTS}}
                     for route in ('generated', 'oracle')}
        self.full['generated']['per_intent']['timer']['gate_gain'] = 4
        self.model = {'schema_and_eos_valid': 100}

    def test_passing_is_review_only_not_automatic_promotion(self):
        result = runner.promotion_review(self.gates, self.pairs, self.full, self.model)
        self.assertTrue(result['prospective_criteria_met'])
        self.assertFalse(result['candidate_promoted'])

    def test_oracle_loss_or_wrong_accept_cannot_hide_behind_generated_gains(self):
        pairs = copy.deepcopy(self.pairs)
        pairs['oracle']['supported_losses'] = 1
        self.assertFalse(runner.promotion_review(self.gates, pairs, self.full, self.model)['prospective_criteria_met'])
        for route in self.gates:
            for arm in self.gates[route]:
                bad = copy.deepcopy(self.gates)
                bad[route][arm]['wrong_accepted'] = 1
                self.assertFalse(runner.promotion_review(bad, self.pairs, self.full, self.model)['prospective_criteria_met'])

    def test_pause_loss_three_gains_or_eos_loss_rejects(self):
        bad = copy.deepcopy(self.full)
        bad['generated']['per_intent']['pause_focus']['gate_loss'] = 1
        self.assertFalse(runner.promotion_review(self.gates, self.pairs, bad, self.model)['prospective_criteria_met'])
        pairs = copy.deepcopy(self.pairs)
        pairs['generated']['supported_gains'] = 3
        self.assertFalse(runner.promotion_review(self.gates, pairs, self.full, self.model)['prospective_criteria_met'])
        self.assertFalse(runner.promotion_review(self.gates, self.pairs, self.full, {'schema_and_eos_valid': 99})['prospective_criteria_met'])


class FrozenPreflightTests(unittest.TestCase):
    def test_changed_ignored_requests_after_initial_success_fails(self):
        parent = runner.TASK / 'verification/build'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            requests = Path(temp) / 'requests.tsv'
            requests.write_bytes(b'original ordered bytes')
            frozen = {'requests_sha256': runner.sha(requests)}
            checks = [(requests, 'requests_sha256')]
            with patch.object(runner.shared, 'frozen_head'), patch.object(runner.shared, 'verify_runtime_and_inventory', return_value=set()):
                runner.verify_frozen(frozen, checks, 'f' * 40)
                requests.write_bytes(b'changed after initial successful preflight')
                with self.assertRaises(ValueError):
                    runner.verify_frozen(frozen, checks, 'f' * 40)

    def test_runtime_boundary_failure_is_not_suppressed_by_source_success(self):
        with patch.object(runner.shared, 'frozen_head'), patch.object(runner.shared, 'verify_runtime_and_inventory', side_effect=ValueError('linked library changed')):
            with self.assertRaisesRegex(ValueError, 'linked library changed'):
                runner.verify_frozen({}, [], 'f' * 40)

    def test_started_record_failure_reaps_only_known_child_and_retains_terminal_metadata(self):
        parent = runner.TASK / 'verification/build'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            build = Path(temp)
            requests = build / 'requests.tsv'
            candidate = build / 'ModelCommandGate.java'
            requests.write_bytes(b'frozen requests')
            candidate.write_bytes(b'frozen gate')
            job = Mock(pid=12345)
            job.poll.return_value = None
            original_write = runner.write_new
            def injected_failure(path, value):
                if path.name.endswith('-started.json'):
                    raise OSError('synthetic metadata write failure')
                return original_write(path, value)
            frozen = {'selected_source_sha256': {'LocalModel.java': 'f' * 64}}
            with patch.object(runner, 'BUILD', build), patch.object(runner, 'verify_frozen'), \
                    patch.object(runner.subprocess, 'run'), patch.object(runner.subprocess, 'Popen', return_value=job), \
                    patch.object(runner, 'write_new', side_effect=injected_failure):
                with self.assertRaises(RuntimeError):
                    runner.capture(requests, candidate, frozen, [], 'f' * 40)
            job.kill.assert_called_once()
            job.wait.assert_called_once_with()
            metadata = runner.json.loads((build / 'baseline-model-metadata.json').read_text())
            self.assertIsNone(metadata['exit_code'])
            self.assertEqual('OSError', metadata['error_type'])
            self.assertEqual(12345, metadata['pid'])
            self.assertTrue((build / 'baseline-model-output.tsv').exists())


if __name__ == '__main__':
    unittest.main()
