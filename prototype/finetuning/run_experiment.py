"""Bounded local MLX QLoRA experiment. Last conventional block MLP only."""
import argparse, hashlib, json, pathlib, random, time
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler
from mlx_lm.tuner.utils import linear_to_lora_layers
from generate_data import SYSTEM
INTENTS={'start_focus','pause_focus','alarm','timer','open_app','explain','unknown'}
def digest_params(params):
 import numpy as np
 h=hashlib.sha256()
 for key,value in sorted(tree_flatten(params)):
  h.update(key.encode());h.update(np.array(value).tobytes())
 return h.hexdigest()
def rows(path):return [json.loads(x) for x in pathlib.Path(path).read_text().splitlines()]
def prompt(tokenizer,row):
 return tokenizer.apply_chat_template(row['messages'][:2],tokenize=True,add_generation_prompt=True,enable_thinking=False)
def example(tokenizer,row):
 p=prompt(tokenizer,row); completion=tokenizer.encode(row['messages'][-1]['content']+'<|im_end|>',add_special_tokens=False)
 seq=p+completion
 assert len(seq)<=256, len(seq)
 return mx.array([seq]),len(p)
def loss(model,x,p):
 logits=model(x[:,:-1]).astype(mx.float32)
 ce=nn.losses.cross_entropy(logits,x[:,1:],reduction='none')
 mask=mx.arange(ce.shape[1])>=p-1
 return mx.sum(ce*mask)/mx.sum(mask)
