# Mira Setup research update

This v21 change corrects Setup copy and companion-state labels for the existing
v20 return-after-unlock feature. Only SetupActivity and build version change;
service, permissions, Qwen/native runtime, command review and user data behavior
are unchanged. The rejected task-planning experiments are not integrated.

Build with the existing offline Android SDK/JDK17:

```sh
cd prototype/android
./gradlew --offline --no-daemon -PbundleLocalModel=false :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

`install_v21.py` is one guarded own-app v20-to-v21 replacement, not a generic
installer. It pins the new APK and artifact inspection, the prior protected
private record digest, exact installed old/test APKs, named preferences,
paused/off checkpoint, canonical model bytes/SHA/inode/links, two runtime grants
and absence of own monitor/floating services. One non-streamed 180-second attempt;
no retry, wake, UI, clear/uninstall, permission change, model load or phone action.
Raw state stays ignored; the public record states only its measured scope.

```sh
python3 prototype/mira-setup-status/install_v21.py --execute-own-v21-update --serial YOUR_AUTHORIZED_PHONE_SERIAL
```

Existing-output, changed source/artifact/baseline or unpaused state refuses before
mutation. A timeout/failure is preserved; follow-up may inspect state read-only,
not silently reinstall. Physical Setup, voice, monitoring, lock/unlock, iQOO/NPU,
Office Kit and event-code eligibility require separate evidence.
