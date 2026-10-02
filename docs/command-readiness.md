# Mira setup and command verification

Pre-event research, 2 October 2026. The 0.6 app adds **Set up Mira** beside the
companion controls. It reads current readiness and provides explicit routes to
Usage Access, notification settings, the app permission screen, Ask Mira and the
selector sandbox. It grants no permission and starts no session, observation,
microphone, inference or selector script. Readiness refreshes when returning from
Android settings. Optional features remain optional; typed commands and focus work
without them.

A private or bundled model's presence is distinguished from checksum verification:
the setup screen does not read 537 MiB of weights or initialize JNI. Ask Mira still
verifies the pinned artifact before loading. Speech-service availability is not
proof of an installed English model or recognized audio. The actual Speak flow
checks the local language only after the user requests voice access.

The original-request gate now requires explicit action phrasing and rejects wrong
creation proposals for cancel, stop, reset, snooze or other changes to existing
alarms/timers. Focus mentions, quotations, statements, conditions and multiple
independent requests require clarification. Supported examples include “Can you
help me start studying?”, “Could you stop my study session?”, “Set an alarm at
7:30 PM”, “Set a 5-minute timer” and “Open calculator”. Existing calendar alarms,
spoken-number slots and alarm/timer cancellation are still unsupported. This is
bounded lexical validation, not proof of semantic understanding. Focus remains
open-ended; a duration in its preview is disclosed as unsupported. The independent
[58-case evaluation](command-reliability.md) includes that failure rather than
counting it as a completed timed session.

## Actual phone evidence

93 integrated JVM tests pass and Android lint has zero errors. The light 0.6 APK
installed on Nothing A059/API36. Its setup screen reported Usage Access off,
notifications blocked and microphone off, without changing any permission or
starting a monitor. Readiness is an observed state, not permission enablement.

The unchanged local Qwen model then proposed Start and Pause; both were reviewed
and confirmed through the own-app UI. The private repository checkpoint changed
active → paused as expected. Observation remained off and the virtual balance
did not change. A subsequent “Cancel my alarm at 7:30” was wrongly classified as
`alarm` by Qwen and rejected by the independent gate; no Clock request ran.
The phone was left paused. [Exact phone report](command-readiness-phone.json)
contains artifact/model identities and the three measured request times. These
are typed synthetic tests, not ASR, disconnected-offline, Clock or NPU proof.

To repeat the benign action test, first leave FocusPilot in front, unlocked,
already paused with usage reading off. Provide the installed APK's complete hash
and the source revision that built it:

```sh
python3 scripts/phone_focus_actions.py --serial YOUR_DEVICE_SERIAL \
  --expected-apk-sha256 INSTALLED_APK_SHA256 --source-commit APK_SOURCE_COMMIT \
  --local-apk artifacts/YOUR_MATCHING_APK.apk \
  --output artifacts/focus-action-repeat.json --execute-reviewed-focus-test
```

The explicit flag authorizes starting and pausing the app's own focus session.
The script refuses a mismatched APK/model or an existing active/observed session,
never confirms an unexpected proposal and attempts to leave its test paused. It
reads only known focus/observation/virtual-point fields; it does not export goals,
other settings, label records or the event trail. Permissioned live monitoring,
offline recognized speech, a disconnected workflow and actual iQOO/Office Kit
execution remain separate required tests.

Android contracts: [runtime permissions](https://developer.android.com/training/permissions/requesting)
and [Settings actions](https://developer.android.com/reference/android/provider/Settings).
