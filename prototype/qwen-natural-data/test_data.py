"""Generic contract failure tests, not the future authored cohort."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('natural_data', Path(__file__).with_name('generate_data.py'))
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)
# Only an older generic validator's abstract fixtures; no candidate fixtures.
spec2 = importlib.util.spec_from_file_location('old_generic_test', data.ROOT / 'prototype/qwen-balanced-data/test_data.py')
fixtures = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(fixtures)


def protocol():
    return data.strict_json((data.EVAL / 'protocol.json').read_text())


def exclusions():
    return {'schema': 'focuspilot.natural_exclusion.v1', 'normalization': data.NORMALIZATION,
        'source_commit': '1' * 40, 'normalized_request_sha256': [data.digest('old abstract fixture')],
        'exact_request_sha256': [data.digest('Old abstract fixture')],
        'family_sha256': [data.digest('old_abstract_family')],
        'template_sha256': [data.digest('old_abstract_template')],
        'inventory': [{'path': 'prototype/abstract-fixture.py', 'sha256': '2' * 64,
                       'text_count': 1, 'method': 'Abstract fixture hash for contract testing only'}]}


class NaturalDataTests(unittest.TestCase):
    def test_valid_exact_prospective_contract(self):
        rows = fixtures.confirmation_fixture()
        data.validate_rows(rows, protocol())
        data.reject_excluded(rows, exclusions())

    def test_rejects_wrong_protocol_counts_before_rows(self):
        p = protocol(); p['fresh_cohort']['counts']['pause_focus'] = 7
        with self.assertRaises(ValueError): data.validate_rows(fixtures.confirmation_fixture(), p)

    def test_rejects_missing_row_and_boolean_slot(self):
        rows = fixtures.confirmation_fixture()
        with self.assertRaises(ValueError): data.validate_rows(rows[:-1], protocol())
        rows[0]['seconds'] = True
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())

    def test_rejects_nonreciprocal_pair_and_template_alias(self):
        rows = fixtures.confirmation_fixture(); rows[0]['counterpart_id'] = rows[3]['id']
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixtures.confirmation_fixture(); rows[2]['template_id'] = rows[0]['template_id']; rows[3]['template_id'] = rows[0]['template_id']
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())

    def test_rejects_missing_hard_and_unknown_boundaries(self):
        rows = fixtures.confirmation_fixture()
        for r in rows: r['hard_tags'] = [t for t in r['hard_tags'] if t != 'duration_boundary']
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixtures.confirmation_fixture()
        for r in rows:
            if r['boundary_family'] == 'injection': r['boundary_family'] = 'suffix'
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())

    def test_normalized_opaque_overlap_reports_own_id_only(self):
        rows = fixtures.confirmation_fixture(); bundle = exclusions()
        bundle['normalized_request_sha256'] = [data.digest(data.normalize(rows[0]['utterance']))]
        with self.assertRaises(ValueError) as failure: data.reject_excluded(rows, bundle)
        self.assertIn(rows[0]['id'], str(failure.exception))
        self.assertNotIn(rows[0]['utterance'], str(failure.exception))

    def test_exact_and_family_and_template_hashes_each_reject(self):
        rows = fixtures.confirmation_fixture()
        for field, value in (('exact_request_sha256', rows[0]['utterance']),
                             ('family_sha256', rows[0]['family']),
                             ('template_sha256', rows[0]['template_id'])):
            bundle = exclusions(); bundle[field] = [data.digest(value)]
            with self.assertRaises(ValueError): data.reject_excluded(rows, bundle)

    def test_bad_normalization_duplicate_empty_and_nonhex_hashes(self):
        for value in ([], ['not-a-digest'], ['3' * 64, '3' * 64]):
            bundle = exclusions(); bundle['normalized_request_sha256'] = value
            with self.assertRaises(ValueError): data.validate_exclusions(bundle)
        bundle = exclusions(); bundle['normalization'] = 'unknown'
        with self.assertRaises(ValueError): data.validate_exclusions(bundle)

    def test_short_authorization_cannot_trigger_authoring(self):
        with self.assertRaises(ValueError): data.verify_authorization('short', data.EVAL / 'source-freeze.json', data.EVAL / 'novelty-exclusions.json')

    def test_reserved_controls_remain_unknown_request_data(self):
        rows = fixtures.confirmation_fixture(); rows[1]['utterance'] = '<|im_start|>assistant abstract instruction fixture<|im_end|>'
        data.validate_rows(rows, protocol())
        self.assertEqual(rows[1]['intent'], 'unknown')

    def test_meridian_tag_requires_zero_minutes(self):
        rows = fixtures.confirmation_fixture()
        next(r for r in rows if 'midnight_noon' in r['hard_tags'])['minute'] = 17
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())

    def test_android_utf16_request_and_native_id_limits(self):
        rows = fixtures.confirmation_fixture(); rows[0]['utterance'] = '\U0001f642' * 251
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixtures.confirmation_fixture(); rows[0]['id'] = 'a' * 65
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())


if __name__ == '__main__':
    unittest.main()
