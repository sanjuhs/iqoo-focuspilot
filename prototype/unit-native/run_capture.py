"""Unpromoted host unit-output research; reuses the pinned native binary."""
import argparse
import base64
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BUILD = TASK / 'build'
CORE = ROOT / 'prototype/qwen-balanced-native'
BINARY = CORE / 'build/capture'
COMPILED = CORE / 'build/capture-build.json'
MODEL = ROOT / 'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
MODEL_SHA = '57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
BINARY_SHA = '32a6869b29816216654640127c9ab6d2e4d5c1763aa729645c36f27563186ce1'
CPP_SHA = 'a63ef223c451944f13d5e2940bea0377225f0f15a5573011e24c935efcebf8da'
COMPILED_SHA = 'e7ff11371aa63584c8f90e3c7c59a73033ddcfb09292a02a1b4c35a680a49631'
LIBS = {
 '/opt/homebrew/opt/llama.cpp/lib/libllama.0.dylib': '2a094b66943b6f6da3eb39cf7360ebd2cef50a864f184bd58a21508ad4ed8668',
 '/opt/homebrew/opt/ggml/lib/libggml.0.dylib': '1c131c59813cb27b2bed388fa27db8647416e74b9fbd5384c22db60db32617d3',
 '/opt/homebrew/opt/ggml/lib/libggml-base.0.dylib': 'c0dcbb8438e3f1ccd40f3a49246c1ea341d813c273bb599448c9766fb2392b56',
}
SETTINGS = {'context':1024, 'batch':1024, 'ubatch':256, 'threads':4,
 'maximum':128, 'capture':False, 'adapter':False, 'sampler':'GBNF then greedy',
 'memory':'fresh context per request plus recurrent and KV clear', 'cpu_only':True}


def sha(path):
 with Path(path).open('rb') as f:
  return hashlib.file_digest(f, 'sha256').hexdigest()


def unique(pairs):
 out = {}
 for key, value in pairs:
  if key in out: raise ValueError('Duplicate JSON key')
  out[key] = value
 return out


