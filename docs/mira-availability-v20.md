# Mira availability — v0.20 pre-event research

Source frozen at `81287b2b08ccedc050635b0b8a27154bed3b5d87`. This change lets an
explicitly chosen floating-companion session stay available through screen-off and
return its portrait after unlock. It does not promise uninterrupted availability
or display on the lock screen. Build, installation, publication and physical
behavior evidence for v20 are **pending**; root will add their final records.

Qwen3.5-0.8B Q4_0 remains selected. Model bytes, prompts, command validation and
the v19 native library are unchanged. Native SHA256 remains
`675f2142a2c35b9c0260dc43944db09c3bb570a63c9f49a27e47625f7b98152e`;
[v19 native evidence](native-page-v19.md) retains its own release attribution.
This is pre-event research, not eligible event-written competition code.

## Explicit choice and next Show

In **Mira while you use your phone**, **Keep Mira nearby after I unlock** defaults
off. Turning it on saves `miraReturnAfterUnlock` for the **next reviewed Show**;
it grants no permission and starts nothing. Overlay access, visible notifications,
unhidden artwork and an interactive unlocked phone are still required. Permission
settings return never starts Mira.

The Show review describes the selected session behavior and expires if the screen
loses foreground status, the selection changes or readiness changes. The service
captures `returnAfterUnlock` once for that session. Repeated Show cannot upgrade its
mode. Turning the preference off immediately stops the current floating service;
turning it back on requires another reviewed Show.

| Transition | Implemented behavior |
|---|---|
| Show with the choice off | Previous behavior: screen-off or lock stops the floating session; another Show is required. |
| Show with the choice on | Start one notification-visible foreground service and one portrait while unlocked. |
| Screen-off or observed lock | Detach the portrait, stop its animation and remove the companion's status/deadline refresh. Retain the same foreground service and Hide notification. |
| Unlock | Recheck permanent prerequisites, then actual interactive/unlocked state; restore the existing window and clamped position at most once. |
| Reviewed manual Show while waiting | Recover the same session if unlocked, including when an OEM omitted the unlock signal; preserve its existing mode. |
| Hide, artwork Hide, or preference off | End availability, remove notification/window/listeners and cancel any later restoration. Focus settings remain separate. |
| Process loss or Android stopping the service | No sticky, boot or automatic restart. The user must choose Show again. |

## Unlock and background boundaries

The existing service dynamically receives only screen-off and the protected
`ACTION_USER_PRESENT` signal. Android documents this signal as user presence after
wake/keyguard removal, and permits only the system to send it. The code still
checks current state rather than trusting delivery alone. Stale session leases,
an ending service and repeated signals cannot restore another window.
[Official USER_PRESENT contract](https://developer.android.com/reference/android/content/Intent#ACTION_USER_PRESENT).

Unlock reattaches an overlay belonging to an **already running**, explicitly
user-started `specialUse` foreground service. It does not start a new service or
activity from the unlock receiver. This distinction matters because Android15+
requires a currently visible overlay for the overlay-permission exemption when
starting a new foreground service from the background.
[Foreground-service start restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start).
The manifest describes the visual companion and locked idle availability under
the [special-use contract](https://developer.android.com/develop/background-work/services/fgs/service-types#special-use).

The dormant notification offers Hide and an explicit Ask Mira destination; Pause
is omitted while dormant. A stale Pause intent received while locked performs no
focus action. Opening Ask Mira still requires separate foreground controls for
recording, model loading/understanding and reviewed actions. Unlock does none of
those things.

## Independent focus and permission behavior

Dormant Mira performs no companion timer tick, countdown completion or usage
query. It does not start voice, inference, observation or a monitor. An already
chosen focus deadline or independently opted-in focus monitor remains independent
and may continue its existing work; “nothing in the app runs while locked” would
be inaccurate. Visible Mira retains its previous own-status/deadline behavior,
including existing-consent accounting when a due countdown completes.

Overlay revocation is watched and stops even a dormant session. Artwork Hide and
preference off stop it explicitly. Notification/channel readiness is rechecked on
unlock and explicit service commands. **There is no dormant permission poll:** a
channel block while fully dormant may remain undetected until that next signal.
A failed check stops availability rather than resurrecting it after a regrant.

## Verification and practical limits

Eight new isolated JVM fixtures pass for default-off behavior, explicit admission,
real-state unlock guards, permission loss/regrant, Hide and stale leases, duplicate
signals, frozen session mode and no implicit startup. They test the pure state
helper; they do not run WindowManager, a foreground service or a real unlock.
The complete v20 build/test counts and artifact identities are not yet recorded.

Physical portrait restoration, touch controls, notification behavior, lock/unlock
timing, process loss and OEM persistence remain unverified. Android can change an
overlay's visibility/placement; protected surfaces need not display it. Foreground
availability supplies no wake lock, battery exemption or 24/7 guarantee.
[Official overlay behavior](https://developer.android.com/reference/android/view/WindowManager.LayoutParams#TYPE_APPLICATION_OVERLAY)
and [Doze guidance](https://developer.android.com/training/monitoring-device-state/doze-standby).
