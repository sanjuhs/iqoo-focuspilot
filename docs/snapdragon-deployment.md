# Snapdragon deployment preparation

Research snapshot: 2 October 2026 IST. This is pre-event research, not eligible event-written
competition code. **The current verified phone backend is CPU/I8MM. GenieX integration,
iQOO hardware execution, NPU use and Office Kit pairing are unverified.**

## Selected route and compatibility

Reuse the selected **Qwen3.5-0.8B Q4_0 GGUF**, 563,036,064 bytes (~537MiB),
SHA256 `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.
Its pinned repository revision is `ggml-org/Qwen3.5-0.8B-GGUF@8fea620810c4afa23dd6443f999a48574c1611a3`.
This text-only artifact is already downloaded; do not fetch another community copy or
vision projector. Model license is Apache-2.0; keep its attribution.

Use GenieX `llama_cpp`, comparing explicit `cpu`, `npu`, and `hybrid`. The documented
`npu` alias selects HTP0; `hybrid` leaves device selection to per-tensor HTP/CPU
scheduling with all layers eligible for offload. CPU forces zero offloaded layers.
Neither all-layer offload nor an NPU alias proves every operation ran on the NPU.
Source: [platforms/runtimes](https://geniex.aihub.qualcomm.com/en/get-started/platforms).

| Device | Established facts | Deployment decision |
|---|---|---|
| iQOO15 target | Official product page lists Snapdragon 8 Elite Gen 5, OriginOS 6 / Android 16, 12/16 GB RAM | Expected SM8850; read actual phone properties before deployment |
| SM8850 / SM8750 | Listed as validated GenieX Android chipsets | Supported SDK trial target, actual model/operator execution still needs testing |
| Nothing A059 / SM7635 | Existing project phone facts and verified custom CPU JNI | Outside GenieX validated mobile list; retain existing CPU implementation |

Sources: [iQOO15 parameters](https://www.iqoo.com/in/products/param/iqoo15),
[Android prerequisites](https://geniex.aihub.qualcomm.com/en/run/android/install).
Absence from the validated list is not proof the chip cannot run any Hexagon code;
it means we lack vendor validation for this SDK/device combination. The SDK CPU
plugin source also handles available HTP sessions during model loading, so retain
our existing custom CPU fallback rather than assuming any SDK CPU setting works
on SM7635. [Pinned SDK model lifecycle](https://github.com/qualcomm/GenieX/blob/v0.7.0/sdk/plugins/llama_cpp/src/llm.cpp).

The Qualcomm mobile Qwen3.5 page currently says no supported mobile chipset while
also listing GalaxyS25/S26 in a generic supported-device section. Treat that as
inconsistent catalogue metadata, not an available iQOO binary. The selected route
is community GGUF, not an asserted precompiled QAIRT bundle. QAIRT requires a
per-chipset compiled bundle; it is NPU-only and cannot provide CPU fallback for
our GGUF. [Qwen mobile catalogue](https://aihub.qualcomm.com/mobile/models/qwen3_5_0_8b),
[models and quantization](https://geniex.aihub.qualcomm.com/en/models/supported).

## Version and storage gate

Official pages differ: install example 0.3.1, repository README 0.4.0, repository POM 0.3.5.
Maven Central metadata actually resolves latest/release **0.7.0** as of this research.
We pinned the published AAR, not one of those stale examples.

- [AAR](https://repo.maven.apache.org/maven2/com/qualcomm/qti/geniex-android/0.7.0/geniex-android-0.7.0.aar):82,287,634bytes (~78.5MiB), SHA256 `a29e88e31e12fd636a9dfa6760c61d04001ab91a932dbd5efe7b0a4335b9f883`.
- Published POM identifies BSD 3-Clause and Qualcomm Terms of Use. Bundled QAIRT/binary
  components retain their own terms; BSD for GenieX is not a blanket relicense.
- Archive inspected locally: arm64-v8a libraries total217,483,576bytes uncompressed;
  classes145,015bytes. Includes GGML Hexagon, HTPv73/v75/v79/v81, OpenCL, CPU and
  QAIRT libraries. Presence of those libraries establishes packaging, not execution.
- Current new laboratory storage:81MiB including one cached AAR; no duplicate weights.
  If integrated later, allow ~0.6GiB for AAR cache/unpacked packaging/build copies and
  up to0.54GiB for a model-manager copy on each target phone. Those are planning
  allowances, not measured peak RAM or total APK size.
- With the parent's remaining ~7.4 GB budget, this route fits provisionally. Recheck
  project/dependency totals before another runtime, model or Docker download.

Sources: [Maven metadata](https://repo.maven.apache.org/maven2/com/qualcomm/qti/geniex-android/maven-metadata.xml),
[published POM](https://repo.maven.apache.org/maven2/com/qualcomm/qti/geniex-android/0.7.0/geniex-android-0.7.0.pom),
[GenieX license](https://github.com/qualcomm/GenieX/blob/v0.7.0/LICENSE),
[NOTICE](https://github.com/qualcomm/GenieX/blob/v0.7.0/NOTICE),
[Qualcomm terms](https://www.qualcomm.com/site/terms-of-use).
Source main snapshot inspected: `073fcde2fba26d460713100c0989faa7755acdad`;
v0.7.0 tag API snapshot tree `c86fe489b69847a7945f3d02eacb393d02913018`.

## Isolated adapter and reproducible host checks

Original [Java research adapter](../prototype/qualcomm/src/dev/focuspilot/qualcomm/GenieXResearchProbe.java)
compiles against the actual 0.7.0 AAR and installed Android 36 / Java 17 without modifying
Mira's app or project dependencies. This is compile evidence only, not an APK or
hardware execution. It requires a worker thread, checks exact model size/hash,
applies the model chat template with thinking disabled, bounds output to 32 tokens,
records native profiling, and releases the native handle. Cancellation discards
results; SDK prefill cancellation latency remains untested. It never performs an action.

```sh
python3 prototype/qualcomm/compile_adapter.py
python3 -m unittest discover -s prototype/qualcomm -p 'test_*.py' -v
python3 prototype/qualcomm/preflight.py --properties prototype/qualcomm/device-properties.example.json
```

The last command uses illustrative properties. Replace them with actual observations;
no tool here queries a phone. Java adapter compile and six substantive preflight/
evidence tests passed. `npu_verified` remains false even for a complete evidence
fixture, because a human must correlate the actual hardware trace to the model run.
The [config](../prototype/qualcomm/deployment-config.json) pins SDK/model identity,
comparison settings and five synthetic requests, including known failure categories.

For a future separate Android probe flavor/module, add pinned
`implementation("com.qualcomm.qti:geniex-android:0.7.0")`, Kotlin runtime dependencies
and `jniLibs.useLegacyPackaging=true` so `nativeLibraryDir` contains real plugin files.
The published POM lists no transitive dependencies; upstream library build declares
AndroidX core and Kotlin coroutines. Resolve versions explicitly before runtime use.
The AAR manifest declares optional libadsprpc/libcdsprpc/libOpenCL and API27 minimum,
and does not add INTERNET. For our local-file probe no network permission is needed.
Do not merge two llama native stacks until symbol/lifecycle collisions are tested;
a separate probe APK is the initial isolation boundary.
[SDK build](https://github.com/qualcomm/GenieX/blob/v0.7.0/bindings/android/app/build.gradle.kts),
[initialization](https://github.com/qualcomm/GenieX/blob/v0.7.0/bindings/android/app/src/main/java/com/geniex/sdk/GenieXSdk.kt).

## Actual iQOO preflight and evidence procedure

1. On the selected unlocked iQOO, manually record model, Android/API, `ro.soc.model`,
   `ro.product.cpu.abi`, available private storage and firmware. Read-only commands
   for the operator: `adb -s SERIAL shell getprop ro.soc.model`, similarly
   `ro.product.cpu.abi` and `ro.build.version.sdk`. Never guess the serial or run
   against multiple connected phones. Store only nonprivate properties in JSON.
2. Reproduce the existing custom CPU baseline first. Transfer only the checksummed
   existing model to app-private storage using the existing safe procedure. For SDK
   model management, use `HubSource.LOCALFS` import rather than a new hub download;
   import may copy the weights. Keep final runtime from `ModelPaths.runtime_id`.
   The isolated adapter uses an already verified app-readable file directly.
3. Run each synthetic case in config with explicit CPU, then HTP0/NPU, then hybrid
   in fresh processes. Keep the application action executor disabled. Record model
   hash, SDK/plugin version, requested and resolved device, raw output, independent
   validator result, context/batch/thread/token counts, model load/TTFT/prefill/decode,
   PSS, battery/thermal state and failure. Label cold separately from repeated warm
   trials; do not compare captured timings to uninstrumented timings as if equivalent.
4. Capture only this research process's logs, e.g.
   `adb -s SERIAL logcat --pid=PID -v threadtime`; SDK uses `GenieXSdk`. No logcat
   clearing, broad account logs or unrelated screen captures are needed. Archive
   immutable synthetic-session IDs and trace checksums under ignored artifacts.
5. Capture completed HTP operator timings, not merely plugin-loaded, allocated-buffer
   or offloaded-layer messages. Upstream Hexagon profiling exposes
   `GGML_HEXAGON_PROFILE=1` and verbose ops; AAR binary inspection contains both
   `GGML_HEXAGON_PROFILE` and `GGML_HEXAGON_VERBOSE` plus `profile-op` marker.
   In an isolated diagnostic process set these before SDK initialization with
   `android.system.Os.setenv`, then verify that the actual build emits profiles.
   If release logging suppresses them, instrument a diagnostic build or use available
   vendor trace tooling; mark hardware proof blocked until captured.
6. Map executed operators/tensors to HTP and CPU, report unsupported/fallback coverage,
   and validate outputs against CPU within appropriate tolerance. Generic Android
   Perfetto CPU activity or vendor library presence alone cannot attribute NPU work.
   Sampling, tokenizer and command validation still use CPU; even an HTP-heavy
   model run must not be advertised as every app computation being NPU-only.
7. Feed the observed property JSON and manually reviewed trace summary into preflight
   `--evidence evidence.json`; required fields: selected model SHA256, matching SoC,
   runtime, requested compute, session ID, executed operator counts `{HTP,CPU}`,
   trace artifacts `{path,sha256}`, and `output_checked:true`. This checks completeness/
   hashes, not authenticity or semantic causation. Human review precedes any claim.
8. If unsupported operators, RPC access, plugin registration or model creation fail,
   preserve the error; use the existing explicit CPU fallback. No silent backend
   substitution, re-download or different-model benchmark presented as Qwen 0.8B.

Sources: [Android API](https://geniex.aihub.qualcomm.com/en/run/android/api-reference),
[pinned upstream Hexagon runtime/profiling](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/docs/backend/snapdragon/README.md),
[backend limitations](https://github.com/ggml-org/llama.cpp/blob/57fe1f07c3b6a1de3f4fff19098e2056a85275b7/docs/backend/snapdragon/developer.md).
Upstream profiling docs are a diagnostic lead; AAR markers support presence of
options, not successful profiling on our device. Operator support depends on the
packaged backend revision and tensor shape; Q4_0 does not establish full coverage.

## Office Kit, separately

The official global OriginOS page limits Office Kit to selected models/apps/regions,
requires x86Windows 10+ or macOS 10.14.6+, and points to
[official desktop download](https://pc.vivoglobal.com/). Native File Manager / Albums are
specifically required for mirrored drag-and-drop. Do not substitute generic ADB,
EasyShare migration, a homegrown socket or Android screen recording for Office Kit.
[Official compatibility notes](https://www.vivo.com/eu/originos).

Operational checklist once the actual device/account are available:

- Confirm Office Kit/Connection Center exists on that iQOO firmware and region;
  use official global desktop installer and record version. Account login and any
  service Terms remain user-operated; no installer/account actions were taken here.
- Follow the desktop app's actual connect prompt. An older official vivo community
  guide documents same vivo account, same network, Bluetooth and unlocked phone
  auto-connect; this is a setup lead, not a guarantee about current India/global
  firmware. QR/other paths should be documented only if observed in that build.
- Demonstrate a synthetic task note on phone, transfer a harmless test file through
  actual Office Kit into the laptop, and compare SHA256 before/after. Optionally mirror
  the native FileManager workflow. Capture only these consented synthetic screens.
- Record pairing/device labels with accounts masked, transfer outcome and app version;
  unplug the ADB cable during this proof. Keep cloud-sync versus local transfer
  evidence distinct. Repeat reconnect and cancellation; no generic private files.
- Office Kit transfers a task file to deeper laptop compute if needed; it is not an
  invented public RPC API. We have not found a verified programmable integration
  API, authenticated application flow, or current India-specific pairing sequence.

[Official vivo connection guide](https://bbs.vivo.com.cn/newbbs/thread/37465798).
No Office Kit installation, login, pairing or transfer has been performed.
