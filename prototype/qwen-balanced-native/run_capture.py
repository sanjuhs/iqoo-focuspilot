"""Pinned small CPU API research capture; never executes phone tools or promotes adapters."""
import argparse
import base64
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
BUILD = TASK / 'build'
JAVA = Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin')
APP = ROOT / 'prototype/android/app/src/main/java/dev/focuspilot/prototype'
MODEL = ROOT / 'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
MODEL_SHA = '57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
JNI = ROOT / 'prototype/command-eval/build/native/libfocuspilot_local.dylib'
JNI_SHA = 'ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e'
LIBS = {
 '/opt/homebrew/opt/llama.cpp/lib/libllama.0.dylib': '2a094b66943b6f6da3eb39cf7360ebd2cef50a864f184bd58a21508ad4ed8668',
 '/opt/homebrew/opt/ggml/lib/libggml.0.dylib': '1c131c59813cb27b2bed388fa27db8647416e74b9fbd5384c22db60db32617d3',
 '/opt/homebrew/opt/ggml/lib/libggml-base.0.dylib': 'c0dcbb8438e3f1ccd40f3a49246c1ea341d813c273bb599448c9766fb2392b56',
}
HEADERS = tuple(Path('/opt/homebrew/include')/name for name in ('llama.h','ggml.h','ggml-cpu.h','ggml-backend.h','ggml-alloc.h','ggml-opt.h','gguf.h'))
SYMBOLS = ('llama_set_adapters_lora', 'llama_adapter_lora_init', 'llama_memory_clear',
           'llama_sampler_init_grammar', 'llama_sampler_init_greedy', 'llama_vocab_is_eog')
INTENTS = {'start_focus','pause_focus','alarm','timer','open_app','explain','unknown'}


def sha(path):
 with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def unique(pairs):
 out={}
 for key,value in pairs:
  if key in out: raise ValueError('Duplicate JSON key')
  out[key]=value
 return out


