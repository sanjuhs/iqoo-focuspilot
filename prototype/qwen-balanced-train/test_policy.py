import json
import unittest
from collections import Counter
from policy import INTENTS, balanced_order, completion_weights, supervised_weights, summary


class Boundaries(unittest.TestCase):
    def test_full_balanced_exposure_is_reproducible_not_row_sampling(self):
        rows = [{'intent': intent} for intent in INTENTS for _ in range(16)]
        order = balanced_order(rows)
        self.assertEqual(order, balanced_order(rows))
        self.assertEqual(224, len(order))
        self.assertEqual(Counter({i: 2 for i in range(112)}), Counter(order))
        for start in range(0, 224, 7):
            self.assertEqual(set(INTENTS), {rows[i]['intent'] for i in order[start:start+7]})
        self.assertNotEqual(order, balanced_order(rows, seed=1))

    def test_missing_or_imbalanced_class_rejected(self):
        rows = [{'intent': intent} for intent in INTENTS for _ in range(16)]
        rows[0] = {'intent': 'unknown'}
        with self.assertRaises(ValueError): balanced_order(rows)
        with self.assertRaises(ValueError): balanced_order(rows[:-1])

    def test_value_overlap_including_mixed_delimiter_token(self):
        pieces = ['{"intent":"sta', 'rt', '_focus"}', '<|im_end|>']
        prefixes = [''.join(pieces[:i]) for i in range(1, len(pieces)+1)]
        weights, overlap = completion_weights('start_focus', prefixes)
        self.assertEqual([8, 8, 8, 1], weights)
        self.assertEqual(3, len(overlap))

    def test_shared_json_and_eos_are_not_intent_weighted(self):
        for intent in INTENTS:
            pieces = ['{"intent":"', intent, '"}', '<|im_end|>']
            prefixes = [''.join(pieces[:i]) for i in range(1, 5)]
            weights, _ = completion_weights(intent, prefixes)
            self.assertEqual([1, 8, 1, 1], weights)

    def test_ambiguous_incomplete_or_wrong_offsets_fail(self):
        for prefixes in [['x'], ['{"intent":"'], ['', '{"intent":"timer"}<|im_end|>'],
                         ['{"intent":"timer"}<|im_end|>']]:
            with self.assertRaises(ValueError): completion_weights('timer', prefixes)

    def test_prompt_mask_supervises_first_completion_and_eos_without_shift(self):
        self.assertEqual([0, 0, 1, 8, 1], supervised_weights(3, [1, 8, 1]))
        self.assertEqual([8, 1], supervised_weights(1, [8, 1]))
        with self.assertRaises(ValueError): supervised_weights(0, [1])

    def test_missing_output_counts_as_incorrect_in_complete_denominator(self):
        r = summary([{'expected': 'timer', 'actual': None, 'canonical_eos': False},
                     {'expected': 'unknown', 'actual': 'unknown', 'canonical_eos': True}])
        self.assertEqual(2, r['rows']); self.assertEqual(1, r['correct'])
        self.assertEqual(1, r['canonical_eos']); self.assertEqual(0, r['per_intent']['timer']['correct'])


if __name__ == '__main__': unittest.main()
