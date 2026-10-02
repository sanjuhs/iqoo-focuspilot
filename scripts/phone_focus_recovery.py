#!/usr/bin/env python3
"""Reviewed synthetic own-app countdown/pause/recovery test; no OS settings edits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import zipfile

from phone_model_smoke import PhoneLab, PACKAGE
from phone_focus_actions import MODEL_SHA
from phone_task_guide import preferences, checkpoint, require_empty_test_state
from phone_readback import permissions, monitor_record_present

APP_SOURCE = '24f10b62a4a62c22ad6db90ac6339f29e2426dbd'
APK_SHA = '4ebd8097c9f3ff4a4cf5f12ecc5b80c1a8974b561c8e4ac733db1d77662583a0'
NATIVE_SHA = '822695ae5ca3467392f48ff04d9eda824f52a5f470ba48264fd457f51881259e'


def snapshot(lab):
    values = preferences(lab)
    return {**checkpoint(values), 'timed': values.get('timedCheckpoint', False),
            'remaining_ms': values.get('remainingCheckpoint', 0),
            'completed': values.get('completedCheckpoint', False)}


def wait_state(lab, predicate, timeout=4):
    deadline = time.monotonic()+timeout
    while True:
        state = snapshot(lab)
        if predicate(state): return state
        if time.monotonic() >= deadline: raise RuntimeError('Expected persisted focus state not observed')
        time.sleep(.1)


def preserved_budget(before, after):
    return not after['observation'] and before['points'] == after['points']


def assert_target(state, base_elapsed, duration_ms=20_000):
    if not state['timed'] or state['elapsed_ms']+state['remaining_ms'] != base_elapsed+duration_ms:
        raise RuntimeError('Countdown elapsed/remainder accounting changed')


def reviewed_proposal(lab, command):
    result = lab.run(command, wake_display=False)
    if result['intent'] != 'start_focus' or result['gate'] != 'REVIEW REQUIRED':
        raise RuntimeError('Expected reviewed Start proposal; nothing confirmed')
    lab.tap('Review proposed phone action')
    preview = ('Start a focus countdown for 20 seconds' if '20 seconds' in command
               else 'Start or resume focus')
    if not any(preview in n.get('text', '') for n in lab.nodes()):
        raise RuntimeError('Review does not preserve expected bounded action')
    return result


def open_model(lab):
    lab.top(); lab.tap('Ask Mira'); lab.tap('Load verified local model')
    for _ in range(20):
        if any(n.get('text', '').startswith('LOCAL MODEL LOADED') for n in lab.nodes()): return
        time.sleep(.25)
    raise RuntimeError('Pinned model not loaded')


def main_screen(lab):
    lab.adb('shell', 'am', 'start', '-n', PACKAGE+'/.MainActivity', '-f', '0x04000000')
    lab.guard()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--local-apk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute-reviewed-recovery', action='store_true')
    args = parser.parse_args()
    if not args.execute_reviewed_recovery: parser.error('Explicit reviewed recovery flag required')
    if args.output.exists(): raise RuntimeError('Refuse to overwrite prior evidence')
    root = Path(__file__).resolve().parents[1]
    harness_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip()
    if dirty or not re.fullmatch('[0-9a-f]{40}', harness_commit):
        raise RuntimeError('Commit harness and keep worktree clean before phone actions')
    with args.local_apk.open('rb') as stream:
        apk_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    if apk_sha != APK_SHA: raise RuntimeError('Selected local APK mismatch')
    with zipfile.ZipFile(args.local_apk) as apk:
        native_sha = hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()
    if native_sha != NATIVE_SHA: raise RuntimeError('Selected native mismatch')
    lab = PhoneLab(args.serial); lab.guard()  # Never wake or bypass a locked/off display.
    installed = lab.adb('shell', 'pm', 'path', PACKAGE).strip().split('package:', 1)[1]
    if lab.adb('shell', 'sha256sum', installed).split()[0] != apk_sha: raise RuntimeError('Installed APK mismatch')
    if lab.adb('shell', 'run-as', PACKAGE, 'sha256sum', 'files/qwen35.gguf').split()[0] != MODEL_SHA:
        raise RuntimeError('Retained model mismatch')
    require_empty_test_state(preferences(lab))
    before = snapshot(lab); grants = permissions(lab)
    if monitor_record_present(lab): raise RuntimeError('Existing monitor left unchanged')
    report = {'research_only': True, 'app_source_commit': APP_SOURCE,
              'harness_commit': harness_commit,
              'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'apk_sha256': apk_sha, 'native_sha256': native_sha, 'model_sha256': MODEL_SHA,
              'backend': 'CPU/KleidiAI I8MM', 'typed_synthetic_only': True,
              'before': before, 'runtime_grants_before': grants, 'phases': [], 'completed': False,
              'permissions_or_settings_changed': False, 'speech_recognition_tested': False,
              'offline_disconnect_verified': False, 'npu_verified': False,
              'device': {name: lab.adb('shell', 'getprop', prop).strip() for name, prop in
                         [('manufacturer', 'ro.product.manufacturer'), ('model', 'ro.product.model'),
                          ('soc', 'ro.soc.model'), ('api', 'ro.build.version.sdk')]}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save(): args.output.write_text(json.dumps(report, indent=2)+'\n')
    def phase(name, **details):
        state = snapshot(lab)
        if not preserved_budget(before, state): raise RuntimeError('Observation/points invariant failed')
        report['phases'].append({'name': name, 'state': state, **details}); save()
        print(json.dumps({'phase': name, 'state': state}), flush=True)
    save()
    try:
        open_model(lab)
        result = reviewed_proposal(lab, 'Start focus for 20 seconds')
        lab.tap('Cancel', scroll=False)
        if snapshot(lab) != before: raise RuntimeError('Cancelled review changed focus')
        phase('review_cancel_no_action', model_result=result)
        lab.tap('Review proposed phone action')
        # The unchanged request is independently checked again before confirmation.
        if not any('Start a focus countdown for 20 seconds' in n.get('text', '') for n in lab.nodes()):
            raise RuntimeError('Repeated countdown review changed')
        lab.tap('Confirm action', scroll=False); report['first_confirmation_tapped'] = True; save()
        active = wait_state(lab, lambda s: s['active'])
        assert_target(active, before['elapsed_ms'])
        main_screen(lab); lab.tap('Stop focus', scroll=False)
        paused = wait_state(lab, lambda s: not s['active'])
        assert_target(paused, before['elapsed_ms'])
        if paused['completed'] or paused['remaining_ms'] <= 0: raise RuntimeError('Pause was not observed before deadline')
        phase('pause_retains_remainder')
        time.sleep(2)
        if snapshot(lab) != paused: raise RuntimeError('Paused countdown progressed')
        phase('paused_time_excluded', observation_seconds=2)
        open_model(lab)
        result = reviewed_proposal(lab, 'Please start a focus session')
        lab.tap('Confirm action', scroll=False); report['resume_confirmation_tapped'] = True; save()
        resumed = wait_state(lab, lambda s: s['active'])
        assert_target(resumed, before['elapsed_ms'])
        phase('reviewed_resume', model_result=result)
        done = wait_state(lab, lambda s: not s['active'] and s['completed'], 35)
        assert_target(done, before['elapsed_ms'])
        if done['remaining_ms'] != 0: raise RuntimeError('Completed countdown retained remainder')
        phase('first_auto_complete', elapsed_delta_ms=done['elapsed_ms']-before['elapsed_ms'])
        second_base = done['elapsed_ms']
        result = reviewed_proposal(lab, 'Start focus for 20 seconds')
        lab.tap('Confirm action', scroll=False); report['second_confirmation_tapped'] = True; save()
        wait_state(lab, lambda s: s['active'])
        lab.guard(); lab.adb('shell', 'am', 'force-stop', PACKAGE)
        # Read only scoped own-app persisted state while the process is absent.
        saved = snapshot(lab)
        assert_target(saved, second_base)
        if not saved['active']: raise RuntimeError('No interrupted active checkpoint survived')
        main_screen(lab)
        recovered = wait_state(lab, lambda s: not s['active'])
        expected = {**saved, 'active': False}
        if recovered != expected: raise RuntimeError('Recovery did not preserve paused checkpoint')
        if not any("That session was interrupted." in n.get('text', '') for n in lab.nodes()):
            raise RuntimeError('Interrupted paused recovery message not observed')
        phase('process_death_recovers_paused', saved_checkpoint=saved)
        time.sleep(2)
        if snapshot(lab) != recovered: raise RuntimeError('Recovered paused countdown progressed')
        lab.top(); lab.tap('Start focus', scroll=False)
        resumed = wait_state(lab, lambda s: s['active'])
        assert_target(resumed, second_base)
        phase('explicit_dashboard_resume')
        done = wait_state(lab, lambda s: not s['active'] and s['completed'], 35)
        assert_target(done, second_base)
        phase('recovered_auto_complete', elapsed_delta_ms=done['elapsed_ms']-second_base)
        open_model(lab)
        result = lab.run('Cancel my alarm at 7:30', wake_display=False)
        if not result['gate'].startswith('ABSTAIN'): raise RuntimeError('Unsupported cancellation was not refused')
        if snapshot(lab) != done: raise RuntimeError('Abstention changed focus')
        phase('unsupported_cancellation_no_action', model_result=result)
        report['completed'] = True; save()
    except Exception as error:
        report['failure_type'] = type(error).__name__
        report['failure'] = str(error) if isinstance(error, (RuntimeError, ValueError)) else 'External operation failed; raw output not exported'
        save(); raise
    finally:
        try:
            main_screen(lab)
            if snapshot(lab)['active']: lab.tap('Stop focus', scroll=False)
            final = wait_state(lab, lambda s: not s['active'])
            report['final'] = final; report['runtime_grants_after'] = permissions(lab)
            report['own_monitor_absent_final'] = not monitor_record_present(lab)
            require_empty_test_state(preferences(lab))
            report['cleanup_verified'] = (preserved_budget(before, final)
                and report['runtime_grants_after'] == grants and report['own_monitor_absent_final'])
            save()
        except Exception:
            report['cleanup_verified'] = False; save(); raise


if __name__ == '__main__': main()
