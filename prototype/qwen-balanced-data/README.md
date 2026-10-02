# Prospective balanced Qwen corpus

Pre-event research data preparation; no training or eligible event submission.
Actual manually authored requests and gold slots stay in ignored `build/`.
The generic freezer performs no model, phone, gate or oracle calls.

Train has 112 rows, 16 per seven-class intent, with eight complete authored
wording families per class and two variants per family. Development has 14 rows,
two per class in seven separately authored families. Confirmation is authored
only after the parent supplies the committed numerical design lock: 100 rows,
50 supported (start 10, pause 8, alarm 8, timer 10, approved app 6, explain 8)
and 50 mandatory unknown counterparts, in 50 reciprocal boundary families.

Each row contains `id`, `family`, `template_id`, `utterance`, `intent`,
`expected_kind`, integer `hour`/`minute`/`seconds`, `hard_tags`, `boundary_family`,
`counterpart_id`, and `oracle_intent`. Labels and slots are author expectations;
the Android gate does not supply them. Unknown rows use `UNKNOWN` and zero slots;
their optional oracle domain isolates parser coverage, not a semantic prediction.
Training consumes the unchanged app's sanitized user prompt and canonical JSON
completion. Raw reserved chat controls must be escaped exactly as LocalModel does.

`generate_data.py` imports the existing strict extraction and normalization
utility, requires every known prior source to remain available, rescans current
Android production/test sources, prior authored attempts, frozen requests and
old train/validation/heldout files. It rejects exact and punctuation/case-normalized
reuse, including between new splits, and rejects shared author family/template
identities. Source paths, full hashes, extraction methods, counts and dataset
hashes are public; raw requests are not. These checks do not establish semantic
independence. The informed author has seen earlier synthetic cases and results;
this is neither a blind author nor a natural user/ASR distribution.

Keep legitimate novel phrasing even if the unchanged gate cannot parse it.
Keep hard Pause, spoken duration, endpoint, nudge-cause and unknown boundaries.
Never remove, relabel or replace rows after model/gate results. Report the manual
oracle ceiling separately. Frozen outputs and manifests refuse overwriting.

Author inputs: `build/author-{train,development,confirmation}.jsonl`.
Freeze training with `python3 prototype/qwen-balanced-data/generate_data.py --stage training`.
Freeze confirmation with `--stage confirmation --design-commit FULL_PARENT_AUTHORIZED_COMMIT`.
Run author-validation checks with
`python3 -m unittest discover -s prototype/qwen-balanced-data -p 'test_*.py'`.
