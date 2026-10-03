# Private Qualcomm Android diagnostic

The separate pre-event Android probe is built from source
`304c102ff44ba30265a2dff76e3cbeefc5d2e85e`. Its package is
`dev.focuspilot.qualcomm.research`; it has no permissions, services, action
executor, observation, microphone, network access or bundled model. Running is
explicit and restricted to fixed synthetic requests. It leaves Mira separate.

Before referencing GenieX, both entry and worker check API 31+, an ARM64 process,
SM8750/SM8850 and actual 4,096-byte pages. The pinned vendor SDK's RELRO limitation
requires refusing other page sizes. Nothing SM7635 is refused, including SDK CPU
mode. Supported hardware remains unobserved; these gates are prerequisites.

The worker checks the selected Qwen3.5-0.8B Q4_0's full size/SHA and stable identity
in this package's own private files. It does not copy or download a model. An
explicit CPU/NPU/hybrid request is reported separately from verified execution;
all observations retain `npu_verified:false` until correlated operator evidence.

Independent review repaired rotation overlap and cancellation of pending results.
A process-wide lease blocks overlapping workers across Activity recreation. Native
cleanup exceptions or an undocumented nonzero destroy status quarantine the process
until restart. Raw return status is retained without inventing its semantics.
Twelve host fixture groups, two storage/cache tests and Java compilation against
the actual cached AAR and Android SDK pass; Android lifecycle behavior is untested.

The private APK is 93,017,281 bytes, SHA-256
`b256491c26d78fb72dce3d81d5a698d4ed77bf1491f44a342d3a93bac3535d60`.
Package/API/signature/ZIP checks pass, five license assets are retained and all 51
vendor shared-object payloads exactly match the pinned AAR. No SDK library is
patched. One offline build finishes without retry or dependency/model downloads.
Reserved effective storage is 13,460,750,594 bytes; polled peak is 12,963,600,193,
including positive new global-cache growth. Sampling does not establish a continuous
peak. [Public artifact evidence](geniex-private-probe-artifact.json).

No APK installation, model inference or NPU execution occurred. The SDK wrapper's
license does not establish redistribution rights for every bundled vendor binary;
the APK remains ignored and private. Original diagnostic source and public hashes
are backed up on GitHub. Actual iQOO execution, operator traces, Office Kit and
eligible accepted submission remain unfinished.

[Source and repeat procedure](../prototype/qualcomm-android/README.md) ·
[Vendor ELF inspection](geniex-aar-native-inspection.json).
