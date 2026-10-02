# Structured-action development feasibility data

This is a 24-row **development** cohort, not a fresh confirmation set, blind test,
training success or promotion result. The informed author may reuse earlier
coverage-failure wording. No candidate prompt, validator, native implementation,
model outputs, model inference, gate or oracle is consulted to select or label rows.

There are 18 supported requests: four Start, four Pause, three Alarm, three Timer,
two Open App and two Explain. Six unknown requests cover compound, negated,
conditional, invalid-duration, destructive and unsupported private-capture neighbors.
Ordinary privacy/no-recording preferences alone remain legitimate requests.

Each private row has `id`, `utterance`, and a manually labelled `expected` object.
The seven exact response shapes are:

- `{"intent":"start_focus","duration_seconds":0}`: zero for untimed, otherwise 1–7,200.
- `{"intent":"pause_focus"}`.
- `{"intent":"alarm","hour":12,"minute":0}`: hour 0–23, minute 0–59.
- `{"intent":"timer","duration_seconds":90}`: 1–7,200 seconds.
- `{"intent":"open_app","app":"settings"}`: settings, calculator or clock.
- `{"intent":"explain"}`.
- `{"intent":"unknown"}`.

Integer slots exclude booleans and floats. Missing/extra slots and unapproved app
targets are invalid. Gold object member order has no semantic significance;
canonical generated-output checks belong to the later runtime experiment.
Exactly matching the structured object is still only a proposal, not Android
execution or successful explanation delivery.

Actual author script and JSONL/TSV remain in ignored `build/`. Public
`data-manifest.json` contains source/data hashes, counts and semantic design notes,
without actual requests. The generic freezer validates objects, counts and
within-cohort duplicates; it performs no oracle filtering or prior-corpus exclusion.
It refuses overwriting an existing frozen cohort or manifest. Preserve gold when
model outputs arrive; this cohort may inform development but cannot support a
fresh-test or generalization claim.

Freeze after manual authoring with `python3 prototype/structured-data/generate_data.py`.
Run generic contract tests with
`python3 -m unittest discover -s prototype/structured-data -p 'test_*.py'`.
The parent reviews manual gold and freezes all candidate/runtime sources before
the single planned development capture. Pre-event research is not eligible
event-written competition code.
