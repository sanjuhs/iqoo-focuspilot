"""Give the fresh author only opaque overlap hashes, including candidate fixtures."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'prototype/qwen-balanced-data'))
import generate_data as previous


def text_sha(text):
    # Invalid Java test surrogates are adversarial fixtures, never allowed corpus text.
    # For valid fresh strings this equals ordinary UTF-8; normalization is always ASCII.
    return hashlib.sha256(text.encode('utf-8', errors='surrogatepass')).hexdigest()


def main():
    inventory, values = previous.inventory_sources()
    seen = {entry['path'] for entry in inventory}
    extra = set()
    for p in (ROOT / 'prototype/qwen-balanced-data/build').glob('*.jsonl'):
        rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
        if rows and all('utterance' in r for r in rows):
            extra.add(p)
    for folder in ('qwen-natural-validation', 'qwen-natural-eval', 'qwen-natural-data', 'qwen-focus-summary'):
        d = ROOT / 'prototype' / folder
        extra.update(d.glob('*.java'))
        extra.update(d.glob('*.py'))
    for p in sorted(extra):
        relative = str(p.relative_to(ROOT))
        if relative in seen:
            continue
        texts, method = previous.inventory_util.extract_requests(p)
        inventory.append({'path': relative, 'sha256': previous.sha(p), 'text_count': len(texts),
                          'method': method, 'previous_required': False})
        values.extend(texts)
        seen.add(relative)
    families, templates = set(), set()
    def collect(x):
        if isinstance(x, dict):
            for key in ('family', 'family_id'):
                if isinstance(x.get(key), str):
                    families.add(x[key])
            for key in ('template_id', 'template'):
                if isinstance(x.get(key), str):
                    templates.add(x[key])
            for value in x.values():
                collect(value)
        elif isinstance(x, list):
            for value in x:
                collect(value)
    for item in inventory:
        p = ROOT / item['path']
        if p.suffix in ('.jsonl', '.json'):
            data = ([json.loads(x) for x in p.read_text().splitlines() if x.strip()]
                    if p.suffix == '.jsonl' else json.loads(p.read_text()))
            collect(data)
    bundle = {'schema': 'focuspilot.natural_exclusion.v1',
              'normalization': 'ascii-alnum-lower-v1',
              'exact_encoding': 'UTF-8; surrogatepass only for invalid source-test literals',
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'normalized_request_sha256': sorted({text_sha(previous.normalize(s)) for s in values}),
              'exact_request_sha256': sorted({text_sha(s) for s in values}),
              'family_sha256': sorted(map(text_sha, families)),
              'template_sha256': sorted(map(text_sha, templates)),
              'inventory': sorted(inventory, key=lambda x: x['path']),
              'no_raw_requests': True, 'candidate_fixture_text_opaque_to_fresh_author': True}
    path = ROOT / 'prototype/qwen-natural-eval/novelty-exclusions.json'
    with path.open('x') as f:
        json.dump(bundle, f, indent=2)
        f.write('\n')
    print(json.dumps({'bundle_sha256': previous.sha(path), 'inventory_sources': len(inventory),
        'normalized_hashes': len(bundle['normalized_request_sha256']), 'families': len(families),
        'templates': len(templates)}))


if __name__ == '__main__':
    main()
