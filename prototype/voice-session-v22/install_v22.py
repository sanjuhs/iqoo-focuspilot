#!/usr/bin/env python3
"""One guarded v21 -> v22 own-app replacement; no wake/UI/grants/inference.

Mandatory build pins refuse execution until root fills them after inspection.
One nonstreamed install, exclusive retained records and no retries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from phone_model_smoke import PhoneLab, PACKAGE
from phone_reviewed_reset import snapshot
from phone_bundled_import import installed_sha, pinned

OLD = 'b6f623aebd148fe4cda0675ab171607689be51d5844ad8d3aabfcc1530a4c5e7'
NEW = '70a0a280a33da06f3a1a56bfc3b2ba448a45bd9bb00b77e4dbb19330ae6b3350'
ARTIFACT_SHA = 'b7b4b333fe0e07d1eeaa33dff5fb27a682e886fda8e4d5cddfd1619e1aab1a24'
SOURCE_COMMIT = '08af30893d6ca7ecec70cf66b5026a88be463ca5'
TEST = 'b79a81444b0956639a54607153e99fe9367e555dde40b9c61267c1ad4cafd61b'
NATIVE = '675f2142a2c35b9c0260dc43944db09c3bb570a63c9f49a27e47625f7b98152e'
BASELINE_SHA = '075f9adb665f5c192ce08551b9b0e98c69e56df19598cc9a5ed75918760f182a'
BASELINE_PUBLIC_SHA = '703e758f4955012c28463d4fee307470d184ea701afacbb9b52d21fa4c4cb251'
APK = ROOT / 'artifacts/focuspilot-research-v022-voice-session-light.apk'
ARTIFACT = ROOT / 'docs/voice-session-artifact-v22.json'
BASELINE = ROOT / 'artifacts/mira-setup-phone-install-v21-private.json'
BASELINE_PUBLIC = ROOT / 'docs/mira-setup-phone-install-v21.json'
RAW = ROOT / 'artifacts/voice-session-phone-install-v22-private.json'
PUBLIC = ROOT / 'docs/voice-session-phone-install-v22.json'
SOURCE_PATHS = {
    'prototype/android/app/build.gradle',
    'prototype/android/app/src/main/java/dev/focuspilot/prototype/MainActivity.java',
    'prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModelActivity.java',
    'prototype/android/app/src/main/java/dev/focuspilot/prototype/ReadbackState.java',
    'prototype/android/app/src/test/java/dev/focuspilot/prototype/ReadbackStateTest.java',
}


def sha(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def regular(file):
    require(file.is_file() and not file.is_symlink()
            and file.resolve().is_relative_to(ROOT.resolve()), 'Regular own-project file required')
    return file


def test_sha(lab):
    paths = lab.adb('shell', 'pm', 'path', PACKAGE + '.test').strip().splitlines()
    require(len(paths) == 1 and paths[0].startswith('package:/data/app/'), 'Original test identity unavailable')
    digest = lab.adb('shell', 'sha256sum', paths[0].removeprefix('package:')).split()[0]
    require(re.fullmatch('[0-9a-f]{64}', digest) is not None, 'Original test digest unavailable')
    return digest


def validate_inputs():
    for value, length in ((NEW, 64), (ARTIFACT_SHA, 64), (SOURCE_COMMIT, 40)):
        require(re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None,
                'Mandatory v22 build pins are unset; execution refused before phone access')
    require(sha(regular(APK)) == NEW and sha(regular(ARTIFACT)) == ARTIFACT_SHA,
            'Frozen v22 APK/artifact differs')
    artifact = json.loads(ARTIFACT.read_text())
    require(artifact['source_commit'] == SOURCE_COMMIT and artifact['apk_sha256'] == NEW
            and artifact['apk_bytes'] == APK.stat().st_size
            and artifact['native_sha256'] == NATIVE
            and artifact['native_unchanged_from_v21'] is True
            and artifact['permissions_unchanged_from_v21'] is True
            and artifact['zip_alignment_16k_verified'] is True
            and artifact['internet_permission'] is False, 'Inspected v22 artifact scope differs')
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', SOURCE_COMMIT + '^{commit}'],
                                     cwd=ROOT, text=True).strip()
    require(commit == SOURCE_COMMIT, 'Frozen build commit identity differs')
    require(set(artifact['source_sha256']) == SOURCE_PATHS, 'Expected five v22 source bindings required')
    for path, digest in artifact['source_sha256'].items():
        require(re.fullmatch('[0-9a-f]{64}', digest) is not None and sha(regular(ROOT / path)) == digest,
                'Current frozen app source differs')
        content = subprocess.check_output(['git', 'show', SOURCE_COMMIT + ':' + path], cwd=ROOT)
        require(hashlib.sha256(content).hexdigest() == digest, 'Committed app source differs')
    with zipfile.ZipFile(APK) as archive:
        require(hashlib.sha256(archive.read('lib/arm64-v8a/libfocuspilot_local.so')).hexdigest() == NATIVE
                and not any(name.endswith('.gguf') for name in archive.namelist()), 'Exact light/native payload required')
    require(sha(regular(BASELINE)) == BASELINE_SHA and sha(regular(BASELINE_PUBLIC)) == BASELINE_PUBLIC_SHA,
            'Exact prior v21 baseline record differs')
    previous_public = json.loads(BASELINE_PUBLIC.read_text())
    previous = json.loads(BASELINE.read_text())
    require(previous_public['private_record_sha256'] == BASELINE_SHA and previous_public['passed'] is True
            and previous_public['apk_sha256'] == OLD and previous.get('passed') is True
            and previous.get('target_installed') is True and previous.get('apk_sha256') == OLD
            and previous.get('after') is not None, 'Prior v21 update did not prove required identity')
    utility_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    utility_path = str(Path(__file__).resolve().relative_to(ROOT))
    frozen_utility = subprocess.check_output(['git', 'show', utility_commit + ':' + utility_path], cwd=ROOT)
    require(hashlib.sha256(frozen_utility).hexdigest() == sha(Path(__file__)), 'Installer must be committed before execution')
    return artifact, previous['after'], utility_commit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-own-v22-update', action='store_true')
    parser.add_argument('--serial', required=True)
    options = parser.parse_args()
    require(options.execute_own_v22_update, 'Explicit own-app v22 update flag required')
    require(not RAW.exists() and not PUBLIC.exists() and not RAW.is_symlink() and not PUBLIC.is_symlink(),
            'Existing record; no retry or overwrite')
    artifact, baseline, utility_commit = validate_inputs()
    lab = PhoneLab(options.serial)
    require(lab.adb('get-state').strip() == 'device', 'Authorized phone required')
    before = snapshot(lab)
    require(before == baseline and installed_sha(lab) == OLD and test_sha(lab) == TEST
            and pinned(before['model']) and not before['checkpoint']['active']
            and not before['checkpoint']['observation'] and before['services_absent'],
            'Known paused protected v21 baseline differs; mutation refused')
    record = {'schema': 'focuspilot.voice_session_install_private.v1',
        'source_commit': artifact['source_commit'], 'harness_sha256': sha(Path(__file__)),
        'baseline_record_sha256': BASELINE_SHA, 'baseline_public_sha256': BASELINE_PUBLIC_SHA,
        'artifact_record_sha256': ARTIFACT_SHA, 'utility_commit': utility_commit,
        'source_sha256': artifact['source_sha256'], 'old_apk_sha256': OLD, 'apk_sha256': NEW,
        'before': before, 'attempts': 1, 'ui_used': False, 'phone_woken': False,
        'permission_changes': 0, 'model_inference': False, 'passed': False}
    # Claim the attempt before mutation, preserving failures/process-loss without a silent retry.
    with RAW.open('x') as raw:
        json.dump(record, raw, indent=2); raw.write('\n'); raw.flush()
        start = time.monotonic()
        try:
            run = subprocess.run(lab.base + ['install', '--no-streaming', '-r', str(APK)],
                                 text=True, capture_output=True, timeout=180)
            record['install_client'] = {'elapsed_ms': round((time.monotonic() - start) * 1000),
                                       'exit_code': run.returncode, 'timed_out': False}
            record['after'] = snapshot(lab); record['installed_target_sha256'] = installed_sha(lab)
            record['original_test_unchanged'] = test_sha(lab) == TEST
            record['protected_state_unchanged'] = record['after'] == before
            record['target_installed'] = record['installed_target_sha256'] == NEW
            record['passed'] = run.returncode == 0 and 'Success' in run.stdout and all(record[key] for key in
                ('original_test_unchanged', 'protected_state_unchanged', 'target_installed'))
            require(record['passed'], 'Installation/postcondition failed; no retry')
        except Exception as error:
            record['failure_type'] = type(error).__name__
            if isinstance(error, subprocess.TimeoutExpired):
                record['install_client'] = {'elapsed_ms': round((time.monotonic() - start) * 1000),
                                           'exit_code': None, 'timed_out': True}
            raise
        finally:
            raw.seek(0); json.dump(record, raw, indent=2); raw.write('\n'); raw.truncate(); raw.flush()
            public = {key: value for key, value in record.items() if key not in ('before', 'after')}
            public.update(schema='focuspilot.voice_session_install.v1', private_record_sha256=sha(RAW),
                protected_scope='Three named preference-store semantic hashes/checkpoint; canonical model full SHA/bytes/inode/links; microphone/notification grants; own monitor/floating service absence; exact original test APK.',
                checkpoint=before['checkpoint'], physical_voice_verified=False, physical_readback_verified=False,
                physical_lock_unlock_verified=False, npu_verified=False)
            with PUBLIC.open('x') as output: json.dump(public, output, indent=2); output.write('\n')
    print(json.dumps({key: record[key] for key in ('passed', 'target_installed', 'protected_state_unchanged')}))


if __name__ == '__main__':
    main()
