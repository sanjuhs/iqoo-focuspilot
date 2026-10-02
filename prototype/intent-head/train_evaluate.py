"""Frozen-Qwen hidden-state classifier; this trains only a separate linear head."""
import argparse,base64,hashlib,json,pathlib,subprocess,time
import numpy as np
INTENTS=['start_focus','pause_focus','alarm','timer','open_app','explain','unknown']
ROOT=pathlib.Path(__file__).resolve().parents[2];TASK=pathlib.Path(__file__).resolve().parent

def sha(path):return hashlib.file_digest(pathlib.Path(path).open('rb'),'sha256').hexdigest()
def softmax(logits):
 shifted=logits-np.max(logits,axis=1,keepdims=True);e=np.exp(shifted);return e/e.sum(axis=1,keepdims=True)
def standardize(x,mean,std):return (x-mean)/std
def parameter_hash(w,b):
 h=hashlib.sha256();h.update(np.asarray(w,dtype='<f8').tobytes());h.update(np.asarray(b,dtype='<f8').tobytes());return h.hexdigest()
def predict(probabilities,threshold,margin):
 top=np.argmax(probabilities,axis=1);ranked=np.sort(probabilities,axis=1);conf=ranked[:,-1];gap=ranked[:,-1]-ranked[:,-2]
 return np.where((conf>=threshold)&(gap>=margin),top,INTENTS.index('unknown'))
def metrics(labels,predictions):
 labels=np.asarray(labels);predictions=np.asarray(predictions);unknown=INTENTS.index('unknown');supported=labels!=unknown;accepted=predictions!=unknown;abstain=~accepted
 return {'rows':int(len(labels)),'correct':int(np.sum(labels==predictions)),'accuracy':float(np.mean(labels==predictions)),'supported_rows':int(supported.sum()),'supported_correct_accepted':int(np.sum(supported&accepted&(labels==predictions))),'supported_false_abstentions':int(np.sum(supported&abstain)),'unknown_rows':int((~supported).sum()),'unknown_to_supported_false_positives':int(np.sum((~supported)&accepted)),'unknown_correct':int(np.sum((~supported)&abstain)),'accepted':int(accepted.sum()),'coverage':float(accepted.mean()),'accepted_precision':float(np.sum(accepted&(labels==predictions))/accepted.sum()) if accepted.any() else None}
def choose_threshold(labels,probabilities):
 candidates=[]
 for threshold in [.35,.45,.55,.65,.75,.85,.95,1.0]:
  for margin in [0.,.05,.1,.2,.3]:
   m=metrics(labels,predict(probabilities,threshold,margin))
   if m['unknown_to_supported_false_positives']==0:
    candidates.append((m['supported_correct_accepted'],m['accepted_precision'] or 0.,-threshold,-margin,threshold,margin,m))
 if not candidates:return {'abstain_all':True,'threshold':None,'margin':None,'validation':metrics(labels,np.full(len(labels),6))}
 best=max(candidates,key=lambda x:x[:4]);return {'abstain_all':False,'threshold':best[4],'margin':best[5],'validation':best[6]}
def policy_predictions(probabilities,selection):
 return np.full(len(probabilities),6) if selection['abstain_all'] else predict(probabilities,selection['threshold'],selection['margin'])
def fit(x,labels,log):
 mean=np.mean(x,axis=0);std=np.maximum(np.std(x,axis=0),.05);z=standardize(x,mean,std)
 n,d=z.shape;w=np.zeros((d,7),dtype=np.float64);b=np.zeros(7,dtype=np.float64)
 before=parameter_hash(w,b);initial_w=w.copy();initial_b=b.copy();counts=np.bincount(labels,minlength=7);assert np.all(counts>0)
 sample_weights=1./counts[labels];sample_weights/=sample_weights.sum();target=np.eye(7)[labels]
 mw=np.zeros_like(w);vw=np.zeros_like(w);mb=np.zeros_like(b);vb=np.zeros_like(b);losses=[];start=time.monotonic()
 for epoch in range(1,401):
  p=softmax(z@w+b);loss=-float(np.sum(sample_weights*np.log(np.maximum(p[np.arange(n),labels],1e-300))))+.02*float(np.mean(w*w));losses.append(loss)
  delta=(p-target)*sample_weights[:,None];dw=z.T@delta+(2*.02/w.size)*w;db=delta.sum(axis=0)
  mw=.9*mw+.1*dw;vw=.999*vw+.001*dw*dw;mb=.9*mb+.1*db;vb=.999*vb+.001*db*db
  w-=.02*(mw/(1-.9**epoch))/(np.sqrt(vw/(1-.999**epoch))+1e-8)
  b-=.02*(mb/(1-.9**epoch))/(np.sqrt(vb/(1-.999**epoch))+1e-8)
  assert np.isfinite(w).all() and np.isfinite(b).all()
  if epoch==1 or epoch%100==0:log('training_epoch',epoch=epoch,loss=loss)
 delta_l2=float(np.sqrt(np.sum((w-initial_w)**2)+np.sum((b-initial_b)**2)));assert delta_l2>0 and parameter_hash(w,b)!=before
 return w,b,mean,std,{'epochs':400,'learning_rate':.02,'regularization_mean_square_weight':.02,'learned_parameters':int(w.size+b.size),'initial_parameter_sha256':before,'final_parameter_sha256':parameter_hash(w,b),'parameter_delta_l2':delta_l2,'first_loss':losses[0],'last_preupdate_loss':losses[-1],'seconds':time.monotonic()-start,'std_floored_coordinates':int(np.sum(std==.05)),'seed':20261003,'initialization':'All-zero; deterministic full-batch optimizer has no stochastic sampling'}
