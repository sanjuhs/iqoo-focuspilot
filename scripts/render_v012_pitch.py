#!/usr/bin/env python3
"""Source-bound v0.12 research pitch, with two real own-app clips at original speed.

Local macOS speech and streamed deterministic Pillow frames; no network or phone
control. Preparation and rendering require separate explicit modes. Older pitch
assets are never written. A completed render is not a submission or audio review.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap

from PIL import Image, ImageDraw
from package_bundled_apk import project_bytes
from render_current_pitch import (
    BG, INK, MUTED, TEAL, LILAC, GOLD, RED, box, clamp, dot, ease,
    lines, mira, path, sha, text, timestamp,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/v012-pitch'
SOURCE = ROOT / 'docs/v012-research-pitch-script.md'
W, H, FPS = 1920, 1080, 24
LIMIT = 15_000_000_000
RESERVATION = 600_000_000
EVIDENCE = (
    'docs/guidance-readback-artifacts.json',
    'docs/guide-readback-phone-v012.json',
    'docs/capture-benchmark-phone-v011.json',
    'prototype/policy/synthetic-model.json',
    'prototype/policy/synthetic-model-results.json',
    'prototype/policy/policy.py',
)


def run(args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def probe(file):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_format', '-show_streams',
        '-of', 'json', str(file),
    ], text=True))


def seconds(file):
    value = float(probe(file)['format']['duration'])
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Media duration must be finite and positive')
    return value


def logical_bytes(directory):
    return project_bytes(directory)


def storage_guard(initial=False):
    project = logical_bytes(ROOT)
    output = logical_bytes(OUT) if OUT.exists() else 0
    if project > LIMIT or output > RESERVATION:
        raise RuntimeError('Strict project/output storage budget exceeded')
    if initial and project + RESERVATION > LIMIT:
        raise RuntimeError('Insufficient project budget for 600 MB output reservation')
    if shutil.disk_usage(ROOT).free < (RESERVATION if initial else 50_000_000):
        raise RuntimeError('Insufficient filesystem space for bounded rendering')
    return {'project_bytes': project, 'output_bytes': output,
            'project_limit_bytes': LIMIT, 'output_reservation_bytes': RESERVATION}


def public_path(value, prefix=None):
    p = Path(value)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Require a project-relative public evidence path')
    target = ROOT / p
    if not target.resolve().is_relative_to(ROOT.resolve()) or target.is_symlink():
        raise ValueError('Evidence must be a regular project file')
    if prefix and not target.resolve().is_relative_to((ROOT / prefix).resolve()):
        raise ValueError('Footage must remain under its dedicated capture directory')
    if not target.is_file():
        raise ValueError('Required evidence file unavailable: ' + str(p))
    return target


def full_hash(value, size=64):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{' + str(size) + '}', value):
        raise ValueError('Full lowercase source/hash identity required')
    return value


def committed_binding(file):
    relative = str(file.relative_to(ROOT))
    commit = subprocess.check_output([
        'git', '-C', str(ROOT), 'log', '-1', '--format=%H', '--', relative,
    ], text=True).strip()
    full_hash(commit, 40)
    content = subprocess.check_output(['git', '-C', str(ROOT), 'show', commit + ':' + relative])
    digest = sha(file)
    if hashlib.sha256(content).hexdigest() != digest:
        raise RuntimeError('Source must be committed before preparation: ' + relative)
    return {'sha256': digest, 'source_commit': commit}


def parse_source():
    chunks = re.split(r'^## Scene (\d+): (.+)$', SOURCE.read_text(), flags=re.M)
    scenes = []
    for n in range(1, len(chunks), 3):
        beats = re.findall(r'^> (.+)$', chunks[n + 2], flags=re.M)
        visual = re.search(r'^Visual: (.+)$', chunks[n + 2], re.M)
        if len(beats) != 3 or visual is None:
            raise ValueError('Every scene requires three narration beats and Visual direction')
        scenes.append({'index': int(chunks[n]) - 1, 'title': chunks[n + 1],
                       'utterances': beats, 'visual_intent': visual.group(1)})
    if [s['index'] for s in scenes] != list(range(8)):
        raise ValueError('Require exactly eight ordered scenes')
    return scenes


def inputs(record_path):
    record_file = public_path(record_path, 'artifacts/v012-phone-demo')
    record = json.loads(record_file.read_text())
    if record.get('completed') is not True or record.get('cleanup_verified') is not True:
        raise RuntimeError('Footage run must complete with verified cleanup')
    if record.get('visual_privacy_review') is not True:
        raise RuntimeError('Root must review cropped footage for privacy before preparation/rendering')
    for flag in ('microphone_started', 'npu_verified'):
        if record.get(flag) is not False:
            raise RuntimeError('This renderer requires the bounded no-mic/CPU recording scope')
    full_hash(record.get('source_commit'), 40)
    capture_commit = full_hash(record.get('pre_run_commit'), 40)
    capture_hash = full_hash(record.get('harness_sha256'))
    capture_path = 'scripts/phone_demo_capture.py'
    capture_file = public_path(capture_path)
    capture_source = subprocess.check_output([
        'git', '-C', str(ROOT), 'show', capture_commit + ':' + capture_path,
    ])
    if sha(capture_file) != capture_hash or hashlib.sha256(capture_source).hexdigest() != capture_hash:
        raise RuntimeError('Capture harness differs from its frozen pre-run identity')
    for key in ('apk_sha256', 'model_sha256', 'native_sha256'):
        full_hash(record.get(key))
    request = record.get('typed_model_request', {})
    if (request.get('command') != 'Stop focus' or request.get('capture') is not True
            or request.get('intent') != 'pause_focus' or request.get('gate') != 'REVIEW REQUIRED'
            or request.get('action_executed') is not False):
        raise RuntimeError('Recorded model proposal differs from the narrated bounded request')
    for key in ('total_ms', 'prefill_ms', 'decode_ms'):
        value = request.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise RuntimeError('Recorded native request timing must be finite and nonnegative')
    if abs(request['total_ms'] - request['prefill_ms'] - request['decode_ms']) > 3:
        raise RuntimeError('Recorded rounded total and phase timings differ')
    package = json.loads(public_path(EVIDENCE[0]).read_text())
    phone = json.loads(public_path(EVIDENCE[1]).read_text())
    if package['source_commit'] != record['source_commit']:
        raise RuntimeError('Footage app revision differs from package manifest')
    artifact = next((a for a in package['artifacts'] if a['sha256'] == record['apk_sha256']), None)
    if (artifact is None or artifact['native_sha256'] != record['native_sha256']
            or package['model']['sha256'] != record['model_sha256']):
        raise RuntimeError('Footage APK/model/native differ from inspected package')
    if phone.get('completed') is not True or phone.get('cleanup_verified') is not True:
        raise RuntimeError('Historical v0.12 phone report is incomplete')
    if any(phone.get(key) != record[key] for key in
           ('source_commit', 'apk_sha256', 'model_sha256', 'native_sha256')):
        raise RuntimeError('Historical phone report attribution differs')
    clips = record.get('clips', [])
    if len(clips) != 2 or {c.get('name') for c in clips} != {'guide', 'model'}:
        raise RuntimeError('Exactly one guide clip and one model clip required')
    validated = {}
    for clip in clips:
        file = public_path(clip['file'], 'artifacts/v012-phone-demo')
        if sha(file) != full_hash(clip.get('sha256')):
            raise RuntimeError('Footage bytes differ from pre-run recording identity')
        info = probe(file)
        streams = [s for s in info['streams'] if s['codec_type'] == 'video']
        length = float(clip.get('seconds', 0))
        measured = float(info['format']['duration'])
        if (not math.isfinite(length) or length <= 0 or abs(length - measured) > .15
                or len(streams) != 1 or streams[0]['width'] < 100 or streams[0]['height'] < 100):
            raise RuntimeError('Footage duration/stream identity differs')
        validated[clip['name']] = {**clip, 'measured_seconds': measured,
                                   'resolution': [streams[0]['width'], streams[0]['height']]}
    bindings = {name: committed_binding(public_path(name)) for name in EVIDENCE}
    bindings[str(SOURCE.relative_to(ROOT))] = committed_binding(SOURCE)
    bindings[str(Path(__file__).resolve().relative_to(ROOT))] = committed_binding(Path(__file__).resolve())
    helper = ROOT / 'scripts/render_current_pitch.py'
    bindings[str(helper.relative_to(ROOT))] = committed_binding(helper)
    bindings[capture_path] = committed_binding(capture_file)
    budget_helper = ROOT / 'scripts/package_bundled_apk.py'
    bindings[str(budget_helper.relative_to(ROOT))] = committed_binding(budget_helper)
    for name, expected in package['source_sha256'].items():
        if sha(public_path(name)) != expected:
            raise RuntimeError('Current app source differs from inspected APK source: ' + name)
        content = subprocess.check_output(['git', '-C', str(ROOT), 'show', record['source_commit'] + ':' + name])
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError('Committed app source differs from inspected APK source')
    return {'footage_record': str(record_file.relative_to(ROOT)), 'footage_record_sha256': sha(record_file),
            'record': record, 'clips': validated, 'evidence_bindings': bindings,
            'app_source_sha256': package['source_sha256'], 'package_jvm_tests': package['build']['jvm']['tests'],
            'authored_steps': record.get('synthetic_steps', phone['synthetic_steps'])}


def policy_trace():
    checkpoint = json.loads((ROOT / EVIDENCE[3]).read_text())
    code = ROOT / EVIDENCE[5]
    if sha(code) != checkpoint['implementation_sha256'] or checkpoint['parameter_count'] != 65:
        raise RuntimeError('Synthetic policy/source identity changed')
    spec = importlib.util.spec_from_file_location('v012_pitch_policy', code)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.PositiveNetwork(checkpoint['parameters']).inspect([.8, .3, .2, .7, .1, .2])


def historical_activations():
    report = json.loads((ROOT / EVIDENCE[2]).read_text())
    if report.get('completed') is not True or report.get('cleanup_verified') is not True:
        raise RuntimeError('Historical capture report incomplete')
    rows = [r['activations'] for r in report['trials'] if r['capture']]
    expected = {'ffn_out-0', 'ffn_out-11', 'ffn_out-23', 'result_norm'}
    for row in rows:
        if len(row) != 4 or {v['tensor'] for v in row} != expected:
            raise RuntimeError('Four historical selected summaries not established')
        for v in row:
            if v['width'] != 1024 or len(v['first_values']) != 8:
                raise RuntimeError('Unexpected historical activation dimensions')
            if not all(math.isfinite(n) for n in [v['mean'], v['rms'], v['min'], v['max'], *v['first_values']]):
                raise RuntimeError('Historical summaries must be finite')
    if len(rows) != 4:
        raise RuntimeError('Four captured historical trials required')
    return rows[0]


def prepare(bound, voice, rate):
    if (OUT / 'timeline.json').exists():
        raise RuntimeError('Prepared timeline exists; use --reuse-timeline or a separately reviewed new output')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'inputs.json').write_text(json.dumps(bound, indent=2) + '\n')
    audio = OUT / 'speech'
    audio.mkdir(exist_ok=False)
    gap = audio / 'gap.aiff'
    run(['ffmpeg', '-v', 'error', '-n', '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono',
         '-t', '0.30', '-c:a', 'pcm_s16be', gap])
    gap_seconds = seconds(gap)
    scenes, captions, audio_files, clock = parse_source(), [], [], 0.
    for scene in scenes:
        scene['start'], scene['beats'] = clock, []
        for utterance in scene['utterances']:
            number = len(captions) + 1
            source, spoken = audio / f'{number:02}.txt', audio / f'{number:02}.aiff'
            source.write_text(utterance)
            run(['say', '-v', voice, '-r', rate, '-o', spoken, '-f', source])
            length = seconds(spoken)
            beat = {'start': clock, 'end': clock + length, 'text': utterance, 'scene': scene['index'] + 1}
            captions.append(beat); scene['beats'].append(beat); audio_files.extend([spoken, gap])
            clock += length + gap_seconds
        scene['end'], scene['duration'] = clock, clock - scene['start']
        print(f"Scene {scene['index'] + 1}: {scene['duration']:.3f} seconds", flush=True)
    if not 180 <= clock <= 300:
        raise ValueError(f'Measured narration {clock:.3f}s must fit 3–5 minutes; revise narration/rate')
    mapping = []
    for name, index in [('guide', 1), ('model', 2)]:
        scene, clip = scenes[index], bound['clips'][name]
        if clip['measured_seconds'] > scene['duration']:
            raise RuntimeError('Full 1x clip does not fit narrated scene: ' + name)
        mapping.append({'clip': name, 'scene': index + 1, 'pitch_start': scene['start'],
                        'pitch_end': scene['end'], 'source_start_seconds': 0,
                        'source_end_seconds': clip['measured_seconds'], 'playback_speed': 1,
                        'final_frame_hold_seconds': scene['duration'] - clip['measured_seconds'],
                        'audio': 'clip audio omitted; only separately generated local narration'})
    concat = audio / 'concat.txt'
    concat.write_text('\n'.join("file '" + str(f) + "'" for f in audio_files) + '\n')
    run(['ffmpeg', '-v', 'error', '-n', '-f', 'concat', '-safe', '0', '-i', concat,
         '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', OUT / 'narration.wav'])
    srt = '\n\n'.join(f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n" +
                       '\n'.join(textwrap.wrap(c['text'], width=92))
                       for i, c in enumerate(captions, 1)) + '\n'
    (OUT / 'pitch-v012.srt').write_text(srt)
    header = ('[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n'
              '[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
              'Style: Default,Arial,34,&H00FAF0F4,&H00FAF0F4,&H00160E10,&H00160E10,0,0,0,0,100,100,0,0,1,0,0,2,110,110,34,1\n'
              '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    events = []
    for c in captions:
        words = '\\N'.join(textwrap.wrap(c['text'].replace('{', '(').replace('}', ')'), width=92))
        events.append(f"Dialogue: 0,{timestamp(c['start'], True)},{timestamp(c['end'], True)},Default,,0,0,0,,{words}")
    (OUT / 'pitch-v012.ass').write_text(header + '\n'.join(events) + '\n')
    timeline = {'scenes': scenes, 'captions': captions, 'seconds': clock, 'clip_segments': mapping}
    (OUT / 'timeline.json').write_text(json.dumps(timeline, indent=2) + '\n')
    files = ('inputs.json', 'timeline.json', 'narration.wav', 'pitch-v012.srt', 'pitch-v012.ass')
    prepared = {'voice': voice, 'words_per_minute': rate, 'files_sha256': {f: sha(OUT / f) for f in files},
                'speech_sha256': {str(f.relative_to(OUT)): sha(f) for f in audio_files if f != gap},
                'measured_seconds': clock, 'caption_segments': 24, 'storage': storage_guard()}
    (OUT / 'prepared-audio.json').write_text(json.dumps(prepared, indent=2) + '\n')
    return timeline, prepared


def shot(scene, t, bound, trace, activation):
    image = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(image)
    local = t - scene['start']
    phase = max(n for n, beat in enumerate(scene['beats']) if t >= beat['start'])
    beat = scene['beats'][phase]
    q = ease((t - beat['start']) / 2.2)
    i = scene['index']
    text(d, (78, 36), 'MIRA / FOCUSPILOT', 25, TEAL, True)
    text(d, (1300, 40), 'PRE-EVENT RESEARCH / v0.12', 24, GOLD, True)
    text(d, (80, 96), scene['title'], 44, INK, True)
    text(d, (80, 162), f'{i + 1:02}/08 · ' + ('Actual own-app clip + illustration' if i in (1, 2) else 'Source-bound illustration'), 21, MUTED)
    if i == 0:
        mira(d, 1250, 220, 1.85, local)
        text(d, (145, 290), 'A smaller next step.', 61, LILAC, True)
        box(d, (145, 410, 770, 625), TEAL)
        lines(d, (185, 447), 'Your chosen task stays close.', 45, INK, 535, True)
        path(d, (795, 508), (1175, 508), q if phase == 0 else 1., TEAL)
        if phase >= 1:
            text(d, (145, 700), 'Friendly. Local. Under your control.', 40, TEAL, True)
        if phase == 2:
            text(d, (145, 802), 'Nothing development phone · Android research build', 29, GOLD)
    elif i in (1, 2):
        # FFmpeg supplies original-speed clip pixels inside this stable phone frame.
        box(d, (1320, 212, 1800, 890), LILAC, '#100E16')
        text(d, (1325, 185), 'OWN-APP RECORDING · 1× SPEED', 21, TEAL, True)
        clip = bound['clips']['guide' if i == 1 else 'model']
        if local >= clip['measured_seconds']:
            text(d, (1355, 865), 'FINAL FRAME HELD', 22, GOLD, True)
        if i == 1:
            labels = bound['authored_steps']
            for n, label in enumerate(labels):
                y = 260 + n * 160
                dot(d, (170, y + 30), 24, TEAL if n <= phase else LILAC)
                lines(d, (216, y + 5), label, 37, INK, 950, True)
                if n < 2:
                    path(d, (170, y + 65), (170, y + 132), q if phase == n else 1., TEAL, 4)
            text(d, (145, 790), 'Authored by you · completion marked by you', 30, GOLD)
            text(d, (145, 843), 'Readback callback ≠ independent speaker audibility', 25, MUTED)
        else:
            box(d, (145, 265, 1110, 420), LILAC)
            text(d, (185, 307), '“Stop focus”', 53, LILAC, True)
            path(d, (625, 450), (625, 540), q if phase == 0 else 1., TEAL)
            text(d, (185, 555), 'Qwen3.5-0.8B · Q4_0 · CPU', 44, TEAL, True)
            if phase >= 1:
                text(d, (185, 647), 'Proposal → independent request gate → review', 32, INK)
            if phase == 2:
                total = bound['record']['typed_model_request']['total_ms']
                text(d, (185, 756), f'Recorded request: {total:,.0f} ms native CPU', 30, GOLD)
                text(d, (185, 812), 'One case; capture enabled; no action confirmed', 25, MUTED)
    elif i == 3:
        names = [('Request', 135), ('Model proposal', 575), ('Original-text gate', 1015), ('Your review', 1455)]
        for n, (label, x) in enumerate(names):
            box(d, (x, 295, x + 330, 435), LILAC if n == 1 else TEAL)
            lines(d, (x + 25, 337), label, 32, INK, 285, True)
            if n < 3 and (n <= phase):
                path(d, (x + 330, 365), (x + 430, 365), q if n == phase else 1., TEAL)
        if phase >= 1:
            path(d, (1620, 464), (1620, 570), q, RED)
            box(d, (1380, 600, 1820, 735), RED)
            text(d, (1420, 640), 'Cancel / no action', 35, RED, True)
        if phase == 2:
            text(d, (145, 646), '100 virtual points', 51, GOLD, True)
            text(d, (145, 731), 'No real money deduction', 37, INK)
        text(d, (145, 836), 'Explanatory diagram · no unrecorded confirmation or action is animated', 26, MUTED)
    elif i == 4:
        text(d, (120, 236), 'HISTORICAL v0.11 / ACTUAL PHONE SUMMARIES', 28, GOLD, True)
        for n, event in enumerate(activation):
            y = 305 + n * 125
            text(d, (120, y), event['tensor'], 28, LILAC, True)
            text(d, (120, y + 42), 'width 1,024', 21, MUTED)
            values = event['first_values']
            limit = max(abs(v) for v in values) or 1
            for index, value in enumerate(values):
                x = 600 + index * 57
                extent = value / limit * 37 * (q if phase == 0 else 1.)
                d.line((x, y + 32, x, y + 32 - extent), fill=TEAL if value >= 0 else RED, width=18)
            text(d, (1130, y + 12), f"RMS {event['rms']:.5f}", 26, INK)
        if phase >= 1:
            text(d, (1440, 320), 'Observe', 44, TEAL, True)
            path(d, (1520, 390), (1520, 515), q, GOLD)
            text(d, (1400, 540), 'Intervene + test', 32, GOLD, True)
        if phase == 2:
            text(d, (1400, 657), 'Meaning needs', 31, MUTED)
            text(d, (1400, 708), 'causal evidence.', 33, GOLD, True)
        text(d, (120, 845), 'First eight values per vector · latest prefill chunk · observational only', 27, MUTED)
    elif i == 5:
        xs, ys = [300, 840, 1300], [[285 + n * 75 for n in range(6)], [260 + n * 57 for n in range(8)], [470]]
        chosen = max(trace['hidden_units'], key=lambda u: u['logit_contribution'])['unit']
        for a in range(6):
            for b in range(8):
                path(d, (xs[0] + 20, ys[0][a]), (xs[1] - 20, ys[1][b]), q if phase == 0 else 1., '#484054', 2)
        for b in range(8):
            path(d, (xs[1] + 20, ys[1][b]), (xs[2] - 20, ys[2][0]), q if phase == 1 else 1.,
                 RED if phase == 2 and b == chosen else TEAL, 3)
        for layer in range(3):
            for n, y in enumerate(ys[layer]):
                dot(d, (xs[layer], y), 19, RED if layer == 1 and phase == 2 and n == chosen else LILAC)
        text(d, (110, 775), '6 inputs → 8 ReLU units → 1 sigmoid', 30, INK, True)
        text(d, (1420, 270), '65', 110, LILAC, True)
        text(d, (1420, 410), 'parameters', 30, INK)
        value = trace['probability'] if phase < 2 else trace['hidden_units'][chosen]['probability_if_suppressed']
        text(d, (1400, 520), f'Toy score {value:.3f}', 34, TEAL, True)
        if phase == 2:
            text(d, (1400, 595), f'Unit {chosen} ablated', 28, RED)
        text(d, (110, 842), 'Synthetic training · shadow only · nonnegative weights / signed biases', 28, GOLD)
    elif i == 6:
        mira(d, 1330, 280, 1.6, local)
        box(d, (135, 260, 1170, 425), TEAL)
        text(d, (180, 303), 'github.com/sanjuhs/iqoo-focuspilot', 36, TEAL, True)
        if phase >= 1:
            text(d, (180, 505), f"{bound['package_jvm_tests']} JVM tests", 60, LILAC, True)
            text(d, (180, 598), 'Exact source + package + physical evidence', 32, INK)
        if phase == 2:
            for n, label in enumerate(['Mute', 'Hide', 'Stop', 'Opt-in']):
                box(d, (180 + n * 230, 700, 370 + n * 230, 783), GOLD)
                text(d, (210 + n * 230, 720), label, 28, GOLD, True)
        text(d, (180, 836), 'Host checks and physical outcomes answer different questions.', 28, MUTED)
    else:
        mira(d, 1270, 240, 1.8, local)
        labels = ['iQOO hardware + verified backend', 'Actual Office Kit connection', 'Voice + consented monitoring']
        for n, label in enumerate(labels):
            y = 295 + n * 148
            dot(d, (145, y + 20), 15, GOLD)
            text(d, (190, y), label, 35, GOLD if n <= phase else MUTED, True)
        if phase == 2:
            text(d, (150, 772), 'Warm companion. Visible next steps.', 39, TEAL, True)
        text(d, (150, 846), 'Pre-event preparation · eligible event build and accepted submission still ahead', 25, MUTED)
    d.rectangle((0, 903, W, H), fill='#100E16')
    d.line((80, 902, 1840, 902), fill='#50445F', width=2)
    return image


def frame(t, timeline, bound, trace, activation):
    scenes = timeline['scenes']
    scene = next((s for s in scenes if s['start'] <= t < s['end']), scenes[-1])
    image = shot(scene, t, bound, trace, activation)
    local = t - scene['start']
    if scene['index'] > 0 and local < .4:
        previous = scenes[scene['index'] - 1]
        image = Image.blend(shot(previous, previous['end'] - 1e-6, bound, trace, activation), image, clamp(local / .4))
    return image


def seek_checks(timeline, bound, trace, activation):
    checks = []
    for scene in timeline['scenes']:
        times = [min(scene['end'] - 1 / FPS, b['start'] + 1) for b in scene['beats']]
        images = [frame(t, timeline, bound, trace, activation) for t in times]
        hashes = [hashlib.sha256(i.tobytes()).hexdigest() for i in images]
        # Evaluate a different time between identical seeks; no mutable frame state may leak.
        frame(scene['end'] - 1e-6, timeline, bound, trace, activation)
        repeated = hashlib.sha256(frame(times[0], timeline, bound, trace, activation).tobytes()).hexdigest()
        if hashes[0] != repeated or len(set(hashes)) != 3:
            raise RuntimeError('Deterministic seek or scene explanatory progression check failed')
        checks.append({'scene': scene['index'] + 1, 'times': times, 'rgb_sha256': hashes, 'backward_seek_matches': True})
        images[1].resize((960, 540)).save(OUT / f"preview-{scene['index'] + 1:02}.png")
    return checks


def render(timeline, prepared, bound):
    for name in ('base.mp4', 'pitch-v012.mp4', 'render-manifest.json'):
        if (OUT / name).exists():
            raise RuntimeError('Refusing to overwrite existing v0.12 render asset: ' + name)
    trace, activation = policy_trace(), historical_activations()
    (OUT / 'policy-trace.json').write_text(json.dumps(trace, indent=2) + '\n')
    checks = seek_checks(timeline, bound, trace, activation)
    base = OUT / 'base.mp4'
    encoder = subprocess.Popen([
        'ffmpeg', '-v', 'warning', '-n', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0', '-t', f"{timeline['seconds']:.6f}",
        '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-maxrate', '3M',
        '-bufsize', '6M', '-threads', '2', '-pix_fmt', 'yuv420p', base,
    ], stdin=subprocess.PIPE)
    try:
        frames = math.ceil(timeline['seconds'] * FPS)
        for n in range(frames):
            encoder.stdin.write(frame(n / FPS, timeline, bound, trace, activation).tobytes())
            if n % (FPS * 10) == 0:
                storage_guard()
                print(f'Procedural frames {n}/{frames}', flush=True)
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError('Procedural stream encoding failed')
    except BaseException:
        encoder.terminate(); encoder.wait()
        raise
    filters, maps = [], timeline['clip_segments']
    for n, mapping in enumerate(maps, 1):
        span = mapping['pitch_end'] - mapping['pitch_start']
        filters.append(f'[{n}:v]fps=24,scale=430:640:force_original_aspect_ratio=decrease,'
                       f'pad=430:640:(ow-iw)/2:(oh-ih)/2:color=0x17151f,setsar=1,'
                       f'tpad=stop_mode=clone:stop_duration={span:.6f},trim=duration={span:.6f},'
                       f'setpts=PTS-STARTPTS+{mapping["pitch_start"]:.6f}/TB[clip{n}]')
    previous = '0:v'
    for n, mapping in enumerate(maps, 1):
        filters.append(f'[{previous}][clip{n}]overlay=x=1345:y=220:eof_action=pass:'
                       f'enable=between(t\\,{mapping["pitch_start"]:.6f}\\,{mapping["pitch_end"]:.6f})[over{n}]')
        previous = 'over' + str(n)
    filters.append(f'[{previous}]ass={OUT / "pitch-v012.ass"}[video]')
    # Original source clips are decoded by FFmpeg; no per-frame phone images are loaded by Python.
    video = OUT / 'pitch-v012.mp4'
    command = ['ffmpeg', '-v', 'warning', '-n', '-i', base]
    for mapping in maps:
        command.extend(['-i', public_path(bound['clips'][mapping['clip']]['file'])])
    command.extend(['-i', OUT / 'narration.wav', '-filter_complex', ';'.join(filters),
                    '-map', '[video]', '-map', '3:a:0', '-t', f"{timeline['seconds']:.6f}",
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-maxrate', '3M',
                    '-bufsize', '6M', '-threads', '2', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                    '-b:a', '160k', '-movflags', '+faststart', video])
    run(command)
    info = probe(video)
    stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
    measured = float(info['format']['duration'])
    if ([stream['width'], stream['height']] != [W, H] or stream['r_frame_rate'] != '24/1'
            or not 180 <= measured <= 300 or abs(measured - timeline['seconds']) > .15):
        raise RuntimeError('Encoded duration/resolution/frame-rate differs')
    run(['ffmpeg', '-v', 'error', '-i', video, '-f', 'null', '-'])
    # Revalidate pre-run sources and footage after encoding; evidence cannot change unnoticed.
    if inputs(bound['footage_record']) != bound:
        raise RuntimeError('Source/evidence/footage changed during rendering')
    manifest = {'kind': 'Edited v0.12 pre-event research pitch; real own-app clips plus original procedural illustrations',
                'completed': True, 'submission_accepted': False, 'eligible_event_code_verified': False,
                'bindings': bound, 'prepared_audio_sha256': sha(OUT / 'prepared-audio.json'),
                'video': str(video.relative_to(ROOT)), 'video_sha256': sha(video), 'bytes': video.stat().st_size,
                'seconds': measured, 'resolution': [W, H], 'fps': FPS, 'caption_segments': 24,
                'captions_sha256': sha(OUT / 'pitch-v012.srt'), 'narration_sha256': sha(OUT / 'narration.wav'),
                'voice': prepared['voice'], 'words_per_minute': prepared['words_per_minute'],
                'timeline': timeline, 'deterministic_seek_checks': checks, 'full_decode_passed': True,
                'phone_capture_used': True, 'phone_clip_speed': 1, 'clip_audio_used': False,
                'renderer_phone_actions_executed': 0, 'human_complete_audio_review': False,
                'human_speaker_audibility_verified': False, 'npu_verified': False,
                'officekit_verified': False, 'offline_disconnect_verified': False,
                'storage': storage_guard(), 'encoded_visual_review_complete': False}
    (OUT / 'render-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'video': manifest['video'], 'seconds': measured, 'bytes': manifest['bytes']}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-only', action='store_true')
    mode.add_argument('--render', action='store_true')
    parser.add_argument('--reuse-timeline', action='store_true')
    parser.add_argument('--footage-manifest', default='artifacts/v012-phone-demo/record.json')
    parser.add_argument('--voice', default='Samantha')
    parser.add_argument('--rate', type=int, default=170)
    args = parser.parse_args()
    if args.reuse_timeline and not args.render:
        parser.error('--reuse-timeline is only valid with --render')
    if not 130 <= args.rate <= 210:
        parser.error('Speech rate must be 130–210 words per minute')
    for tool in ('say', 'ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise RuntimeError('Required local tool unavailable: ' + tool)
    storage_guard(initial=True)
    bound = inputs(args.footage_manifest)
    if args.reuse_timeline:
        prepared = json.loads((OUT / 'prepared-audio.json').read_text())
        if any(sha(OUT / name) != digest for name, digest in prepared['files_sha256'].items()):
            raise RuntimeError('Prepared timeline/audio/captions changed')
        if json.loads((OUT / 'inputs.json').read_text()) != bound:
            raise RuntimeError('Pre-run source/evidence/footage bindings changed')
        timeline = json.loads((OUT / 'timeline.json').read_text())
    else:
        timeline, prepared = prepare(bound, args.voice, args.rate)
    if args.render:
        render(timeline, prepared, bound)


if __name__ == '__main__':
    main()
