# Vocabulary-only token preflight

`token_count.cpp` reads the actual already-rendered prompt bytes and counts them
with the selected native model's vocabulary. It creates no llama context, calls
neither `llama_decode` nor sampling/generation, and loads with `vocab_only=true`,
zero GPU layers and the same CPU-only device list as the pinned native capture.
This is a token-budget check, not inference/grammar/quality/latency evidence.

Compile using the existing pinned Homebrew headers/libraries, without downloads:

```sh
mkdir -p prototype/structured-eval/build
clang++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib \
  -Wl,-rpath,/opt/homebrew/lib prototype/structured-eval/token_count.cpp \
  -lllama -o prototype/structured-eval/build/token_count
```

Do not overwrite a previously frozen binary; choose an unused ignored output name
when repeating compilation. Record source/compiler/binary/header/library hashes
in the experiment freeze before execution. Reuse the model at
`models/qwen/Qwen3.5-0.8B-Q4_0.gguf`, SHA256
`57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`;
the caller must verify its existing identity and the same runtime pins used by
`qwen-balanced-native/run_capture.py`. No model copy is needed.

CLI: `token_count MODEL PROMPT_DIR`. The directory must contain only direct
regular `ID.txt` files (ASCII letters/digits/underscore/hyphen, 1–64 characters).
Pass distinct ignored directories for baseline and structured arms. Decode each
renderer TSV base64 field to its exact `ID.txt` bytes **without adding a newline**;
do not edit prompts, rerender a different template, or truncate oversized input.
The directory supports 1–200 prompts, at most12000 bytes per prompt/1MiB total,
no symlink entries/NULs. Counts are sorted by ID, not author order; the caller must
verify the exact ID set matches the corresponding source/rendered inventory.

Stdout is one JSON line per prompt with `id`, `token_count`,
`maximum_prompt_tokens:896`, `within_limit`, and explicit vocabulary/tokenizer
settings. Logs/errors go to stderr. Success exit0 requires **every** prompt fit
896 tokens; exit3 emits the complete measured inventory when any exceeds the
limit; exit2 indicates invalid input/load/tokenization and emits no count records.
Require exit0, exact IDs/count and all `within_limit:true` for **both arms** before
preparing inference. Context1024 reserves128 output tokens. Actual capture retains
its own token-budget check; this preflight does not replace it.

API provenance: the installed `/opt/homebrew/include/llama.h` declares
`llama_model_params.vocab_only` (load vocabulary without weights),
`llama_model_load_from_file`, `llama_model_get_vocab`, and `llama_tokenize`.
Its tokenizer contract returns a negative required-size count when capacity is
insufficient. The tool first queries capacity then independently tokenizes into
that capacity and requires the same positive count. Both `add_special` and
`parse_special` are **true**, matching existing `qwen-balanced-native/capture.cpp`.
The flags matter for the actual ChatML/no-thinking reserved controls.

Primary source references for the pinned vendored API lineage:
[llama.h](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/include/llama.h),
[model loading](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/src/llama-model.cpp).
These references explain the API; actual installed header/library byte identities
must remain separately pinned. No tokenizer counts or runtime pass are claimed by
source creation alone; root invokes the preflight after the source is frozen.