def strict_json(text):
 return json.loads(text,object_pairs_hook=unique,parse_constant=lambda v: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def write_new(path,value):
 with Path(path).open('x') as f: json.dump(value,f,indent=2);f.write('\n')


def private_path(path):
 path=Path(path).resolve()
 if BUILD.resolve() not in path.parents: raise ValueError('Raw outputs must stay in ignored task build/')
 return path


def requests(path):
 path=Path(path)
 if not path.is_file() or path.stat().st_size>1024*1024: raise ValueError('Bounded request file required')
 text=path.read_bytes().decode('utf-8')
 if any(c in text for c in ('\r','\u2028','\u2029')): raise ValueError('Request separators must be literal LF')
 if not text.endswith('\n'): raise ValueError('Terminal newline required')
 rows=[];ids=set()
 for line in text.splitlines():
  fields=line.split('\t')
  if len(fields)!=2: raise ValueError('Two request columns required')
  ident,request=fields
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',ident) or ident in ids: raise ValueError('Unique bounded ID required')
  if not request.strip() or len(request.encode('utf-16-le'))//2>500 or any(ord(c)<32 or ord(c) in (127,0x2028,0x2029) for c in request): raise ValueError('Invalid request')
  ids.add(ident);rows.append((ident,request))
 if not 1<=len(rows)<=200: raise ValueError('1-200 requests required')
 return rows


def runtime_guard():
 if sha(MODEL)!=MODEL_SHA or sha(JNI)!=JNI_SHA: raise ValueError('Pinned existing model/JNI changed')
 for path,digest in LIBS.items():
  if sha(path)!=digest: raise ValueError('Pinned shared runtime changed')
 text=subprocess.check_output(['nm','-gU','/opt/homebrew/opt/llama.cpp/lib/libllama.0.dylib'],text=True,timeout=30)
 exports={line.split()[-1] for line in text.splitlines() if line.split()}
 if any('_'+name not in exports for name in SYMBOLS): raise ValueError('Expected llama API exports missing')
 return {str(MODEL):MODEL_SHA,str(JNI):JNI_SHA,**LIBS}


def work_budget():
 import sys
 sys.path.insert(0,str(ROOT/'scripts'))
 from package_bundled_apk import project_bytes
 if sum(p.stat().st_size for p in TASK.rglob('*') if p.is_file())>8_000_000: raise ValueError('Task exceeds 8 MB work allowance')
 if project_bytes(ROOT)+10_000_000>15_000_000_000: raise ValueError('10 MB reservation exceeds project cap')


def compile_only():
 work_budget();runtime_guard();BUILD.mkdir(exist_ok=True)
 binary=BUILD/'capture'
 if binary.exists(): raise ValueError('Existing compiled capture preserved; no overwrite')
 command=['clang++','-std=c++17','-O2','-I/opt/homebrew/include','-L/opt/homebrew/lib',
 '-Wl,-rpath,/opt/homebrew/lib',str(TASK/'capture.cpp'),'-lllama','-o',str(binary)]
 subprocess.run(command,check=True,timeout=60)
 write_new(BUILD/'capture-build.json',{'schema':'focuspilot.native_compile.v1','command':command,
 'compiler_version':subprocess.check_output(['clang++','--version'],text=True,timeout=30),
 'source_sha256':sha(TASK/'capture.cpp'),'binary_sha256':sha(binary),
 'headers_sha256':{str(path):sha(path) for path in HEADERS}})
 return binary


def prepare(input_path,out,pins):
 runtime=runtime_guard();work_budget();rows=requests(input_path);out=private_path(out);out.mkdir(parents=True,exist_ok=False)
 binary=BUILD/'capture'
 if not binary.is_file(): raise ValueError('Compile capture before preparing lock')
 build_record=BUILD/'capture-build.json'
 compiled=strict_json(build_record.read_text())
 if compiled['source_sha256']!=sha(TASK/'capture.cpp') or compiled['binary_sha256']!=sha(binary) or compiled['headers_sha256']!={str(path):sha(path) for path in HEADERS}: raise ValueError('Compilation source, binary or headers changed')
 selected={str(APP/name):sha(APP/name) for name in ('LocalModel.java','ModelCommandGate.java','CommandNumberWords.java')}
 selected[str(ROOT/'prototype/native/core.cpp')]=sha(ROOT/'prototype/native/core.cpp')
 classes=out/'java';classes.mkdir()
 snapshots=[]
 for name in ('LocalModel.java','ModelCommandGate.java','CommandNumberWords.java'):
  snapshot=out/name;snapshot.write_bytes((APP/name).read_bytes());snapshots.append(snapshot)
 subprocess.run([str(JAVA/'javac'),'-d',str(classes),*[str(p) for p in snapshots],str(TASK/'Render.java'),str(TASK/'CommandGateEval.java')],check=True,timeout=30)
 prompts=out/'prompts.tsv';grammar=out/'grammar.gbnf'
 subprocess.run([str(JAVA/'java'),'-Djava.library.path='+str(JNI.parent),'-cp',str(classes),
 'dev.focuspilot.prototype.Render',str(Path(input_path).resolve()),str(prompts),str(grammar)],check=True,timeout=30)
 emitted=[line.split('\t')[0] for line in prompts.read_text().splitlines()]
 if emitted!=[r[0] for r in rows]: raise ValueError('Rendered inventory differs')
 files={**runtime,**selected,str(Path(input_path).resolve()):sha(input_path),str(prompts):sha(prompts),str(grammar):sha(grammar),str(binary):sha(binary)}
 for path in (TASK/'run_capture.py',TASK/'capture.cpp',TASK/'Render.java',TASK/'CommandGateEval.java',TASK/'score.py',TASK/'test_capture.py',TASK/'README.md',build_record,*HEADERS):
  files[str(path)]=sha(path)
 for path in (*snapshots,*classes.rglob('*.class')): files[str(path)]=sha(path)
 for path in pins: files[str(Path(path).resolve())]=sha(path)
 lock={'schema':'focuspilot.balanced_native_lock.v1','rows':len(rows),'ids':[r[0] for r in rows],
 'classes':str(classes),'requests':str(Path(input_path).resolve()),'prompts':str(prompts),'grammar':str(grammar),'binary':str(binary),
 'files_sha256':files,'selected_source_sha256':selected,'context':1024,'threads':4,'maximum':128,
 'capture':False,'sampler':'GBNF then greedy','memory':'fresh context per request plus recurrent and KV clear',
 'scope':'Standalone host C API; original prompt and inference defaults mirrored; not unchanged JNI, MLX or phone evidence'}
 write_new(out/'lock.json',lock);return out/'lock.json'


def verify_lock(lock,source_commit):
 if lock.get('schema')!='focuspilot.balanced_native_lock.v1' or lock.get('context')!=1024 or lock.get('threads')!=4 or lock.get('maximum')!=128 or lock.get('capture') is not False: raise ValueError('Invalid locked settings')
 if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=30).strip()!=source_commit: raise ValueError('Expected frozen current source commit required')
 for path,digest in lock['files_sha256'].items():
  if sha(path)!=digest: raise ValueError('Frozen file changed: '+Path(path).name)
  path=Path(path)
  if ROOT in path.parents:
   relative=str(path.relative_to(ROOT))
   tracked=subprocess.run(['git','ls-files','--error-unmatch','--',relative],cwd=ROOT,capture_output=True,timeout=30).returncode==0
   if tracked:
    old=subprocess.check_output(['git','show',source_commit+':'+relative],cwd=ROOT,timeout=30)
    if hashlib.sha256(old).hexdigest()!=digest: raise ValueError('Tracked bytes differ from frozen commit')
 runtime_guard()
 rows=requests(lock['requests'])
 if len(rows)!=lock['rows'] or [r[0] for r in rows]!=lock['ids']: raise ValueError('Locked request inventory changed')
 return rows


