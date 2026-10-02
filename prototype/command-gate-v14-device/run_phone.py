#!/usr/bin/env python3
"""Install pinned v14 light APK; run pure gate fixtures; restore exact old test APK."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
HELPER = ROOT / 'scripts/phone_network_isolation.py'
HELPER_SHA = 'e8231523de1a5fdfb738624bac98240b02a2d732848c8bf6b07d04f2402a658b'
APP_SOURCE = '1eb2fb55bf0322237bce0bc04942cb0d6652ddcc'
RUNNER_CLASS = 'dev.focuspilot.prototype.GateIsolationInstrumentation'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if sha(HELPER) != HELPER_SHA:
    raise RuntimeError('Frozen phone helper bytes changed')
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('v14_phone_helper', HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def protected(snapshot):
    return {key: value for key, value in snapshot.items() if key != 'installed_app_sha256'}


def restoration_guard(before, current, current_test, candidate_test, light_sha, light_verified):
    """Never stop a process or overwrite a test package across unknown production state."""
    if protected(current) != protected(before):
        raise RuntimeError('Protected production changed concurrently; process stop and restoration refused')
    expected_app = light_sha if light_verified else helper.APP_SHA
    if current['installed_app_sha256'] != expected_app:
        raise RuntimeError('Unknown installed app retained; process stop and restoration refused')
    mode = helper.restore_mode(helper.ORIGINAL_TEST_SHA, current_test, candidate_test)
    if not light_verified and mode != 'already_restored':
        raise RuntimeError('Candidate test is not owned before verified light upgrade')
    return mode


def validate_report(report):
    expected = {'schema': 'focuspilot.gate_isolation.v1', 'passed': True, 'checks': 334,
                'expected_checks': 334, 'expected_positive_full_slot_checks': 25,
                'expected_all_route_negative_checks': 273, 'expected_wrong_route_checks': 36,
                'failed_fixture_ids': [], 'failure_type': None, 'gate_class': 'dev.focuspilot.prototype.ModelCommandGate',
                'actions_executed': 0, 'model_accessed': False,
                'production_preferences_accessed': False, 'services_started': False}
    for key, value in expected.items():
        if key not in report or report[key] != value or type(report[key]) is not type(value):
            raise RuntimeError('Incomplete or failed gate report field: ' + key)
    if report.get('scope') != 'Already-seen pure gate fixtures; no model inference or tool execution':
        raise RuntimeError('Unexpected gate diagnostic scope')


def install_light(lab, path, expected):
    run = subprocess.run(lab.base + ['install', '-r', str(path)], text=True, capture_output=True, timeout=90)
    if run.returncode or 'Success' not in run.stdout or helper.installed_sha(lab) != expected:
        raise RuntimeError('Pinned light APK upgrade failed; no app rollback attempted')


def save_record(path, record):
    path.write_text(json.dumps(record, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--light-apk', type=Path, required=True)
    parser.add_argument('--light-sha', required=True)
    parser.add_argument('--test-apk', type=Path, required=True)
    parser.add_argument('--test-sha', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--app-source', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--execute-gate-fixtures', action='store_true')
    args = parser.parse_args()
    if not args.execute_gate_fixtures:
        parser.error('Explicit pure gate fixture execution flag required')
    if args.app_source != APP_SOURCE or not re.fullmatch('[0-9a-f]{40}', args.source):
        raise RuntimeError('Exact v14 app source and full frozen harness HEAD required')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() != args.source \
            or subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise RuntimeError('Clean exact frozen source HEAD required')
    output = args.output_dir.resolve()
    if not output.is_relative_to(ROOT / 'artifacts') or output.exists() or not output.parent.is_dir():
        raise RuntimeError('New ignored artifact directory in existing parent required')
    old_light = ROOT / 'artifacts/focuspilot-research-v013-reset-light.apk'
    old_test = ROOT / 'artifacts/focuspilot-research-v013-reset-test.apk'
    if sha(old_light) != helper.APP_SHA or sha(old_test) != helper.ORIGINAL_TEST_SHA:
        raise RuntimeError('Frozen original APK identities differ')
    for path, expected in ((args.light_apk, args.light_sha), (args.test_apk, args.test_sha)):
        if not re.fullmatch('[0-9a-f]{64}', expected) or sha(path) != expected:
            raise RuntimeError('Candidate APK hash mismatch')
    if args.light_sha == helper.APP_SHA or args.test_sha == helper.ORIGINAL_TEST_SHA:
        raise RuntimeError('Distinct v14 light and command-gate test APKs required')
    sdk = Path.home() / 'Library/Android/sdk/build-tools/36.0.0'
    helper.require_package(old_light, sdk, helper.PACKAGE)
    helper.require_package(args.light_apk, sdk, helper.PACKAGE)
    helper.require_package(old_test, sdk, helper.TEST_PACKAGE, 'dev.focuspilot.prototype.ResetIsolationInstrumentation')
    helper.require_package(args.test_apk, sdk, helper.TEST_PACKAGE, RUNNER_CLASS)
    badging = subprocess.check_output([str(sdk / 'aapt'), 'dump', 'badging', str(args.light_apk)], text=True)
    if not re.search(r"^package: .*\bversionCode='14'", badging, re.M):
        raise RuntimeError('Exact version14 light APK required')
    apks = [old_light, old_test, args.light_apk, args.test_apk]
    certificates = [helper.verified_certificate(sdk / 'apksigner', apk) for apk in apks]
    if len(set(certificates)) != 1:
        raise RuntimeError('All old/new APK signing identities must match')
    for apk in apks:
        permissions = subprocess.check_output([str(sdk / 'aapt'), 'dump', 'permissions', str(apk)], text=True)
        if 'android.permission.INTERNET' in permissions:
            raise RuntimeError('Frozen package requests INTERNET')
        subprocess.run([str(sdk / 'apksigner'), 'verify', str(apk)], check=True, capture_output=True)
    with zipfile.ZipFile(args.light_apk) as apk:
        if hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest() != helper.NATIVE_SHA:
            raise RuntimeError('Embedded native library differs')
        if any(name.endswith('.gguf') for name in apk.namelist()):
            raise RuntimeError('Light APK must not package or import model weights')
    lab = helper.PhoneLab(args.serial)
    before = helper.snapshot(lab)
    if before['installed_app_sha256'] != helper.APP_SHA or not helper.pinned(before['model']) \
            or not before['services_absent'] or before['checkpoint']['active'] or before['checkpoint']['observation']:
        raise RuntimeError('Pinned old app/model, paused/off checkpoint and absent services required')
    if helper.test_sha(lab) != helper.ORIGINAL_TEST_SHA:
        raise RuntimeError('Unknown initial test APK retained')
    if helper.project_bytes(ROOT) + 10_000_000 > 15_000_000_000:
        raise RuntimeError('10 MB diagnostic reserve exceeds strict project cap')
    if sum(path.stat().st_size for path in TASK.rglob('*') if path.is_file()) > 1_000_000:
        raise RuntimeError('Device fixture preparation exceeds1 MB work budget')
    output.mkdir()
    record = {'kind': 'Already-seen pure installed-app gate regression fixtures', 'source_commit': args.source,
              'app_source_commit': APP_SOURCE, 'harness_sha256': sha(Path(__file__)), 'helper_sha256': HELPER_SHA,
              'old_light_apk_sha256': helper.APP_SHA, 'light_apk': {'sha256': args.light_sha, 'bytes': args.light_apk.stat().st_size},
              'original_test_apk_sha256': helper.ORIGINAL_TEST_SHA,
              'candidate_test_apk': {'sha256': args.test_sha, 'bytes': args.test_apk.stat().st_size},
              'native_sha256': helper.NATIVE_SHA, 'signing_certificate_sha256': certificates[0], 'before': before,
              'passed': False, 'restored': False, 'phases': [], 'product_ui_or_tool_actions': False,
              'network_settings_changed': False, 'permission_grants': 0, 'model_inference_calls': 0,
              'instrumentation_restarts_target_process': True, 'light_apk_left_installed': False}
    status = output / 'status.json'
    save_record(status, record)  # Reviewable initial record before any phone mutation.
    light_verified = False
    try:
        install_light(lab, args.light_apk, args.light_sha)
        light_verified = True
        record['after_upgrade'] = helper.snapshot(lab)
        if protected(record['after_upgrade']) != protected(before) \
                or record['after_upgrade']['installed_app_sha256'] != args.light_sha:
            raise RuntimeError('Protected production changed during APK upgrade')
        record['phases'].append('pinned v14 light upgrade preserved protected snapshot')
        save_record(status, record)
        helper.install_test(lab, args.test_apk, args.test_sha)
        record['phases'].append('exact command-gate test APK installed')
        save_record(status, record)
        restoration_guard(before, helper.snapshot(lab), helper.test_sha(lab), args.test_sha, args.light_sha, True)
        if helper.test_sha(lab) != args.test_sha:
            raise RuntimeError('Exact command-gate test APK required before instrumentation')
        component = helper.TEST_PACKAGE + '/' + RUNNER_CLASS
        try:
            run = subprocess.run(lab.base + ['shell', 'am', 'instrument', '-r', '-w', component],
                                 text=True, capture_output=True, timeout=90)
        except subprocess.TimeoutExpired as error:
            for suffix, value in (('stdout', error.stdout), ('stderr', error.stderr)):
                partial = value or b''
                (output / ('runner-timeout-' + suffix + '.txt')).write_bytes(partial if isinstance(partial, bytes) else partial.encode())
            raise RuntimeError('Gate instrumentation timeout; partial evidence retained') from error
        (output / 'runner-raw.txt').write_text(run.stdout)
        (output / 'runner-stderr.txt').write_text(run.stderr)
        report = helper.parse_raw(run.stdout)
        (output / 'runner-report.json').write_text(json.dumps(report, indent=2) + '\n')
        for name in ('runner-raw.txt', 'runner-stderr.txt', 'runner-report.json'):
            record[name + '_sha256'] = sha(output / name)
        validate_report(report)
        if run.returncode or 'INSTRUMENTATION_CODE: -1' not in run.stdout:
            raise RuntimeError('Instrumentation terminal status did not pass')
        record['after_instrumentation'] = helper.snapshot(lab)
        if protected(record['after_instrumentation']) != protected(before) \
                or record['after_instrumentation']['installed_app_sha256'] != args.light_sha:
            raise RuntimeError('Protected state or v14 installed app changed after fixtures')
        record['phases'].append('334 actual pure gate checks passed with protected state exact')
        record['passed'] = True
    except Exception as error:
        record['failure_type'] = type(error).__name__
        record['failure'] = str(error)
        raise
    finally:
        try:
            current = helper.snapshot(lab)
            mode = restoration_guard(before, current, helper.test_sha(lab), args.test_sha, args.light_sha, light_verified)
            if light_verified:
                lab.adb('shell', 'am', 'force-stop', helper.PACKAGE)
            if mode == 'restore':
                helper.install_test(lab, old_test, helper.ORIGINAL_TEST_SHA)
            record['restored_test_sha256'] = helper.test_sha(lab)
            record['after_restoration'] = helper.snapshot(lab)
            restoration_guard(before, record['after_restoration'], record['restored_test_sha256'], args.test_sha, args.light_sha, light_verified)
            if record['restored_test_sha256'] != helper.ORIGINAL_TEST_SHA:
                raise RuntimeError('Original test APK not exact after cleanup')
            record['restored'] = True
            record['light_apk_left_installed'] = light_verified
            record['phases'].append('original test APK exact; selected light and protected production retained')
        except Exception as error:
            record['passed'] = False
            record['restored'] = False
            record['restoration_failure_type'] = type(error).__name__
            record['restoration_failure'] = str(error)
        record['project_bytes_after'] = helper.project_bytes(ROOT)
        save_record(status, record)
    if record['passed'] is not True or not record['restored'] or not record['light_apk_left_installed']:
        raise RuntimeError('Gate verification or test restoration incomplete')
    print(json.dumps({'passed': True, 'checks': 334, 'restored_test': True,
                      'v14_light_left_installed': True, 'private_record': str(status)}, indent=2))


if __name__ == '__main__':
    main()
