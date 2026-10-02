package dev.focuspilot.prototype;

import org.junit.Test;
import java.util.Random;
import static org.junit.Assert.*;

/** Generated Python held-out reference fixtures, not hand-invented expected scores. */
public class TrainedPolicyTest {
    // Min/max/nearest-threshold examples per held-out scenario family.
    private static final double[][] FIXTURE_FEATURES = {
        {0.09667869344225002, 0.002238690780475963, 0.18739399940885393, 0.881884122298174, 0.806774608715406, 0.4606382687166447}, // correlated_overruns
        {0.8391839252928903, 0.8695794693654164, 0.9786706619731318, 0.1752318457623765, 0.6662260369465749, 0.4281712375822446}, // correlated_overruns
        {0.4584634713669008, 0.45387353843465644, 0.8970261988295808, 0.33155901882215566, 0.6639392308551885, 0.08130102966100461}, // correlated_overruns
        {0.22446637941011022, 0.6331063610607578, 0.21165247708723875, 0.38002386324492204, 0.36224748579854127, 0.579800931338829}, // moderate_everywhere
        {0.7303741715738183, 0.7118089457209202, 0.6004414363647003, 0.6892954342285427, 0.5266750827211613, 0.6851353540877871}, // moderate_everywhere
        {0.42348851669784393, 0.5949625053802399, 0.39357401222428834, 0.35256566108624554, 0.6308337752839022, 0.3418755869843042}, // moderate_everywhere
        {0.0744113138318922, 0.9469826219587074, 0.015946553454238854, 0.08432948499561264, 0.11090130340411054, 0.07882077251852872}, // sparse_extremes
        {0.8720439598987271, 0.9452772104323252, 0.8828056884314056, 0.9546836166916051, 0.07174758145036884, 0.8072095973532318}, // sparse_extremes
        {0.8402261262999644, 0.02925685523614761, 0.970108217565208, 0.04596040464508276, 0.904000182611912, 0.02824891745256867}, // sparse_extremes
    };
    private static final double[] FIXTURE_SCORES = {0.0029154998354511846, 1.0, 0.6826135683596624, 0.0029154998354511846, 0.9999999999999711, 0.6576971231930878, 0.0029154998354511846, 1.0, 0.735395683938086};
    private static final double[] FIXTURE_LOGITS = {-5.8347942455574575, 39.958811362966316, 0.7658088550196362, -5.8347942455574575, 31.179504477585855, 0.6530485764118072, -5.8347942455574575, 53.4112964777062, 1.0221731366556144};
    private static final double[] REFERENCE_CONTRIBUTIONS = {0.9033426734564931, 0.7613802068272829, 1.2384656496029631, 0.8417027764024847, 0.3140574074750255, 0.8046861677692076, 0.6025389963917753, 1.134429222651861};
    private static final double[] REFERENCE_ABLATIONS = {0.0029154998354511846, 0.0029154998354511846, 0.0029154998354511846, 0.039192179746460325, 0.026085597521362844, 0.4340870654974393};
    @Test public void matchesPythonHeldoutReference() {
        for (int i = 0; i < FIXTURE_FEATURES.length; i++) {
            TrainedPolicy.Evaluation result = TrainedPolicy.evaluate(FIXTURE_FEATURES[i]);
            assertEquals("score fixture " + i, FIXTURE_SCORES[i], result.score, 1e-12);
            assertEquals("logit fixture " + i, FIXTURE_LOGITS[i], result.logit, 1e-10);
            assertEquals(FIXTURE_SCORES[i] >= TrainedPolicy.DEV_THRESHOLD,
                         result.score >= TrainedPolicy.DEV_THRESHOLD);
        }
    }

    @Test public void matchesPythonContributionsAndFeatureAblations() {
        TrainedPolicy.Evaluation result = TrainedPolicy.evaluate(FIXTURE_FEATURES[2]);
        assertArrayEquals(REFERENCE_CONTRIBUTIONS, result.hiddenContributions(), 1e-10);
        assertArrayEquals(REFERENCE_ABLATIONS, result.featureAblationScores(), 1e-12);
        double total = result.outputBias;
        for (double contribution : result.hiddenContributions()) total += contribution;
        assertEquals(result.logit, total, 1e-12);
        double[] drops = result.featureAblationDrops();
        for (int i = 0; i < 6; i++) {
            assertEquals(result.score - REFERENCE_ABLATIONS[i], drops[i], 1e-12);
            assertTrue(drops[i] >= -1e-12);
        }
    }

    @Test public void isMonotonicAcrossSampledRiskIncreases() {
        Random random = new Random(9);
        for (int trial = 0; trial < 300; trial++) {
            double[] features = new double[6];
            for (int i = 0; i < 6; i++) features[i] = random.nextDouble();
            double score = TrainedPolicy.evaluate(features).score;
            for (int i = 0; i < 6; i++) {
                double increased = features[i] + random.nextDouble() * (1.0 - features[i]);
                assertTrue(TrainedPolicy.intervene(features, i, increased).score >= score - 1e-12);
            }
        }
    }

    @Test public void rejectsMalformedAndUnboundedFeatures() {
        assertThrows(IllegalArgumentException.class, () -> TrainedPolicy.evaluate(null));
        assertThrows(IllegalArgumentException.class, () -> TrainedPolicy.evaluate(new double[5]));
        for (double invalid : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, -0.1, 1.1}) {
            double[] features = new double[6]; features[3] = invalid;
            assertThrows(IllegalArgumentException.class, () -> TrainedPolicy.evaluate(features));
        }
        assertThrows(IllegalArgumentException.class, () -> TrainedPolicy.intervene(new double[6], 6, 0.5));
        assertThrows(IllegalArgumentException.class, () -> TrainedPolicy.intervene(new double[6], 0, -0.1));
    }

    @Test public void resultAndFeatureNamesAreDefensiveCopies() {
        double[] features = FIXTURE_FEATURES[0].clone();
        TrainedPolicy.Evaluation original = TrainedPolicy.evaluate(features);
        double score = original.score;
        features[0] = 1.0 - features[0];
        assertEquals(FIXTURE_FEATURES[0][0], original.features()[0], 0.0);
        double[] contributions = original.hiddenContributions(); contributions[0] = -1000;
        assertTrue(original.hiddenContributions()[0] >= 0.0);
        String[] names = TrainedPolicy.featureNames(); names[0] = "mutated";
        assertEquals("selected_app_budget_overrun", TrainedPolicy.featureNames()[0]);
        assertEquals(score, TrainedPolicy.evaluate(FIXTURE_FEATURES[0]).score, 0.0);
    }

    @Test public void hiddenSuppressionCannotRaiseSyntheticRisk() {
        for (double[] features : FIXTURE_FEATURES) {
            TrainedPolicy.Evaluation result = TrainedPolicy.evaluate(features);
            for (double counterfactual : result.suppressedHiddenScores())
                assertTrue(counterfactual <= result.score + 1e-12);
        }
    }
}
