"""Score immutable MLX diagnostics with the same frozen Java request gate."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK.parent / 'qwen-balanced-native'))
import run_capture as native
import score
import run as trainer


def main():
    p = argparse.ArgumentParser()
    for key in ('lock', 'run', 'arm', 'data', 'out', 'source-commit'):
        p.add_argument('--' + key, required=True)
    a = p.parse_args()
    lock = native.strict_json(Path(a.lock).read_text())
    native.verify_lock(lock, a.source_commit)
    rows = score.read_rows(a.data, lock)
    run_dir = Path(a.run).resolve()
    status = native.strict_json((run_dir / 'status.json').read_text())
    if not status.get('completed') or status['data_sha256'] != native.sha(a.data):
        raise ValueError('Completed selected MLX phase required')
    records_path = run_dir / (a.arm + '-predictions.json')
    records = native.strict_json(records_path.read_text())
    if [r['id'] for r in records] != [r['id'] for r in rows] or any(
        not r['canonical_eos'] or not r['reached_eos'] or r['expected'] != row['intent']
        or r['actual'] not in native.INTENTS or r['prompt_sha256'] !=
        __import__('hashlib').sha256(trainer.render_prompt(row['utterance']).encode()).hexdigest()
        for r, row in zip(records, rows)):
        raise ValueError('Exact canonical/EOS/prompt/gold inventory required')
    predictions = {r['id']: r['actual'] for r in records}
    out = Path(a.out).resolve()
    if not out.is_relative_to(TASK / 'build'):
        raise ValueError('Private ignored output required')
    out.mkdir(parents=True, exist_ok=False)
    result = {'scope': 'MLX Metal host token-trie diagnostic; same Java gate; not native/phone',
              'promoted': False, 'source_commit': a.source_commit,
              'status_sha256': native.sha(run_dir / 'status.json'),
              'predictions_sha256': native.sha(records_path), 'gold_sha256': native.sha(a.data),
              'lock_sha256': native.sha(a.lock), 'canonical_eos': len(records)}
    for route in ('generated', 'oracle'):
        inp = out / (route + '-gate.tsv')
        with inp.open('x') as f:
            for row in rows:
                f.write(row['id'] + '\t' + (predictions[row['id']] if route == 'generated'
                        else row['oracle_intent']) + '\t' + row['utterance'] + '\n')
        raw = subprocess.check_output([str(native.JAVA / 'java'), '-cp', lock['classes'],
            'dev.focuspilot.prototype.CommandGateEval', str(inp)], text=True, timeout=30)
        (out / (route + '-gate-output.tsv')).write_text(raw)
        proposals = {}
        for line in raw.splitlines():
            f = line.split('\t')
            if len(f) != 6 or f[0] in proposals:
                raise ValueError('Invalid gate record')
            proposals[f[0]] = {'kind': f[1], 'hour': int(f[2]), 'minute': int(f[3]), 'seconds': int(f[4])}
        result[route], details = score.summarize(rows, predictions, proposals)
        native.write_new(out / (route + '-details.json'), details)
    native.verify_lock(lock, a.source_commit)
    native.write_new(out / 'summary.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
