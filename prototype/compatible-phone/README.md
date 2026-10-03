# Compatible command Android replay preparation

Pre-event research utility. This replays **already-seen** synthetic host requests
and captured replies through the target APK's pure Java classes. It performs no
new Qwen inference, voice recognition, UI operation, permission grant, singleton,
service or phone action. Installed parser parity is distinct from phone-model
accuracy, responsiveness and the real reviewed assistant workflow.

`CompatibleReplayInstrumentation.java` makes 300 comparisons: 100 fixtures through
baseline `ModelCommandGate`, checked `CompatibleUnitCommand`, and the fast-local
then checked-model pipeline. Every comparison checks exact canonical argument
slots, acceptance and actual origin. Eight separate in-memory
`CompatibleReviewState`/`CompatibleActionRouter` checks cover edits, cancellation,
epoch ownership, replacement, foreground/busy gating, single consumption and
copied model slots. These checks return proposals only; they do not confirm or
execute Android tools. Report schema: `focuspilot.compatible_android_replay.v1`,
`replay_checks=300`, `review_checks=8`, `checks=308`, all failed IDs empty on success.

The source must be compiled against the actual target app classes. It reads its
own test-package asset, `compatible-fixtures.json`. It verifies that asset against
an explicit `fixture_sha256` instrumentation argument, the test and target package
contexts, process name and target UID. Source attribution uses frozen Java hashes
and the exact signed APK identity. The local APK inspector verifies the seven
helpers are defined exactly once in target DEX and not defined by the test APK;
DEX does not expose recoverable original Java-source hashes.

## Generate ignored assets

The generator calls no validators or models. It reads fixed manual gold, actual
terminal native captures and host decision expectations already bound by the
independent actual-result audit. It verifies input hashes, capture EOS, inventory,
raw-response equality, canonical slot types and origins. It never derives gold
from a target proposal. Raw requests/responses stay in ignored generated assets,
ignored test APKs and ignored local records. Do not publish the test APK or asset.

Run from the repository root, using **new, nonexisting ignored outputs**:

```sh
python3 prototype/compatible-phone/generate_fixtures.py \
  --gold prototype/compatible-data/build/confirmation.jsonl \
  --baseline prototype/unit-native/build/compatible-fresh-baseline-capture \
  --candidate prototype/unit-native/build/compatible-fresh-candidate-capture \
  --scoring prototype/compatible-eval/build/scoring \
  --audit prototype/compatible-unit/fresh-result-audit.json \
  --router-source prototype/android/app/src/main/java/dev/focuspilot/prototype/CompatibleActionRouter.java \
  --review-source prototype/android/app/src/main/java/dev/focuspilot/prototype/CompatibleReviewState.java \
  --output prototype/android/app/build/generated/compatibleReplayFixtures/compatible-fixtures.json \
  --manifest prototype/compatible-phone/build/asset-manifest.json
```

Root owns copying/registering the runner, Android build source sets and APK builds.
Register only `dev.focuspilot.prototype.CompatibleReplayInstrumentation` in the
selected diagnostic test build. This utility does not modify Gradle or app sources.
The root-generated asset is 58,167 bytes, SHA256
`e482515b40ac547a6ab60302273302641b99c51418f037f3af599efe15de2370`.
It binds the original fresh execution commit
`5fa9909415af50a599116a60943002830ad7c3c2`; that host attribution differs from the
later app integration/source commit supplied to the phone harness.

## Later explicitly authorized physical replay

`phone_replay.py` requires exact clean committed source and full frozen light/test
APK hashes. It rebuilds expected asset bytes **without model/gate calls** from the
independently audited inputs before mutation, verifying current generator source,
input identities, audited result binding, source pins and the whole asset manifest.
It verifies local signatures and shared public certificate, v17 package/version,
fixed runner/target manifest, no test permissions/native payload, no Internet or
GGUF target payload, selected native hash, target-only helper DEX ownership, asset
hash and 16 KiB alignment. All named protected preferences, focus checkpoint,
runtime microphone/notification grants, private model byte/inode/hash identity and
absence of the two companion/monitor services are compared exactly before/after.

It only accepts the installed v0.16 light SHA256
`1f25c95c7d58d354e55675778fc975768049495be20a05bf7cd709423b73218b`,
paused focus/observation off, the pinned retained model, no services, and original
test APK SHA256
`b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b`.
It does not wake/unlock the phone, navigate UI, grant permissions, load/infer the
model or execute actions. The instrumentation process has a 45-second host bound.
The protected snapshot reads the private model hash; the instrumentation itself
does not access the model file or native runtime.

After source freeze and APK inspection, root supplies actual identities:

```sh
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home \
python3 prototype/compatible-phone/phone_replay.py \
  --serial YOUR_AUTHORIZED_DEVICE_SERIAL \
  --source FULL_CLEAN_INTEGRATION_COMMIT \
  --light artifacts/NEW_V017_LIGHT.apk --light-sha FULL_LIGHT_SHA256 \
  --test-apk artifacts/NEW_V017_REPLAY_TEST.apk --test-sha FULL_TEST_SHA256 \
  --restore-test-apk artifacts/focuspilot-research-v013-reset-test.apk \
  --fixture-manifest prototype/compatible-phone/build/asset-manifest.json \
  --output artifacts/NEW_EXCLUSIVE_COMPATIBLE_REPLAY_RECORD.json \
  --execute-own-compatible-fixtures
```

The new target stays installed; this is an authorized retained-data upgrade, not
an app rollback or clean reinstall. The exact original test APK is restored in a
`finally` path even after fixture failure/timeout. Restoration only replaces the
exact run-owned test bytes; unknown current test packages are left intact and
reported. Unexpected protected-state/installed-target differences fail the record.
No source-level harness can make concurrent outside device changes atomic.

## Local verification

```sh
python3 -m unittest discover -s prototype/compatible-phone -p 'test_*.py' -v
```

Ten local tests pass, including deterministic fixture generation, changed
capture/audit/result/generator rejection, malformed slots/JSON, strict final
instrumentation reports, target UID/origins, known-only restoration, timeout
cleanup, valid empty test-version manifest fields and DEX definition ownership.
The Java runner compiles against Android36 and the actual integrated target APIs.
Read-only inspection of the current built v17 app/test plus original test APK passes
signature, manifest, asset, native, alignment and target-only DEX ownership checks.
These are preparation results; **no physical replay has been performed by this
utility's author at this handoff**. Root records any actual device result separately.
