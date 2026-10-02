import unittest
from generate_data import cases
from run_evaluation import strict_score


class EvaluationTests(unittest.TestCase):
    def test_expected_slots_are_independent_and_bounded(self):
        rows=cases()
        self.assertEqual((len(rows),len({r['family'] for r in rows})),(100,50))
        self.assertEqual(sum(r['expected_kind']!='UNKNOWN' for r in rows),40)
        self.assertEqual(len({r['utterance'] for r in rows}),100)
        for r in rows:
            if r['expected_kind'] in {'START_FOCUS','TIMER'}:
                self.assertTrue(0<=r['seconds']<=7200)
            if r['expected_kind']=='ALARM':
                self.assertTrue(0<=r['hour']<24 and 0<=r['minute']<60)

    def test_wrong_slot_and_unsupported_acceptance_are_failures(self):
        rows=[dict(id='a',family='supported',expected_kind='TIMER',hour=0,minute=0,seconds=60),
              dict(id='b',family='unsupported',expected_kind='UNKNOWN',hour=0,minute=0,seconds=0)]
        summary,_=strict_score(rows,{'a':('TIMER',0,0,6),'b':('EXPLAIN',0,0,0)})
        self.assertEqual(summary['strict_correct'],0)
        self.assertEqual(summary['wrong_accepted'],2)
        self.assertEqual(summary['supported_wrong_accepted'],1)
        self.assertEqual(summary['unsupported_false_accepts'],1)

    def test_abstention_is_not_supported_coverage(self):
        rows=[dict(id='a',family='f',expected_kind='ALARM',hour=8,minute=23,seconds=0),
              dict(id='b',family='g',expected_kind='UNKNOWN',hour=0,minute=0,seconds=0)]
        summary,_=strict_score(rows,{'a':('UNKNOWN',0,0,0),'b':('UNKNOWN',0,0,0)})
        self.assertEqual(summary['strict_correct'],1)
        self.assertEqual(summary['supported_false_abstentions'],1)
        self.assertEqual(summary['coverage'],0)
        self.assertIsNone(summary['accepted_precision'])

    def test_missing_or_extra_output_rows_reject(self):
        row=dict(id='a',family='f',expected_kind='UNKNOWN',hour=0,minute=0,seconds=0)
        for outputs in [{},{'a':('UNKNOWN',0,0,0),'extra':('UNKNOWN',0,0,0)}]:
            with self.assertRaises(AssertionError): strict_score([row],outputs)


if __name__=='__main__': unittest.main()
