#!/usr/bin/env python3
"""Explicit own-app focus action test. Starts/pauses focus; changes no OS permissions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from phone_model_smoke import PhoneLab, PACKAGE

MODEL_SHA="57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf"

def focus_state(lab):
    root=ET.fromstring(lab.adb("shell","run-as",PACKAGE,"cat","shared_prefs/focuspilot_research.xml"))
    # Never retain/export goal text, other settings, examples or the event trail.
    state={"activeCheckpoint":"false","observe":"false","points":"100"}
    for node in root:
        if node.get("name") in state:state[node.get("name")]=node.get("value")
    return state

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial",required=True)
    parser.add_argument("--expected-apk-sha256",required=True)
    parser.add_argument("--local-apk",type=Path,help="Optional matching local APK to bind its packaged ARM64 native-library identity")
    parser.add_argument("--source-commit",required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--execute-reviewed-focus-test",action="store_true",help="Explicitly authorize two benign own-app confirmations")
    args=parser.parse_args()
    if not args.execute_reviewed_focus_test:parser.error("This test changes focus state; explicitly pass --execute-reviewed-focus-test")
    if not re.fullmatch("[0-9a-f]{64}",args.expected_apk_sha256) or not re.fullmatch("[0-9a-f]{40}",args.source_commit):parser.error("Full APK SHA256 and source commit required")
    native_sha=None
    if args.local_apk:
        with args.local_apk.open("rb") as stream:local_sha=hashlib.file_digest(stream,"sha256").hexdigest()
        if local_sha!=args.expected_apk_sha256:raise RuntimeError("Local APK identity differs; no phone test started")
        with zipfile.ZipFile(args.local_apk) as apk_file:native_sha=hashlib.sha256(apk_file.read("lib/arm64-v8a/libfocuspilot_local.so")).hexdigest()
    lab=PhoneLab(args.serial);lab.adb("shell","input","keyevent","KEYCODE_WAKEUP");lab.guard()
    apk=lab.adb("shell","pm","path",PACKAGE).strip().split("package:",1)[1]
    apk_sha=lab.adb("shell","sha256sum",apk).split()[0]
    model_sha=lab.adb("shell","run-as",PACKAGE,"sha256sum","files/qwen35.gguf").split()[0]
    if apk_sha!=args.expected_apk_sha256 or model_sha!=MODEL_SHA:raise RuntimeError("Installed artifact identity differs; no action test started")
    initial=focus_state(lab)
    if initial["activeCheckpoint"]!="false" or initial["observe"]!="false":raise RuntimeError("Test requires an already paused session with observation off; existing user state left unchanged")
    results=[]
    device={name:lab.adb("shell","getprop",prop).strip() for name,prop in
        [("manufacturer","ro.product.manufacturer"),("model","ro.product.model"),("soc","ro.soc.model"),("api","ro.build.version.sdk")]}
    report={"research_only":True,"source_commit":args.source_commit,"apk_sha256":apk_sha,"model_sha256":model_sha,
        "device":device,"test_input":"typed synthetic own-app commands; explicit UI confirmations, not ASR",
        "offline_disconnect_verified":False,"phone_clock_action_verified":False,"permissions_changed":False,"results":results}
    if native_sha:report.update(native_sha256=native_sha,native_identity_scope="Packaged library in local APK matching actual installed APK SHA256")
    def save():
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+"\n")
    try:
        lab.top();lab.tap("Ask Mira");lab.tap("Load verified local model")
        for _ in range(16):
            if any(n.get("text","").startswith("LOCAL MODEL LOADED") for n in lab.nodes()):break
            time.sleep(.25)
        else:raise RuntimeError("Model did not load")
        for command,intent,active in [("Please start a focus session","start_focus","true"),("Stop focus","pause_focus","false")]:
            result=lab.run(command)
            if result["intent"]!=intent or result["gate"]!="REVIEW REQUIRED":raise RuntimeError("Model or independent gate did not propose expected focus action; no confirmation")
            lab.tap("Review proposed phone action");lab.tap("Confirm action",scroll=False);time.sleep(.15)
            current=focus_state(lab)
            if current["activeCheckpoint"]!=active or current["observe"]!="false" or current["points"]!=initial["points"]:raise RuntimeError("Focus postcondition or observation/virtual-points invariant failed")
            result.update(action_executed=True,repository_focus_active_verified=active=="true",background_observation_enabled=False)
            results.append(result);save();print(json.dumps(result),flush=True)
        result=lab.run("Cancel my alarm at 7:30");results.append(result);save();print(json.dumps(result),flush=True)
        if result["gate"]!="ABSTAIN":raise RuntimeError("Cancellation did not abstain; no action was confirmed")
        report["completed"]=True
    finally:
        # Return only to our app, then use its persistent Stop control if cleanup is needed.
        lab.adb("shell","am","start","-n",PACKAGE+"/.MainActivity","-f","0x04000000");lab.guard()
        if focus_state(lab)["activeCheckpoint"]=="true":lab.tap("Stop focus",scroll=False)
        report["final_focus_paused"]=focus_state(lab)["activeCheckpoint"]=="false";save()

if __name__=="__main__":main()
