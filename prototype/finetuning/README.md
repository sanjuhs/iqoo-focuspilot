# Local Qwen adapter research

**Pre-event preparation, not eligible event-created competition code. Rejected candidate: do not install it in the phone app.**

This experiment performs actual local QLoRA updates of Qwen3.5-0.8B on Apple M4 Pro/48GiB using MLX GPU/Metal. It adapts only the final conventional-attention block's three MLP projections (layer 23, rank 4, scale 8): **55,296 learned adapter parameters**. Language inference/training uses the official MLX-LM implementation, with no remote executable code, cloud training, API spending, or user/phone data. The quantized base is frozen; the recurrent blocks, attention projections, embedding, normalization and vision encoder are not trained.

The pinned MLX repository includes vision weights in its single safetensors file; MLX-LM sanitizes/removes those keys and loads text inference. No images or vision training are involved. Its README attributes conversion to Qwen/Qwen3.5-0.8B, while card metadata says 0.8B-Base. That inconsistent lineage metadata needs upstream clarification. Do not claim identity with the existing Q4_0 phone quantization.

## Fixed experiment and result

Source templates were assigned to named families before training: 116 train rows/32 families, 14 validation rows/9 families, 41 heldout rows/21 families. Generated JSONL is ignored under `build/data`. The holdout contains different utterance-template families and timing/duration values, while the seven intent classes and three permitted app names necessarily recur. This is synthetic English coverage, not proof of real-user/general-language generalization.

80 Adam updates, batch 1, learning rate 0.0005, seed 20261002, completion-token-only cross entropy, maximum 170 tokens. Checkpoint selection was fixed at 80 steps; no heldout tuning or repeated candidate selection. Validation only reports loss. Training finished in 27.43 s, whole free-generation experiment 33.78 s; peak MLX allocator 1,348,399,715 bytes, not process RSS. First 10 mean loss 0.7616 → last 10 mean 0.4360, validation 0.5985. The parameter digest changed; L2 parameter delta 4.0962. The adapter hash remained unchanged after evaluation.

| Frozen 41-case test | Base | Fixed adapter |
|---|---:|---:|
| Free-generation syntactically valid JSON |37/41|41/41|
| Free-generation exact intent schema |0/41|41/41|
| Free-generation exact intent |0/41|12/41|
| Seven-canonical-answer decoder exact intent |29/41 (70.7%)|12/41 (29.3%)|
| Canonical decoder valid intent JSON |41/41|41/41|
| Correct unknown abstention |3/13|0/13|
| Supported commands falsely abstained |0/28|0/28|
| Canonical decoder warm median local latency |64.2ms|64.8ms|

The base's free answers often use another JSON shape, such as a label as a key; that 0/41 strict-schema score is **not evidence that the base understands nothing**. The finite canonical-answer decoder was added as a separately labelled post-training diagnostic, forces format only, and exposes the semantic regression. It is a token-prefix trie, not equivalent to native GBNF. It emits an action proposal for 38/41 base cases and 41/41 adapter cases, including unsupported requests: coverage without abstention is unsafe. The runtime has no calibrated confidence score.

Actual failure traces by heldout family: a negated launch family (`heldout/unknown/0`) produces `alarm`, `alarm`, `start_focus` under the adapter; negated focus (`unknown/1`) produces `start_focus`; cancellation of a bank transfer (`unknown/2`) produces `alarm`; messaging (`unknown/3`) produces `alarm`; compound commands (`unknown/5`) produce `alarm` for all three. These are rejected model proposals, not executed actions. Per-intent/per-family counts, latency limits and digest evidence are in [results.json](results.json). The main Android app continues to use its unchanged base model and independent deterministic gates/explicit confirmation.

The base decoder's first case took 0.812 s vs adapter first 0.069 s after the runtime was warm; compare warm medians, not those unequal cold/warm cases. Measurements are one serial laptop GPU run with fresh KV/recurrent cache per utterance and include Python constraint masks. They are not Android/NPU/production latency claims.

## Reproduce locally

```sh
uv venv --python 3.12 prototype/finetuning/build/venv
UV_CACHE_DIR=prototype/finetuning/build/uv-cache uv pip install \
  --python prototype/finetuning/build/venv/bin/python \
  -r prototype/finetuning/requirements.lock.txt
python3 prototype/finetuning/prepare_model.py
python3 prototype/finetuning/generate_data.py
python3 -m unittest discover -s prototype/finetuning -p 'test_*.py' -v
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  prototype/finetuning/build/venv/bin/python prototype/finetuning/run_experiment.py \
  --steps 80 --out prototype/finetuning/build/reproduction
```

