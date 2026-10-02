"""Publish aggregate-only seen development evidence; retain raw requests/text ignored."""
import base64, hashlib, json, math, pathlib, statistics
LAB=pathlib.Path(__file__).resolve().parent
ROOT=LAB.parents[1]
def sha(path):
    with pathlib.Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(path):return json.loads(path.read_text())
def capture(directory):
    meta=read(directory/'capture-metadata.json'); result=read(directory/'results.json'); details=read(directory/'details.json')
    assert meta['exit_code']==0 and meta['timed_out'] is False
    assert sha(directory/'model-output.tsv')==meta['output_sha256']
    assert sha(directory/'requests.tsv')==meta['requests_sha256']
    assert len(details)==36 and len({d['id'] for d in details})==36
    native=[];token=[];generated=[];java=[]
    for line in (directory/'model-output.tsv').read_text().splitlines():
        fields=line.split('\t')
        if fields[0]=='LOAD':continue
        raw=json.loads(base64.b64decode(fields[2])); m=raw['metrics']; answer=json.loads(raw['text'])
        assert set(answer)=={'intent'} and answer['intent'] in {'start_focus','pause_focus','alarm','timer','open_app','explain','unknown'}
        assert raw['text']=='{"intent":"'+answer['intent']+'"}'
        assert m['reached_eos'] is True and m['cpu_only'] is True and m['capture_enabled'] is False
        assert raw.get('activations',[])==[]
        assert all(isinstance(m[key],(int,float)) and not isinstance(m[key],bool) and math.isfinite(m[key]) and m[key]>=0 for key in ['total_ms','prefill_ms','decode_ms'])
        assert all(isinstance(m[key],int) and not isinstance(m[key],bool) and m[key]>0 for key in ['prompt_tokens','generated_tokens'])
        native.append(m['total_ms']);token.append(m['prompt_tokens']);generated.append(m['generated_tokens']);java.append(int(fields[1])/1e6)
    assert len(native)==36 and result['format_eos_valid']==36
    assert len(details)==result['rows'] and sum(d['raw_correct'] for d in details)==result['raw_correct']
    assert sum(d['supported'] and d['correct'] for d in details)==result['supported_action_slot_correct']
    assert all(sha(directory/'source'/name)==digest for name,digest in meta['source_sha256'].items())
    return meta,result,details,{'first_native_ms':native[0],'warm_native_ms_median':statistics.median(native[1:]),'native_ms_median':statistics.median(native),'native_ms_range':[min(native),max(native)],'java_ms_median':statistics.median(java),'prompt_tokens_median':statistics.median(token),'prompt_tokens_range':[min(token),max(token)],'generated_tokens_median':statistics.median(generated),'generated_tokens_range':[min(generated),max(generated)]}
