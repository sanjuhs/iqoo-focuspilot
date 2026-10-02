#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
TASK=prototype/command-eval
MODEL=${1:-models/qwen/Qwen3.5-0.8B-Q4_0.gguf}
JAVA_RUNTIME=${JAVA_HOME:-/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home}
LLAMA_PREFIX=/opt/homebrew/opt/llama.cpp
VERSION=$("$LLAMA_PREFIX/bin/llama-server" --version 2>&1)
case "$VERSION" in *57fe1f07c*) ;; *) echo 'Host llama runtime differs from pinned source' >&2;exit 1;; esac
mkdir -p "$TASK/build/source" "$TASK/build/native" "$TASK/build/java"
cp prototype/native/core.cpp prototype/native/core.h prototype/native/jni.cpp "$TASK/build/source/"
clang++ -std=c++17 -O2 -fPIC -shared \
 -I"$LLAMA_PREFIX/include" -I/opt/homebrew/include -I"$JAVA_RUNTIME/include" -I"$JAVA_RUNTIME/include/darwin" \
 "$TASK/build/source/core.cpp" "$TASK/build/source/jni.cpp" \
 -L"$LLAMA_PREFIX/lib" -L/opt/homebrew/lib -lllama -lggml -lggml-base \
 -Wl,-rpath,"$LLAMA_PREFIX/lib" -Wl,-rpath,/opt/homebrew/lib \
 -o "$TASK/build/native/libfocuspilot_local.dylib"
"$JAVA_RUNTIME/bin/javac" -d "$TASK/build/java" \
 prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java "$TASK/NativeEval.java"
"$JAVA_RUNTIME/bin/java" -Djava.library.path="$TASK/build/native" -cp "$TASK/build/java" \
 dev.focuspilot.prototype.NativeEval "$MODEL" "$TASK/build/native-input.tsv"
