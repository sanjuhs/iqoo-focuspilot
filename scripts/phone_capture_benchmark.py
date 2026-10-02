#!/usr/bin/env python3
"""Paired own-app capture observations; no review/confirmation, mic or grants."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import time
import zipfile

from phone_model_smoke import PhoneLab, PACKAGE
from phone_focus_actions import MODEL_SHA
from phone_task_guide import checkpoint, preferences
from phone_readback import permissions, monitor_record_present

ORDERS = [(False, True), (True, False), (False, True), (True, False)]
COMMAND = 'Stop focus'


def memory(lab):
    raw = lab.adb('shell', 'dumpsys', 'meminfo', PACKAGE)
    values = {}
    for name in ('PSS', 'RSS'):
        match = re.search(r'TOTAL '+name+r':\s*(\d+)', raw)
        if not match: raise RuntimeError('Own-app memory sample unavailable')
        values[name.lower()+'_kib'] = int(match[1])
    return values


def trace(lab, capture):
    prefix = 'ACTUAL PREFILL TENSOR OBSERVATIONS' if capture else 'Capture disabled;'
    for _ in range(10):
        for node in lab.nodes():
            text = node.get('text', '')
            if text.startswith(prefix):
                if not capture: return []
                pattern = (r'\n([^\n]+) · width (\d+) · chunk positions (\d+)\n'
                           r'mean ([-\d.]+) · RMS ([-\d.]+) · range ([-\d.]+)…([-\d.]+)\n'
                           r'first values (\[[^\n]+\])')
                events = []
                for match in re.finditer(pattern, text):
                    event = dict(tensor=match[1], width=int(match[2]), positions_in_chunk=int(match[3]),
                                 mean=float(match[4]), rms=float(match[5]), min=float(match[6]),
                                 max=float(match[7]), first_values=json.loads(match[8]))
                    if not all(math.isfinite(v) for v in [event['mean'], event['rms'], event['min'],
                                                          event['max'], *event['first_values']]):
                        raise RuntimeError('Nonfinite displayed activation')
                    events.append(event)
                if not events: raise RuntimeError('Capture enabled but no actual tensor observations visible')
                return events
        lab.guard(); lab.adb('shell', 'input', 'swipe', '540', '1800', '540', '800', '250')
    raise RuntimeError('Activation result not visible')


def request_details(lab, capture):
    text = next(n.get('text','') for n in lab.nodes() if n.get('text','').startswith('Model proposal:'))
    setup = re.search(r'Context setup ([\d.]+) ms', text)
    tokens = re.search(r'(\d+) prompt tokens · (\d+) generated tokens · capture (on|off)', text)
    if not setup or not tokens or (tokens[3]=='on') != capture:
        raise RuntimeError('Request setup/token/capture identity missing')
    return dict(context_setup_ms=float(setup[1]), prompt_tokens=int(tokens[1]), generated_tokens=int(tokens[2]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--local-apk', type=Path, required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    lab = PhoneLab(args.serial); lab.guard()
    with args.local_apk.open('rb') as stream: apk_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    installed = lab.adb('shell', 'pm', 'path', PACKAGE).strip().split('package:', 1)[1]
    if lab.adb('shell', 'sha256sum', installed).split()[0] != apk_sha: raise RuntimeError('Installed APK differs')
    if lab.adb('shell', 'run-as', PACKAGE, 'sha256sum', 'files/qwen35.gguf').split()[0] != MODEL_SHA:
        raise RuntimeError('Pinned Qwen3.5 model differs')
    before = checkpoint(preferences(lab)); grants = permissions(lab)
    if before['active'] or before['observation'] or monitor_record_present(lab):
        raise RuntimeError('Requires paused focus, observation off and no own monitor')
    with zipfile.ZipFile(args.local_apk) as apk:
        native_sha = hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()
    report = dict(research_only=True, model='Qwen3.5-0.8B Q4_0', backend='CPU', context=1024,
                  threads=4, source_commit=args.source_commit, apk_sha256=apk_sha, model_sha256=MODEL_SHA,
                  native_sha256=native_sha, harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  pair_orders=ORDERS, command=COMMAND, before_checkpoint=before, permissions_before=grants,
                  trials=[], action_executed=False, microphone_started=False, npu_verified=False,
                  device={k: lab.adb('shell','getprop',p).strip() for k,p in
                          [('manufacturer','ro.product.manufacturer'),('model','ro.product.model'),
                           ('soc','ro.soc.model'),('api','ro.build.version.sdk')]}, completed=False,
                  memory_scope='Post-request PSS/RSS snapshots, not peak or continuous memory',
                  activation_scope='UI-rounded summaries of latest prefill chunk/last position; observational only')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save(): args.output.write_text(json.dumps(report, indent=2)+'\n')
    save()
    try:
        lab.top(); lab.tap('Ask Mira'); lab.tap('Load verified local model')
        for _ in range(16):
            if any(n.get('text','').startswith('LOCAL MODEL LOADED') for n in lab.nodes()): break
            time.sleep(.25)
        else: raise RuntimeError('Model did not load')
        report['loaded_memory'] = memory(lab)
        report['warmup'] = lab.run(COMMAND, False); save()
        for pair, order in enumerate(ORDERS):
            for capture in order:
                result = lab.run(COMMAND, capture)
                result.update(request_details(lab,capture))
                result.update(pair=pair+1, activations=trace(lab,capture), memory=memory(lab))
                if result['intent'] != 'pause_focus' or result['gate'] != 'REVIEW REQUIRED':
                    raise RuntimeError('Repeated command prediction changed; nothing confirmed')
                if checkpoint(preferences(lab)) != before: raise RuntimeError('Focus checkpoint changed')
                report['trials'].append(result); save()
                print(json.dumps({k:result[k] for k in ('pair','capture','total_ms','prefill_ms','decode_ms','memory')}),flush=True)
        deltas = []
        for pair in range(1,len(ORDERS)+1):
            rows = {r['capture']:r for r in report['trials'] if r['pair']==pair}
            if any(rows[True][k] != rows[False][k] for k in ('intent','gate','prompt_tokens','generated_tokens')):
                raise RuntimeError('Pair output/token counts differ; timings cannot isolate capture')
            deltas.append(rows[True]['total_ms']-rows[False]['total_ms'])
        report['paired_total_deltas_ms'] = deltas
        report['median_paired_delta_ms'] = statistics.median(deltas)
        report['completed'] = True; save()
    except Exception as error:
        report['failure_type'] = type(error).__name__
        report['failure'] = str(error) if isinstance(error,(RuntimeError,ValueError)) else 'External operation failed'
        save(); raise
    finally:
        try:
            lab.guard(); lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000'); lab.guard()
            report['final_checkpoint'] = checkpoint(preferences(lab))
            report['permissions_after'] = permissions(lab)
            report['cleanup_verified'] = (report['final_checkpoint']==before and permissions(lab)==grants
                                          and not monitor_record_present(lab))
        except Exception:
            report['cleanup_verified'] = False
        save()
    if not report['cleanup_verified']: raise RuntimeError('Final checkpoint/permissions not verified')


if __name__ == '__main__': main()
