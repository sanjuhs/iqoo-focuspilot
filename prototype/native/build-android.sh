#!/bin/sh
set -eu
NATIVE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$NATIVE_DIR/../.." && pwd)
EXPECTED_COMMIT=57fe1f07c3b6a1de3f4fff19098e2056a85275b7
ACTUAL_COMMIT=$(git -C "$PROJECT_DIR/research/llama.cpp" rev-parse HEAD)
[ "$ACTUAL_COMMIT" = "$EXPECTED_COMMIT" ] || { echo 'llama.cpp checkout does not match pinned commit' >&2; exit 1; }
SDK_ROOT=${ANDROID_SDK_ROOT:-"$HOME/Library/Android/sdk"}
NDK_ROOT="$SDK_ROOT/ndk/28.2.13676358"
case "${NATIVE_BUILD_VARIANT:-generic}" in
  generic) BUILD_DIR="$NATIVE_DIR/build/android-arm64"; ARM_ARCH=armv8-a; KLEIDIAI=OFF ;;
  optimized) BUILD_DIR="$NATIVE_DIR/build/android-arm64-optimized"; ARM_ARCH=armv8.2-a+dotprod+i8mm+fp16; KLEIDIAI=ON ;;
  *) echo 'NATIVE_BUILD_VARIANT must be generic or optimized' >&2; exit 1 ;;
esac
cmake -S "$NATIVE_DIR" -B "$BUILD_DIR" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$NDK_ROOT/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-28 -DANDROID_STL=c++_static \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CPU_ARM_ARCH="$ARM_ARCH" -DGGML_CPU_KLEIDIAI="$KLEIDIAI"
cmake --build "$BUILD_DIR" --target focuspilot_local -j 6
"$NDK_ROOT/toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-strip" --strip-unneeded "$BUILD_DIR/libfocuspilot_local.so"
echo "Built $BUILD_DIR/libfocuspilot_local.so"
