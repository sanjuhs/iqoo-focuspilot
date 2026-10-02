# Prepared Android gate fixtures

Source-only, pre-event diagnostic preparation. Nothing in this folder has been
installed, compiled or executed on the phone. Root may integrate the custom
instrumentation into `androidTest` only after the fresh gate confirmation passes
and the candidate receives integration review.

`dev.focuspilot.prototype.GateIsolationInstrumentation` directly calls the real
target app's `ModelCommandGate.validate`. Its package contains no shadow gate or
number parser. Fixtures reuse exact utterances already present in
`command-gate-v14-dev/CandidateGateTest.java` and the existing Android
`ModelCommandGateTest.java`; they are openly seen regression fixtures, not fresh
holdout evidence.

The 334 expected checks comprise 25 complete positive kind/hour/minute/seconds
checks, 39 rejected utterances across all seven intent routes (273 checks), and
six supported forms across each of their six wrong semantic routes (36 checks).
They cover spoken-number slots, resume versus timed focus, Pause direction,
midnight alarms, approved Clock launch, local explanations, negation, conditions,
compound requests, unsafe domains, malformed times and invalid durations.

The runner only reads inputs and returns proposals in memory. It does not access
LocalModel, an executor, UI, services, preferences, settings, permissions, network
APIs or device files. No activity is required, so a later authorized run can use
a locked phone. Android instrumentation itself injects/restarts the target app
process; a future outer harness must verify protected app state before and after
and restore any replaced test package.

`onCreate` starts instrumentation, and `onStart` finishes with `-1` on success or
`0` on failure. `report_json` and `stream` bundle strings contain a structured
`focuspilot.gate_isolation.v1` report: completed check count, expected inventory,
failed fixture IDs and failure type. No raw phrases or proposals are emitted.
Fixture or report exceptions produce failure rather than a fabricated pass.

A future successful run establishes those already-seen pure gate checks against
the installed app. It does not establish model accuracy, execution of phone
tools, UI behavior, voice, persistent monitoring, NPU use or hackathon eligibility.
