"""Boundary tests use generic toy fixtures, never the private author corpus."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('gate_v14_confirm_data', Path(__file__).with_name('generate_data.py'))
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)
PROTOCOL = json.loads(Path(__file__).with_name('protocol.json').read_text())


def toy_rows():
    rows = []
    kind_for_intent = {'start_focus': 'START_FOCUS', 'pause_focus': 'PAUSE_FOCUS',
                       'alarm': 'ALARM', 'timer': 'TIMER', 'open_app': 'OPEN_SETTINGS', 'explain': 'EXPLAIN'}
    app_index = 0
    for intent, count in PROTOCOL['corpus']['supported_by_intent'].items():
        for _ in range(count):
            index = len(rows)
            kind = kind_for_intent[intent]
            tags = []
            seconds = 0
            if intent in {'start_focus', 'timer'}:
                seconds = 1
                tags += ['duration_boundary', 'spoken_number_slot', 'seconds_minutes_unit']
            if intent == 'start_focus':
                tags += ['resume_vs_start']
            if intent == 'pause_focus':
                tags += ['pause_preservation', 'current_or_spoken_focus_pause']
            if intent == 'alarm':
                tags += ['midnight_noon', 'spoken_number_slot']
            if intent == 'explain':
                tags += ['nudge_cause']
            if intent == 'open_app':
                kind = ('OPEN_SETTINGS', 'OPEN_CALCULATOR', 'OPEN_CLOCK')[app_index // 2]
                app_index += 1
            first = {'id': 'toy_' + str(index), 'family': 'toy_family_' + str(index),
                     'counterpart_id': 'toy_' + str(index + 1), 'utterance': 'Supported fixture row ' + str(index),
                     'semantic_intent': intent, 'oracle_intent': intent, 'expected_kind': kind,
                     'hour': 0, 'minute': 0, 'seconds': seconds, 'hard_tags': tags}
            second = dict(first, id='toy_' + str(index + 1), counterpart_id=first['id'],
                          utterance='Unsupported fixture row ' + str(index), semantic_intent='unknown',
                          expected_kind='UNKNOWN', seconds=0, hard_tags=[])
            rows += [first, second]
    return rows


class DataBoundaries(unittest.TestCase):
    def test_authorization_needs_full_committed_identity(self):
        with self.assertRaisesRegex(ValueError, 'Full root-authorized'):
            data.verify_authorization_commit('short')

    def test_changed_committed_selection_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task = root / 'confirm'
            dev = root / 'dev'
            task.mkdir()
            dev.mkdir()
            (task / 'selection-lock.json').write_bytes(b'changed selection')
            with patch.object(data, 'ROOT', root), patch.object(data, 'TASK', task), patch.object(data, 'DEV', dev):
                with patch.object(data.subprocess, 'run'), patch.object(data.subprocess, 'check_output', return_value=b'committed selection'):
                    with self.assertRaisesRegex(ValueError, 'differs from authorized'):
                        data.verify_authorization_commit('a' * 40)

    def test_valid_balanced_reciprocal_fixture(self):
        self.assertEqual(len(data.validate_rows(toy_rows(), PROTOCOL)), 100)

    def test_counterpart_cannot_point_to_unrelated_family(self):
        rows = toy_rows()
        rows[0]['counterpart_id'] = rows[3]['id']
        with self.assertRaisesRegex(ValueError, 'Reciprocal'):
            data.validate_rows(rows, PROTOCOL)

    def test_boolean_slot_cannot_be_treated_as_integer(self):
        rows = toy_rows()
        rows[0]['seconds'] = True
        with self.assertRaisesRegex(ValueError, 'Exact integer'):
            data.validate_rows(rows, PROTOCOL)

    def test_unknown_cannot_retain_executable_slots(self):
        rows = toy_rows()
        rows[1]['seconds'] = 1
        with self.assertRaisesRegex(ValueError, 'zero slots'):
            data.validate_rows(rows, PROTOCOL)

    def test_pause_cannot_escape_preservation_denominator(self):
        rows = toy_rows()
        row = next(r for r in rows if r['semantic_intent'] == 'pause_focus')
        row['hard_tags'].remove('pause_preservation')
        with self.assertRaisesRegex(ValueError, 'Every Pause'):
            data.validate_rows(rows, PROTOCOL)

    def test_normalization_exposes_signed_punctuation_overlap(self):
        rows = [{'utterance': 'Toy signal -7'}, {'utterance': 'Toy signal 7'}]
        with self.assertRaisesRegex(ValueError, 'Within-corpus'):
            data.reject_overlap(rows, [])

    def test_prior_normalized_fixture_reuse_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Prior/example'):
            data.reject_overlap([{'utterance': 'TOY marker!'}], ['toy marker'])

    def test_missing_prospective_tag_minimum_fails(self):
        rows = toy_rows()
        for row in rows:
            row['hard_tags'] = [tag for tag in row['hard_tags'] if tag != 'nudge_cause']
        with self.assertRaisesRegex(ValueError, 'minimum missing'):
            data.validate_rows(rows, PROTOCOL)

    def test_changed_required_source_pin_stops_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'fixture.py'
            source.write_text('marker="first fixture"')
            required = {'path': 'fixture.py', 'sha256_at_protocol': data.sha(source)}
            protocol = {'corpus': {'overlap': {'actual_available_required_sources': [required]}}}
            source.write_text('marker="changed fixture"')
            with patch.object(data, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'missing/changed'):
                    data.overlap_inventory(protocol)

    def test_training_assistant_messages_do_not_enter_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'toy.jsonl'
            source.write_text(json.dumps({'utterance': 'Toy author input', 'messages': [
                {'role': 'user', 'content': 'Toy user input'},
                {'role': 'assistant', 'content': 'Private assistant output'}]}) + '\n')
            values, _ = data.extract_requests(source)
            self.assertEqual(values, ['Toy author input', 'Toy user input'])

    def test_result_metadata_is_not_extracted_as_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'candidate.json'
            path.write_text(json.dumps({'fixed_examples': ['Toy request'], 'outputs': ['Private output']}))
            values, _ = data.extract_requests(path)
            self.assertEqual(values, ['Toy request'])

    def test_empty_java_fixture_inventory_is_explicitly_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'NoStrings.java'
            path.write_text('final class NoStrings { int count=1; }')
            values, _ = data.extract_requests(path)
            self.assertEqual(values, [])

    def test_native_three_column_requests_use_original_text(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'prompt-cases.tsv'
            path.write_text('toy_id\tunknown\tToy native fixture\n')
            values, _ = data.extract_requests(path)
            self.assertEqual(values, ['Toy native fixture'])

    def test_duplicate_json_labels_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            data.strict_json('{"label":"first","label":"second"}')

    def test_exclusive_creation_preserves_first_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.bin'
            data.write_new(path, b'first evidence')
            with self.assertRaises(FileExistsError):
                data.write_new(path, b'replacement')
            self.assertEqual(path.read_bytes(), b'first evidence')


if __name__ == '__main__':
    unittest.main()
