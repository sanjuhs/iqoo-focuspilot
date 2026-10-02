"""Boundary checks only: no model load or generated development requests."""
import base64
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_capture as runner


class BoundaryTests(unittest.TestCase):
 def row(self):
  return {'id':'one', 'text':'{"kind":"TIMER","seconds":30}',
   'metrics':{'prompt_tokens':300,'generated_tokens':15,'prefill_ms':2.0,
    'decode_ms':3.0,'total_ms':5.0,'context_setup_ms':1.0,'reached_eos':True,
    'cpu_only':True,'capture_enabled':False}}

 def raw(self,row=None):
  return json.dumps({'phase':'load','load_ms':10,'adapter':False})+'\n'+json.dumps(row or self.row())+'\n'

 def test_generic_object_keeps_exact_text_and_does_not_score_schema(self):
  for text in ['{"kind":"TIMER", "seconds":30}', '{"intent":"unknown"}', '{"unsupported":1}', '{}']:
   row=self.row();row['text']=text
   self.assertEqual(runner.validate_capture(self.raw(row),['one'])[1][0]['text'],text)

 def test_duplicate_keys_invalid_numbers_and_non_object_refused(self):
  for text in ['{"x":1,"x":2}','{"x":NaN}','{"x":1e999}','[]','null','"timer"','not JSON']:
   row=self.row();row['text']=text
   with self.subTest(text=text),self.assertRaises(ValueError):runner.validate_capture(self.raw(row),['one'])

 def test_full_denominator_order_and_terminal_newline(self):
  for raw,ids in [(self.raw(),['two']), (self.raw(),['one','two']),
                  (self.raw()+json.dumps(self.row())+'\n',['one']),
                  (self.raw().rstrip(),['one']), (self.raw(),['one','one'])]:
   with self.assertRaises(ValueError):runner.validate_capture(raw,ids)

 def test_eos_cpu_capture_are_literal_booleans(self):
  for key,value in [('reached_eos',False),('reached_eos',1),('cpu_only',False),('capture_enabled',True)]:
   row=self.row();row['metrics'][key]=value
   with self.assertRaises(ValueError):runner.validate_capture(self.raw(row),['one'])

 def test_native_strict_token_and_timing_bounds(self):
  for key,value in [('generated_tokens',128),('generated_tokens',0),('generated_tokens',True),
                   ('prompt_tokens',897),('prefill_ms',-1),('decode_ms',True),('total_ms',float('inf'))]:
   row=self.row();row['metrics'][key]=value
   with self.assertRaises(ValueError):runner.validate_capture(self.raw(row),['one'])

 def test_metric_inventory_and_adapter_refused(self):
  row=self.row();row['metrics'].pop('context_setup_ms')
  with self.assertRaises(ValueError):runner.validate_capture(self.raw(row),['one'])
  with self.assertRaises(ValueError):runner.validate_capture(self.raw().replace('"adapter": false','"adapter": true'),['one'])

 def test_prompt_encoding_parity_with_native_parser_without_load(self):
  with tempfile.TemporaryDirectory(dir=runner.BUILD) as folder:
   p=Path(folder)/'prompts.tsv'
   for prompt in ['a','\n<|im_start|>user\nhello 😀\n<|im_end|>\n','é'*6000]:
    p.write_text('one\t'+base64.b64encode(prompt.encode()).decode()+'\n')
    self.assertEqual(runner.prompts(p),[('one',prompt)])
    result=subprocess.run([str(runner.BINARY),'--check-input',str(p)],capture_output=True,text=True,timeout=30)
    self.assertEqual((result.returncode,result.stdout),(0,'1\n'))

 def test_prompt_encoding_boundaries_and_duplicate_ids(self):
  with tempfile.TemporaryDirectory(dir=runner.BUILD) as folder:
   p=Path(folder)/'prompts.tsv'
   for raw in ['one\tYQ==','one\tYR==\n','one\tYQ=\n','one\tAA==\n',
               'one\t/w==\n','bad id\tYQ==\n','one\tYQ==\none\tYQ==\n',
               'one\tYQ==\textra\n','one\tYQ==\r\n']:
    p.write_text(raw)
    with self.assertRaises(ValueError):runner.prompts(p)

 def test_grammar_root_nul_and_size(self):
  with tempfile.TemporaryDirectory(dir=runner.BUILD) as folder:
   p=Path(folder)/'grammar.gbnf';p.write_text('root ::= "{}"\n');runner.grammar(p)
   for text in ['','action ::= "{}"\n','root ::= "{}"\0','root ::= "{}"\n'+' '*4096]:
    p.write_text(text)
    with self.assertRaises(ValueError):runner.grammar(p)

 def test_private_boundary_and_exclusive_json(self):
  with self.assertRaises(ValueError):runner.private_path(runner.TASK/'public.json')
  with tempfile.TemporaryDirectory(dir=runner.BUILD) as folder:
   p=Path(folder)/'one.json';runner.write_new(p,{'done':True})
   with self.assertRaises(FileExistsError):runner.write_new(p,{'done':False})
   self.assertEqual(json.loads(p.read_text()),{'done':True})

 def test_claim_blocks_same_lock_alias_retry(self):
  with tempfile.TemporaryDirectory(dir=runner.BUILD) as folder:
   p=Path(folder);lock=p/'lock.json';lock.write_text('{}')
   runner.claim_attempt(lock,p/'first','a'*40)
   with self.assertRaises(FileExistsError):runner.claim_attempt(lock,p/'second','a'*40)
   self.assertFalse((p/'second').exists())

 def test_fixed_core_model_settings_required_before_runtime_or_model_checks(self):
  for lock in [{}, {'schema':'focuspilot.unit_native_lock.v1','settings':dict(runner.SETTINGS,adapter=True)}]:
   with patch.object(runner,'runtime_guard',side_effect=AssertionError('No runtime load expected')):
    with self.assertRaises(ValueError):runner.verify_lock(lock,'a'*40)

 def test_other_task_output_and_lock_namespaces_refused(self):
  with self.assertRaises(ValueError):runner.private_path(runner.ROOT/'prototype/structured-native/build/other/raw.jsonl')
  lock={'schema':'focuspilot.structured_native_lock.v1','settings':runner.SETTINGS}
  with patch.object(runner,'runtime_guard',side_effect=AssertionError('No runtime access expected')):
   with self.assertRaises(ValueError):runner.verify_lock(lock,'a'*40)

 def test_unit_wrapper_task_resources_stay_local_except_shared_core(self):
  self.assertEqual(runner.TASK.name,'unit-native')
  self.assertEqual(runner.BUILD,runner.TASK/'build')
  self.assertEqual(runner.CORE,runner.ROOT/'prototype/qwen-balanced-native')
  self.assertEqual(runner.BINARY_SHA,runner.sha(runner.BINARY))

if __name__ == '__main__':
 runner.BUILD.mkdir(exist_ok=True)
 unittest.main()