def data(split,manifest):
 path=TASK/'build'/f'{split}.jsonl';assert sha(path)==manifest['splits'][split]['sha256'];return [json.loads(x) for x in path.read_text().splitlines()]
def features(rows,vectors):return np.array([vectors[r['id']]['vector'] for r in rows],dtype=np.float64)
def labels(rows):return np.array([INTENTS.index(r['intent']) for r in rows])
def confidence_diagnostics(split_features,w,b,mean,std,selection):
 # Read-only numerical review: these finite softmax values are not calibrated certainty.
 observed={}
 for split,x in split_features.items():
  logits=standardize(x,mean,std)@w+b;probabilities=softmax(logits)
  ranked=np.sort(logits,axis=1);top=np.max(probabilities,axis=1)
  observed[split]={'rows':len(x),'max_probability_exactly_1_due_to_float_rounding':int(np.sum(top==1.)),'top_probability_median':float(np.median(top)),'top2_logit_gap_median':float(np.median(ranked[:,-1]-ranked[:,-2]))}
 return {'selected_probability_threshold':selection['threshold'],'observed_float64_saturation':observed,'meaning':'A finite logit gap can round softmax to exactly 1. Threshold 1.0 accepts rounded values, not mathematically certain/calibrated decisions. Backend/precision changes can alter acceptance. Small synthetic validation zero FP does not guarantee safety. Do not deploy this frozen policy as a production confidence gate.'}

def review_diagnostics(summary,out,vectors_path):
 checkpoint=out/'checkpoint.npz';before=sha(checkpoint)
 assert before==summary['checkpoint_sha256'] and sha(vectors_path)==summary['vectors_sha256']
 manifest=json.loads((TASK/'data-manifest.json').read_text())
 vectors={r['id']:r for r in map(json.loads,pathlib.Path(vectors_path).read_text().splitlines())}
 with np.load(checkpoint) as c:
  w,b,mean,std=(c[k] for k in ['weights','bias','train_mean','train_std'])
  assert parameter_hash(w,b)==summary['training']['final_parameter_sha256']
  summary['confidence_limitations']=confidence_diagnostics({split:features(data(split,manifest),vectors) for split in ['train','validation','heldout']},w,b,mean,std,summary['selected_validation_policy'])
 assert sha(checkpoint)==before
 summary['current_source_sha256']=sha(__file__)
 summary['post_training_source_change']='Added baseline provenance verification and read-only numerical confidence diagnostics after the frozen training run; no fit, threshold selection, data, checkpoint or prediction changes.'
 return summary

def vector_timing(vectors):
 records=list(vectors.values());timings=[r['metrics']['prefill_ms']+r['metrics']['setup_ms'] for r in records]
 return {'rows':len(records),'first_setup_plus_prefill_ms':timings[0],'subsequent_setup_plus_prefill_ms_median':float(np.median(timings[1:])),'prefill_ms_median':float(np.median([r['metrics']['prefill_ms'] for r in records])),'setup_ms_median':float(np.median([r['metrics']['setup_ms'] for r in records])),'definition':'Host CPU-only full native prompt, fresh context plus full1024-vector eval observation; no generation. Not head-only timing or phone/NPU result.'}
