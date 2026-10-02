"""Frozen manual-exemplar retrieval experiment; no optimization, phone observations or provider API."""
from __future__ import annotations
import hashlib
import json
import math
import random
import subprocess
import sys
from pathlib import Path

DIRECTORY=Path(__file__).resolve().parent
ROOT=DIRECTORY.parent.parent
sys.path.insert(0,str(ROOT/'prototype/policy'))
from policy import PositiveNetwork, generate_data, canonical_hash

MAX_DISTANCE=0.25
PROFILES={'lenient':(-1.2,0.0),'strict':(1.2,0.0),'focus_sensitive':(0.0,2.4)}
SEED=20261003


def label(x,profile):
    offset,focus=PROFILES[profile]
    score=(3.1*x[0]+2.3*x[1]+x[2]+0.8*x[3]+0.55*x[4]+0.9*x[5]
           +2.5*max(0,x[0]+x[1]-0.95)-4.1+offset+focus*(x[3]-0.5))
    return int(score>=0)


def evaluate(query,examples):
    distance=lambda x:math.sqrt(sum((a-b)**2 for a,b in zip(query,x))/6)
    ordered=sorted(enumerate(examples,1),key=lambda item:(distance(item[1]['features']),item[0]))
    if not ordered:return 'ABSTAIN',0.5,1.0
    nearest=distance(ordered[0][1]['features'])
    exact=[row for _,row in ordered if distance(row['features'])<=1e-12]
    selected=exact or [row for _,row in ordered[:3]]
    weights=[1/(0.05+distance(row['features'])) for row in selected]
    vote=sum(w*row['label'] for w,row in zip(weights,selected))/sum(weights)
    uncertainty=min(1,max(1-abs(2*vote-1),nearest/MAX_DISTANCE))
    if exact and len({row['label'] for row in exact})>1:return 'ABSTAIN',vote,1.0
    if nearest>MAX_DISTANCE or 0.35<vote<0.65:return 'ABSTAIN',vote,uncertainty
    return ('NUDGE' if vote>=0.65 else 'ALLOW'),vote,uncertainty


