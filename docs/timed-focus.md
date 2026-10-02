# Timed focus — research v0.7

Prepared 2 October 2026. This is a pre-event research implementation. The integrated build passes 105 JVM tests and lint with zero errors and 59 warnings. Both signed debug APKs passed package/native/model/license checks; [artifact identities](timed-focus-artifacts.json) bind them to source `6bd4841b170be0445470eff9977133bc2accc8f6`. [Both APKs are published](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.7). Actual v0.7 phone countdown verification is pending: the light APK installed, but the own-app UI guard refused the unlocked-own-app foreground precondition before inference or action.

## Later v0.11 physical branch

The [current phone record](current-countdown-phone-v011.json) verifies one actual
reviewed typed 20-second countdown on the installed v0.11 light APK: active state,
automatic pause, exact 20,000 ms additional persisted time and paused/off/100 final
state. Reported native inference was 1,932 ms. The [first failed harness attempt](countdown-first-attempt-v011.json)
is preserved; polling now waits for asynchronous disk persistence. Other physical
branches below, including recovery, deep sleep, replacement and voice, remain
pending. The original v0.7 installation description above is historical.

## Choosing and reviewing a duration

The dashboard's **Focus for 25 minutes** button opens a review explaining that a new countdown replaces the current countdown while keeping accumulated focus time. Only the positive confirmation starts it; cancellation leaves the session unchanged. This quick action needs no model inference.

Ask Mira can propose a timed focus session from an explicit original request such as “Start focus for 17 minutes” or “Start a 30-second study session.” The independent original-request gate validates one duration written in digits, in seconds or minutes, from **1 second through 120 minutes inclusive**. The bounded proposal carries `seconds` (`1..7200`) and its review names the duration and replacement behavior. A plain start/resume proposal has `seconds == 0` and is reviewed separately. Model output alone does not start either kind of session.

Spoken-number durations, fractions, signed/negative amounts, hour units, calendar/clock deadlines, missing amounts, multiple durations and out-of-range durations require clarification. Negated, conditional, quoted, statement-like or compound requests remain subject to the original gates. An explicit duration that cannot be honored must not silently become open-ended focus. The focus-duration parser is separate from the existing Android Clock timer/alarm contracts.

A saved planned-focus target in **Choose your task & targets** remains an explanation input. Saving that target alone does not create a countdown. The 25-minute action or a reviewed timed proposal explicitly creates the timed session.

## Session behavior

| Transition | Required behavior |
|---|---|
| New timed start | Replace the old remaining duration with the reviewed duration; preserve accumulated historical active-focus time. |
| Pause before completion | Add active time spent so far and retain the unspent countdown; cancel the obsolete deadline callback. |
| Ordinary Start after that pause | Resume the retained remaining duration rather than restart the original full duration. |
| Countdown reaches zero | Finalize the session as completed and paused; count active time only through its logical deadline. |
| Ordinary Start after completion | Begin an open-ended session; preserve historical total and do not automatically repeat the completed countdown. |
| Process restart/recovery | Restore the last saved total/remaining/completion checkpoint **paused**; require explicit restart. Do not silently resume monitoring or infer unobserved time after process death. |

The dashboard distinguishes countdown remaining from total elapsed focus. Replacing or pausing a timed session does not erase prior total time. Finalizing a due session invalidates its observation scope and stops any already-running focus monitor; creating a countdown does not enable that monitor.

## Clock and Android scheduling limits

`FocusSession` accounts active time with monotonic `SystemClock.elapsedRealtime()`. That clock includes device sleep and is suitable for interval accounting, independently of wall-clock edits. [Official SystemClock documentation](https://developer.android.com/reference/android/os/SystemClock#elapsedRealtime()).

`FocusRepository` owns a main-thread `Handler` deadline callback. Pause, replacement and completion cancel old callbacks; generation/epoch checks prevent an obsolete callback from completing a newer session. Repository/UI ticks check whether the logical deadline is due before normal usage/nudge decisions. Usage accumulation is capped to the timed interval, and session elapsed time is capped at the countdown deadline, so a delayed callback does not grant extra timed focus or a post-deadline budget nudge.

A Handler callback uses **uptime**, which does not advance during deep sleep. Delivery can therefore be late when the phone sleeps, the main loop is busy, or the process cannot run. On a subsequent callback/tick, elapsed-realtime accounting determines completion, while the visible completed/paused transition can occur later than the logical deadline. A scheduled callback is also lost when its process/looper ends. [Official Handler `postDelayed` contract](https://developer.android.com/reference/android/os/Handler#postDelayed(java.lang.Runnable,%20long)). This is an in-process focus countdown, not a guarantee of an exact wake-up or a Clock alarm.

The feature adds no permission request, background monitor enablement, microphone activation, exact alarm, wake lock or boot receiver. It does not keep the screen awake or promise uninterrupted OEM background execution. Actual deep-sleep/process recovery and already-enabled monitor stopping remain separate physical verification cases.

## Bounded explanation requests

The `EXPLAIN` proposal is confined to an explicit request for focus status or a focus-nudge explanation. Examples include “Show my focus status” and “Why did Mira nudge me?” An unrelated request such as erasing a picture must not be accepted as an explanation merely because the model chose `explain`. Start/stop imperatives routed to `EXPLAIN` also require clarification rather than silently becoming status display. This is lexical request validation with an allowlist, not broad semantic understanding.

## Evidence and regression boundary

The original v0.6 [58-case frozen host evaluation](command-reliability.md) remains unchanged: its timed-focus-to-open-ended mismatch and unrelated erase-picture-to-explain mismatch are preserved as failures. These v0.7 repairs address **known post-test cases**. Passing their new regression tests cannot be presented as an independent held-out accuracy gain or substituted into the older 49/58 result.

Before claiming physical support, record a reviewed short countdown, its remaining display and exact paused/completed checkpoint; pause/resume and replacement preserving total; completed Start becoming open-ended; process recovery as paused; unsupported duration/EXPLAIN rejection; stale callback behavior and deadline-before-nudge logic. Preserve permission/monitor/microphone state and virtual balance. Tie actual outcomes to the installed APK/native/model hashes and source revision, and separate pure clock tests from phone, sleep and OEM evidence. The build totals above are verified; these broader physical cases remain pending.


## Repeating the physical countdown test

Unlock the phone, keep FocusPilot in front, and leave focus paused with observation
off. This explicitly authorized own-app test confirms only a matching, reviewed
20-second focus proposal, waits for automatic completion, verifies exactly 20,000
additional checkpoint milliseconds with unchanged points/observation, and attempts
to leave focus paused. It reads only named session/checkpoint fields and exports
synthetic commands/metrics; it grants no OS permissions.

```sh
python3 scripts/phone_timed_focus.py --serial YOUR_DEVICE_SERIAL \
  --local-apk artifacts/focuspilot-research-v011-light.apk \
  --expected-apk-sha256 6541ced715c48d8fd226e6dd2c8ff762485cda6901ded06e43bae4f97893adc2 \
  --source-commit e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a \
  --output artifacts/timed-focus-repeat.json --execute-reviewed-countdown
```

Seven new pure timer tests exercise deadline/accounting boundaries, pause/resume,
replacement/history and generation changes, completion-to-open-ended start,
monotonic rollback defense, paused checkpoint recovery, and invalid-duration
nonmutation/reset. Five new gate tests exercise duration slots and bounded
explanations. They verify logic, not real Android sleep, notifications or OEM
process survival. The unchanged 0.6 phone Start/Pause evidence remains separate.
