# Storage-bounded research APK packaging

`scripts/package_bundled_apk.py` packages an already-built, frozen light APK with the existing pinned Qwen3.5-0.8B Q4_0 GGUF. It does not build, download, install or run the app. Payload hashes and signing verification establish artifact identity; they do not prove phone behavior or event eligibility.

Before any packaging file is written, the script validates the caller's full light APK hash and source commit, the fixed model hash/563036064-byte size, a valid single-signer light APK, available local tools/debug keystore, a new ignored output path and an ignored new report path. It measures all logical project file bytes, including ignored files and `.git`, without following symlinks. It requires `project bytes + 2 × (light bytes + model bytes + 256 KiB) ≤ 15,000,000,000` and enough disk free bytes. Run one packaging job at a time with the workspace otherwise stable: the preflight reservation is an estimate, not a filesystem quota or a lock against unrelated concurrent writers. If that estimate cannot fit, the script aborts before writing.

The script streams all original ZIP payloads, removes only direct `META-INF/MANIFEST.MF` and direct `.SF/.RSA/.DSA/.EC` signature entries, and adds `assets/qwen35.gguf` as `ZIP_STORED`. It checks duplicate names and rejects an already-bundled input. The temporary clone is byte-bounded. Official `zipalign -P 16 4` produces the aligned copy; the unaligned copy is deleted before signing. The SDK then signs the aligned file in place with the existing standard Android debug key and v4 signing disabled. This leaves room for the signer's temporary copy and avoids a third full APK. No private key material is read or printed by Python.

Alignment must precede signing, because changing the archive afterward invalidates its signature; the 16 KiB option aligns uncompressed native libraries. See the official [zipalign documentation](https://developer.android.com/tools/zipalign) and [apksigner documentation](https://developer.android.com/tools/apksigner). SDK Build Tools 36.0.0 under `~/Library/Android/sdk/build-tools/` and `~/.android/debug.keystore` are the defaults. The key alias/password are only the standard development defaults; this is not release-key management.

After signing, the script verifies the final signature, exact public certificate SHA-256 parity with the light APK, 16 KiB native/4-byte archive alignment, every original non-signature entry hash, and the only added non-signature entry's model size/hash/storage method. It checks input hashes again and publishes only after all checks pass. Publication uses a same-filesystem hardlink followed by unlink: this gives rename semantics without copying or overwriting an output created during a race. Failed temporary work is removed; an existing artifact is never replaced.

Run the three small synthetic ZIP/signature-filter/storage regressions without packaging an APK:

```sh
python3 scripts/package_bundled_apk.py --self-test
```

For the frozen v0.11 research input:

```sh
python3 scripts/package_bundled_apk.py \
  --light artifacts/focuspilot-research-v011-light.apk \
  --output artifacts/focuspilot-research-v011-bundled.apk \
  --expected-light-sha256 6541ced715c48d8fd226e6dd2c8ff762485cda6901ded06e43bae4f97893adc2 \
  --app-source-commit e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a \
  --report artifacts/bundled-apk-v011.json
```

The JSON report records byte identities, public signer digest, entry parity, SDK/source hashes, caller-supplied build attribution and the two-copy peak estimate. The source commit attribution is not a repeated compilation proof. Native signatures/license/resource payloads are preserved by hash, while ZIP metadata/alignment and APK signatures are necessarily rebuilt. No previous APK is overwritten. Preserve the report separately; no runtime, NPU, ASR, Office Kit, live task completion or accepted submission follows from packaging.

The authorized v0.11 run completed with exit 0: bundled bytes `568538615`, SHA-256 `ba135c616c0cb49edd67988b25a746da1adb7c5fe7a86ea0e4b135c5b35fb795`. All 16 original payload entries matched; the pinned stored GGUF was the only addition. Both verified public signer digests matched, and final alignment passed. The executed packager SHA was `31114c061941a8f8afab038f997c267f1a56c393137bb5794c9d7fc720605104`.

Measured logical project bytes before this run were `11922624618`; its reserved two-copy peak estimate was `13060832410` bytes (about 13.061 GB). This measures the chosen streaming workflow after the light build, not an alternative Gradle bundle build. The streaming path minimizes additional model working copies; these measurements do not establish that normal Gradle bundling necessarily exceeds the 15 GB allowance. No additional bundle run is needed to publish this verified artifact.

The exact executed source is preserved at commit `8ce82be896dd6e6a8511525a03bbc2dd811395dc`.
The later source adds a pre-write check that APK output is ignored by Git. Three
small self-tests pass for that version; the already verified bundle was not rebuilt.
The immutable artifact manifest records the executed source, rather than claiming
the newer guard was used to generate historical bytes.
