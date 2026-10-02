# Reviewed Calculator and Clock launches on Nothing

Pre-event research, 3 October 2026. The installed v0.11 app and pinned
Qwen3.5-0.8B Q4_0 completed two typed commands through inference, independent
validation, review, Cancel, a second review and Confirm. Foreground component
metadata then verified the requested app package. No target UI hierarchy,
screenshot, alarm contents or calculator contents were inspected.

| Typed request | Model / gate | Native inference | Observed target |
| --- | --- | ---: | --- |
| Open calculator | `open_app` / review required | 2,016 ms | `com.google.android.calculator/com.android.calculator2.Calculator` |
| Open clock | `open_app` / review required | 1,998 ms | `com.google.android.deskclock/com.android.deskclock.DeskClock` |

For each request, Cancel retained FocusPilot's model screen with the original
paused/off checkpoint and grants. Confirm was tapped only after the exact original
request and approved launch preview were checked. Target foreground identity was
observed twice, then the harness returned directly to FocusPilot's main screen.
Calculator matched its pre-resolved component exactly. Clock resolved to
`com.google.android.deskclock/com.android.deskclock.HandleApiCalls` and redirected
within the same package to `DeskClock`; the record preserves the class difference.

Clock uses `ACTION_SHOW_ALARMS`, not a set-alarm or set-timer request. These results
prove approved app launches for two typed commands. **They do not prove alarm
creation, timer creation, voice transcription, arbitrary screen automation or
completion of an external workflow.** No external UI control was touched.

Final state remained focus paused, observation off, 100 virtual points and
57,331 ms elapsed. Microphone and notification grants stayed false, and no own
focus-monitor service record was present. A separate fresh-screen inspection after
returning through Main with CLEAR_TOP found Review disabled; this does not test a
stale dialog in a surviving activity. Native timings cover reported CPU
prefill/decoding, not the complete request or app-launch delay.

[Current phone record and source/APK/model/native identities](app-launch-phone-v011.json).
No app, prompt, model or native source changed for this test. The full selected app
commit is `e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a`; installed byte identities
match the existing [release manifest](task-guide-artifacts.json).

## Retained failed attempt

The first harness compared a full Android activity name with its shorthand form
and stopped at Cancel validation. It recorded no action confirmation/execution,
and final cleanup verified the original checkpoint and grants. Cancellation was
not marked verified by that report. The corrected comparison expands a shorthand
class within its own package, preserving package and activity identity.

[First-attempt report](app-launch-first-attempt-v011.json),
[exact executed reference source](../prototype/app-launch-phone-proof/reference/phone_app_launch_first_attempt.py).
The current successful result does not rewrite that failed attempt.

## Repeat

Unlock FocusPilot, keep it in front with focus paused and usage reading off, and
use the matching installed APK. This command explicitly authorizes the two benign
review confirmations and changes which app is foreground; it creates no alarm or
timer and grants no permission:

```sh
python3 scripts/phone_app_launch.py \
  --serial YOUR_SERIAL \
  --local-apk artifacts/focuspilot-research-v011-light.apk \
  --output artifacts/app-launch-phone-v011.json \
  --execute-reviewed-app-launches
```

The harness resolves each intent before confirmation and stops if there is no
unique usable target. It never replaces a rejected model proposal with a manually
chosen intent. After confirmation it reads only foreground component metadata;
own-app UI operations resume after the explicit return to FocusPilot. Keep private
captures, unrelated app contents and credentials out of Git.