def run_gate(rows,intents,out,prefix):
 source=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype/ModelCommandGate.java';expected='30f35d17a54717318492110d39c5de260a57d6878bab1d1365f658bd8ee7200d';assert sha(source)==expected,'Current gate source changed; record a separately reviewed contract instead of silently changing experiment.'
 java='/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin'
 java_out=TASK/'build/java';java_out.mkdir(exist_ok=True)
 subprocess.run([java+'/javac','-d',str(java_out),str(source),str(TASK/'IntentGateEval.java')],check=True)
 input_path=out/f'{prefix}-gate-input.tsv';input_path.write_text(''.join(r['id']+'\t'+i+'\t'+r['utterance']+'\n' for r,i in zip(rows,intents)))
 raw=subprocess.check_output([java+'/java','-cp',str(java_out),'dev.focuspilot.prototype.IntentGateEval',str(input_path)],text=True);(out/f'{prefix}-gate-output.tsv').write_text(raw)
 parsed={x[0]:x for x in (line.split('\t') for line in raw.splitlines())};results=[]
 for r in rows:
  p=parsed[r['id']];actual=(p[1],int(p[2]),int(p[3]),int(p[4]));expected_action=(r['expected_action'],r['hour'],r['minute'],r['seconds']);results.append({'id':r['id'],'family':r['family'],'expected':expected_action,'actual':actual,'correct':actual==expected_action,'accepted':p[1]!='UNKNOWN'})
 (out/f'{prefix}-action-results.json').write_text(json.dumps(results,indent=2)+'\n');supported=[r for r in results if r['expected'][0]!='UNKNOWN'];blocked=[r for r in results if r['expected'][0]=='UNKNOWN'];accepted=[r for r in results if r['accepted']]
 return {'rows':len(results),'strict_action_and_slot_correct':sum(r['correct'] for r in results),'supported_rows':len(supported),'supported_correct':sum(r['correct'] for r in supported),'must_abstain_rows':len(blocked),'correct_abstentions':sum(r['actual'][0]=='UNKNOWN' for r in blocked),'supported_false_abstentions':sum(r['actual'][0]=='UNKNOWN' for r in supported),'accepted':len(accepted),'coverage':len(accepted)/len(results),'correct_accepted':sum(r['correct'] for r in accepted),'wrong_accepted':sum(not r['correct'] for r in accepted),'gate_sha256':sha(source),'actions_executed':0}
def baseline(rows,out):
 source=TASK/'build/baseline.tsv'
 if not source.exists():return None
 metadata=json.loads((TASK/'build/baseline-metadata.json').read_text())
 assert metadata['exit_code']==0 and metadata['output_sha256']==sha(source) and metadata['input_sha256']==sha(TASK/'build/heldout.tsv')
 assert metadata['model_sha256']=='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
 assert metadata['adapter_sha256']==json.loads((TASK/'prompt-template.json').read_text())['source_sha256']
 results={};load_ms=None
 for line in source.read_text().splitlines():
  parts=line.split('\t')
  if parts[0]=='LOAD':load_ms=int(parts[1])/1e6;continue
  raw=json.loads(base64.b64decode(parts[2]));valid=False;intent='unknown'
  try:
   response=json.loads(raw['text']);valid=set(response)=={'intent'} and response['intent'] in INTENTS and raw['metrics']['reached_eos'] is True
   if valid:intent=response['intent']
  except (KeyError,ValueError,TypeError):pass
  results[parts[0]]={'intent':intent,'valid':valid,'metrics':raw['metrics'],'wall_ms':int(parts[1])/1e6}
 assert set(results)=={r['id'] for r in rows};pred=np.array([INTENTS.index(results[r['id']]['intent']) for r in rows]);m=metrics(labels(rows),pred);m['schema_and_eos_valid']=sum(r['valid'] for r in results.values());m['metadata']=metadata;m['model_load_ms']=load_ms;m['native_total_ms_median']=float(np.median([v['metrics']['total_ms'] for v in results.values()]));m['wall_ms_median']=float(np.median([v['wall_ms'] for v in results.values()]));m['gate']=run_gate(rows,[results[r['id']]['intent'] for r in rows],out,'baseline');return m

