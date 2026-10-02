"""Boundary checks for preservation ownership and the own-dashboard preflight.

No ADB, phone files, models or package installation are used by these tests.
"""
import copy
import unittest

from phone_bundled_import import (
    MODEL_BYTES, MODEL_SHA, PACKAGE, main_is_focused, restoration_mode,
)


def model_identity(inode):
    return {
        'exists': True, 'bytes': MODEL_BYTES, 'inode': inode,
        'links': 1, 'sha256': MODEL_SHA,
    }


class RestorationOwnershipTest(unittest.TestCase):
    def setUp(self):
        self.original = model_identity(101)
        self.imported = model_identity(202)
        self.absent = {'exists': False}

    def test_recorded_import_can_be_held_before_original_restoration(self):
        self.assertEqual(restoration_mode(
            self.original, copy.deepcopy(self.original),
            copy.deepcopy(self.imported), copy.deepcopy(self.imported),
        ), 'hold_then_restore')

    def test_absent_canonical_can_restore_intact_preserved_original(self):
        self.assertEqual(restoration_mode(
            self.original, copy.deepcopy(self.original), self.absent, None,
        ), 'restore')

    def test_noop_preservation_with_exact_original_is_already_restored(self):
        self.assertEqual(restoration_mode(
            self.original, self.absent, copy.deepcopy(self.original), None,
        ), 'already_restored')

    def test_pinned_new_file_without_recorded_ownership_is_refused(self):
        # Matching weight bytes do not establish that this run created the file.
        for recorded in (None, self.absent, model_identity(303)):
            with self.subTest(recorded=recorded):
                with self.assertRaises(RuntimeError):
                    restoration_mode(
                        self.original, self.original, self.imported, recorded,
                    )

    def test_modified_import_identity_is_refused(self):
        changes = {
            'inode': 303, 'sha256': '0' * 64,
            'bytes': MODEL_BYTES - 1, 'links': 2,
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                current = {**self.imported, field: value}
                with self.assertRaises(RuntimeError):
                    restoration_mode(
                        self.original, self.original, current, self.imported,
                    )

    def test_invalid_pinned_record_cannot_authorize_import_removal(self):
        # Even an exact recorded/current match must satisfy the pinned artifact.
        for field, value in (
            ('sha256', '0' * 64), ('bytes', MODEL_BYTES + 1), ('links', 2),
        ):
            with self.subTest(field=field):
                bad = {**self.imported, field: value}
                with self.assertRaises(RuntimeError):
                    restoration_mode(self.original, self.original, bad, bad)

    def test_original_inode_cannot_be_treated_as_import(self):
        with self.assertRaises(RuntimeError):
            restoration_mode(
                self.original, self.original,
                copy.deepcopy(self.original), copy.deepcopy(self.original),
            )

    def test_missing_preserved_original_is_refused_without_exact_canonical(self):
        for current in (self.absent, self.imported, model_identity(303)):
            with self.subTest(current=current):
                with self.assertRaises(RuntimeError):
                    restoration_mode(
                        self.original, self.absent, current, self.imported,
                    )

    def test_modified_preserved_original_is_refused(self):
        for field, value in (
            ('inode', 404), ('sha256', '1' * 64),
            ('bytes', MODEL_BYTES - 1), ('links', 2),
        ):
            with self.subTest(field=field):
                preserved = {**self.original, field: value}
                for current in (self.absent, self.imported, self.original):
                    with self.subTest(current=current):
                        with self.assertRaises(RuntimeError):
                            restoration_mode(
                                self.original, preserved, current, self.imported,
                            )

    def test_decision_does_not_modify_identity_snapshots(self):
        inputs = [self.original, copy.deepcopy(self.original),
                  self.imported, copy.deepcopy(self.imported)]
        before = copy.deepcopy(inputs)
        restoration_mode(*inputs)
        self.assertEqual(inputs, before)


class DashboardFocusTest(unittest.TestCase):
    @staticmethod
    def focused(component):
        return '  mCurrentFocus=Window{abcdef u0 ' + component + '}\n'

    def test_short_and_fully_qualified_main_are_accepted(self):
        for activity in ('.MainActivity', PACKAGE + '.MainActivity'):
            with self.subTest(activity=activity):
                self.assertTrue(main_is_focused(
                    self.focused(PACKAGE + '/' + activity),
                ))

    def test_other_own_screens_and_main_name_extensions_are_refused(self):
        for activity in (
            '.LocalModelActivity', '.SetupActivity', '.MainActivityExtra',
            '.MainActivity$Nested', PACKAGE + '.MainActivityExtra',
        ):
            with self.subTest(activity=activity):
                self.assertFalse(main_is_focused(
                    self.focused(PACKAGE + '/' + activity),
                ))

    def test_other_packages_are_refused_even_with_main_activity_name(self):
        for package in ('com.android.settings', PACKAGE + '.other',
                        'prefix' + PACKAGE):
            with self.subTest(package=package):
                self.assertFalse(main_is_focused(
                    self.focused(package + '/.MainActivity'),
                ))

    def test_background_main_metadata_does_not_override_current_focus(self):
        window = (
            'mFocusedApp=ActivityRecord{123 u0 ' + PACKAGE + '/.MainActivity}\n'
            + self.focused('com.android.settings/.Settings')
            + 'mLastFocus=Window{456 u0 ' + PACKAGE + '/.MainActivity}\n'
        )
        self.assertFalse(main_is_focused(window))

    def test_missing_or_null_current_focus_is_refused(self):
        for window in ('', 'mCurrentFocus=null\n',
                       'mFocusedApp=' + PACKAGE + '/.MainActivity\n'):
            with self.subTest(window=window):
                self.assertFalse(main_is_focused(window))


if __name__ == '__main__':
    unittest.main()
