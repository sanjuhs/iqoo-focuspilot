#!/usr/bin/env python3
"""Explicit own-app synthetic authored-guide test; refuses existing goals/plans."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from phone_model_smoke import PhoneLab, PACKAGE
from phone_focus_actions import MODEL_SHA

GOAL = 'Prepare a three point focus demo'
STEPS = ['Open my notes', 'Draft three points', 'Review the draft']
REPLACEMENT = ['Check the outline', 'Review the final notes']
PREFIX = 'taskGuide.'


def preferences(lab):
    root = ET.fromstring(lab.adb('shell', 'run-as', PACKAGE, 'cat', 'shared_prefs/focuspilot_research.xml'))
    values = {}
    for node in root:
        key = node.get('name')
        if not key or key in values:
            raise RuntimeError('Malformed own-app preference keys')
        if node.tag == 'string': values[key] = node.text or ''
        elif node.tag == 'boolean':
            if node.get('value') not in ('true', 'false'): raise RuntimeError('Malformed own-app boolean')
            values[key] = node.get('value') == 'true'
        elif node.tag in ('int', 'long'): values[key] = int(node.get('value'))
        else: values[key] = {'unsupported_type': node.tag}
        # This harness neither exports nor modifies unrelated preference values.
    return values


def checkpoint(values):
    return {'active': values.get('activeCheckpoint', False), 'observation': values.get('observe', False),
            'points': values.get('points', 100), 'elapsed_ms': values.get('elapsedCheckpoint', 0)}


def require_empty_test_state(values):
    # Missing optional values have the selected source's defaults, not inferred UI readiness.
    if values.get('focusGoal', '') != '' or any(k.startswith(PREFIX) for k in values):
        raise RuntimeError('Existing goal or guide present; no edits authorized by this synthetic harness')
    if checkpoint(values)['active'] is not False or checkpoint(values)['observation'] is not False:
        raise RuntimeError('Requires already paused focus with observation off')
    if values.get('shadowPlannedFocus', 0) != 0 or values.get('shadowContinuousLimit', 0) != 0:
        raise RuntimeError('Existing declared targets present; left unchanged')


def guide_record(values):
    return {k: v for k, v in values.items() if k.startswith(PREFIX)}


def owns_synthetic_guide(values):
    if values.get('focusGoal', '') != GOAL: return False
    record = guide_record(values)
    if not record: return True
    count = record.get(PREFIX+'count')
    if type(count) is not int or count not in (2, 3): return False
    steps = [record.get(PREFIX+'step.'+str(i)) for i in range(count)]
    return (record.get(PREFIX+'schema') == 1 and
            record.get(PREFIX+'goal') == hashlib.sha256(GOAL.encode()).hexdigest() and
            steps in (STEPS, REPLACEMENT))


def find_attribute(lab, attr, expected):
    for _ in range(14):
        for node in lab.nodes():
            if node.get(attr) == expected:
                xy = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
                if len(xy) == 4 and xy[3]-xy[1] >= 25: return node
        lab.guard(); lab.adb('shell', 'input', 'swipe', '540', '1800', '540', '700', '350')
    raise RuntimeError('Named own-app field not visible')


def tap_node(lab, node):
    xy = list(map(int, re.findall(r'\d+', node.get('bounds'))))
    lab.guard(); lab.adb('shell', 'input', 'tap', str((xy[0]+xy[2])//2), str((xy[1]+xy[3])//2))


def disclosure(lab, name):
    lab.top()
    for _ in range(14):
        for node in lab.nodes():
            desc = node.get('content-desc', '')
            if desc == name+', expanded': return
            if desc == name+', collapsed': tap_node(lab, node); return
        lab.guard(); lab.adb('shell', 'input', 'swipe', '540', '1800', '540', '700', '350')
    raise RuntimeError('Named own-app disclosure not visible')


def set_field(lab, attr, name, value):
    if not re.fullmatch(r'[A-Za-z0-9 \n]*', value): raise ValueError('Synthetic ASCII only')
    node = find_attribute(lab, attr, name); tap_node(lab, node)
    lab.guard(); lab.adb('shell', 'input', 'keycombination', '113', '29')
    lab.guard(); lab.adb('shell', 'input', 'keyevent', 'KEYCODE_DEL')
    for i, line in enumerate(value.split('\n')):
        if i: lab.guard(); lab.adb('shell', 'input', 'keyevent', 'KEYCODE_ENTER')
        if line: lab.guard(); lab.adb('shell', 'input', 'text', line.replace(' ', '%s'))
    lab.guard(); lab.adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
    actual = find_attribute(lab, attr, name).get('text', '')
    # Empty fields may expose their hint as the UI text; durable empty goal is checked after Save.
    if value and actual != value: raise RuntimeError('Synthetic field readback mismatch; no save')


def wait_preferences(lab, predicate, timeout=4):
    until = time.monotonic()+timeout
    while True:
        values = preferences(lab)
        if predicate(values): return values
        if time.monotonic() >= until: raise RuntimeError('Expected durable own-app state not observed')
        time.sleep(.1)


def assert_plan(values, steps, completed):
    record = guide_record(values)
    assert values.get('focusGoal') == GOAL, 'Synthetic task changed'
    assert record.get(PREFIX+'schema') == 1 and record.get(PREFIX+'count') == len(steps), 'Guide shape mismatch'
    assert record.get(PREFIX+'completed') == completed, 'Guide progress mismatch'
    assert record.get(PREFIX+'goal') == hashlib.sha256(GOAL.encode()).hexdigest(), 'Guide task association mismatch'
    assert isinstance(record.get(PREFIX+'revision'), str) and record[PREFIX+'revision'], 'Guide revision missing'
    assert [record.get(PREFIX+'step.'+str(i)) for i in range(len(steps))] == steps, 'Synthetic steps differ'
    assert all(PREFIX+'step.'+str(i) not in record for i in range(len(steps), 8)), 'Stale step retained'
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--local-apk', type=Path, required=True)
    parser.add_argument('--expected-apk-sha256', required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute-authored-guide', action='store_true')
    args = parser.parse_args()
    if not args.execute_authored_guide: parser.error('Explicit --execute-authored-guide required')
    if not re.fullmatch('[0-9a-f]{64}', args.expected_apk_sha256) or not re.fullmatch('[0-9a-f]{40}', args.source_commit): parser.error('Full identities required')
    apk_sha = hashlib.sha256(args.local_apk.read_bytes()).hexdigest()
    if apk_sha != args.expected_apk_sha256: raise RuntimeError('Local APK identity differs; no phone edits')
    lab = PhoneLab(args.serial); lab.guard()
    installed = lab.adb('shell', 'pm', 'path', PACKAGE).strip().split('package:', 1)[1]
    if lab.adb('shell', 'sha256sum', installed).split()[0] != apk_sha: raise RuntimeError('Installed APK identity differs')
    if lab.adb('shell', 'run-as', PACKAGE, 'sha256sum', 'files/qwen35.gguf').split()[0] != MODEL_SHA: raise RuntimeError('Retained model identity differs')
    before = preferences(lab); require_empty_test_state(before); baseline = checkpoint(before)
    with zipfile.ZipFile(args.local_apk) as apk: native_sha = hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest()
    report = {'research_only': True, 'source_commit': args.source_commit, 'apk_sha256': apk_sha,
              'model_sha256': MODEL_SHA, 'native_sha256': native_sha, 'model_inference_performed': False,
              'device': {'manufacturer': lab.adb('shell', 'getprop', 'ro.product.manufacturer').strip(),
                         'model': lab.adb('shell', 'getprop', 'ro.product.model').strip(),
                         'soc': lab.adb('shell', 'getprop', 'ro.soc.model').strip(),
                         'api': lab.adb('shell', 'getprop', 'ro.build.version.sdk').strip()},
              'synthetic_goal': GOAL, 'synthetic_steps': STEPS, 'synthetic_replacement': REPLACEMENT,
              'before_checkpoint': baseline, 'phases': [], 'completed': False,
              'permission_or_settings_actions': False, 'tts_or_microphone_actions': False,
              'external_app_actions': False, 'npu_verified': False, 'private_original_text_exported': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save(): args.output.write_text(json.dumps(report, indent=2)+'\n')
    def phase(name, values=None, **extra):
        values = preferences(lab) if values is None else values
        if checkpoint(values) != baseline: raise RuntimeError('Focus checkpoint changed during authored-only test')
        report['phases'].append({'name': name, 'checkpoint_unchanged': True, **extra}); save()
    def show_progress(count, total, next_text):
        lab.top(); lab.find(f'{count} / {total} steps completed by you')
        lab.find(next_text)
    def reopen():
        lab.guard(); lab.adb('shell', 'am', 'force-stop', PACKAGE)
        lab.adb('shell', 'am', 'start', '-n', PACKAGE+'/.MainActivity'); lab.guard()
    def edit_steps(steps):
        disclosure(lab, 'Write or edit my steps')
        set_field(lab, 'resource-id', PACKAGE+':id/task_guide_editor', '\n'.join(steps))
        lab.tap('Save these steps')
    synthetic_created = False
    save()
    try:
        disclosure(lab, 'Choose your task & targets')
        set_field(lab, 'content-desc', 'Focus task', GOAL)
        lab.tap('Save task & targets')
        synthetic_created = True
        wait_preferences(lab, lambda v: v.get('focusGoal') == GOAL)
        phase('synthetic_goal_saved')
        edit_steps(STEPS); record = assert_plan(preferences(lab), STEPS, 0)
        phase('authored_steps_saved', count=3, completed=0, revision_present=True)
        show_progress(0, 3, 'Next · '+STEPS[0])
        lab.tap("I've done this step")
        marked = assert_plan(preferences(lab), STEPS, 1)
        if marked[PREFIX+'revision'] == record[PREFIX+'revision']: raise RuntimeError('Progress revision not rotated')
        show_progress(1, 3, 'Next · '+STEPS[1]); phase('mark_ui_and_durable_state', completed=1)
        lab.tap('Undo last completed step'); assert_plan(preferences(lab), STEPS, 0)
        show_progress(0, 3, 'Next · '+STEPS[0]); phase('undo_ui_and_durable_state', completed=0)
        lab.tap("I've done this step"); expected = assert_plan(preferences(lab), STEPS, 1)
        reopen(); recovered = assert_plan(preferences(lab), STEPS, 1)
        if recovered != expected: raise RuntimeError('Saved guide changed across process restart')
        show_progress(1, 3, 'Next · '+STEPS[1]); phase('process_restart_recovery', exact_record_preserved=True)
        for completed in (2, 3):
            lab.tap("I've done this step"); assert_plan(preferences(lab), STEPS, completed)
        show_progress(3, 3, 'You finished your plan. Take a moment to breathe.')
        if lab.find("I've done this step").get('enabled') != 'false': raise RuntimeError('Complete-plan mark remained enabled')
        phase('all_steps_completed_ui', completed=3, mark_disabled=True)
        lab.tap('Undo last completed step'); assert_plan(preferences(lab), STEPS, 2)
        show_progress(2, 3, 'Next · '+STEPS[2]); phase('undo_after_complete', completed=2)
        old = guide_record(preferences(lab)); edit_steps(REPLACEMENT)
        lab.find('Replace your saved steps?'); lab.tap('Cancel', scroll=False)
        if guide_record(preferences(lab)) != old: raise RuntimeError('Cancelled replacement mutated saved guide')
        phase('replacement_cancel', exact_record_preserved=True)
        lab.tap('Save these steps'); lab.find('Replace your saved steps?'); lab.tap('Replace steps', scroll=False)
        assert_plan(preferences(lab), REPLACEMENT, 0)
        show_progress(0, 2, 'Next · '+REPLACEMENT[0]); phase('replacement_confirmed', count=2, completed=0)
        disclosure(lab, 'Write or edit my steps'); old = guide_record(preferences(lab))
        lab.tap('Clear my steps'); lab.find('Clear your saved steps?'); lab.tap('Cancel', scroll=False)
        if guide_record(preferences(lab)) != old: raise RuntimeError('Cancelled clear mutated saved guide')
        phase('clear_cancel', exact_record_preserved=True)
        lab.tap('Clear my steps'); lab.find('Clear your saved steps?'); lab.tap('Clear steps', scroll=False)
        if guide_record(preferences(lab)): raise RuntimeError('Confirmed clear left guide fields')
        phase('clear_confirmed', task_goal_retained=True)
        reopen()
        if guide_record(preferences(lab)): raise RuntimeError('Cleared guide reappeared after restart')
        lab.top(); lab.find('One small step at a time.')
        phase('clear_process_restart', guide_record_absent=True)
        report['completed'] = True; save()
    except Exception as error:
        # Known error messages may contain labels but never original goal/step text.
        report['failure_type'] = type(error).__name__; report['failure'] = str(error) if isinstance(error, (RuntimeError, AssertionError, ValueError)) else 'External operation failed; no raw command or UI exported'; save()
        raise
    finally:
        # Never globally delete data or restore over a task/guide that the user changed.
        current = preferences(lab)
        if synthetic_created and owns_synthetic_guide(current):
            lab.guard()
            if guide_record(current):
                disclosure(lab, 'Write or edit my steps'); lab.tap('Clear my steps')
                lab.tap('Clear steps', scroll=False)
            current = preferences(lab)
            if not guide_record(current) and current.get('focusGoal') == GOAL:
                disclosure(lab, 'Choose your task & targets')
                set_field(lab, 'content-desc', 'Focus task', '')
                lab.tap('Save task & targets')
                wait_preferences(lab, lambda v: v.get('focusGoal', '') == '')
        final = preferences(lab)
        report['final_checkpoint'] = checkpoint(final)
        report['empty_goal_restored'] = final.get('focusGoal', '') == ''
        report['guide_record_removed'] = not guide_record(final)
        report['cleanup_scope'] = 'UI clears only this synthetic guide and restores the original empty goal. Task-save log entries and zero target keys may remain; no global deletion or byte-identical preference restoration.'
        report['cleanup_verified'] = (report['empty_goal_restored'] and report['guide_record_removed'] and checkpoint(final) == baseline)
        save()
    if not report['cleanup_verified']: raise RuntimeError('Synthetic cleanup not fully verified')
    print(json.dumps({'completed': report['completed'], 'phases': len(report['phases']), 'cleanup_verified': report['cleanup_verified']}), flush=True)


if __name__ == '__main__': main()
