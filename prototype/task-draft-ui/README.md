# Unselected local task-draft UI

Pre-event research, prepared 2 October 2026. **This integration is not applied to
the selected Android app, installed on the phone, or published as a release.**
Qwen3.5-0.8B remains selected, but neither evaluated planning prompt is good enough
to promote: the first declined every benign task; the second met only 4/10 benign
prewritten criteria and included a nonsensical draft and a negation violation.
[Actual model evidence](../task-draft-confirm/README.md).

The preserved [integration patch](integration.patch) is against full source commit
`65f59a001405e2d5c351d03e938ee40ce5b4b174`. It was compiled before being removed from
the selected worktree. The [build record](build-check.json) binds the exact source,
patch and ignored compiled light APK: **156 JVM tests passed**, zero failures,
errors or skips; lint zero errors/76 warnings. [SDK package inspection](package-check.json)
verified version 12, signature, all six licenses, unchanged native library and
absence of INTERNET permission. These checks prove neither draft usefulness nor
actual Android UI/lifecycle behavior. The candidate APK remains ignored and was
never installed or released. The selected v0.11 app was restored and rebuilt with
143 passing JVM tests and lint zero errors/65 warnings.

## Intended flow, still unverified on Android

An explicit request from the private task guide opens the existing nonexported
local-model Activity. Its worker reuses the same pinned model/import path and
unchanged JNI library. A separate prompt/grammar proposes three inert steps;
the original command prompt, gate and activation path are not used for planning.
Generation requires actual EOS, a strict full-string schema and bounded Unicode
text, with no capture. An empty decline or incomplete result yields no plan.

The request binds a memory-only nonce, exact saved goal hash and revision, saved
plan revision/epoch and editable-text hash. Editor changes, goal changes and data
deletion invalidate it. Returned text must match those scopes, then pass separate
review before replacing only the editor buffer. Saving remains a later explicit
action, including existing replacement review. There is no clipboard, automatic
persistence, completion mark, focus/point change, speech or phone execution.
Generation still needs better semantic quality; a strict parser cannot establish it.

Cancellation/backgrounding discards previews and requests native cancellation;
model release is queued behind current work and controls block during release.
Returning requires an explicit reload. This applies to the model Activity's
existing command mode as well, and has not been tested for physical memory,
latency, interruptions or OEM lifecycle behavior. The approach follows the
[Android activity lifecycle](https://developer.android.com/guide/components/activities/activity-lifecycle)
and existing private [Activity result flow](https://developer.android.com/training/basics/intents/result).
No duplicate-memory or on-device outcome is claimed from source review.

## Reproduce only in a disposable research checkout

The patch is kept unapplied until a better model/contract passes a fresh quality
evaluation. The following checks source applicability; it does not approve the
generator or operate a phone:

```sh
git checkout 65f59a001405e2d5c351d03e938ee40ce5b4b174
git apply --check /absolute/path/to/integration.patch
git apply /absolute/path/to/integration.patch
NATIVE_BUILD_VARIANT=optimized ./scripts/build_android.sh
```

The caller supplies the patch from a later checkout. Use the generic variant on
ARM64 devices without the required DOTPROD/I8MM/FP16 CPU features. The normal build
needs the SDK/NDK and pinned native source described in the Android instructions;
it does not bundle/download a model by default. The patch removes automatic
overwriting of the Android Java adapter by the historical host fixture.

`git apply --check` succeeded against the restored source. Build-report hashes
refer to ignored `artifacts/unselected-ui-checks/`; source attribution and recorded
counts are not a byte-identical compilation guarantee for another machine.
All review/import, process recovery, speech, focus-state and runtime outcomes
remain physical test requirements. This scaffold is future work, not a completed
local assistant or eligible event-created submission.
