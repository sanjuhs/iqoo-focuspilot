import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TASK=Path(__file__).resolve().parent
sys.path.insert(0,str(TASK))
import run_capture as runner
import score


class BoundaryTests(unittest.TestCase):
 def make_record(self,ident='one',intent='pause_focus'):
  return {'id':ident,'text':json.dumps({'intent':intent},separators=(',',':')),
   'metrics':{'prompt_tokens':180,'generated_tokens':7,'prefill_ms':2.0,'decode_ms':1.0,'total_ms':3.0,
   'context_setup_ms':0.5,'reached_eos':True,'cpu_only':True,'capture_enabled':False}}
 def captured(self,record=None):
  return json.dumps({'phase':'load','load_ms':4,'adapter':False})+'\n'+json.dumps(record or self.make_record())+'\n'
 def test_complete_canonical_real_eos(self):
  load,rows=runner.validate_capture(self.captured(),['one'],False);self.assertEqual(len(rows),1)
 def test_partial_missing_and_extra_denominator(self):
  with self.assertRaises(ValueError):runner.validate_capture(self.captured(),['one','two'],False)
  with self.assertRaises(ValueError):runner.validate_capture(self.captured()+json.dumps(self.make_record())+'\n',['one'],False)
 def test_order_and_duplicate_ids(self):
  text=self.captured()+json.dumps(self.make_record('two'))+'\n'
  with self.assertRaises(ValueError):runner.validate_capture(text,['two','one'],False)
  with self.assertRaises(ValueError):runner.validate_capture(text,['one','one'],False)
 def test_invented_eos_cpu_capture(self):
  for key,value in [('reached_eos',False),('reached_eos',1),('cpu_only',False),('capture_enabled',True)]:
   row=self.make_record();row['metrics'][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):runner.validate_capture(self.captured(row),['one'],False)
 def test_canonical_shape_and_duplicate_keys(self):
  for value in ['{"intent":"pause_focus", "x":0}','{"intent": "pause_focus"}','{"intent":"pause_focus","intent":"timer"}','{"intent":"bad"}','{"intent":[]}']:
   row=self.make_record();row['text']=value
   with self.subTest(value=value),self.assertRaises(ValueError):runner.validate_capture(self.captured(row),['one'],False)
 def test_finite_positive_token_and_bounds(self):
  for key,value in [('total_ms',float('nan')),('prefill_ms',True),('context_setup_ms',-1),('generated_tokens',0),('generated_tokens',129),('prompt_tokens',897),('prompt_tokens',True)]:
   row=self.make_record();row['metrics'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):runner.validate_capture(self.captured(row),['one'],False)
 def test_adapter_load_identity(self):
  with self.assertRaises(ValueError):runner.validate_capture(self.captured(),['one'],True)
 def test_metric_inventory(self):
  row=self.make_record();row['metrics'].pop('context_setup_ms')
  with self.assertRaises(ValueError):runner.validate_capture(self.captured(row),['one'],False)
 def test_duplicate_and_nonfinite_json(self):
  for text in ['{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}']:
   with self.assertRaises(ValueError):runner.strict_json(text)
 def test_exclusive_immutable_output(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'one.json';runner.write_new(p,{'done':True})
   with self.assertRaises(FileExistsError):runner.write_new(p,{'done':False})
   self.assertEqual(json.loads(p.read_text()),{'done':True})
 def test_raw_private_output_boundary(self):
  with self.assertRaises(ValueError):runner.private_path(TASK/'public.json')
  self.assertEqual(runner.private_path(runner.BUILD/'one/raw.jsonl'),(runner.BUILD/'one/raw.jsonl').resolve())
 def test_requests_utf16_bound_and_reserved_controls(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'requests.tsv'
   for raw in ['one\tStop focus\n','one\t'+('é'*500)+'\n']:
    p.write_text(raw);self.assertEqual(len(runner.requests(p)),1)
   for raw in ['one\tStop focus','one\t\n','one\tStop focus\none\tStart focus\n','one\t'+('😀'*251)+'\n','one\tStop\x00focus\n','one\tStop focus\r\n','one\tStop\u2028focus\n']:
    p.write_text(raw)
    with self.subTest(raw=repr(raw[:30])),self.assertRaises(ValueError):runner.requests(p)
 def test_small_gguf_adapter_uses_hash_not_legacy_header_size(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'adapter.gguf'
   for size in (221888,221920):
    p.write_bytes(b'GGUF'+b'\0'*(size-4));self.assertEqual(runner.validate_adapter(p,runner.sha(p)),p.resolve())
   with self.assertRaises(ValueError):runner.validate_adapter(p,'0'*64)
   p.write_bytes(b'BAD!'+b'\0'*50)
   with self.assertRaises(ValueError):runner.validate_adapter(p,runner.sha(p))
   p.write_bytes(b'GGUF'+b'\0'*300000)
   with self.assertRaises(ValueError):runner.validate_adapter(p,runner.sha(p))
 def test_same_lock_arm_claim_prevents_output_alias_retry(self):
  with tempfile.TemporaryDirectory() as folder:
   old_build=runner.BUILD
   with patch.object(runner,'BUILD',Path(folder)):
    lock=Path(folder)/'lock.json';lock.write_text('{}')
    first=Path(folder)/'first';second=Path(folder)/'second'
    runner.claim_attempt(lock,first,'frozen',None)
    with self.assertRaises(FileExistsError):runner.claim_attempt(lock,second,'frozen',None)
    self.assertFalse(second.exists())
    runner.claim_attempt(lock,Path(folder)/'adapter','frozen','a'*64)
    with self.assertRaises(FileExistsError):runner.claim_attempt(lock,Path(folder)/'adapter-alias','frozen','b'*64)
 def test_native_input_preflight_canonical_encoding(self):
  binary=runner.BUILD/'capture'
  if not binary.exists():self.skipTest('Compile-only binary needed for native parser boundary test')
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'prompts.tsv'
   p.write_text('one\tYQ==\n');r=subprocess.run([str(binary),'--check-input',str(p)],capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertEqual(r.stdout,'1\n')
   for raw in ['one\tYQ==','one\tYQ=\n','one\tYR==\n','one\tYQ==\none\tYQ==\n','one\tAA==\n','bad id\tYQ==\n','one\tYQ==\textra\n']:
    p.write_text(raw);r=subprocess.run([str(binary),'--check-input',str(p)],capture_output=True,text=True)
    with self.subTest(raw=raw):self.assertEqual(r.returncode,2)


class ScoringTests(unittest.TestCase):
 def rows(self):
  return [{'id':'one','utterance':'Pause my focus','intent':'pause_focus','oracle_intent':'pause_focus','expected_kind':'PAUSE_FOCUS','hour':0,'minute':0,'seconds':0,'family':'pause','hard_tags':['pause']},
   {'id':'two','utterance':'Timer for 30 seconds','intent':'timer','oracle_intent':'timer','expected_kind':'TIMER','hour':0,'minute':0,'seconds':30,'family':'timer','hard_tags':['seconds']},
   {'id':'three','utterance':'Delete my files','intent':'unknown','oracle_intent':'unknown','expected_kind':'UNKNOWN','hour':0,'minute':0,'seconds':0,'family':'delete','hard_tags':['destructive']}]
 def props(self):
  return {'one':{'kind':'PAUSE_FOCUS','hour':0,'minute':0,'seconds':0},'two':{'kind':'TIMER','hour':0,'minute':0,'seconds':30},'three':{'kind':'UNKNOWN','hour':0,'minute':0,'seconds':0}}
 def test_semantic_unknown_distinguished_from_gate_refusal(self):
  counts,_=score.summarize(self.rows(),{'one':'pause_focus','two':'timer','three':'start_focus'},self.props())
  self.assertEqual(counts['unknown_refused_by_gate'],1);self.assertEqual(counts['unknown_model_abstentions'],0);self.assertEqual(counts['supported_complete_proposals'],2)
 def test_wrong_slots_count_as_wrong_accept(self):
  props=self.props();props['two']['seconds']=25
  counts,_=score.summarize(self.rows(),{'one':'pause_focus','two':'timer','three':'unknown'},props)
  self.assertEqual(counts['supported_complete_proposals'],1);self.assertEqual(counts['wrong_accepts'],1)
 def test_oracle_gold_not_gate_derived(self):
  props=self.props();props['one']['kind']='UNKNOWN'
  counts,_=score.summarize(self.rows(),{'one':'pause_focus','two':'timer','three':'unknown'},props)
  self.assertEqual(counts['supported_semantic_correct'],2);self.assertEqual(counts['supported_false_abstentions'],1)
 def test_no_paired_loss_hidden_by_gain(self):
  _,old=score.summarize(self.rows(),{'one':'pause_focus','two':'start_focus','three':'unknown'},dict(self.props(),two={'kind':'UNKNOWN','hour':0,'minute':0,'seconds':0}))
  _,new=score.summarize(self.rows(),{'one':'start_focus','two':'timer','three':'unknown'},dict(self.props(),one={'kind':'UNKNOWN','hour':0,'minute':0,'seconds':0}))
  paired,_=score.paired(old,new)
  self.assertEqual(paired['supported_rows']['gate_gain'],1);self.assertEqual(paired['supported_rows']['gate_loss'],1)
  self.assertEqual(paired['per_intent']['pause_focus']['gate_loss'],1)
 def test_no_missing_gold_or_reordered_score(self):
  with self.assertRaises(ValueError):score.summarize(self.rows(),{'two':'timer','one':'pause_focus','three':'unknown'},self.props())
 def test_gold_locked_request_inventory(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'data.jsonl';p.write_text('\n'.join(json.dumps(r) for r in self.rows())+'\n')
   t=Path(folder)/'req.tsv';t.write_text(''.join(r['id']+'\t'+r['utterance']+'\n' for r in self.rows()))
   lock={'requests':str(t),'files_sha256':{str(p.resolve()):runner.sha(p)}}
   self.assertEqual(len(score.read_rows(p,lock)),3)
   p.write_text(p.read_text()+'\n')
   with self.assertRaises(ValueError):score.read_rows(p,lock)
if __name__=='__main__':unittest.main()
