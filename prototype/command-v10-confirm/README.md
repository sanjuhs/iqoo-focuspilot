# Fresh gate-only confirmation

This pre-event synthetic confirmation follows a gate-only choice from the earlier
explicitly post-hoc comparison. The choice was locked **before authoring** these
requests: expanded gate SHA
`cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4`,
number parser SHA
`e5fa4770924e18c12eae89196646bf1ca9e7287ef8e460e9504166b4b5ff716d`,
unchanged OLD prompt adapter SHA
`2f6784c524ca9304fd714b86c04f5b1c3c5deb7e5ff562fbc34ae32c39e51e5d`.
The rejected longer prompt is not used. The baseline gate is the preserved
`54d1f3d71ff76c8b271c76a2fe1475e185f1f07370f4664d121a1e87a78cbc71`.

One author froze 100 synthetic requests in 50 wording families, 50 supported
exact-slot actions and 50 required abstentions, at
2026-10-02T15:10:31.142310+00:00. Root received counts/hashes without request text
before terminal evaluation. This author knows previous failures/results: it is
fresh data after source selection, **not independent human sampling** or evidence
of performance on real voice transcripts. Common domain words/classes recur;
new wording retains difficult current-focus and warned-during-focus forms.

Exact and normalized text overlap with 675 prior texts is zero: prior 58/373,
v0.8 100, v0.10 100, seen development 36 and eight actual pinned inline prompt
examples. Normalization lowercases, replaces non-ASCII alphanumeric runs with
spaces and collapses whitespace; it does not normalize meanings or number words.
No rows are removed. The rendered adapter inventory also verifies zero exact and
case/whitespace overlap. `freeze-manifest.json` binds all request/source bytes.

The runner performs one actual unchanged Qwen3.5-0.8B Q4_0 CPU/JNI capture and
shares its exact intents with separately compiled baseline and selected gates.
Both receive full original text. Oracle domain proposals independently expose
validator coverage/rejection; unsupported semantic labels remain unknown even
when the oracle proposes a plausible action. Exact kind/hour/minute/seconds
must match; wrong slots are failures. Accepted proposals execute no action.

Model timings use four CPU threads, context 1024 and state cleared per utterance.
The first request follows model load but is not OS-cache-cold; thermals/power are
uncontrolled. Java process timing includes launch, 100 validations and output,
and excludes compilation. It is not isolated parser, phone or NPU timing.

## Reproduce

Keep existing frozen evidence first. Repeating these now-seen requests is not
another independent confirmation. The generator requires all prior raw overlap
inventories, refuses changed request files, and the runner refuses to overwrite
an existing model capture. Model/runtime downloads and provider calls are absent.

```sh
python3 prototype/command-v10-confirm/generate_data.py
python3 -m unittest discover -s prototype/command-v10-confirm -p 'test_*.py' -v
python3 prototype/command-v10-confirm/run_evaluation.py
```

The pinned local GGUF, verified existing host JNI library, OpenJDK 17 and ignored
source snapshots must be present. Sources/hashes are in the manifest and prior
tracked repository revisions. Each model subprocess has a 300-second bound.
`--score-only` reads existing captures and compiles actual snapshotted gates,
without generating tokens. Six meaningful tests cover labels, paired regression
accounting, output completeness, abstention and wrong slots. Raw requests,
captured model text, binary classes and per-case details stay in ignored `build/`.

## Restore source snapshots in a scratch checkout

A public checkout does not include ignored `build/` source snapshots or raw
captures. Use a separate scratch clone/checkout containing the v0.10 selected
app sources (gate SHA `cc1eacd83a411817582a4902c0db03b2b3933b3466ba55af5e1acc4ac90a7ba4`),
not the workspace containing original evidence. Historical baseline commit
`6e483aaf9e42889794ed77c272b8a912539cfc7c` contains the baseline gate, number parser
and old prompt; its bytes were verified against this manifest. From the scratch
repository root, recover exactly the source directories required by the runner:

```sh
python3 - <<'PY'
import hashlib,json,pathlib,subprocess
root=pathlib.Path('.')
task=root/'prototype/command-v10-confirm'
manifest=json.loads((task/'freeze-manifest.json').read_text())
app=root/'prototype/android/app/src/main/java/dev/focuspilot/prototype'
baseline='6e483aaf9e42889794ed77c272b8a912539cfc7c'
for version in ['baseline','selected']:
    destination=task/'build'/(version+'-source')
    destination.mkdir(parents=True,exist_ok=True)
    for name,expected in manifest[version+'_source_sha256'].items():
        relative='prototype/android/app/src/main/java/dev/focuspilot/prototype/'+name
        raw=(subprocess.check_output(['git','show',baseline+':'+relative])
             if version=='baseline' else (app/name).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==expected, 'Wrong source revision: '+name
        target=destination/name
        if target.exists():
            assert target.read_bytes()==raw, 'Preserve different existing evidence'
        else:
            target.write_bytes(raw)
PY
```

