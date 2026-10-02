import json,pathlib,tempfile,unittest
from generate_cases import generate
from evaluate import decode,strict_match
class EvaluationTests(unittest.TestCase):
 def test_frozen_cases_reproduce(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   x=generate(a);y=generate(b);self.assertEqual(x,y);self.assertEqual(x['rows'],58);self.assertEqual(x['families'],26)
 def test_eos_and_schema_are_required(self):
  good={'text':'{"intent":"timer"}','metrics':{'reached_eos':True}}
  self.assertEqual(decode(json.dumps(good))[:2],('timer',True))
  good['metrics']['reached_eos']=False;self.assertEqual(decode(json.dumps(good))[:2],('unknown',False))
  good['metrics']['reached_eos']=True;good['text']='{"intent":"timer","seconds":60}';self.assertEqual(decode(json.dumps(good))[:2],('unknown',False))
  self.assertEqual(decode('not json')[:2],('unknown',False))
 def test_correct_label_with_wrong_slots_is_failure(self):
  c={'expected_action':'ALARM','hour':6,'minute':45,'seconds':0}
  self.assertTrue(strict_match(c,'ALARM',6,45,0));self.assertFalse(strict_match(c,'ALARM',18,45,0));self.assertFalse(strict_match(c,'ALARM',6,15,0));self.assertFalse(strict_match(c,'UNKNOWN',0,0,0))
 def test_abstention_does_not_count_as_supported_success(self):
  supported={'expected_action':'TIMER','hour':0,'minute':0,'seconds':90}
  must_clarify={'expected_action':'UNKNOWN','hour':0,'minute':0,'seconds':0}
  self.assertFalse(strict_match(supported,'UNKNOWN',0,0,0));self.assertTrue(strict_match(must_clarify,'UNKNOWN',0,0,0));self.assertFalse(strict_match(must_clarify,'START_FOCUS',0,0,0))
if __name__=='__main__':unittest.main()
