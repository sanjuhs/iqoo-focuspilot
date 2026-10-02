"""Freeze exactly one already captured development candidate, never promote it."""
import argparse,base64,hashlib,json,pathlib,re,subprocess
from run_development import LAB,JAVA,MAP,sha,save,budget

MARKER='UNIQUE_COMPACT_INVENTORY_REQUEST_314159'
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('candidate',choices=['compact1','compact2','compact3']);args=parser.parse_args()
    if (LAB/'CompactIntentCandidate.java').exists() or (LAB/'candidate.json').exists():raise ValueError('Frozen candidate already exists; never overwrite')
    out=LAB/'build'/args.candidate;results=json.loads((out/'results.json').read_text())
    original=LAB/'candidates'/args.candidate/'CompactIntentCandidate.java'
    assert sha(original)==results['metadata']['source_sha256']['CompactIntentCandidate.java']
    inventory=subprocess.check_output([str(JAVA/'java'),'-cp',str(out/'java'),'dev.focuspilot.prototype.PromptInventory',MARKER],text=True,timeout=30).splitlines()
    assert len(inventory)==3
    prompt=base64.b64decode(inventory[0]).decode();grammar=base64.b64decode(inventory[1]).decode();maximum=int(inventory[2])
    turns=re.findall(r'<\|im_start\|>user\n(.*?)<\|im_end\|>',prompt,re.S);assert turns.count(MARKER)==1
    examples=[x for x in turns if x!=MARKER]
    if not examples:
        system=re.search(r'<\|im_start\|>system\n(.*?)<\|im_end\|>',prompt,re.S).group(1)
        prose=system.split('Examples: ',1)[1]
        examples=[x.strip() for x in re.findall(r'([^=]+?)=[0-6]\.(?:\s|$)',prose)]
    assert examples and maximum==4
    (LAB/'CompactIntentCandidate.java').write_bytes(original.read_bytes())
    data={'scope':'Development-selected; frozen for fresh independently authored synthetic confirmation; unpromoted',
      'candidate':args.candidate,'candidate_java_sha256':sha(original),'source_sha256':sha(original),
      'grammar':grammar,'grammar_sha256':digest(grammar),'max_tokens':maximum,'digit_to_intent':MAP,
      'prompt_marker':MARKER,'rendered_marker_prompt_sha256':digest(prompt),'prompt_template_sha256':digest(prompt),
      'prompt_hash_scope':'Exact actual renderPrompt(marker) bytes, including chat controls and escaped assistant thinking prefix',
      'fixed_example_count':len(examples),'examples':examples,'inventory_source_sha256':sha(LAB/'PromptInventory.java'),
      'development_round':args.candidate,'development_results_sha256':sha(out/'results.json'),
      'baseline_rows':'Same openly seen prior36 development requests; no new holdout',
      'model_sha256':results['metadata']['model_sha256'],'native_sha256':results['metadata']['native_sha256'],
      'context':1024,'threads':4,'capture_enabled':False,'cpu_only':True,'actions_executed':0,'promoted':False}
    save(LAB/'candidate.json',data)
    summaries=[json.loads((LAB/'build'/r/'results.json').read_text()) for r in ['baseline','compact1','compact2','compact3']]
    save(LAB/'development-results.json',{'scope':'OPENLY_SEEN_DEVELOPMENT; all completed attempts retained; no phone, NPU, training or generalization claim',
      'rows':36,'supported_rows':18,'unsupported_rows':18,'selected_candidate':args.candidate,
      'selection_rule':'Maximize correct supported action+slots; break ties by more raw unknown rejections, then lower native median. No candidate promotes from development.',
      'rounds':summaries,'candidate':data,'directory_bytes_before_aggregate':budget(),'actions_executed':0,'promoted':False})
    budget();print(json.dumps(data,indent=2))

if __name__=='__main__':main()
