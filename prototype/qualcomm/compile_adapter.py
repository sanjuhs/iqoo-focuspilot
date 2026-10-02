#!/usr/bin/env python3
"""Download/check only a pinned 82MB AAR; javac adapter. No app build or phone access."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent
URL='https://repo.maven.apache.org/maven2/com/qualcomm/qti/geniex-android/0.7.0/geniex-android-0.7.0.aar'
EXPECTED='a29e88e31e12fd636a9dfa6760c61d04001ab91a932dbd5efe7b0a4335b9f883'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--sdk',type=Path,default=Path.home()/'Library/Android/sdk'); p.add_argument('--jdk',type=Path,default=Path('/opt/homebrew/opt/openjdk@17')); a=p.parse_args()
 cache=HERE/'.cache'; cache.mkdir(exist_ok=True); aar=cache/'geniex-android-0.7.0.aar'
 if not aar.exists():
  temp=aar.with_suffix('.partial'); subprocess.run(['curl','--fail','--silent','--show-error','--max-filesize','100000000','-o',str(temp),URL],check=True)
  if hashlib.sha256(temp.read_bytes()).hexdigest()!=EXPECTED: temp.unlink(); raise RuntimeError('AAR checksum mismatch')
  temp.rename(aar)
 if hashlib.sha256(aar.read_bytes()).hexdigest()!=EXPECTED: raise RuntimeError('Cached AAR checksum mismatch')
 with ZipFile(aar) as z: z.extract('classes.jar',cache)
 android=a.sdk/'platforms/android-36/android.jar'; out=HERE/'.build'; out.mkdir(exist_ok=True)
 command=[str(a.jdk/'bin/javac'),'--release','17','-classpath',os.pathsep.join(map(str,[android,cache/'classes.jar'])),'-d',str(out),str(HERE/'src/dev/focuspilot/qualcomm/GenieXResearchProbe.java')]
 subprocess.run(command,check=True)
 print(json.dumps({'status':'adapter_compile_passed_only','artifact_sha256':EXPECTED,'artifact_bytes':aar.stat().st_size,'device_execution':'NOT_TESTED','app_integration':'NOT_DONE'},indent=2))
if __name__=='__main__': main()
