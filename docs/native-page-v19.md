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

Physical JNI regression and actual 16 KB runtime checks are separate. Nothing
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
