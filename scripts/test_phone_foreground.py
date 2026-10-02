import unittest
from phone_model_smoke import own_interactive_foreground


class PhoneForegroundTests(unittest.TestCase):
    window = "mCurrentFocus=Window{abc u0 dev.focuspilot.prototype/.MainActivity}\nmAwake=true"

    def test_current_device_activity_keyguard_proves_unlocked(self):
        self.assertTrue(own_interactive_foreground(self.window, "mKeyguardShowing=false"))

    def test_missing_lock_or_awake_metadata_cannot_authorize_capture(self):
        self.assertFalse(own_interactive_foreground(self.window, ""))
        self.assertFalse(own_interactive_foreground(self.window.replace("mAwake=true", ""), "mKeyguardShowing=false"))

    def test_screen_off_and_any_showing_keyguard_block_capture(self):
        self.assertFalse(own_interactive_foreground(self.window.replace("mAwake=true", "mAwake=false"), "mKeyguardShowing=false"))
        self.assertFalse(own_interactive_foreground(self.window, "mKeyguardShowing=true"))
        self.assertFalse(own_interactive_foreground(self.window, "mKeyguardShowing=false\nmKeyguardShowing=true"))

    def test_legacy_false_is_observed_evidence_but_true_wins(self):
        self.assertTrue(own_interactive_foreground(self.window + "\nmShowingLockscreen=false", ""))
        self.assertFalse(own_interactive_foreground(self.window + "\nmShowingLockscreen=true", "mKeyguardShowing=false"))

    def test_other_owner_or_similar_package_name_is_not_our_app(self):
        self.assertFalse(own_interactive_foreground(self.window.replace("dev.focuspilot.prototype/", "dev.focuspilot.prototype.evil/"), "mKeyguardShowing=false"))
        self.assertFalse(own_interactive_foreground("mCurrentFocus=Window{abc u0 other.app/.MainActivity dev.focuspilot.prototype}\nmAwake=true", "mKeyguardShowing=false"))


if __name__ == "__main__":
    unittest.main()
