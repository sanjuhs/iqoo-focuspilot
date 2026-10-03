import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('geniex_build_private', Path(__file__).with_name('build_private.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BuildBoundsTest(unittest.TestCase):
    def test_native_copy_reserve_and_budget_fail_before_build(self):
        with self.assertRaises(ValueError):
            build.budget_preflight(11_000_000_000, 4_000_000, build.MIN_RESERVE - 1)
        with self.assertRaises(ValueError):
            build.budget_preflight(14_000_000_000, 4_000_000, build.DEFAULT_RESERVE)
        self.assertEqual(12_254_000_000, build.budget_preflight(11_000_000_000, 4_000_000, build.DEFAULT_RESERVE))

    def test_global_cache_growth_never_credits_unrelated_deletions(self):
        before = {'a': 100, 'b': 500, 'removed': 900}
        after = {'a': 130, 'b': 400, 'new-transform': 217_483_576}
        self.assertEqual(217_483_606, build.cache_growth(before, after))


if __name__ == '__main__':
    unittest.main()