def strict_json(text):
 def finite_float(value):
  number = float(value)
  if not math.isfinite(number): raise ValueError('Nonfinite JSON number')
  return number
 return json.loads(text, object_pairs_hook=unique,
  parse_float=finite_float,
  parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def write_new(path, value):
 with Path(path).open('x') as f:
  json.dump(value, f, indent=2); f.write('\n')


def private_path(path):
 path = Path(path).resolve()
 if BUILD.resolve() not in path.parents:
  raise ValueError('Outputs must remain in ignored unit-native/build/')
 return path


def prompts(path):
 path = Path(path)
 if not path.is_file() or not 0 < path.stat().st_size <= 1024*1024:
  raise ValueError('Bounded prompts TSV required')
 raw = path.read_bytes()
 text = raw.decode('ascii')
 if not text.endswith('\n') or '\r' in text:
  raise ValueError('Literal LF rows and terminal newline required')
 rows = []; ids = set()
 for line in text.split('\n')[:-1]:
  fields = line.split('\t')
  if len(fields) != 2: raise ValueError('Two TSV columns required')
  ident, encoded = fields
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', ident) or ident in ids:
   raise ValueError('Unique bounded IDs required')
  if not encoded or len(encoded) > 16000:
   raise ValueError('Bounded base64 required')
  value = base64.b64decode(encoded, validate=True)
  if base64.b64encode(value).decode() != encoded or not 0 < len(value) <= 12000:
   raise ValueError('Canonical bounded base64 required')
  decoded = value.decode('utf-8')
  if '\0' in decoded: raise ValueError('NUL prompt refused')
  ids.add(ident); rows.append((ident, decoded))
 if not 1 <= len(rows) <= 200: raise ValueError('1-200 prompt rows required')
 return rows


def grammar(path):
 path = Path(path)
 if not path.is_file() or not 0 < path.stat().st_size <= 4096:
  raise ValueError('GBNF must contain 1-4096 bytes')
 value = path.read_bytes().decode('utf-8')
 if '\0' in value or not re.search(r'^root\s*::=', value, re.M):
  raise ValueError('NUL-free grammar with root rule required')
 return value


def runtime_guard():
 if sha(COMPILED) != COMPILED_SHA:
  raise ValueError('Pinned original compilation record changed')
 compiled = strict_json(COMPILED.read_text())
 if compiled.get('source_sha256') != CPP_SHA or compiled.get('binary_sha256') != BINARY_SHA:
  raise ValueError('Pinned original native compilation required')
 if sha(CORE/'capture.cpp') != CPP_SHA or sha(BINARY) != BINARY_SHA:
  raise ValueError('Pinned original native source/binary changed')
 if len(compiled.get('headers_sha256', {})) != 7:
  raise ValueError('Seven original compiled headers required')
 files = {str(CORE/'capture.cpp'):CPP_SHA, str(BINARY):BINARY_SHA,
  str(COMPILED):sha(COMPILED), **compiled['headers_sha256'], **LIBS}
 for path, digest in files.items():
  if sha(path) != digest: raise ValueError('Pinned native dependency changed: '+Path(path).name)
 exports = subprocess.check_output(['nm','-gU',next(iter(LIBS))], text=True, timeout=30)
 names = {line.split()[-1] for line in exports.splitlines() if line.split()}
 for symbol in ['llama_memory_clear','llama_sampler_init_grammar',
                'llama_sampler_init_greedy','llama_vocab_is_eog']:
  if '_'+symbol not in names: raise ValueError('Required actual runtime symbol absent')
 return files


def budget():
 sys.path.insert(0, str(ROOT/'scripts'))
 from package_bundled_apk import project_bytes
 if sum(p.stat().st_size for p in TASK.rglob('*') if p.is_file()) > 2_000_000:
  raise ValueError('Structured wrapper exceeds 2 MB allowance')
 if project_bytes(ROOT) + 3_000_000 > 15_000_000_000:
  raise ValueError('3 MB output reserve exceeds project cap')


def prepare(prompt_path, grammar_path, out, pins):
 budget(); files = runtime_guard()
 prompt_path = Path(prompt_path).resolve(); grammar_path = Path(grammar_path).resolve()
 rows = prompts(prompt_path); grammar(grammar_path)
 # Pure native input parser exits before backend/model initialization.
 parsed = subprocess.check_output([str(BINARY),'--check-input',str(prompt_path)], text=True, timeout=30)
 if parsed != str(len(rows))+'\n': raise ValueError('Native/Python prompt inventory mismatch')
 out = private_path(out)
 if out.exists(): raise ValueError('Existing lock directory preserved')
 for path in [prompt_path, grammar_path, TASK/'run_capture.py', TASK/'test_capture.py', TASK/'README.md', TASK/'.gitignore', *map(Path, pins)]:
  path = path.resolve(); files[str(path)] = sha(path)
 out.mkdir(parents=True, exist_ok=False)
 lock = {'schema':'focuspilot.unit_native_lock.v1', 'settings':SETTINGS,
  'ids':[r[0] for r in rows], 'rows':len(rows), 'prompts':str(prompt_path),
  'grammar':str(grammar_path), 'binary':str(BINARY), 'files_sha256':files,
  'model':str(MODEL), 'model_sha256':MODEL_SHA,
  'scope':'Development host C API structured-output capture; unchanged base weights, no adapter, no phone/tool action. Prompt/grammar are research inputs, not the selected app prompt.'}
 write_new(out/'lock.json', lock)
 return out/'lock.json'


def verify_lock(lock, source_commit):
 if lock.get('schema') != 'focuspilot.unit_native_lock.v1' or lock.get('settings') != SETTINGS:
  raise ValueError('Exact unit capture settings required')
 if lock.get('binary') != str(BINARY) or lock.get('model') != str(MODEL) or lock.get('model_sha256') != MODEL_SHA:
  raise ValueError('Only the pinned existing binary/base model is supported')
 if not re.fullmatch(r'[a-f0-9]{40}', source_commit): raise ValueError('Full source commit required')
 if subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True, timeout=30).strip() != source_commit:
  raise ValueError('Expected current frozen source commit required')
 required = {*runtime_guard(), str(TASK/'run_capture.py'), str(TASK/'test_capture.py'),
  str(TASK/'README.md'), str(TASK/'.gitignore'), lock['prompts'], lock['grammar']}
 if not required <= set(lock['files_sha256']): raise ValueError('Required lock bindings missing')
 for path, digest in lock['files_sha256'].items():
  if sha(path) != digest: raise ValueError('Locked file changed: '+Path(path).name)
  path = Path(path)
  if ROOT in path.parents:
   relative = str(path.relative_to(ROOT))
   tracked = subprocess.run(['git','ls-files','--error-unmatch','--',relative], cwd=ROOT, capture_output=True, timeout=30).returncode == 0
   if tracked and hashlib.sha256(subprocess.check_output(['git','show',source_commit+':'+relative],cwd=ROOT,timeout=30)).hexdigest() != digest:
    raise ValueError('Tracked bytes differ from frozen commit')
 if sha(MODEL) != MODEL_SHA: raise ValueError('Pinned original model changed')
 rows = prompts(lock['prompts']); grammar(lock['grammar'])
 if [r[0] for r in rows] != lock['ids'] or len(rows) != lock['rows']:
  raise ValueError('Locked request inventory differs')


