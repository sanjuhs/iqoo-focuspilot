import unittest
from phone_task_guide import GOAL, STEPS, PREFIX, checkpoint, require_empty_test_state, owns_synthetic_guide, assert_plan
import hashlib


class SyntheticGuideBoundaryTests(unittest.TestCase):
    def test_existing_goal_even_without_guide_cannot_be_overwritten(self):
        with self.assertRaises(RuntimeError): require_empty_test_state({'focusGoal': 'A private existing goal'})

    def test_corrupt_or_partial_guide_cannot_be_treated_as_empty(self):
        for record in ({PREFIX+'revision': ''}, {PREFIX+'schema': {'unsupported_type': 'set'}}):
            with self.subTest(record=record), self.assertRaises(RuntimeError): require_empty_test_state(record)

    def test_active_observation_or_declared_targets_refuse_test(self):
        for record in ({'activeCheckpoint': True}, {'observe': True}, {'shadowPlannedFocus': 60000}, {'shadowContinuousLimit': 60000}):
            with self.subTest(record=record), self.assertRaises(RuntimeError): require_empty_test_state(record)

    def test_cleanup_cannot_clear_a_user_changed_goal_or_steps(self):
        record={'focusGoal': GOAL, PREFIX+'schema': 1, PREFIX+'count': 3,
                PREFIX+'goal': hashlib.sha256(GOAL.encode()).hexdigest()}
        record.update({PREFIX+'step.'+str(i): step for i,step in enumerate(STEPS)})
        self.assertTrue(owns_synthetic_guide(record))
        self.assertFalse(owns_synthetic_guide({**record, 'focusGoal': 'Changed by the user'}))
        self.assertFalse(owns_synthetic_guide({**record, PREFIX+'step.1': 'A user supplied step'}))

    def test_restoration_assertion_rejects_stale_step_and_wrong_association(self):
        record={'focusGoal': GOAL, PREFIX+'schema': 1, PREFIX+'count': 3, PREFIX+'completed': 0,
                PREFIX+'revision': 'example revision', PREFIX+'goal': hashlib.sha256(GOAL.encode()).hexdigest()}
        record.update({PREFIX+'step.'+str(i): step for i,step in enumerate(STEPS)})
        assert_plan(record, STEPS, 0)
        for bad in ({**record, PREFIX+'step.7': 'Stale'}, {**record, PREFIX+'goal': '0'*64}):
            with self.assertRaises(AssertionError): assert_plan(bad, STEPS, 0)


class CleanupFailureTests(unittest.TestCase):
    def test_locked_phone_records_cleanup_failure_without_claiming_restoration(self):
        from phone_task_guide import cleanup_synthetic
        from unittest.mock import Mock, patch
        lab=Mock();lab.guard.side_effect=RuntimeError('Locked own app')
        values={'focusGoal':GOAL};baseline=checkpoint(values)
        with patch('phone_task_guide.preferences', return_value=values): result=cleanup_synthetic(lab,baseline,True)
        self.assertFalse(result['cleanup_verified'])
        self.assertEqual(result['cleanup_failure_type'],'RuntimeError')
        self.assertFalse(result['empty_goal_restored'])
        lab.tap.assert_not_called()

    def test_failed_private_read_never_fabricates_empty_state(self):
        from phone_task_guide import cleanup_synthetic
        from unittest.mock import Mock, patch
        with patch('phone_task_guide.preferences', side_effect=RuntimeError('Read unavailable')):
            result=cleanup_synthetic(Mock(),checkpoint({}),True)
        self.assertFalse(result['cleanup_verified'])
        self.assertIsNone(result['final_checkpoint'])
        self.assertFalse(result['guide_record_removed'])

    def test_new_user_session_is_preserved_without_cleanup_taps(self):
        from phone_task_guide import cleanup_synthetic
        from unittest.mock import Mock, patch
        lab=Mock();values={'focusGoal':GOAL,'activeCheckpoint':True}
        with patch('phone_task_guide.preferences', return_value=values): result=cleanup_synthetic(lab,checkpoint({}),True)
        self.assertFalse(result['cleanup_verified'])
        lab.guard.assert_not_called();lab.tap.assert_not_called()


if __name__ == '__main__': unittest.main()
