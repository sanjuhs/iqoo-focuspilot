# Selected v0.12 bundled-model import — actual phone proof

Verified 3 October 2026 on Nothing A059 / SM7635 / Android API36. This is
pre-event research. **Qwen3.5-0.8B Q4_0 remains the selected command model.**
The selected app source and APKs were unchanged; this test verifies their existing
missing-model import branch with retained app data, not a clean reinstall.

[Exact physical record](bundled-import-phone-v012.json) binds app source
`24f10b62a4a62c22ad6db90ac6339f29e2426dbd` and executed harness
`c0039c7a019f5afc632682273c5157f4953180ca` to the installed APK/model/native hashes.
Both completion and cleanup passed.

The metadata record is also backed up with
[research v0.12](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.12).
Its server size/digest matched, all fourteen prior asset identities stayed
unchanged, and the release tag retained the selected app source.
[Publication verification](bundled-import-publication-v012.json).

| Physical phase | Observed result |
| --- | --- |
| Preserve original private model | Renamed the verified single-link original into a unique backup; canonical model path absent. No model copy. |
| Replace light package with selected bundled APK | Installed with `adb install -r`; installed checksum matched. Canonical model remained absent until explicit Load. |
| Ask Mira → Load verified local model | Actual bundled-import status: **1,077 ms** copy plus SHA verification, then **2,320 ms** native CPU load. Independently verified the new 563,036,064-byte model, checksum and distinct inode. |
| Typed `Stop focus` | `pause_focus`, **REVIEW REQUIRED**, **9,534 ms** native CPU inference: 8,680 ms prefill / 854 ms decode. No action confirmed or executed; activation capture off. |
| Return and load again | Actual existing-private-model status; the imported model retained its exact inode, size, link count and SHA. |

The first typed request after import is one observation, distinct from the earlier
1.8–1.9-second timer observations. It establishes no latency distribution or cause
for the difference. The import status reports private-file hash time rounded to
0 ms because the streamed import had already verified SHA; the harness separately
hashed the complete private file after loading.

The model SHA-256 is
`57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.
The bundled APK SHA-256 is
`8fb78f14311ddec0c92357f95d13603a19b009a5add399a05e6284894c0ba088`.
The light APK SHA-256 is
`4ebd8097c9f3ff4a4cf5f12ecc5b80c1a8974b561c8e4ac733db1d77662583a0`.
[Full packaging/source manifest](guidance-readback-artifacts.json).

## Restoration and test boundaries

The harness force-stopped only FocusPilot before model moves. It held the exact
run-owned imported model, restored the original file (including inode), removed
only that verified test copy, and restored the selected light APK. Unique backup
and hold paths were absent afterward. All three named preference-store identities
matched semantically before/after; raw preferences were not published.

Focus remained paused, observation off, 100 virtual points and elapsed 97,331 ms.
Microphone and notification grants stayed denied; own focus-monitor and floating
services were absent. No app-data clear, uninstall, settings/grant action,
microphone use, action confirmation or separate GGUF transfer occurred. The APK
itself was transferred through ADB. Project preflight measured 13,821,970,510
logical bytes, including ignored files and Git, below the 15 GB cap; existing
shared SDK caches are excluded. Phone storage reserve exceeded 4 GB.

CPU execution is directly reported by the app. I8MM was observed in earlier
evidence for this pinned native library; a kernel log was not collected in this
run. No NPU, fully disconnected operation, ASR, general screen automation,
Office Kit, clean fresh-data installation or eligible submission is established.
This test is not depicted in the existing video.

## Reproduce without clearing user data

Use the exact selected v0.12 artifacts and an unlocked own MainActivity. Keep
focus paused, observation/own services off, and authored goal/guide/targets empty.
The pinned original model must already exist as a regular single-link file.
Commit the harness, keep the worktree clean, reserve at least 4 GB on the phone,
and choose an unused ignored output path.

```sh
python3 scripts/phone_bundled_import.py --serial YOUR_DEVICE_SERIAL \
  --light-apk artifacts/focuspilot-research-v012-feedback-light.apk \
  --bundled-apk artifacts/focuspilot-research-v012-feedback-bundled.apk \
  --output artifacts/bundled-import-repeat-v012.json \
  --execute-retained-data-import
```

The test refuses mismatched packages/model, active own services, unknown files,
symlinks, hard-linked originals and existing evidence. Restoration requires exact
protected-original and recorded import identities. Unexpected files are retained
and restoration marked incomplete rather than removed. Fifteen host boundary
tests cover ownership and foreground refusal; Python compilation also passed.
If interrupted, inspect the evidence and protected original before attempting
recovery; never clear app data or overwrite an unknown file.

A clean installation with fresh app data remains a separate consented test.
Actual user-granted voice/monitoring, iQOO NPU/Office Kit, event-code eligibility
and accepted submission remain full-goal requirements.
