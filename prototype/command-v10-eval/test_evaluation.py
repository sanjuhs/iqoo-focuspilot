import unittest
from generate_data import cases
from run_evaluation import strict_score,paired_gate,semantic_score


class EvaluationTests(unittest.TestCase):
    def test_frozen_balanced_cases_and_independent_semantic_labels(self):
        rows=cases();self.assertEqual((len(rows),len({r['family'] for r in rows})),(100,50))
        self.assertEqual(sum(r['expected_kind']!='UNKNOWN' for r in rows),50)
        self.assertEqual(sum(r['semantic_intent']=='unknown' for r in rows),50)
        self.assertTrue(all(r['semantic_intent']=='unknown' or r['semantic_intent']==r['oracle_intent'] for r in rows))
        for r in rows:
            if r['expected_kind']=='ALARM':self.assertTrue(0<=r['hour']<24 and 0<=r['minute']<60)
            if r['expected_kind']=='TIMER':self.assertTrue(1<=r['seconds']<=7200)

    def test_wrong_slot_is_distinct_from_wrong_action_and_rejection(self):
        rows=[dict(id='a',family='f',expected_kind='TIMER',hour=0,minute=0,seconds=120),
              dict(id='b',family='g',expected_kind='ALARM',hour=5,minute=16,seconds=0),
              dict(id='c',family='h',expected_kind='UNKNOWN',hour=0,minute=0,seconds=0)]
        s,_=strict_score(rows,{'a':('TIMER',0,0,12),'b':('EXPLAIN',0,0,0),'c':('UNKNOWN',0,0,0)})
        self.assertEqual(s['strict_correct'],1);self.assertEqual(s['supported_wrong_accepted'],2)
        self.assertEqual(s['supported_wrong_slots'],1);self.assertEqual(s['unsupported_false_accepts'],0)

    def test_abstention_never_counts_as_supported_coverage(self):
        rows=[dict(id='a',family='f',expected_kind='START_FOCUS',hour=0,minute=0,seconds=47)]
        s,_=strict_score(rows,{'a':('UNKNOWN',0,0,0)})
        self.assertEqual(s['supported_correct'],0);self.assertEqual(s['supported_false_abstentions'],1)
        self.assertIsNone(s['accepted_precision'])

    def test_pairing_exposes_losses_behind_net_improvement(self):
        a=[dict(id='a',family='f',supported=True,correct=False),dict(id='b',family='g',supported=True,correct=True),
           dict(id='c',family='h',supported=False,correct=False)]
        b=[dict(id='a',family='f',supported=True,correct=True),dict(id='b',family='g',supported=True,correct=False),
           dict(id='c',family='h',supported=False,correct=True)]
        s=paired_gate(a,b);self.assertEqual((s['supported_gains'],s['supported_losses']),(1,1))
        self.assertEqual(s['losses_per_family'],{'g':1})

    def test_unsupported_oracle_action_is_not_semantic_label(self):
        rows=[dict(id='a',expected_kind='UNKNOWN',semantic_intent='unknown',oracle_intent='timer'),
              dict(id='b',expected_kind='TIMER',semantic_intent='timer',oracle_intent='timer')]
        s=semantic_score(rows,{'a':dict(intent='timer',valid=True),'b':dict(intent='timer',valid=True)})
        self.assertEqual(s['semantic_correct'],1);self.assertEqual(s['unknown_nonunknown_proposals'],1)
        self.assertEqual(s['supported_correct'],1)

    def test_missing_or_duplicate_output_contract_rejects(self):
        row=dict(id='a',family='f',expected_kind='UNKNOWN',hour=0,minute=0,seconds=0)
        with self.assertRaises(AssertionError):strict_score([row],{})
        with self.assertRaises(AssertionError):strict_score([row],{'a':('UNKNOWN',0,0,0),'x':('UNKNOWN',0,0,0)})


if __name__=='__main__':unittest.main()