def evaluate(model,tok,data,label,log):
 model.eval(); records=[];t0=time.monotonic()
 for n,row in enumerate(data):
  start=time.monotonic()
  text=generate(model,tok,prompt=prompt(tok,row),max_tokens=32,sampler=make_sampler(temp=0),verbose=False)
  actual=None;valid=False;syntactic=False
  try:
   parsed=json.loads(text.strip());syntactic=True;valid=isinstance(parsed,dict) and set(parsed)=={'intent'} and parsed['intent'] in INTENTS
   if valid:actual=parsed['intent']
  except (ValueError,TypeError):pass
  record={'group':row['group'],'expected':row['intent'],'actual':actual,'valid_json':valid,'syntactically_valid_json':syntactic,'text':text,'seconds':time.monotonic()-start}
  records.append(record)
  log('evaluation_case',model=label,index=n+1,total=len(data),expected=row['intent'],actual=actual,valid_json=valid)
 total=len(records);unk=[r for r in records if r['expected']=='unknown'];supported=[r for r in records if r['expected']!='unknown'];predunk=[r for r in records if r['actual']=='unknown']
 summary={'rows':total,'correct':sum(r['actual']==r['expected'] for r in records),'accuracy':sum(r['actual']==r['expected'] for r in records)/total,'syntactically_valid_json':sum(r['syntactically_valid_json'] for r in records),'valid_intent_schema':sum(r['valid_json'] for r in records),'valid_json':sum(r['valid_json'] for r in records),'unknown_rows':len(unk),'unknown_correct_abstention':sum(r['actual']=='unknown' for r in unk),'unknown_recall':sum(r['actual']=='unknown' for r in unk)/len(unk),'supported_rows':len(supported),'supported_false_abstention':sum(r['actual']=='unknown' for r in supported),'predicted_unknown':len(predunk),'abstention_precision':sum(r['expected']=='unknown' for r in predunk)/len(predunk) if predunk else None,'seconds':time.monotonic()-t0,'per_intent':{i:{'n':sum(r['expected']==i for r in records),'correct':sum(r['expected']==i and r['actual']==i for r in records)} for i in sorted(INTENTS)},'per_group':{g:{'n':sum(r['group']==g for r in records),'correct':sum(r['group']==g and r['actual']==r['expected'] for r in records)} for g in sorted({r['group'] for r in records})}}
 return summary,records

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='prototype/finetuning/build/model');p.add_argument('--data',default='prototype/finetuning/build/data');p.add_argument('--out',default='prototype/finetuning/build/run');p.add_argument('--steps',type=int,default=80);p.add_argument('--seed',type=int,default=20261002);p.add_argument('--skip-eval',action='store_true');a=p.parse_args()
 assert 1<=a.steps<=100
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 def log(phase,**kw):
  entry={'phase':phase,'elapsed_s':round(time.monotonic()-started,3),**kw};raw=json.dumps(entry);print(raw,flush=True)
  with (out/'phase-log.jsonl').open('a') as f:f.write(raw+'\n')
 started=time.monotonic();random.seed(a.seed);mx.random.seed(a.seed)
 log('load',device=str(mx.default_device()),model=a.model,steps=a.steps)
 model,tok=load(a.model,trust_remote_code=False);mx.eval(model.parameters());log('loaded',layers=len(model.layers),last_is_linear=model.layers[-1].is_linear)
 assert len(model.layers)==24 and not model.layers[-1].is_linear
 train=rows(pathlib.Path(a.data)/'train.jsonl');valid=rows(pathlib.Path(a.data)/'valid.jsonl')
 tokenized=[example(tok,r) for r in train];validation=[example(tok,r) for r in valid]
 log('data_frozen',train_rows=len(train),validation_rows=len(valid),max_tokens=max(x.shape[1] for x,_ in tokenized),heldout_not_read=True)
 model.freeze();params={'rank':4,'scale':8.0,'dropout':0.0,'keys':['mlp.gate_proj','mlp.up_proj','mlp.down_proj']}
 linear_to_lora_layers(model,1,params)
 names=[k for k,v in tree_flatten(model.trainable_parameters())]
 assert all(k.startswith('language_model.model.layers.23.mlp.') and k.endswith(('lora_a','lora_b')) for k in names),names
 mx.eval(model.trainable_parameters());initial_hash=digest_params(model.trainable_parameters());initial={k:mx.array(v) for k,v in tree_flatten(model.trainable_parameters())}
 mx.save_safetensors(str(out/'initial-adapters.safetensors'),dict(tree_flatten(model.trainable_parameters())))
 optimizer=optim.Adam(learning_rate=5e-4);vg=nn.value_and_grad(model,loss)
 log('training_start',trainable_parameters=sum(v.size for _,v in tree_flatten(model.trainable_parameters())),trainable_names=names,initial_parameters_sha256=initial_hash)
 order=list(range(len(train)));random.shuffle(order);losses=[]
 for step in range(a.steps):
  if step and step%len(order)==0:random.shuffle(order)
  x,boundary=tokenized[order[step%len(order)]]
  model.train();val,grads=vg(model,x,boundary);optimizer.update(model,grads);mx.eval(model.parameters(),optimizer.state,val)
  value=float(val.item());assert value==value and value<100,value;losses.append(value)
  if step==0 or (step+1)%10==0:
   log('training_step',step=step+1,loss=value,peak_memory_bytes=mx.get_peak_memory())
 model.eval();validation_loss=sum(float(loss(model,x,b).item()) for x,b in validation)/len(validation)
 final_params=dict(tree_flatten(model.trainable_parameters()));final_hash=digest_params(model.trainable_parameters());delta_sq=sum(float(mx.sum((v-initial[k])**2).item()) for k,v in final_params.items());assert final_hash!=initial_hash and delta_sq>0
 mx.save_safetensors(str(out/'adapters.safetensors'),final_params)
 adapter_config={'fine_tune_type':'lora','num_layers':1,'lora_parameters':params,'base_model':a.model,'seed':a.seed,'steps':a.steps}
 (out/'adapter_config.json').write_text(json.dumps(adapter_config,indent=2)+'\n')
 training={'steps':a.steps,'seed':a.seed,'learning_rate':5e-4,'batch_size':1,'rank':4,'scale':8,'last_layer':23,'targets':params['keys'],'trainable_parameters':sum(v.size for v in final_params.values()),'initial_parameters_sha256':initial_hash,'final_parameters_sha256':final_hash,'parameter_delta_l2':delta_sq**.5,'adapter_file_sha256':hashlib.file_digest((out/'adapters.safetensors').open('rb'),'sha256').hexdigest(),'first_loss':losses[0],'last_loss':losses[-1],'mean_first10_loss':sum(losses[:10])/len(losses[:10]),'mean_last10_loss':sum(losses[-10:])/len(losses[-10:]),'validation_completion_loss':validation_loss,'peak_memory_bytes':mx.get_peak_memory(),'seconds':time.monotonic()-started}
 log('training_complete',**training)
 summary={'schema':1,'scope':'Pre-event synthetic local MLX GPU research, no phone/native promotion.','training':training}
 if not a.skip_eval:
  # Read frozen heldout only after fixed-step candidate is final; no tuning after results.
  heldout=rows(pathlib.Path(a.data)/'heldout.jsonl')
  model.load_weights(list(initial.items()),strict=False)
  baseline,records=evaluate(model,tok,heldout,'base_zero_adapter',log);(out/'baseline-predictions.json').write_text(json.dumps(records,indent=2)+'\n');summary['baseline']=baseline
  model.load_weights(str(out/'adapters.safetensors'),strict=False)
  adapter,records=evaluate(model,tok,heldout,'trained_adapter',log);(out/'adapter-predictions.json').write_text(json.dumps(records,indent=2)+'\n');summary['adapter']=adapter
  summary['promoted']=False;summary['heldout_used_for_training_or_selection']=False
 summary['adapter_sha256_after_evaluation']=hashlib.file_digest((out/'adapters.safetensors').open('rb'),'sha256').hexdigest()
 assert summary['adapter_sha256_after_evaluation']==training['adapter_file_sha256']
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');log('complete',summary_file=str(out/'summary.json'))
if __name__=='__main__':main()
