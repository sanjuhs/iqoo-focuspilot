# Command-model activation experiment

Prepared 2 October 2026 after the user's Qwen/activation-inspector direction.
**Status: experiment protocol; no LLM causal result has been demonstrated.**
Selected command model: [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B),
using a pinned Q4_0 GGUF from [ggml-org](https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF).
The user has expanded the original 0.5B target. Prior 0.5B artifacts remain comparisons.
Qwen3.5 uses hybrid recurrent/attention state: reset recurrent and attention caches
between independent cases, record cache policy, and adapt tensor selection/patching
to the actual architecture rather than assuming Qwen2.5 tensor semantics.
Primary baseline runtime: pinned llama.cpp with a quantized GGUF and instrumented
CPU execution. [Upstream evaluation-callback example](https://github.com/ggml-org/llama.cpp/blob/master/examples/eval-callback/eval-callback.cpp)
shows how intermediate evaluation tensors can be observed. Capturing a tensor does
not establish its semantic meaning or a causal effect.

## The first narrow hypothesis

For a fixed prompt and closed command grammar, one candidate activation component
distinguishes `START_FOCUS` from `END_FOCUS`. Intervening on that component shifts
the command logits in the predicted direction without generally breaking inference.
This is a hypothesis to test, not a promised outcome.

Keep action execution disconnected while experimenting. The experiment emits a
proposed command, not an actual phone action. Command labels cannot bypass user
consent, argument validation or confirmation gates.

## Reproducible setup

Record model ID, full revision, GGUF SHA-256, quantization type, llama.cpp commit,
compiler/backend/device, prompt template, tokenizer and sampling settings. Fix the
context length (start with 512), candidate labels and slot schema. Use temperature
zero where supported and retain raw logits/outputs for every case. Weight size and
working-memory estimates are provisional until measured on the runtime/device.

The user-proposed 0.3–0.6 GB weight and 1–2 GB RAM figures are planning ranges,
not our benchmarks. Weight quantization, embeddings, KV cache, activation capture
and CPU/GPU memory behavior affect the actual footprint. Capture only selected
tensors/tokens; do not retain every activation for every layer in the mobile loop.

## Data and analysis split

Use matched command pairs: "start focus"/"stop focus", "begin a work session"/
"end my work session", and longer paraphrases with similar context. Add negatives,
negation, quoted instructions, multiple commands and UNKNOWN cases. Split whole
paraphrase families into discovery, selection/validation and untouched holdout.
Do not choose a component on the same cases used to report its success.

Baseline gate: commands and UNKNOWN decisions are sufficiently accurate for the
demo and malformed output abstains. An inaccurate 0.5B model is not rescued by an
interesting heatmap; fix the prompt/model or reduce scope first.

## Experiments

1. Capture selected residual/MLP/attention outputs on discovery pairs, keeping token
   positions and tensor names/shapes. Align semantic positions or use an explicit
   final decision-token position; different tokenization can create misleading differences.
2. Rank candidate components using discovery data, then freeze the candidate and
   intervention before evaluating holdout.
3. Ablate the component (zero/mean baseline) and measure change in start/end logit
   margin, command accuracy, UNKNOWN rate and grammar validity.
4. Patch from a matched opposite-command run into the recipient and measure whether
   the margin shifts in the predicted direction. Use matched shapes/positions.
5. Include controls: random components, same-class patches, unchanged/no-op patches,
   similar-magnitude perturbations and unrelated commands. Check global degradation.
6. Repeat on held-out wording and the exact deployed quantized artifact. Compare
   against higher precision only if that additional artifact fits the disk budget.
7. Repeat the bounded finding on the phone CPU runtime. Treat NPU deployment as a
   separate inference backend; fused graphs may not expose the same tensors or
   permit patching. Do not infer NPU interpretability from a CPU experiment.

An observation callback is not automatically a safe mutation API. Implement
interventions deliberately in an instrumented backend, synchronize access, and
check tensor layout/lifetime and numeric dtype. GPU/offloaded tensors may need a
copy and cannot be treated as CPU pointers. Add no-op parity tests before mutation.

## Inspector design

Show selected command, actual label probabilities/logit margins where available,
capture backend, chosen layer/tensor/token, a small activation comparison and the
intervention's measured effect. Keep a separate panel for the tiny positive-policy
feature contributions and gates. They explain different components.

All activation screens say **"Exploratory association"** until an intervention
passes the protocol. A completed narrow result can say: "Under this prompt and
artifact, intervention X changed the start/stop margin on N held-out commands."
Report failures and scope; do not call a component a universal "focus neuron".

## Target hardware

The user identifies a **16 GB iQOO 15** as the intended target. Official
[iQOO specifications](https://www.iqoo.com/en/products/param/iqoo-15) list 16 GB
variants, OriginOS 6, Android 16 and Snapdragon 8 Elite Gen 5. This confirms that
such a product variant exists, not that it is the event loaner or currently connected.
The connected development phone remains Nothing A059.

## Deliverables and go/no-go

- Checksummed model/runtime manifest; baseline command and abstention results.
- Sanitized activation traces, discovery protocol, frozen intervention and controls.
- Holdout results with sample count, accuracy/margin effects and latency overhead.
- Exact-artifact phone replication or an explicit laptop-only label.
- One readable demo sequence; no promised causal finding if the controls fail.

Keep the product usable without activation capture. Discovery tools belong in
developer mode; the ordinary user sees concise reasons and controls. If experiments
miss the deadline, show the independently verified tiny-policy explanations and
label command-model interpretation as ongoing research.
