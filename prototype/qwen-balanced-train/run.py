"""One frozen local MLX candidate. No downloads, base merges or phone operations."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'prototype/finetuning'))
from package_bundled_apk import project_bytes
from generate_data import SYSTEM
from policy import INTENTS, balanced_order, completion_weights, supervised_weights, summary
from token_trie import allowed_next

MODEL = ROOT / 'prototype/finetuning/build/model'
PROTOCOL = ROOT / 'prototype/qwen-balanced-protocol/protocol.json'


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_rows(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 2_000_000: raise ValueError('Bounded selected rows required')
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if not rows or len(rows) > 112: raise ValueError('Bounded nonempty corpus required')
    ids = set()
    for row in rows:
        if row['id'] in ids or row['intent'] not in INTENTS: raise ValueError('Duplicate id or invalid intent')
        ids.add(row['id'])
        u = row['utterance']
        if not isinstance(u, str) or not u.strip() or len(u.encode('utf-16-le')) // 2 > 500:
            raise ValueError('Whole bounded utterance required')
    return rows


def render_prompt(utterance):
    u = utterance.replace('<|', '< | ').replace('|>', ' | >')
    return ('<|im_start|>system\n' + SYSTEM + '<|im_end|>\n<|im_start|>user\n' + u
            + '<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n')


def verify_freeze(path):
    freeze = json.loads(Path(path).read_text())
    for name, expected in freeze['sha256'].items():
        p = (ROOT / name).resolve()
        if not p.is_relative_to(ROOT) or sha(p) != expected: raise ValueError('Frozen artifact changed: ' + name)
    for name, expected in freeze.get('external_sha256', {}).items():
        if not Path(name).is_absolute() or sha(name) != expected:
            raise ValueError('Pinned external runtime changed: ' + name)
    count = project_bytes(ROOT)
    if count + 5_000_000 > 15_000_000_000 or count > freeze['project_bytes_at_freeze'] + 25_000_000:
        raise ValueError('Prospective storage allowance exhausted')
    manifest = json.loads((ROOT / 'prototype/finetuning/model-manifest.json').read_text())
    for item in manifest['files']:
        p = MODEL / item['file']
        if p.stat().st_size != item['bytes'] or sha(p) != item['sha256']: raise ValueError('Pinned local model changed')
    for name in ('mlx', 'mlx-lm'):
        if importlib.metadata.version(name) != manifest['runtime'][name]: raise ValueError('Pinned runtime version changed')
    for line in (ROOT / 'prototype/finetuning/requirements.lock.txt').read_text().splitlines():
        if not line.strip(): continue
        name, version = line.split('==')
        if importlib.metadata.version(name) != version: raise ValueError('Pinned dependency version changed: ' + name)
    return freeze


def prepare(tokenizer, rows):
    import mlx.core as mx
    encoded = []
    labels = {}
    for intent in INTENTS:
        target = json.dumps({'intent': intent}, separators=(',', ':')) + '<|im_end|>'
        completion = tokenizer.encode(target, add_special_tokens=False)
        prefixes = [tokenizer.decode(completion[:n], skip_special_tokens=False,
                    clean_up_tokenization_spaces=False) for n in range(1, len(completion)+1)]
        weights, spans = completion_weights(intent, prefixes)
        if completion[-1] != tokenizer.eos_token_id: raise ValueError('Explicit EOS differs')
        labels[intent] = {'completion': completion, 'weights': weights, 'spans': spans,
                         'mixed_boundary_tokens': [n for n, (a, b) in zip(
                            [index for index, weight in enumerate(weights) if weight == 8.0], spans)
                            if a < 11 or b > 11 + len(intent)]}
    for row in rows:
        prompt = render_prompt(row['utterance'])
        sanitized = row['utterance'].replace('<|', '< | ').replace('|>', ' | >')
        rendered = tokenizer.apply_chat_template([{'role': 'system', 'content': SYSTEM},
                    {'role': 'user', 'content': sanitized}], tokenize=False,
                    add_generation_prompt=True, enable_thinking=False)
        if rendered != prompt: raise ValueError('MLX chat template differs from frozen native prompt')
        p = tokenizer.encode(prompt, add_special_tokens=False)
        target = labels[row['intent']]
        sequence = p + target['completion']
        if len(sequence) > 256: raise ValueError('Whole sequence exceeds fixed 256 tokens')
        encoded.append((mx.array([sequence]), mx.array([supervised_weights(len(p), target['weights'])])))
    return encoded, labels


def evaluate(model, tokenizer, rows, out, label):
    import mlx.core as mx
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_sampler
    sequences = [tokenizer.encode(json.dumps({'intent': i}, separators=(',', ':')),
                 add_special_tokens=False) + [tokenizer.eos_token_id] for i in INTENTS]
    records = []
    model.eval()
    for row in rows:
        prompt = tokenizer.encode(render_prompt(row['utterance']), add_special_tokens=False)
        boundary = len(prompt)
        def processor(tokens, logits):
            ids = mx.array(allowed_next(sequences, tokens.tolist()[boundary:]))
            vocab = mx.arange(logits.shape[-1])
            mask = mx.any(vocab[None, :] == ids[:, None], axis=0)
            return mx.where(mask, logits, -float('inf'))
        began = time.monotonic(); text = ''; tokens = []; final = None
        for response in stream_generate(model, tokenizer, prompt=prompt, max_tokens=128,
                sampler=make_sampler(temp=0), logits_processors=[processor]):
            text += response.text; tokens.append(response.token); final = response
        eos = final is not None and final.finish_reason == 'stop' and final.token == tokenizer.eos_token_id
        actual = None
        for intent, canonical in zip(INTENTS, sequences):
            if tokens == canonical and text == json.dumps({'intent': intent}, separators=(',', ':')) and eos:
                actual = intent
        records.append({'id': row['id'], 'expected': row['intent'], 'actual': actual,
                        'canonical_eos': actual is not None, 'reached_eos': eos, 'tokens': tokens,
                        'text': text, 'seconds': time.monotonic() - began,
                        'prompt_sha256': hashlib.sha256(render_prompt(row['utterance']).encode()).hexdigest()})
        print(json.dumps({'phase': 'evaluate', 'arm': label, 'done': len(records), 'total': len(rows)}), flush=True)
    (out / (label + '-predictions.json')).write_text(json.dumps(records, indent=2) + '\n')
    result = summary(records)
    import statistics
    times = [r['seconds'] for r in records]
    result['latency_seconds'] = {'first': times[0], 'subsequent_median': statistics.median(times[1:]) if len(times)>1 else None,
                                'scope': 'MLX Metal host, fresh cache, includes Python token-trie mask; not native GBNF'}
    return result


def main():
    p = argparse.ArgumentParser(); p.add_argument('--phase', choices=['preflight', 'dev', 'train', 'confirmation'], required=True)
    p.add_argument('--freeze', required=True); p.add_argument('--data', required=True); p.add_argument('--out', required=True)
    p.add_argument('--train-run'); p.add_argument('--expected-adapter-sha256'); a = p.parse_args()
    if os.environ.get('HF_HUB_OFFLINE') != '1' or os.environ.get('TRANSFORMERS_OFFLINE') != '1':
        raise ValueError('Explicit offline runtime settings required')
    freeze = verify_freeze(a.freeze)
    data = Path(a.data).resolve()
    selected_data = freeze['phase_data'][a.phase]
    if data != (ROOT / selected_data).resolve() or selected_data not in freeze['sha256'] or sha(data) != freeze['sha256'][selected_data]:
        raise ValueError('Phase must use its exact selected frozen corpus')
    rows = read_rows(a.data)
    expected_rows = {'preflight': 112, 'train': 112, 'dev': 14, 'confirmation': 100}[a.phase]
    if len(rows) != expected_rows: raise ValueError('Exact phase denominator required')
    out = Path(a.out).resolve()
    if not out.is_relative_to(ROOT) or out.exists(): raise ValueError('Exclusive new project output required')
    if subprocess_ignored(out) is not True: raise ValueError('Output must be ignored by Git')
    claim_dir = ROOT / 'prototype/qwen-balanced-train/build'
    claim_dir.mkdir(exist_ok=True)
    with (claim_dir / ('claim-' + a.phase + '.json')).open('x') as claim:
        json.dump({'phase': a.phase, 'out': str(out), 'freeze_sha256': sha(a.freeze)}, claim)
    out.mkdir(parents=True)
    state = {'phase': a.phase, 'completed': False, 'data_sha256': sha(a.data), 'freeze_sha256': sha(a.freeze),
             'model_identity_equivalence_claim': False, 'promoted': False}
    import subprocess
    state['source_commit'] = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    def save(): (out / 'status.json').write_text(json.dumps(state, indent=2) + '\n')
    save(); started = time.monotonic()
    try:
        import mlx.core as mx
        import mlx.nn as nn
        import mlx.optimizers as optim
        from mlx_lm import load
        from mlx_lm.tuner.utils import linear_to_lora_layers, load_adapters
        from mlx.utils import tree_flatten
        from run_experiment import digest_params
        model, tok = load(str(MODEL), trust_remote_code=False); mx.eval(model.parameters())
        if str(mx.default_device()) != 'Device(gpu, 0)': raise ValueError('Expected local MLX GPU')
        encoded, label_contract = prepare(tok, rows)
        state['label_contract'] = label_contract
        state['maximum_sequence_tokens'] = max(x.shape[1] for x, _ in encoded)
        if a.phase == 'dev': state['result'] = evaluate(model, tok, rows, out, 'base')
        elif a.phase == 'train':
            if freeze.get('pretraining_dev_complete') is not True: raise ValueError('Both pretraining dev arms required')
            mx.random.seed(20261003); model.freeze()
            params = {'rank': 4, 'scale': 8.0, 'dropout': 0.0,
                      'keys': ['mlp.gate_proj', 'mlp.up_proj', 'mlp.down_proj']}
            linear_to_lora_layers(model, 1, params)
            names = [k for k, _ in tree_flatten(model.trainable_parameters())]
            if len(model.layers) != 24 or model.layers[-1].is_linear or len(names) != 6 or any(
                    not k.startswith('language_model.model.layers.23.mlp.') or not k.endswith(('lora_a', 'lora_b')) for k in names):
                raise ValueError('Only final conventional-block three MLP adapters allowed')
            mx.eval(model.trainable_parameters()); initial = dict(tree_flatten(model.trainable_parameters()))
            initial_hash = digest_params(model.trainable_parameters())
            count = sum(v.size for v in initial.values())
            if count != 55296: raise ValueError('Unexpected trainable parameter count')
            mx.save_safetensors(str(out / 'initial-adapters.safetensors'), initial)
            optimizer = optim.Adam(learning_rate=2e-4, betas=[0.9, 0.999], eps=1e-8, bias_correction=True)
            def weighted_loss(m, x, weights):
                logits = m(x[:, :-1]).astype(mx.float32)
                ce = nn.losses.cross_entropy(logits, x[:, 1:], reduction='none')
                return mx.sum(weights * ce) / mx.sum(weights)
            vg = nn.value_and_grad(model, weighted_loss)
            order = balanced_order(rows); losses = []
            for step, index in enumerate(order, 1):
                model.train(); x, weights = encoded[index]
                value, gradients = vg(model, x, weights)
                optimizer.update(model, gradients); mx.eval(model.parameters(), optimizer.state, value)
                scalar = float(value.item())
                if not (0 <= scalar < 100): raise ValueError('Nonfinite or excessive training loss')
                losses.append(scalar)
                if step == 1 or step % 14 == 0:
                    print(json.dumps({'phase': 'train', 'update': step, 'loss': scalar}), flush=True)
            final = dict(tree_flatten(model.trainable_parameters())); final_hash = digest_params(model.trainable_parameters())
            delta = sum(float(mx.sum((v-initial[k])**2).item()) for k, v in final.items()) ** .5
            if final_hash == initial_hash or delta <= 0: raise ValueError('No verified learned update')
            mx.save_safetensors(str(out / 'adapters.safetensors'), final)
            config = {'fine_tune_type': 'lora', 'num_layers': 1, 'lora_parameters': params,
                      'base_model': str(MODEL), 'seed': 20261003, 'steps': 224}
            (out / 'adapter_config.json').write_text(json.dumps(config, indent=2) + '\n')
            (out / 'training-order.json').write_text(json.dumps(order) + '\n')
            state['training'] = {'updates': len(order), 'trainable_parameters': count, 'first14_mean_loss': sum(losses[:14])/14,
                'last14_mean_loss': sum(losses[-14:])/14, 'parameter_delta_l2': delta,
                'initial_parameters_sha256': initial_hash, 'final_parameters_sha256': final_hash,
                'adapter_sha256': sha(out / 'adapters.safetensors'),
                'optimizer': {'name': 'mlx.optimizers.Adam', 'learning_rate': 0.0002,
                              'betas': [0.9, 0.999], 'eps': 1e-8, 'bias_correction': True},
                'training_order_sha256': sha(out / 'training-order.json')}
        elif a.phase == 'confirmation':
            if not a.train_run or not a.expected_adapter_sha256: raise ValueError('Frozen terminal adapter required')
            train_run = Path(a.train_run).resolve()
            if train_run != (ROOT / freeze['terminal_adapter']['directory']).resolve():
                raise ValueError('Exact frozen terminal training directory required')
            adapter = train_run / 'adapters.safetensors'
            for name in ('adapters.safetensors', 'adapter_config.json'):
                path = train_run / name
                key = str(path.relative_to(ROOT))
                if key not in freeze['sha256'] or sha(path) != freeze['sha256'][key]:
                    raise ValueError('Terminal adapter weights/config must both be frozen')
            if sha(adapter) != a.expected_adapter_sha256: raise ValueError('Candidate differs from frozen adapter')
            state['base'] = evaluate(model, tok, rows, out, 'base')
            load_adapters(model, Path(a.train_run))
            state['adapter'] = evaluate(model, tok, rows, out, 'adapter')
            if sha(adapter) != a.expected_adapter_sha256: raise ValueError('Candidate changed after evaluation')
        state['elapsed_seconds'] = time.monotonic()-started
        state['peak_mlx_allocator_bytes'] = mx.get_peak_memory()
        state['project_bytes_after'] = project_bytes(ROOT)
        verify_freeze(a.freeze)
        state['completed'] = True; save()
        print(json.dumps({'completed': True, 'phase': a.phase, 'elapsed_seconds': state['elapsed_seconds']}), flush=True)
    except Exception as error:
        state['failure_type'] = type(error).__name__; state['failure'] = str(error); save(); raise


def subprocess_ignored(path):
    import subprocess
    return subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '--quiet', str(path)], capture_output=True).returncode == 0


if __name__ == '__main__': main()
