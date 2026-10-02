"""Focused provenance, fit-boundary and explanation/gate checks; no phone use."""
import copy
import importlib.util
import math
from pathlib import Path
import shutil
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("baseline_experiment", HERE / "experiment.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy, cls.artifact, _, cls.splits = experiment.load_reference()

    def test_reference_and_split_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in experiment.PINS:
                shutil.copyfile(experiment.ROOT / "prototype/policy" / name, directory / name)
            for name in experiment.PINS:
                original = (directory / name).read_bytes()
                (directory / name).write_bytes(original + b"\n")
                with self.assertRaisesRegex(ValueError, "Pinned reference changed"):
                    experiment.load_reference(directory)
                (directory / name).write_bytes(original)
        changed = copy.deepcopy(self.splits)
        row = changed["holdout"][0]
        changed["holdout"][0] = self.policy.Example(row.family, row.features, 1 - row.label)
        with self.assertRaisesRegex(ValueError, "split checksum"):
            experiment.verify_splits(self.policy, changed, self.artifact["dataset"])
        families = [set(value["families"]) for value in self.artifact["dataset"].values()]
        self.assertTrue(all(not families[i] & families[j] for i in range(3) for j in range(i)))

    def test_fit_has_no_holdout_access_and_threshold_is_dev_selected(self):
        p = self.policy
        train = [p.Example("toy_train", [0.0] * 6, 0), p.Example("toy_train", [1.0] * 6, 1)]
        dev = [p.Example("toy_dev", [0.2] * 6, 0), p.Example("toy_dev", [0.8] * 6, 1)]
        protocol = {"seed": 13, "epochs": 3, "initial_learning_rate": 0.02,
                    "threshold_grid": [i / 100 for i in range(10, 91)]}
        class NoReadHoldout:
            def __iter__(self):
                raise AssertionError("Holdout was accessed during fitting")
        container = {"train": train, "dev": dev, "holdout": NoReadHoldout()}
        first, details = experiment.fit(p, container["train"], container["dev"], protocol, False)
        container["holdout"] = [p.Example("different", [0.5] * 6, 1)]
        second, repeated = experiment.fit(p, container["train"], container["dev"], protocol, False)
        self.assertEqual(first.parameters(), second.parameters())
        self.assertEqual(details, repeated)
        expected = min(protocol["threshold_grid"], key=lambda t: (
            1 - p.metrics(first, dev, t)["accuracy"], abs(t - .5), t))
        self.assertEqual(details["threshold"], expected)
        self.assertGreater(details["parameter_update_l2"], 0)

    def test_signed_contributions_projection_and_external_vetoes(self):
        p = self.policy
        model = experiment.Logistic(p, [-2.0, 3.0, 0.4, -0.7, 1.2, .5], bias=-.3)
        x = [.7, .6, .4, .8, .2, .5]
        explanation = model.explain(x)
        expected = -.3 + sum(w * v for w, v in zip([-2, 3, .4, -.7, 1.2, .5], x))
        self.assertAlmostEqual(explanation["logit"], expected, places=14)
        self.assertLess(explanation["contributions"][p.FEATURES[0]], 0)
        self.assertAlmostEqual(model.probability(x), 1 / (1 + math.exp(-expected)), places=14)
        projected = experiment.Logistic(p, projected=True)
        projected.step([1.0] * 6, 0, 1.0)
        self.assertEqual(projected.weights, [0.0] * 6)
        self.assertLess(projected.bias, 0)
        high = experiment.Logistic(p, [100.0] * 6, 100.0)
        checks = experiment.gate_checks(p, {"high": high}, {"high": .5})
        self.assertEqual(checks["checks"], 5)
        self.assertEqual(checks["failures"], 0)
        with self.assertRaises(ValueError):
            model.probability([float("nan")] * 6)


if __name__ == "__main__":
    unittest.main()
