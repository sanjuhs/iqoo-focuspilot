"""Failure-oriented tests; no native inference, corpus authoring or phone calls."""
import copy
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('json_runner', Path(__file__).with_name('run_evaluation.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
gate = runner.load_frozen_module(runner.GATE_HELPER, runner.GATE_HELPER_SHA, 'json_test_gate')


def row(identifier='a', intent='timer', kind='TIMER', seconds=30):
    return dict(id=identifier, family='toy', semantic_intent=intent, expected_kind=kind,
                hour=0, minute=0, seconds=seconds, hard_tags=['toy'])


def output(intent='timer', valid=True):
    return {'intent': intent, 'valid': valid, 'metrics': {'reached_eos': True}}


class StrictOutputTests(unittest.TestCase):
    def test_malformed_duplicates_extra_keys_digit_and_noncanonical_fail(self):
        bad = ['{"intent":"timer","intent":"unknown"}', '{"intent":"timer","extra":0}',
               '4', '{"intent":"timer"} trailing', '{ "intent": "timer" }',
               '{"intent":true}', '{"intent":["timer"]}', '{"intent":"not_allowed"}']
        for text in bad:
            with self.subTest(text=text):
                self.assertEqual(('unknown', False), runner.decode_intent({'text': text, 'metrics': {'reached_eos': True}}))
        self.assertEqual(('timer', True), runner.decode_intent({'text': '{"intent":"timer"}', 'metrics': {'reached_eos': True}}))

    def test_eos_loss_is_semantic_failure_even_unknown_fallback(self):
        raw = {'text': '{"intent":"unknown"}', 'metrics': {'reached_eos': False}}
        intent, valid = runner.decode_intent(raw)
        scored = runner.semantic_score([row(intent='unknown', kind='UNKNOWN', seconds=0)], {'a': output(intent, valid)})
        self.assertEqual(0, scored['unknown_correct'])
        self.assertEqual(1, scored['invalid_outputs'])

    def test_duplicate_native_envelope_and_nonfinite_json_rejected(self):
        for text in ('{"text":"x","text":"y"}', '{"metric":NaN}'):
            with self.assertRaises(ValueError):
                runner.strict_json(text)

    def test_incomplete_or_unexpected_inventory_never_scores(self):
        for outputs in ({}, {'other': output()}, {'a': output(), 'extra': output()}):
            with self.assertRaises(ValueError):
                runner.semantic_score([row()], outputs)

    def test_slot_mismatch_is_wrong_accept_and_paired_loss(self):
        rows = [row()]
        old_summary, old = gate.strict_score(rows, {'a': ('TIMER', 0, 0, 30)})
        new_summary, new = gate.strict_score(rows, {'a': ('TIMER', 0, 0, 300)})
        paired, _ = runner.paired_summary(rows, {'a': output()}, {'a': output()}, old, new)
        self.assertEqual(1, old_summary['supported_correct'])
        self.assertEqual(1, new_summary['supported_wrong_slots'])
        self.assertEqual(1, new_summary['wrong_accepted'])
        self.assertEqual(1, paired['supported_rows']['gate_loss'])
        self.assertEqual(0, paired['supported_rows']['semantic_loss'])

    def test_metric_validation_rejects_fake_cpu_and_nonfinite(self):
        metrics = dict(cpu_only=True, capture_enabled=False, reached_eos=True,
                       total_ms=1, prefill_ms=1, decode_ms=0, context_setup_ms=0,
                       prompt_tokens=1, generated_tokens=1)
        for key, invalid in [('cpu_only', 1), ('capture_enabled', True), ('total_ms', float('nan')),
                             ('generated_tokens', True), ('reached_eos', 'true')]:
            bad = dict(metrics, **{key: invalid})
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.require_complete_capture([row()], {'a': {'metrics': bad}})

    def test_native_order_missing_and_duplicate_rows_refused(self):
        rows = [row('a'), row('b')]
        metrics = dict(cpu_only=True, capture_enabled=False, reached_eos=True,
                       total_ms=1, prefill_ms=1, decode_ms=0, context_setup_ms=0,
                       prompt_tokens=1, generated_tokens=1)
        out = {'metrics': metrics}
        runner.require_complete_capture(rows, {'a': out, 'b': out})
        for bad in ({'b': out, 'a': out}, {'a': out}, {'a': out, 'unexpected': out}):
            with self.assertRaises(ValueError):
                runner.require_complete_capture(rows, bad)

    def test_capture_parser_rejects_reordering_duplicate_and_missing(self):
        parent = runner.TASK / 'verification/build'
        parent.mkdir(parents=True, exist_ok=True)
        metrics = dict(cpu_only=True, capture_enabled=False, reached_eos=True,
                       total_ms=1, prefill_ms=1, decode_ms=0, context_setup_ms=0,
                       prompt_tokens=1, generated_tokens=1)
        raw = base64.b64encode(json.dumps({'text': '{"intent":"timer"}',
                   'metrics': metrics, 'activations': []}).encode()).decode()
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            build = Path(temp)
            target = build / 'baseline-model-output.tsv'
            with patch.object(runner, 'BUILD', build), patch.object(runner, 'verified_capture_metadata', return_value={}):
                for ids in (['b', 'a'], ['a', 'a'], ['a']):
                    target.write_text('LOAD\t1000\n' + ''.join(i + '\t1000\t' + raw + '\n' for i in ids))
                    with self.assertRaises(ValueError):
                        runner.read_capture('baseline', None, [row('a'), row('b')], {}, None)


class PromotionTests(unittest.TestCase):
    def setUp(self):
        zero = dict(semantic_gain=0, semantic_loss=0, gate_gain=0, gate_loss=0,
                    baseline_wrong_accept=0, candidate_wrong_accept=0)
        self.paired = {'supported_rows': dict(zero, gate_gain=4),
                       'all_rows': dict(zero), 'per_intent': {intent: dict(zero) for intent in runner.INTENTS}}
        self.paired['per_intent']['timer']['gate_gain'] = 4
        self.models = {'candidate': {'schema_and_eos_valid': 100}}
        self.gates = {'baseline': {'wrong_accepted': 0}, 'candidate': {'wrong_accepted': 0}}

    def test_pass_is_only_review_prerequisite_never_promotion(self):
        result = runner.promotion_review(self.models, self.gates, self.paired)
        self.assertTrue(result['prospective_criteria_met'])
        self.assertFalse(result['candidate_promoted'])

    def test_gains_do_not_hide_pause_or_unknown_semantic_losses(self):
        for target in ('supported_rows', 'all_rows'):
            bad = copy.deepcopy(self.paired)
            bad[target]['semantic_loss' if target == 'all_rows' else 'gate_loss'] = 1
            self.assertFalse(runner.promotion_review(self.models, self.gates, bad)['prospective_criteria_met'])
        bad = copy.deepcopy(self.paired)
        bad['per_intent']['pause_focus']['gate_loss'] = 1
        self.assertFalse(runner.promotion_review(self.models, self.gates, bad)['prospective_criteria_met'])

    def test_three_gains_invalid_schema_or_either_arm_wrong_accept_reject(self):
        bad = copy.deepcopy(self.paired)
        bad['supported_rows']['gate_gain'] = 3
        self.assertFalse(runner.promotion_review(self.models, self.gates, bad)['prospective_criteria_met'])
        self.assertFalse(runner.promotion_review({'candidate': {'schema_and_eos_valid': 99}}, self.gates, self.paired)['prospective_criteria_met'])
        for arm in self.gates:
            gates = copy.deepcopy(self.gates)
            gates[arm]['wrong_accepted'] = 1
            self.assertFalse(runner.promotion_review(self.models, gates, self.paired)['prospective_criteria_met'])


class RuntimeBoundaryTests(unittest.TestCase):
    def test_private_inventory_or_linked_library_mutation_after_initial_check_fails(self):
        parent = runner.TASK / 'verification/build'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            root = Path(temp)
            model = root / 'model'
            native = root / 'native'
            library = root / 'library'
            inventory = root / 'private-requests.tsv'
            for file in (model, native, library, inventory):
                file.write_bytes(b'frozen bytes')
            linked = {str(library): runner.sha(library)}
            frozen = {'linked_libraries_sha256': linked,
                      'overlap_inventory': [{'path': inventory.name, 'sha256': runner.sha(inventory)}]}
            with patch.multiple(runner, ROOT=root, MODEL=model, NATIVE=native,
                                MODEL_SHA=runner.sha(model), NATIVE_SHA=runner.sha(native), LINKED_LIBRARIES=linked):
                for file in (inventory, library):
                    self.assertEqual({inventory.name}, runner.verify_runtime_and_inventory(frozen))
                    file.write_bytes(b'mutated after initial successful check')
                    with self.assertRaises(ValueError):
                        runner.verify_runtime_and_inventory(frozen)
                    file.write_bytes(b'frozen bytes')


if __name__ == '__main__':
    unittest.main()
