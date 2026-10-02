#!/bin/sh
set -eu
LAB_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_DIR=$(CDPATH= cd -- "$LAB_DIR/../.." && pwd)
LLAMA_PREFIX=${LLAMA_PREFIX:-/opt/homebrew/opt/llama.cpp}
case "$("$LLAMA_PREFIX/bin/llama-server" --version 2>&1)" in
  *57fe1f07c*) ;;
  *) echo 'Pinned llama.cpp runtime mismatch' >&2; exit 1;;
esac
ADAPTER="$REPO_DIR/prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java"
ADAPTER_SHA=$(shasum -a 256 "$ADAPTER" | cut -d ' ' -f 1)
case "$ADAPTER_SHA" in
  2f6784c524ca9304fd714b86c04f5b1c3c5deb7e5ff562fbc34ae32c39e51e5d) ;;
  *) echo 'Frozen adapter changed; review prompt parity before building probe' >&2; exit 1;;
esac
TEMPLATE_SHA=$(python3 - "$LAB_DIR" <<'PY'
import json,pathlib,re,sys
lab=pathlib.Path(sys.argv[1]);source=(lab/'probe.cpp').read_text();template=json.loads((lab/'prompt-template.json').read_text())
literal=r'"(?:\\.|[^"\\])*"'
system=''.join(json.loads(s) for s in re.findall(literal,re.search(r'const std::string system=(.*?)\n\s*return',source,re.S)[1]))
parts=re.search(r'return\s*('+literal+r')\+system\+('+literal+r')\+input\+\s*('+literal+r');',source)
if not parts:raise SystemExit('Cannot verify probe prompt structure')
prefix=json.loads(parts[1])+system+json.loads(parts[2]);suffix=json.loads(parts[3])
sanitization=[[json.loads(a),json.loads(b)] for a,b in re.findall(r'replaceAll\(input,('+literal+r'),('+literal+r')\)',source)]
if (prefix,suffix,sanitization)!=(template['prefix'],template['suffix'],template['reserved_control_sanitization']):raise SystemExit('Probe/frozen prompt mismatch')
sha=template['template_sha256']
if not re.fullmatch('[0-9a-f]{64}',sha):raise SystemExit('Invalid prompt template hash')
print(sha)
PY
)
SOURCE_SHA=$(shasum -a 256 "$LAB_DIR/probe.cpp" | cut -d ' ' -f 1)
mkdir -p "$LAB_DIR/build"
clang++ -std=c++17 -O2 -Wno-deprecated-declarations \
  -DPROBE_SOURCE_SHA=\""$SOURCE_SHA"\" -DPROBE_ADAPTER_SHA=\""$ADAPTER_SHA"\" -DPROBE_TEMPLATE_SHA=\""$TEMPLATE_SHA"\" \
  -I"$LLAMA_PREFIX/include" -I/opt/homebrew/include \
  "$LAB_DIR/probe.cpp" -L"$LLAMA_PREFIX/lib" -L/opt/homebrew/lib \
  -lllama -lggml -lggml-base -Wl,-rpath,"$LLAMA_PREFIX/lib" -Wl,-rpath,/opt/homebrew/lib \
  -o "$LAB_DIR/build/intent_vector_probe"
python3 - "$LAB_DIR" "$LLAMA_PREFIX" <<'PY'
import hashlib,json,pathlib,subprocess,sys
lab,prefix=map(pathlib.Path,sys.argv[1:])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'schema':1,'platform':'macOS host CPU only','llama_commit':'57fe1f07c3b6a1de3f4fff19098e2056a85275b7',
 'compiler':subprocess.check_output(['clang++','--version'],text=True).splitlines()[0],
 'runtime_version':subprocess.run([str(prefix/'bin/llama-server'),'--version'],capture_output=True,text=True).stderr.strip(),
 'source_sha256':digest(lab/'probe.cpp'),'build_script_sha256':digest(lab/'build-probe.sh'),
 'prompt_template_file_sha256':digest(lab/'prompt-template.json'),
 'binary_sha256':digest(lab/'build/intent_vector_probe'),
 'libraries':{str(p.resolve()):digest(p) for p in [prefix/'lib/libllama.dylib',pathlib.Path('/opt/homebrew/lib/libggml.dylib'),pathlib.Path('/opt/homebrew/lib/libggml-base.dylib')]}}
(lab/'build/build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
PY
echo "Host probe: $LAB_DIR/build/intent_vector_probe" >&2
