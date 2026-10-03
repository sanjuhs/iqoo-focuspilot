# v19 native page-layout regression

This is prospective pre-event research. It replaces no historical protocol or
measurement. The target app is already installed separately by root. The harness
never installs it, never starts UI/voice/actions or changes permissions/settings.

The v19 native library changes only ELF linker layout: maximum and common page
sizes are both16384. APK/native source pins and ELF LOAD/RELRO alignment are
checked before phone mutation. Six openly seen requests are identical to the v17
unit JNI diagnostic, with capture only on Stop focus. Model semantics may be
refused safely; any wrong accepted full canonical slots fail. Historical313 checks
are historical: report the actual new runner count without assuming it in advance.

Both host getconf PAGE_SIZE and runner Os.sysconf must report4096. The run is a
Nothing4KiB regression. Static16KiB ELF alignment does not prove16KiB runtime,
iQOO/NPU, Office Kit, fresh accuracy or a causal interpretation result.

Freeze protocol, runner, harness, tests and test-only Gradle init script before
building or authorizing execution. The init script uses AGP finalizeDsl to select
only the dedicated runner/ directory containing PageNativeIsolationInstrumentation.java for androidTest and its exact runner;
main sources/Gradle/historical runners are untouched. Root builds and verifies
that the existing target APK hash remains unchanged and that the new test APK
contains no target class shadows, native/model assets or permissions. APK source
hashes are build attribution, not source recovered from DEX.

Proposed root-only test build, after source freeze:

```sh
./gradlew --offline --init-script ../native-page-phone/test-runner.gradle \
  -PdiagnosticRunner=unitNative assembleDebugAndroidTest
```

Keep the original test APK. Initial test replacement gets one45-second client
attempt. Native work has one global120-second cooperative deadline; the polled
host instrumentation deadline is150seconds. On unsafe/hung inference, force-stop
only the exact own target after checking its installed hash. The original-test
restore is one `adb install --no-streaming -r` with180-second client bound. Check
installed hash read-only after timeout; preserve client failure/status separately
from effective restoration. Never repeat install, instrumentation or inference.
Unknown target/test APKs are preserved.

The host compares all three named preference-store identities, paused/off
checkpoint, existing canonical model full SHA/bytes/inode/links, microphone and
notification runtime grants, and own services before/after. This does not cover
every Android setting or AppOp. Logs, native output and tensor values stay in new
ignored artifacts. Publish counts/hashes/limitations only. The15GB logical project
cap includes a conservative20MB probe reserve and no downloads/model copies.

Run the 19 pure boundary tests:

```sh
python3 -m unittest discover -s prototype/native-page-phone -p test_phone_probe.py
```

These tests execute no phone, model or test APK.
