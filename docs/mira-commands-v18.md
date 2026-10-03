# Mira command screen — v0.18 research

Ask Mira now puts an empty editable request, draft-only examples and Understand
before model setup. The original goth companion stays beside the request. Examples
fill the draft; they perform no inference or action. Editing still cancels the old
request, clears its response/activation display and invalidates its review.

The screen shows quick local versus Qwen provenance, a plain action preview and
Review when a valid proposal exists. Confirm remains a separate action-level step.
Model loading is explicit and never evaluates the draft. The visible status reports
whether Qwen is actually loaded and its CPU backend. Model responses, timing and
optional tensor capture live in an initially collapsed details section.

Finish/Cancel voice appear during a voice draft; Cancel inference appears during
model work. Active readback has a separate Stop button that preserves the confirmed
status. Load failure appears visibly, with the technical reason in details. The
command screen accepts existing incoming/restored drafts without automatic execution.
No parser, validation, executor, model, native library or permission changes occur.

## Verification and artifact

Source: `959f27a0721deca58dc45852e79759bc5a255539`. Two concrete review findings
(missing readback Stop and hidden load failure) were fixed before final packaging.
The final offline build passes all **208 JVM tests in 28 suites**, zero failures,
errors or skips; lint has zero errors/fatal issues and 79 warnings. These checks
cover existing contracts and compilation, not physical layout/touch behavior.

The signed light APK is **5,942,764 bytes**, SHA-256
`dc40863819dd7fd12e93500cf279c343121a9c4af5a71986d5d4a29a7699f44d`.
Package inspection passes version18/0.18-mira-commands-research, signing and 16 KiB
native alignment, unchanged native payload and all six unchanged license assets.
There are no bundled weights or INTERNET permission. Existing pinned private Qwen
weights are required for fallback inference; quick commands need no model load.
[Artifact/source/build record](mira-commands-artifact-v18.json).

One streamed update installs the exact APK on Nothing. The original test package,
three named preference-store identities/paused checkpoint, canonical model identity,
two runtime grants and own-service absence remain unchanged. Focus stays paused,
observation off, 100 simulated points and 97,331 ms accumulated time. No app UI,
voice, model generation, phone wake or permission change occurs during installation.
[Actual installation record](mira-commands-phone-v18.json).

The phone remains locked/off. Physical layout, examples, review cancellation,
fallback, voice and readback Stop still require unlocked own-app checks. Previous
v17 model measurements retain their exact old-APK attribution. Current logical
storage remains below 15 GB; no new dependencies, downloads or weight copies.

This is pre-event research. Actual iQOO NPU, Office Kit, event-code eligibility and
accepted submission remain unfinished requirements of the full project.
