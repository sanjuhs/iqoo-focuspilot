# Bounded Android accessibility proof

Pre-event research, 2 October 2026. This extension demonstrates the real Android accessibility action API against a separate **synthetic own-app Activity**. It is not general cross-app automation, a trained screen-action model, a CUA model deployment or a verified phone result. Existing reviewed Android intents remain a separate application path.

The proof has exactly two selector actions:

1. Click `dev.focuspilot.prototype:id/sandbox_open_task` with `AccessibilityNodeInfo.ACTION_CLICK`, then retrieve a fresh node and verify the synthetic task panel is visible.
2. Click `dev.focuspilot.prototype:id/sandbox_task_checkbox` with the same accessibility API, then retrieve a fresh node and verify it is checkable and checked.

`performAction` returning true is recorded only as an accepted click. The final success message is issued after both observed postconditions. There is no coordinate, gesture, global action, parent-click heuristic, direct `View.performClick`, arbitrary selector, text-based matching or fallback to a normal app click. Manual synthetic controls work as normal UI, but do not constitute an accessibility proof; every Arm tap resets the invented task before the service script starts.

## User authorization and boundaries

The user must manually enable **Mira · own-app automation proof** in Android Accessibility Settings, return to this screen, and tap **Arm one synthetic proof · five seconds**. Enabling the service alone does not arm or click anything. The screen offers Cancel and an explicit Disable service button. No ADB grant, secure-setting write, automatic enablement or other permission bypass is used.

A pure `SandboxActionGate` binds the arm to the exact package, `SandboxAutomationActivity` class, unique root ID and observed accessibility window ID. It expires after five seconds. Snapshots used to authorize/verify actions must be no older than 250 ms, and the service re-fetches the root and refreshes selected nodes. The script enforces the action order and allows one click per stage. Stale tokens cannot act on or cancel a newer arm. Missing/duplicate selectors, changed window, background, disconnected service, expiry or invalid postconditions produce no subsequent click or success claim.

Activity onPause or window-focus loss cancels the arm immediately, including when going to Settings, another screen or an overlay that takes focus. Service interruption, unbind or destruction also cancels. The executor checks the requester is foreground before root retrieval, checks the root package before traversal, requires the unique synthetic root, and rejects password nodes. It never reads event text, node text or content descriptions, and never retains audio, UI dumps or screenshots. The screen's bounded trace contains only fixed synthetic script outcomes; nothing is persisted or logged by this service.

The service XML and runtime event configuration filter `packageNames` to `dev.focuspilot.prototype`. Android's accessibility permission itself is broader than an app-created selector policy; package filtering is an event filter, not an OS capability sandbox. The implementation traverses only a matching own-package synthetic root and has no selector for another app or any product control. Ledger, monitor switches, model review/confirmation dialogs and real task data are excluded by the exact root/selector policy. This restriction is part of the implementation, not a claim that Android can grant only these two controls.

## Root application wiring contract

This slice adds new source/resource files only. Root integration owns the manifest and Main navigation:

```xml
<activity android:name=".SandboxAutomationActivity" android:exported="false" />
<service
    android:name=".SandboxAccessibilityService"
    android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
    android:exported="true"
    android:label="@string/sandbox_service_label">
    <intent-filter>
        <action android:name="android.accessibilityservice.AccessibilityService" />
    </intent-filter>
    <meta-data android:name="android.accessibilityservice"
        android:resource="@xml/sandbox_accessibility_service" />
</service>
```

The `BIND_ACCESSIBILITY_SERVICE` permission confines binding to Android. Configuration requests own-package window/content/click/selection events, `flagReportViewIds` and content retrieval, with gestures disabled. Unique resources are in `res/xml/sandbox_accessibility_service.xml` and `res/values/sandbox_resources.xml`. Android generates the real resource IDs; the isolated Java compilation stub is not an app resource.

Static helpers, called on the main thread:

| Helper | Meaning |
| --- | --- |
| `connected()` | Whether Android has connected this service instance; Settings remains the permission source of truth |
| `armedFor(SandboxAutomationActivity)` | Whether this specific foreground screen owns an active arm |
| `arm(SandboxAutomationActivity)` | Bind a new short-lived arm after the explicit button tap and current root check |
| `cancel(SandboxAutomationActivity)` | Cancel that request and queued work |
| `disableForUser(SandboxAutomationActivity)` | Disarm and call Android `disableSelf()` after the explicit Disable tap |

Weak references avoid retaining a closed Activity. The service performs no retrieval while unarmed and clears its queued work when cancelled or complete. The UI deliberately contains no text input, password field, real account data or real task controls.

## Verification and remaining phone gate

Eight isolated JVM tests pass: exactly ordered selector/postcondition flow; out-of-scope selectors; missing/cancelled/expired/reversed-time authorization; exact package/activity/root/window requirements; background/disconnect/stale snapshots; old-token isolation; malformed arm context; and postcondition denial without a preceding authorized click or after expiry. The Activity/service compiled with `javac` against the installed Android 36 SDK using a compilation-only resource stub. Resource XML parses successfully. No Gradle build, phone install or accessibility enablement was performed by this slice while other agents were editing.

Root should run a unified app build/test/lint, inspect service permission text, and record actual connected-device results after the user enables it. Verify unarmed does nothing; Arm completes both real node actions/postconditions; leaving the screen or tapping Cancel prevents later clicks; disabling/revoking the service prevents another arm; and manual checkbox changes never count as a service proof. Until those observations exist, label the feature **implemented own-app accessibility sandbox, phone execution unverified**.

Primary Android contracts: [accessibility service declaration/configuration](https://developer.android.com/guide/topics/ui/accessibility/service), [service lifecycle and active-window retrieval](https://developer.android.com/reference/android/accessibilityservice/AccessibilityService), and [node selectors, refresh and action APIs](https://developer.android.com/reference/android/view/accessibility/AccessibilityNodeInfo). These sources describe API capabilities; they do not validate this implementation's runtime result.
