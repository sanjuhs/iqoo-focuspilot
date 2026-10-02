"""Host-only report/ownership boundaries; never call ADB, a model or installers."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('gate_phone_runner', Path(__file__).with_name('run_phone.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def report():
    return {'schema': 'focuspilot.gate_isolation.v1', 'passed': True, 'checks': 334,
            'expected_checks': 334, 'expected_positive_full_slot_checks': 25,
            'expected_all_route_negative_checks': 273, 'expected_wrong_route_checks': 36,
            'failed_fixture_ids': [], 'failure_type': None,
            'gate_class': 'dev.focuspilot.prototype.ModelCommandGate', 'actions_executed': 0,
            'model_accessed': False, 'production_preferences_accessed': False,
            'services_started': False,
            'scope': 'Already-seen pure gate fixtures; no model inference or tool execution'}


def before():
    return {'installed_app_sha256': runner.helper.APP_SHA, 'checkpoint': {'active': False, 'observation': False, 'points': 100},
            'preferences': {'semantic_sha256': 'original'}, 'model': {'inode': 42, 'sha256': 'original'},
            'grants': {'microphone': False}, 'services_absent': True}


class GatePhoneBoundaryTests(unittest.TestCase):
    def test_complete_success_required_not_just_a_pass_flag(self):
        runner.validate_report(report())
        for key, value in [('checks', 333), ('passed', False), ('checks', True),
                           ('expected_wrong_route_checks', 35), ('failed_fixture_ids', ['wrong_slot_01']),
                           ('failure_type', 'AssertionError'), ('model_accessed', True),
                           ('actions_executed', True), ('scope', 'other')]:
            bad = report()
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                runner.validate_report(bad)
        bad = report()
        del bad['failed_fixture_ids']
        with self.assertRaises(RuntimeError):
            runner.validate_report(bad)

    def test_unknown_test_or_app_cannot_authorize_stop_or_restore(self):
        initial = before()
        current = dict(initial, installed_app_sha256='new-light')
        self.assertEqual('restore', runner.restoration_guard(initial, current, 'candidate-test', 'candidate-test', 'new-light', True))
        self.assertEqual('already_restored', runner.restoration_guard(initial, current, runner.helper.ORIGINAL_TEST_SHA, 'candidate-test', 'new-light', True))
        with self.assertRaisesRegex(RuntimeError, 'Unknown'):
            runner.restoration_guard(initial, current, 'different-test', 'candidate-test', 'new-light', True)
        with self.assertRaisesRegex(RuntimeError, 'Unknown installed app'):
            runner.restoration_guard(initial, dict(current, installed_app_sha256='different-app'), 'candidate-test', 'candidate-test', 'new-light', True)
        with self.assertRaisesRegex(RuntimeError, 'not owned'):
            runner.restoration_guard(initial, initial, 'candidate-test', 'candidate-test', 'new-light', False)

    def test_concurrent_production_mutation_refuses_cleanup_before_any_phone_operation(self):
        initial = before()
        for field, replacement in [('checkpoint', {'active': True}), ('preferences', {'semantic_sha256': 'changed'}),
                                   ('model', {'inode': 43}), ('grants', {'microphone': True}), ('services_absent', False)]:
            current = copy.deepcopy(initial)
            current['installed_app_sha256'] = 'new-light'
            current[field] = replacement
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, 'concurrently'):
                runner.restoration_guard(initial, current, 'candidate-test', 'candidate-test', 'new-light', True)


if __name__ == '__main__':
    unittest.main()
