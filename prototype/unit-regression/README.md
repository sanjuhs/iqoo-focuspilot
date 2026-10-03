# Known-wording source-unit regression

This is pure validator **development** tooling. It performs no model inference,
phone action, training or external calls, and gives no fresh/general accuracy or
promotion claim. It preserves existing data and old outcomes.

Inputs are the exact balanced train/development/confirmation-v2 gold files (226
rows) plus the previously frozen natural-validation known-route and baseline-output
TSVs. Their hashes are pinned from the public `development-results.json`. There are
1,582 routes: 158 supported correct routes, 948 supported wrong-intent routes and
476 routes over the 68 unknown requests. Exactly 80 baseline routes were accepted.

`prepare` parses literal numeric quantity and unit from each source request with
an independent Python parser. It never opens UnitCommand. Correct Start/Timer
oracles require the source amount × unit factor to equal the old manually labelled
seconds, without deriving amount by dividing gold seconds. Alarm clock slots and
approved app targets likewise require independent source agreement. Start without
a duration uses amount 0/unit none; timer must be positive. Other response shapes
retain the prior structured fields.

All seven routes receive one deterministic mock reply. Wrong/unknown routes use
the first source quantity, time or approved app where present, and valid default
slots when absent. Multiple-duration adversaries use the first quantity. This finite
challenge does not cover every possible model response or prove universal safety.
Actual responses and gold/decisions remain in ignored `build/`; public readiness
and result metadata contain hashes, counts and methodology without requests.

Only after the parent freezes candidate source, `evaluate` compiles the provided
UnitCommand/StructuredCommand/CommandNumberWords plus this Java helper into the
owned ignored subtree. It calls `UnitCommand.validate(original, output)` and compares
canonical kinds and full hour/minute/seconds against historical manual gold.
Approved app mapping becomes the exact old OPEN_SETTINGS/CALCULATOR/CLOCK kind.
Prior accepted canonical behavior must be retained; preview wording may differ.
Results report all 80 preservations, 158 oracle opportunities, 476 unknown routes,
948 wrong-intent routes and every observed false accept, without modifying labels.

Run `python3 -m unittest discover -s prototype/unit-regression -p 'test_*.py'`.
Prepare with `python3 prototype/unit-regression/regression.py prepare`.
The root then invokes `evaluate` with the full authorized source commit and exact
three source paths. No candidate execution is authorized merely by preparation.
This pre-event research is not eligible event-written competition code.