def validate_capture(text, ids):
 if not text.endswith('\n'): raise ValueError('Complete output terminal newline required')
 lines = text.splitlines()
 if len(lines) != len(ids)+1 or len(set(ids)) != len(ids):
  raise ValueError('No partial, duplicate or extra capture scoring')
 load = strict_json(lines[0])
 if set(load) != {'phase','load_ms','adapter'} or load['phase'] != 'load' or load['adapter'] is not False:
  raise ValueError('Base-only load record required')
 if type(load['load_ms']) not in (int,float) or not math.isfinite(load['load_ms']) or load['load_ms'] < 0:
  raise ValueError('Finite load time required')
 records = []
 for ident, line in zip(ids, lines[1:]):
  row = strict_json(line)
  if set(row) != {'id','text','metrics'} or row['id'] != ident or type(row['text']) is not str:
   raise ValueError('Exact ordered record inventory required')
  if not isinstance(strict_json(row['text']), dict): raise ValueError('Strict generated JSON object required')
  m = row['metrics']
  if set(m) != {'prompt_tokens','generated_tokens','prefill_ms','decode_ms','total_ms','context_setup_ms','reached_eos','cpu_only','capture_enabled'}:
   raise ValueError('Exact metric inventory required')
  if m['reached_eos'] is not True or m['cpu_only'] is not True or m['capture_enabled'] is not False:
   raise ValueError('Actual EOS, CPU and disabled capture required')
  for key in ['prompt_tokens','generated_tokens']:
   if type(m[key]) is not int or m[key] < 1: raise ValueError('Positive integer token counts required')
  # Core samples at most 128 times; EOS must occupy one of those samples.
  if m['generated_tokens'] >= 128 or m['prompt_tokens']+128 > 1024:
   raise ValueError('Native token bounds exceeded')
  for key in ['prefill_ms','decode_ms','total_ms','context_setup_ms']:
   if type(m[key]) not in (int,float) or not math.isfinite(m[key]) or m[key] < 0:
    raise ValueError('Finite nonnegative timings required')
  records.append(row)
 return load, records


def claim_attempt(lock_path, out, source_commit):
 lock_path = private_path(lock_path); out = private_path(out)
 if out.exists(): raise ValueError('Existing attempt preserved; no retry/overwrite')
 write_new(lock_path.parent/'capture-claim.json', {'source_commit':source_commit,
  'lock_sha256':sha(lock_path), 'out':str(out)})
 out.mkdir(parents=True, exist_ok=False)
 return out


