# JSON command prompt development — unpromoted

This pre-event research keeps the user-selected Qwen3.5-0.8B Q4_0, original exact
seven-intent JSON grammar, 128-token generation bound, nonthinking chat wrapper,
1,024-token context, four CPU threads and whole original-request gate unchanged.
One prompt candidate explicitly prioritizes unknown categories and distinguishes
starting work from pausing work. No Android app, native binary, phone, weights,
release or training process changed. No phone action ran.

The candidate was frozen before its sole native capture. It uses the same actual
host JNI as the historical development baseline, not the different frozen
confirmation backend. The openly seen 36-case corpus has 18 supported and 18
unsupported synthetic requests. This is development selection, not a fresh holdout.

| Actual seen capture | Supported complete proposal /18 | Raw unknown /18 | Raw intent /36 | Exact JSON + actual EOS /36 | Wrong accepts | Median prompt tokens | Median emitted tokens | Median native ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Historical deployed-prompt baseline | 12 | 2 | 14 | 36 | 0 | 158 | 8 | 444.05 |
| Frozen JSON candidate | 16 | 9 | 25 | 36 | 0 | 200 | 5 | 483.92 |

All four supported gains preserve complete action and argument values: seconds
timer (`dev010`), countdown (`dev011`), Clock navigation (`dev015`) and focus
status (`dev018`). There are no supported raw-intent or full-proposal losses.
The study-break request (`dev005`) still misclassifies and abstains; remaining
focus time (`dev017`) abstains. Pause coverage stays 2/3. Nine of 18 unsupported
requests still have incorrect non-unknown raw intent; the independent gate rejects
all of them in this seen set.

| Expected intent | Rows | Baseline raw correct | Candidate raw correct | Baseline complete proposal | Candidate complete proposal |
| --- | ---: | ---: | ---: | ---: | ---: |
| start_focus | 3 | 3 | 3 | 3 | 3 |
| pause_focus | 3 | 2 | 2 | 2 | 2 |
| alarm | 3 | 3 | 3 | 3 | 3 |
| timer | 3 | 1 | 3 | 1 | 3 |
| open_app | 3 | 2 | 3 | 2 | 3 |
| explain | 3 | 1 | 2 | 1 | 2 |
| unknown | 18 | 2 | 9 | 18 | 18 |

The first native request took **515.42 ms**, compared with historical 469.72 ms.
Subsequent native median was 483.84 ms versus 444.00 ms. Candidate native load took
457.21 ms, historical load 416.13 ms. The sole candidate process completed in
18.03 seconds, exit 0, within its 180-second bound. Timings are uncontrolled host
CPU observations; the extra prompt tokens and changed emitted intent distribution
do not establish a causal latency attribution. No Android or NPU timing follows.

**GO only to independently authored fresh frozen confirmation.** The seen candidate
gains four complete supported proposals without losses, but may overfit. It is not
promoted. Confirmation must retain the exact original request/gate/slots, include
all cases/failures and focus/pause regressions, and obey the parent's locked
acceptance protocol. Any future deployment still requires actual device cost and
regression checks. The older rejected digit experiment remains unchanged.

## Source and evidence identities

- Candidate source [JsonIntentCandidate.java](JsonIntentCandidate.java), SHA-256
  `a0dcde6e8adeb86e7ef22d07195abe074be86e9ba3700e6d6e6f7899d4245f13`.
- Exact rendered marker `UNIQUE_JSON_INVENTORY_REQUEST_271828`, SHA-256
  `3464e8c5e50553addff6a48a44dcfdc0b508854961924eb988c8c191814a137b`.
- Grammar SHA-256
  `b9426549188c9e393dd285a44ec13ec32d4e9ecb3bfc65e1194d869d002798f4`.
- Model SHA-256
  `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`.
- Actual development JNI SHA-256
  `2e9fa6676c4d68d0b4119cf13d8176d4d6674939c9361c48883c15cfad2cb156`.

[freeze.json](freeze.json) preserves the pre-capture prompt/runner/selection
contract. [candidate.json](candidate.json) adds actual unchanged app/gate/parser
source bindings and literal example inventory. [development-results.json](development-results.json)
contains aggregate/per-family correctness, all gains/losses, actual metrics and
ignored evidence hashes. [summarize.py](summarize.py) validates both original raw
captures before publishing aggregate-only files. Its exclusive creation refuses
overwrite. No synthetic request or full generated output is copied into aggregates.
The old runtime [provenance](../command-compact-dev/runtime-provenance.json)
retains the limits of attributing a pre-existing JNI build; linked runtime library
hashes were rechecked for this capture. No native rebuild occurred.

## Reproduction

From the repository root with the existing model, pinned host libraries and Java 17:

```sh
python3 prototype/command-json-dev/run_development.py --round replay-json1 --candidate json1
```

Each new round must have a unique ignored `build/` path. A failed or timed-out
capture preserves terminal metadata and partial output and is not automatically
restarted. Compilation/gate calls have 30-second bounds; the single native process
has a 180-second bound and closes its handle in `finally`. The runner is adapted
from the existing development runner; scoring uses unchanged `DevGateEval.java`.
Original baseline and candidate raw request/text/class/log artifacts remain
ignored. This directory reserves at most 2 MB, including ignored files; the actual
completed capture plus publication uses under 0.3 MB.
