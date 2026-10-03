#!/usr/bin/env python3
"""Offline/private APK build, dependency pins and bounded logical storage accounting.

Never install/publish/download/copy a model. Existing Mira Gradle wrapper is only a
tool; all build outputs belong to this separate project. No overwrite of final APK.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
LIMIT = 15_000_000_000
DEFAULT_RESERVE = 1_250_000_000
MIN_RESERVE = 1_075_000_000  # four 217.5MB native copies + two APKs + class/tool overhead
PACKAGE = 'dev.focuspilot.qualcomm.research'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def inventory(root):
    """No directory symlink traversal; count file logical bytes conservatively."""
    result = {}
    if not root.exists():
        return result
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(folder) / name).is_symlink()]
        for name in names:
            path = Path(folder) / name
            try:
                if path.is_file():
                    result[str(path)] = path.stat().st_size
            except FileNotFoundError:
                pass  # Concurrent atomic file removal; next poll remeasures.
    return result


def cache_growth(before, after):
    return sum(max(0, size - before.get(path, 0)) for path, size in after.items())


def budget_preflight(project_bytes, cached_dependency_bytes, reserve):
    if reserve < MIN_RESERVE:
        raise ValueError('Reserve below the bounded native/APK working-copy estimate')
    estimated = project_bytes + cached_dependency_bytes + reserve
    if estimated > LIMIT:
        raise ValueError(f'15GB budget exceeded before build: {estimated} bytes reserved')
    return estimated


def dependencies(gradle_home):
    records = []
    for pin in json.loads((HERE / 'dependencies.json').read_text())['artifacts']:
        base = PROJECT if pin['location'] == 'project' else gradle_home / 'caches/modules-2/files-2.1'
        path = base / pin['relative_path']
        if not path.is_file() or path.stat().st_size != pin['bytes'] or sha256(path) != pin['sha256']:
            raise ValueError('Missing or changed cached dependency: ' + pin['name'])
        records.append({**pin, 'resolved_path': str(path)})
    return records


def source_hashes():
    return {str(p.relative_to(PROJECT)): sha256(p) for p in sorted(HERE.rglob('*'))
            if p.is_file() and not any(x in {'build', '.gradle', '__pycache__'} for x in p.relative_to(HERE).parts)
            and p.name != 'local.properties'}


def checked(command):
    return subprocess.run([str(x) for x in command], check=True, text=True, capture_output=True).stdout


def zip_sha(archive, name):
    digest = hashlib.sha256()
    with archive.open(name) as stream:
        for data in iter(lambda: stream.read(65536), b''):
            digest.update(data)
    return digest.hexdigest()


def inspect_apk(apk, aar, tools):
    badging = checked([tools / 'aapt', 'dump', 'badging', apk])
    if not re.search(r"package: name='" + re.escape(PACKAGE) + r"' versionCode='1'", badging):
        raise ValueError('Unexpected diagnostic package/version')
    if "sdkVersion:'31'" not in badging or "targetSdkVersion:'35'" not in badging:
        raise ValueError('Unexpected platform bounds')
    permissions = checked([tools / 'aapt', 'dump', 'permissions', apk])
    if 'uses-permission' in permissions:
        raise ValueError('Permission-free probe unexpectedly requests permissions')
    manifest = checked([tools / 'aapt', 'dump', 'xmltree', apk, 'AndroidManifest.xml'])
    if re.search(r'E: (service|receiver|provider)\b', manifest) or len(re.findall(r'E: activity\b', manifest)) != 1:
        raise ValueError('Unexpected executable Android component')
    if not re.search(r"^native-code: 'arm64-v8a'\s*$", badging, re.MULTILINE):
        raise ValueError('Unexpected native ABI set')
    checked([tools / 'zipalign', '-c', '-P', '16', '4', apk])
    signature = checked([tools / 'apksigner', 'verify', '--verbose', '--print-certs', apk])
    cert = re.findall(r'Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]{64})', signature)
    if len(cert) != 1:
        raise ValueError('Missing public signer identity')
    native = {}
    with ZipFile(aar) as vendor, ZipFile(apk) as app:
        license_root = HERE / 'app/src/main/assets/licenses'
        expected_assets = {'assets/licenses/' + p.name: p for p in license_root.iterdir() if p.is_file()}
        actual_assets = {name for name in app.namelist() if name.startswith('assets/') and not name.endswith('/')}
        if actual_assets != set(expected_assets) or any(name.endswith('.gguf') for name in app.namelist()):
            raise ValueError('Unexpected model/non-license assets in diagnostic APK')
        license_assets = {}
        for name, source in sorted(expected_assets.items()):
            digest = zip_sha(app, name)
            if digest != sha256(source):
                raise ValueError('Retained license source differs from APK: ' + name)
            license_assets[name] = {'bytes': app.getinfo(name).file_size, 'sha256': digest}
        expected = {n.replace('jni/', 'lib/', 1): n for n in vendor.namelist()
                    if n.startswith('jni/arm64-v8a/') and n.endswith('.so')}
        actual = {n for n in app.namelist() if n.startswith('lib/') and n.endswith('.so')}
        if actual != set(expected):
            raise ValueError('Native payload set differs from the pinned arm64 AAR')
        for name, vendor_name in sorted(expected.items()):
            digest = zip_sha(app, name)
            if digest != zip_sha(vendor, vendor_name):
                raise ValueError('Vendor native bytes changed: ' + name)
            native[name] = {'sha256': digest, 'bytes': app.getinfo(name).file_size}
    return {'package': PACKAGE, 'version_code': 1, 'min_sdk': 31, 'target_sdk': 35,
            'permissions': [], 'bundled_model': False, 'native_payloads': native, 'license_assets': license_assets,
            'native_vendor_payload_parity': True, 'zip_alignment': '16KiB ZIP check passed; runtime restricted to 4KiB by vendor GNU_RELRO guard',
            'signature_verified': True, 'public_certificate_sha256': cert[0].lower(),
            'badging': badging, 'manifest_xmltree': manifest, 'signature_output': signature}


def terminate_owned(process):
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--storage-approved', action='store_true', help='Root approval after independent source review is required')
    parser.add_argument('--reserve-bytes', type=int, default=DEFAULT_RESERVE)
    parser.add_argument('--timeout-seconds', type=int, default=600)
    parser.add_argument('--sdk', type=Path, default=Path.home() / 'Library/Android/sdk')
    parser.add_argument('--jdk', type=Path, default=Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home'))
    args = parser.parse_args()
    if not args.storage_approved:
        parser.error('Wait for root source review/storage authorization; no build started')
    if not 30 <= args.timeout_seconds <= 600:
        parser.error('Build deadline must be 30..600 seconds')
    gradle_home = Path(os.environ.get('GRADLE_USER_HOME', str(Path.home() / '.gradle'))).resolve()
    pins = dependencies(gradle_home)
    cached_bytes = sum(p['bytes'] for p in pins if p['location'] == 'gradle')
    before_project = sum(inventory(PROJECT).values())
    reserved_peak = budget_preflight(before_project, cached_bytes, args.reserve_bytes)
    before_cache = inventory(gradle_home / 'caches')
    wrapper = PROJECT / 'prototype/android/gradlew'
    wrapper_config = PROJECT / 'prototype/android/gradle/wrapper/gradle-wrapper.properties'
    wrapper_jar = PROJECT / 'prototype/android/gradle/wrapper/gradle-wrapper.jar'
    # The wrapper itself can download before Gradle sees --offline. Require its
    # exact existing distribution so this helper never exercises that route.
    if 'gradle-8.14-all.zip' not in wrapper_config.read_text():
        raise ValueError('Unexpected shared wrapper distribution')
    cached_launchers = list((gradle_home / 'wrapper/dists/gradle-8.14-all').glob('*/gradle-8.14/bin/gradle'))
    if len(cached_launchers) != 1 or not cached_launchers[0].is_file():
        raise ValueError('Exact Gradle8.14 distribution missing; downloads are forbidden')
    tools = args.sdk / 'build-tools/36.0.0'
    for tool in [wrapper, args.jdk / 'bin/java', tools / 'aapt', tools / 'apksigner', tools / 'zipalign']:
        if not tool.is_file():
            raise ValueError('Required cached build tool missing: ' + str(tool))
    output = HERE / 'build/private-geniex-research.apk'
    report_file = HERE / 'build/package-report.json'
    log_file = HERE / 'build/gradle-build.log'
    for path in [output, report_file, log_file]:
        if path.exists():
            raise ValueError('No overwrite: ' + str(path))
        checked(['git', '-C', PROJECT, 'check-ignore', '--quiet', path])
    sources = source_hashes()
    command = [str(wrapper), '--offline', '--no-daemon', '--max-workers=1', '-p', str(HERE), ':app:assembleDebug']
    env = {**os.environ, 'JAVA_HOME': str(args.jdk), 'ANDROID_HOME': str(args.sdk)}
    report = {'schema': 'focuspilot.geniex_private_package.v1', 'status': 'started',
              'source_git_commit': checked(['git', '-C', PROJECT, 'rev-parse', 'HEAD']).strip(),
              'source_sha256': sources, 'dependencies': pins, 'wrapper_sha256': sha256(wrapper),
              'wrapper_config_sha256': sha256(wrapper_config), 'wrapper_jar_sha256': sha256(wrapper_jar),
              'project_bytes_before': before_project, 'existing_external_dependency_bytes': cached_bytes,
              'reserve_bytes': args.reserve_bytes, 'reserved_peak_bytes': reserved_peak,
              'command': command, 'downloads_allowed': False, 'phone_accessed': False,
              'binary_publication_allowed': False, 'redistribution_terms': 'UNRESOLVED; private build only'}
    HERE.joinpath('build').mkdir(exist_ok=True)
    process = None; started = time.monotonic(); peak = before_project + cached_bytes; cache_peak = 0
    try:
        with log_file.open('x') as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            while process.poll() is None:
                current_project = sum(inventory(PROJECT).values())
                growth = cache_growth(before_cache, inventory(gradle_home / 'caches'))
                cache_peak = max(cache_peak, growth)
                effective = current_project + cached_bytes + growth
                peak = max(peak, effective)
                if effective > LIMIT or effective - (before_project + cached_bytes) > args.reserve_bytes:
                    raise RuntimeError('Storage limit/reserve exceeded; terminating owned offline build')
                if time.monotonic() - started > args.timeout_seconds:
                    raise RuntimeError('Bounded build deadline exceeded')
                time.sleep(1)
            if process.returncode != 0:
                raise RuntimeError('Offline Gradle build failed; inspect ignored log')
        if sources != source_hashes():
            raise RuntimeError('Probe source changed during build')
        effective = sum(inventory(PROJECT).values()) + cached_bytes + cache_growth(before_cache, inventory(gradle_home / 'caches'))
        if effective > LIMIT or effective - (before_project + cached_bytes) > args.reserve_bytes:
            raise RuntimeError('Storage bound exceeded at terminal build check')
        apk = HERE / 'app/build/outputs/apk/debug/app-debug.apk'
        inspected = inspect_apk(apk, Path(pins[0]['resolved_path']), tools)
        # Fail on an existing destination atomically. Hard-link/move avoids another APK data copy.
        os.link(apk, output); apk.unlink()
        effective = sum(inventory(PROJECT).values()) + cached_bytes + cache_growth(before_cache, inventory(gradle_home / 'caches'))
        if effective > LIMIT or effective - (before_project + cached_bytes) > args.reserve_bytes:
            raise RuntimeError('Storage bound exceeded at verified artifact check')
        report.update(inspected)
        report.update(status='private_apk_verified', artifact_path=str(output.relative_to(PROJECT)),
                      artifact_bytes=output.stat().st_size, artifact_sha256=sha256(output))
    except BaseException as error:
        if process is not None:
            terminate_owned(process)
        report.update(status='failed', error=type(error).__name__ + ': ' + str(error))
        raise
    finally:
        current_project = sum(inventory(PROJECT).values())
        growth = cache_growth(before_cache, inventory(gradle_home / 'caches'))
        report.update(project_bytes_after=current_project, additional_global_cache_bytes=growth,
                      peak_additional_global_cache_bytes=max(cache_peak, growth),
                      peak_polled_effective_bytes=max(peak, current_project + cached_bytes + growth),
                      elapsed_seconds=time.monotonic() - started,
                      storage_measurement_scope='Logical project bytes plus pinned external JARs and positive global Gradle-cache growth; poll sampling is not a continuous peak proof')
        with report_file.open('x') as stream:
            json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({'status': report['status'], 'apk_sha256': report.get('artifact_sha256'),
                      'apk_bytes': report.get('artifact_bytes'), 'report': str(report_file.relative_to(PROJECT))}))


if __name__ == '__main__':
    main()