def main():
    candidate=LAB/'build/json1';baseline=ROOT/'prototype/command-compact-dev/build/baseline'
    cm,cr,cd,ct=capture(candidate);bm,br,bd,bt=capture(baseline)
    frozen=read(LAB/'freeze.json')
    assert sha(LAB/'JsonIntentCandidate.java')==frozen['candidate_java_sha256']==cm['source_sha256']['JsonIntentCandidate.java']
    assert sha(LAB/'JsonRunner.java')==frozen['runner_java_sha256'] and sha(LAB/'run_development.py')==frozen['runner_python_sha256']
    assert sha(baseline/'results.json')==frozen['baseline_results_sha256']
    assert sha(baseline/'capture-metadata.json')==frozen['baseline_capture_metadata_sha256']
    assert cm['requests_sha256']==bm['requests_sha256'] and cm['corpus_generator_sha256']==bm['corpus_generator_sha256']
    assert cm['model_sha256']==bm['model_sha256']==frozen['model_sha256']
    assert cm['native_sha256']==bm['native_sha256']==frozen['native_sha256']
    for name in ['LocalModel.java','ModelCommandGate.java','CommandNumberWords.java','DevGateEval.java']:
        assert cm['source_sha256'][name]==bm['source_sha256'][name]
    linked=read(ROOT/'prototype/command-compact-dev/runtime-provenance.json')['linked_libraries_current_readonly_sha256']
    assert all(sha(path)==digest for path,digest in linked.items())
    old={d['id']:d for d in bd}
    gains=[d['id'] for d in cd if d['correct'] and not old[d['id']]['correct']]
    losses=[d['id'] for d in cd if not d['correct'] and old[d['id']]['correct']]
    raw_losses=[d['id'] for d in cd if d['supported'] and not d['raw_correct'] and old[d['id']]['raw_correct']]
    go=cr['supported_action_slot_correct']>br['supported_action_slot_correct'] and not losses and not raw_losses and cr['supported_wrong_accepted']==0 and cr['unsupported_action_false_accepts']==0
    selected={key:cr[key] for key in ['rows','supported_rows','unsupported_rows','raw_correct','supported_raw_correct','unknown_raw_correct','unsupported_model_nonunknown','format_eos_valid','supported_action_slot_correct','supported_false_abstentions','supported_wrong_accepted','unsupported_action_false_accepts','strict_correct','model_load_ms']}
    previous={key:br[key] for key in selected}
    per_intent=[]
    for intent in ['start_focus','pause_focus','alarm','timer','open_app','explain','unknown']:
        rows=[d for d in cd if d['expected_intent']==intent]
        per_intent.append(dict(intent=intent,rows=len(rows),baseline_raw_correct=sum(old[d['id']]['raw_correct'] for d in rows),candidate_raw_correct=sum(d['raw_correct'] for d in rows),baseline_complete_proposal_correct=sum(old[d['id']]['correct'] for d in rows),candidate_complete_proposal_correct=sum(d['correct'] for d in rows)))
    result={'schema':'focuspilot.json_development.v1','scope':'One fixed candidate on 36 openly seen synthetic development requests, not fresh accuracy or promotion','candidate':selected,'historical_same_backend_baseline':previous,'candidate_timing_tokens':ct,'baseline_timing_tokens':bt,'per_intent':per_intent,'full_proposal_gain_ids':gains,'full_proposal_loss_ids':losses,'supported_raw_intent_loss_ids':raw_losses,'remaining_supported_failure_ids':[d['id'] for d in cd if d['supported'] and not d['correct']],'all_row_correctness':[{'id':d['id'],'family':d['family'],'supported':d['supported'],'baseline_raw_correct':old[d['id']]['raw_correct'],'candidate_raw_correct':d['raw_correct'],'baseline_complete_proposal_correct':old[d['id']]['correct'],'candidate_complete_proposal_correct':d['correct'],'candidate_format_eos_valid':d['valid']} for d in cd],'decision':'GO to a fresh frozen confirmation; no app promotion' if go else 'NO GO; do not confirm or promote','promoted':False,'actions_executed':0,'cpu_only':True,'capture_enabled':False,'context':1024,'threads':4,'native_timeout_seconds':180,'actual_capture_wall_seconds':cm['wall_seconds'],'actual_capture_exit_code':cm['exit_code'],'actual_capture_timed_out':cm['timed_out'],'candidate_sources':cm['source_sha256'],'linked_libraries_verified_sha256':linked,'model_sha256':cm['model_sha256'],'native_sha256':cm['native_sha256'],'requests_sha256':cm['requests_sha256'],'corpus_generator_sha256':cm['corpus_generator_sha256'],'private_evidence_sha256':{'candidate_output':cm['output_sha256'],'candidate_results':sha(candidate/'results.json'),'candidate_capture_metadata':sha(candidate/'capture-metadata.json'),'baseline_output':bm['output_sha256'],'baseline_results':sha(baseline/'results.json'),'baseline_capture_metadata':sha(baseline/'capture-metadata.json')},'freeze_sha256':sha(LAB/'freeze.json'),'aggregate_publisher_sha256':sha(__file__),'limits':['Both captures use already seen development requests; examples and development selection can overfit.','Historical baseline and candidate run at different times; no controlled thermal, cache or scheduler experiment.','No phone, NPU, ASR, action execution, training, new model or causal interpretation evidence.','Two supported false abstentions remain; nine unsupported raw intents remain non-unknown and depend on the independent gate.','Pre-existing host dylib was not rebuilt; observed identity is established, immutable build-time compiler/source provenance is not newly established.']}
    with (LAB/'development-results.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    metadata={**frozen,'source_sha256':cm['source_sha256'],'actual_capture_metadata_sha256':sha(candidate/'capture-metadata.json'),'development_results_sha256':sha(LAB/'development-results.json'),'selection_decision':result['decision']}
    with (LAB/'candidate.json').open('x') as stream:stream.write(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({'decision':result['decision'],'supported_gains':gains,'supported_losses':losses,'raw_losses':raw_losses,'aggregate_sha256':sha(LAB/'development-results.json'),'directory_bytes':sum(p.stat().st_size for p in LAB.rglob('*') if p.is_file())},indent=2))
if __name__=='__main__':main()
