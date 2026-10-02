"""Fixture and provenance regressions; no model/phone execution."""
import base64
import importlib.util
import json
from pathlib import Path
import unittest

import generate_data
import run_research


class ResearchTests(unittest.TestCase):
    def test_fixtures_have_fixed_domains_bounds_and_prior_criteria(self):
        rows = generate_data.cases()
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(row["kind"] == "benign" for row in rows), 8)
        self.assertEqual(sum(row["kind"] == "tricky" for row in rows), 4)
        self.assertEqual(len({row["id"] for row in rows}), 12)
        for row in rows:
            self.assertLessEqual(len(row["goal"].encode("utf-16-le")) // 2, 120)
            self.assertTrue(row["criterion"].strip())
            self.assertEqual(base64.b64decode(run_research.encoded(row["goal"])).decode(), row["goal"])
        self.assertEqual(sum(row["expected"] == "decline" for row in rows), 2)

    def test_freeze_hashes_if_capture_protocol_exists(self):
        manifest = run_research.HERE / "freeze-manifest.json"
        if not manifest.exists():
            self.skipTest("Shared contract has not been frozen yet")
        frozen = run_research.verify_freeze()
        self.assertTrue(frozen["frozen_before_any_model_run"])
        self.assertEqual(frozen["native_sha256"], run_research.NATIVE_SHA)
        self.assertEqual(frozen["model_sha256"], run_research.MODEL_SHA)
        self.assertEqual(len(frozen["prompt_sha256_by_id"]), 12)

    def test_actual_capture_complete_not_just_parseable_if_present(self):
        result_path = run_research.HERE / "results.json"
        if not result_path.exists():
            self.skipTest("No actual capture yet")
        result = json.loads(result_path.read_text())
        counts = result["counts"]
        self.assertEqual(counts["captured"], 12)
        self.assertEqual(counts["completed_eos_and_schema"], counts["usable_shape_three_steps"] + counts["explicit_declines"])
        self.assertEqual(counts["completed_eos_and_schema"] + counts["invalid_or_incomplete"], 12)
        self.assertTrue(result["capture_enabled_all_false"])
        self.assertTrue(result["cpu_only_all_true"])
        self.assertTrue(result["activations_all_empty"])
        process = json.loads((run_research.BUILD / "process-result.json").read_text())
        self.assertEqual(process["output_sha256"], run_research.sha(run_research.BUILD / "output.tsv"))


if __name__ == "__main__":
    unittest.main()
