#!/bin/sh
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
task_variant=${NATIVE_BUILD_VARIANT:-generic}
case "$task_variant" in
  generic) task_native_dir=android-arm64 ;;
  optimized) task_native_dir=android-arm64-optimized ;;
  *) echo 'NATIVE_BUILD_VARIANT must be generic or optimized' >&2; exit 1 ;;
esac
# Keep third-party sources outside Git; checkout the exact native runtime revision.
if [ ! -d "$task_root/research/llama.cpp/.git" ]; then
  mkdir -p "$task_root/research/llama.cpp"
  git -C "$task_root/research/llama.cpp" init
  git -C "$task_root/research/llama.cpp" remote add origin https://github.com/ggml-org/llama.cpp.git
  git -C "$task_root/research/llama.cpp" fetch --depth 1 origin 57fe1f07c3b6a1de3f4fff19098e2056a85275b7
  git -C "$task_root/research/llama.cpp" checkout --detach FETCH_HEAD
fi
"$task_root/prototype/native/build-android.sh"
mkdir -p "$task_root/prototype/android/app/src/main/jniLibs/arm64-v8a"
cp "$task_root/prototype/native/build/$task_native_dir/libfocuspilot_local.so" "$task_root/prototype/android/app/src/main/jniLibs/arm64-v8a/"
cp "$task_root/prototype/native/java/LocalModel.java" "$task_root/prototype/android/app/src/main/java/dev/focuspilot/prototype/LocalModel.java"
cd "$task_root/prototype/android"
./gradlew testDebugUnitTest assembleDebug lintDebug "$@"
