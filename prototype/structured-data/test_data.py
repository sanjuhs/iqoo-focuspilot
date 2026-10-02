"""Abstract structured-object contract tests; no actual author requests."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('structured_data', Path(__file__).with_name('generate_data.py'))
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


def fixtures():
    rows = []
    for intent, count in data.COUNTS.items():
        for n in range(count):
            expected = {'intent': intent}
            if intent in {'start_focus', 'timer'}:
                expected['duration_seconds'] = 0 if intent == 'start_focus' and n == 0 else 91
            elif intent == 'alarm':
                expected.update(hour=12, minute=0)
            elif intent == 'open_app':
                expected['app'] = 'clock'
            rows.append({'id': f'abstract_{intent}_{n}',
                'utterance': f'Structured contract fixture {intent} item {n}', 'expected': expected})
    return rows


class StructuredDataTests(unittest.TestCase):
    def test_all_seven_shapes_and_exact_cohort(self):
        data.validate_rows(fixtures())

    def test_slotless_responses_reject_extraneous_duration(self):
        for intent in ('pause_focus', 'explain', 'unknown'):
            with self.assertRaises(ValueError):
                data.validate_expected({'intent': intent, 'duration_seconds': 0})

    def test_untimed_focus_allowed_zero_timer_rejected(self):
        data.validate_expected({'intent': 'start_focus', 'duration_seconds': 0})
        with self.assertRaises(ValueError): data.validate_expected({'intent': 'timer', 'duration_seconds': 0})

    def test_duration_endpoints_and_nonintegers(self):
        for intent in ('start_focus', 'timer'):
            for good in (1, 7200): data.validate_expected({'intent': intent, 'duration_seconds': good})
            for bad in (-1, 7201, True, 1.0):
                with self.assertRaises(ValueError): data.validate_expected({'intent': intent, 'duration_seconds': bad})

    def test_alarm_slots_are_exact_and_complete(self):
        for h, m in ((0, 0), (12, 0), (23, 59)):
            data.validate_expected({'intent': 'alarm', 'hour': h, 'minute': m})
        for bad in ({'intent': 'alarm', 'hour': 24, 'minute': 0},
                    {'intent': 'alarm', 'hour': 6, 'minute': 60},
                    {'intent': 'alarm', 'hour': True, 'minute': 0},
                    {'intent': 'alarm', 'hour': 6}):
            with self.assertRaises(ValueError): data.validate_expected(bad)

    def test_open_app_allowlist_and_shape(self):
        for app in data.APPS: data.validate_expected({'intent': 'open_app', 'app': app})
        for bad in ({'intent': 'open_app', 'app': 'banking'}, {'intent': 'open_app'},
                    {'intent': 'open_app', 'app': 'clock', 'hour': 6}):
            with self.assertRaises(ValueError): data.validate_expected(bad)

    def test_changed_class_balance_and_duplicate_request_rejected(self):
        rows = fixtures(); rows[0]['expected'] = {'intent': 'unknown'}
        with self.assertRaises(ValueError): data.validate_rows(rows)
        rows = fixtures(); rows[1]['utterance'] = rows[0]['utterance'].upper() + '!!'
        with self.assertRaises(ValueError): data.validate_rows(rows)

    def test_single_line_and_utf16_bounds(self):
        for bad in ('two\nlines', '\U0001f642' * 251):
            rows = fixtures(); rows[0]['utterance'] = bad
            with self.assertRaises(ValueError): data.validate_rows(rows)

    def test_strict_json_duplicate_and_nonfinite_rejected(self):
        for raw in ('{"intent":"explain","intent":"unknown"}', '{"duration_seconds":NaN}'):
            with self.assertRaises(ValueError): data.strict_json(raw)


if __name__ == '__main__':
    unittest.main()
