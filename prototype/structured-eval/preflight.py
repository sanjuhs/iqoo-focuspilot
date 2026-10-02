"""Vocabulary-only prompt-budget preflight; never generates or executes actions."""
import argparse
import subprocess
from pathlib import Path
from evaluate import driver, private, TASK, ROOT


def run(comparison, out):
    runtime = driver.runtime_guard()
    if driver.sha(driver.MODEL) != driver.MODEL_SHA:
        raise ValueError('Selected model differs')
    lock = driver.strict_json(Path(comparison).read_text())
    out = private(out); out.mkdir(parents=True, exist_ok=False)
    binary = out / 'token_count'
    command = ['clang++', '-std=c++17', '-O2', '-I/opt/homebrew/include',
               '-L/opt/homebrew/lib', '-Wl,-rpath,/opt/homebrew/lib',
               str(TASK / 'token_count.cpp'), '-lllama', '-o', str(binary)]
    subprocess.run(command, check=True, timeout=60)
    result = {'schema': 'focuspilot.structured_token_preflight.v1',
              'generation_called': False, 'model_sha256': driver.MODEL_SHA,
              'comparison_lock_sha256': driver.sha(comparison), 'compile_command': command,
              'compiler_version': subprocess.check_output(['clang++', '--version'], text=True),
              'runtime_files_sha256': runtime, 'binary_sha256': driver.sha(binary),
              'source_sha256': driver.sha(TASK / 'token_count.cpp'), 'arms': {}}
    for arm in ('baseline', 'structured'):
        native = driver.strict_json(Path(lock['locks'][arm]).read_text())
        prompts = driver.prompts(native['prompts'])
        folder = out / arm; folder.mkdir()
        for ident, prompt in prompts:
            (folder / (ident + '.txt')).write_bytes(prompt.encode())
        job_command = [str(binary), str(driver.MODEL), str(folder)]
        with (out / (arm + '-tokens.jsonl')).open('x') as stdout, (out / (arm + '-stderr.log')).open('x') as stderr:
            process = subprocess.run(job_command, stdout=stdout, stderr=stderr, timeout=60)
        if process.returncode != 0: raise ValueError('Token budget preflight failed; preserve outputs')
        measured = [driver.strict_json(line) for line in (out / (arm + '-tokens.jsonl')).read_text().splitlines()]
        if [r['id'] for r in measured] != sorted(ident for ident, _ in prompts):
            raise ValueError('Exact tokenizer inventory required')
        if not all(type(r['token_count']) is int and 0 < r['token_count'] <= 896
                   and r['within_limit'] is True and r['generation_called'] is False
                   and r['add_special'] is True and r['parse_special'] is True for r in measured):
            raise ValueError('Actual pinned tokenizer bounds required')
        result['arms'][arm] = {'rows': len(measured), 'minimum': min(r['token_count'] for r in measured),
                              'maximum': max(r['token_count'] for r in measured), 'exit_code': 0,
                              'command': job_command, 'prompts_sha256': driver.sha(native['prompts'])}
    result['private_files_sha256'] = {str(p.relative_to(ROOT)): driver.sha(p)
                                     for p in out.rglob('*') if p.is_file()}
    driver.write_new(out / 'preflight.json', result)
    return out / 'preflight.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--comparison', required=True)
    parser.add_argument('--out', required=True); args = parser.parse_args()
    print(run(args.comparison, args.out))
