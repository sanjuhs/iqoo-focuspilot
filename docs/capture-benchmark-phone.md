# Qwen3.5 capture comparison on the development phone

Pre-event research, 3 October 2026. The selected model remains Qwen3.5-0.8B
Q4_0; the installed app remains v0.11. This experiment evaluates the current
activation viewer on Nothing A059/SM7635/API36, using CPU inference, not the iQOO
NPU. It confirms displayed observations and measures a small paired timing sample.

## Actual result

The terminal run completed all eight trials and cleanup. The installed APK,
private model and packaged native-library hashes match the v0.11 release
manifest. Relevant current sources also match its full app-source commit.
[Recorded measurements and identities](capture-benchmark-phone-v011.json).

| Pair | Order | Capture off, native ms | Capture on, native ms | On minus off, ms |
| --- | --- | ---: | ---: | ---: |
| 1 | off → on | 2,069 | 1,870 | −199 |
| 2 | on → off | 2,166 | 1,864 | −302 |
| 3 | off → on | 1,965 | 1,919 | −46 |
| 4 | on → off | 1,899 | 2,034 | +135 |

All trials proposed `pause_focus` with `REVIEW REQUIRED`, 155 prompt tokens and
eight generated tokens. No action was executed. Capture-off emitted no summaries.
Every capture-on trial displayed all four distinct selected tensors, width 1,024,
with finite summary statistics and eight initial values. Their displayed values
matched exactly across repeats within the UI's formatting precision. This verifies
repeatable observations for this one input, not a command-specific causal finding.

Median native total was 2,017 ms off and 1,894.5 ms on. The four paired differences
had median −122.5 ms and mixed signs. **This sample does not establish a capture
overhead or a speed advantage.** Recreated-context setup measured 30–37 ms;
reused-context setup rounded to zero. Setup is excluded from the table's totals.
The warm-up measured 1,855 ms and is excluded from the pairs.

Post-request app memory samples ranged from 1,307,961 to 1,315,619 KiB PSS
(approximately 1.25 GiB), and 1,413,104 to 1,423,248 KiB RSS (approximately
1.35–1.36 GiB). A later sample after returning to the main screen was recorded
separately in the report. It is a snapshot, not proof of peak-memory bounds or
completed native deallocation.

The unchanged final checkpoint was focus paused, observation off, 100 virtual
points and 57,331 ms elapsed. Microphone and notification grants stayed false,
and no own focus-monitor service record was present. Actual ASR, permissioned
monitoring, iQOO/NPU and Office Kit remain separate requirements.

## Method

The own-app harness verifies installed APK and private model SHA-256 identities,
requires unlocked FocusPilot with focus paused and observation off, loads the
existing model, and runs one warm-up plus four pairs of the identical typed
`Stop focus` command. Capture order is off/on, on/off, off/on, on/off. No proposal
is reviewed or confirmed; no microphone, permission or system setting is changed.
The harness records synthetic result labels, selected tensor summaries, and
post-request PSS/RSS snapshots. It returns to the main screen and verifies the
original focus checkpoint, runtime grants and absent monitor service.

The runtime clears recurrent and attention memory for each independent request.
Changing capture mode recreates its context while retaining the loaded model.
This sequence balances reused and recreated contexts between modes, but does not
control phone scheduling, temperature or allocation effects. Four paired timing
differences describe this session; they cannot establish a general capture cost.

The callback selects `ffn_out-0`, `ffn_out-11`, `ffn_out-23`, and `result_norm`.
It observes only eligible contiguous F32 tensors during prefill. For each selected
node, the last prefill chunk replaces earlier chunks; the stored observation is
the last-position vector's mean, RMS, range and first eight values. Decoding is not
captured. These are actual values with no established causal semantic meaning.

The UI rounds native timing to whole milliseconds and tensor summary statistics
to five decimal places. Native total covers prefill and decoding; context setup
is separate. Memory clearing, tokenization, grammar construction, worker/UI work
and serialization are not included in native total. No full user-visible request
latency, continuous or peak memory, power use, independently audible voice, ASR,
network-disconnected operation or NPU execution is measured by this experiment.

## Repeat

Unlock FocusPilot in the foreground, leave focus paused and usage reading off,
and use the matching installed light APK:

```sh
python3 scripts/phone_capture_benchmark.py \
  --serial YOUR_SERIAL \
  --local-apk artifacts/focuspilot-research-v011-light.apk \
  --source-commit e8691e0a17f53d7d1ed0eebc2bd7bebb4a10bd4a \
  --output artifacts/capture-benchmark-v011.json
```

The harness takes its source commit argument as metadata. The public record must
also match the existing release manifest and relevant committed sources. Keep
raw screen hierarchies and private phone data out of Git. This procedure runs
only typed synthetic proposals; it cannot establish action accuracy on arbitrary
requests or mechanistic understanding of the model.