def main():
 p=argparse.ArgumentParser();p.add_argument('--vectors',default=str(TASK/'build/vectors.jsonl'));p.add_argument('--out',default=str(TASK/'build/head-run'));p.add_argument('--attach-baseline-only',action='store_true');p.add_argument('--review-diagnostics-only',action='store_true');a=p.parse_args();out=pathlib.Path(a.out)
 if a.review_diagnostics_only:
  summary=review_diagnostics(json.loads((TASK/'results.json').read_text()),out,a.vectors);(TASK/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['confidence_limitations'],indent=2));return
 if a.attach_baseline_only:
  summary=json.loads((TASK/'results.json').read_text());checkpoint=out/'checkpoint.npz';before=sha(checkpoint);rows=data('heldout',json.loads((TASK/'data-manifest.json').read_text()));summary['autoregressive_baseline']=baseline(rows,out);assert before==sha(checkpoint)==summary['checkpoint_sha256'];(TASK/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['autoregressive_baseline'],indent=2));return
 if out.exists():raise ValueError('Use a new output directory; never overwrite a frozen candidate or silently retrain after evaluation')
 out.mkdir(parents=True);(out/'train-source-at-run.py').write_bytes(pathlib.Path(__file__).read_bytes());started=time.monotonic()
 def log(phase,**kw):
  record={'phase':phase,'elapsed_seconds':time.monotonic()-started,**kw};print(json.dumps(record),flush=True)
  with (out/'phase-log.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 freeze=json.loads((TASK/'freeze-manifest.json').read_text());assert sha(TASK/'protocol.json')==freeze['protocol_sha256'];assert sha(TASK/'data-manifest.json')==freeze['data_manifest_sha256'];assert sha(TASK/'prompt-template.json')==freeze['template_manifest_sha256'];manifest=json.loads((TASK/'data-manifest.json').read_text())
 probe_metadata=json.loads((TASK/'build/probe.log').read_text().splitlines()[0]);capture_status=json.loads((TASK/'build/capture-status.json').read_text())
 assert capture_status['exit_code']==0 and sha(a.vectors)==capture_status['vectors_sha256']
 assert probe_metadata['model_sha256']=='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
 assert probe_metadata['prompt_template_sha256']==json.loads((TASK/'prompt-template.json').read_text())['template_sha256']
 assert probe_metadata['input_sha256']==freeze['all_cases_tsv_sha256'] and probe_metadata['tensor']=='result_norm' and probe_metadata['mutation'] is False and probe_metadata['generation'] is False
 vectors={r['id']:r for r in map(json.loads,pathlib.Path(a.vectors).read_text().splitlines())};assert len(vectors)==manifest['all_rows']
 for r in vectors.values():assert r['width']==1024 and len(r['vector'])==1024 and np.isfinite(r['vector']).all() and r['metrics']['cpu_only'] and r['metrics']['generated_tokens']==0 and r['metrics']['context']==1024
 train=data('train',manifest);validation=data('validation',manifest);log('data_verified',train=len(train),validation=len(validation),heldout_labels_not_read=True,vectors=len(vectors))
 w,b,mean,std,training=fit(features(train,vectors),labels(train),log);checkpoint=out/'checkpoint.npz';np.savez_compressed(checkpoint,weights=w,bias=b,train_mean=mean,train_std=std);checkpoint_sha=sha(checkpoint)
 val_prob=softmax(standardize(features(validation,vectors),mean,std)@w+b);selection=choose_threshold(labels(validation),val_prob);log('candidate_frozen',checkpoint_sha256=checkpoint_sha,selection=selection,heldout_labels_not_read=True)
 (out/'selected-policy.json').write_text(json.dumps(selection,indent=2)+'\n')
 # First heldout label access only after immutable400-update checkpoint + validation policy.
 heldout=data('heldout',manifest);x=features(heldout,vectors);z=standardize(x,mean,std);logits=z@w+b;probabilities=softmax(logits);raw=np.argmax(probabilities,axis=1);pred=policy_predictions(probabilities,selection)
 examples=[];max_sum_error=0.;ablated_changed=0;max_head_intervention_error=0.
 for index,row in enumerate(heldout):
  order=np.argsort(logits[index]);top=int(order[-1]);runner=int(order[-2]);contrib=z[index]*w[:,top];gap_contrib=z[index]*(w[:,top]-w[:,runner]);reconstructed=float(contrib.sum()+b[top]);max_sum_error=max(max_sum_error,abs(reconstructed-float(logits[index,top])))
  coordinate=int(np.argmax(np.abs(gap_contrib)));ablated=z[index].copy();ablated[coordinate]=0.;intervened=ablated@w+b;expected=logits[index]-z[index,coordinate]*w[coordinate];max_head_intervention_error=max(max_head_intervention_error,float(np.max(np.abs(intervened-expected))));ablated_changed+=int(np.argmax(intervened)!=top)
  strongest=np.argsort(np.abs(contrib))[-10:][::-1]
  examples.append({'id':row['id'],'family':row['family'],'expected_intent':row['intent'],'top_class':INTENTS[top],'final_policy_intent':INTENTS[int(pred[index])],'class_logit':float(logits[index,top]),'class_bias':float(b[top]),'sum_all_coordinate_contributions':float(contrib.sum()),'top10_signed_contributions':[{'coordinate':int(j),'train_standardized_feature':float(z[index,j]),'signed_weight':float(w[j,top]),'signed_product':float(contrib[j])} for j in strongest],'head_only_intervention':{'set_normalized_coordinate_to_zero':coordinate,'meaning':'Replace this head input coordinate with train mean; no Qwen model/state mutation.','class_after':INTENTS[int(np.argmax(intervened))],'all_class_logit_change':(intervened-logits[index]).tolist()}})
 (out/'contribution-examples.json').write_text(json.dumps(examples,indent=2)+'\n');(out/'heldout-predictions.json').write_text(json.dumps([{'id':r['id'],'family':r['family'],'expected':r['intent'],'raw':INTENTS[int(u)],'policy':INTENTS[int(v)],'probabilities':p.tolist()} for r,u,v,p in zip(heldout,raw,pred,probabilities)],indent=2)+'\n')
 assert max_sum_error<1e-9 and max_head_intervention_error<1e-9
 latencies=[]
 for row in x:
  begin=time.perf_counter_ns();p=softmax(standardize(row[None,:],mean,std)@w+b);policy_predictions(p,selection);latencies.append((time.perf_counter_ns()-begin)/1e6)
 action=run_gate(heldout,[INTENTS[int(i)] for i in pred],out,'head')
 summary={'schema':1,'scope':'Separate7175parameter signed linear intent head on frozen realQwen result_norm observations. Not Qwen fine-tuning/positive feature-policy/phone/NPU deployment.','protocol_sha256':freeze['protocol_sha256'],'dataset_sha256':manifest['all_sha256'],'vectors_sha256':sha(a.vectors),'template_sha256':json.loads((TASK/'prompt-template.json').read_text())['template_sha256'],'model_sha256':'57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf','training':training,'checkpoint_sha256':checkpoint_sha,'normalization_fit':'train only','validation_raw':metrics(labels(validation),np.argmax(val_prob,axis=1)),'selected_validation_policy':selection,'heldout_raw_head':metrics(labels(heldout),raw),'heldout_abstaining_head':metrics(labels(heldout),pred),'heldout_actions':action,'per_family':{f:{'rows':sum(r['family']==f for r in heldout),'raw_correct':sum(r['family']==f and INTENTS[int(raw[i])]==r['intent'] for i,r in enumerate(heldout)),'policy_correct':sum(r['family']==f and INTENTS[int(pred[i])]==r['intent'] for i,r in enumerate(heldout))} for f in sorted({r['family'] for r in heldout})},'probe_metadata':probe_metadata,'probe_timing':vector_timing(vectors),'head_only_cpu_ms':{'first':latencies[0],'median':float(np.median(latencies[1:])),'max':max(latencies),'definition':'Single-row numpy normalization+logits+softmax+threshold; existing captured vector assumed. Excludes model load/prefill/capture/Java gating.'},'attribution':{'exact_sum_max_abs_error':max_sum_error,'head_only_intervention_max_abs_error':max_head_intervention_error,'strongest_top_vs_runner_coordinate_ablation_changed_argmax':ablated_changed,'cases':len(heldout),'contribution_file':'ignored build/head-run/contribution-examples.json','limit':'Coordinate contributions explain this separate linear head exactly. Coordinates have no assigned human semantic meanings. No full Qwen causal/neuron/safety interpretation.'},'autoregressive_baseline':baseline(heldout,out),'checkpoint_unchanged_after_eval':sha(checkpoint)==checkpoint_sha,'promoted':False,'actions_executed':0,'wall_seconds':time.monotonic()-started,'source_sha256':sha(__file__)}
 summary['training_source_at_run_sha256']=sha(out/'train-source-at-run.py');summary['confidence_limitations']=confidence_diagnostics({'train':features(train,vectors),'validation':features(validation,vectors),'heldout':x},w,b,mean,std,selection)
 assert summary['checkpoint_unchanged_after_eval'];(TASK/'results.json').write_text(json.dumps(summary,indent=2)+'\n');log('complete',heldout_raw=summary['heldout_raw_head'],heldout_policy=summary['heldout_abstaining_head'],actions=action,checkpoint_unchanged=True)
if __name__=='__main__':main()
