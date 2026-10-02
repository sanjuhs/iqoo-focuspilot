"""Bound one owned offline MLX child; preserve process records and failed attempts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]


def main():
    args = sys.argv[1:]
    phase = args[args.index('--phase') + 1]
    out = Path(args[args.index('--out') + 1]).resolve()
    if phase not in ('preflight', 'dev', 'train', 'confirmation') or not out.is_relative_to(TASK / 'build'):
        raise ValueError('Known phase and ignored owned output required')
    log = out.with_name(out.name + '-process.json')
    stdout = out.with_name(out.name + '-stdout.log')
    stderr = out.with_name(out.name + '-stderr.log')
    record = {'phase': phase, 'completed': False, 'timeout_seconds': 600 if phase == 'train' else 240,
              'command': [sys.executable, str(TASK / 'run.py'), *args], 'timed_out': False}
    with log.open('x') as f:
        json.dump(record, f, indent=2)
    began = time.monotonic()
    with stdout.open('x') as fout, stderr.open('x') as ferr:
        child = subprocess.Popen(record['command'], cwd=ROOT, stdout=fout, stderr=ferr,
            env={**os.environ, 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'})
        record['pid'] = child.pid
        log.write_text(json.dumps(record, indent=2) + '\n')
        try:
            record['exit_code'] = child.wait(timeout=record['timeout_seconds'])
        except subprocess.TimeoutExpired:
            record['timed_out'] = True
            child.kill()
            record['exit_code'] = child.wait(timeout=15)
    record['elapsed_seconds'] = time.monotonic() - began
    record['completed'] = not record['timed_out'] and record['exit_code'] == 0
    log.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)
    if not record['completed']:
        print(stderr.read_text()[-4000:], file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
