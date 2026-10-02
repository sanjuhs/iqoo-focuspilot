# Foreground Ask Mira entry — v0.15 research

Qwen3.5-0.8B Q4_0 remains the selected model. This pre-event prototype connects the
friendly floating companion and dashboard drafts to the existing foreground model
screen. It changes access, not model accuracy, backend placement or training.

## Interaction

Floating Mira's **Ask Mira** control and notification content tap open the local
command screen directly. Repeated entry requests reuse an existing assistant
instance through `CLEAR_TOP | SINGLE_TOP`; the overlay also uses `NEW_TASK` from
its service context. No command extra is supplied by the service. Android may
refuse background launches silently, so exception handling is not launch proof.
[Android activity security](https://developer.android.com/guide/components/activities/secure-bal),
[task and launch flags](https://developer.android.com/guide/components/activities/tasks-and-back-stack).

On the dashboard, type a request or finish a voice draft, then tap **Ask Mira with
this draft**. The new explicit internal Intent supplies editable text only. The
existing **Run command** shortcut remains available. The destination is not
exported. The handoff rejects null, blank, malformed, control-containing and
overlong text whole; it preserves accepted text exactly, up to 500 UTF-16 code
units. It never truncates a request into a different command.

On arrival, review/edit the draft, explicitly load the verified local model, tap
**Understand command locally**, then review any validated proposal. Entry invokes
no microphone, inference, action executor, permission request or model load.
The original prompt, whole-request validator, model and native library are retained.

Activity recreation saves bounded edits, including deliberate empty input, rather
than replaying the old Intent. Invalid edits are discarded whole. Model state,
predictions and active action reviews are not restored. Saved instance state is
transient Android-managed state, not a new app history or export.
[Android saved-state guidance](https://developer.android.com/guide/components/activities/activity-lifecycle#saras).

## Verification and remaining work

Seven new pure JVM checks cover exact text, Unicode/size boundaries, corrupt
state, edited/empty restoration and new versus recreated entry. All **165 app
JVM tests pass**; Android lint reports **zero errors and 64 warnings**. The signed
light APK passes package/native/version/permission/license inspection. Its native
library matches v0.14 exactly and it has no `INTERNET` permission.

App source: `c2062de0a46e3e16c2bf474a18f5b480d764daf5`. Light APK:
`artifacts/focuspilot-research-v015-entry-light.apk`, **5,513,492 bytes**, SHA-256
`09ead22560d9aef6bf21031690f173b7d4862662cd8a75eaec841cbbbeb06b76`.
Installation used `adb -s <authorized-device> install -r <light-apk>`, with pinned
v0.14 app/model, absent services and paused/off state checked first. No `-g`, data
clear, activity launch, screen wake, instrumentation or permission edit occurred.
Before/after checks verified the installed v0.15 APK and exact preservation of
three named preference-file identities, model hash/inode/size, two measured grants,
absent services and paused/off/100 points/97,331 ms. The original v0.13 reset test
APK stays installed unchanged. The installed app was not interacted with.

[Artifact and installation record](companion-entry-v15-artifacts.json) binds the
actual source, packaged bytes, report identities and sanitized installation record.
To reproduce the build with the existing SDK/model/runtime:

```sh
cd prototype/android
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew testDebugUnitTest assembleDebug lintDebug -PbundleLocalModel=false
```

Build outputs are not byte-for-byte reproducibility promises. Reinspect their
identities before installation; do not manufacture repeated upgrade proof by
downgrading a phone. The above state comparison is installation evidence only.

Physical draft handoff, rotation, repeated overlay entry, notification launch,
actual speech transcription and reviewed actions remain pending. The current
Nothing development phone is USB-authorized but asleep/locked, with microphone
and notification permissions off at the preceding check. Installation alone
establishes none of these interaction outcomes.

Floating mode still requires explicit Show and user-granted overlay/notification
permissions, and stops on screen-off or lock. It is not an always-listening or
unconditionally always-on assistant. Actual iQOO NPU, Office Kit and eligible
accepted submission remain full-project requirements.

Only a light v0.15 package is produced for this slice to retain storage headroom
under the strict 15 GB limit. It reuses the existing checksummed private model on
the development phone. The standalone bundled v0.14 package remains historical;
its interaction behavior must not be attributed to v0.15.
