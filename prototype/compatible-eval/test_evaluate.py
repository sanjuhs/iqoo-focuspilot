"""Source-only scoring boundaries; no corpus reads, gates or inference."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.dont_write_bytecode=True
TASK=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('compatible_evaluate_tests',TASK/'evaluate.py')
ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)


def row(ident,gold):
 return {'id':ident,'family':'fixture_'+ident,'expected':gold}


def proposal(value,origin=None):
 accepted=value['intent']!='unknown'
 return {'proposal':value,'accepted':accepted,
  'origin':origin or ('CHECKED_MODEL' if accepted else 'UNKNOWN'),'reason':'source-only fixture'}


class Boundaries(unittest.TestCase):
 def test_shapes_and_boolean_slots(self):
  valid=[{'intent':'start_focus','duration_seconds':0},{'intent':'timer','duration_seconds':7200},
   {'intent':'alarm','hour':23,'minute':59},{'intent':'open_app','app':'clock'},
   {'intent':'pause_focus'},{'intent':'explain'},{'intent':'unknown'}]
  for value in valid:self.assertEqual(ev.canonical(value),value)
  for value in [{'intent':'timer','duration_seconds':True},{'intent':'timer','duration_seconds':0},
   {'intent':'start_focus','duration_seconds':7201},{'intent':'alarm','hour':24,'minute':0},
   {'intent':'unknown','app':'clock'},{'intent':'open_app','app':'instagram'}]:
   with self.subTest(value=value),self.assertRaises(ValueError):ev.canonical(value)

 def test_raw_quantity_is_distinct_from_canonical_seconds(self):
  a={'intent':'timer','amount':2,'unit':'minutes'}
  b={'intent':'timer','amount':120,'unit':'seconds'}
  self.assertNotEqual(a,b);self.assertEqual(ev.raw_canonical(a),ev.raw_canonical(b))
  self.assertEqual(ev.raw_canonical({'intent':'start_focus','amount':0,'unit':'none'}),
   {'intent':'start_focus','duration_seconds':0})
  for value in [{'intent':'timer','amount':0,'unit':'none'},
   {'intent':'timer','amount':3,'unit':'hours'},
   {'intent':'start_focus','amount':True,'unit':'seconds'}]:
   with self.assertRaises(ValueError):ev.raw_canonical(value)

 def test_oracle_order_independent_of_sorted_author_keys(self):
  values=[({'unit':'minutes','intent':'start_focus','amount':2},'{"intent":"start_focus","amount":2,"unit":"minutes"}'),
   ({'unit':'none','intent':'start_focus','amount':0},'{"intent":"start_focus","amount":0,"unit":"none"}'),
   ({'unit':'seconds','intent':'timer','amount':25},'{"intent":"timer","amount":25,"unit":"seconds"}'),
   ({'minute':30,'intent':'alarm','hour':8},'{"intent":"alarm","hour":8,"minute":30}'),
   ({'app':'clock','intent':'open_app'},'{"intent":"open_app","app":"clock"}'),
   ({'intent':'pause_focus'},'{"intent":"pause_focus"}'),
   ({'intent':'explain'},'{"intent":"explain"}'),
   ({'intent':'unknown'},'{"intent":"unknown"}')]
  for value,want in values:
   sorted_value=json.loads(json.dumps(value,sort_keys=True))
   self.assertEqual(ev.ordered_unit_response(sorted_value),want)

 def test_full_slots_and_wrong_accept_not_intent_only(self):
  rows=[row('clock',{'intent':'alarm','hour':7,'minute':30}),row('u',{'intent':'unknown'})]
  raw={'clock':{'intent':'alarm'},'u':{'intent':'unknown'}}
  proposals={'clock':proposal({'intent':'alarm','hour':7,'minute':31}),
   'u':proposal({'intent':'unknown'})}
  summary,details=ev.summarize(rows,raw,proposals)
  self.assertEqual(summary['supported_complete'],0)
  self.assertEqual(summary['wrong_accepts'],1)
  self.assertEqual(summary['raw_intent_correct'],2)
  self.assertEqual(summary['unknown_validator_refusals'],1)
  self.assertTrue(details[0]['wrong_accept'])

 def test_fast_local_has_separate_model_accuracy(self):
  rows=[row('s',{'intent':'start_focus','duration_seconds':60})]
  raw={'s':{'intent':'unknown'}}
  summary,_=ev.summarize(rows,raw,{'s':proposal(rows[0]['expected'],'FAST_LOCAL_REQUEST')})
  self.assertEqual(summary['supported_complete'],1)
  self.assertEqual(summary['raw_intent_correct'],0)
  self.assertEqual(summary['origin_counts']['FAST_LOCAL_REQUEST'],1)

 def test_unknown_false_accept_and_acceptance_consistency(self):
  rows=[row('u',{'intent':'unknown'})];raw={'u':{'intent':'unknown'}}
  summary,_=ev.summarize(rows,raw,{'u':proposal({'intent':'explain'})})
  self.assertEqual(summary['wrong_accepts'],1)
  self.assertEqual(summary['unknown_validator_refusals'],0)
  bad=proposal({'intent':'unknown'});bad['accepted']=True
  with self.assertRaises(ValueError):ev.summarize(rows,raw,{'u':bad})

 def test_paired_full_slot_loss_and_raw_semantic_gain(self):
  rows=[row('a',{'intent':'alarm','hour':8,'minute':0}),row('u',{'intent':'unknown'})]
  a_raw={'a':{'intent':'timer'},'u':{'intent':'unknown'}}
  b_raw={'a':{'intent':'alarm'},'u':{'intent':'unknown'}}
  _,a=ev.summarize(rows,a_raw,{'a':proposal(rows[0]['expected']),'u':proposal(rows[1]['expected'])})
  _,b=ev.summarize(rows,b_raw,{'a':proposal({'intent':'alarm','hour':8,'minute':1}),'u':proposal(rows[1]['expected'])})
  complete,_=ev.paired(a,b);semantic,_=ev.paired(a,b,semantic=True)
  self.assertEqual((complete['supported_gain'],complete['supported_loss']),(0,1))
  self.assertEqual((semantic['supported_gain'],semantic['supported_loss']),(1,0))
  self.assertEqual(semantic['same_intent_all_rows'],1)
  self.assertEqual(complete['per_supported_class']['alarm']['loss'],1)
  with self.assertRaises(ValueError):ev.paired(a,list(reversed(b)))
  different=copy.deepcopy(b);different[0]['gold']['minute']=2
  with self.assertRaises(ValueError):ev.paired(a,different)

 def test_inventory_cannot_omit_duplicate_or_reorder(self):
  rows=[row('a',{'intent':'unknown'}),row('b',{'intent':'unknown'})]
  raw={'b':{'intent':'unknown'},'a':{'intent':'unknown'}}
  with self.assertRaises(ValueError):ev.summarize(rows,raw,{k:proposal(v) for k,v in raw.items()})

 def test_serial_actual_process_time(self):
  a={'started_utc':'2026-10-03T00:00:00+00:00','seconds':2.5,'pid':1}
  b={'started_utc':'2026-10-03T00:00:03+00:00','seconds':1,'pid':2}
  ev.serial_processes(a,b)
  for change in [{'started_utc':'2026-10-03T00:00:02+00:00'},
   {'pid':1},{'seconds':float('nan')},{'seconds':True},
   {'started_utc':'2026-10-03T00:00:03'}]:
   with self.subTest(change=change),self.assertRaises(ValueError):ev.serial_processes(a,{**b,**change})

 def test_protocol_thresholds_independently_block(self):
  protocol=json.loads((TASK/'protocol.json').read_text())
  history={'prior_preserved':80,'prior_regressions':0,'unknown_false_accepts':0,
   'supported_wrong_route_false_accepts':0,'supported_oracle_wrong_accepts':0}
  base={'wrong_accepts':0,'unknown_validator_refusals':50,'supported_complete':10,
   'per_class':{i:{'complete_correct':1} for i in ev.INTENTS}}
  pipeline=copy.deepcopy(base);pipeline['per_class']['start_focus']['complete_correct']=4
  arms={'baseline':base,'checked_model':copy.deepcopy(base),'product_pipeline':pipeline,
   'baseline_oracle':{'supported_complete':30},'candidate_oracle':{'supported_complete':30}}
  pair={'supported_gain':6,'supported_loss':0}
  self.assertTrue(all(ev.qualify(protocol,history,arms,pair).values()))
  cases=[('pipeline_net_gain',{'supported_gain':5,'supported_loss':0},None),
   ('pipeline_losses',{'supported_gain':7,'supported_loss':1},None)]
  for key,value,_ in cases:self.assertFalse(ev.qualify(protocol,history,arms,value)[key])
  altered=copy.deepcopy(arms);altered['checked_model']['wrong_accepts']=1
  self.assertFalse(ev.qualify(protocol,history,altered,pair)['checked_wrong_accepts'])
  altered=copy.deepcopy(arms);altered['product_pipeline']['per_class']['timer']['complete_correct']=0
  self.assertFalse(ev.qualify(protocol,history,altered,pair)['pipeline_per_class'])
  altered=copy.deepcopy(arms);altered['candidate_oracle']['supported_complete']=29
  self.assertFalse(ev.qualify(protocol,history,altered,pair)['oracle_coverage'])

 def test_private_path_and_native_reserve(self):
  self.assertEqual(ev.private(TASK/'build/test/a'),TASK/'build/test/a')
  for path in [TASK,TASK/'build',TASK/'build/../../external']:
   with self.assertRaises(ValueError):ev.private(path)
  folder=MagicMock();entry=MagicMock();entry.is_file.return_value=True
  entry.stat.return_value.st_size=251120;folder.rglob.return_value=[entry]
  with patch.object(ev.driver,'TASK',folder):
   self.assertLess(ev.native_budget({'/source':'a'*64})['two_arm_reserved_bytes']+251120,2_000_000)
   entry.stat.return_value.st_size=1_000_000
   with self.assertRaises(ValueError):ev.native_budget({'/source':'a'*64})

 def test_strict_json_duplicate_and_nonfinite(self):
  for text in ['{"intent":"unknown","intent":"timer"}','{"seconds":NaN}']:
   with self.assertRaises(ValueError):ev.driver.strict_json(text)


if __name__=='__main__':unittest.main()
