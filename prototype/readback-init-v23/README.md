# Readback-initialization research update — v23

This utility prepares one guarded v22-to-v23 own-app update for Ask Mira's
readback-initialization retry repair. Typing remains available. The repair does
not establish audible speech, an installed offline voice, or correct physical
speech callbacks; those checks remain pending. Qwen3.5-0.8B Q4_0 remains selected,
and this update retains the existing model/native bytes, permissions, reviewed
actions and Mira availability behavior. This is pre-event research, not eligible
event-created code or an accepted submission.

The new APK digest, artifact-record digest and build-source commit initially use
unique mandatory uppercase placeholders. `install_v23.py` rejects them before
any phone access. Root supplies the inspected light-build identities and commits
the installer before execution. The full artifact hash binds its source map;
every listed source must match both the current file and the exact build commit.
The map must include app Gradle, LocalModelActivity, ReadbackInitialization and
ReadbackInitializationTest. It may additionally include the actual app manifest
or Java sources/tests in the existing app package. Paths outside that scope are
refused. The utility does not
rebuild native code, load the model or perform inference.

```sh
python3 prototype/readback-init-v23/install_v23.py --execute-own-v23-update --serial YOUR_AUTHORIZED_PHONE_SERIAL
```

Run from the repository root. Before mutation, the recorded v22 public/private
baseline, exact installed v22 light APK and original test APK, three named
preference stores/checkpoint, pinned own-model identity, measured microphone and
notification grants, and absence of own services must agree. The checkpoint must
remain paused with observation off. The new light APK's native payload and full
artifact hash are checked locally. Unknown or changed state refuses the update.

There is one nonstreamed install with a 180-second client deadline, no retry,
wake, UI, force stop, uninstall/clear, permission change or model/action call.
An exclusive private attempt record is claimed before installation, retaining
failures and process loss without allowing a silent retry. Existing records
refuse execution. A client timeout stays a failed record; it does not assert the
eventual Android package state. Any later inspection is separately recorded and
read-only.

Raw protected snapshots stay in ignored
`artifacts/readback-init-phone-install-v23-private.json`. The scoped public
summary goes to `docs/readback-init-phone-install-v23.json`, without serial,
raw preferences, capture output or credentials. Success requires exact new
target identity, unchanged original test identity and complete protected-state
parity. Installation does not exercise ASR, readback initialization/retry,
speaker audibility, floating overlays, iQOO/NPU or Office Kit. Pure fixtures and
build evidence must retain their separate scope from physical verification.

The initial utility-preparation step performed no installation, build, tests or
device operations. Root filled the new build pins after freezing and inspecting
the actual artifact; completed installation has its separate public record.
