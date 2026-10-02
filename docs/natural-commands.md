# Natural commands — research v0.8 contract

Prepared 2 October 2026. The v0.8 source expands the **model-facing original-request validator**, retaining explicit proposal review. Qwen3.5-0.8B weights, the `LocalModel` prompt and native runtime are unchanged. The frozen-representation intent classifier remains unpromoted. The integrated build reports **119 passing JVM cases**, zero failures/errors/skips, zero lint errors and **59 warnings**. Both light/bundled APKs passed signature/native/model/license/permission inspection. The light APK installed on Nothing and its installed APK/private-model hashes match. Physical v0.8 command/countdown outcomes remain pending an unlocked own-app foreground. [Artifact identities](natural-commands-artifacts.json). The source-locked independent 100-request/50-family host evaluation is complete, with low supported-task coverage described below. Host tests and evaluation do not establish phone outcomes.

[Research v0.8](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.8)
publishes both APKs and the artifact manifest, bound to source
`a214bd7fc6ddd3cc3917d7a1f1aa9d854b7f3eb3`. All three GitHub asset sizes and
server SHA-256 digests match local files; earlier packages/video remain preserved.
This is delivery/identity evidence, not a physical result or submission acceptance.

## Whole-request validation

Qwen proposes an intent; `ModelCommandGate` then consumes one complete supported original request and validates its slots independently. A matching word inside unrelated prose is insufficient. Supported conversational wrappers such as “Please,” “Could you,” “Help me” and a Mira greeting may surround the bounded forms. Terminal punctuation and supported politeness suffixes are normalized; quoted statements, arbitrary additional prose and a second instruction do not become commands.

The gate offers only focus start/pause, focus status/nudge explanation, the approved Settings/Calculator/Clock apps and new Clock alarm/timer requests. An accepted proposal remains subject to explicit review and confirmation; native Clock controls final alarm/timer creation. This contract does not let a language-model prediction execute a tool automatically. If Qwen chooses a wrong intent, the gate can reject the original request; it does not guarantee Qwen selects the intended tool.

| Intended action | Supported examples when the model proposes the matching intent | Slots / review |
|---|---|---|
| Start/resume focus | “Help me focus”; “Get back to work”; “Focus for twenty-five minutes”; “Give me ten minutes of focus” | Without a duration, resume the paused countdown or start open-ended focus. A reviewed duration replaces the countdown while preserving historical total. |
| Pause focus | “Pause my focus session”; “Take a study break”; “Take a break from studying” | Pause focus; stop any already-active background focus monitor. No new monitor starts. |
| Focus explanation | “Show my focus status”; “How much focus time is left?”; “Why did Mira nudge me?” | Local focus information only; unrelated requests cannot become `EXPLAIN`. |
| Open approved app | “Bring up calculator”; “Take me to settings”; “Open the clock app” | One explicitly approved app, with outcome verification separate. |
| Clock timer | “Set a five-minute timer”; “Count down for thirty seconds” | One bounded duration; review seconds before requesting Clock. |
| Clock alarm | “Wake me at seven thirty PM”; “Set an alarm at seven oh five AM”; “Set an alarm at 19:30” | One exact hour/minute; review normalized clock time before requesting Clock. |

The Ask Mira UI supplies examples for focus, timer and alarm. They are **textual command forms**, not evidence that speech recognition works. The legacy dashboard quick-command parser remains a separate narrower fallback unless its own implementation is updated and verified; natural-form support documented here belongs to the model-facing gate.

## Deterministic number and duration slots

`CommandNumberWords` is a deterministic whole-slot English integer utility: **zero through 999**, with ordinary spaces/case and tens-to-ones hyphens such as “twenty-five.” Digit-only values up to 999 are supported by that utility; digits mixed with words are rejected. “And,” signed amounts, fractions, unsupported hyphens and non-English characters are not normalized into a number. Zero is a valid integer utility result, but it is not a valid timer/focus duration.

Focus and Clock timer slots accept one whole duration from **1 through 7200 seconds**. Direct digits can name up to 7200 seconds; English word amounts can name up to 999, with minute amounts limited to 120 by the duration ceiling. “One hundred twenty minutes” is permitted; “one hundred twenty-one minutes” exceeds the limit. Units are seconds/secs or minutes/mins. “One hour,” “one and a half minutes,” “minus five minutes,” two durations and trailing prose require clarification. The complete slot is consumed; an allowed substring does not discard an unsupported suffix.

Timed focus accounting, pause/resume/replacement, completed-start and paused process-recovery behavior remain governed by the [timer contract](timed-focus.md). No exact alarm, wake lock, boot receiver, permission request, microphone activation or monitor enablement is added by number parsing.

## Clock times

Colon times consume an entire `HH:MM` slot: without AM/PM they use 24-hour notation, with hour 0..23 and minute 00..59. With AM/PM, the hour must be 1..12 and is converted to 24-hour time for review.

