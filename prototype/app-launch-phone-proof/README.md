# Reviewed app-launch phone experiment

Pre-event research. The current repeat harness is
[`scripts/phone_app_launch.py`](../../scripts/phone_app_launch.py); it uses the
selected v0.11 APK/Qwen3.5 model, own-app review controls, and metadata-only target
foreground verification. No external-app view hierarchy, screenshot or content is
read. It launches Calculator and the Clock alarm view, creating no alarm or timer.

The first attempt stopped at the cancellation check because the harness compared
Android's full activity class name with its shorthand form. Its report records
no confirmation or executed action and verified final own-app cleanup; cancellation
itself was not marked verified. The exact executed source is retained in
[`reference/phone_app_launch_first_attempt.py`](reference/phone_app_launch_first_attempt.py),
with bytes matching that report's harness SHA-256. This is historical reference
source, not the selected repeat harness. The corrected harness canonicalizes the
two component-name forms while retaining package and class identity.

[First-attempt record](../../docs/app-launch-first-attempt-v011.json).
The public current results and limits belong in
[`docs/app-launch-phone.md`](../../docs/app-launch-phone.md).
