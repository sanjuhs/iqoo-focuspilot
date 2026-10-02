"""POST-HOC locked 2x2 comparison; never generates or modifies primary evidence."""
import json
from run_evaluation import (TASK,BUILD,NAMES,sha,verify_freeze,read_model,
                            evaluate_gate,paired_gate,write_json)


def main():
    frozen,rows=verify_freeze()
    primary_path=TASK/'results.json';primary_before=sha(primary_path)
    primary=json.loads(primary_path.read_text());lock=json.loads((BUILD/'candidate-lock.json').read_text())
    assert primary['candidate_lock']==lock
    versions={'v09':frozen['v09_source_sha256'],'v10':lock['source_sha256']}
    for version,hashes in versions.items():
        for name in NAMES:assert sha(BUILD/(version+'-source')/name)==hashes[name]
    outputs={};models={}
    for version,hashes in versions.items():outputs[version],models[version]=read_model(rows,frozen,version,hashes)
    grid={};details={}
    for prompt in ['v09','v10']:
        grid[prompt]={}
        intents={key:value['intent'] for key,value in outputs[prompt].items()}
        for gate in ['v09','v10']:
            grid[prompt][gate],details[(prompt,gate)]=evaluate_gate(rows,intents,gate,'posthoc-prompt-'+prompt)
    result=dict(schema=1,scope='EXPLICITLY POST-HOC on already-seen frozen holdout. Locked prompt outputs crossed with locked actual Java gates. No new inference, selection-independent confirmation, model training, repairs or actions.',
      primary_results_sha256=primary_before,source_sha256=sha(__file__),
      dataset_sha256=frozen['cases_sha256'],source_locks=versions,
      model_output_sha256={v:m['metadata']['output_sha256'] for v,m in models.items()},
      prompt_by_gate=grid,
      gate_only_vs_baseline=paired_gate(details[('v09','v09')],details[('v09','v10')]),
      prompt_only_vs_baseline=paired_gate(details[('v09','v09')],details[('v10','v09')]),
      new_prompt_vs_old_prompt_under_new_gate=paired_gate(details[('v09','v10')],details[('v10','v10')]),
      generated_tokens=0,actions_executed=0,candidate_promoted=False,
      selection_limit='Any gate-only choice from this post-hoc result requires a NEW independently frozen blind set before deployment; this comparison is not independent confirmation.')
    assert sha(primary_path)==primary_before
    write_json(TASK/'posthoc-results.json',result)
    print(json.dumps(dict(grid={p:{g:{key:score[key] for key in ['supported_correct','supported_false_abstentions','supported_wrong_slots','wrong_accepted','unsupported_false_accepts','strict_correct']} for g,score in gates.items()} for p,gates in grid.items()},
      gate_only_vs_baseline=result['gate_only_vs_baseline'],prompt_only_vs_baseline=result['prompt_only_vs_baseline'],
      new_prompt_vs_old_prompt_under_new_gate=result['new_prompt_vs_old_prompt_under_new_gate'],primary_unchanged=True),indent=2))


if __name__=='__main__':main()
