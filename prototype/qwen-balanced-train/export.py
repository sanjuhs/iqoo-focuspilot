"""Narrow f32 adapter export, no base fusion. Verify transpose/scaling for each target."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import mlx.core as mx

ROOT = Path(__file__).resolve().parents[2]
LLAMA_COMMIT = '57fe1f07c3b6a1de3f4fff19098e2056a85275b7'


def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(); p.add_argument('--run', required=True); p.add_argument('--sha256', required=True)
    a = p.parse_args(); run = Path(a.run).resolve()
    if not run.is_relative_to(ROOT) or not (run / 'status.json').is_file(): raise ValueError('Known training output required')
    status = json.loads((run / 'status.json').read_text())
    if status.get('completed') is not True or status.get('training', {}).get('updates') != 224:
        raise ValueError('Completed terminal224 candidate required')
    src = run / 'adapters.safetensors'; target = run / 'adapter-f32.gguf'; manifest = run / 'export.json'
    if target.exists() or manifest.exists() or sha(src) != a.sha256: raise ValueError('Exclusive output and frozen adapter required')
    source = ROOT / 'research/llama.cpp'
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != LLAMA_COMMIT:
        raise ValueError('Pinned GGUF writer source required')
    sys.path.insert(0, str(source / 'gguf-py')); import gguf
    config = json.loads((run / 'adapter_config.json').read_text())
    if config['num_layers'] != 1 or config['lora_parameters'] != {
        'rank': 4, 'scale': 8.0, 'dropout': 0.0, 'keys': ['mlp.gate_proj', 'mlp.up_proj', 'mlp.down_proj']}:
        raise ValueError('Exact frozen final MLP contract required')
    arrays = mx.load(str(src)); rng = np.random.default_rng(20261003)
    mapping = {'gate_proj': 'ffn_gate', 'up_proj': 'ffn_up', 'down_proj': 'ffn_down'}
    if len(arrays) != 6: raise ValueError('Exactly six A/B tensors required')
    converted = []; record = []; worst = 0.0
    for old, new in mapping.items():
        prefix = 'language_model.model.layers.23.mlp.' + old
        A = np.array(arrays[prefix + '.lora_a']); B = np.array(arrays[prefix + '.lora_b'])
        if A.shape[1] != 4 or B.shape[0] != 4 or not np.isfinite(A).all() or not np.isfinite(B).all():
            raise ValueError('Rank or finite parameter mismatch')
        x = rng.normal(size=(3, A.shape[0])).astype(np.float32)
        left = (x @ A) @ B * 8.0; right = ((B.T @ (A.T @ x.T)) * (32.0 / 4)).T
        error = float(np.max(np.abs(left-right))); worst = max(worst, error)
        if error >= 1e-4: raise ValueError('Matrix orientation/scaling parity failed')
        for suffix, value in [('lora_a', A.T), ('lora_b', B.T)]:
            tensor = np.ascontiguousarray(value, dtype=np.float32)
            name = 'blk.23.' + new + '.weight.' + suffix
            converted.append((name, tensor))
            record.append({'name': name, 'shape': list(tensor.shape), 'dtype': str(tensor.dtype),
                           'sha256': hashlib.sha256(tensor.tobytes()).hexdigest()})
    # All shape/finiteness/matrix checks occur before opening a new GGUF output.
    writer = gguf.GGUFWriter(target, 'qwen35'); writer.add_type(gguf.GGUFType.ADAPTER)
    writer.add_string(gguf.Keys.Adapter.TYPE, 'lora'); writer.add_float32(gguf.Keys.Adapter.LORA_ALPHA, 32.0)
    writer.add_name('FocusPilot balanced terminal224 final-MLP research adapter')
    for name, tensor in converted: writer.add_tensor(name, tensor)
    writer.write_header_to_file(); writer.write_kv_data_to_file(); writer.write_tensors_to_file(); writer.close()
    if sha(src) != a.sha256 or target.stat().st_size > 300_000: raise ValueError('Source identity/output allowance changed')
    result = {'kind': 'narrow transpose/scaling check only, runtime prediction transfer unproven',
              'source_sha256': sha(src), 'gguf_sha256': sha(target), 'gguf_bytes': target.stat().st_size,
              'gguf_writer_commit': LLAMA_COMMIT, 'rank': 4, 'mlx_scale': 8, 'native_alpha': 32,
              'native_load_scale': 1.0, 'matrix_max_abs_error': worst, 'tensors': record,
              'promoted': False, 'base_fused_or_copied': False}
    manifest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
