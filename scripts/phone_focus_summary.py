#!/usr/bin/env python3
"""Upgrade the research app and run in-memory summary fixtures, without UI or grants.

Full production preferences/model/runtime grants are compared before/after.
The exact previous test APK is restored even when a fixture fails. This is not
model, voice, persistence, service, foreground-screen or recovery-process proof.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import zipfile

from phone_model_smoke import PhoneLab, PACKAGE
from phone_reviewed_reset import snapshot, sha, NATIVE
from phone_bundled_import import pinned, installed_sha, install
from package_bundled_apk import ROOT, project_bytes

TEST_PACKAGE = PACKAGE + '.test'
RUNNER = TEST_PACKAGE + '/dev.focuspilot.prototype.FocusSummaryIsolationInstrumentation'


def test_sha(lab):
    raw = lab.adb('shell', 'pm', 'path', TEST_PACKAGE).strip().splitlines()
    if len(raw) != 1 or not raw[0].startswith('package:/data/app/'):
        raise RuntimeError('Exact existing test application required; left unchanged')
    return lab.adb('shell', 'sha256sum', raw[0].removeprefix('package:')).split()[0]


def replace_test(lab, path, expected):
    run = subprocess.run(lab.base + ['install', '-r', str(path)], text=True,
                         capture_output=True, timeout=90)
    if run.returncode or 'Success' not in run.stdout or test_sha(lab) != expected:
        raise RuntimeError('Own synthetic test application replacement failed')


def fixture_report(raw):
    lines = [s.removeprefix('INSTRUMENTATION_RESULT: report_json=')
             for s in raw.splitlines()
             if s.startswith('INSTRUMENTATION_RESULT: report_json=')]
    if len(lines) != 1:
        raise ValueError('Exact instrumented report required')
    r = json.loads(lines[0])
    if (r.get('schema') != 'focuspilot.focus_summary_isolation.v1'
            or r.get('passed') is not True or r.get('checks') != 12
            or r.get('expected_checks') != 12 or r.get('failed_fixture_ids') != []
            or r.get('failure_type') is not None
            or r.get('model_accessed') is not False
            or r.get('production_preferences_accessed') is not False
            or r.get('production_singleton_used') is not False
            or r.get('services_started') is not False or r.get('actions_executed') != 0
            or 'INSTRUMENTATION_CODE: -1' not in raw):
        raise ValueError('Pure installed-app summary fixtures did not pass')
    return r


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('serial', 'source', 'previous-app-sha', 'light-sha', 'test-sha', 'restore-test-sha'):
        p.add_argument('--' + k, required=True)
    for k in ('light', 'test-apk', 'restore-test-apk', 'output'):
        p.add_argument('--' + k, required=True, type=Path)
    p.add_argument('--execute-own-summary-fixtures', action='store_true')
    a = p.parse_args()
    if not a.execute_own_summary_fixtures:
        p.error('Explicit own-app isolated fixture flag required')
    if not re.fullmatch('[0-9a-f]{40}', a.source):
        p.error('Full source identity required')
    if (subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != a.source
            or subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()):
        raise RuntimeError('Exact clean committed source required')
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise RuntimeError('Exclusive ignored output required')
    for path, expected in ((a.light, a.light_sha), (a.test_apk, a.test_sha),
                           (a.restore_test_apk, a.restore_test_sha)):
        if sha(path) != expected:
            raise RuntimeError('Frozen local APK identity differs')
    with zipfile.ZipFile(a.light) as apk:
        import hashlib
        if (hashlib.sha256(apk.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest() != NATIVE
                or any(n.endswith('.gguf') for n in apk.namelist())):
            raise RuntimeError('Unchanged native/light APK required')
    if project_bytes(ROOT) + 20_000_000 > 15_000_000_000:
        raise RuntimeError('Fixture storage reserve exceeds project cap')
    lab = PhoneLab(a.serial)
    before = snapshot(lab)
    if (before['checkpoint']['active'] or before['checkpoint']['observation']
            or not before['services_absent'] or not pinned(before['model'])
            or installed_sha(lab) != a.previous_app_sha
            or test_sha(lab) != a.restore_test_sha):
        raise RuntimeError('Exact paused/off/no-services/pinned-model app and original test required')
    record = {'schema': 'focuspilot.focus_summary_phone.v1', 'source_commit': a.source,
              'harness_sha256': sha(Path(__file__)), 'before': before,
              'previous_app_sha256': a.previous_app_sha, 'light_apk_sha256': a.light_sha,
              'test_apk_sha256': a.test_sha, 'restore_test_apk_sha256': a.restore_test_sha,
              'permission_grants': 0, 'ui_started': False, 'phone_woken': False,
              'model_inference': False, 'passed': False, 'original_test_restored': False}
    # Claim the evidence destination before making any replacement.
    with out.open('x') as f:
        json.dump(record, f, indent=2)
    try:
        install(lab, a.light, a.light_sha)
        if snapshot(lab) != before:
            raise RuntimeError('Production snapshot changed during app replacement')
        replace_test(lab, a.test_apk, a.test_sha)
        run = subprocess.run(lab.base + ['shell', 'am', 'instrument', '-r', '-w', RUNNER],
                             text=True, capture_output=True, timeout=45)
        record['instrumentation'] = run.stdout
        if run.returncode:
            raise RuntimeError('Instrument process failed')
        record['report'] = fixture_report(run.stdout)
        if snapshot(lab) != before or installed_sha(lab) != a.light_sha:
            raise RuntimeError('Production snapshot or target APK changed during fixtures')
        record['passed'] = True
    except Exception as error:
        record['failure_type'] = type(error).__name__
        record['failure'] = str(error)
        raise
    finally:
        try:
            # Restore only if current bytes are the exact original or this run's test.
            current = test_sha(lab)
            if current == a.test_sha:
                replace_test(lab, a.restore_test_apk, a.restore_test_sha)
            elif current != a.restore_test_sha:
                raise RuntimeError('Unknown test APK left intact; automatic restoration refused')
            record['original_test_restored'] = test_sha(lab) == a.restore_test_sha
            record['after'] = snapshot(lab)
            record['protected_state_unchanged'] = record['after'] == before
            record['installed_app_sha256'] = installed_sha(lab)
            if not record['protected_state_unchanged']:
                record['passed'] = False
        except Exception as error:
            record['passed'] = False
            record['cleanup_failure_type'] = type(error).__name__
            record['cleanup_failure'] = str(error)
        record['project_logical_bytes_after'] = project_bytes(ROOT)
        out.write_text(json.dumps(record, indent=2) + '\n')
    if not record['passed'] or not record['original_test_restored']:
        raise RuntimeError('Fixture outcome or restoration incomplete; consult preserved record')
    print(json.dumps({k: record[k] for k in ('passed', 'protected_state_unchanged',
                                            'original_test_restored')}, indent=2))


if __name__ == '__main__':
    main()
