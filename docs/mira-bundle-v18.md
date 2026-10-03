# Mira v0.18 — model inside the APK

The standalone research APK packages the selected Qwen3.5-0.8B Q4_0 GGUF inside
the current Mira command screen. Its size is **568,608,247 bytes**; SHA-256
`7ff98674b8e0213fc93f3adb3a736246ea283f8051e307d31758a92177cdc85b`.
It contains the pinned 563,036,064-byte model, SHA-256
`57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.

[Download the bundle](https://github.com/sanjuhs/iqoo-focuspilot/releases/download/research-v0.18/focuspilot-research-v018-mira-commands-bundled.apk)
· [Public packaging record](mira-commands-bundled-artifact-v18.json)
· [Verified server assets and tool identities](mira-bundle-publication-v18.json).

## What was verified

The existing stream packager used the exact frozen light APK and app source
`959f27a0721deca58dc45852e79759bc5a255539`. All **16 original non-signature ZIP
payloads** match SHA-256, including DEX, manifest, resources, native library and six
license assets. The only added payload is stored `assets/qwen35.gguf`.
SDK signing verification, identical public certificate and 16 KiB native alignment
pass. Qwen Apache-2.0 and llama.cpp/KleidiAI notices remain inside the APK.
Existing upstream model provenance is in [model evidence](on-device-model.md).

The original 208 JVM tests and lint results belong to the unchanged light build;
packaging executes no new app compilation, inference or phone operation. The
light variant remains installed. **v0.18 bundled installation, missing-model import,
model load and UI operation are unverified.** Historical v0.12 import and v0.17 CPU
measurements remain separately attributed; they do not establish current results.

Two obsolete local bundles were removed only after matching their complete hashes
and sizes to published GitHub assets. Their recovery URLs and identities remain
in the [cleanup record](recoverable-bundle-cleanup-v18.json). Temporary two-copy
packaging reserved a maximum project size of **14,471,951,584 bytes**. Final measured
logical storage was **13,902,082,489 bytes**, before this small documentation update,
under the 15 GB limit. No dependency or model download occurred.

## Repeat packaging

Use the existing pinned model and light APK. The script refuses changed inputs,
existing output files or a two-copy reservation above 15 GB. Confirm storage first;
do not duplicate large artifacts unnecessarily.

```sh
python3 scripts/package_bundled_apk.py \
  --light artifacts/focuspilot-research-v018-mira-commands-light.apk \
  --expected-light-sha256 dc40863819dd7fd12e93500cf279c343121a9c4af5a71986d5d4a29a7699f44d \
  --app-source-commit 959f27a0721deca58dc45852e79759bc5a255539 \
  --output artifacts/focuspilot-research-v018-mira-commands-bundled.apk \
  --report artifacts/mira-v18-bundled-packaging.json
```

Install only on compatible ARM64 hardware supporting DOTPROD/I8MM/FP16. Open
Ask Mira and load Qwen explicitly; existing code imports/verifies the bundled model
when its private file is missing. Loading does not evaluate a draft. Observation
and permissions remain opt-in; understood actions still require Review and Confirm.
Allow approximately 1.1 GiB for installed APK plus private model and additional
Android installation staging space. This is a planning allowance, not measured RAM.

The bundle intentionally includes public pretrained weights as a release asset;
weights remain outside Git. No credentials, private phone evidence or training
data are published. This remains pre-event research, with iQOO NPU, Office Kit,
live permissioned workflows and eligible accepted submission still pending.
