"""Independent source-unit and preservation-contract fixtures; no candidate calls."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('unit_regression', Path(__file__).with_name('regression.py'))
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


def duration_row(text, seconds, intent='start_focus'):
    return {'id': 'abstract_duration', 'utterance': text, 'intent': intent,
        'expected_kind': 'START_FOCUS' if intent == 'start_focus' else 'TIMER',
        'hour': 0, 'minute': 0, 'seconds': seconds}


class UnitRegressionTests(unittest.TestCase):
    def test_source_quantity_preserves_minutes_not_converted_seconds(self):
        reply = data.source_reply(duration_row('Concentrate for forty-five minutes.', 2700), 'start_focus')
        self.assertEqual(reply, {'intent': 'start_focus', 'amount': 45, 'unit': 'minutes'})

    def test_seconds_hyphenation_and_hundred_words(self):
        self.assertEqual(data.source_reply(duration_row('A one-hundred-and-forty-one-second timer.', 141, 'timer'), 'timer'),
            {'intent': 'timer', 'amount': 141, 'unit': 'seconds'})
        self.assertEqual(data.source_quantities('A 27-minute focus block.')[0]['seconds'], 1620)

    def test_hours_endpoint_and_source_conversion(self):
        self.assertEqual(data.source_reply(duration_row('A two-hour focus block.', 7200), 'start_focus')['unit'], 'hours')
        self.assertEqual(data.source_reply(duration_row('A one-second focus block.', 1), 'start_focus')['amount'], 1)

    def test_untimed_focus_zero_none_and_gold_disagreement_fail(self):
        self.assertEqual(data.source_reply(duration_row('Focus now.', 0), 'start_focus'), {'intent': 'start_focus', 'amount': 0, 'unit': 'none'})
        with self.assertRaises(ValueError): data.source_reply(duration_row('Focus for 23 minutes.', 23), 'start_focus')
        with self.assertRaises(ValueError): data.source_reply(duration_row('Focus for 23 minutes.', 0), 'start_focus')

    def test_no_ambiguous_multi_quantity_correct_oracle(self):
        with self.assertRaises(ValueError): data.source_reply(duration_row('Focus for 3 minutes or 5 minutes.', 180), 'start_focus')

    def test_alarm_meridians_and_word_minutes(self):
        self.assertEqual(data.source_clock('Wake at seven forty-five PM.'), {'hour': 19, 'minute': 45})
        self.assertEqual(data.source_clock('Alarm at twelve AM.'), {'hour': 0, 'minute': 0})
        self.assertEqual(data.source_clock('Alarm at noon.'), {'hour': 12, 'minute': 0})
        self.assertEqual(data.source_clock('Alarm at 22:14.'), {'hour': 22, 'minute': 14})

    def test_invalid_clock_and_word_composition_do_not_create_oracle(self):
        self.assertIsNone(data.source_clock('Alarm at 25:61.'))
        with self.assertRaises(ValueError): data.number(['thirty', 'thirty'])

    def test_wrong_routes_are_explicit_mock_slots_not_gold(self):
        row = duration_row('Focus now.', 0)
        self.assertEqual(data.source_reply(row, 'timer'), {'intent': 'timer', 'amount': 1, 'unit': 'seconds'})
        self.assertEqual(data.source_reply(row, 'alarm'), {'intent': 'alarm', 'hour': 0, 'minute': 0})
        self.assertEqual(data.source_reply(row, 'open_app'), {'intent': 'open_app', 'app': 'clock'})

    def test_open_target_and_alarm_source_agreement(self):
        row = {'id': 'abstract_app', 'utterance': 'Show calculator.', 'intent': 'open_app', 'expected_kind': 'OPEN_CALCULATOR', 'hour': 0, 'minute': 0, 'seconds': 0}
        self.assertEqual(data.source_reply(row, 'open_app'), {'intent': 'open_app', 'app': 'calculator'})
        row = {'id': 'abstract_alarm', 'utterance': 'Wake at six seventeen PM.', 'intent': 'alarm', 'expected_kind': 'ALARM', 'hour': 18, 'minute': 17, 'seconds': 0}
        self.assertEqual(data.source_reply(row, 'alarm'), {'intent': 'alarm', 'hour': 18, 'minute': 17})
        row['hour'] = 6
        with self.assertRaises(ValueError): data.source_reply(row, 'alarm')


if __name__ == '__main__':
    unittest.main()