Spoken/non-colon forms require explicit **AM or PM**. A whole hour may mean minute zero, including supported “o'clock” wording. Hour-plus-minute forms are accepted only when there is a unique valid full-slot split; numeric components and English number words are parsed, without leftover text. “Oh” or “zero” may lead a spoken one-through-nine minute: “seven oh five AM” becomes 07:05; “seven zero nine PM” becomes 19:09. Ambiguous splits, invalid minute/hour values, dates, fractions, extra times and omitted spoken meridian are rejected. “Set an alarm at seven thirty” therefore requires clarification.

This requests a **new** alarm or timer. Cancelling, snoozing, resetting or changing an existing Clock item remains unsupported. A successful proposal or launch is not proof that Clock created the intended item. Verify the receiving Clock state separately; physical Clock outcomes remain pending.

## Regression and evidence boundary

The v0.6 frozen 58-case report and v0.7 timer snapshot remain historical, unmodified evidence. Known-case repairs are post-test regressions. The separately authored 100-request/50-family evaluation was frozen before the candidate gate edit, and both candidate sources were locked before inference. The same unchanged Qwen outputs were passed to both Java gates; no request, prompt, label or gate repair occurred after results. Passing 119 JVM examples is separate logic evidence. [Protocol and reproduction](../prototype/command-v08-eval/README.md), [results/source identities](../prototype/command-v08-eval/results.json), [freeze manifest](../prototype/command-v08-eval/freeze-manifest.json).

### Actual frozen host result

All 100 Qwen responses met the schema and reached EOS. Raw semantic intent correctness was **29/100**: 29/40 supported intents were correct, while all 60 unsupported requests received a non-unknown model proposal. The original-request gate supplied the rejection, not model abstention. No phone actions ran.

| Exact original action/slot or rejection | Generated Qwen + v0.7 | Generated Qwen + v0.8 | Oracle domain + v0.7 | Oracle domain + v0.8 |
|---|---:|---:|---:|---:|
| Strict correct, including required abstention |64/100|72/100|68/100|79/100|
| Supported action/slots correct |9/40|12/40|14/40|19/40|
| Supported false abstentions |31/40|28/40|26/40|21/40|
| Unsupported false accepts |5/60|0/60|6/60|0/60|
| Wrong accepted proposals |5|0|6|0|

The generated-model path therefore handled **30% of supported requests**; overall accepted coverage was 12/100. Its increase from 9 to 12 supported successes comprises **nine gains and six regressions**, rather than a uniform improvement. Oracle domain proposals handled 19/40 supported requests, gaining 12 and losing 7 versus v0.7; the remaining 21 supported requests still abstained even with the intended domain supplied. Oracle results measure gate coverage/rejection, not Qwen semantic understanding.

English-number focus/alarm forms and Clock-launch wording improved. Some valid polite comma suffixes, focus/pause wrappers, a colon-time suffix and a Calculator application qualifier regressed; the oracle also lost a valid “lasting” timer form. Sources and requests were not repaired after observing these losses. Zero wrong accepts on this small synthetic set is not universal safety, and conservative rejection still leaves substantial usability work. These are host CPU observations, not Android/ASR/NPU latency or live execution proof.

v0.6 typed Start/Pause and alarm-cancellation observations cannot be attributed to v0.8. Its broader forms, numbers and Clock slots require fresh source-bound APK tests after build, an unlocked own-app foreground state and explicit review. Actual ASR/TTS, permissioned monitoring/OEM behavior, disconnected offline execution, iQOO NPU and Office Kit transfer remain separate incomplete gates. Keep the v0.3 concept video labelled historical; it does not demonstrate these command changes.

## Repeating the reviewed phone countdown

On an unlocked foreground app, paused with observation off, the existing authorized
own-app script can type a synthetic English duration and verify exact countdown
accounting. `--spoken-duration` tests typed wording; it does **not** invoke or prove
speech recognition. No Clock tool or OS permission is changed.

```sh
python3 scripts/phone_timed_focus.py --serial YOUR_DEVICE_SERIAL \
  --local-apk artifacts/focuspilot-research-v08-light.apk \
  --expected-apk-sha256 67a97acbbbeb47ec0c14aac6c3f926d2068c7016612d325ecb8607e8e517c5a3 \
  --source-commit a214bd7fc6ddd3cc3917d7a1f1aa9d854b7f3eb3 \
  --output artifacts/natural-commands-phone-repeat.json \
  --execute-reviewed-countdown --spoken-duration
```

The script will confirm only a matching 20-second reviewed proposal, verify automatic
pause and exactly 20,000 added checkpoint milliseconds with unchanged points and
observation, then attempt to leave focus paused. This is a planned physical check;
installation and host tests do not establish its outcome.
