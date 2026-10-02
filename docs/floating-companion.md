# Floating Mira — research v0.9

Prepared 2 October 2026. The source implements an optional visual companion beside other apps. **Actual overlay appearance, permission grants, notification actions and lifecycle behavior have not been physically verified.** This is pre-event research. Source/build identities are recorded below; physical verification remains pending. Prior command/video evidence does not prove this new service.

## Explicit permission and Show

The dashboard and **Set up Mira** offer a reviewed route to Android's **Display over other apps** settings. The user chooses whether to grant FocusPilot this special permission. Returning from settings only refreshes readiness; it never starts the overlay.

**Show floating Mira** is a separate reviewed action from the resumed dashboard. Before confirming and again in the service, the implementation requires:

- Actual `Settings.canDrawOverlays` permission.
- Available app notifications, Android 13+ notification permission when applicable, and an unblocked **Floating Mira controls** channel.
- Companion artwork unhidden in preferences.
- Interactive, unlocked phone state.

If a prerequisite changes or the dashboard is no longer resumed, Show expires and the user must review it again. A positive confirmation starts the service; cancellation starts nothing. The permission-granted state alone is never a persisted “always show” preference.

The manifest declares `SYSTEM_ALERT_WINDOW` and a nonexported `FloatingCompanionService` with foreground-service type `specialUse` and its explicit visual-companion subtype. Android requires user approval for application overlays; declaration alone is insufficient. [Official overlay settings contract](https://developer.android.com/reference/android/provider/Settings#canDrawOverlays(android.content.Context)). The foreground-service type/permission/subtype follow the [official special-use contract](https://developer.android.com/develop/background-work/services/fgs/service-types#special-use); this declaration is not physical runtime evidence.

## Small window and controls

The implemented **176×250dp** touchable `TYPE_APPLICATION_OVERLAY` contains original Mira artwork, own focus status/countdown and three controls. Dragging the portrait moves it within current usable display bounds; portrait clicks have no action, so a drag does not open an app or pause focus. The source computes bounds using system bar, cutout and keyboard insets; actual placement behavior remains untested. If the available area cannot contain the complete controls, the implementation stops rather than silently shrinking controls away.

| Control or transition | Implementation behavior |
|---|---|
| Open | Only an explicit user tap opens FocusPilot. The portrait, permission return and service ticks do not launch activities. Android may refuse the launch; the app/notification remains the fallback. |
| Hide, dashboard Hide or notification Hide | Remove the floating window, callbacks/listeners and foreground notification; leave focus and observation settings unchanged. |
| Hide companion artwork preference | Stop the floating service; Show stays blocked until artwork is unhidden and the user explicitly reviews Show again. |
| Pause focus, window or notification | Explicitly pause the existing own focus session and stop its monitor. The floating companion may remain visible with paused status. |
| Screen off or phone locked | Screen-off receiver and repeated unlocked/interactive checks stop the floating service. Visibility/cleanup timing remains subject to Android scheduling. Focus is not paused merely by hiding Mira. |
| Overlay permission revoked or notifications/channel blocked | Permission watcher/readiness checks stop and clean up the service. No automatic permission request or restart occurs. |
| Process loss, Android window removal or unsuitable display | Remove/abandon the window and stop as applicable. Service is `START_NOT_STICKY`; Show must be chosen again. |

The notification exposes Open, Pause focus and Hide. A one-second main-thread refresh reads the app's own session status and can finalize an already-due own countdown. Reduced motion honors the saved preference and system animator availability; paused artwork is static. Animation does not imply model inference or active listening.

Android can change overlay position, size or visibility, and places these windows below critical system windows. This feature does not promise display over every app, secure surface or locked screen. [Official window-type behavior](https://developer.android.com/reference/android/view/WindowManager.LayoutParams#TYPE_APPLICATION_OVERLAY).

## Observation, model and lifecycle boundaries

Show starts no new observation session, microphone, screen capture, UI-text reading or Qwen inference. The overlay does not run the monitor's continuous usage/nudge tick or discover the foreground app. **Existing-consent accounting still applies:** countdown completion and an explicit Pause delegate to the repository, which may flush selected-app usage for an already-consented observed session. Consequently, “no usage query ever” would be inaccurate. Hide itself does not flush/pause the session or change its observation setting.

Qwen3.5 weights, prompt and native inference are unchanged. Opening FocusPilot does not itself issue an LLM request. There is no boot receiver, sticky restart, wake lock, exact alarm, silent voice recorder or automatic background activity launch. Starting a visible floating service does not establish actual background-monitor permission or OEM process persistence. Screen-off stops this companion rather than keeping a screen or CPU awake. [Existing timer limitations](timed-focus.md).

## Physical proof checklist — pending

Use only synthetic own-app focus state and consented harmless test screens. The operator must explicitly grant any overlay/notification access through Android; do not use ADB grants. Keep private captures ignored and mask unrelated screens/accounts.

| Test | Required observable proof |
|---|---|
| Permission off / blocked notification / hidden artwork / locked phone | Show refuses; no overlay/service/inference/voice/monitor starts and focus checkpoint remains unchanged. |
| Permission settings return | Returning with a grant refreshes readiness but leaves the floating service stopped until reviewed Show. |
| Show review cancel / expired callback | Nothing starts; no stale dialog can start after the Activity pauses or a prerequisite is removed. |
| Actual Show | Exactly one small window and the correct own notification appear; current artwork/status and all controls are usable. Record initial focus/observation/points. |
| Drag and app interaction | Bounds remain usable through orientation and keyboard changes; dragging does not Open/Pause, and no claim is made about taps on unrelated app surfaces without observing them. |
| Open | A user tap returns to FocusPilot; no auto-launch happens during idle refresh or permission return. |
| Hide / artwork hide / notification Hide | Window and service notification disappear; callbacks/listeners stop; focus and observation stay as before except a separately due countdown. |
| Pause focus | Reviewed explicit control changes the checkpoint to paused and stops any already-enabled monitor; points/permission state stay unchanged. |
| Screen off / lock / permission revoke / notification block | Window/service clean up without pausing a still-running focus session; no automatic resurrection on unlock/regrant. Android/OEM scheduling delay is recorded. |
| Timer due / process recovery | Countdown accounting stays bounded; delayed completion is disclosed. Recovery stays paused and floating Show remains explicit. |
| Android refusal or process loss | Failure leaves no stranded window/notification and offers the in-app fallback; no 24/7 persistence claim. |

Tie the observations to exact installed APK, source and native/model identities, Android/SoC and prerequisite states. Source review, pure movement tests or a service label cannot certify WindowManager behavior. Physical tests must distinguish Hide from Pause focus and account for an independently due timer before asserting unchanged session state.

## Source and build evidence

Root reported the frozen source revision **`6e483aaf9e42889794ed77c272b8a912539cfc7c`**, **127 Android JVM tests passing** with zero failures/errors/skips, and lint with **zero errors, 62 warnings**. Both signed version-9 APKs were inspected for the native library, bundled model where applicable, all six license notices and packaged permissions. `SYSTEM_ALERT_WINDOW` is present; `INTERNET` is absent. These are build/package observations, not an overlay test.

| APK | Bytes | SHA-256 |
|---|---:|---|
| Light | 5,773,312 | `e57a9c57cec2bbac6e9912b2772c5fe155f14c4e09b55a69fc272e5fc91f9b61` |
| Bundled | 568,809,488 | `fa5fad50862b4d9eef9bcbbc07d6ab0425699b6bf7e37ceef3150b63fc61c693` |

Light APK installation and installed APK/private-model hash identity were verified; the session was already paused, observation off and points 100. No OS permissions changed. The phone is asleep and FocusPilot is not focused; no permission interaction, overlay appearance, drag, notification action or lifecycle transition has been physically tested for this release. Device-specific prerequisite states and exact physical observations remain **pending**. Actual overlay success is **unverified**; voice, continuous live monitoring, NPU and Office Kit remain separate verification gates.

[Machine-readable package and installation identities](floating-companion-artifacts.json).

## Published checkpoint

The [0.9 prerelease](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.9)
publishes light/bundled APKs and the immutable artifact manifest. All three server
sizes/SHA-256 digests match local files; tag resolves to the stated app-source SHA.
After installation, one display-wake/own-app-launch attempt failed the unlocked
own-app foreground guard. No UI was inspected, permissions granted or commands
executed; subsequent metadata still reported asleep/not-own-app-focused. Actual
overlay and countdown tests remain pending. This later attempt is separate from
the initial installation snapshot.

