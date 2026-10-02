#!/usr/bin/env python3
"""Own-app prerequisite-block and confirmed benign Pause TTS callback test."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import zipfile
from phone_model_smoke import PhoneLab, PACKAGE
from phone_focus_actions import MODEL_SHA
from phone_task_guide import checkpoint, preferences

TTS_OUTCOMES = {
    'Confirmed focus status read with an installed offline voice.': 'engine_completed_callback',
    'No installed offline English TTS voice is ready. Nothing was spoken.': 'offline_voice_unavailable',
    'Offline readback is unavailable here. The confirmed status stays on screen.': 'offline_voice_unavailable',
    'Offline readback could not start. Your status remains on screen.': 'engine_start_failed',
    'Offline readback failed. The status remains on screen.': 'engine_error_callback',
    'Offline readback timed out. Nothing else is blocked; your status remains on screen.': 'bounded_timeout',
    'Companion voice is muted. Your confirmed status remains on screen.': 'companion_muted',
}


def terminal_readback(texts):
    observed = [TTS_OUTCOMES[t] for t in texts if t in TTS_OUTCOMES]
    if len(set(observed)) > 1: raise RuntimeError('Conflicting terminal readback states')
    return observed[0] if observed else None


def permissions(lab):
    raw = lab.adb('shell', 'dumpsys', 'package', PACKAGE)
    return {name: bool(re.search(re.escape(name)+r': granted=true\b', raw)) for name in
            ('android.permission.RECORD_AUDIO', 'android.permission.POST_NOTIFICATIONS')}


def monitor_record_present(lab):
    raw = lab.adb('shell', 'dumpsys', 'activity', 'services', PACKAGE)
    return 'dev.focuspilot.prototype/.FocusMonitorService' in raw


def assert_inert_checkpoint(before, after):
    if before != after or before['active'] is not False or before['observation'] is not False:
        raise RuntimeError('Paused/off focus checkpoint changed; no further action')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--local-apk', type=Path, required=True)
    parser.add_argument('--expected-apk-sha256', required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute-reviewed-pause-readback', action='store_true')
    args = parser.parse_args()
    if not args.execute_reviewed_pause_readback: parser.error('Explicit --execute-reviewed-pause-readback required')
    if not re.fullmatch('[0-9a-f]{64}', args.expected_apk_sha256) or not re.fullmatch('[0-9a-f]{40}', args.source_commit): parser.error('Full identities required')
    with args.local_apk.open('rb') as stream: apk_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    if apk_sha != args.expected_apk_sha256: raise RuntimeError('Local APK mismatch')
    lab = PhoneLab(args.serial); lab.guard()
    installed = lab.adb('shell', 'pm', 'path', PACKAGE).strip().split('package:', 1)[1]
    if lab.adb('shell', 'sha256sum', installed).split()[0] != apk_sha: raise RuntimeError('Installed APK mismatch')
    model_sha = lab.adb('shell', 'run-as', PACKAGE, 'sha256sum', 'files/qwen35.gguf').split()[0]
    if model_sha != MODEL_SHA: raise RuntimeError('Retained model mismatch')
    before = checkpoint(preferences(lab)); assert_inert_checkpoint(before, before)
    if monitor_record_present(lab): raise RuntimeError('Own monitor service already present; left unchanged')
    with zipfile.ZipFile(args.local_apk) as apk: native_sha = hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()
    report = {'research_only': True, 'source_commit': args.source_commit, 'apk_sha256': apk_sha,
              'model_sha256': model_sha, 'native_sha256': native_sha, 'backend': 'CPU/KleidiAI I8MM',
              'before_checkpoint': before, 'runtime_grants_before': permissions(lab), 'phases': [],
              'microphone_started': False, 'permissions_or_settings_actions': False,
              'human_audibility_verified': False, 'offline_disconnect_verified': False,
              'speech_recognition_tested': False, 'npu_verified': False, 'completed': False,
              'device': {name: lab.adb('shell','getprop',prop).strip() for name,prop in
                         [('manufacturer','ro.product.manufacturer'),('model','ro.product.model'),('soc','ro.soc.model'),('api','ro.build.version.sdk')]}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save(): args.output.write_text(json.dumps(report, indent=2)+'\n')
    def phase(name, **details):
        current = checkpoint(preferences(lab)); assert_inert_checkpoint(before, current)
        report['phases'].append({'name': name, 'checkpoint_unchanged': True, **details}); save()
    save()
    try:
        lab.top()
        switch = lab.find('Keep this focus session in the background')
        if switch.get('checked') != 'false': raise RuntimeError('Monitor switch is not initially off')
        lab.tap('Keep this focus session in the background', scroll=False)
        blocked = 'To start the visible monitor, turn on usage reading and grant Usage Access first.'
        lab.find(blocked)
        lab.top(); reset = lab.find('Keep this focus session in the background')
        if reset.get('checked') != 'false' or monitor_record_present(lab): raise RuntimeError('Prerequisite block did not leave monitor off')
        phase('monitor_prerequisite_block', switch_restored_off=True, own_service_record_absent=True,
              scope='Observation is off, so early prerequisite guard applies; later notification/revocation branches were not reached')
        lab.top(); lab.tap('Ask Mira'); lab.tap('Load verified local model')
        for _ in range(16):
            if any(n.get('text','').startswith('LOCAL MODEL LOADED') for n in lab.nodes()): break
            time.sleep(.25)
        else: raise RuntimeError('Pinned local model did not load')
        result = lab.run('Stop focus'); report['typed_pause_result'] = result; save()
        if result['intent'] != 'pause_focus' or result['gate'] != 'REVIEW REQUIRED': raise RuntimeError('Expected reviewed Pause not proposed; nothing confirmed')
        lab.tap('Review proposed phone action')
        if not any('Pause focus and stop any active background focus monitor.' in n.get('text','') for n in lab.nodes()): raise RuntimeError('Review differs from bounded Pause')
        lab.tap('Confirm action', scroll=False)
        result['confirmation_tapped'] = True; save()
        lab.find('Focus paused; foreground monitor stop requested.')
        result['action_executed'] = True
        result['already_paused_before_action'] = True
        phase('reviewed_pause_on_already_paused_session', original_request='Stop focus', action_executed=True)
        lab.tap('Read confirmed focus status')
        report['readback_tapped'] = True; save(); began = time.monotonic()
        while time.monotonic()-began < 35:
            outcome = terminal_readback([n.get('text','') for n in lab.nodes()])
            if outcome is not None: break
            time.sleep(.25)
        else: raise RuntimeError('No terminal readback UI observed; do not claim engine completion')
        report['tts_outcome'] = outcome
        report['engine_completion_callback_observed'] = outcome == 'engine_completed_callback'
        phase('explicit_readback_terminal_ui', outcome=outcome, independently_audible=False)
        report['completed'] = True; save()
    except Exception as error:
        report['failure_type'] = type(error).__name__
        report['failure'] = str(error) if isinstance(error,(RuntimeError,ValueError)) else 'External operation failed; raw command/UI not exported'
        save(); raise
    finally:
        try:
            # Own app only: leave the model screen to stop readback and release its runtime.
            lab.adb('shell','am','start','-n',PACKAGE+'/.MainActivity','-f','0x04000000'); lab.guard()
            final = checkpoint(preferences(lab)); report['final_checkpoint'] = final
            report['runtime_grants_after'] = permissions(lab)
            report['own_monitor_service_record_absent_final'] = not monitor_record_present(lab)
            report['cleanup_verified'] = final == before and final['active'] is False and final['observation'] is False and report['own_monitor_service_record_absent_final']
        except Exception as error:
            report['cleanup_verified'] = False; report['cleanup_failure_type'] = type(error).__name__
        save()
    if not report['cleanup_verified']: raise RuntimeError('Final paused/off/service state not verified')
    print(json.dumps({'completed':report['completed'],'tts_outcome':report['tts_outcome'],
                      'human_audibility_verified':False,'cleanup_verified':report['cleanup_verified']}), flush=True)


if __name__ == '__main__': main()
