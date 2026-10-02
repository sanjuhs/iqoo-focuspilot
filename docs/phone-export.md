# Actual v0.12 phone export and laptop validation

Verified 3 October 2026, pre-event research. Nothing A059 / SM7635 / API36 used
the selected light APK with SHA-256
`4ebd8097c9f3ff4a4cf5f12ecc5b80c1a8974b561c8e4ac733db1d77662583a0`.
App source remains `24f10b62a4a62c22ad6db90ac6339f29e2426dbd`.
No app/model rebuild, settings change or microphone activation occurred.

[Exact accepted record](phone-export-v012.json) binds executed harness
`e51a74f2703537c187e42e528f9d03636087d750` and its SHA-256 to the installed APK.
All three recorded phases and app-state cleanup passed:

| Physical branch | Observed outcome |
| --- | --- |
| Export review → Cancel | Review closed; own focus checkpoint unchanged. |
| Choose destination → Android picker → Back | Returned to FocusPilot with its cancelled/expired status; checkpoint unchanged. |
| New local Downloads file → Save | App reported completion; exact new 496-byte file parsed and matched its source checksum on the laptop. |

The phone-source and received SHA-256 are
`b4ad013ff98b83a8b93576cb9c186b17d13b6e06eb7f6406edaf6f321994057f`.
The existing laptop consumer accepted the complete schema and pinned policy
identities: **zero records, zero contexts, empty groups**, no phone action,
no Office Kit or NPU claim. No policy forward inference occurred because there
were no records. This establishes actual closed-file export and local-file
interoperability; transport was an explicit ADB read of this exact new test file.

Research defaults, empty goal/no guide and zero saved live labels were checked
before export. Focus remained paused/off/100 points/97,331 ms; runtime microphone
and notification grants stayed denied, and no focus monitor appeared. Android's
normal one-document URI access is part of Save. The original report's
`permissions_changed: false` refers to runtime/settings actions, not absence of
that document access; the current harness labels this scope explicitly.
[Official Android document flow](https://developer.android.com/training/data-storage/shared/documents-files).

The actual payload and laptop aggregate stay in ignored `artifacts/`, outside Git
and public release assets. The uniquely named test phone copy remains in local
Downloads; exported files are outside app-data deletion. App-state
`cleanup_verified` does not mean exported/partial provider files were deleted.
No directory entries, account names, raw task text or screenshots enter this record.

The metadata-only physical record is also backed up with
[research v0.12](https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.12).
Its server size/digest, all thirteen prior asset identities and the unchanged
selected tag passed [publication verification](phone-export-publication-v012.json).
Storage measured about 13.822 GB, below the strict 15 GB project cap.

## Preserved unsuccessful attempts

- [First transition attempt](export-picker-transition-first-v012.json), source
  `0c6f5d063ec12197b4f95096c4e41da03896aaae`: own review Cancel passed, but the
  immediate foreground check stopped during picker launch. Completion and cleanup
  were false; no provider controls were inspected or Save invoked. A separate
  [manual guarded recovery](export-picker-transition-recovery-v012.json) later
  observed the exact unlocked picker, cancelled it and verified app-state cleanup.
- [First local-save attempt](export-local-first-attempt-v012.json), source
  `3ba8ae8`: both cancellation branches passed; an incorrect root-row selector
  stopped before filename editing or Save. Cleanup passed. The correction uses the
  observed unique `android:id/title` Downloads entry inside the exact roots drawer
  and its bounded clickable parent, then the observed system Save button.

These are harness failures, not evidence of a failed app file write. None is
rewritten as a successful run. Accepted-source reproduction remains pinned above;
the later runtime-permission field label and optional safe test-filename argument
were not rerun on phone. The original default filename/UI flow remains unchanged.
Six foreground-owner tests, including explicit picker/default-owner separation,
Python compilation and source/checksum/report inspection passed.

## Repeat and remaining scope

Use the exact selected v0.12 light APK, unlocked with FocusPilot foreground,
empty authored goal/guide, default research settings, no live labels, paused focus
and observation/monitor off. Commit the harness and keep the worktree clean.
The script refuses existing evidence or either exact test copy. Choose a new
synthetic `--test-filename` and output path; retained copies must never be
overwritten. For example:

```sh
python3 scripts/phone_export.py --serial YOUR_DEVICE_SERIAL \
  --local-apk artifacts/focuspilot-research-v012-feedback-light.apk \
  --output artifacts/phone-export-repeat.json --execute-export-test --save-local \
  --test-filename focuspilot-v012-export-test-repeat-20261003.json
```

The default filename refuses the retained copy. The optional filename accepts only
the fixed synthetic prefix and a safe suffix; change the example if that copy
already exists. Do not bypass the absence checks. Cancellation-only testing also
uses this conservative precondition. A chosen destination is scoped operator
interaction, not broad phone storage permission.

Real observation-record export, nonempty actual-policy replay, provider error/
partial-write/recreation branches, concurrent data deletion, actual iQOO/Office Kit
pairing/transfer, disconnected operation, NPU and accepted eligible submission
remain unfinished. The official phone/laptop bridge still needs the supported
hardware and account; ADB is not Office Kit. This test is not in the existing video.
