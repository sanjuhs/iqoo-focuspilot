# Fresh natural-command corpus preparation

Pre-event research tooling only. This stage contains a generic freezer and
contract tests; fresh requests are authored only after the parent explicitly
authorizes a committed candidate/source freeze. No model weights, outputs,
candidate grammar, candidate tests, gate or oracle are consulted by the author.

The locked protocol lives in `prototype/qwen-natural-eval/protocol.json`.
The prospective corpus has 100 rows in 50 reciprocal supported/unknown families:
10 start, 8 pause, 8 alarm, 10 timer, 6 approved-app and 8 explain requests,
plus 50 mandatory unknown near-neighbors. Each approved app has two requests.
Hard Pause, resume, spoken numbers, four duration endpoints, noon/midnight and
nudge-cause cases remain. All twelve declared unknown boundary families remain.

Rows use the existing shared schema: `id`, `family`, `template_id`, `utterance`,
`intent`, `expected_kind`, integer `hour`/`minute`/`seconds`, `hard_tags`,
`boundary_family`, `counterpart_id`, and `oracle_intent`. The author supplies
labels and exact slots manually. `UNKNOWN` uses zero slots. Oracle domain metadata
does not override unknown semantic gold. Actual requests stay in ignored `build/`;
public manifests contain identities, counts and hashes, never raw requests.

The parent supplies `novelty-exclusions.json` with opaque SHA256 inventories.
Schema is `focuspilot.natural_exclusion.v1`, normalization is
`ascii-alnum-lower-v1` (lowercase, replace non-ASCII-alphanumeric runs with spaces,
collapse whitespace). `normalized_request_sha256` and `exact_request_sha256`
hash normalized and exact UTF-8 request strings; `family_sha256` and
`template_sha256` hash exact prior IDs. Each array is sorted, unique and nonempty.
`inventory` supplies project-relative paths, source hashes, extraction methods and
text counts; `source_commit` supplies a full provenance commit. Candidate fixture
strings remain hidden. A collision reports only the new author's own row IDs.

Parent `source-freeze.json` supplies `files_sha256` mapping project-relative paths
to hashes. It must bind protocol, design lock, exclusion bundle, these three
generic files and the old generic validator, extraction utility and abstract test
fixture helper (`qwen-balanced-data/test_data.py`), plus candidate sources.
The freezer checks readable metadata and generic files against the explicitly
authorized commit. Candidate bindings are recorded as opaque metadata; their
actual inspection and verification remain the parent's responsibility. The
freezer never reads those candidate bytes and never calls an inventory rescanner.

Write private author inputs to `build/author-confirmation.jsonl` after authorization.
Freeze with `python3 prototype/qwen-natural-data/generate_data.py --authorization-commit FULL_COMMIT`.
The freezer checks schema, counts, exact slots, reciprocal pairs, template identities,
hard coverage and opaque exclusions; it refuses overwriting frozen outputs.
Preserve any initial authored attempt before pre-output manual corrections.
Never replace, relabel or remove difficult rows after model/gate outputs.
Exact/normalized exclusion and manual family assignment do not establish semantic
independence; the author is informed, not blind. No training or eligible submission
claim follows from this preparation.

Run contract tests with
`python3 -m unittest discover -s prototype/qwen-natural-data -p 'test_*.py'`.