def validate_capture(text,ids,adapter):
 lines=text.splitlines()
 if len(lines)!=len(ids)+1: raise ValueError('No partial capture scoring')
 load=strict_json(lines[0])
 if set(load)!={'phase','load_ms','adapter'} or load['phase']!='load' or type(load['adapter']) is not bool or load['adapter']!=adapter: raise ValueError('Invalid load record')
 if type(load['load_ms']) not in (int,float) or not math.isfinite(load['load_ms']) or load['load_ms']<0: raise ValueError('Invalid load timing')
 records=[]
 for ident,line in zip(ids,lines[1:]):
  row=strict_json(line)
  if set(row)!={'id','text','metrics'} or row['id']!=ident: raise ValueError('Missing, duplicate or reordered record')
  payload=strict_json(row['text'])
  if set(payload)!={'intent'} or type(payload['intent']) is not str or payload['intent'] not in INTENTS or row['text']!=json.dumps(payload,separators=(',',':')): raise ValueError('Canonical intent JSON required')
  m=row['metrics']
  if set(m)!={'prompt_tokens','generated_tokens','prefill_ms','decode_ms','total_ms','context_setup_ms','reached_eos','cpu_only','capture_enabled'}: raise ValueError('Metric keys differ')
  if m['reached_eos'] is not True or m['cpu_only'] is not True or m['capture_enabled'] is not False: raise ValueError('Actual EOS/CPU/capture proof required')
  for key in ('prompt_tokens','generated_tokens'):
   if type(m[key]) is not int or m[key]<1: raise ValueError('Positive token counts required')
  if m['generated_tokens']>128 or m['prompt_tokens']+128>1024: raise ValueError('Token bound exceeded')
  for key in ('prefill_ms','decode_ms','total_ms','context_setup_ms'):
   if type(m[key]) not in (int,float) or not math.isfinite(m[key]) or m[key]<0: raise ValueError('Finite nonnegative timing required')
  records.append(row)
 return load,records


def claim_attempt(lock_path,out,source_commit,adapter_sha):
 lock_path=private_path(lock_path)
 out=private_path(out)
 claim=Path(lock_path).resolve().parent/('adapter-claim.json' if adapter_sha else 'base-claim.json')
 if out.exists(): raise ValueError('Existing attempt preserved; no retry or overwrite')
 write_new(claim,{'source_commit':source_commit,'lock_sha256':sha(lock_path),'out':str(out),'adapter_sha256':adapter_sha})
 out.mkdir(parents=True,exist_ok=False)
 return out


def validate_adapter(path,digest):
 path=Path(path).resolve()
 if not path.is_file() or not 0<path.stat().st_size<=300000 or sha(path)!=digest:
  raise ValueError('Prospectively pinned small adapter required')
 with path.open('rb') as f:
  if f.read(4)!=b'GGUF': raise ValueError('GGUF adapter required')
 return path


