"""Checker boundaries only; no candidate import, compile, calls or inference."""
import base64
import json
from pathlib import Path
import tempfile
import unittest

import validate as checker


class Boundaries(unittest.TestCase):
 def gold(self):return [{'route_id':'one','expected_kind_slots':['TIMER',0,0,30]}]
 def record(self,kind='TIMER',seconds=30,origin='CHECKED_MODEL'):
  canonical={'intent':'timer','duration_seconds':seconds}
  return '\t'.join(['one','true',kind,'0','0',str(seconds),'',
   base64.b64encode(json.dumps(canonical).encode()).decode(),base64.b64encode(b'Review').decode(),origin])+'\n'

 def test_canonical_full_duration_and_app_identity(self):
  self.assertEqual(checker.canonical_tuple({'intent':'timer','duration_seconds':30}),['TIMER',0,0,30])
  self.assertEqual(checker.canonical_tuple({'intent':'open_app','app':'clock'}),['OPEN_CLOCK',0,0,0])
  for value in [{'intent':'timer','duration_seconds':True},{'intent':'timer','duration_seconds':0},
                {'intent':'alarm','hour':24,'minute':0},{'intent':'open_app','app':'browser'},
                {'intent':'unknown','duration_seconds':0}]:
   with self.assertRaises(ValueError):checker.canonical_tuple(value)

 def test_complete_decision_preserves_origin(self):
  for origin in ['CHECKED_MODEL','FAST_LOCAL_REQUEST']:
   rows=checker.decisions(self.record(origin=origin),self.gold());self.assertTrue(rows[0]['complete']);self.assertEqual(rows[0]['origin'],origin)

 def test_wrong_slots_are_not_complete(self):
  rows=checker.decisions(self.record(seconds=31),self.gold());self.assertFalse(rows[0]['complete'])

 def test_frame_inventory_origin_and_canonical_consistency(self):
  for value in [self.record(kind='ALARM'),self.record(origin='UNKNOWN'),self.record(origin='MODEL'),
                self.record().replace('one','two',1),self.record()+self.record(),self.record().replace('\tCHECKED_MODEL','')]:
   with self.assertRaises(ValueError):checker.decisions(value,self.gold())

 def test_duplicate_and_nonfinite_json(self):
  for value in ['{"intent":"unknown","intent":"timer"}','{"value":NaN}']:
   with self.assertRaises(ValueError):checker.strict(value)

 def test_private_boundary_and_exclusive_writes(self):
  with self.assertRaises(ValueError):checker.private(checker.TASK/'public.json')
  with self.assertRaises(ValueError):checker.private(checker.ROOT/'prototype/unit-regression/build/output.json')
  with tempfile.TemporaryDirectory(dir=checker.BUILD) as folder:
   p=Path(folder)/'result.json';checker.write_new(p,{'done':True})
   with self.assertRaises(FileExistsError):checker.write_new(p,{'done':False})
   self.assertEqual(json.loads(p.read_text()),{'done':True})

 def test_invalid_freeze_stops_before_any_candidate_source_read(self):
  with self.assertRaises(ValueError):checker.evaluate('not-a-commit',checker.BUILD/'unused')

if __name__=='__main__':
 checker.BUILD.mkdir(exist_ok=True)
 unittest.main()
