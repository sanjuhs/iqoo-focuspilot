# Phase 1 concept document

Four-page public concept PDF for the authenticated Finale idea form. The form
requires a PDF/PPT (maximum 25 MB) or document link. Title limits are 5–200
characters; description limits are 50–2,000. Displayed Phase 1 deadline is
5 October 2026; exact cutoff time/timezone is unverified.

The document discloses pre-event code, distinguishes current v18 installation
from historical v17 CPU inference, reports limited command coverage, and leaves
voice, persistent mode, iQOO NPU and Office Kit as verification work. Artwork
reuses the project's original procedural Mira illustration, with no private
phone capture or account details.

Run with Python containing ReportLab and Pillow:

```sh
python3 prototype/phase1-document/build_pdf.py
```

Output: `output/pdf/focuspilot-phase1-concept.pdf`. The builder validates its
public evidence inputs, uses invariant PDF metadata and makes no network, model
or phone calls. [QA/source hashes](../../docs/phase1-document-evidence.json) bind
the four visually inspected pages and final pixel-equivalent render.

Prepared form copy is in [the application draft](../../docs/application-draft.md)
and [structured fields](../../docs/phase1-form-copy.json). Human proficiency,
prior-build answers and final attestation remain unresolved. No form fill,
dashboard upload or submission has occurred.
