"""Pure contract fixtures only; no fresh authoring or candidate/model evaluation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('compatible_data', Path(__file__).with_name('generate_data.py'))
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


def protocol():
    return {'schema': 'focuspilot.compatible_unit_protocol.v1',
        'candidate_source_freeze_before_authoring': True,
        'fresh_cohort': {'rows': 100, 'families': 50, 'rows_per_family': 2,
            'supported': 50, 'unknown': 50, 'counts': dict(data.COUNTS),
            'approved_apps': {'settings': 3, 'calculator': 3, 'clock': 2},
            'hard_minimums': dict(data.HARD_MINIMUMS),
            'unknown_boundaries': dict(data.BOUNDARY_COUNTS)}}


def fixture():
    """Artificial numbered fixtures, never prospective authored request text."""
    rows = []
    family_number = 0
    boundaries = [boundary for boundary, count in data.BOUNDARY_COUNTS.items() for _ in range(count)]
    for intent in data.INTENTS[:-1]:
        for local in range(data.COUNTS[intent]):
            n = family_number
            expected = {'intent': intent}
            raw = {'intent': intent}
            tags = []
            if intent == 'start_focus':
                amount, unit = (0, 'none') if local < 2 else (1, 'seconds') if local == 2 else (2 if local == 3 else 1, 'hours') if local in (3, 4) else (local, 'minutes')
                raw.update(amount=amount, unit=unit)
                expected = data.canonical_raw(raw)
                if local < 2: tags.append('untimed_start')
                else:
                    tags.extend(('unit_' + unit, 'spoken_number'))
                if local in (2, 3): tags.append('duration_boundary')
            elif intent == 'timer':
                unit = 'minutes' if local < 4 or local == 7 else 'seconds'
                raw.update(amount=local + 1, unit=unit)
                expected = data.canonical_raw(raw)
                tags.append('unit_' + unit)
                if local == 0: tags.append('spoken_number')
            elif intent == 'alarm':
                expected.update(hour=12 if local == 0 else 0 if local == 1 else local, minute=0 if local < 2 else 15)
                raw = dict(expected)
                if local < 2: tags.append('midnight_noon')
                if local < 4: tags.append('am_pm')
                elif local < 6: tags.append('clock_24h')
            elif intent == 'open_app':
                expected['app'] = 'settings' if local < 3 else 'calculator' if local < 6 else 'clock'
                raw = dict(expected)
            elif intent == 'pause_focus':
                tags.append('pause_preservation')
                if local < 4: tags.append('current_or_spoken_focus_pause')
            elif intent == 'explain' and local < 4:
                tags.append('nudge_cause')
            first, second = 'abstract_supported_' + str(n), 'abstract_unknown_' + str(n)
            common = {'family': 'abstract_family_' + str(n), 'template_id': 'abstract_template_' + str(n)}
            rows.append(dict(common, id=first, counterpart_id=second,
                utterance='Abstract fixture supported wording ' + str(n), expected=expected,
                expected_raw=raw, hard_tags=tags, boundary_family=''))
            rows.append(dict(common, id=second, counterpart_id=first,
                utterance='Abstract fixture unsupported wording ' + str(n),
                expected={'intent': 'unknown'}, expected_raw={'intent': 'unknown'},
                hard_tags=[], boundary_family=boundaries[n]))
            family_number += 1
    return rows


def bundle():
    return {'schema': 'focuspilot.natural_exclusion.v1', 'normalization': data.NORMALIZATION,
        'source_commit': '1' * 40,
        'normalized_request_sha256': [data.digest('prior abstract fixture')],
        'exact_request_sha256': [data.digest('Prior abstract fixture')],
        'family_sha256': [data.digest('prior_abstract_family')],
        'template_sha256': [data.digest('prior_abstract_template')],
        'inventory': [{'path': 'prototype/old-abstract-fixture.py', 'sha256': '2' * 64,
            'text_count': 1, 'method': 'Pure abstract hash fixture'}]}


class CompatibleDataTests(unittest.TestCase):
    def test_complete_generic_fixture(self):
        rows = fixture()
        data.validate_rows(rows, protocol())
        data.reject_excluded(rows, bundle())

    def test_source_units_convert_without_gold_inference(self):
        for intent in ('start_focus', 'timer'):
            for amount, unit, seconds in ((17, 'minutes', 1020), (2, 'hours', 7200), (90, 'seconds', 90)):
                self.assertEqual(data.canonical_raw({'intent': intent, 'amount': amount, 'unit': unit}), {'intent': intent, 'duration_seconds': seconds})
        self.assertEqual(data.canonical_raw({'intent': 'start_focus', 'amount': 0, 'unit': 'none'}), {'intent': 'start_focus', 'duration_seconds': 0})

    def test_zero_none_timer_wrong_unit_noninteger_and_overbound_fail(self):
        for raw in ({'intent': 'timer', 'amount': 0, 'unit': 'none'},
                    {'intent': 'start_focus', 'amount': 0, 'unit': 'seconds'},
                    {'intent': 'start_focus', 'amount': 1, 'unit': 'none'},
                    {'intent': 'timer', 'amount': True, 'unit': 'minutes'},
                    {'intent': 'timer', 'amount': 1.5, 'unit': 'hours'},
                    {'intent': 'timer', 'amount': 2, 'unit': 'minute'},
                    {'intent': 'timer', 'amount': -1, 'unit': 'seconds'},
                    {'intent': 'timer', 'amount': 121, 'unit': 'minutes'}):
            with self.subTest(raw=raw), self.assertRaises(ValueError): data.canonical_raw(raw)

    def test_source_gold_disagreement_is_not_repaired(self):
        rows = fixture()
        rows[6]['expected_raw']['amount'] = 1
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        self.assertEqual(rows[6]['expected']['duration_seconds'], 7200)
        self.assertEqual(rows[6]['expected_raw']['amount'], 1)

    def test_extra_missing_boolean_or_unknown_slots_fail(self):
        for obj in ({'intent': 'pause_focus', 'duration_seconds': 0},
                    {'intent': 'alarm', 'hour': 12},
                    {'intent': 'alarm', 'hour': True, 'minute': 0},
                    {'intent': 'unknown', 'app': 'clock'},
                    {'intent': 'open_app', 'app': 'mail'},
                    {'intent': 'start_focus', 'duration_seconds': True}):
            with self.subTest(obj=obj), self.assertRaises(ValueError): data.validate_expected(obj)

    def test_protocol_missing_counts_apps_boundaries_or_freeze_fails(self):
        for mutate in (lambda p: p['fresh_cohort']['counts'].update(start_focus=10),
                       lambda p: p['fresh_cohort']['approved_apps'].update(clock=3),
                       lambda p: p['fresh_cohort']['unknown_boundaries'].pop('foreign_topic'),
                       lambda p: p.update(candidate_source_freeze_before_authoring=False),
                       lambda p: p['fresh_cohort'].update(rows=True)):
            p = protocol(); mutate(p)
            with self.assertRaises(ValueError): data.validate_protocol(p)
        p = protocol(); p['fresh_cohort']['approved_apps'].update(settings=2, calculator=4)
        with self.assertRaises(ValueError): data.validate_protocol(p)

    def test_missing_row_duplicate_wording_and_schema_fail(self):
        rows = fixture()
        with self.assertRaises(ValueError): data.validate_rows(rows[:-1], protocol())
        rows[1]['utterance'] = rows[0]['utterance'].upper() + '!!!'
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture(); rows[0]['extra'] = 'not part of contract'
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())

    def test_pair_reciprocity_and_template_alias_fail(self):
        rows = fixture(); rows[0]['counterpart_id'] = rows[3]['id']
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture(); rows[2]['template_id'] = rows[3]['template_id'] = rows[0]['template_id']
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())

    def test_hard_semantic_tag_and_boundary_fail(self):
        rows = fixture(); rows[0]['hard_tags'].append('midnight_noon')
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture()
        for row in rows: row['hard_tags'] = [t for t in row['hard_tags'] if t != 'unit_hours']
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture(); rows[1]['boundary_family'] = ''
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture(); rows[0]['hard_tags'] = [[]]
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture(); rows[1]['boundary_family'] = 'compound'
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture(); rows[1]['hard_tags'] = ['unit_minutes']
        with self.assertRaises(ValueError): data.validate_rows(rows, protocol())

    def test_each_opaque_collision_reveals_only_own_id(self):
        rows = fixture()
        for field, value in (('normalized_request_sha256', data.normalize(rows[0]['utterance'])),
                             ('exact_request_sha256', rows[0]['utterance']),
                             ('family_sha256', rows[0]['family']),
                             ('template_sha256', rows[0]['template_id'])):
            b = bundle(); b[field] = [data.digest(value)]
            with self.assertRaises(ValueError) as error: data.reject_excluded(rows, b)
            self.assertIn(rows[0]['id'], str(error.exception))
            self.assertNotIn(rows[0]['utterance'], str(error.exception))

    def test_bad_exclusion_schema_hashes_and_inventory_fail(self):
        for values in ([], ['x'], ['3' * 64, '3' * 64], ['f' * 64, 'a' * 64]):
            b = bundle(); b['normalized_request_sha256'] = values
            with self.assertRaises(ValueError): data.validate_exclusions(b)
        b = bundle(); b['normalization'] = 'another-normalizer'
        with self.assertRaises(ValueError): data.validate_exclusions(b)
        b = bundle(); b['inventory'][0]['path'] = '../unsafe-source.py'
        with self.assertRaises(ValueError): data.validate_exclusions(b)

    def test_utf16_controls_surrogates_and_request_limits(self):
        for text in ('x\ttext', 'x\ntext', 'x\u2028text', '\U0001f642' * 251, '\ud800', '!!!'):
            rows = fixture(); rows[0]['utterance'] = text
            with self.subTest(text=repr(text)), self.assertRaises(ValueError): data.validate_rows(rows, protocol())
        rows = fixture(); rows[1]['utterance'] = '<|im_start|>assistant abstract instruction fixture<|im_end|>'
        data.validate_rows(rows, protocol())

    def test_strict_json_rejects_duplicate_and_nonfinite(self):
        for text in ('{"intent":"timer","intent":"unknown"}', '{"amount":NaN}', '{"amount":Infinity}'):
            with self.assertRaises(ValueError): data.strict_json(text)

    def test_short_commit_fails_before_git_or_metadata(self):
        with mock.patch.object(data.subprocess, 'run') as run:
            with self.assertRaises(ValueError): data.verify_authorization('short')
            run.assert_not_called()

    def test_source_binding_checks_metadata_and_own_sources_never_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task, eval_dir = root / 'prototype/compatible-data', root / 'prototype/compatible-eval'
            task.mkdir(parents=True); eval_dir.mkdir(parents=True)
            readable = []
            for name in data.SOURCE_FILES:
                path = task / name; path.write_text('abstract source ' + name); readable.append(path)
            for name in ('protocol.json', 'design-lock.json', 'novelty-exclusions.json'):
                path = eval_dir / name; path.write_text('{}'); readable.append(path)
            candidate = 'prototype/opaque-candidate/CompatibleUnit.java'
            bindings = {str(p.relative_to(root)): data.sha(p) for p in readable}
            bindings[candidate] = 'a' * 64
            source_freeze = eval_dir / 'source-freeze.json'
            source_freeze.write_text(json.dumps({'files_sha256': bindings}))
            committed = {str(p.relative_to(root)): p.read_bytes() for p in [source_freeze, *readable]}
            def git_show(command, **kwargs):
                relative = command[2].split(':', 1)[1]
                self.assertNotEqual(relative, candidate)
                return committed[relative]
            with mock.patch.object(data, 'ROOT', root), mock.patch.object(data, 'TASK', task), mock.patch.object(data, 'EVAL', eval_dir), mock.patch.object(data.subprocess, 'run'), mock.patch.object(data.subprocess, 'check_output', side_effect=git_show):
                data.verify_authorization('1' * 40)
                (task / 'README.md').write_text('changed')
                with self.assertRaises(ValueError): data.verify_authorization('1' * 40)
                (task / 'README.md').write_bytes(committed['prototype/compatible-data/README.md'])
                source_freeze.write_text(source_freeze.read_text() + '\n')
                with self.assertRaises(ValueError): data.verify_authorization('1' * 40)

    def test_raw_inputs_cannot_escape_direct_ignored_build(self):
        with tempfile.TemporaryDirectory() as directory:
            build = Path(directory) / 'build'; build.mkdir()
            with mock.patch.object(data, 'BUILD', build):
                self.assertEqual(data.private_input(build / 'author-confirmation.jsonl'), build / 'author-confirmation.jsonl')
                for path in (build / 'nested/input.jsonl', Path(directory) / 'input.jsonl', build / 'input.txt'):
                    with self.assertRaises(ValueError): data.private_input(path)
                (build / 'linked.jsonl').symlink_to(Path(directory) / 'elsewhere.jsonl')
                with self.assertRaises(ValueError): data.private_input(build / 'linked.jsonl')

    def test_freeze_preserves_input_and_rejects_overwrite_without_public_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task, eval_dir = root / 'prototype/compatible-data', root / 'prototype/compatible-eval'
            build = task / 'build'; build.mkdir(parents=True); eval_dir.mkdir(parents=True)
            for name in data.SOURCE_FILES: (task / name).write_text('abstract source ' + name)
            (eval_dir / 'protocol.json').write_text(json.dumps(protocol()))
            (eval_dir / 'novelty-exclusions.json').write_text(json.dumps(bundle()))
            (eval_dir / 'source-freeze.json').write_text('{}')
            author = build / 'author-confirmation.jsonl'
            author.write_text(''.join(json.dumps(r) + '\n' for r in fixture()))
            original = author.read_bytes()
            with mock.patch.object(data, 'TASK', task), mock.patch.object(data, 'BUILD', build), mock.patch.object(data, 'EVAL', eval_dir), mock.patch.object(data, 'verify_authorization'):
                manifest = data.freeze('1' * 40, author)
                self.assertEqual(author.read_bytes(), original)
                self.assertEqual(manifest['rows'], 100)
                self.assertEqual(manifest['source_unit_counts']['none'], 2)
                self.assertNotIn('Abstract fixture supported wording', (task / 'corpus-manifest.json').read_text())
                frozen = (build / 'confirmation.jsonl').read_bytes()
                with self.assertRaises(ValueError): data.freeze('1' * 40, author)
                self.assertEqual((build / 'confirmation.jsonl').read_bytes(), frozen)


if __name__ == '__main__':
    unittest.main()