def main():
    artifact=json.loads((ROOT/'prototype/policy/synthetic-model.json').read_text())
    baseline=PositiveNetwork(artifact['parameters'])
    threshold=artifact['training']['threshold'] if 'training' in artifact else artifact['training_config']['threshold']
    # Families are assigned before evaluation. No heldout label enters exemplar selection.
    splits=generate_data(seed=SEED,per_family=80)
    support=[row for family in sorted({r.family for r in splits['train']})
             for row in [r for r in splits['train'] if r.family==family][:8]]
    heldout=splits['holdout']
    examples_by_profile={profile:[{'features':row.features,'label':label(row.features,profile),'family':row.family} for row in support]
                         for profile in PROFILES}
    build=DIRECTORY/'build';build.mkdir(exist_ok=True)
    java_root=ROOT/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
    subprocess.run(['javac','-d',str(build),str(java_root/'FewShotPolicy.java'),str(java_root/'TrainedPolicy.java'),str(DIRECTORY/'FewShotParity.java')],check=True)
    protocol=[];cases=[]
    for profile,examples in examples_by_profile.items():
        protocol.append('clear')
        for row in examples:protocol.append('\t'.join(['add','NUDGE' if row['label'] else 'ALLOW',*map(str,row['features'])]))
        for index,row in enumerate(heldout):
            case_id=f'{profile}:{index}'
            protocol.append('\t'.join(['eval',case_id,*map(str,row.features)]));cases.append((profile,row))
    process=subprocess.run(['java','-cp',str(build),'dev.focuspilot.prototype.FewShotParity'],input='\n'.join(protocol)+'\n',text=True,capture_output=True,check=True)
    lines=process.stdout.splitlines()
    if len(lines)!=len(cases):raise AssertionError('JVM output row count differs')
    results=[];maximum_error=0
    for line,(profile,row) in zip(lines,cases):
        case_id,recommendation,vote,uncertainty,contribution,base=line.split('\t')
        reference=evaluate(row.features,examples_by_profile[profile]);base_reference=baseline.probability(row.features)
        if recommendation!=reference[0]:raise AssertionError(f'Retrieval mismatch: {case_id}')
        for actual,expected in [(float(vote),reference[1]),(float(uncertainty),reference[2]),(float(contribution),reference[1]),(float(base),base_reference)]:
            error=abs(actual-expected);maximum_error=max(maximum_error,error)
            if error>1e-10:raise AssertionError(f'Numerical parity mismatch: {case_id} {error}')
        target=label(row.features,profile);covered=recommendation!='ABSTAIN'
        results.append({'profile':profile,'family':row.family,'target':target,'covered':covered,
                        'fewshot_correct':covered and (recommendation=='NUDGE')==bool(target),
                        'baseline_correct':(base_reference>=threshold)==bool(target),
                        'recommendation':recommendation,'id':case_id})
    summary={}
    for profile in PROFILES:
        rows=[r for r in results if r['profile']==profile];covered=[r for r in rows if r['covered']]
        summarize=lambda rows:{'total':len(rows),'baseline_correct':sum(r['baseline_correct'] for r in rows),
                              'fewshot_correct':sum(r['fewshot_correct'] for r in rows),'answered':sum(r['covered'] for r in rows),
                              'abstained':sum(not r['covered'] for r in rows)}
        summary[profile]={**summarize(rows),'coverage':len(covered)/len(rows),
                          'selective_accuracy':sum(r['fewshot_correct'] for r in covered)/len(covered) if covered else None,
                          'baseline_accuracy_same_covered_cases':sum(r['baseline_correct'] for r in covered)/len(covered) if covered else None,
                          'per_heldout_family':{family:summarize([r for r in rows if r['family']==family]) for family in sorted({r['family'] for r in rows})}}
    support_manifest={profile:{'count':len(rows),'families':sorted({r['family'] for r in rows}),'sha256':canonical_hash(rows)} for profile,rows in examples_by_profile.items()}
    report={'status':'Pre-event synthetic shifted-preference comparison, not real user outcomes or neural fine-tuning',
            'seed':SEED,'support':support_manifest,'heldout':{'count_per_profile':len(heldout),'families':sorted({r.family for r in heldout}),
            'features_sha256':canonical_hash([{'family':r.family,'features':r.features} for r in heldout])},
            'frozen_retrieval':{'maximum_examples':32,'nearest_neighbors':3,'max_rms_distance':0.25,'allow_threshold':0.35,'nudge_threshold':0.65,
                                'weight':'1/(0.05+RMS_distance)','abstention_is_counted_correct':False,'fallback_to_baseline':False},
            'profiles':PROFILES,'summary':summary,'java_python_parity':{'cases':len(cases),'maximum_absolute_error':maximum_error,'status':'passed'},
            'source_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in [('evaluate.py',Path(__file__)),('FewShotPolicy.java',java_root/'FewShotPolicy.java'),('FewShotParity.java',DIRECTORY/'FewShotParity.java')]},
            'baseline_checkpoint_sha256':hashlib.sha256((ROOT/'prototype/policy/synthetic-model.json').read_bytes()).hexdigest(),
            'limitations':['All preference labels are invented mathematical rules.','Support examples are selected by fixed family/order; no heldout-based selection or hyperparameter search.',
                           'Same feature geometry as original synthetic lab; preference teacher is shifted.','Distance/uncertainty are heuristic, uncalibrated; sparse support often abstains.',
                           'Grouped family split reduces row-level leakage but does not establish real-world generalization.','Personalization may lower accuracy; report coverage and baseline on the same answered cases.']}
    (DIRECTORY/'synthetic-exemplars.json').write_text(json.dumps(examples_by_profile,indent=2)+'\n')
    (DIRECTORY/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'summary':summary,'parity':report['java_python_parity']},indent=2))

if __name__=='__main__':main()
