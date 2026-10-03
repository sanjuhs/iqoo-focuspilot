# Voice-session research update — v22

This utility prepares one guarded v21-to-v22 own-app update. Qwen3.5-0.8B Q4_0
remains selected; model/native bytes, permissions, command meanings, explicit
action review and persistent-Mira behavior are retained. It is pre-event research,
not eligible event-created code or an accepted submission.

The dashboard draft cannot be manually edited during active voice capture, and
its listening instructions name the actual **Push to talk / stop** button. Final
transcription stays an editable draft; cancellation/error/timeout preserves the
existing text. Ask Mira's readback changes bind done/error/stop callbacks to the
active utterance/token so stale speech events cannot replace current status.
These are lifecycle/UI repairs, not proof of ASR, speaker audibility, installed
offline-language availability or disconnected OS speech behavior. Root's pure
fixtures/build checks have their separate scope; physical verification is pending.

The new APK digest, artifact-record digest and build-source commit initially use
mandatory uppercase placeholders. `install_v22.py` rejects them before any phone
access. Root supplies real identities only after the actual light build and
artifact inspection, then commits the installer before execution. Current source
bytes and Git snapshot bytes must both match the artifact's five pinned files:
Gradle, MainActivity, LocalModelActivity, ReadbackState and its tests. No native
rebuild, model load or inference is part of this installer.

```sh
python3 prototype/voice-session-v22/install_v22.py --execute-own-v22-update --serial YOUR_AUTHORIZED_PHONE_SERIAL
```

Run from the repository root. The previous v21 public/private records, exact old
APK and original test APK, named preference stores/checkpoint, pinned own model
identity, measured microphone/notification grants and absence of own services
must agree before mutation. The new light/native payload and full artifact hash
are checked locally. Unknown or changed state refuses the update.

There is one nonstreamed install with a 180-second client deadline, no retry,
wake, UI, force stop, uninstall/clear, permission change or model/action call.
An exclusive private attempt record is created before installation; existing
records refuse execution. Failures/timeouts remain recorded, without pretending
the eventual Android package result is known. Follow-up inspection is a separate
read-only operation, never automatic reinstallation.

Raw snapshots stay in ignored `artifacts/voice-session-phone-install-v22-private.json`.
Only measured, scoped summary data goes to `docs/voice-session-phone-install-v22.json`;
serial, raw preference contents, capture output and credentials are not published.
Original test identity and the complete named protected snapshot must remain
exact after a successful update. This does not exercise voice, speech callbacks,
floating overlays, current bundled import, iQOO/NPU or Office Kit.
