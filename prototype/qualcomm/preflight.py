#!/usr/bin/env python3
"""Offline deployment preflight/evidence completeness. Never operates a phone."""
import argparse,hashlib,json
from pathlib import Path
MODEL_HASH='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
VALIDATED={'SM8750','SM8850'}
def assess(props, evidence=None):
 soc=props.get('ro.soc.model','').upper(); abi=props.get('ro.product.cpu.abi',''); api=int(props.get('ro.build.version.sdk',0))
 ready=soc in VALIDATED and abi=='arm64-v8a' and api>=27
 out={'sdk_validated_device':ready,'soc':soc,'abi':abi,'api':api,'device_scope':'validated mobile' if ready else 'outside validated mobile prerequisites','npu_verified':False,'recommendation':'compare explicit cpu/npu/hybrid' if ready else 'retain verified CPU fallback; do not infer HTP support','evidence_complete':False,'operator_coverage':'unknown'}
 if evidence is None: return out
 issues=[]
 if not ready: issues.append('device outside SDK validated mobile prerequisites')
 if evidence.get('model_sha256')!=MODEL_HASH: issues.append('wrong or missing selected model checksum')
 if evidence.get('soc')!=soc: issues.append('trace/device SoC mismatch')
 if not evidence.get('session_id'): issues.append('missing correlated synthetic session ID')
 if evidence.get('runtime')!='llama_cpp': issues.append('selected GGUF requires llama_cpp runtime')
 if evidence.get('requested_compute') not in ('cpu','npu','hybrid'): issues.append('missing explicit requested compute')
 counts=evidence.get('executed_operators',{}); htp=counts.get('HTP',0); cpu=counts.get('CPU',0)
 if type(htp) is not int or htp<=0: issues.append('no executed HTP operators supplied')
 if type(cpu) is not int or cpu<0: issues.append('CPU operator coverage missing')
 if evidence.get('requested_compute')=='cpu' and type(htp) is int and htp>0: issues.append('CPU-only request contradicts model HTP execution count')
 refs=evidence.get('trace_artifacts',[])
 if not refs: issues.append('missing hardware/operator trace artifact')
 for ref in refs:
  path=Path(ref.get('path','')); expected=ref.get('sha256','')
  if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected: issues.append('trace artifact missing/checksum mismatch')
 if not evidence.get('output_checked'): issues.append('generated result not checked')
 out['evidence_complete']=not issues; out['missing']=issues
 if not issues:
  out['operator_coverage']='mixed HTP+CPU evidence' if cpu else 'HTP operators evidenced; ancillary CPU not excluded'
  out['review']='Human review must correlate trace operations to the model run; no automatic verified NPU claim'
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--properties',type=Path,required=True);p.add_argument('--evidence',type=Path);a=p.parse_args()
 print(json.dumps(assess(json.loads(a.properties.read_text()),json.loads(a.evidence.read_text()) if a.evidence else None),indent=2))
if __name__=='__main__': main()