Then run the separate bounded-decoder/export diagnostics against that same fixed adapter:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  prototype/finetuning/build/venv/bin/python prototype/finetuning/evaluate_bounded.py \
  --run prototype/finetuning/build/reproduction
prototype/finetuning/build/venv/bin/python prototype/finetuning/export_mlp_adapter.py \
  --run prototype/finetuning/build/reproduction
```

No training/evaluation network requests are permitted by these offline environment settings. Downloading before that uses only pinned HF data URLs and verifies every file size/SHA. Each download is bounded at 10 minutes with connection timeout; no tokens are required. The training CLI is capped at 100 steps per run. Keep output directories distinct to retain phase logs. All weights, adapters, generated data, live logs, predictions and caches stay ignored under `build/`. Inspect `build/experiment/phase-log.jsonl` for actual phase updates; do not restart an experiment solely because an observation handle expires.

## Experimental GGUF export

`export_mlp_adapter.py` uses pinned llama.cpp's GGUF writer to map only these three MLP projections. MLX A(input,rank) and B(rank,output) transpose to GGUF/PEFT matrices. GGUF alpha 32 / rank 4 reproduces MLX scale 8. A deterministic synthetic matrix check measured max absolute error 4.77e-7. The 221,888-byte f32 adapter successfully loaded with llama-completion build 9620, source 57fe1f07c, on the existing Q4_0 base; one host `start_focus` fixture passed. The native log reports adapter target buffers falling back from CPU_REPACK to CPU. Wall time 0.973 s; reported total 335.73 ms, while reported prefill 0 ms is invalid and omitted as a measurement. See [runtime-smoke.json](runtime-smoke.json) and [export-manifest.json](export-manifest.json).

This narrow writer avoids installing Torch or downloading fp16 base weights. It is not a general MLX exporter: other layers/model types require explicit mapping, rank/scale and equivalence checks. Official `convert_lora_to_gguf.py` expects PEFT names/config and Torch; a generic direct MLX adapter is not accepted unchanged. Do not fuse/export a full Qwen model with MLX-LM's limited legacy GGUF export path.

**No phone integration or promotion.** Quantization differs (MLX group64 affine vs phone GGUF Q4_0); one fixture only proves load compatibility. A successful next adapter must first pass a newly frozen independent holdout, unknown/negation/compound safety regressions, exact JNI grammar/context/tokenizer checks and actual phone performance/memory/lifecycle tests. Loading an adapter does not remove the existing user-confirmation/permission/slot gates.

## Pins, licenses and storage

See [model-manifest.json](model-manifest.json), [requirements.lock.txt](requirements.lock.txt), [data-manifest.json](data-manifest.json) and [source-manifest.json](source-manifest.json). One model download is 652,025,746 bytes (including config/tokenizer files): weights 625,229,487 bytes, SHA `f5a0d9dd3efa73510542a8023d610ff26be2b4b020d181cfc4bedaa1fcc5dd9e`; revision `da28692b5f139cb0ec58a356b437486b7dac7462`. Qwen weights Apache-2.0; MLX/MLX-LM and llama.cpp MIT. Measured model directory 635 MiB, venv 335 MiB and UV cache 341 MiB separately; shared hardlinks may make the combined physical total smaller. Workspace 7.9 GiB when recorded, below 15 GiB. No duplicate full fp16 weights were downloaded.

Primary documentation: [MLX-LM LoRA guide](https://github.com/ml-explore/mlx-lm/blob/v0.32.0/mlx_lm/LORA.md), [pinned Qwen3.5 implementation](https://github.com/ml-explore/mlx-lm/blob/a9bd8af5c02118882af735cef60705d2efce9fd0/mlx_lm/models/qwen3_5.py), [pinned MLX model](https://huggingface.co/mlx-community/Qwen3.5-0.8B-4bit/tree/da28692b5f139cb0ec58a356b437486b7dac7462), [Qwen license](https://huggingface.co/Qwen/Qwen3.5-0.8B/blob/main/LICENSE), [pinned llama.cpp adapter converter](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/convert_lora_to_gguf.py).

The workspace grew to approximately 10 GiB when the 0.5 bundled APKs and build outputs were retained; it remains within the 15 GiB ceiling.
