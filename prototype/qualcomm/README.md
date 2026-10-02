# Qualcomm deployment laboratory

Pre-event research only. No app integration, hardware run or NPU verification yet.
See [deployment instructions](../../docs/snapdragon-deployment.md).

```sh
python3 prototype/qualcomm/compile_adapter.py
python3 -m unittest discover -s prototype/qualcomm -p 'test_*.py' -v
python3 prototype/qualcomm/preflight.py --properties prototype/qualcomm/device-properties.example.json
```

The example properties are illustrative, not a detected phone. The compiler downloads
only the pinned 82MB GenieX0.7.0 AAR (checksum verified) into ignored `.cache/`, extracts
its Java classes, and compiles the original Java adapter against installed Android36
and Java17. It neither installs SDK globally nor downloads model weights.

The adapter uses the pinned SDK's lower-level JNI interfaces to avoid coroutine
requirements in the Java probe. SDK upgrades require API recompilation and device
lifecycle tests. It returns proposals, never executes phone actions, keeps compute
explicit, verifies model bytes, uses model chat template and token bounds, releases
the model, and discards cancelled output. Native prefill cancellation latency is
unknown. Use a new adapter after cancelling. Profiling reports timings, not backend
proof; backend proof is deliberately UNVERIFIED.

The SDK is third-party Qualcomm GenieX, BSD-3-Clause plus Qualcomm Terms of Use,
with bundled QAIRT and other components; preserve upstream notices and applicable
binary terms before distribution. No Qualcomm source copied into this repository.
Sources: [GenieX v0.7.0](https://github.com/qualcomm/GenieX/tree/v0.7.0),
[LICENSE](https://github.com/qualcomm/GenieX/blob/v0.7.0/LICENSE),
[NOTICE](https://github.com/qualcomm/GenieX/blob/v0.7.0/NOTICE),
[Qualcomm terms](https://www.qualcomm.com/site/terms-of-use).
