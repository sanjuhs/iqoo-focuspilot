import unittest
from phone_readback import terminal_readback, assert_inert_checkpoint


class ReadbackEvidenceBoundaryTests(unittest.TestCase):
    def test_transient_reading_is_not_engine_completion(self):
        self.assertIsNone(terminal_readback(['Reading only the confirmed focus status. No microphone is active.']))
        self.assertEqual(terminal_readback(['Confirmed focus status read with an installed offline voice.']), 'engine_completed_callback')

    def test_failure_missing_voice_and_mute_are_not_success(self):
        for text,outcome in [('No installed offline English TTS voice is ready. Nothing was spoken.','offline_voice_unavailable'),
                             ('Offline readback failed. The status remains on screen.','engine_error_callback'),
                             ('Companion voice is muted. Your confirmed status remains on screen.','companion_muted')]:
            with self.subTest(outcome=outcome):self.assertEqual(terminal_readback([text]),outcome)

    def test_conflicting_terminal_states_are_rejected(self):
        with self.assertRaises(RuntimeError):terminal_readback(['Confirmed focus status read with an installed offline voice.','Offline readback failed. The status remains on screen.'])

    def test_already_paused_tts_cannot_hide_elapsed_or_points_change(self):
        before={'active':False,'observation':False,'points':100,'elapsed_ms':57331}
        assert_inert_checkpoint(before,dict(before))
        for field,value in [('active',True),('observation',True),('points',99),('elapsed_ms',57332)]:
            with self.subTest(field=field),self.assertRaises(RuntimeError):assert_inert_checkpoint(before,{**before,field:value})


if __name__=='__main__':unittest.main()
