#!/usr/bin/env python3
"""Eight-scene v20 research pitch. Local speech and deterministic illustrations.

Explicit preparation/rendering; current evidence and historical footage have
separate source identities. No phone, model, API, download or existing overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from PIL import Image, ImageDraw
from package_bundled_apk import project_bytes
from render_current_pitch import (BG, INK, MUTED, TEAL, LILAC, GOLD, RED,
    box, clamp, dot, ease, lines, mira, path, sha, text, timestamp)
import render_v012_pitch as media

OUT = ROOT / 'artifacts/v020-pitch'
SOURCE = ROOT / 'docs/v020-research-pitch-script.md'
W, H, FPS = 1920, 1080, 24
LIMIT, RESERVATION, GLOBAL_CACHE_GROWTH = 15_000_000_000, 600_000_000, 218_929_328
EVIDENCE = (
    'docs/mira-availability-artifact-v20.json',
    'docs/mira-availability-phone-install-v20.json',
    'docs/mira-availability-bundle-artifact-v20.json',
    'docs/mira-availability-publication-v20.json',
    'docs/native-page-phone-result-v19.json',
    'docs/demo-capture-phone-v012.json',
    'docs/guidance-readback-artifacts.json',
    'docs/guide-readback-phone-v012.json',
    'prototype/policy/synthetic-model.json',
    'prototype/policy/synthetic-model-results.json',
    'prototype/policy/policy.py',
)
HELPERS = ('scripts/render_current_pitch.py', 'scripts/render_v012_pitch.py',
           'scripts/package_bundled_apk.py', 'prototype/v020-pitch/render.py',
           'prototype/v020-pitch/README.md', 'docs/v020-research-pitch-script.md')
MODEL = '57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'


def fail(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_json(file, value):
    with file.open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def regular(name, prefix=None):
    return media.public_path(name, prefix)


def frozen(name, commit, expected=None, current=True):
    media.full_hash(commit, 40)
    p = Path(name)
    fail(not p.is_absolute() and '..' not in p.parts, 'Require relative frozen path')
    content = subprocess.check_output(['git', '-C', str(ROOT), 'show', commit + ':' + name])
    digest = hashlib.sha256(content).hexdigest()
    if expected is not None:
        fail(digest == media.full_hash(expected), 'Historical source binding differs: ' + name)
    if current:
        fail(sha(regular(name)) == digest, 'Uncommitted or changed frozen input: ' + name)
    return {'sha256': digest, 'source_commit': commit, 'current_bytes_required': current}


def storage_guard(initial=False):
    project = project_bytes(ROOT)
    output = project_bytes(OUT) if OUT.exists() else 0
    effective = project + GLOBAL_CACHE_GROWTH
    fail(effective <= LIMIT and output <= RESERVATION, 'Strict project/output storage budget exceeded')
    remaining = RESERVATION - output
    if initial:
        fail(effective + remaining <= LIMIT, 'Insufficient storage for remaining 600 MB reservation')
    fail(shutil.disk_usage(ROOT).free >= (remaining if initial else 50_000_000), 'Insufficient filesystem space')
    return {'project_bytes': project, 'new_global_cache_bytes': GLOBAL_CACHE_GROWTH,
            'effective_bytes': effective, 'output_bytes': output,
            'output_reservation_bytes': RESERVATION, 'project_limit_bytes': LIMIT}


def parse_source():
    chunks = re.split(r'^## Scene (\d+): (.+)$', SOURCE.read_text(), flags=re.M)
    scenes = []
    for n in range(1, len(chunks), 3):
        beats = re.findall(r'^> (.+)$', chunks[n + 2], flags=re.M)
        visual = re.search(r'^Visual: (.+)$', chunks[n + 2], re.M)
        fail(len(beats) == 3 and visual is not None, 'Each scene needs three narration beats and Visual direction')
        scenes.append({'index': int(chunks[n]) - 1, 'title': chunks[n + 1],
                       'utterances': beats, 'visual_intent': visual.group(1)})
    fail([s['index'] for s in scenes] == list(range(8)), 'Require eight ordered scenes')
    return scenes


def inputs(commit):
    bindings = {name: frozen(name, commit) for name in (*EVIDENCE, *HELPERS)}
    records = [json.loads(regular(name).read_text()) for name in EVIDENCE[:8]]
    package, install, bundle, published, cpu, film, historical, old_phone = records
    fail(package['tests'] == {'tests': 216, 'failures': 0, 'errors': 0, 'skipped': 0}
         and package['lint'] == {'Warning': 79}, 'Current v20 build counts differ')
    fail(package['source_commit'] == '81287b2b08ccedc050635b0b8a27154bed3b5d87'
         and package['apk_sha256'] == 'e128bd1986bad10ff00f385a22f0a1b70ac696ab7c42a547e65717a1d8789239'
         and package['internet_permission'] is False and package['physical_lock_unlock_verified'] is False,
         'Current build scope changed')
    for name, digest in package['source_sha256'].items():
        bindings['current:' + name] = frozen(name, package['source_commit'], digest)
    fail(install['passed'] is True and install['protected_state_unchanged'] is True
         and install['original_test_unchanged'] is True and install['attempts'] == 1
         and install['installed_target_sha256'] == package['apk_sha256']
         and install['source_commit'] == package['source_commit'], 'Current installation differs')
    fail(bundle['app_source_commit'] == package['source_commit']
         and bundle['light']['sha256'] == package['apk_sha256']
         and bundle['model']['sha256'] == MODEL and bundle['original_payload_parity_verified'] is True
         and bundle['current_bundle_import_verified'] is False, 'Current bundle scope differs')
    artifacts = {}
    for item in (bundle['light'], bundle['bundle']):
        file = regular(item['file'], 'artifacts')
        fail(file.stat().st_size == item['bytes'] and sha(file) == item['sha256'], 'APK identity differs')
        artifacts[item['file']] = {'bytes': item['bytes'], 'sha256': item['sha256']}
    fail(published['tag_commit'] == package['source_commit'], 'v20 publication attribution differs')
    for item in published['assets']:
        file = regular(item['file'])
        fail(sha(file) == item['sha256'] and file.stat().st_size == item['bytes']
             and item['server_digest'] == 'sha256:' + item['sha256'], 'Published local asset binding differs')
    fail(cpu['passed'] is True and cpu['completed_native_requests'] == 6 and cpu['runtime_checks'] == 313
         and cpu['raw_full_slot_matches'] == 6 and cpu['requests_already_seen'] is True
         and cpu['page_size_bytes'] == 4096 and cpu['npu_verified'] is False
         and cpu['model_sha256'] == MODEL and cpu['native_sha256'] == package['native_sha256'], 'v19 CPU scope differs')
    fail(set(cpu['routes']) == {'checked_model', 'fast_local', 'product_pipeline'}
         and all(r == {'complete_supported_proposals': 5, 'unsupported_refusals': 1, 'wrong_accepts': 0}
             for r in cpu['routes'].values()), 'v19 route counts differ')
    for flag in ('completed', 'cleanup_verified', 'visual_privacy_review'):
        fail(film[flag] is True, 'Historical footage privacy/completion unverified')
    fail(film['microphone_started'] is False and film['npu_verified'] is False
         and film['action_confirmed'] is False, 'Historical footage scope differs')
    fail(historical['source_commit'] == film['source_commit']
         and historical['model']['sha256'] == MODEL, 'Historical package attribution differs')
    for key in ('source_commit', 'apk_sha256', 'model_sha256', 'native_sha256'):
        fail(film[key] == old_phone[key], 'Historical phone/package identities differ')
    fail(old_phone['completed'] is True and old_phone['cleanup_verified'] is True,
         'Historical guide report incomplete')
    old_artifact = next(a for a in historical['artifacts'] if a['sha256'] == film['apk_sha256'])
    fail(old_artifact['native_sha256'] == film['native_sha256'], 'Historical native attribution differs')
    for name, digest in historical['source_sha256'].items():
        bindings['historical:' + name] = frozen(name, film['source_commit'], digest, current=False)
    bindings['historical:scripts/phone_demo_capture.py'] = frozen(
        'scripts/phone_demo_capture.py', film['pre_run_commit'], film['harness_sha256'], current=False)
    request = film['typed_model_request']
    fail(request['command'] == 'Stop focus' and request['capture'] is True
         and request['intent'] == 'pause_focus' and request['gate'] == 'REVIEW REQUIRED'
         and request['action_executed'] is False, 'Historical filmed command scope differs')
    fail(all(type(request[k]) in (float, int) and math.isfinite(request[k]) and request[k] >= 0
             for k in ('total_ms', 'prefill_ms', 'decode_ms'))
         and abs(request['total_ms'] - request['prefill_ms'] - request['decode_ms']) <= 3,
         'Historical request timings differ')
    clips = {}
    fail(len(film['clips']) == 2, 'Require exactly two historical clips')
    for clip in film['clips']:
        file = regular(clip['file'], 'artifacts/v012-phone-demo')
        fail(clip['name'] in ('guide', 'model') and clip['name'] not in clips
             and sha(file) == clip['sha256'] and file.stat().st_size == clip['bytes']
             and clip['speed'] == 1 and clip['audio_track'] is False, 'Historical footage bytes/speed differ')
        info = media.probe(file)
        streams = [s for s in info['streams'] if s['codec_type'] == 'video']
        length = float(info['format']['duration'])
        fail(len(streams) == 1 and not any(s['codec_type'] == 'audio' for s in info['streams'])
             and streams[0]['width'] > 100 and streams[0]['height'] > 100
             and math.isfinite(length) and length > 0
             and abs(length - clip['seconds']) <= .15, 'Historical footage duration differs')
        clips[clip['name']] = {key: clip[key] for key in ('name', 'file', 'sha256', 'bytes', 'seconds')}
        clips[clip['name']].update(measured_seconds=length, resolution=[streams[0]['width'], streams[0]['height']])
    activation = film['activation_observations']
    fail(len(activation) == 4 and {v['tensor'] for v in activation} == {'ffn_out-0', 'ffn_out-11', 'ffn_out-23', 'result_norm'}
         and all(v['width'] == 1024 and len(v['first_values']) == 8
         and all(math.isfinite(n) for n in [v['mean'], v['rms'], v['min'], v['max'], *v['first_values']])
         for v in activation), 'Historical activation dimensions differ')
    return {'execution_source_commit': commit, 'current_app_source_commit': package['source_commit'],
            'historical_app_source_commit': film['source_commit'], 'evidence_bindings': bindings,
            'artifact_bindings': artifacts, 'clips': clips, 'authored_steps': old_phone['synthetic_steps'],
            'historical_model_request': request, 'historical_activations': activation,
            'current_jvm_tests': 216, 'current_lint_warnings': 79, 'v19_cpu_load_ms': cpu['model_load_ms'],
            'v19_cpu_source_commit': cpu['app_source_commit'], 'v19_cpu_counts': cpu['routes'],
            'current_light_sha256': package['apk_sha256'], 'bundle_sha256': bundle['bundle']['sha256'],
            'model_sha256': MODEL, 'native_sha256': package['native_sha256'],
            'publication_remote_verification': 'Attributed to frozen root publication record; renderer verifies local byte parity only'}


def prepare(bound, voice, rate):
    fail(not OUT.exists(), 'Output already exists; only explicit --reuse-timeline may reuse preparation')
    OUT.mkdir(parents=True, exist_ok=False)
    write_json(OUT / 'inputs.json', bound)
    audio = OUT / 'speech'; audio.mkdir()
    gap = audio / 'gap.aiff'
    media.run(['ffmpeg', '-v', 'error', '-n', '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono',
               '-t', '0.30', '-c:a', 'pcm_s16be', gap])
    gap_seconds = media.seconds(gap)
    scenes, captions, files, clock = parse_source(), [], [], 0.
    for scene in scenes:
        scene['start'], scene['beats'] = clock, []
        for utterance in scene['utterances']:
            number = len(captions) + 1
            source, spoken = audio / f'{number:02}.txt', audio / f'{number:02}.aiff'
            with source.open('x') as stream: stream.write(utterance)
            fail(not spoken.exists(), 'Speech output exists')
            media.run(['say', '-v', voice, '-r', rate, '-o', spoken, '-f', source])
            length = media.seconds(spoken)
            beat = {'start': clock, 'end': clock + length, 'text': utterance, 'scene': scene['index'] + 1}
            captions.append(beat); scene['beats'].append(beat); files.extend([spoken, gap]); clock += length + gap_seconds
            storage_guard()
        scene['end'], scene['duration'] = clock, clock - scene['start']
        print(f"Scene {scene['index'] + 1}: {scene['duration']:.3f}s", flush=True)
    fail(180 <= clock <= 300, f'Measured {clock:.3f}s must fit 3–5 minutes; preserve failed attempt')
    mapping = []
    for name, index in [('guide', 1), ('model', 2)]:
        scene, clip = scenes[index], bound['clips'][name]
        fail(clip['measured_seconds'] <= scene['duration'], 'Full historical clip must fit at 1x')
        mapping.append({'clip': name, 'scene': index + 1, 'pitch_start': scene['start'], 'pitch_end': scene['end'],
                        'source_start_seconds': 0, 'source_end_seconds': clip['measured_seconds'], 'playback_speed': 1,
                        'final_frame_hold_seconds': scene['duration'] - clip['measured_seconds'],
                        'attribution': 'HISTORICAL v0.12', 'audio': 'omitted; generated local narration only'})
    concat = audio / 'concat.txt'
    with concat.open('x') as stream: stream.write('\n'.join("file '" + str(f) + "'" for f in files) + '\n')
    media.run(['ffmpeg', '-v', 'error', '-n', '-f', 'concat', '-safe', '0', '-i', concat,
               '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', OUT / 'narration.wav'])
    with (OUT / 'pitch-v020.srt').open('x') as stream:
        stream.write('\n\n'.join(f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n" +
                     '\n'.join(textwrap.wrap(c['text'], width=92)) for i, c in enumerate(captions, 1)) + '\n')
    header = ('[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n'
              '[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
              'Style: Default,Arial,34,&H00FAF0F4,&H00FAF0F4,&H00160E10,&H00160E10,0,0,0,0,100,100,0,0,1,0,0,2,110,110,34,1\n'
              '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    events = []
    for c in captions:
        words = '\\N'.join(textwrap.wrap(c['text'].replace('{', '(').replace('}', ')'), width=92))
        events.append(f"Dialogue: 0,{timestamp(c['start'], True)},{timestamp(c['end'], True)},Default,,0,0,0,,{words}")
    with (OUT / 'pitch-v020.ass').open('x') as stream: stream.write(header + '\n'.join(events) + '\n')
    timeline = {'scenes': scenes, 'captions': captions, 'seconds': clock, 'clip_segments': mapping}
    write_json(OUT / 'timeline.json', timeline)
    names = ('inputs.json', 'timeline.json', 'narration.wav', 'pitch-v020.srt', 'pitch-v020.ass')
    prepared = {'voice': voice, 'words_per_minute': rate, 'files_sha256': {n: sha(OUT / n) for n in names},
                'speech_sha256': {str(f.relative_to(OUT)): sha(f) for f in sorted(set(files))},
                'measured_seconds': clock, 'caption_segments': 24, 'storage': storage_guard()}
    write_json(OUT / 'prepared-audio.json', prepared)
    return timeline, prepared


def phone(d, x, y, portrait=False, locked=False, t=0):
    box(d, (x, y, x + 300, y + 505), LILAC, '#100E16', 38)
    d.line((x + 115, y + 22, x + 185, y + 22), fill=MUTED, width=5)
    if locked:
        d.arc((x + 119, y + 180, x + 181, y + 248), 180, 360, fill=GOLD, width=8)
        box(d, (x + 108, y + 214, x + 192, y + 290), GOLD)
        text(d, (x + 65, y + 336), 'LOCKED', 30, GOLD, True)
    elif portrait:
        mira(d, x + 42, y + 65, .9, t)
        text(d, (x + 55, y + 420), 'Ask / Hide', 26, TEAL, True)
    else:
        text(d, (x + 77, y + 216), 'HIDDEN', 29, MUTED, True)


def shot(scene, t, bound, trace, activation):
    image = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(image)
    local = t - scene['start']
    phase = max(n for n, b in enumerate(scene['beats']) if t >= b['start'])
    beat = scene['beats'][phase]; q = ease((t - beat['start']) / 2.2); i = scene['index']
    text(d, (78, 36), 'MIRA / FOCUSPILOT', 25, TEAL, True)
    text(d, (1230, 40), 'PRE-EVENT RESEARCH / v0.20', 24, GOLD, True)
    text(d, (80, 96), scene['title'], 44, INK, True)
    text(d, (80, 163), f'{i + 1:02}/08 · ' + ('HISTORICAL v0.12 recording' if i in (1, 2) else 'Source-bound illustration'), 21, MUTED)
    if i == 0:
        mira(d, 1280, 218, 1.8, local)
        text(d, (145, 275), 'One task. Many detours.', 59, LILAC, True)
        text(d, (180, 439), 'Your chosen goal', 40, INK, True)
        path(d, (195, 515), (1120, 515), q if phase == 0 else 1, TEAL)
        if phase >= 1:
            d.arc((440, 435, 850, 805), 0, 180, fill=RED, width=6)
            dot(d, (645 + 190 * math.cos(math.pi * q), 620 + 105 * math.sin(math.pi * q)), 15, RED)
            text(d, (470, 750), 'A distraction is a detour', 31, MUTED)
        if phase == 2:
            path(d, (1010, 700), (1120, 535), q, TEAL)
            text(d, (145, 834), 'Your limits · virtual points · your choice', 37, TEAL, True)
    elif i in (1, 2):
        box(d, (1320, 212, 1800, 890), LILAC, '#100E16')
        text(d, (1325, 185), 'HISTORICAL v12 · 1× SPEED', 21, GOLD, True)
        clip = bound['clips']['guide' if i == 1 else 'model']
        if local >= clip['measured_seconds']:
            text(d, (1355, 866), 'FINAL FRAME HELD', 21, GOLD, True)
        if i == 1:
            for n, label in enumerate(bound['authored_steps']):
                y = 280 + n * 155
                dot(d, (170, y + 24), 23, TEAL if n <= phase else LILAC)
                lines(d, (215, y), label, 38, INK, 1000, True)
                if n < 2: path(d, (170, y + 59), (170, y + 129), q if phase == n else 1, TEAL, 4)
            text(d, (145, 775), 'Authored steps · completion by you', 33, TEAL, True)
            text(d, (145, 837), 'Readback callback ≠ verified speaker audibility', 27, GOLD)
        else:
            text(d, (170, 283), '“Stop focus”', 63, LILAC, True)
            path(d, (405, 385), (405, 490), q if phase == 0 else 1, TEAL)
            text(d, (170, 510), 'Qwen3.5-0.8B Q4_0 · CPU', 42, TEAL, True)
            if phase >= 1:
                path(d, (405, 578), (405, 660), q, TEAL)
                text(d, (170, 683), 'Proposal → gate → review', 37, INK, True)
            if phase == 2:
                text(d, (170, 770), f"v12 capture: {bound['historical_model_request']['total_ms']:,.0f} ms", 32, GOLD)
                text(d, (170, 834), 'One seen case · no action confirmed', 27, MUTED)
    elif i == 3:
        text(d, (125, 254), 'Editable request', 39, INK, True)
        dot(d, (220, 392), 22, LILAC)
        path(d, (245, 392), (650, 300), q if phase == 0 else 1, TEAL)
        text(d, (680, 263), 'Exact local match', 35, TEAL, True)
        text(d, (680, 318), 'No model call', 27, MUTED)
        path(d, (1040, 310), (1430, 465), q if phase == 0 else 1, TEAL)
        box(d, (1440, 410, 1810, 605), TEAL)
        text(d, (1480, 455), 'Your review', 37, TEAL, True)
        text(d, (1480, 522), 'Then Confirm', 29, INK)
        if phase >= 1:
            path(d, (240, 420), (650, 603), q, LILAC)
            text(d, (675, 540), 'Explicit Qwen fallback', 34, LILAC, True)
            text(d, (675, 595), 'Original request + exact slots', 27, MUTED)
            path(d, (1070, 590), (1420, 530), q, LILAC)
        if phase == 2:
            path(d, (1070, 660), (1360, 775), q, RED)
            d.line((1360, 728, 1360, 822), fill=RED, width=11)
            text(d, (1400, 755), 'Refuse / cancel', 34, RED, True)
        text(d, (145, 855), 'Pipeline illustration · not a new accuracy or latency measurement', 27, GOLD)
    elif i == 4:
        # Three identities persist: phone, reviewed FGS lease, explicit stop switch.
        phone(d, 125, 269, portrait=True, t=local)
        text(d, (130, 790), 'Reviewed Show', 31, TEAL, True)
        path(d, (440, 490), (730, 490), q if phase == 0 else 1, TEAL)
        phone(d, 750, 269, locked=phase >= 1, portrait=phase == 0, t=local)
        text(d, (735, 795), 'Same idle service', 30, LILAC, True)
        if phase >= 1:
            text(d, (720, 218), 'Window + refresh removed', 27, GOLD, True)
            path(d, (1065, 490), (1300, 490), q if phase == 1 else 1, GOLD, dashed=True)
        if phase == 2:
            last = clamp((t - beat['start']) / max(.1, beat['end'] - beat['start']))
            stopped = last >= .65
            phone(d, 1320, 269, portrait=not stopped, t=local)
            text(d, (1280, 217), 'Recheck → unlock return', 28, TEAL, True)
            if stopped:
                box(d, (1310, 697, 1675, 780), RED)
                text(d, (1360, 720), 'HIDE → STOP', 32, RED, True)
                path(d, (1490, 684), (1490, 624), 1, RED)
            else:
                text(d, (1350, 794), 'Only this session', 28, TEAL)
        text(d, (120, 855), 'Default off · Android may stop it · physical lock/unlock still pending', 27, GOLD)
    elif i == 5:
        text(d, (110, 237), 'HISTORICAL v12 · observed tensors', 29, GOLD, True)
        for n, value in enumerate(activation):
            y = 318 + n * 103
            text(d, (110, y), value['tensor'], 26, LILAC, True)
            numbers = value['first_values']; limit = max(abs(v) for v in numbers) or 1
            for index, number in enumerate(numbers):
                x = 420 + index * 43
                extent = number / limit * 29 * (q if phase == 0 else 1)
                d.line((x, y + 27, x, y + 27 - extent), fill=TEAL if number >= 0 else RED, width=13)
        text(d, (110, 754), '4 × width 1,024 · first eight values', 27, INK, True)
        text(d, (110, 795), 'Normalized per vector; no shared amplitude scale', 23, MUTED)
        text(d, (110, 837), 'Observation ≠ causal meaning', 27, GOLD)
        d.line((930, 240, 930, 854), fill='#50445F', width=2)
        text(d, (1040, 237), 'Synthetic shadow · 65 parameters', 30, TEAL, True)
        chosen = max(trace['hidden_units'], key=lambda u: u['logit_contribution'])['unit']
        xs, ys = [1080, 1380, 1700], [[360 + n * 43 for n in range(6)], [326 + n * 40 for n in range(8)], [480]]
        for a in range(6):
            for b in range(8): path(d, (xs[0], ys[0][a]), (xs[1], ys[1][b]), q if phase == 1 else 1, '#484054', 2)
        for b in range(8):
            path(d, (xs[1], ys[1][b]), (xs[2], ys[2][0]), q if phase == 1 else 1,
                 RED if phase == 2 and b == chosen else TEAL, 3)
        for layer in range(3):
            for n, y in enumerate(ys[layer]): dot(d, (xs[layer], y), 14, RED if phase == 2 and layer == 1 and n == chosen else LILAC)
        text(d, (1040, 652), 'Synthetic inputs [0,1]: .8 .3 .2 .7 .1 .2', 25, MUTED)
        score = trace['probability'] if phase < 2 else trace['hidden_units'][chosen]['probability_if_suppressed']
        text(d, (1070, 690), f'Synthetic score {score:.3f}', 34, TEAL, True)
        if phase == 2: text(d, (1070, 758), f'Unit {chosen} suppressed in this toy', 29, RED, True)
        text(d, (1070, 826), 'Shadow only · hand-set live policy', 26, GOLD)
    elif i == 6:
        text(d, (130, 237), 'v20 source → signed APK → installation', 43, TEAL, True)
        for n, (x, label) in enumerate([(140, '81287b2b'), (745, 'e128bd19'), (1350, 'Protected state')]):
            dot(d, (x + 80, 392), 32, TEAL if n <= phase else LILAC)
            text(d, (x, 463), label, 34, INK, True)
            if n < 2: path(d, (x + 145, 392), (x + 555, 392), q if phase == n else 1, TEAL)
        if phase >= 1:
            for n in range(216): dot(d, (150 + (n % 36) * 22, 570 + (n // 36) * 23), 5, TEAL)
            text(d, (1030, 566), '216 JVM tests · lint: 0 errors', 37, TEAL, True)
            text(d, (1030, 630), '79 warnings retained', 30, MUTED)
        if phase == 2:
            text(d, (145, 778), 'v19 CPU: 6 seen requests / 313 checks', 36, GOLD, True)
            text(d, (1030, 778), f"Load {bound['v19_cpu_load_ms'] / 1000:.3f}s · 4 KB", 34, GOLD, True)
        text(d, (145, 853), 'Bundle: same app + pinned weights; current import and unlocked workflows pending', 25, MUTED)
    else:
        mira(d, 1360, 273, 1.55, local)
        labels = ['Physical Mira + permitted voice', 'iQOO backend / NPU verification', 'Actual Office Kit bridge']
        for n, label in enumerate(labels):
            y = 293 + n * 136
            dot(d, (160, y + 20), 17, GOLD if n <= phase else MUTED)
            text(d, (205, y), label, 39, GOLD if n <= phase else MUTED, True)
        if phase == 2:
            path(d, (160, 768), (1240, 768), q, TEAL)
            text(d, (160, 704), 'Eligible event code → reviewed submission', 35, TEAL, True)
        text(d, (145, 851), '9–11 October event · pre-event prototype is not an eligible or accepted entry', 26, MUTED)
    d.rectangle((0, 903, W, H), fill='#100E16'); d.line((80, 902, 1840, 902), fill='#50445F', width=2)
    return image


def render(timeline, prepared, bound):
    reserved = ('base.mp4', 'pitch-v020.mp4', 'render-manifest.json', 'policy-trace.json',
                *(f'preview-{n:02}.png' for n in range(1, 9)))
    fail(not any((OUT / name).exists() for name in reserved), 'Render output exists; no overwrite or retry')
    # These module-local hooks reuse the pure frame/seek algorithm, never historical inputs/render writers.
    media.OUT, media.shot = OUT, shot
    trace, activation = media.policy_trace(), bound['historical_activations']
    write_json(OUT / 'policy-trace.json', trace)
    checks = media.seek_checks(timeline, bound, trace, activation)
    base = OUT / 'base.mp4'
    encoder = subprocess.Popen(['ffmpeg', '-v', 'warning', '-n', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0', '-t', f"{timeline['seconds']:.6f}",
        '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-maxrate', '3M',
        '-bufsize', '6M', '-threads', '2', '-pix_fmt', 'yuv420p', base], stdin=subprocess.PIPE)
    try:
        frames = math.ceil(timeline['seconds'] * FPS)
        for n in range(frames):
            encoder.stdin.write(media.frame(n / FPS, timeline, bound, trace, activation).tobytes())
            if n % (FPS * 10) == 0:
                storage_guard(); print(f'Frames {n}/{frames}', flush=True)
        encoder.stdin.close(); fail(encoder.wait() == 0, 'Frame encoding failed')
    except BaseException:
        if encoder.poll() is None: encoder.terminate(); encoder.wait()
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
    filters.append(f'[{previous}]ass={OUT / "pitch-v020.ass"}[video]')
    video = OUT / 'pitch-v020.mp4'
    command = ['ffmpeg', '-v', 'warning', '-n', '-i', base]
    for mapping in maps: command.extend(['-i', regular(bound['clips'][mapping['clip']]['file'])])
    command.extend(['-i', OUT / 'narration.wav', '-filter_complex', ';'.join(filters), '-map', '[video]',
        '-map', '3:a:0', '-t', f"{timeline['seconds']:.6f}", '-c:v', 'libx264', '-preset', 'veryfast',
        '-crf', '21', '-maxrate', '3M', '-bufsize', '6M', '-threads', '2', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', video])
    media.run(command); storage_guard()
    info = media.probe(video); videos = [s for s in info['streams'] if s['codec_type'] == 'video']
    audios = [s for s in info['streams'] if s['codec_type'] == 'audio']; measured = float(info['format']['duration'])
    fail(len(videos) == 1 and len(audios) == 1 and [videos[0]['width'], videos[0]['height']] == [W, H]
         and videos[0]['r_frame_rate'] == '24/1' and 180 <= measured <= 300
         and abs(measured - timeline['seconds']) <= .15, 'Encoded streams/duration differ')
    media.run(['ffmpeg', '-v', 'error', '-i', video, '-f', 'null', '-'])
    fail(inputs(bound['execution_source_commit']) == bound, 'Source/evidence changed during rendering')
    validate_prepared(bound, prepared['voice'], prepared['words_per_minute'])
    manifest = {'kind': 'v20 pre-event research pitch; historical v12 own-app clips plus current source-bound illustrations',
        'completed': True, 'submission_accepted': False, 'eligible_event_code_verified': False,
        'bindings': bound, 'prepared_audio_sha256': sha(OUT / 'prepared-audio.json'),
        'video': str(video.relative_to(ROOT)), 'video_sha256': sha(video), 'bytes': video.stat().st_size,
        'seconds': measured, 'resolution': [W, H], 'fps': FPS, 'caption_segments': 24,
        'captions_sha256': sha(OUT / 'pitch-v020.srt'), 'ass_sha256': sha(OUT / 'pitch-v020.ass'),
        'narration_sha256': sha(OUT / 'narration.wav'), 'voice': prepared['voice'],
        'words_per_minute': prepared['words_per_minute'], 'timeline': timeline,
        'deterministic_seek_checks': checks, 'full_decode_passed': True,
        'phone_capture_used': True, 'phone_capture_attribution': 'HISTORICAL v0.12; no v20 screen capture',
        'phone_clip_speed': 1, 'clip_audio_used': False, 'renderer_phone_actions_executed': 0,
        'human_complete_audio_review': False, 'human_speaker_audibility_verified': False,
        'physical_v20_overlay_lock_unlock_verified': False, 'current_bundle_import_verified': False,
        'npu_verified': False, 'officekit_verified': False, 'runtime_16k_verified': False,
        'activation_summaries_establish_causal_meaning': False, 'new_model_calls': 0,
        'offline_disconnect_verified': False, 'encoded_visual_review_complete': False,
        'storage': storage_guard()}
    write_json(OUT / 'render-manifest.json', manifest)
    print(json.dumps({'video': manifest['video'], 'seconds': measured, 'bytes': manifest['bytes']}), flush=True)


def validate_prepared(bound, voice, rate):
    prepared = json.loads((OUT / 'prepared-audio.json').read_text())
    fail(prepared['voice'] == voice and prepared['words_per_minute'] == rate, 'Prepared voice/rate differs')
    for name, digest in {**prepared['files_sha256'], **prepared['speech_sha256']}.items():
        file = regular(str((OUT / name).relative_to(ROOT)), 'artifacts/v020-pitch')
        fail(sha(file) == digest, 'Prepared media/timing changed')
    fail(json.loads((OUT / 'inputs.json').read_text()) == bound, 'Prepared frozen bindings changed')
    timeline = json.loads((OUT / 'timeline.json').read_text())
    fail([s['index'] for s in timeline['scenes']] == list(range(8)) and len(timeline['captions']) == 24,
         'Prepared scene/caption contract differs')
    return timeline, prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-only', action='store_true'); mode.add_argument('--render', action='store_true')
    parser.add_argument('--reuse-timeline', action='store_true'); parser.add_argument('--source-commit', required=True)
    parser.add_argument('--voice', default='Samantha'); parser.add_argument('--rate', type=int, default=170)
    args = parser.parse_args()
    if args.reuse_timeline and not args.render: parser.error('--reuse-timeline requires --render')
    if not 130 <= args.rate <= 210: parser.error('Speech rate must be 130–210 wpm')
    for tool in ('say', 'ffmpeg', 'ffprobe'):
        fail(shutil.which(tool) is not None, 'Required local tool unavailable: ' + tool)
    fail(not OUT.is_symlink(), 'Output symlinks are refused')
    storage_guard(initial=True); bound = inputs(args.source_commit)
    if args.reuse_timeline: timeline, prepared = validate_prepared(bound, args.voice, args.rate)
    else: timeline, prepared = prepare(bound, args.voice, args.rate)
    if args.render: render(timeline, prepared, bound)


if __name__ == '__main__':
    main()
