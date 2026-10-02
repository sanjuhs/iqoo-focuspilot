import unittest
from unittest.mock import patch
from phone_timed_focus import await_checkpoint


class PersistedCheckpointTests(unittest.TestCase):
    def test_stale_disk_state_is_not_treated_as_terminal_action_failure(self):
        with patch('phone_timed_focus.checkpoint',side_effect=[{'active':'false'},{'active':'true'}]) as read,\
             patch('phone_timed_focus.time.sleep'),patch('phone_timed_focus.time.monotonic',return_value=0):
            self.assertEqual({'active':'true'},await_checkpoint(None,lambda s:s['active']=='true'))
            self.assertEqual(2,read.call_count)

    def test_missing_expected_state_times_out_without_fabricating_success(self):
        with patch('phone_timed_focus.checkpoint',return_value={'active':'false'}),\
             patch('phone_timed_focus.time.monotonic',return_value=0):
            with self.assertRaises(RuntimeError):await_checkpoint(None,lambda s:s['active']=='true',timeout=0)


if __name__=='__main__':unittest.main()
