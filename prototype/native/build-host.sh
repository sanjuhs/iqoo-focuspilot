#!/bin/sh
set -eu
NATIVE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
JAVA_RUNTIME=${JAVA_HOME:-$(/usr/libexec/java_home)}
LLAMA_PREFIX=${LLAMA_PREFIX:-/opt/homebrew/opt/llama.cpp}
RUNTIME_VERSION=$("$LLAMA_PREFIX/bin/llama-server" --version 2>&1)
case "$RUNTIME_VERSION" in *57fe1f07c*) ;; *) echo 'Host llama runtime does not match pinned commit' >&2; exit 1 ;; esac
mkdir -p "$NATIVE_DIR/build/host" "$NATIVE_DIR/build/java"
clang++ -std=c++17 -O2 -fPIC -shared \
  -I"$LLAMA_PREFIX/include" -I/opt/homebrew/include -I"$JAVA_RUNTIME/include" -I"$JAVA_RUNTIME/include/darwin" \
  "$NATIVE_DIR/core.cpp" "$NATIVE_DIR/jni.cpp" \
  -L"$LLAMA_PREFIX/lib" -L/opt/homebrew/lib -lllama -lggml -lggml-base \
  -Wl,-rpath,"$LLAMA_PREFIX/lib" -Wl,-rpath,/opt/homebrew/lib \
  -o "$NATIVE_DIR/build/host/libfocuspilot_local.dylib"
clang++ -std=c++17 -O2 -I"$LLAMA_PREFIX/include" -I/opt/homebrew/include \
  "$NATIVE_DIR/core.cpp" "$NATIVE_DIR/probe.cpp" -L"$LLAMA_PREFIX/lib" -L/opt/homebrew/lib \
  -lllama -lggml -lggml-base -Wl,-rpath,"$LLAMA_PREFIX/lib" -Wl,-rpath,/opt/homebrew/lib \
  -o "$NATIVE_DIR/build/host/focuspilot_probe"
javac -d "$NATIVE_DIR/build/java" "$NATIVE_DIR/java/LocalModel.java" "$NATIVE_DIR/java/NativeSmoke.java"
