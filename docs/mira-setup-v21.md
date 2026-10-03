# Mira Setup — v0.21 pre-event research

The signed **v21 light APK is installed on Nothing** with the checked protected
state unchanged. Source is `6027fa5c49f7ef4f383e0eeabb0694463c0eb77a`.
The user-selected **Qwen3.5-0.8B Q4_0 remains primary**. This update changes only
`SetupActivity` wording/status and the build version; permissions, companion
service, native runtime, command review and user-data behavior remain unchanged.
Rejected automatic task-planning experiments are not integrated.

## Behavior

Setup now describes the existing default-off **Keep Mira nearby after I unlock**
choice accurately: select it before the next reviewed Show to retain that session
through lock, with the portrait hidden until guarded restoration. With it off,
lock or screen-off ends the session. Hide ends availability while focus remains
separate. Setup distinguishes stopped, visible and waiting-for-unlock states.
These are source changes, not a physical UI or lock/unlock result.
[Existing v20 behavior and Android boundaries](mira-availability-v20.md).

## Completed evidence

- [Build/package inspection](mira-setup-artifact-v21.json): **216 JVM tests** pass
  across 29 suites; lint has zero errors/fatal findings and 79 warnings. The light
  APK is 5,562,744 bytes, SHA256
  `b6f623aebd148fe4cda0675ab171607689be51d5844ad8d3aabfcc1530a4c5e7`.
  Native bytes, seven permissions, public signing certificate and six license
  assets retain their verified identities; APK alignment passes.
- [Guarded installation](mira-setup-phone-install-v21.json): one non-streamed
  attempt succeeds in 1,756 ms, and the installed APK matches that SHA. Three
  named preference-store semantic identities, the paused/observation-off
  checkpoint, canonical model bytes/SHA/inode/links, microphone/notification
  grants, service absence and exact original test APK remain unchanged. The
  checkpoint stays paused, observation off, 100 virtual points and 97,331 ms.
  No UI, wake, permission change, model inference or phone action occurred.
- [Standalone bundle packaging](mira-setup-bundle-artifact-v21.json): the
  568,604,151-byte APK preserves all 16 original light payloads and adds only the
  pinned 563,036,064-byte model. Bundle SHA256 is
  `c7ddddc899ffeb11c9b0503319cae56c334d9b840b153bbae783c4dea75edb3e`.
  Model identity, signatures/certificate and alignment pass. This is packaging
  evidence only; current bundled installation/import/load remain unverified.

## Reproduction and limits

Use the [source/build/installer instructions](../prototype/mira-setup-status/README.md)
with the existing offline SDK and JDK17:

```sh
cd prototype/android
./gradlew --offline --no-daemon -PbundleLocalModel=false :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

The installer is a pinned, one-attempt v20-to-v21 update, requiring an explicitly
supplied authorized serial and matching baseline/artifact/source identities. Its
completed output records already exist, so rerunning refuses rather than
overwriting or retrying. Private snapshots remain ignored; public evidence states
only the protected scope measured above.

There is **no new model or UI execution proof** in this update. Actual CPU
measurements retain their [v19 attribution](native-page-v19.md). Physical Setup,
permitted voice/usage workflows, companion lock/unlock/OEM persistence, current
bundle import, actual iQOO/NPU and Office Kit still need separate evidence.
This is pre-event research; eligible event code and accepted submission remain
separate requirements.
