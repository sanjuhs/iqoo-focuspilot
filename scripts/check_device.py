#!/usr/bin/env python3
"""Read-only ADB verification. No captures, permissions or device changes."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def adb(*args):
    return subprocess.run(["adb", *args], check=True, capture_output=True,
                          text=True, timeout=20).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", help="Select one device if multiple are connected")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    if not shutil.which("adb"):
        parser.error("adb is missing; install Android SDK Platform Tools")
    entries = [line.split()[:2] for line in adb("devices").splitlines()[1:]
               if line.strip()]
    if args.serial:
        entries = [entry for entry in entries if entry[0] == args.serial]
    if len(entries) != 1:
        parser.error("Connect one phone or select a connected device with --serial")
    serial, state = entries[0]
    if state != "device":
        print(json.dumps({"authorized": False, "adb_state": state}, indent=2))
        print("Unlock phone and accept this computer's USB debugging prompt.", file=sys.stderr)
        return 2
    properties = {
        "manufacturer": "ro.product.manufacturer",
        "model": "ro.product.model",
        "android_version": "ro.build.version.release",
        "api_level": "ro.build.version.sdk",
        "soc": "ro.soc.model",
        "abi": "ro.product.cpu.abi",
    }
    report = {"authorized": True, "adb_state": state}
    for key, prop in properties.items():
        report[key] = adb("-s", serial, "shell", "getprop", prop)
    report["shell_check"] = adb("-s", serial, "shell", "pm", "path",
                                "com.android.settings").startswith("package:")
    report["npu_verified"] = False
    report["office_kit_verified"] = False
    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    return 0 if report["shell_check"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
