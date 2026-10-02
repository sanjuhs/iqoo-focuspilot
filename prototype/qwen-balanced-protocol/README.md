# Balanced local Qwen adapter: prospective experiment

The **design is locked before corpus creation**, training or candidate outputs,
following root's configuration confirmation on 3 October 2026. `design-lock.json`
binds this document and `protocol.json`. Sources, tools, runtime, tokenizer/base
artifacts and adapter conversion must be bound in separate immutable manifests
before execution; train/dev hashes precede training, and confirmation hashes
precede confirmation inference with the terminal candidate already fixed. Later
bindings cannot change these fixed choices. This is pre-event research. No success,
phone, NPU, fine-tuning quality or causal circuit is established.

Run one rank-4 LoRA candidate on the locally available Qwen3.5-0.8B MLX base,
targeting only final layer 23's three MLP projections. Keep the shipped original
command prompt, seven labels, tokenizer contract and independent full-request
Android gate. Train 112 author-written synthetic examples (16 per label), with a
separate 14-example diagnostic dev set (two per label). Exact and normalized overlap
must be absent, and independently authored confirmation families must not be used
as training templates. Authors are informed; this is not population/user evidence.

There are exactly **224 optimizer updates: two full epochs at batch size one**.
For each epoch, independently shuffle each class's 16 rows using the frozen seed
and interleave one row from each class in each of 16 rounds, shuffling class order
within each round. Every row occurs once per epoch. There are no dropped, packed,
truncated or dynamically repeated examples. The original prompt, completion and
EOS must fit 256 tokens; fail preflight otherwise, rather than changing the token
limit after seeing results. Pin RNG implementation and optimizer in trainer source.
Learning rate is constant 2e-4; rank 4, adapter scale 8 and dropout 0. The precise
meaning of MLX scale and its native conversion must be established before locking;
do not assume scale is PEFT alpha/rank without inspecting the actual runtime.

Mask prompt labels. For teacher-forced completion cross-entropy, weight every
completion token **intersecting the intent-value character span** 8, including
mixed value/delimiter tokens; other JSON tokens and terminal EOS receive 1.
Normalize each example's weighted sum by **its sum of supervised weights**.
Construct offsets from exact cumulative tokenizer decoding of each token prefix
against canonical ASCII JSON with an explicit EOS contract. Fail preflight on
non-prefix decoding or inconsistent offsets; never guess or truncate boundaries.
Record supervised counts/weight sums per label and each mixed-boundary token's
effect: punctuation inside a mixed token also receives weight8. This is label emphasis, not evidence that a particular
hidden unit represents an intent. Evaluate the terminal update-224 adapter only;
there is no dev/confirmation checkpoint, prompt, threshold or hyperparameter search.

Before training, run all 14 diagnostic dev requests on BOTH the unchanged MLX base
and unchanged native GGUF baseline. Preserve paired raw intent, canonical JSON/EOS,
complete gated action and slots, and timing. Disagreement is reported per case; it
does not establish identical base weights or license a claim that quantization is
the only difference. MLX architecture/tokenizer/weights and GGUF lineage remain
independently bound. Dev is too small to infer general equivalence.

After a single training run, compare the original native baseline and converted
adapter on exactly the same frozen **100 fresh confirmation requests**: 50 supported
(start 10, pause 8, alarm 8, timer 10, open app 6, explain 8) and 50 unknown.
Confirmation authors freeze requests, expectations, families and hashes after the
candidate/configuration lock and before inference. No examples, intermediate
outputs or score feedback reach the trainer for further selection. Native arms use
CPU, four threads, context 1024, maximum 128 generated tokens, capture off and fresh
KV/recurrent context for every request. Report model raw correctness separately
from original-request gate/action/slot correctness, all paired gains/losses,
per-intent denominators, abstentions, wrong accepted proposals, EOS and timing.
Exclude load/context setup from native total only if the actual runner separately
measures them; distinguish first-request from subsequent latency. No phone timing.

The candidate qualifies only if ALL prospective conditions in `protocol.json` pass:
at least four supported complete gains net, zero supported complete losses, no
supported class count decline, Pause at least baseline and at least 4/8, zero wrong
accepted proposals, raw unknown recall at least baseline, and all 100 outputs
canonical with EOS in both arms. A zero baseline unknown recall makes “no decline”
a weak floor: report its exact numerator, not “reliable rejection.” Finite-sample
zero wrong accepts is not a universal safety guarantee. Any incomplete request or
runtime failure fails qualification; retain failed results, with no checkpoint
retry or corpus replacement. A rerun for an independently demonstrated harness
failure is a separately named experiment, never an overwritten primary result.

The incremental disk reserve is 25 MB. Use existing dependencies and model weights,
with no paid cloud/API/download. **Do not write a full merged or dequantized model**.
Native comparison must reuse the existing pinned Q4_0 GGUF and apply only a small
converted LoRA adapter at runtime. Pin every exported tensor name, shape,
orientation, dtype and effective scaling; validate mapping/parity before native
comparison. If this route cannot be verified within reserve, record MLX-only
research as unpromoted and stop. Successful adapter load is not proof of MLX/native
numerical equivalence or Snapdragon NPU acceleration.

Even qualified host results cannot deploy automatically. Additional signed-package,
model/adapter-identity, actual phone runtime/performance, original-request review,
cancellation/lifecycle/permission and end-to-end voice/tool checks are required.
The installed research app and its original Qwen artifact remain selected meanwhile.
