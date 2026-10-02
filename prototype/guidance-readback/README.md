# Preserved first readback layout

`first-layout-artifacts.json` is the exact selected manifest from before the layout
repair, binding source `9fb4f7a4b341b8d563f033429b505a4432e7e09e` and its two
APK identities. It is historical evidence, not the current selection.

The executed failed harness sources are recoverable from Git:

- First attempt: `c409e68:scripts/phone_guide_readback.py`.
- Second attempt: `768dcb6:scripts/phone_guide_readback.py`.
- Grammatical goal/layout attempt: `166572e:scripts/phone_guide_readback.py`.

Their public reports retain the exact harness and manifest SHA-256 values. The
first two stopped before saving; the third saved a synthetic plan and verified
mute refusal, but observed no terminal readback outcome. All verified scoped
cleanup. See [the later selection](../../docs/guidance-readback-artifacts.json) and
[readback documentation](../../docs/guidance-readback.md).
