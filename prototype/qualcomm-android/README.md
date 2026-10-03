# Private GenieX Android research probe

Pre-event diagnostic shell, separately created from Mira. It is not eligible event
code and is not evidence of iQOO/NPU execution. No permissions, phone-action
executor, network, microphone, observation, service, receiver, model asset or
automatic model transfer. Its package is `dev.focuspilot.qualcomm.research`.
Do not publicly redistribute this APK until every vendor binary's terms are resolved.

The foreground screen offers an explicit CPU/NPU/hybrid request and five fixed
synthetic cases copied from `prototype/qualcomm/deployment-config.json`. It never
executes a generated label. Backend requests and SDK profiling are reported with
`npu_verified:false`; correlated executed-HTP operator traces and output review
are required for any later hardware claim. No automatic fallback occurs.

## Hardware and model prerequisites

The entry screen and worker independently require API31+, an actual arm64 process,
SM8750 or SM8850, and `Os.sysconf(_SC_PAGESIZE)==4096` **before any GenieXSdk
reference**. The pinned SDK's `GenieXSdk` static initializer loads `npu_jni`;
guarding only `sdk.init()` would be too late. Nothing A059/SM7635 is refused,
including SDK CPU mode. A supported SoC is only a prerequisite, not execution proof.

The AAR has 16KiB-aligned load segments, but vendor GNU_RELRO layouts have an
unresolved runtime risk on 16KiB-page Android devices. This probe conservatively
refuses other/unknown page sizes. An updated vendor binary or verified vendor fix
is required for those devices; this is a limitation of this pinned SDK, not a
general Qwen/NPU limitation. Actual iQOO page size and hardware remain unobserved.
See the [Android page-size guide](https://developer.android.com/guide/practices/page-sizes).

Prepare the selected GGUF separately in **this package's** private
`files/qwen35.gguf`; it cannot read Mira's private model. No Intent can choose its
path or trigger a run. The worker requires a regular non-symlink/non-hardlinked
file with 563,036,064 bytes and SHA256
`57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.
It checks full checksum and stable file identity before initialization and after
generation. Model preparation is separately authorized work, not part of this build.

One process-wide lease admits native create/generate/destroy, including across
Activity recreation; each Activity has an isolated result epoch. Cancellation is sticky for that
request; `stopStream` is dispatched once off the main thread with a handle ownership
lock. Backgrounding invalidates the result epoch and cancels work; returning never
reruns it. No replacement starts until the previous worker releases ownership.
Native load/prefill cancellation latency is unverified and may be slow. Cancellation
discards output; it does not claim immediate native interruption. Rotation starts an
empty screen and does not retain or revive the old request; explicit Run stays
blocked while the previous screen's worker still owns cleanup. A foreground-only
control refresh notices lease release without invoking the SDK. Cancel also
invalidates a result that has finished on the worker but awaits UI delivery.
The raw destroy return status is recorded, with vendor-code semantics explicitly
unverified. Nonzero status or a thrown destroy quarantines process-wide admission
until manual process restart; a zero status is not hardware-release proof.

## Dependencies and provenance

`dependencies.json` pins the cached GenieX0.7.0 AAR and Kotlin stdlib2.0.21,
coroutines core/android1.8.1 and annotations13.0 by full size/SHA. Java code calls
the SDK's synchronous JNI API. The AAR has Kotlin2.0 metadata, no AndroidX class
references and no embedded dependencies; no Kotlin Gradle plugin or AndroidX is
needed for this standard `android.app.Activity` shell. AGP8.12.1, Java17 and Android36
are already installed. Runtime compatibility remains untested until an allowed device run.

NativeProbe derives from our existing compile-only `GenieXResearchProbe.java`
(original SHA `ea7ab076f437dc411e30924a1a6f13703fb9b1eef2106053992abab9e1f39227`).
Vendor API sources are [GenieX v0.7.0](https://github.com/qualcomm/GenieX/tree/v0.7.0),
[SDK initialization](https://github.com/qualcomm/GenieX/blob/v0.7.0/bindings/android/app/src/main/java/com/geniex/sdk/GenieXSdk.kt),
[LICENSE](https://github.com/qualcomm/GenieX/blob/v0.7.0/LICENSE) and
[NOTICE](https://github.com/qualcomm/GenieX/blob/v0.7.0/NOTICE).
The model remains the existing Apache2 Qwen3.5-0.8B Q4_0 at pinned revision
`8fea620810c4afa23dd6443f999a48574c1611a3`; it is not redistributed in this APK.
Kotlin/coroutines use Apache2; annotations13 uses Apache2. SDK source licensing
does not establish rights to redistribute all AAR native components.

## Host checks and private build

Pure Java tests require only the existing JDK. They exercise twelve grouped
prerequisite, explicit-admission, cancellation, epoch, ownership and immutable-case
fixtures. They do not initialize the actual vendor SDK or prove Android outcomes.

```sh
mkdir -p prototype/qualcomm-android/build/host-tests
/opt/homebrew/opt/openjdk@17/bin/javac --release 17 \
  -d prototype/qualcomm-android/build/host-tests \
  prototype/qualcomm-android/app/src/main/java/dev/focuspilot/qualcomm/research/{HardwareGate,ProbeLifecycle,ProcessProbeOwner,SyntheticCases}.java \
  prototype/qualcomm-android/app/src/test/java/dev/focuspilot/qualcomm/research/HardwareAndLifecycleTest.java
/opt/homebrew/opt/openjdk@17/bin/java -cp prototype/qualcomm-android/build/host-tests \
  dev.focuspilot.qualcomm.research.HardwareAndLifecycleTest
python3 -m unittest discover -s prototype/qualcomm-android -p test_build_private.py
```

**Wait for independent source review and root storage authorization before building.**
After that, this one-shot helper uses the existing wrapper with `--offline`, no daemon
reuse and one worker. It requires the cached bytes, a 1.25GB additional reserve
(minimum1.075GB), the 15GB logical project limit, and new ignored output/report paths.
No models or dependencies are downloaded/copied. It measures positive global Gradle
cache growth without crediting unrelated deletions and polls storage/deadline during
the build. Polling is not continuous peak proof; reserve supplies conservative headroom.

```sh
python3 prototype/qualcomm-android/build_private.py --storage-approved
```

The helper verifies package/API bounds, zero manifest permissions, signatures,
ZIP alignment, no model assets, and **every** native library's exact AAR SHA parity.
`keepDebugSymbols` prevents Gradle stripping vendor bytes; legacy native packaging
provides real files under nativeLibraryDir for SDK plugin registration. No vendor
library is patched. The final private APK, build log, package/dependency/source hashes,
public signer digest and measured storage report live only in ignored `build/`.
No phone installation, model generation, public binary publication or NPU verification
is part of this helper.

Android source references: [Build.SOC_MODEL](https://developer.android.com/reference/android/os/Build#SOC_MODEL),
[Os.sysconf](https://developer.android.com/reference/android/system/Os#sysconf(int)),
[Activity.onStop](https://developer.android.com/reference/android/app/Activity#onStop()),
[native-library packaging](https://developer.android.com/guide/topics/manifest/application-element#extractNativeLibs).