def capture(lock_path,out,source_commit,adapter_path=None,adapter_sha=None):
 lock_path=private_path(lock_path)
 lock=strict_json(Path(lock_path).read_text());verify_lock(lock,source_commit);work_budget()
 if bool(adapter_path)!=bool(adapter_sha): raise ValueError('Adapter path and prospectively recorded hash required together')
 adapter=None
 if adapter_path:
  adapter=validate_adapter(adapter_path,adapter_sha)
 out=claim_attempt(lock_path,out,source_commit,adapter_sha)
 command=[lock['binary'],str(MODEL),str(adapter) if adapter else '-',lock['prompts'],lock['grammar']]
 began=time.monotonic();utc=datetime.datetime.now(datetime.timezone.utc).isoformat();job=None;exit_code=None;timed_out=False;failure=None
 record={'schema':'focuspilot.balanced_native_process.v1','source_commit':source_commit,'lock_sha256':sha(lock_path),
 'started_utc':utc,'command':command,'adapter_sha256':adapter_sha,'pid':None,'scope':lock['scope']}
 # The root-visible initial record exists before any model-loading subprocess.
 write_new(out/'initial.json',record)
 print(json.dumps({'phase':'native_capture_starting','rows':lock['rows'],'adapter':bool(adapter)}),flush=True)
 with (out/'raw.jsonl').open('x') as stdout,(out/'stderr.log').open('x') as stderr:
  try:
   job=subprocess.Popen(command,stdout=stdout,stderr=stderr);record['pid']=job.pid;write_new(out/'started.json',record)
   print(json.dumps({'phase':'native_capture_child_started','pid':job.pid,'rows':lock['rows'],'adapter':bool(adapter)}),flush=True)
   exit_code=job.wait(timeout=240)
  except subprocess.TimeoutExpired:
   job.kill();job.wait();timed_out=True
  except BaseException as problem:
   if job is not None and job.poll() is None: job.kill();job.wait()
   failure=problem
 record.update(exit_code=exit_code,timed_out=timed_out,seconds=time.monotonic()-began,
 raw_sha256=sha(out/'raw.jsonl'),stderr_sha256=sha(out/'stderr.log'),error_type=type(failure).__name__ if failure else None)
 try:
  verify_lock(lock,source_commit)
  if adapter and sha(adapter)!=adapter_sha: raise ValueError('Adapter changed during capture')
 except BaseException as problem:
  if failure is None: failure=problem
  record['postflight_error_type']=type(problem).__name__
 write_new(out/'process.json',record)
 if failure: raise failure
 if timed_out or exit_code!=0: raise ValueError('Native process incomplete; no retry or partial score')
 load,records=validate_capture((out/'raw.jsonl').read_text(),lock['ids'],bool(adapter))
 logs=(out/'stderr.log').read_text()
 fallback=[]
 for layer in ('down','gate','up'):
  marker="lora for 'blk.23.ffn_"+layer+".weight' cannot use buft 'CPU_REPACK', fallback to CPU"
  if marker in logs: fallback.append(layer)
 summary={'schema':'focuspilot.balanced_native_capture.v1','rows':len(records),'canonical_json_and_real_eos':len(records),
 'load_ms':load['load_ms'],'adapter':bool(adapter),'cpu_repack_to_cpu_lora_fallback_projections':fallback,
 'raw_sha256':record['raw_sha256'],'lock_sha256':record['lock_sha256'],'source_commit':source_commit,
 'scope':lock['scope'],'promoted':False}
 write_new(out/'capture-summary.json',summary)
 print(json.dumps({'phase':'native_capture_complete','rows':len(records),'adapter':bool(adapter),'exit_code':exit_code}),flush=True)
 return summary


def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
 sub.add_parser('compile')
 a=sub.add_parser('prepare');a.add_argument('--requests',required=True);a.add_argument('--out',required=True);a.add_argument('--pin',action='append',default=[])
 a=sub.add_parser('capture');a.add_argument('--lock',required=True);a.add_argument('--out',required=True);a.add_argument('--source-commit',required=True);a.add_argument('--adapter');a.add_argument('--adapter-sha')
 a=p.parse_args()
 if a.mode=='compile': print(compile_only())
 elif a.mode=='prepare': print(prepare(a.requests,a.out,a.pin))
 else: capture(a.lock,a.out,a.source_commit,a.adapter,a.adapter_sha)
if __name__=='__main__':main()