def capture(lock_path, out, source_commit):
 lock_path = private_path(lock_path); lock = strict_json(lock_path.read_text())
 verify_lock(lock, source_commit); budget()
 out = claim_attempt(lock_path, out, source_commit)
 command = [lock['binary'], str(MODEL), '-', lock['prompts'], lock['grammar']]
 record = {'schema':'focuspilot.unit_native_process.v1', 'source_commit':source_commit,
  'lock_sha256':sha(lock_path), 'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'command':command, 'adapter':False, 'model_sha256':MODEL_SHA, 'pid':None, 'scope':lock['scope']}
 write_new(out/'initial.json', record)
 print(json.dumps({'phase':'unit_native_starting','rows':lock['rows']}), flush=True)
 began = time.monotonic(); job = None; failure = None; exit_code = None; timed_out = False
 with (out/'raw.jsonl').open('x') as stdout, (out/'stderr.log').open('x') as stderr:
  try:
   job = subprocess.Popen(command, stdout=stdout, stderr=stderr)
   record['pid'] = job.pid; write_new(out/'started.json', record)
   print(json.dumps({'phase':'unit_native_child_started','pid':job.pid,'rows':lock['rows']}), flush=True)
   exit_code = job.wait(timeout=240)
  except subprocess.TimeoutExpired:
   job.kill(); exit_code = job.wait(); timed_out = True
  except BaseException as problem:
   if job is not None and job.poll() is None: job.kill(); job.wait()
   failure = problem
 record.update(exit_code=exit_code, timed_out=timed_out, seconds=time.monotonic()-began,
  raw_sha256=sha(out/'raw.jsonl'), stderr_sha256=sha(out/'stderr.log'),
  initial_sha256=sha(out/'initial.json'),
  started_sha256=sha(out/'started.json') if (out/'started.json').exists() else None,
  error_type=type(failure).__name__ if failure else None)
 try: verify_lock(lock, source_commit)
 except BaseException as problem:
  if failure is None: failure = problem
  record['postflight_error_type'] = type(problem).__name__
 write_new(out/'process.json', record)
 if failure: raise failure
 if timed_out or exit_code != 0: raise ValueError('Incomplete native process; no retry or partial score')
 load, rows = validate_capture((out/'raw.jsonl').read_text(), lock['ids'])
 summary = {'schema':'focuspilot.unit_native_capture.v1', 'rows':len(rows),
  'strict_json_objects_and_actual_eos':len(rows), 'load_ms':load['load_ms'],
  'raw_sha256':record['raw_sha256'], 'process_sha256':sha(out/'process.json'),
  'stderr_sha256':record['stderr_sha256'], 'lock_sha256':record['lock_sha256'],
  'source_commit':source_commit, 'model_sha256':MODEL_SHA, 'adapter':False,
  'scope':lock['scope'], 'promoted':False}
 write_new(out/'capture-summary.json', summary)
 print(json.dumps({'phase':'unit_native_complete','rows':len(rows)}), flush=True)
 return summary


def main():
 p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='mode',required=True)
 sub.add_parser('check-runtime')
 a = sub.add_parser('prepare'); a.add_argument('--prompts',required=True); a.add_argument('--grammar',required=True); a.add_argument('--out',required=True); a.add_argument('--pin',action='append',default=[])
 a = sub.add_parser('capture'); a.add_argument('--lock',required=True); a.add_argument('--out',required=True); a.add_argument('--source-commit',required=True)
 a = p.parse_args()
 if a.mode == 'check-runtime': print(json.dumps({'runtime_files_sha256':runtime_guard(),'model_loaded':False}))
 elif a.mode == 'prepare': print(prepare(a.prompts,a.grammar,a.out,a.pin))
 else: capture(a.lock,a.out,a.source_commit)

if __name__ == '__main__': main()