This restores only `build/baseline-source/{ModelCommandGate,CommandNumberWords,
LocalModel}.java` and `build/selected-source/` with the same three filenames. It
performs no model inference. Reconstruct prior synthetic overlap inventories from
their tracked generators in the scratch checkout before the confirmation
`generate_data.py`; it expects their exact JSONL/TSV paths and the rendered
old-prompt example inventory documented in that generator. Original raw model
captures are not public, so `--score-only` requires a retained local capture;
source recovery alone cannot reproduce measured timings. A fresh measured run
also needs the pinned GGUF and matching host JNI artifact. The original binary
identity is given below; rebuilding on another toolchain may produce different
bytes and requires separately documented runtime provenance, rather than
silently claiming the original artifact hash.

## Actual confirmation result

The single old-prompt capture completed with exit 0 in 46.064 seconds. The source
choice, generator, protocol, all requests and labels remained unchanged before
and after capture. Both actual gate versions received identical model intents.
No repair or alternative prompt selection followed these results.

| Model-only result | Same unchanged old prompt |
|---|---:|
| Overall semantic intent correct | 36/100 |
| Supported intent correct | 35/50 |
| Unsupported correctly unknown | 1/50 |
| Unsupported non-unknown proposals | 49/50 |
| JSON schema + EOS valid | 100/100 |

The raw model frequently proposes actions for unsupported requests. The
original-text validator supplies rejection; schema compliance is not semantic
understanding or permission to act.

| Exact original-request result | Model + baseline gate | Model + selected gate | Oracle + baseline | Oracle + selected |
|---|---:|---:|---:|---:|
| Correct supported actions/slots | 15/50 | **31/50** | 20/50 | 45/50 |
| Supported false abstentions | 35/50 | 19/50 | 30/50 | 5/50 |
| Correct required abstentions | 50/50 | 50/50 | 50/50 | 50/50 |
| Correct actions/slots or abstentions | 65/100 | 81/100 | 70/100 | 95/100 |
| Wrong accepted proposals | 0 | 0 | 0 | 0 |
| Wrong accepted supported slots | 0 | 0 | 0 | 0 |
| Accepted proposals | 15/100 | 31/100 | 20/100 | 45/100 |

Paired generated outcomes gained sixteen supported requests and lost zero;
oracle outcomes gained twenty-five and lost zero. This fresh set reproduces the
selected gate's coverage gain after the earlier post-hoc choice. It does not
repair the model's poor unknown classification, nor establish universal safety.
The selected gate handles 62% of supported model-backed requests versus 90% with
oracle domain labels; language classification still limits useful coverage.

Five supported oracle failures remain: current-focus/current-concentration stop
requests, warned-during-focus explanation, a reason question ending in Mira's
name, and an "I'd like to see" focus-status wrapper. These intentionally difficult
forms were kept as new wording after earlier related failures. All were rejected
rather than executed; no source or request changes were made from the result.

Host CPU model load was 431.89 ms, first native request 465.99 ms and subsequent
native median 454.53 ms (wall median 456.02 ms). Median prompt length was 163
input tokens, range 158–170. Both gates shared that one model capture, so no
extra inference cost is attributed to gate selection. Java gate processes took
75–77 ms for 100 proposals including JVM launch and output; this is neither an
isolated parser benchmark nor measured Android overhead. Cache/thermal conditions
were uncontrolled; no phone/NPU timing claim follows.

Six evaluation tests pass. `results.json` contains actual aggregate/per-class,
per-family and paired counts, source/model/output hashes and no-promotion state.
`experiment-metadata.json` records source/test/capture digests. The confirmation
added no model download, dependency, provider cost, phone action or permission
change. Root assesses source promotion and real-device regressions separately.
This remains fresh synthetic data by the same informed author, not independent
human evidence.

## Timing wording erratum

The immutable `results.json` field `model.timing_limit` inherited the phrase
"Each version has its own model load, fixed baseline-then-candidate order" from
the preceding two-prompt experiment. That phrase is inaccurate for this
confirmation: **there was exactly one model load and one 100-request native
capture, shared by both gates**, as recorded by `new_inference_captures: 1`,
model metadata and the runner. The remainder of the host/cache/thermal limitation
still applies. Results, runner and metadata bytes are deliberately preserved;
this README is the correction.

The actual verified host native library used was
`prototype/command-eval/build/native/libfocuspilot_local.dylib`, SHA-256
`ad57cd04bcb439a94b1f82800b91125dc07da23f08867fb854020aa18beccd7e`.
The protocol and capture metadata contain that identity. An earlier summary
using a different native hash was stale, not a change to this experiment.
