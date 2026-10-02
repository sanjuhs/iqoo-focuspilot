# Actual local Qwen fine-tuning experiment

This is **pre-event research, not event-created submission code**. An actual local language-model adapter was trained on 2 October 2026; it failed semantic/safety evaluation and is **not deployed**. The app's pinned Qwen3.5-0.8B Q4_0 and JNI remain untouched.

[Reproducible lab](../prototype/finetuning/README.md) uses Apple M4 Pro 48 GiB, Python 3.12.13, MLX 0.32.2 and MLX-LM 0.32.0 on local GPU/Metal. A single pinned [4-bit MLX artifact](https://huggingface.co/mlx-community/Qwen3.5-0.8B-4bit/tree/da28692b5f139cb0ec58a356b437486b7dac7462) was downloaded and verified: weights 625,229,487 bytes, SHA `f5a0d9dd3efa73510542a8023d610ff26be2b4b020d181cfc4bedaa1fcc5dd9e`, Apache-2.0. Complete config/tokenizer/model download 652,025,746 bytes. No full-fp16 duplicate, paid cloud/API, tokens, user history or private screens were used; model loading disallows remote code.

The quantized base was frozen. Rank 4 LoRA adapted the three MLP projections in layer 23, the final conventional-attention block: 55,296 trainable parameters. Recurrent/attention/embedding/normalization weights and vision were not trained. [Official MLX-LM supports quantized low-rank training](https://github.com/ml-explore/mlx-lm/blob/v0.32.0/mlx_lm/LORA.md); the [pinned Qwen3.5 source](https://github.com/ml-explore/mlx-lm/blob/a9bd8af5c02118882af735cef60705d2efce9fd0/mlx_lm/models/qwen3_5.py) provides the hybrid model implementation. Successful last-MLP updates establish this narrow training path, not whole recurrent-model backpropagation or causal interpretability.

80 fixed Adam updates, batch 1, learning rate 0.0005, completion-only loss, ≤170 tokens. Synthetic wording families were frozen into 116 train / 14 validation / 41 heldout rows before training. Entire utterance-template families and timing/duration values differ across splits; shared intent classes and permitted app names recur. Source generator and dataset/group hashes are tracked; generated data, adapters, logs and predictions are ignored. No checkpoint selection or retraining followed the heldout results.

| Frozen 41-case comparison | Base | Adapter |
|---|---:|---:|
| Free-generation JSON syntax |37/41|41/41|
| Free-generation exact intent schema |0/41|41/41|
| Free-generation exact intent |0/41|12/41|
| Canonical seven-answer decoder exact intent |29/41|12/41|
| Correct unsupported-request abstention |3/13|0/13|
| Canonical decoder schema-valid output |41/41|41/41|
| Warm median local GPU inference |64.2ms|64.8ms|

The free baseline often emits a different JSON shape. An added finite answer-token trie reveals that format learning masks a semantic regression: 70.7%→29.3% exact intent. It is a separate diagnostic and is not identical to native GBNF. Neither model's abstention is sufficient: the adapter proposes a supported intent for every unsupported request, including negation, financial cancellation, messaging and compound commands. These proposals were never executed. Real Android slot/permission/confirmation gates remain mandatory.

Training 27.43 s, whole free-generation experiment 33.78 s; MLX peak allocator 1,348,399,715 bytes. Mean loss first 10 steps 0.7616 → last 10 steps 0.4360, validation 0.5985. Initial parameter SHA `4cca6155a4dba982480104d3935f6e59349454f1dce4c515848dcd4685591446` changed to `8ced7b0ee0b6a5399f2d8f616d87572f1e24d0423c2e2e77717235f042161252`, deltaL2=4.0962. Adapter file SHA `221a2030d2af7122fcb1613059923ba024adecbdf71a81a00c729bbd542f6f9a` remained unchanged after evaluation. This is real parameter learning; retrieval/prompt examples and the existing trained tiny feature policy are separate mechanisms. See [machine-readable results](../prototype/finetuning/results.json).

A narrowly implemented f32 LoRA GGUF export is 221,888 bytes, SHA `ab8e90c470901652b66ab1d74de560a765cbe92deb92c4b8017389447259dd03`. Matrix transpose/scale equivalence was checked (max error 4.77e-7). [Pinned llama.cpp](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/convert_lora_to_gguf.py) adapter layout guided the writer, avoiding a Torch install. Actual host llama-completion build 9620 loaded it with the unchanged Q4_0 base and returned `start_focus` on one fixture. Native logs show the three adapter targets falling back from CPU_REPACK to CPU; wall 0.973 s, total native 335.73 ms. The tool logged zero prefill time, which is invalid and not presented as a prefill measurement. One successful fixture proves load compatibility only; the MLX affine quantization and GGUF Q4_0 can transfer differently.

Decision: reject this adapter. Any next candidate needs a newly frozen independent evaluation set, stronger unknown/negation/compound performance, exact JNI grammar/context/tokenizer regression and actual phone lifecycle/memory/backend benchmarks before promotion. No Android adapter loading, phone fine-tuning, Snapdragon NPU training/inference or interpretability gain was established here. Recorded workspace 7.9 GiB is below 15 GiB; isolated dependency/venv/cache directories together are under 1 GiB even before shared-hardlink accounting.

The workspace grew to approximately 10 GiB when the 0.5 bundled APKs and build outputs were retained; it remains within the 15 GiB ceiling.
