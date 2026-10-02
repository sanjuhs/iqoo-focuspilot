# One balanced Qwen3.5 training candidate

Pre-event synthetic local research only. The prospective experiment design lives
in `../qwen-balanced-protocol/`. Reuse the existing offline MLX weights and Python
environment; no base merge, downloads, cloud job, user data or phone operations.

`run.py` validates pinned source/data/runtime manifests and refuses existing output
directories. It provides separate preflight, pretraining dev, fixed terminal224
training and final MLX confirmation phases. `policy.py` controls complete balanced
exposure and tokenizer-verified intent-value loss weights. Seven pure boundary
tests cover full per-row/per-class exposure, exact token spans, prompt masking and
complete evaluation denominators. Generated datasets, phase records, parameters
and prediction text stay under ignored `build/` directories.

MLX confirmation uses a seven-answer token trie and requires an actual final EOS
token. This is a separate decoder from native GBNF. Native confirmation must load
the small adapter with the exact existing Q4_0 GGUF and retain full-request slot
validation. MLX/native lineage and quantization differences remain unresolved.

`export.py` maps only three final-block MLP A/B matrix pairs, with effective scale
8 (`alpha32/rank4`, runtime adapter scale1). Each target gets a deterministic
matrix transpose/scale check. This proves a narrow conversion contract, not full
model equivalence or useful transfer. The fixed adapter stays unpromoted unless
the prospective native criteria and later real-phone requirements pass.

Before execution, freeze all source, protocol, model/tokenizer/dependency, corpus
and native tool identities. Complete both original-base dev arms before training.
Use separate immutable manifests to bind those dev results and then the terminal
adapter. Keep failed attempts intact. Neither loss reduction nor JSON validity is
semantic training success or mechanistic interpretability.

`execute.py` runs one owned offline child with a 600-second training / 240-second
other-phase deadline, recording and reaping that PID on timeout. Exclusive phase
claims prevent a second attempt through an aliased output. `score_mlx.py` uses the
locked native Java gate for full-slot MLX diagnostics without new inference.
External native/MLX runtime bytes and source dependencies are independently pinned.
The optimizer is MLX Adam, constant lr0.0002, betas(0.9,0.999), eps1e-8 and explicit
bias correction enabled; this binding supplements the immutable design protocol.
