#!/bin/sh
set -eu
NATIVE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$NATIVE_DIR/../.." && pwd)
sh "$NATIVE_DIR/build-host.sh"
node --input-type=module - "$PROJECT_DIR" <<'JS'
import fs from 'node:fs';
import path from 'node:path';
const project=process.argv[2];
const cases=JSON.parse(fs.readFileSync(path.join(project,'prototype/qwen/intent-holdout.json'),'utf8'));
fs.writeFileSync(path.join(project,'prototype/native/build/prompt-cases.tsv'),cases.map(x=>[x.id,x.expected.intent,x.command].join('\t')).join('\n'));
JS
javac -cp "$NATIVE_DIR/build/java" -d "$NATIVE_DIR/build/java" "$NATIVE_DIR/java/PromptBenchmark.java"
java -Djava.library.path="$NATIVE_DIR/build/host" -cp "$NATIVE_DIR/build/java" \
  dev.focuspilot.prototype.PromptBenchmark "$PROJECT_DIR/models/qwen/Qwen3.5-0.8B-Q4_0.gguf" \
  "$NATIVE_DIR/build/prompt-cases.tsv" > "$NATIVE_DIR/build/prompt-comparison.tsv" \
  2> "$NATIVE_DIR/build/prompt-comparison.log"
echo "Raw per-case envelopes: $NATIVE_DIR/build/prompt-comparison.tsv"
