"""Narrow experimental MLX->GGUF adapter writer. Only block23 MLP; never fuse base."""
import argparse, hashlib, json, pathlib, sys
import mlx.core as mx
import numpy as np
LLAMA_COMMIT='57fe1f07c3b6a1de3f4fff19098e2056a85275b7'
def main():
 p=argparse.ArgumentParser();p.add_argument('--llama-source',default='research/llama.cpp');p.add_argument('--run',default='prototype/finetuning/build/experiment');a=p.parse_args()
 import subprocess
 commit=subprocess.check_output(['git','-C',a.llama_source,'rev-parse','HEAD'],text=True).strip();assert commit==LLAMA_COMMIT
 sys.path.insert(0,str(pathlib.Path(a.llama_source).resolve()/'gguf-py'));import gguf
 out=pathlib.Path(a.run);config=json.loads((out/'adapter_config.json').read_text());assert config['num_layers']==1 and config['lora_parameters']['rank']==4 and config['lora_parameters']['scale']==8
 arrays=mx.load(str(out/'adapters.safetensors'));assert len(arrays)==6
 mapping={'gate_proj':'ffn_gate','up_proj':'ffn_up','down_proj':'ffn_down'}
 writer=gguf.GGUFWriter(out/'adapter-f32.gguf','qwen35');writer.add_type(gguf.GGUFType.ADAPTER);writer.add_string(gguf.Keys.Adapter.TYPE,'lora');writer.add_float32(gguf.Keys.Adapter.LORA_ALPHA,32.0);writer.add_name('FocusPilot synthetic fixed80-step last-MLP research adapter')
 metadata=[]
 rng=np.random.default_rng(20261002);worst=0.
 for source,dest in mapping.items():
  prefix=f'language_model.model.layers.23.mlp.{source}'
  A=np.array(arrays[prefix+'.lora_a']);B=np.array(arrays[prefix+'.lora_b']);assert A.shape[1]==4 and B.shape[0]==4
  # MLX x@A@B*scale == PEFT/GGUF B.T@A.T@x.T*(alpha/rank).
  x=rng.normal(size=(2,A.shape[0])).astype(np.float32)
  lhs=(x@A)@B*8.;rhs=((B.T@(A.T@x.T))*8.).T
  error=float(np.max(np.abs(lhs-rhs)));worst=max(worst,error);assert error<1e-4,error
  for suffix,array in [('lora_a',A.T),('lora_b',B.T)]:
   name=f'blk.23.{dest}.weight.{suffix}';v=np.ascontiguousarray(array,dtype=np.float32);writer.add_tensor(name,v);metadata.append({'name':name,'numpy_shape':list(v.shape)})
 writer.write_header_to_file();writer.write_kv_data_to_file();writer.write_tensors_to_file();writer.close()
 target=out/'adapter-f32.gguf';result={'llama_source_commit':commit,'adapter_safetensors_sha256':hashlib.file_digest((out/'adapters.safetensors').open('rb'),'sha256').hexdigest(),'gguf_bytes':target.stat().st_size,'gguf_sha256':hashlib.file_digest(target.open('rb'),'sha256').hexdigest(),'tensor_map':metadata,'synthetic_matrix_equivalence_max_abs_error':worst,'adapter_alpha':32,'rank':4,'scale':8,'scope':'Experimental narrowly mapped 3 MLP projections; runtime loading and prediction transfer separate gates. Quantization base differs from MLX; not phone promoted.'}
 (out/'export-manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
