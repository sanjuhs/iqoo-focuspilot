#!/usr/bin/env python3
"""Render the editable pre-event pitch with local speech, original diagrams and captions.

Requires Pillow, macOS say/qlmanage, ffmpeg and ffprobe. No network/API/phone access.
Narration source: docs/research-pitch-script.md. Outputs stay under ignored artifacts/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
ASSETS = OUT / "pitch-assets"
W, H = 1920, 1080
BG, SURFACE, LILAC, TEAL, INK, MUTED, GOLD = "#17151F", "#292536", "#C9B7EA", "#79DBC8", "#F4EFFA", "#B7AEC5", "#EDCD94"
FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FONT = FONT_DIR / "Arial.ttf"
BOLD = FONT_DIR / "Arial Bold.ttf"


def run(args, **kwargs):
    subprocess.run([str(value) for value in args], check=True, **kwargs)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], text=True).strip())


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def wrapped(draw, xy, value, size=38, color=INK, width=900, bold=False, spacing=12):
    words, rows, line = value.split(), [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if line and draw.textlength(candidate, font=font(size, bold)) > width:
            rows.append(line); line = word
        else:
            line = candidate
    if line:
        rows.append(line)
    draw.multiline_text(xy, "\n".join(rows), font=font(size, bold), fill=color, spacing=spacing)
    return len(rows) * (size + spacing)


def panel(draw, box, fill=SURFACE, outline=None):
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=3)


def label(draw, xy, value, size=32, fill=INK, bold=False):
    draw.text(xy, value, font=font(size, bold), fill=fill)


def arrow(draw, start, end, color=TEAL, width=6, dashed=False):
    x, y = start; xx, yy = end
    if dashed:
        steps = max(2, int(math.hypot(xx-x, yy-y) / 28))
        for i in range(0, steps, 2):
            a, b = i / steps, min(1, (i+1) / steps)
            draw.line((x+(xx-x)*a, y+(yy-y)*a, x+(xx-x)*b, y+(yy-y)*b), fill=color, width=width)
    else:
        draw.line((start, end), fill=color, width=width)
    angle = math.atan2(yy-y, xx-x)
    points = [(xx, yy), (xx-22*math.cos(angle-.45), yy-22*math.sin(angle-.45)), (xx-22*math.cos(angle+.45), yy-22*math.sin(angle+.45))]
    draw.polygon(points, fill=color)


def process(draw, nodes, phase, y=410, pending=False):
    width = 1560 / len(nodes)
    for i, value in enumerate(nodes):
        x = 160 + i * width
        active = i <= phase if len(nodes) <= 3 else i <= phase+1
        panel(draw, (x, y, x+width-45, y+160), outline=TEAL if active else "#494255")
        wrapped(draw, (x+24, y+35), value, 34, TEAL if active else MUTED, width-90, True)
        if i < len(nodes)-1:
            arrow(draw, (x+width-38, y+80), (x+width-5, y+80), TEAL if active else "#494255", dashed=pending)


def avatar_asset():
    source = ROOT / "prototype/companion/avatar.svg"
    target = ASSETS / "avatar.svg.png"
    if not target.exists():
        run(["qlmanage", "-t", "-s", "900", "-o", ASSETS, source], stdout=subprocess.DEVNULL)
    image = Image.open(target).convert("RGBA")
    # Quick Look rasterizes onto pure white; original vector uses off-white eyes.
    pixels = [(r,g,b,0 if min(r,g,b)>250 else a) for r,g,b,a in image.getdata()]
    image.putdata(pixels)
    image.save(ASSETS / "pitch-avatar-cutout.png")
    return image


RUBRIC = {2: "PRODUCT QUALITY · 30%", 4: "NOVELTY + IMPACT · 20%", 5: "CREATIVE PHONE USE · 15%", 6: "TECHNICAL DEPTH · 15%", 9: "OFFICE KIT · 10%", 11: "DEMO + PRESENTATION · 10%"}


def frame(scene, phase, avatar, phone):
    index = scene["index"]
    image = Image.new("RGB", (W,H), BG)
    draw = ImageDraw.Draw(image)
    label(draw, (110,48), "MIRA / FOCUSPILOT", 24, TEAL, True)
    label(draw, (110,92), "PRE-EVENT CONCEPT / RESEARCH", 21, GOLD, True)
    if index in RUBRIC:
        label(draw, (1220,52), RUBRIC[index], 23, LILAC, True)
    wrapped(draw, (110,155), scene["title"], 64, INK, 1630, True, 9)
    if index in (0,13):
        art = avatar.copy(); art.thumbnail((630,630))
        image.paste(art, (1210,225), art)
        if index == 0:
            wrapped(draw,(120,365),"A quiet local productivity companion",62,INK,1000,True)
            lines = ["Your goal. Your chosen limits.", "Small approved actions.", "Room to pause and take a break."]
        else:
            wrapped(draw,(120,350),"Make room for what matters.",65,INK,1050,True)
            lines = ["Local where verified.", "Understandable decisions.", "User control at every step."]
        for i,value in enumerate(lines[:phase+1]): label(draw,(125,600+i*70),value,36,TEAL)
    elif index == 1:
        process(draw,["A useful task", "A short detour", "Return by choice"],phase)
        label(draw,(165,650),["Start with the user's intention.","A break is not automatically a failure.","A gentle prompt, not forced control."][phase],42,LILAC,True)
        label(draw,(165,750),"Illustrated workflow · no measured distraction-reduction claim",24,MUTED)
    elif index == 2:
        if phone:
            capture=Image.open(phone).convert("RGB"); capture=capture.crop((0,126,capture.width,min(2292,capture.height)))
            capture.thumbnail((430,665))
            panel(draw,(1350,160,1840,855),outline="#5E516F")
            image.paste(capture,(1380+(430-capture.width)//2,175))
        points=[("Choose","Set your own app budget."),("Focus","Start a session and see its state."),("Pause","Mute, hide, reduce motion, or stop.")]
        for i,(heading,body) in enumerate(points[:phase+1]):
            label(draw,(145,355+i*140),heading,48,TEAL,True); label(draw,(145,417+i*140),body,34,INK)
        label(draw,(1370,875),"Research UI still · app content",22,MUTED)
    elif index == 3:
        process(draw,["Your request","Local proposal","Independent review","Android action"],phase,y=420)
        label(draw,(160,655),["Model output is a proposal.","Review and validate before execution.","Clock completion remains unverified."][phase],40,LILAC,True)
    elif index == 4:
        panel(draw,(130,350,1000,515),outline=LILAC); label(draw,(165,380),"LANGUAGE LANE",24,LILAC,True); label(draw,(165,429),"New request → local model",43,INK,True)
        if phase>=1:
            panel(draw,(130,560,1000,725),outline=TEAL); label(draw,(165,590),"FAST LANE",24,TEAL,True); label(draw,(165,639),"Recurring decision → small policy",39,INK,True)
        arrow(draw,(1030,445),(1190,525),LILAC)
        if phase>=1: arrow(draw,(1030,640),(1190,555))
        panel(draw,(1215,410,1790,660),outline=TEAL); wrapped(draw,(1260,460),"Bounded user-approved actions",48,INK,480,True)
        if phase>=2: label(draw,(150,805),"Hand-set recurring policy · cooldown · virtual points only",30,GOLD)
    elif index == 5:
        values=[("Cold",13.521),("Warm",1.646),("Warm + capture",1.719)]
        for i,(name,value) in enumerate(values[:phase+1]):
            y=350+i*130; label(draw,(145,y),name,33,INK,True)
            draw.rounded_rectangle((460,y,460+value/14*960,y+58),radius=16,fill=LILAC if i==0 else TEAL)
            label(draw,(1470,y),f"{value:.3f}s",42,INK,True)
        label(draw,(145,770),"Five-case CPU smoke · one observation per condition · not p50/p95",28,GOLD,True)
        if phase>=2: label(draw,(145,825),"2 wrong negated/compound model outputs → gate ABSTAIN → no action",27,TEAL)
        label(draw,(145,863),"Earlier generic CPU baseline: 19.853s / 4.107s (2 observations)",20,MUTED)
    elif index == 6:
        process(draw,["Phone tensors","Actual summaries","Observation, not causation"],phase,y=355)
        if phase>=1:
            panel(draw,(170,585,930,760),outline=LILAC); label(draw,(205,615),"LAPTOP INTERVENTION STUDY",26,LILAC,True); label(draw,(205,665),"108 trials · 16 identical controls",34,INK,True)
        if phase>=2:
            panel(draw,(1000,585,1780,760),outline=GOLD); wrapped(draw,(1035,625),"No reliable selected-channel steering advantage",39,GOLD,690,True)
        label(draw,(170,820),"Negative semantic result ≠ failed measurement machinery",29,MUTED)
    elif index == 7:
        xs=[245,660,1100]; ys=[[370+i*63 for i in range(6)],[323+i*55 for i in range(8)],[515]]
        for layer in range(2):
            for a in ys[layer]:
                for b in ys[layer+1]: draw.line((xs[layer]+17,a,xs[layer+1]-17,b),fill="#4C435F",width=2)
        for layer in range(3):
            for y in ys[layer]: draw.ellipse((xs[layer]-19,y-19,xs[layer]+19,y+19),fill=TEAL if layer<=phase else "#4C435F")
        label(draw,(175,785),"6 features → 8 hidden units → 1 output",29,MUTED)
        label(draw,(1310,370),"65",116,LILAC,True); label(draw,(1318,510),"parameters",32,INK)
        if phase>=1: label(draw,(1260,620),"98.33%",73,TEAL,True)
        if phase>=2: wrapped(draw,(1265,720),"Synthetic holdout only. Not real-world productivity accuracy.",31,GOLD,530,True)
    elif index == 8:
        process(draw,["Explicit opt-in","Usage access","Visible notification"],phase,y=385)
        panel(draw,(615,650,1305,760),fill="#4A3457",outline=LILAC); label(draw,(815,680),"STOP FOCUS",46,INK,True)
        label(draw,(165,800),"Permission/device tests pending · OEM power rules can interrupt",29,GOLD,True)
        label(draw,(165,860),"No open microphone · no screen capture · no 24/7 guarantee",28,MUTED)
    elif index == 9:
        panel(draw,(185,340,670,730),outline=TEAL); label(draw,(250,385),"PHONE",48,TEAL,True); wrapped(draw,(240,480),"Nothing: CPU research verified",34,INK,375); wrapped(draw,(240,600),"iQOO: event demo target",32,GOLD,375)
        panel(draw,(1270,340,1755,730),outline=LILAC); label(draw,(1330,385),"LAPTOP",48,LILAC,True); wrapped(draw,(1325,480),"Deeper compute",34,INK,390); wrapped(draw,(1325,590),"Office Kit target",32,GOLD,390)
        arrow(draw,(710,500),(1230,500),MUTED,dashed=True)
        label(draw,(800,420),"OFFICE KIT",30,GOLD,True); label(draw,(805,535),"PENDING",30,GOLD,True)
        if phase>=2: label(draw,(230,815),"Snapdragon NPU: pending · USB debugging is a separate bridge",31,GOLD)
    elif index == 10:
        process(draw,["32 local labels","Neighbor retrieval","720 grouped cases"],phase,y=355)
        if phase>=1:
            label(draw,(210,615),"Answered accuracy improved",46,TEAL,True)
            label(draw,(210,685),"~70% coverage · more abstention",42,LILAC,True)
        if phase>=2:
            label(draw,(210,765),"Fewer overall correct cases. Report the tradeoff.",35,GOLD,True)
            label(draw,(210,835),"8 tests · phone label UI tested · live policy integration pending",26,MUTED)
    elif index == 11:
        groups=[("Works + matters","Product quality 30%\nNovelty + impact 20%",TEAL),("Uses the hardware","Creative phone use 15%\nTechnical depth 15%\nOffice Kit 10%",LILAC),("Shows the story","Demo + presentation 10%",GOLD)]
        for i,(heading,body,color) in enumerate(groups[:phase+1]):
            x=145+i*570; panel(draw,(x,360,x+520,775),outline=color)
            wrapped(draw,(x+32,400),heading,45,color,440,True)
            draw.multiline_text((x+32,555),body,font=font(30),fill=INK,spacing=24)
        label(draw,(150,840),"Primary track: Productivity · sourced from the published guide",30,MUTED)
    elif index == 12:
        panel(draw,(150,380,870,660),outline=TEAL); label(draw,(195,425),"2 OCTOBER 2026",34,TEAL,True); wrapped(draw,(195,500),"Research + preparation",50,INK,625,True)
        arrow(draw,(925,525),(1050,525),GOLD,dashed=True)
        if phase>=1:
            panel(draw,(1110,380,1790,660),outline=GOLD); label(draw,(1150,425),"9–11 OCTOBER 2026",32,GOLD,True); wrapped(draw,(1150,500),"Eligible event window",48,INK,590,True)
        if phase>=2: label(draw,(175,780),"Do not present pre-built research code as event-written work.",35,GOLD,True)
        label(draw,(175,855),"Public rules: iqoo.reskilll.com/guide + /terms",26,MUTED)
    draw.rectangle((0,930,W,H),fill="#100E16")
    draw.line((110,927,1810,927),fill="#50445F",width=2)
    label(draw,(110,902),f"RESEARCH SNAPSHOT · 2 OCT 2026 · {index+1:02d}/14",18,MUTED)
    return image


def parse_source(path):
    source=path.read_text()
    sections=re.split(r"^## Scene (\d+): (.+)$",source,flags=re.MULTILINE)
    scenes=[]
    for i in range(1,len(sections),3):
        body=sections[i+2]
        utterances=re.findall(r"^> (.+)$",body,flags=re.MULTILINE)
        if not utterances: raise ValueError("Scene has no narration")
        scenes.append({"index":int(sections[i])-1,"title":sections[i+1],"utterances":utterances,"visual_intent":re.search(r"^Visual: (.+)$",body,re.MULTILINE).group(1)})
    if len(scenes)!=14: raise ValueError("Expected the fourteen editable storyboard scenes")
    return scenes


def timestamp(seconds, ass=False):
    total=round(seconds*(100 if ass else 1000))
    unit=100 if ass else 1000; h=total//(3600*unit); m=(total//(60*unit))%60; s=(total//unit)%60; sub=total%unit
    return f"{h}:{m:02}:{s:02}.{sub:02}" if ass else f"{h:02}:{m:02}:{s:02},{sub:03}"


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voice",default="Samantha"); parser.add_argument("--rate",type=int,default=190)
    parser.add_argument("--fps",type=int,default=24); parser.add_argument("--phone-still",type=Path,default=ROOT/"artifacts/mira-home-v2.png")
    args=parser.parse_args()
    for tool in ("say","ffmpeg","ffprobe","qlmanage"):
        if not shutil.which(tool): raise RuntimeError(f"Install required local tool: {tool}")
    ASSETS.mkdir(parents=True,exist_ok=True)
    source=ROOT/"docs/research-pitch-script.md"; scenes=parse_source(source)
    avatar=avatar_asset(); phone=args.phone_still if args.phone_still.exists() else None
    silence=ASSETS/"gap.aiff"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","0.28","-c:a","pcm_s16be",silence])
    gap=duration(silence); clock=0; captions=[]; audio_files=[]; video_lines=[]; serial=0
    for scene in scenes:
        scene["start"]=clock
        for phase,utterance in enumerate(scene["utterances"]):
            serial+=1; name=f"{serial:02d}"; text_file=ASSETS/f"speech-{name}.txt"; audio=ASSETS/f"speech-{name}.aiff"
            text_file.write_text(utterance)
            # Always regenerate audio so edits/rate/voice cannot silently reuse stale narration.
            run(["say","-v",args.voice,"-r",args.rate,"-o",audio,"-f",text_file])
            length=duration(audio)
            photo=ASSETS/f"frame-{name}.png"; frame(scene,phase,avatar,phone).save(photo)
            captions.append({"start":clock,"end":clock+length,"text":utterance,"scene":scene["index"]+1})
            audio_files.extend([audio,silence]); video_lines.extend([f"file '{photo.as_posix()}'",f"duration {length+gap:.6f}"])
            clock+=length+gap
        scene["duration"]=clock-scene["start"]
        print(f"Scene {scene['index']+1:02d}: {scene['duration']:.1f}s",flush=True)
    if not 180<=clock<=300:
        raise RuntimeError(f"Narration duration {clock:.1f}s is outside 3–5 minutes. Adjust editable narration or --rate before export.")
    audio_list=ASSETS/"audio-list.txt"; audio_list.write_text("\n".join(f"file '{file.as_posix()}'" for file in audio_files)+"\n")
    narration=OUT/"pitch-research.wav"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",audio_list,"-ac","2","-ar","48000","-c:a","pcm_s16le",narration])
    srt=OUT/"pitch-research.srt"; ass=OUT/"pitch-research.ass"
    srt.write_text("\n\n".join(f"{i}\n{timestamp(item['start'])} --> {timestamp(item['end'])}\n"+"\n".join(textwrap.wrap(item['text'],width=88)) for i,item in enumerate(captions,1))+"\n")
    header="[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,36,&H00FAF0F4,&H00FAF0F4,&H00160E10,&H00160E10,0,0,0,0,100,100,0,0,1,0,0,2,110,110,35,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    lines=[]
    for item in captions:
        text="\\N".join(textwrap.wrap(item["text"].replace("{","(").replace("}",")"),width=88))
        lines.append(f"Dialogue: 0,{timestamp(item['start'],True)},{timestamp(item['end'],True)},Default,,0,0,0,,{text}")
    ass.write_text(header+"\n".join(lines)+"\n")
    video_list=ASSETS/"video-list.txt"; video_list.write_text("\n".join(video_lines)+f"\nfile '{photo.as_posix()}'\n")
    video=OUT/"pitch-research.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","warning","-y","-f","concat","-safe","0","-i",video_list,"-i",narration,"-vf",f"fps={args.fps},ass={ass.as_posix()}","-t",f"{clock:.6f}","-c:v","libx264","-preset","veryfast","-crf","21","-threads","2","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",video])
    measured=duration(video)
    manifest={"title":"Mira / FocusPilot: a quiet local productivity companion","label":"PRE-EVENT CONCEPT / RESEARCH","retrieval_date":"2026-10-02 IST","duration_seconds":measured,"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"renderer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"video_sha256":hashlib.sha256(video.read_bytes()).hexdigest(),"captions_sha256":hashlib.sha256(srt.read_bytes()).hexdigest(),"voice":args.voice,"words_per_minute":args.rate,"caption_segments":len(captions),"scenes":scenes,"phone_still":str(phone) if phone else None,"phone_still_note":"Inspected research UI still with system bars cropped; not a live recording","phone_crop_pixels":[0,126,1080,2292],"avatar_source":"prototype/companion/avatar.svg","claims":{"phone_baseline_ms":[19853,4107],"optimized_phone_smoke_ms":{"cold":13521,"warm":1646,"capture":1719,"negated":1724,"compound":1663},"optimized_model_failures_rejected_by_gate":2,"optimized_actions_executed":0,"npu_verified":False,"office_kit_verified":False,"background_permission_device_test":"pending","fewshot":"32-label research sandbox; 720 grouped synthetic comparison, higher answered accuracy, roughly 70% coverage, lower overall correct count from abstention; phone label UI tested, live policy integration pending","causal_laptop_trials":108,"causal_restoration_controls":16,"causal_result":"No reliable selected-channel steering advantage","trained_policy_parameters":65,"trained_policy_synthetic_holdout_accuracy":0.9833333333333333,"recurring_policy":"hand-set baseline"}}
    (OUT/"pitch-render-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"Rendered {video} · {measured:.1f}s · {video.stat().st_size/1e6:.1f}MB",flush=True)


if __name__=="__main__":
    main()
