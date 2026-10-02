"""A separate fixed-candidate diagnostic: seven canonical token sequences, no training."""
import argparse, hashlib, json, pathlib, statistics, time
import mlx.core as mx
from mlx_lm import load
from run_experiment import INTENTS,evaluate
from mlx_lm.tuner.utils import load_adapters

from token_trie import allowed_next

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='prototype/finetuning/build/model');p.add_argument('--run',default='prototype/finetuning/build/experiment');p.add_argument('--data',default='prototype/finetuning/build/data/heldout.jsonl');a=p.parse_args();out=pathlib.Path(a.run)
 before=hashlib.file_digest((out/'adapters.safetensors').open('rb'),'sha256').hexdigest()
 model,tok=load(a.model,trust_remote_code=False);model.eval()
 sequences=[tok.encode(json.dumps({'intent':i},separators=(',',':')),add_special_tokens=False)+[tok.eos_token_id] for i in sorted(INTENTS)]
 data=[json.loads(x) for x in pathlib.Path(a.data).read_text().splitlines()];results={}
 # Reuse the exact evaluator but intercept generate only to add a finite trie.
 import run_experiment
 original=run_experiment.generate
 def bounded(*args,**kwargs):
  boundary=len(kwargs['prompt'])
  def processor(tokens,logits):
   permitted=allowed_next(sequences,tokens.tolist()[boundary:]);ids=mx.array(permitted);vocab=mx.arange(logits.shape[-1]);mask=mx.any(vocab[None,:]==ids[:,None],axis=0)
   return mx.where(mask,logits,-float('inf'))
  kwargs['logits_processors']=[processor]
  return original(*args,**kwargs)
 run_experiment.generate=bounded
 for name in ['baseline','adapter']:
  if name=='adapter':load_adapters(model,out);model.eval()
  def log(phase,**kw):print(json.dumps({'phase':phase,**kw}),flush=True)
  summary,records=evaluate(model,tok,data,name,log)
  durations=[r['seconds'] for r in records];summary['latency_seconds']={'first':durations[0],'median':statistics.median(durations),'min':min(durations),'max':max(durations),'scope':'single serial warm local MLX GPU run; includes Python token-trie masks, fresh recurrent/KV state per case'}
  results[name]=summary;(out/f'{name}-bounded-predictions.json').write_text(json.dumps(records,indent=2)+'\n')
 after=hashlib.file_digest((out/'adapters.safetensors').open('rb'),'sha256').hexdigest();assert before==after
 results.update({'decoder':'Canonical JSON token trie, greedy; forces syntax/schema only, not correct intent. Diagnostic added after fixed-candidate free-generation evaluation. No new training/checkpoint selection.','adapter_sha256_before':before,'adapter_sha256_after':after,'promoted':False,'equivalent_to_native_gbnf':False})
 (out/'bounded-summary.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps({n:{k:results[n][k] for k in ['correct','rows','unknown_correct_abstention','valid_json','latency_seconds']} for n in ['baseline','adapter']},indent=2))
if __name__=='__main__':main()
