"""Corpus-contract and overlap/ownership checks, with no native generation."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('compact_corpus', Path(__file__).with_name('generate_data.py'))
DATA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DATA)


class CorpusTests(unittest.TestCase):
    def test_fixed_contract_and_hard_rows(self):
        rows = DATA.cases()
        self.assertEqual(len(rows), 100)
        self.assertEqual(sum(r['expected_kind'] == 'UNKNOWN' for r in rows), 50)
        self.assertEqual(sum(bool(r['hard_tags']) for r in rows), 25)
        self.assertEqual(sum('midnight_noon' in r['hard_tags'] for r in rows), 2)

    def test_original_slot_identity_rejects_inconsistent_labels(self):
        rows = copy.deepcopy(DATA.cases())
        selected = next(r for r in rows if r['expected_kind'] == 'ALARM')
        selected['minute'] = 60
        with self.assertRaisesRegex(ValueError, 'alarm slots'):
            DATA.validate_rows(rows)
        rows = copy.deepcopy(DATA.cases())
        selected = next(r for r in rows if r['expected_kind'] == 'UNKNOWN')
        selected['semantic_intent'] = 'alarm'
        with self.assertRaisesRegex(ValueError, 'Required unknown'):
            DATA.validate_rows(rows)

    def test_duplicate_family_and_duplicate_normalized_request_rejected(self):
        rows = copy.deepcopy(DATA.cases()); rows[1]['family'] = rows[2]['family']
        with self.assertRaisesRegex(ValueError, 'two-row families'):
            DATA.validate_rows(rows)
        rows = copy.deepcopy(DATA.cases()); rows[1]['utterance'] = rows[0]['utterance'].upper() + '!!!'
        with self.assertRaisesRegex(ValueError, 'normalized duplicate'):
            DATA.validate_rows(rows)

    def test_prior_exact_and_normalized_matches_fail(self):
        rows = DATA.cases()
        with self.assertRaisesRegex(ValueError, 'Exact prior'):
            DATA.reject_overlap(rows, [rows[0]['utterance']])
        with self.assertRaisesRegex(ValueError, 'Normalized prior'):
            DATA.reject_overlap(rows, [rows[0]['utterance'].upper() + '???'])
        self.assertEqual(DATA.normalize('twenty-five  MINUTES!'), 'twenty five minutes')
        self.assertNotEqual(DATA.normalize('twenty five minutes'), DATA.normalize('25 minutes'))

    def test_all_available_prior_and_locked_example_inventories_have_zero_overlap(self):
        inventories, texts = DATA.overlap_inventory()
        self.assertGreaterEqual(len(inventories), 8)
        self.assertGreaterEqual(len(texts), 790)
        DATA.reject_overlap(DATA.cases(), texts)
        self.assertTrue(any(i['path'].endswith('candidate.json') and i['text_count'] == 15 for i in inventories))

    def test_missing_mandatory_inventory_fails_closed(self):
        original = DATA.ROOT
        try:
            with tempfile.TemporaryDirectory() as folder:
                DATA.ROOT = Path(folder)
                with self.assertRaisesRegex(ValueError, 'Missing mandatory'):
                    DATA.overlap_inventory()
        finally:
            DATA.ROOT = original

    def test_existing_changed_evidence_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'frozen.tsv'
            DATA.write_unchanged_or_new(path, b'original\n')
            DATA.write_unchanged_or_new(path, b'original\n')
            with self.assertRaisesRegex(ValueError, 'Refuse replacing'):
                DATA.write_unchanged_or_new(path, b'changed\n')
            self.assertEqual(path.read_bytes(), b'original\n')

    def test_boolean_slots_and_wrong_hard_tags_fail(self):
        rows = copy.deepcopy(DATA.cases()); rows[0]['seconds'] = False
        with self.assertRaisesRegex(ValueError, 'exact integers'):
            DATA.validate_rows(rows)
        rows = copy.deepcopy(DATA.cases()); rows[0]['hard_tags'] = ['duration_boundary']
        with self.assertRaisesRegex(ValueError, 'boundary hard tag'):
            DATA.validate_rows(rows)


if __name__ == '__main__':
    unittest.main()
