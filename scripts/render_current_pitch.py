#!/usr/bin/env python3
"""Deterministic current research pitch. Local speech; no API, network or phone.

Streams frames to FFmpeg rather than retaining thousands of PNGs. Historical
pitch assets are never overwritten. Illustrations are distinct from phone proof.
"""
from __future__ import annotations
import argparse, functools, hashlib, importlib.util, json, math, re, shutil, subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/current-pitch'; W,H=1920,1080
BG='#17151F'; SURFACE='#292536'; INK='#F4EFFA'; MUTED='#B7AEC5'
TEAL='#79DBC8'; LILAC='#C9B7EA'; GOLD='#EDCD94'; RED='#EB9BBD'
SOURCE=ROOT/'docs/current-research-pitch-script.md'
METRICS=ROOT/'prototype/current-pitch/metrics.json'
POLICY=ROOT/'prototype/policy/synthetic-model.json'

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(args,**kwargs):return subprocess.run(list(map(str,args)),check=True,**kwargs)
def duration(path):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True))
def clamp(x):return max(0.,min(1.,x))
def ease(x):return 1-(1-clamp(x))**3
@functools.lru_cache(maxsize=128)
def font(size,bold=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',size)
def text(d,xy,value,size=32,color=INK,bold=False):d.text(xy,str(value),font=font(size,bold),fill=color)
def lines(d,xy,value,size=36,color=INK,width=900,bold=False):
 words=value.split(); rows=[]; line=''
 for word in words:
  candidate=(line+' '+word).strip()
  if line and d.textlength(candidate,font=font(size,bold))>width:rows.append(line);line=word
  else:line=candidate
 if line:rows.append(line)
 d.multiline_text(xy,'\n'.join(rows),font=font(size,bold),fill=color,spacing=12)
 return len(rows)*(size+12)
def box(d,rect,outline=TEAL,fill=SURFACE,radius=22):d.rounded_rectangle(rect,radius=radius,fill=fill,outline=outline,width=3)
def path(d,a,b,p=1.,color=TEAL,width=6,dashed=False):
 x,y=a;xx,yy=b;end=(x+(xx-x)*clamp(p),y+(yy-y)*clamp(p))
 if dashed:
  n=max(2,int(math.hypot(end[0]-x,end[1]-y)/22))
  for i in range(0,n,2):d.line((x+(end[0]-x)*i/n,y+(end[1]-y)*i/n,x+(end[0]-x)*min(i+1,n)/n,y+(end[1]-y)*min(i+1,n)/n),fill=color,width=width)
 else:d.line((a,end),fill=color,width=width)
 if p>=.98:
  ang=math.atan2(yy-y,xx-x);d.polygon([end,(xx-18*math.cos(ang-.5),yy-18*math.sin(ang-.5)),(xx-18*math.cos(ang+.5),yy-18*math.sin(ang+.5))],fill=color)
def dot(d,xy,r=13,color=TEAL):x,y=xy;d.ellipse((x-r,y-r,x+r,y+r),fill=color)

def mira(d,x,y,scale,t):
 """Original procedural adult portrait, adapted from project's vector vocabulary."""
 def rect(a,b,c,e):return (x+a*scale,y+b*scale,x+c*scale,y+e*scale)
 bob=math.sin(t*1.5)*2; y+=bob
 d.ellipse(rect(35,18,205,250),fill='#242330')
 d.rounded_rectangle(rect(28,224,212,318),radius=int(30*scale),fill='#363145',outline=LILAC,width=max(1,int(scale)))
 d.rectangle(rect(90,203,150,318),fill='#1B1D28')
 d.rounded_rectangle(rect(99,190,141,227),radius=int(12*scale),fill='#E6B9B7')
 d.ellipse(rect(67,57,173,209),fill='#EDC5BF')
 d.ellipse(rect(76,148,96,155),fill='#D69CA9');d.ellipse(rect(144,148,164,155),fill='#D69CA9')
 for a in (67,173):d.ellipse(rect(a-5,149,a+5,159),outline=TEAL,width=max(1,int(2*scale)))
 blink=(t%5.2)<.15
 for a in (94,146):
  if blink:d.line((x+(a-12)*scale,y+130*scale,x+(a+12)*scale,y+130*scale),fill='#292330',width=max(1,int(3*scale)))
  else:
   d.ellipse(rect(a-13,123,a+13,140),fill='#FAF3F1');d.ellipse(rect(a-5,124,a+5,139),fill='#668A84');d.ellipse(rect(a-2,125,a+2,138),fill='#282833')
   d.line((x+(a-13)*scale,y+128*scale,x+(a+12)*scale,y+126*scale),fill='#292330',width=max(1,int(2*scale)))
 d.arc(rect(106,163,135,183),10,168,fill='#5C384F',width=max(1,int(3*scale)))
 d.polygon([(x+a*scale,y+b*scale) for a,b in [(63,127),(62,88),(77,51),(113,35),(152,43),(179,78),(178,119),(151,91),(139,77),(131,109),(113,89),(103,112),(86,94),(77,122)]],fill='#242330')
 d.polygon([(x+a*scale,y+b*scale) for a,b in [(129,47),(145,54),(157,106),(142,87),(134,101),(127,96),(131,72)]],fill='#B8A0DD')
 d.arc(rect(56,267,75,287),55,315,fill=LILAC,width=max(1,int(4*scale)))
 d.line((x+98*scale,y+216*scale,x+142*scale,y+216*scale),fill='#303040',width=max(1,int(8*scale)))
 dot(d,(x+120*scale,y+220*scale),3*scale,LILAC)

def parse_source():
 chunks=re.split(r'^## Scene (\d+): (.+)$',SOURCE.read_text(),flags=re.M);scenes=[]
 for i in range(1,len(chunks),3):
  narration=re.findall(r'^> (.+)$',chunks[i+2],flags=re.M)
  if len(narration)!=3:raise ValueError('Each shot needs three measured narration beats')
  scenes.append({'index':int(chunks[i])-1,'title':chunks[i+1],'utterances':narration,'visual_intent':re.search(r'^Visual: (.+)$',chunks[i+2],re.M).group(1)})
 if len(scenes)!=10 or [s['index'] for s in scenes]!=list(range(10)):raise ValueError('Expected ten ordered shots')
 return scenes

def trace_policy():
 p=ROOT/'prototype/policy/policy.py';checkpoint=json.loads(POLICY.read_text());metrics=json.loads(METRICS.read_text())
 if sha(POLICY)!=metrics['policy']['checkpoint_sha256'] or sha(p)!=checkpoint['implementation_sha256']:raise RuntimeError('Executable policy/checkpoint changed; use the pinned source snapshot')
 spec=importlib.util.spec_from_file_location('pitch_policy',p);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 # This invented [0,1] example is not phone data or a calibrated human score.
 return module.PositiveNetwork(checkpoint['parameters']).inspect([.8,.3,.2,.7,.1,.2])

def shot(scene,t,metrics,trace):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im);local=t-scene['start'];phase=max(i for i,b in enumerate(scene['beats']) if t>=b['start']);beat=scene['beats'][phase];q=ease((t-beat['start'])/2.2);i=scene['index']
 text(d,(78,36),'MIRA / FOCUSPILOT',25,TEAL,True);text(d,(1310,40),'PRE-EVENT / RESEARCH',24,GOLD,True)
 text(d,(80,96),scene['title'],44,INK,True)
 text(d,(80,163),'Illustration · '+f'{i+1:02}/10',21,MUTED)
 if i==0:
  mira(d,1240,218,1.8,local)
  box(d,(140,300,720,605),LILAC);text(d,(185,343),'YOUR CHOSEN TASK',25,LILAC,True);lines(d,(185,409),'Make room for what matters.',55,INK,490,True)
  path(d,(760,450),(1100,450),q if phase==0 else 1.,TEAL)
  if phase>=1:
   d.arc((770,480,1120,755),0,180,fill=LILAC,width=8);dot(d,(945+140*math.sin(q*math.pi),520+110*math.sin(q*math.pi)),15,LILAC)
   text(d,(760,758),'A detour can return by choice.',29,TEAL)
  if phase>=2:text(d,(145,710),'Your goal. Your limits. Your control.',39,TEAL,True)
 elif i==1:
  box(d,(100,230,625,535),LILAC);text(d,(145,275),'Study one chapter',48,INK,True);text(d,(145,359),'Goal chosen by you',30,MUTED)
  d.ellipse((785,250,1165,630),outline=TEAL,width=10);d.arc((785,250,1165,630),-90,-90+280*(q if phase==0 else 1),fill=LILAC,width=20);text(d,(868,378),'FOCUS',42,TEAL,True);text(d,(879,442),'25 min',35,INK)
  if phase>=1:
   box(d,(1310,260,1810,620),GOLD);text(d,(1350,305),'Chosen app budget',31,GOLD,True);path(d,(1360,435),(1740,435),q,GOLD,16);text(d,(1350,505),'Offer one gentle nudge',32,INK)
  if phase>=2:
   box(d,(375,681,1465,789),TEAL);text(d,(422,710),'Allow / return / pause — the choice remains yours',36,TEAL,True)
  text(d,(105,590),'Virtual balance: 100 points',32,GOLD,True);text(d,(105,642),'No real debit',30,MUTED);text(d,(935,817),'Intended workflow · physical monitor proof pending',24,GOLD)
 elif i==2:
  nodes=[(110,'Your request'),(560,'Qwen proposal'),(1010,'Whole-request gate'),(1460,'Your review')]
  for x,name in nodes:box(d,(x,320,x+350,485),LILAC if x==560 else TEAL);lines(d,(x+25,361),name,35,INK,300,True)
  for n in range(3):
   progress=(q if n==0 else 0) if phase==0 else (1 if n==0 else q) if phase==1 else (1 if n<2 else 0)
   if progress>0:path(d,(nodes[n][0]+350,405),(nodes[n+1][0],405),progress,TEAL)
  if phase<2:
   box(d,(305,595,1560,718),TEAL);text(d,(340,626),'Illustrated supported command → validate → confirm',37,TEAL,True)
  else:
   box(d,(265,578,1130,758),RED);text(d,(300,603),'“Cancel my alarm” → wrong alarm proposal',34,INK,True);text(d,(300,672),'ABSTAIN: creation was never requested',37,RED,True)
   path(d,(1180,672),(1405,672),q,RED);d.line((1425,620,1425,726),fill=RED,width=13);text(d,(1480,653),'NO ACTION',35,RED,True)
   text(d,(280,803),'Historical v0.6 cancellation branch · CPU / typed',24,MUTED)
 elif i==3:
  text(d,(110,224),'HISTORICAL v0.6',29,LILAC,True);text(d,(1110,224),'CURRENT v0.10',29,TEAL,True)
  for n,(name,value,state) in enumerate([('Start',metrics['historical_phone']['start_ms'],'active'),('Pause',metrics['historical_phone']['pause_ms'],'paused')]):
   y=307+n*215;text(d,(110,y),f'{name}: {value/1000:.3f}s',42,INK,True);path(d,(115,y+85),(115+value/17323*745,y+85),q if phase==n else 1.,LILAC,20)
   if phase>=n:text(d,(115,y+130),'Own checkpoint → '+state,29,LILAC)
  box(d,(1085,298,1810,704),TEAL);text(d,(1130,341),'Signed package installed',43,INK,True);text(d,(1130,421),'133 JVM tests pass',40,TEAL,True);text(d,(1130,500),'APK + retained model hashes match',28,MUTED)
  if phase>=2:lines(d,(1130,572),'Phone asleep. Current actions untested.',37,GOLD,610,True)
  text(d,(115,808),'Single typed observations · not ASR, averages or current phone latency',26,GOLD)
 elif i==4:
  c=metrics['commands'];text(d,(120,237),'Correct supported proposals / 50',33,INK,True)
  for row,(name,count,col) in enumerate([('Previous gate',c['baseline'],LILAC),('Selected gate',c['selected'],TEAL)]):
   y=315+row*190;text(d,(120,y),name,33,col,True)
   shown=count*(q if phase==row else 1 if phase>row else 0)
   for n in range(50):
    x=495+(n%25)*43;yy=y+(n//25)*43
    d.ellipse((x,yy,x+23,yy+23),fill=col if n<shown else BG,outline=col,width=2)
   text(d,(1650,y),f'{count}/50',51,col,True)
  if phase>=1:text(d,(500,676),'16 gains · 0 losses · 19 still abstain',39,GOLD,True)
  if phase>=2:
   text(d,(120,766),'50/50 unsupported rejected · 0 wrong accepts observed',32,TEAL,True)
   text(d,(120,814),'Raw model: 36/100 correct; 49 unsupported tool proposals',28,GOLD)
  text(d,(120,864),'Fresh synthetic wording · same informed author · no phone actions',21,MUTED)
 elif i==5:
  box(d,(110,270,645,555),LILAC);text(d,(150,315),'Qwen3.5-0.8B',48,LILAC,True);text(d,(150,398),'Q4_0 · original prompt',33,INK);text(d,(150,474),'Weights unchanged',31,MUTED)
  path(d,(660,398),(1005,398),q if phase==0 else 1.,TEAL);box(d,(1030,290,1760,535),TEAL);text(d,(1070,340),'Expanded request gate',46,TEAL,True);text(d,(1070,424),'Listed polite wrappers + exact slots',31,INK)
  if phase>=1:
   path(d,(700,535),(975,695),q,RED);box(d,(1000,621,1735,783),RED);text(d,(1040,651),'Longer prompt: rejected',41,RED,True);text(d,(1040,715),'Useful intent accuracy fell; host latency rose',28,MUTED)
  if phase>=2:text(d,(130,705),'CPU today',54,GOLD,True);text(d,(130,777),'NPU execution pending',32,GOLD)
 elif i==6:
  xs=[340,855,1270];ys=[[300+65*n for n in range(6)],[262+57*n for n in range(8)],[468]]
  chosen=max(trace['hidden_units'],key=lambda u:u['logit_contribution'])['unit']
  for a in range(6):
   for b in range(8):path(d,(xs[0]+14,ys[0][a]),(xs[1]-14,ys[1][b]),q if phase==0 else 1.,'#484054',2)
  for b in range(8):path(d,(xs[1]+15,ys[1][b]),(xs[2]-25,ys[2][0]),q if phase==1 else 1.,RED if phase==2 and b==chosen else TEAL,3)
  for layer in range(3):
   for n,y in enumerate(ys[layer]):dot(d,(xs[layer],y),19,RED if layer==1 and phase==2 and n==chosen else TEAL if layer<=phase else LILAC)
  for n,(name,value) in enumerate(trace['features'].items()):text(d,(110,ys[0][n]-15),f'x{n}: {value:.1f}',28,MUTED)
  text(d,(190,740),'6 inputs → 8 ReLU units → 1 sigmoid',29,MUTED)
  text(d,(1415,270),'65',105,LILAC,True);text(d,(1415,390),'parameters',31,INK)
  value=trace['probability'] if phase<2 else trace['hidden_units'][chosen]['probability_if_suppressed']
  text(d,(1385,496),f'Toy score: {value:.3f}',34,TEAL,True)
  if phase>=1:
   z=trace['logit']-(trace['hidden_units'][chosen]['logit_contribution'] if phase==2 else 0)
   lines(d,(1385,570),f"Bias + contributions\nlogit = {z:.3f}",29,INK,420)
  if phase==2:text(d,(1385,677),f'Unit {chosen} suppressed',30,RED,True)
  text(d,(140,802),'Nonnegative connections · signed biases · synthetic example',28,GOLD,True)
  text(d,(140,850),'98.33% synthetic holdout · shadow only · recurring policy hand-set',23,MUTED)
 elif i==7:
  box(d,(110,242,565,462),GOLD);text(d,(155,285),'User permissions',39,GOLD,True);text(d,(155,360),'Return starts nothing',29,INK)
  path(d,(585,351),(920,351),q if phase==0 else 1.,GOLD);box(d,(960,261,1410,451),TEAL);text(d,(1000,305),'Explicit reviewed Show',35,TEAL,True)
  if phase>=1:
   box(d,(1480,208,1810,748),LILAC);mira(d,1505,246,1.15,local);text(d,(1510,646),'OPEN / HIDE',26,TEAL,True);text(d,(1510,690),'PAUSE FOCUS',26,GOLD,True)
   text(d,(115,558),'Hide ≠ Pause focus',52,LILAC,True);text(d,(115,637),'No automatic restart or open microphone',31,MUTED)
  if phase>=2:
   d.rectangle((1484,213,1806,744),fill=BG);text(d,(1510,410),'SCREEN OFF',29,RED,True);text(d,(1510,468),'Window ends',27,MUTED)
   text(d,(115,738),'Implementation illustrated · physical tests pending',34,GOLD,True)
  text(d,(115,812),'Voice: push-to-talk → draft review → model → confirmation',27,MUTED)
 elif i==8:
  for n,(name,reason) in enumerate([('LoRA adapter','Rejected: semantic regression'),('Frozen-representation head','Unpromoted: action coverage fell')]):
   y=250+n*145;box(d,(110,y,965,y+116),RED);text(d,(145,y+20),name,36,INK,True);text(d,(145,y+71),reason,25,RED)
  if phase>=1:
   text(d,(1170,265),'108 trials',63,LILAC,True);text(d,(1170,365),'16 restoration controls',33,TEAL,True)
   for n in range(16):dot(d,(1190+(n%8)*68,468+(n//8)*55),15,TEAL)
   text(d,(1170,589),'Full logits restored identically',30,MUTED)
  if phase>=2:
   box(d,(165,666,1745,788),GOLD);text(d,(210,699),'No reliable selected-channel steering advantage',44,GOLD,True)
  text(d,(150,828),'Observation and negative results ≠ full-model causal understanding',28,MUTED)
 else:
  box(d,(110,250,555,560),TEAL);text(d,(150,295),'Bounded export',39,TEAL,True);text(d,(150,382),'Synthetic Java fixture',28,INK);text(d,(150,450),'User-selected summary',26,MUTED)
  path(d,(575,400),(950,400),q if phase==0 else 1.,TEAL);box(d,(980,250,1780,560),LILAC);text(d,(1020,298),'Laptop shadow review',47,LILAC,True);text(d,(1020,395),'15 tests · Java → Python interop',34,INK);text(d,(1020,472),'Local file is not Office Kit',30,GOLD)
  if phase>=1:
   path(d,(210,620),(1740,620),q,GOLD,6,True);text(d,(240,650),'iQOO hardware / NPU / Office Kit / live workflow: pending',35,GOLD,True)
  if phase>=2:
   text(d,(170,761),'2 October research',33,TEAL,True);text(d,(710,761),'→',42,MUTED);text(d,(830,761),'9–11 October event window',36,GOLD,True)
   text(d,(170,821),'Eligible source + dashboard requirements → accepted submission still ahead',27,MUTED)
 # Captions occupy a dedicated region and are burned by FFmpeg, not this drawing.
 d.rectangle((0,903,W,H),fill='#100E16');d.line((80,902,1840,902),fill='#50445F',width=2)
 return im

def frame(t,scenes,metrics,trace):
 scene=next((s for s in scenes if s['start']<=t<s['end']),scenes[-1]);image=shot(scene,t,metrics,trace)
 elapsed=t-scene['start']
 if scene['index']>0 and elapsed<.4:
  previous=scenes[scene['index']-1];old=shot(previous,previous['end']-1e-6,metrics,trace);image=Image.blend(old,image,clamp(elapsed/.4))
 return image

def timestamp(seconds,ass=False):
 scale=100 if ass else 1000;total=round(seconds*scale);h=total//(3600*scale);m=total//(60*scale)%60;s=total//scale%60;ms=total%scale
 return f'{h}:{m:02}:{s:02}.{ms:02}' if ass else f'{h:02}:{m:02}:{s:02},{ms:03}'

def prepare(voice,rate):
 OUT.mkdir(parents=True,exist_ok=True);audio_dir=OUT/'speech';audio_dir.mkdir(exist_ok=True);scenes=parse_source();captions=[];files=[];clock=0.
 gap=audio_dir/'gap.aiff';run(['ffmpeg','-v','error','-y','-f','lavfi','-i','anullsrc=r=22050:cl=mono','-t','0.30','-c:a','pcm_s16be',gap])
 for scene in scenes:
  scene['start']=clock;scene['beats']=[]
  for utterance in scene['utterances']:
   n=len(captions)+1;p=audio_dir/f'{n:02}.txt';a=audio_dir/f'{n:02}.aiff';p.write_text(utterance)
   run(['say','-v',voice,'-r',rate,'-o',a,'-f',p]);length=duration(a);c={'start':clock,'end':clock+length,'text':utterance,'scene':scene['index']+1};scene['beats'].append(c);captions.append(c);files.extend([a,gap]);clock+=length+duration(gap)
  scene['end']=clock;scene['duration']=clock-scene['start'];print(f"scene {scene['index']+1}: {scene['duration']:.2f}s",flush=True)
 if not 180<=clock<=300:raise ValueError(f'Measured {clock:.2f}s outside 3–5 minute pitch')
 concat=audio_dir/'concat.txt';concat.write_text('\n'.join(f"file '{p.as_posix()}'" for p in files)+'\n')
 run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',concat,'-ac','2','-ar','48000','-c:a','pcm_s16le',OUT/'narration.wav'])
 (OUT/'pitch-current.srt').write_text('\n\n'.join(f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n"+'\n'.join(textwrap.wrap(c['text'],width=92)) for i,c in enumerate(captions,1))+'\n')
 header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,34,&H00FAF0F4,&H00FAF0F4,&H00160E10,&H00160E10,0,0,0,0,100,100,0,0,1,0,0,2,110,110,34,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
 event=[]
 for c in captions:
  words='\\N'.join(textwrap.wrap(c['text'].replace('{','(').replace('}',')'),width=92));event.append(f"Dialogue: 0,{timestamp(c['start'],True)},{timestamp(c['end'],True)},Default,,0,0,0,,{words}")
 (OUT/'pitch-current.ass').write_text(header+'\n'.join(event)+'\n');(OUT/'timeline.json').write_text(json.dumps({'scenes':scenes,'captions':captions,'seconds':clock},indent=2)+'\n')
 prepared={'source_sha256':sha(SOURCE),'voice':voice,'rate':rate,'files_sha256':{name:sha(OUT/name) for name in ('timeline.json','narration.wav','pitch-current.srt','pitch-current.ass')}}
 (OUT/'prepared-audio.json').write_text(json.dumps(prepared,indent=2)+'\n')
 return scenes,captions,clock

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--voice',default='Samantha');p.add_argument('--rate',type=int,default=185);p.add_argument('--prepare-only',action='store_true');p.add_argument('--reuse-timeline',action='store_true');args=p.parse_args()
 for tool in ('say','ffmpeg','ffprobe'):
  if not shutil.which(tool):raise RuntimeError(f'Required local tool unavailable: {tool}')
 metrics=json.loads(METRICS.read_text())
 evidence_bindings={}
 for name,expected in metrics['sources'].items():
  p=Path(name)
  if p.is_absolute() or '..' in p.parts or p.parts[0] not in ('prototype','docs'):raise RuntimeError('Evidence path outside public project scope')
  current=(ROOT/p).is_file() and sha(ROOT/p)==expected['sha256']
  if not current:
   commit=expected['source_commit']
   if not re.fullmatch('[0-9a-f]{40}',commit):raise RuntimeError('Full evidence commit required')
   historical=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+name])
   if hashlib.sha256(historical).hexdigest()!=expected['sha256']:raise RuntimeError('Pinned evidence source changed: '+name)
  evidence_bindings[name]={'sha256':expected['sha256'],'current_file_matches':current,'recorded_commit':expected['source_commit'],'recorded_commit_used':not current}
 if args.reuse_timeline:
  prepared=json.loads((OUT/'prepared-audio.json').read_text())
  if prepared['source_sha256']!=sha(SOURCE) or prepared['voice']!=args.voice or prepared['rate']!=args.rate:raise RuntimeError('Source/voice/rate changed; regenerate measured narration')
  if any(sha(OUT/name)!=expected for name,expected in prepared['files_sha256'].items()):raise RuntimeError('Prepared audio/timing/captions changed; regenerate')
  tl=json.loads((OUT/'timeline.json').read_text());scenes,captions,clock=tl['scenes'],tl['captions'],tl['seconds']
 else:scenes,captions,clock=prepare(args.voice,args.rate)
 if args.prepare_only:return
 trace=trace_policy();(OUT/'policy-trace.json').write_text(json.dumps(trace,indent=2)+'\n');video=OUT/'pitch-current.mp4';fps=24
 process=subprocess.Popen(['ffmpeg','-v','warning','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','pipe:0','-i',str(OUT/'narration.wav'),'-vf','ass='+str(OUT/'pitch-current.ass'),'-t',f'{clock:.6f}','-c:v','libx264','-preset','veryfast','-crf','21','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
 try:
  for n in range(math.ceil(clock*fps)):
   process.stdin.write(frame(n/fps,scenes,metrics,trace).tobytes())
   if n%(fps*15)==0:print(f'encoded input {n/fps:.0f}/{clock:.0f}s',flush=True)
  process.stdin.close();code=process.wait()
  if code!=0:raise RuntimeError('FFmpeg failed')
 except BaseException:
  process.terminate();process.wait();raise
 prepared=json.loads((OUT/'prepared-audio.json').read_text())
 manifest={'kind':'current pre-event concept/research pitch; procedural illustration, not live recording or eligible event entry','app_source_commit':metrics['current_app']['source_commit'],'source_sha256':sha(SOURCE),'renderer_sha256':sha(Path(__file__)),'metrics_sha256':sha(METRICS),'evidence_bindings':evidence_bindings,'prepared_audio_sha256':sha(OUT/'prepared-audio.json'),'timeline_sha256':sha(OUT/'timeline.json'),'policy_source_sha256':sha(ROOT/'prototype/policy/policy.py'),'policy_checkpoint_sha256':sha(POLICY),'video_sha256':sha(video),'captions_sha256':sha(OUT/'pitch-current.srt'),'narration_sha256':sha(OUT/'narration.wav'),'seconds':duration(video),'resolution':[W,H],'fps':fps,'scenes':scenes,'caption_segments':len(captions),'voice':prepared['voice'],'words_per_minute':prepared['rate'],'artwork':'original procedural Mira in renderer; project vector vocabulary, not captured app window','phone_capture_used':False,'phone_actions_executed':0,'human_complete_audio_review':False}
 (OUT/'render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'video':str(video),'seconds':manifest['seconds'],'bytes':video.stat().st_size}),flush=True)

if __name__=='__main__':main()
