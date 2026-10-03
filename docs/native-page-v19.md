# Native page-layout repair — v0.19 research

Qwen3.5-0.8B Q4_0 remains selected. This update adds the linker's
`common-page-size=16384` alongside `max-page-size=16384` and increments the
research app version. Model, prompts, parser, executor, permissions and companion
UI source are unchanged.

The previous native library passed load-segment and APK ZIP alignment checks but
failed the separate GNU_RELRO end check: `0x4eb000 % 0x4000 = 0x3000`.
Earlier v18 "16 KiB alignment" records cover those narrower checks; they do not
establish full runtime compatibility. [Android's official guidance](https://developer.android.com/guide/practices/page-sizes#check-relro)
requires checking RELRO as well as load/packaging alignment and actual runtime behavior.

The rebuilt ELF ends RELRO at `0x4ec000`, correctly divisible by 16,384. All three
load segments retain 16,384-byte alignment and matching offset/address congruence.
RELRO, BIND_NOW, the five JNI exports and four system-library dependencies remain
present. Native SHA-256 is
`675f2142a2c35b9c0260dc43944db09c3bb570a63c9f49a27e47625f7b98152e`.
The cached optimized build uses disconnected FetchContent, with no downloads.

Source commit: `caaf5246116ad02144f8bf0a4d92ce8053bf8275`.
The signed light APK is 5,562,644 bytes, SHA-256
`cb6cdb68af46d5cd476b5fca00a9375223ce69ad7bde5b641cd3ec0c8daef13f`.
All 208 JVM tests pass; lint has zero errors/fatal findings and 79 warnings.
APK version/signature, ZIP alignment, exact new native payload and six unchanged
license assets pass inspection. No weights or INTERNET permission are present.
[Artifact/build evidence](native-page-artifact-v19.json).

One guarded update installs this light APK on Nothing, retaining the original
test package and exact protected preferences/checkpoint/model/grant/service snapshot.
No UI, wake, inference or permission grant occurs during the update.
[Installation evidence](native-page-phone-install-v19.json).

The physical JNI regression below verifies the rebuilt library on 4 KB pages.
Actual 16 KB runtime checks remain separate. Nothing
uses 4,096-byte pages; a successful test there cannot establish 16 KB execution,
iQOO NPU use or Office Kit integration. Historical inference results keep their
original APK attribution. This remains pre-event research.

The separately pinned GenieX SDK has 40 Android ARM64 libraries whose load
alignment passes, but 30 fail the RELRO-end check. Its private diagnostic refuses
non-4 KB page sizes before SDK initialization; vendor binaries are retained intact.
Eleven Hexagon ELF32 payloads are recorded separately from ARM64 libraries.
[SDK inspection](geniex-aar-native-inspection.json).

## Standalone packaging

The v19 bundle contains the exact light app payload plus the pinned stored Qwen
asset. It is 568,604,151 bytes, SHA-256
`4a0e7f5c2b45daa9f8c39f0cebb8f6a6456e7c42a0ecfa0b7853fc87e9385d73`.
All 16 app-payload identities, signing, ZIP alignment, model size/checksum and six
license assets pass. Reserved two-copy peak was 12,776,135,271 logical project
bytes, below 15 GB. No bundle installation/import or inference occurs during
packaging. Public weights are intentionally included in the APK and remain outside
Git. [Packaging evidence](native-page-bundle-artifact-v19.json).

Published [research v0.19](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.19); all five server asset sizes/digests and exact source tag are checked in the [publication record](native-page-publication-v19.json).

## Actual Nothing CPU regression

Frozen protocol/runner/harness source:
`4ee8f59dad7dcedc65712fddcb967ef5357e40c6`. Nineteen pure harness boundary
tests pass. One test-only APK build leaves both frozen and build-output target APK
hashes unchanged; manifest/signature/DEX inspection verifies the dedicated runner
with no target class shadow, native/model payload or permissions. An initial inode
preflight used the wrong working directory and failed while Gradle completed; the
corrected check verified unchanged target bytes before any phone execution. No
rebuild or runtime retry followed. The failure is preserved in the private build
record and flagged in the public result.

One network-denied native run completes all six already-seen requests and **313
runtime checks**. All raw intent/argument slots match the frozen examples; each
checked-model, fast-local and product route accepts the five supported proposals
and refuses the negated request, with zero wrong accepts. These are a narrow runtime
regression, not fresh command accuracy. Forced Qwen inference occurs even when
the fast local route accepts; no proposal is executed.

Model load is 2,361.472 ms. First uncaptured native request is 3,854.957 ms; later
uncaptured requests are 3,318.174–4,625.598 ms. Captured Pause is 3,480.150 ms. Four
finite 1,024-wide tensor observations remain descriptive activation capture, not
a causal finding. A direct IPv4 TCP socket-creation denial precedes model access;
no whole-device disconnection claim is made.

The original test restores once through non-streamed install in 988.563 ms, without
client timeout or retry. Target APK, three named preference stores/checkpoint,
canonical model identity, microphone/notification grants and own service absence
match the pre-run snapshot. Model closure and actual 4,096-byte pages are verified.
No UI, voice, phone action or permission change occurs.
[Source-bound result and limitations](native-page-phone-result-v19.json).

After verified public recovery cleanup and deletion of regenerable SDK native
intermediate copies, logical project size is 9,463,892,530 bytes; including the
218,929,328 bytes of new global-cache growth gives 9,682,821,858. Current APKs,
private SDK package/logs, all light/test/native proof artifacts and selected model
remain retained. [Published bundle recovery](recoverable-bundle-cleanup-v19.json) ·
[SDK intermediate recovery](regenerable-sdk-native-cleanup-v19.json).
