# Compatible unit contract: prospective author tooling

This folder contains generic validation/freezing utilities for a future 100-row
synthetic confirmation cohort. It is pre-event research. No fresh requests are
authored at the tooling-preparation stage, and these utilities perform no model,
gate, oracle, phone or network calls.

The parent must explicitly authorize authoring after committing the candidate,
protocol, generic source and opaque exclusion hashes. The author must not inspect
the new candidate validator, tests, model prompt or outputs. A separate manual
semantic/slot review occurs before any baseline/candidate capture. Qualification
criteria are parent-owned and fixed prospectively; this tool never scores or
promotes a candidate.

The author is informed by earlier development. This is an informed synthetic
cohort, not a blind study or a population accuracy estimate. Prior exact and
normalized wording, family IDs and template IDs are excluded using opaque hashes;
hash novelty cannot prove semantic independence. Preserve every authored attempt,
including attempts rejected for opaque overlap. Never replace hard cases or alter
gold in response to model/gate outputs.

The planned cohort has 50 reciprocal supported/unknown pairs and class counts
9 start, 9 pause, 8 alarm, 8 timer, 8 open-app, 8 explain, and 50 unknown. The
protocol fixes app counts (Settings3/Calculator3/Clock2), supported hard-tag
minima, and exact counts for all twelve unknown boundary families. No row/random
split applies.

Each row has exactly these keys:

```json
{"id":"bounded_id","family":"paired_family","template_id":"paired_template","utterance":"manually authored request","expected":{"intent":"timer","duration_seconds":1020},"expected_raw":{"intent":"timer","amount":17,"unit":"minutes"},"hard_tags":[],"boundary_family":"","counterpart_id":"paired_unknown_id"}
```

`expected` is manually labelled canonical gold. `expected_raw` is independently
labelled source quantity/unit gold. Their arithmetic must agree, but the generic
validator does not parse the request or derive either gold object from a gate.
The root's review checks that the actual wording supports both objects.

The seven exact response shapes are:

- Start: canonical `intent` and `duration_seconds` from 0 through 7,200; raw
  `intent`, integer `amount`, and `unit`. Untimed start is exactly 0/`none`.
- Timer: canonical `intent` and `duration_seconds` from 1 through 7,200; raw
  positive integer `amount` and `unit`.
- Alarm: `intent`, `hour` from 0 through 23, and `minute` from 0 through 59.
- Open app: `intent` and `app` equal to `settings`, `calculator`, or `clock`.
- Pause, explain and unknown: `intent` only.

For timed responses the units are exactly `seconds`, `minutes`, or `hours`.
Alarm/app/pause/explain/unknown raw objects equal their canonical objects. Unknown
objects contain no stray slots. A privacy or no-recording constraint alone is a
legitimate bounded request. Its unknown neighbor needs an actual extra capability,
negation, compound request, unsupported/ambiguous demand, invalid/malformed slot,
conditional/quoted instruction, or adversarial suffix/injection.

All requests, raw gold, author scripts and failed attempts remain in ignored
`build/`. Public files contain generic source, tests, hash/count manifests and
methodological notes, never the authored corpus. Raw requests must fit Android's
500 UTF-16-code-unit bound and the native single-line TSV format. Reserved chat
controls remain literal request data for app-exact rendering by the parent.

Root-owned metadata paths:

- `prototype/compatible-eval/protocol.json`, schema
  `focuspilot.compatible_unit_protocol.v1`, with
  `candidate_source_freeze_before_authoring: true` and `fresh_cohort` containing
  `rows`, `families`, `rows_per_family`, `supported`, `unknown`, `counts`,
  `approved_apps`, `hard_minimums`, and `unknown_boundaries` maps.
- `prototype/compatible-eval/design-lock.json`.
- `prototype/compatible-eval/novelty-exclusions.json`, existing
  `focuspilot.natural_exclusion.v1` schema and `ascii-alnum-lower-v1`
  normalization; sorted unique full hash lists for exact/normalized wording,
  families/templates, plus inventory metadata and full provenance commit.
- `prototype/compatible-eval/source-freeze.json`, with `files_sha256` mapping
  project-relative source/metadata paths to full hashes. The parent verifies
  candidate bytes. The author tool reads only the metadata and its own three
  generic files, and compares those bytes to the explicit authorization commit.

The exact unknown counts are negation5, compound5, conditional4, quoted4,
foreign_topic5, privacy_capture4, destructive4, messaging3, payments3,
malformed_argument5, unsupported_target4, and third_party4. Adversarial suffixes
or chat-control injections fit their actual semantic boundary rather than adding
a thirteenth bucket.

The minimum hard-tag counts apply only to supported rows: `unit_minutes`8,
`unit_seconds`4, `unit_hours`2, `spoken_number`8, `untimed_start`2, `am_pm`4,
and `clock_24h`2. Unit/untimed/clock tags must agree with the gold shapes.
Generic checks also enforce slot consistency for optional pause/resume/nudge,
duration endpoint and exact noon/midnight tags. Tags do not prove source wording
semantics; clock notation and spoken quantity need manual source review.

Run pure contract tests before the source freeze:

```sh
python3 -m unittest discover -s prototype/compatible-data -p test_data.py
```

After explicit parent authorization, author a preserved
`build/author-confirmation.jsonl`, then freeze once:

```sh
python3 prototype/compatible-data/generate_data.py --authorization-commit FULL_40_HEX_COMMIT
```

The command creates ignored `build/confirmation.jsonl` and
`build/confirmation-requests.tsv`, plus public `corpus-manifest.json`. It refuses
overwriting any existing frozen output. Full source/input/corpus hashes, class,
family, app, unit, hard-tag and boundary counts are recorded before outputs.
Partial failures remain preserved for inspection rather than being silently
overwritten. The parent must review every label before inference.
