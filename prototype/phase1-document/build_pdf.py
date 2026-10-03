#!/usr/bin/env python3
"""Create the public Phase 1 concept PDF from verified prototype evidence.

No phone, network, API keys or model access. No private account/profile fields.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_current_pitch import mira
from package_bundled_apk import project_bytes

OUT = ROOT / 'output/pdf/focuspilot-phase1-concept.pdf'
W, H = 595.28, 841.89
INK, MUTED, LILAC, TEAL = '#262232', '#625A70', '#C9B7EA', '#79DBC8'
BG, WHITE = '#1A1724', '#FFFFFF'


def text(c, x, y, value, size=12, color=INK, bold=False):
    c.setFillColor(HexColor(color))
    c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    c.drawString(x, y, value)


def paragraph(c, x, top, width, value, size=12, color=INK):
    style = ParagraphStyle('body', fontName='Helvetica', fontSize=size,
                           leading=size*1.48, textColor=HexColor(color))
    p = Paragraph(escape(value), style)
    _, height = p.wrap(width, H)
    if top-height < 66:
        raise ValueError('Text would enter footer: ' + value[:40])
    p.drawOn(c, x, top-height)
    return top-height


def card(c, y, title, body, height=112):
    c.setFillColor(HexColor('#F2EEF8'))
    c.roundRect(42, y-height, W-84, height, 12, fill=1, stroke=0)
    text(c, 58, y-27, title, 16, INK, True)
    bottom = paragraph(c, 58, y-44, W-116, body)
    if bottom < y-height+13:
        raise ValueError('Card text overflow: ' + title)


def page(c, index, title, subtitle):
    c.setFillColor(HexColor(WHITE)); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor(BG)); c.rect(0, H-154, W, 154, fill=1, stroke=0)
    text(c, 42, H-38, 'FOCUSPILOT / MIRA', 12, TEAL, True)
    text(c, 42, H-82, title, 27, WHITE, True)
    paragraph(c, 42, H-101, W-84, subtitle, 11, LILAC)
    footer(c, index)


def footer(c, index, dark=False):
    color = LILAC if dark else MUTED
    text(c, 42, 37, 'PHASE 1 CONCEPT | PRE-EVENT RESEARCH | 03 OCT 2026', 8, color)
    text(c, W-52, 37, str(index), 9, color, True)


def link(c, y, title, url):
    text(c, 42, y, title, 11, INK, True)
    text(c, 42, y-17, url, 9, MUTED)
    c.linkURL(url, (42, y-20, W-42, y+12), relative=0)


def main():
    if project_bytes(ROOT)+10_000_000 > 15_000_000_000:
        raise RuntimeError('Document reservation exceeds project storage cap')
    app = json.loads((ROOT/'docs/mira-commands-artifact-v18.json').read_text())
    install = json.loads((ROOT/'docs/mira-commands-phone-v18.json').read_text())
    native = json.loads((ROOT/'docs/unit-native-phone-v17.json').read_text())
    dashboard = json.loads((ROOT/'docs/phase1-dashboard-observation.json').read_text())
    if app['tests']['tests'] != 208 or not install['passed'] or native['raw_exact_seen_cases'] != 6:
        raise RuntimeError('Expected evidence changed; review document facts first')
    if dashboard['phase1_deadline_displayed'] != '5 Oct 2026' or dashboard['selected_track'] != 'Productivity':
        raise RuntimeError('Observed application requirements changed; review document first')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), invariant=1)
    c.setTitle('FocusPilot: Mira - Phase 1 concept')
    c.setAuthor('FocusPilot project')
    c.setSubject('Productivity concept, verified CPU prototype and disclosed pre-existing components')

    # Cover: original procedural character, an illustration rather than a phone capture.
    c.setFillColor(HexColor(BG)); c.rect(0, 0, W, H, fill=1, stroke=0)
    text(c, 42, 790, 'PRODUCTIVITY / GRAND FINALE / PHASE 1', 10, TEAL, True)
    text(c, 42, 729, 'A little focus,', 34, WHITE, True)
    text(c, 42, 686, 'with Mira.', 34, LILAC, True)
    paragraph(c, 42, 648, 304, 'A friendly local Android companion that helps you return to the task you chose.', 17, WHITE)
    avatar = Image.new('RGBA', (480, 660), (0, 0, 0, 0))
    mira(ImageDraw.Draw(avatar), 0, 0, 2, 1)
    image = io.BytesIO(); avatar.save(image, format='PNG'); image.seek(0)
    c.drawImage(ImageReader(image), 354, 467, 198, 272, mask='auto')
    text(c, 42, 477, 'YOUR GOAL. YOUR LIMITS. YOUR CONTROL.', 11, TEAL, True)
    for y, title, body in [
        (434, 'Choose one next step', 'Start or pause focus, set a timer, or ask for a supported phone action.'),
        (333, 'Review together', 'Typed or optional voice drafts become bounded proposals. You confirm the action.'),
        (232, 'Make detours understandable', 'Opt-in app budgets and a simulated balance aim to support focus without real money deductions.')]:
        text(c, 42, y, title, 18, WHITE, True)
        paragraph(c, 42, y-16, W-84, body, 12, LILAC)
    paragraph(c, 42, 132, W-84, 'A pre-event CPU research prototype exists. Voice, persistent monitoring and iQOO hardware are verification goals, not demonstrated claims.', 10, TEAL)
    footer(c, 1, True); c.showPage()

    page(c, 2, 'Fast decisions, deliberate actions.', 'The language model proposes; Android validates and executes only a confirmed supported action.')
    card(c, 654, '1 / Observe with permission', 'Use the selected app, declared focus goal and consented usage summaries. No blanket screen capture or continuous microphone is implied.', 112)
    card(c, 523, '2 / Decide locally', 'Quick complete-request recognition can skip model loading. For fallback, explicitly load quantized Qwen3.5-0.8B Q4_0 and request one structured CPU prediction.', 126)
    card(c, 378, '3 / Validate, review, verify', 'Check original wording, quantities, units and allowed tools. Edits cancel stale proposals. Review and Confirm precede Android actions; external Clock outcomes require separate verification.', 126)
    card(c, 233, '4 / Explain bounded decisions', 'A separate 65-parameter positive-weight sandbox policy supports inspectable contributions. Qwen tensor summaries are observations, not proof of causal understanding.', 126)
    c.showPage()

    page(c, 3, 'What the prototype proves.', 'Evidence is tied to its tested artifact. A small diagnostic does not establish general phone automation accuracy.')
    card(c, 654, 'v0.18 / Built and installed', '208 JVM tests pass. Signed 5.94 MB light APK installed on Nothing with protected state preserved. Friendly draft-first screen implemented; physical layout, touch and voice remain unchecked.', 126)
    card(c, 509, 'v0.17 / Actual local CPU model', 'Six already-seen requests reached EOS with correct intent and argument slots; five supported proposals and one negation refusal. Model load: 2.24 s. Uncaptured requests: 3.31-5.74 s.', 126)
    card(c, 364, 'v0.17 / Observations and limits', 'Four finite 1024-wide tensor summaries captured. No causal interpretation or NPU claim. A restore client timed out; later read-only checks proved original package and protected state restored.', 126)
    card(c, 219, 'Coverage is still a product risk', 'On one fresh informed synthetic host set, the combined pipeline served 19/50 supported requests and refused all 50 unsupported requests. This is limited coverage, not autonomous reliability.', 126)
    c.showPage()

    page(c, 4, 'Build openly. Claim precisely.', 'Phase 1 idea deadline shown in the signed-in dashboard: 5 October 2026. Exact cutoff time/timezone still unverified.')
    card(c, 654, 'Pre-existing components disclosed', 'This repository contains dated pre-event research. Qwen3.5 and llama.cpp provide the selected model/runtime. Kev, Laya and Cua informed research; they are not claimed as deployed phone backends.', 126)
    card(c, 509, 'Original design and event work', 'Mira uses original project artwork inspired by the user\'s earlier productivity companion. No Grok character assets are copied. Eligible competition code must follow the event window or explicit organizer reuse approval.', 126)
    card(c, 364, 'Grand Finale execution plan', 'Verify local voice and opt-in monitor/floating lifecycles. Test the actual iQOO device and prove the chosen NPU backend or report CPU fallback. Demonstrate real Office Kit transfer, then record the live workflow.', 126)
    link(c, 205, 'Open-source prototype and evidence', 'https://github.com/sanjuhs/iqoo-focuspilot')
    link(c, 159, 'Current installable research build', 'https://github.com/sanjuhs/iqoo-focuspilot/releases/tag/research-v0.18')
    link(c, 113, 'Official guide and event restrictions', 'https://iqoo.reskilll.com/guide')
    c.save()
    record = {'pdf': str(OUT.relative_to(ROOT)), 'bytes': OUT.stat().st_size,
              'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(), 'pages': 4,
              'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [ROOT/'docs/mira-commands-artifact-v18.json', ROOT/'docs/mira-commands-phone-v18.json',
                                    ROOT/'docs/unit-native-phone-v17.json', ROOT/'docs/compatible-command-research.md',
                                    ROOT/'docs/phase1-dashboard-observation.json', Path(__file__), ROOT/'scripts/render_current_pitch.py']},
              'phone_capture_used': False, 'private_profile_data_used': False,
              'network_used': False, 'scope': 'Phase 1 concept document, not a submission receipt or final eligibility claim'}
    (ROOT/'artifacts/phase1-document-build.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
