# Staged compatible command integration

This is isolated pre-event integration preparation. Actual Android app sources,
installed files, model/native artifacts and phone permissions remain unchanged
by the staging work. Parent promotion requires the independent qualification and
code reviews, full app checks and package inspection. `source-manifest.json`
binds the unchanged selected/candidate sources and every reviewed staged file;
`integration.patch` provides the exact two Android source diffs.

Explicit Understand first tries the frozen deterministic recognizer. An accepted
fast request needs no loaded model, native preparation or inference and is labelled
FAST LOCAL. An unresolved request asks the user to manually load Qwen. Once loaded,
another explicit Understand may run one Qwen fallback. Loading alone never starts
inference. Voice only fills an editable draft. Every executable proposal still
needs Review, then Cancel or Confirm action.

The staged `LocalModel.generatePreparedUnitCommand` calls the exact frozen
Compatible renderer and GBNF, the current native handle, and the existing128-token
limit. Submitting-thread `prepareGeneration` and subsequent cancellation semantics
remain unchanged. Historical `generatePreparedIntent`, `renderPrompt`, and
`INTENT_GRAMMAR` remain available. No native implementation or candidate bytes change.

`CompatibleReviewState` privately owns the original request, actual raw model
response or null for fast, origin and epoch in an immutable snapshot. Review and
Confirm revalidate through `CompatibleActionRouter.review` and check foreground,
request epoch, current text, voice/model/audio idleness. Consume-before-execute
prevents duplicate confirmation. Typed edits, Cancel, voice entry and screen leave
clear pending provenance, confirmed readback text, old activation displays and the
review dialog. A stale worker releases only its own busy state and cannot publish
an old result. No proposal is persisted or restored after recreation.

Fast requests and refusals clear activation displays. Only accepted actual Qwen
inference displays its current native metrics and opt-in tensor observations.
Activations remain observational; no causal interpretation, NPU, Office Kit or
new phone performance claim follows. Explain maps to a reviewed local status
snapshot, not an answer to arbitrary questions or a past nudge-cause reconstruction.
Existing Android execute behavior is retained; its persisted pause reason is now
source-neutral so a fast action is not falsely attributed to a model.

Verified in isolation: all6 existing adapter tests and6 new ownership/lifecycle
tests pass. The staged integration plus baseline app dependencies compiles as47
Java sources using cached Android SDK35, generated debug `R.jar` and BuildConfig.
The first compile attempt omitted generated resources and is preserved in
`build/android-compile.log`; the corrected classpath passes in
`build/android-compile-with-cached-resources.log`. This source compilation is not
an APK/resource/lint/instrumentation or physical UI/action test. Actual voice,
rotation, worker cancellation, Android actions, phone latency and capture on the
new flow remain to be tested by the parent after integration.

For parent promotion after all approvals/checks, copy these exact manifest-pinned
sources into `prototype/android/app/src/main/java/dev/focuspilot/prototype/`:

```sh
cp prototype/compatible-app/build/staged/LocalModel.java prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java
cp prototype/compatible-app/build/staged/LocalModelActivity.java prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModelActivity.java
cp prototype/compatible-app/CompatibleActionRouter.java prototype/android/app/src/main/java/dev/focuspilot/prototype/CompatibleActionRouter.java
cp prototype/compatible-app/CompatibleReviewState.java prototype/android/app/src/main/java/dev/focuspilot/prototype/CompatibleReviewState.java
cp prototype/compatible-unit/CompatibleUnitCommand.java prototype/android/app/src/main/java/dev/focuspilot/prototype/CompatibleUnitCommand.java
cp prototype/unit-command/UnitCommand.java prototype/android/app/src/main/java/dev/focuspilot/prototype/UnitCommand.java
cp prototype/structured-command/StructuredCommand.java prototype/android/app/src/main/java/dev/focuspilot/prototype/StructuredCommand.java
cp prototype/compatible-app/CompatibleActionRouterTest.java prototype/android/app/src/test/java/dev/focuspilot/prototype/CompatibleActionRouterTest.java
cp prototype/compatible-app/CompatibleReviewStateTest.java prototype/android/app/src/test/java/dev/focuspilot/prototype/CompatibleReviewStateTest.java
```

Keep selected `ModelCommandGate`, `CommandNumberWords`, native, permission and
execution dependencies unchanged. The public patch is an alternative to the
first two copies, not an additional patch to apply after copying. The parent owns
version changes, Gradle app checks, packaging, promotion and phone verification.
