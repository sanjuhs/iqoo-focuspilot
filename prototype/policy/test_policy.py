import copy
import math
import unittest

from policy import (FEATURES, PositiveNetwork, dataset_manifest, generate_data,
                    metrics, monotonicity_check, policy_decision, train)


class PositivePolicyTests(unittest.TestCase):
    def setUp(self):
        self.model = PositiveNetwork.initialize(42)
        self.features = [0.6, 0.5, 0.8, 0.4, 0.3, 0.9]

    def test_disjoint_scenario_groups_and_deterministic_data(self):
        splits = generate_data(4, 20)
        families = [{row.family for row in rows} for rows in splits.values()]
        for i, left in enumerate(families):
            for right in families[i + 1:]:
                self.assertFalse(left & right)
        self.assertEqual(dataset_manifest(splits), dataset_manifest(generate_data(4, 20)))
        self.assertNotEqual(dataset_manifest(splits), dataset_manifest(generate_data(5, 20)))

    def test_analytic_gradient_matches_finite_difference(self):
        gradients = self.model.gradients(self.features, 1)
        epsilon = 1e-6
        for key, index in [("output_bias", None), ("output_weights", 3), ("hidden_biases", 3)]:
            plus = copy.deepcopy(self.model.parameters)
            minus = copy.deepcopy(self.model.parameters)
            if index is None:
                plus[key] += epsilon
                minus[key] -= epsilon
                analytic = gradients[key]
            else:
                plus[key][index] += epsilon
                minus[key][index] -= epsilon
                analytic = gradients[key][index]
            loss_plus = -math.log(PositiveNetwork(plus).probability(self.features))
            loss_minus = -math.log(PositiveNetwork(minus).probability(self.features))
            self.assertAlmostEqual(analytic, (loss_plus - loss_minus) / (2 * epsilon), places=7)
        plus, minus = copy.deepcopy(self.model.parameters), copy.deepcopy(self.model.parameters)
        plus["input_weights"][3][2] += epsilon
        minus["input_weights"][3][2] -= epsilon
        numeric = (-math.log(PositiveNetwork(plus).probability(self.features))
                   + math.log(PositiveNetwork(minus).probability(self.features))) / (2 * epsilon)
        self.assertAlmostEqual(gradients["input_weights"][3][2], numeric, places=7)

    def test_contributions_and_hidden_intervention(self):
        report = self.model.inspect(self.features)
        summed = report["output_bias"] + sum(u["logit_contribution"] for u in report["hidden_units"])
        self.assertAlmostEqual(summed, report["logit"], places=12)
        for unit in report["hidden_units"]:
            changed = copy.deepcopy(self.model.parameters)
            changed["output_weights"][unit["unit"]] = 0
            self.assertAlmostEqual(PositiveNetwork(changed).probability(self.features),
                                   unit["probability_if_suppressed"], places=12)
        for item in report["feature_ablations"]:
            changed = self.features[:]
            changed[FEATURES.index(item["feature"])] = 0
            self.assertAlmostEqual(self.model.probability(changed), item["probability_after"], places=12)
            self.assertGreaterEqual(item["score_drop"], -1e-12)

    def test_monotonicity_and_projected_update(self):
        for _ in range(30):
            self.model.step(self.features, 0, 0.1)
        self.assertEqual(monotonicity_check(self.model, trials=100)["failures"], 0)
        weights = [w for row in self.model.parameters["input_weights"] for w in row]
        weights += self.model.parameters["output_weights"]
        self.assertTrue(all(w >= 0 for w in weights))

    def test_pause_permission_and_other_gates_dominate_score(self):
        for gate, kwargs in [("paused", {"paused": True}),
                             ("permission_denied", {"permission_granted": False}),
                             ("focus_inactive", {"focus_active": False}),
                             ("cooldown", {"cooldown": True}),
                             ("stale_observation", {"observation_fresh": False})]:
            outcome = policy_decision(self.model, [1] * 6, 0.0, **kwargs)
            self.assertEqual(outcome["recommendation"], "blocked")
            self.assertEqual(outcome["reason"], gate)
            self.assertIsNone(outcome["probability"])
        self.assertEqual(policy_decision(self.model, self.features, 0.0)["recommendation"], "offer_nudge")
        self.assertEqual(policy_decision(self.model, self.features, 1.0)["recommendation"], "allow")

    def test_invalid_features_and_negative_weights_rejected(self):
        for bad in ([0] * 5, [math.nan] * 6, [1.1] * 6, [-0.1] * 6, [True] * 6):
            with self.assertRaises(ValueError):
                self.model.probability(bad)
        params = copy.deepcopy(self.model.parameters)
        params["output_weights"][0] = -0.01
        with self.assertRaises(ValueError):
            PositiveNetwork(params)
        with self.assertRaises(ValueError):
            policy_decision(self.model, self.features, 0.5, permission_granted="yes")

    def test_training_improves_dev_without_reusing_holdout(self):
        model, details, splits = train(seed=13, epochs=35, per_family=30)
        final = metrics(model, splits["dev"], details["threshold"])
        self.assertLess(final["binary_cross_entropy"], details["initial_dev_metrics"]["binary_cross_entropy"])
        self.assertEqual(monotonicity_check(model, trials=60)["failures"], 0)
        repeated, repeated_details, _ = train(seed=13, epochs=35, per_family=30)
        self.assertEqual(model.parameters, repeated.parameters)
        self.assertEqual(details, repeated_details)


if __name__ == "__main__":
    unittest.main()
