#!/usr/bin/env python3
"""Inspect completed v20 media, actual encoded frames and original clip parity.

No audio listening claim, phone activity or media rewrite. Outputs ignored review
images plus a scoped report; refuses overwrites. Run from repository root.
"""
import argparse,hashlib,json,math,re,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/v020-pitch'

def run(args):return subprocess.check_output(list(map(str,args)),stderr=subprocess.STDOUT)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rgb(file,t,filter=None):
    args=['ffmpeg','-v','error','-ss',f'{t:.6f}','-i',file,'-frames:v','1']
    if filter:args+=['-vf',filter]
    return Image.open(__import__('io').BytesIO(run(args+['-f','image2pipe','-vcodec','png','pipe:1']))).convert('RGB')
def psnr(a,b):
    assert a.size==b.size
    data=zip(a.tobytes(),b.tobytes());mse=sum((x-y)**2 for x,y in data)/(a.width*a.height*3)
    return 99.0 if mse==0 else 10*math.log10(255**2/mse)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-media-qa',action='store_true');p.add_argument('--review-id',default='initial');a=p.parse_args()
    if not a.execute_media_qa:p.error('Explicit QA flag required')
    if not re.fullmatch('[a-z][a-z0-9-]{0,31}',a.review_id):raise RuntimeError('Simple bounded review ID required')
    suffix='' if a.review_id=='initial' else '-'+a.review_id
    report=OUT/f'qa{suffix}.json'
    if report.exists():raise RuntimeError('Existing QA record; no overwrite')
    manifest=json.loads((OUT/'render-manifest.json').read_text());video=OUT/'pitch-v020.mp4'
    assert sha(video)==manifest['video_sha256']
    info=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',video]))
    vs=[s for s in info['streams'] if s['codec_type']=='video'];aud=[s for s in info['streams'] if s['codec_type']=='audio']
    assert len(vs)==len(aud)==1 and vs[0]['codec_name']=='h264' and aud[0]['codec_name']=='aac'
    assert (vs[0]['width'],vs[0]['height'],vs[0]['r_frame_rate'])==(1920,1080,'24/1')
    length=float(info['format']['duration']);timeline=json.loads((OUT/'timeline.json').read_text())
    assert 180<=length<=300 and abs(length-timeline['seconds'])<.15
    captions=timeline['captions'];assert len(captions)==24
    for i,c in enumerate(captions):
        assert 0<=c['start']<c['end']<=length and (i==0 or c['start']>=captions[i-1]['end'])
    levels=run(['ffmpeg','-hide_banner','-i',video,'-af','volumedetect','-vn','-f','null','-']).decode()
    mean=float(re.search(r'mean_volume: (-?[\d.]+) dB',levels)[1]);peak=float(re.search(r'max_volume: (-?[\d.]+) dB',levels)[1])
    assert -60<mean<-3 and peak<=0
    av_gap=abs(float(vs[0]['duration'])-float(aud[0]['duration']));assert av_gap<.15
    review=OUT/f'encoded-review{suffix}';review.mkdir(exist_ok=False)
    contact=Image.new('RGB',(1920,6*290),'#17151f');d=ImageDraw.Draw(contact);samples=[]
    for i,c in enumerate(captions):
        t=min(c['end']-.05,c['start']+1);frame=rgb(video,t);small=frame.resize((480,270));x=(i%4)*480;y=(i//4)*290
        contact.paste(small,(x,y));d.text((x+8,y+272),f'Beat {i+1} @ {t:.2f}s',fill='white')
        samples.append({'beat':i+1,'seconds':t,'encoded_rgb_sha256':hashlib.sha256(frame.tobytes()).hexdigest()})
        if i in (0,9,12,14,23):frame.save(review/f'critical-{i+1:02}.png')
    contact.save(review/'contact.png')
    comparisons=[]
    for mapping in timeline['clip_segments']:
        for local in (1.0,7.0):
            t=mapping['pitch_start']+local
            # YUV420 overlay placement rounds requested odd x=1345 to x=1344.
            # Match the actual encoded chroma grid, not a one-pixel shifted crop.
            actual=rgb(video,t).crop((1344,220,1774,860))
            source=ROOT/f'artifacts/v012-phone-demo/{mapping["clip"]}.mp4'
            expected=rgb(source,local,'fps=24,scale=430:640:force_original_aspect_ratio=decrease,pad=430:640:(ow-iw)/2:(oh-ih)/2:color=0x17151f,setsar=1,format=yuv420p')
            value=psnr(actual,expected);assert value>28,('Historical clip parity',mapping['clip'],local,value)
            comparisons.append({'clip':mapping['clip'],'source_seconds':local,'pitch_seconds':t,'psnr_db':value,'encoded_crop':[1344,220,430,640],'reference_pixel_format':'yuv420p','scope':'Four sampled original-speed comparisons, not every encoded frame'})
    r={'schema':'focuspilot.v020_pitch_qa.v1','video_sha256':sha(video),'renderer_full_decode_recorded':manifest.get('full_decode_passed') is True,'seconds':length,'caption_segments':24,'caption_order_and_bounds_pass':True,'audio_mean_db':mean,'audio_peak_db':peak,'av_duration_gap_seconds':av_gap,'sampled_encoded_frames':samples,'historical_clip_comparisons':comparisons,'encoded_visual_review_complete':False,'human_complete_audio_review':False,'phone_speaker_audibility_verified':False,'phone_actions_executed':0,'qa_source_sha256':sha(Path(__file__))}
    with report.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps({'report':str(report),'seconds':length,'audio_mean_db':mean,'audio_peak_db':peak,'clip_parity_samples':len(comparisons)}))
if __name__=='__main__':main()
