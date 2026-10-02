import json
import unittest
from phone_focus_summary import fixture_report


class ReportBoundaries(unittest.TestCase):
    def report(self, **changes):
        r = dict(schema='focuspilot.focus_summary_isolation.v1', passed=True,
                 checks=12, expected_checks=12, failed_fixture_ids=[], failure_type=None,
                 model_accessed=False, production_preferences_accessed=False,
                 production_singleton_used=False, services_started=False, actions_executed=0)
        r.update(changes)
        return 'INSTRUMENTATION_RESULT: report_json=' + json.dumps(r) + '\nINSTRUMENTATION_CODE: -1'

    def test_complete_exact_report(self):
        self.assertEqual(12, fixture_report(self.report())['checks'])

    def test_partial_failed_or_impure_report(self):
        for changed in [dict(checks=11), dict(passed=False), dict(failed_fixture_ids=['legacy']),
                        dict(failure_type='AssertionError'), dict(model_accessed=True),
                        dict(production_preferences_accessed=True), dict(production_singleton_used=True),
                        dict(services_started=True), dict(actions_executed=1)]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                fixture_report(self.report(**changed))

    def test_missing_duplicated_or_unfinished_report(self):
        valid = self.report()
        for raw in ['summary only', valid + '\n' + valid,
                    valid.replace('INSTRUMENTATION_CODE: -1', 'INSTRUMENTATION_CODE: 0')]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                fixture_report(raw)


if __name__ == '__main__':
    unittest.main()
