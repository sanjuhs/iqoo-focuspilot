import unittest
from evaluate import shape, summarize


class ExactProposalScoring(unittest.TestCase):
    def test_numbers_are_not_booleans_or_approximate_values(self):
        for value in [True, 1.0, -1, 7201]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                shape({'intent': 'timer', 'duration_seconds': value})

    def test_exact_field_sets_and_known_targets(self):
        for value in [{'intent': ['alarm']}, {'intent': 'alarm', 'hour': 1, 'minute': 60},
                      {'intent': 'unknown', 'duration_seconds': 0},
                      {'intent': 'open_app', 'app': ['settings']},
                      {'intent': 'open_app', 'app': 'bank'}]:
            with self.subTest(value=value), self.assertRaises(ValueError): shape(value)

    def test_wrong_accepted_slot_is_not_an_intent_success(self):
        rows = [{'id': 'x', 'utterance': 'timer request',
                 'expected': {'intent': 'timer', 'duration_seconds': 90}}]
        prediction = {'intent': 'timer', 'duration_seconds': 60}
        summary, details = summarize(rows, {'x': prediction}, {'x': (prediction, True, 'accepted')})
        self.assertEqual(1, summary['raw_intent_correct'])
        self.assertEqual(0, summary['supported_complete'])
        self.assertEqual(1, summary['wrong_accepts'])
        self.assertTrue(details[0]['wrong_accept'])

    def test_guard_refusal_is_distinct_from_model_unknown(self):
        rows = [{'id': 'x', 'utterance': 'unsupported request', 'expected': {'intent': 'unknown'}}]
        summary, _ = summarize(rows, {'x': {'intent': 'pause_focus'}},
                               {'x': ({'intent': 'unknown'}, False, 'guard refused')})
        self.assertEqual(0, summary['unknown_model_abstentions'])
        self.assertEqual(1, summary['unknown_validator_refusals'])
        self.assertEqual(0, summary['wrong_accepts'])

    def test_acceptance_flag_cannot_hide_unknown_or_wrong_slots(self):
        rows = [{'id': 'x', 'utterance': 'pause request', 'expected': {'intent': 'pause_focus'}}]
        with self.assertRaises(ValueError):
            summarize(rows, {'x': {'intent': 'pause_focus'}},
                      {'x': ({'intent': 'pause_focus'}, False, 'inconsistent')})


if __name__ == '__main__': unittest.main()
