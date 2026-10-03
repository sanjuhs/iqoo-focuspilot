"""Build opaque prior-request exclusions before compatible cohort authoring."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('prior_inventory', ROOT/'prototype/qwen-balanced-data/generate_data.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

def digest(text):
    return hashlib.sha256(text.encode('utf-8', errors='surrogatepass')).hexdigest()

def java_strings(source):
    # Skip comments and character literals before reading double-quoted strings.
    token = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|\'(?:\\.|[^\'\\])*\'|"((?:\\.|[^"\\\r\n])*)"')
    values=[]
    escapes={'b':'\b','t':'\t','n':'\n','f':'\f','r':'\r','s':' ','"':'"',"'":"'",'\\':'\\'}
    for match in token.finditer(source):
        raw=match.group(1)
        if raw is None: continue
        decoded=[];i=0
        while i<len(raw):
            if raw[i]!='\\': decoded.append(raw[i]);i+=1;continue
            i+=1
            if i>=len(raw): raise ValueError('Incomplete Java escape')
            if raw[i] in escapes: decoded.append(escapes[raw[i]]);i+=1
            elif raw[i]=='u':
                while i<len(raw) and raw[i]=='u': i+=1
                part=raw[i:i+4]
                if not re.fullmatch('[0-9a-fA-F]{4}',part): raise ValueError('Invalid Java Unicode escape')
                decoded.append(chr(int(part,16)));i+=4
            elif raw[i] in '01234567':
                end=i+1;limit=3 if raw[i] in '0123' else 2
                while end<len(raw) and end-i<limit and raw[end] in '01234567': end+=1
                decoded.append(chr(int(raw[i:end],8)));i=end
            else: raise ValueError('Unsupported Java literal escape')
        values.append(''.join(decoded))
    return values

def main():
    inventory, values = previous.inventory_sources()
    seen = {x['path'] for x in inventory}
    extra = set()
    for folder in (ROOT/'prototype').iterdir():
        if not folder.is_dir() or folder.name == 'compatible-data':
            continue
        extra.update(folder.glob('*.java'))
        extra.update(folder.glob('test*.py'))
        for path in (folder/'build').glob('*.jsonl'):
            if path.stat().st_size > 2_000_000:
                continue
            rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            if rows and all(isinstance(row, dict) and 'utterance' in row for row in rows):
                extra.add(path)
    for path in sorted(extra):
        relative = str(path.relative_to(ROOT))
        if relative in seen:
            continue
        if path.suffix=='.java':
            texts=java_strings(path.read_text())
            texts+=previous.inventory_util.prompt_examples(texts)
            # Structured/unit prompt examples have quoted request => JSON syntax.
            texts += [m.group(1) for value in list(texts) for m in re.finditer(r"'([^'\n]+)'\s*=>\s*\{",value)]
            method='Decoded Java string tokens, excluding comments/char literals, plus intent and structured prompt examples'
        else:
            texts, method = previous.inventory_util.extract_requests(path)
        inventory.append({'path':relative,'sha256':previous.sha(path),'text_count':len(texts),'method':method,'previous_required':False})
        values.extend(texts)
        seen.add(relative)
    families, templates = set(), set()
    def collect(value):
        if isinstance(value,dict):
            for key in ('family','family_id'):
                if isinstance(value.get(key),str): families.add(value[key])
            for key in ('template','template_id'):
                if isinstance(value.get(key),str): templates.add(value[key])
            for item in value.values(): collect(item)
        elif isinstance(value,list):
            for item in value: collect(item)
    for item in inventory:
        path=ROOT/item['path']
        if path.suffix in ('.json','.jsonl'):
            collect([json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.suffix=='.jsonl' else json.loads(path.read_text()))
    bundle={'schema':'focuspilot.natural_exclusion.v1','normalization':'ascii-alnum-lower-v1',
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'exact_encoding':'UTF-8; surrogatepass only for invalid source-test literals',
        'normalized_request_sha256':sorted({digest(previous.normalize(v)) for v in values}),
        'exact_request_sha256':sorted({digest(v) for v in values}),
        'family_sha256':sorted(map(digest,families)),'template_sha256':sorted(map(digest,templates)),
        'inventory':sorted(inventory,key=lambda x:x['path']),'no_raw_requests':True,
        'candidate_fixture_text_opaque_to_fresh_author':True}
    with (TASK/'novelty-exclusions.json').open('x') as stream:
        json.dump(bundle,stream,indent=2);stream.write('\n')
    print(json.dumps({'inventory_sources':len(inventory),'normalized_hashes':len(bundle['normalized_request_sha256']),'families':len(families),'templates':len(templates)}))

if __name__=='__main__': main()
