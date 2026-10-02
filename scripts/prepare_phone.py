#!/usr/bin/env python3
"""Install the research APK and stream a checksummed model into debug app storage.

Does not grant usage/microphone/notification permissions or change device settings.
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "dev.focuspilot.prototype"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "prototype/qwen/model-manifest.json").read_text())["models"]["qwen35"]
    model = args.model or ROOT / "models/qwen" / manifest["file"]
    if not model.is_file() or model.stat().st_size != manifest["bytes"]:
        parser.error(f"Missing or wrong-sized model: {model}")
    with model.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != manifest["sha256"]:
        parser.error("Model checksum differs; no phone changes made")
    base = ["adb", "-s", args.serial]
    state = subprocess.check_output(base + ["get-state"], text=True).strip()
    if state != "device":
        parser.error("Phone is not authorized")
    if not args.skip_install:
        apk = ROOT / "prototype/android/app/build/outputs/apk/debug/app-debug.apk"
        if not apk.is_file():
            parser.error("Build the research APK first")
        subprocess.run(base + ["install", "-r", str(apk)], check=True)
    # mmap-loaded weights must not be truncated while inference is using them.
    subprocess.run(base + ["shell", "am", "force-stop", PACKAGE], check=True)
    subprocess.run(base + ["shell", "run-as", PACKAGE, "mkdir", "-p", "files"], check=True)
    print("Streaming verified GGUF directly to app-private files; no public staging copy.", flush=True)
    with model.open("rb") as stream:
        process = subprocess.Popen(base + ["exec-in", "run-as", PACKAGE, "dd", "of=files/qwen35.gguf.pending", "bs=1048576"], stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            out, error = process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise RuntimeError("ADB model transfer timed out; run preparation again") from None
    if process.returncode:
        raise RuntimeError("ADB model transfer failed: " + error.decode(errors="replace"))
    verified = subprocess.check_output(base + ["shell", "run-as", PACKAGE, "sha256sum", "files/qwen35.gguf.pending"], text=True).split()[0]
    if verified != manifest["sha256"]:
        raise RuntimeError("Phone copy checksum differs; app will refuse to load it")
    subprocess.run(base + ["shell", "run-as", PACKAGE, "mv", "files/qwen35.gguf.pending", "files/qwen35.gguf"], check=True)
    print("Phone model checksum matches. Permissions remain user-controlled.")
    # A large USB transfer can briefly reset ADB transport on some phones.
    for attempt in range(3):
        launched = subprocess.run(base + ["shell", "am", "start", "-W", "-n", PACKAGE + "/.MainActivity"], capture_output=True, text=True)
        if launched.returncode == 0 and "Error:" not in launched.stdout:
            print("FocusPilot launch requested. Unlock the phone to inspect it.")
            break
        if attempt == 2:
            raise RuntimeError("Model prepared, but app launch failed. Reconnect and open FocusPilot manually.")
        time.sleep(1)


if __name__ == "__main__":
    main()
