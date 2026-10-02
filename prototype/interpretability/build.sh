#!/bin/sh
set -eu
LAB_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LLAMA_PREFIX=${LLAMA_PREFIX:-/opt/homebrew/opt/llama.cpp}
case "$("$LLAMA_PREFIX/bin/llama-server" --version 2>&1)" in
  *57fe1f07c*) ;;
  *) echo 'Pinned llama.cpp runtime mismatch' >&2; exit 1;;
esac
mkdir -p "$LAB_DIR/build"
clang++ -std=c++17 -O2 -I"$LLAMA_PREFIX/include" -I/opt/homebrew/include \
  "$LAB_DIR/probe.cpp" -L"$LLAMA_PREFIX/lib" -L/opt/homebrew/lib \
  -lllama -lggml -lggml-base -Wl,-rpath,"$LLAMA_PREFIX/lib" -Wl,-rpath,/opt/homebrew/lib \
  -o "$LAB_DIR/build/intervention_probe"
