"""Qualification boundaries: a net gain cannot hide losses or wrong slot acceptance."""
import copy
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
import evaluate


class QualificationTest(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((Path(__file__).parent / 'protocol.json').read_text())
        counts = {'rows': 100, 'supported_rows': 50, 'unknown_rows': 50,
            'supported_complete_proposals': 10, 'unknown_refused_by_gate': 50,
            'wrong_accepts': 0,
            'per_class': {i: {'complete_proposal_correct': 1} for i in evaluate.native.INTENTS}}
        self.old = {'generated': copy.deepcopy(counts), 'oracle': copy.deepcopy(counts)}
        self.new = copy.deepcopy(self.old)
        self.new['generated']['supported_complete_proposals'] = 16
        self.new['oracle']['supported_complete_proposals'] = 20
        self.paired = {'supported_rows': {'gate_loss': 0}}
        self.process = {'exit_code': 0, 'timed_out': False}

    def checks(self):
        return evaluate.qualification(self.old, self.new, self.paired, 100, self.process, self.protocol)

    def test_locked_valid_case_and_gain_floor(self):
        self.assertTrue(all(self.checks().values()))
        self.new['generated']['supported_complete_proposals'] = 15
        self.assertFalse(self.checks()['supported_complete_net_gain_at_least_6'])

    def test_net_gain_cannot_hide_individual_or_class_loss(self):
        self.paired['supported_rows']['gate_loss'] = 1
        self.assertFalse(self.checks()['supported_complete_losses_zero'])
        self.new['generated']['per_class']['pause_focus']['complete_proposal_correct'] = 0
        self.assertFalse(self.checks()['supported_per_class_preserved'])
        self.assertFalse(self.checks()['pause_preserved'])

    def test_oracle_unknown_acceptance_is_not_hidden_by_model_abstention(self):
        self.new['oracle']['wrong_accepts'] = 1
        self.new['oracle']['unknown_refused_by_gate'] = 49
        self.assertFalse(self.checks()['wrong_accepts_zero_generated_and_oracle'])
        self.assertFalse(self.checks()['all_unknown_refused_generated_and_oracle'])

    def test_incomplete_denominator_and_failed_owned_process_fail(self):
        self.new['generated']['rows'] = 99
        self.process['timed_out'] = True
        self.assertFalse(self.checks()['exact_denominators'])
        self.assertFalse(self.checks()['runtime_failures_zero'])

    def test_wrong_slots_count_as_wrong_accept_not_success(self):
        rows = [{'id': 'slot', 'intent': 'alarm', 'family': 'slot-family', 'hard_tags': [],
                 'expected_kind': 'ALARM', 'hour': 7, 'minute': 25, 'seconds': 0}]
        summary, details = evaluate.scoring.summarize(rows, {'slot': 'alarm'},
            {'slot': {'kind': 'ALARM', 'hour': 19, 'minute': 25, 'seconds': 0}})
        self.assertEqual(0, summary['supported_complete_proposals'])
        self.assertEqual(1, summary['wrong_accepts'])
        self.assertFalse(details[0]['complete_proposal_correct'])

    def test_source_changed_after_prospective_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / 'candidate.java'
            source.write_text('frozen candidate')
            manifest = root / 'freeze.json'
            manifest.write_text(json.dumps({'files_sha256': {'candidate.java': evaluate.native.sha(source)}}))
            with patch.object(evaluate, 'ROOT', root):
                evaluate.verify_source_freeze(manifest)
                source.write_text('post-corpus candidate change')
                with self.assertRaises(ValueError):
                    evaluate.verify_source_freeze(manifest)


if __name__ == '__main__':
    unittest.main()
