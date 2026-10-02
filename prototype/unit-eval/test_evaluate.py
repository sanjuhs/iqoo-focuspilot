import unittest
from evaluate import assess, expected_raw

CRITERIA={'complete_supported_net_gain_minimum':2,'complete_supported_losses_maximum':0,'complete_start_minimum':1,'wrong_accepts_maximum':0,'unknown_validator_refusals_required':6}

class DevelopmentDecision(unittest.TestCase):
    def sample(self):
        return {'per_class':{'start_focus':{'complete_correct':1}},'wrong_accepts':0,'unknown_validator_refusals':6}
    def test_net_gain_cannot_hide_a_regression(self):
        checks=assess(self.sample(),{'gain':5,'loss':1},CRITERIA)
        self.assertTrue(checks['net_gain']);self.assertFalse(checks['losses'])
    def test_arithmetic_gain_does_not_qualify_without_focus(self):
        candidate=self.sample();candidate['per_class']['start_focus']['complete_correct']=0
        self.assertFalse(assess(candidate,{'gain':3,'loss':0},CRITERIA)['start'])
    def test_wrong_accept_or_missing_unknown_refusal_fails(self):
        candidate=self.sample();candidate['wrong_accepts']=1;candidate['unknown_validator_refusals']=5
        checks=assess(candidate,{'gain':3,'loss':0},CRITERIA)
        self.assertFalse(checks['wrong_accepts']);self.assertFalse(checks['unknown_refusals'])
    def test_fixed_gain_threshold_is_inclusive(self):
        self.assertTrue(all(assess(self.sample(),{'gain':2,'loss':0},CRITERIA).values()))
        self.assertFalse(assess(self.sample(),{'gain':1,'loss':0},CRITERIA)['net_gain'])
    def test_reviewed_raw_unit_labels_cannot_disagree_with_canonical_seconds(self):
        row={'id':'fixture','expected':{'intent':'start_focus','duration_seconds':900}}
        self.assertEqual({'intent':'start_focus','amount':15,'unit':'minutes'},expected_raw(row,{'fixture':{'intent':'start_focus','amount':15,'unit':'minutes'}}))
        row['expected']['duration_seconds']=150
        with self.assertRaises(ValueError):expected_raw(row,{'fixture':{'intent':'start_focus','amount':15,'unit':'minutes'}})

if __name__=='__main__':unittest.main()
