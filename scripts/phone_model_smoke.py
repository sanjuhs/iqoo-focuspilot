#!/usr/bin/env python3
"""Own-app-only synthetic model smoke test. No permission grants or action execution.

Unlock FocusPilot first. Outputs contain synthetic commands/metrics only; never
raw UI or screenshots. Timing is the native runtime's reported inference time.
"""
import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = "dev.focuspilot.prototype"


def own_interactive_foreground(window, activity, package=PACKAGE):
    """Require observed awake/unlocked state; missing flags never imply unlocked."""
    focus = next((line for line in window.splitlines() if "mCurrentFocus=" in line), "")
    owner = re.search(r"(?:^|\s)" + re.escape(package) + r"/", focus)
    awake = re.findall(r"\bmAwake\s*=\s*(true|false)", window)
    legacy = re.findall(r"\bmShowingLockscreen\s*=\s*(true|false)", window)
    keyguard = re.findall(r"\bmKeyguardShowing\s*=\s*(true|false)", activity)
    if not owner or not awake or any(value != "true" for value in awake):
        return False
    if any(value != "false" for value in legacy + keyguard):
        return False
    return bool(legacy or keyguard)


class PhoneLab:
    def __init__(self, serial):
        self.base = ["adb", "-s", serial]

    def adb(self, *args):
        return subprocess.check_output(self.base + list(args), text=True, timeout=20)

    def guard(self):
        for _ in range(4):
            window = self.adb("shell", "dumpsys", "window")
            activity = self.adb("shell", "dumpsys", "activity", "activities")
            if own_interactive_foreground(window, activity):
                return
            time.sleep(.3)
        raise RuntimeError("FocusPilot must be unlocked and in front; no other screen is inspected")

    def nodes(self):
        self.guard()
        self.adb("shell", "uiautomator", "dump", "/sdcard/focuspilot-lab.xml")
        root = ET.fromstring(self.adb("shell", "cat", "/sdcard/focuspilot-lab.xml"))
        self.guard()
        return [n for n in root.iter("node") if n.get("package") == PACKAGE]

    def find(self, label, scroll=True):
        for _ in range(14 if scroll else 1):
            for node in self.nodes():
                if node.get("text", "").casefold() == label.casefold():
                    xy = list(map(int, re.findall(r"\d+", node.get("bounds"))))
                    if xy[3] - xy[1] < 25:
                        continue
                    return node
            if scroll:
                self.guard()
                self.adb("shell", "input", "swipe", "540", "1800", "540", "700", "350")
        raise RuntimeError("Own-app control not visible: " + label)

    def tap(self, label, scroll=True):
        node=self.find(label,scroll)
        xy=list(map(int,re.findall(r"\d+",node.get("bounds"))))
        self.guard()
        self.adb("shell","input","tap",str((xy[0]+xy[2])//2),str((xy[1]+xy[3])//2))

    def top(self):
        self.guard()
        for _ in range(5):
            self.guard()
            self.adb("shell", "input", "swipe", "540", "650", "540", "1900", "180")

    def command(self, value):
        if not re.fullmatch(r"[A-Za-z0-9 :]+", value):
            raise ValueError("Smoke input must be simple synthetic ASCII")
        self.top()
        node=None
        for _ in range(8):
            node=next((n for n in self.nodes() if n.get("class")=="android.widget.EditText"),None)
            if node is not None: break
            self.guard()
            self.adb("shell","input","swipe","540","1800","540","700","350")
        if node is None: raise RuntimeError("Own-app editable command not visible")
        xy = list(map(int, re.findall(r"\d+", node.get("bounds"))))
        self.adb("shell", "input", "tap", str((xy[0]+xy[2])//2), str((xy[1]+xy[3])//2))
        self.adb("shell", "input", "keyevent", "KEYCODE_MOVE_END")
        # Long DEL removes only the own-app command field's previous text.
        self.adb("shell", "input", "keyevent", "--longpress", "KEYCODE_DEL")
        self.adb("shell", "input", "keycombination", "113", "29")  # Ctrl+A
        self.adb("shell", "input", "text", value.replace(" ", "%s"))
        self.adb("shell", "input", "keyevent", "KEYCODE_BACK")
        actual = next(n.get("text") for n in self.nodes() if n.get("class") == "android.widget.EditText")
        if actual != value:
            raise RuntimeError("Synthetic command field did not match requested input; no inference performed")

    def run(self, value, capture=False, *, wake_display=True):
        self.command(value)
        node=self.find("Capture selected actual activation summaries")
        if (node.get("checked")=="true")!=capture:
            self.tap(node.get("text"),scroll=False)
        self.tap("Understand command locally")
        self.guard()
        self.adb("shell","input","swipe","540","1800","540","1100","250")
        began = time.monotonic()
        while time.monotonic()-began < 60:
            # Wake display only; this does not bypass a keyguard.
            if wake_display:
                self.adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
            for node in self.nodes():
                value_text = node.get("text", "")
                if value_text.startswith("Model proposal:"):
                    match = re.search(r"CPU total ([\d.]+) ms · prefill ([\d.]+) ms · decode ([\d.]+) ms", value_text)
                    if not match:
                        raise RuntimeError("Runtime metrics missing")
                    return {"command":value,"capture":capture,"intent":value_text.splitlines()[0].split(": ")[1],
                            "gate":value_text.splitlines()[1].split(": ")[1],
                            "total_ms":float(match[1]),"prefill_ms":float(match[2]),"decode_ms":float(match[3]),
                            "action_executed":False}
                if value_text.startswith("Inference failed"):
                    raise RuntimeError(value_text)
            time.sleep(.5)
        raise RuntimeError("Model request did not finish within 60 seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", default="generic")
    args = parser.parse_args()
    lab = PhoneLab(args.serial)
    lab.adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    lab.guard()
    texts = [n.get("text", "") for n in lab.nodes()]
    if "MIRA · LOCAL MODEL LAB" not in texts:
        lab.tap("Ask Mira" if "Ask Mira" in texts else "Open local command model")
    texts = [n.get("text", "") for n in lab.nodes()]
    if not any(t.startswith("LOCAL MODEL LOADED") for t in texts):
        lab.tap("Load verified local model")
        for _ in range(12):
            if any(n.get("text", "").startswith("LOCAL MODEL LOADED") for n in lab.nodes()):
                break
        else:
            raise RuntimeError("Model did not load")
    results = []
    for command, capture in [("Please start a focus session",False),("Please start a focus session",False),
                             ("Please start a focus session",True),("Do not start focus",False),
                             ("Start focus and open settings",False)]:
        item = lab.run(command,capture)
        results.append(item)
        print(json.dumps(item),flush=True)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({"variant":args.variant,"model":"Qwen3.5-0.8B-Q4_0",
            "device":"Nothing A059/SM7635/API36","backend":"CPU","context":1024,"threads":4,
            "synthetic_smoke_only":True,"results":results},indent=2)+"\n")


if __name__ == "__main__":
    main()
