#!/usr/bin/env python3
"""Stream a frozen light APK into a model-bundled, SDK-aligned debug research APK.

No downloads, builds, phone actions or existing-output overwrites. A byte budget
reserves two complete temporary APKs before writing. Private key material is
read only by apksigner; this script reports public certificate digests only.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re, shutil, stat, subprocess, tempfile
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_STORED

ROOT=Path(__file__).resolve().parents[1]
MODEL_SHA='57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf'
MODEL_BYTES=563036064
MODEL_ENTRY='assets/qwen35.gguf'
WORKSPACE_LIMIT=15_000_000_000
OVERHEAD=256*1024
CHUNK=1024*1024

def digest(stream):
 h=hashlib.sha256()
 while block:=stream.read(CHUNK):h.update(block)
 return h.hexdigest()
def identity(path):
 with path.open('rb') as stream:return {'bytes':path.stat().st_size,'sha256':digest(stream)}
def signature_entry(name):
 return bool(re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',name,re.I))
def project_bytes(root):
 """Conservative logical bytes, all files including ignored/.git; no symlink follow."""
 total=0
 def fail(error):raise error
 for folder,dirs,files in os.walk(root,followlinks=False,onerror=fail):
  for name in dirs+files:
   entry=(Path(folder)/name).lstat()
   if stat.S_ISREG(entry.st_mode) or stat.S_ISLNK(entry.st_mode):total+=entry.st_size
 return total

def budget(root_size,light_size,model_size=MODEL_BYTES):
 cap=light_size+model_size+OVERHEAD;peak=root_size+2*cap
 if peak>WORKSPACE_LIMIT:raise ValueError(f'Two-copy peak estimate {peak} exceeds {WORKSPACE_LIMIT} byte project budget; nothing written')
 return {'project_bytes_before':root_size,'per_copy_byte_cap':cap,'reserved_temporary_bytes':2*cap,'estimated_peak_project_bytes':peak,'project_limit_bytes':WORKSPACE_LIMIT,'estimate':'logical bytes; directories not counted, symlinks not followed; full two-copy allowance includes 256KiB overhead each'}

class BoundedWriter:
 """Prevent the streaming clone from exceeding its pre-reserved file allowance."""
 def __init__(self,stream,limit):self.stream=stream;self.limit=limit
 def write(self,data):
  if self.stream.tell()+len(data)>self.limit:raise ValueError('Clone exceeds reserved byte allowance')
  return self.stream.write(data)
 def __getattr__(self,name):return getattr(self.stream,name)

def payload_hashes(path):
 with ZipFile(path) as archive:
  names=archive.namelist()
  if len(names)!=len(set(names)):raise ValueError('APK contains duplicate ZIP entries')
  return {item.filename:digest(archive.open(item)) for item in archive.infolist() if not signature_entry(item.filename)}

def clone_with_model(light,target,model,cap,expected_model_sha=MODEL_SHA,expected_model_bytes=MODEL_BYTES):
 removed=[]
 with light.open('rb') as light_file,model.open('rb') as model_file,target.open('xb') as target_file:
  with ZipFile(light_file) as source,ZipFile(BoundedWriter(target_file,cap),'w') as destination:
   for info in source.infolist():
    if signature_entry(info.filename):removed.append(info.filename);continue
    clone=copy.copy(info)
    with source.open(info) as reader,destination.open(clone,'w') as writer:shutil.copyfileobj(reader,writer,CHUNK)
   info=ZipInfo(MODEL_ENTRY,(1980,1,1,0,0,0));info.compress_type=ZIP_STORED;info.file_size=expected_model_bytes;info.external_attr=0o100644<<16
   h=hashlib.sha256();count=0
   with destination.open(info,'w') as writer:
    while block:=model_file.read(CHUNK):writer.write(block);h.update(block);count+=len(block)
   if count!=expected_model_bytes or h.hexdigest()!=expected_model_sha:raise ValueError('Model changed during streaming clone')
 return removed

def sdk_command(arguments):
 result=subprocess.run(list(map(str,arguments)),text=True,capture_output=True)
 if result.returncode:raise RuntimeError(f'{Path(arguments[0]).name} failed with exit {result.returncode}; no final APK published')
 return result.stdout

def verified_certificate(signer,apk):
 output=sdk_command([signer,'verify','--verbose','--print-certs',apk])
 certs=re.findall(r'^Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-fA-F]{64})$',output,re.M)
 if len(certs)!=1:raise ValueError('Expected exactly one verified public APK signing certificate')
 return certs[0].lower()

def new_project_path(value,description):
 p=Path(value).expanduser().resolve()
 if not p.is_relative_to(ROOT) or p==ROOT:raise ValueError(description+' must be inside this project')
 if p.exists():raise FileExistsError(description+' already exists; refusing overwrite')
 return p

def publish_without_overwrite(source,target):
 # Same-filesystem hardlink/unlink provides atomic rename semantics without the
 # overwrite behavior of POSIX rename and never copies the large payload.
 os.link(source,target);source.unlink()

def package(args):
 light=Path(args.light).expanduser().resolve();model=ROOT/'models/qwen/Qwen3.5-0.8B-Q4_0.gguf'
 output=new_project_path(args.output,'Output APK');report=new_project_path(args.report,'Report') if args.report else None
 if report==output:raise ValueError('Report must differ from APK output')
 if not output.parent.is_dir() or (report and not report.parent.is_dir()):raise ValueError('Output/report parent must already exist')
 ignored_output=subprocess.run(['git','-C',str(ROOT),'check-ignore','--quiet',str(output)],capture_output=True)
 if ignored_output.returncode!=0:raise ValueError('APK output path must be ignored by Git')
 if report:
  ignored=subprocess.run(['git','-C',str(ROOT),'check-ignore','--quiet',str(report)],capture_output=True)
  if ignored.returncode!=0:raise ValueError('Report path must be ignored by Git')
 if not re.fullmatch('[0-9a-f]{64}',args.expected_light_sha256):raise ValueError('Full frozen light SHA-256 required')
 if not re.fullmatch('[0-9a-f]{40}',args.app_source_commit):raise ValueError('Full frozen app source commit required')
 resolved=sdk_command(['git','-C',ROOT,'rev-parse','--verify',args.app_source_commit+'^{commit}']).strip()
 if resolved!=args.app_source_commit:raise ValueError('Frozen source commit unavailable')
 tools=Path(args.tools).expanduser().resolve();align=tools/'zipalign';signer=tools/'apksigner';keystore=Path.home()/'.android/debug.keystore'
 if not all(p.is_file() for p in (light,model,align,signer,keystore)):raise FileNotFoundError('Existing APK/model/SDK/debug signing prerequisites unavailable')
 light_id=identity(light);model_id=identity(model)
 if light_id['sha256']!=args.expected_light_sha256:raise ValueError('Light APK differs from frozen input')
 if model_id!={'bytes':MODEL_BYTES,'sha256':MODEL_SHA}:raise ValueError('Model differs from fixed Qwen artifact')
 original=payload_hashes(light)
 if MODEL_ENTRY in original or any(name.endswith('.gguf') for name in original):raise ValueError('Input must be a light APK without model entries')
 with ZipFile(light) as archive:
  padding_bound=sum(16384 if i.compress_type==ZIP_STORED and i.filename.endswith('.so') else 4 for i in archive.infolist())+4
  if padding_bound+128*1024>OVERHEAD:raise ValueError('Alignment/signing padding cannot fit reserved overhead')
 certificate=verified_certificate(signer,light)
 allocation=budget(project_bytes(ROOT),light_id['bytes'])
 if shutil.disk_usage(output.parent).free<allocation['reserved_temporary_bytes']:raise ValueError('Disk free bytes insufficient for two-copy reservation')
 # No packaging output exists before every identity/signature/storage guard passes.
 temporary=Path(tempfile.mkdtemp(prefix='.bundle-packaging-',dir=output.parent))
 try:
  unaligned=temporary/'unaligned.apk';aligned=temporary/'aligned.apk'
  removed=clone_with_model(light,unaligned,model,allocation['per_copy_byte_cap'])
  sdk_command([align,'-P','16','4',unaligned,aligned])
  if aligned.stat().st_size>allocation['per_copy_byte_cap']:raise ValueError('Aligned APK exceeds reserved copy allowance')
  unaligned.unlink()  # In-place SDK signing may need one temporary copy; only two remain.
  sdk_command([signer,'sign','--ks',keystore,'--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--v4-signing-enabled','false',aligned])
  if aligned.stat().st_size>allocation['per_copy_byte_cap']:raise ValueError('Signed APK exceeds reserved copy allowance')
  final_certificate=verified_certificate(signer,aligned)
  if certificate!=final_certificate:raise ValueError('Public signing certificate differs from frozen light APK')
  sdk_command([align,'-c','-P','16','4',aligned])
  final_payload=payload_hashes(aligned)
  if set(final_payload)!=set(original)|{MODEL_ENTRY} or any(final_payload[name]!=h for name,h in original.items()):raise ValueError('Original non-signature payload parity failed')
  with ZipFile(aligned) as archive:
   embedded=archive.getinfo(MODEL_ENTRY)
   if embedded.compress_type!=ZIP_STORED or embedded.file_size!=MODEL_BYTES or final_payload[MODEL_ENTRY]!=MODEL_SHA:raise ValueError('Embedded model storage/hash differs from fixed artifact')
  if identity(light)!=light_id or identity(model)!=model_id:raise ValueError('Input bytes changed during packaging')
  final_id=identity(aligned)
  record={'kind':'pre-event debug research APK packaging; byte/signature proof, no phone run','app_source_commit':args.app_source_commit,'app_source_attribution':'caller-supplied frozen build commit, not compilation replay','packager_sha256':identity(Path(__file__).resolve())['sha256'],'light':{'file':str(light.relative_to(ROOT)) if light.is_relative_to(ROOT) else str(light),**light_id},'model':{'entry':MODEL_ENTRY,'compression':'ZIP_STORED',**model_id},'bundle':{'file':str(output.relative_to(ROOT)),**final_id},'storage':allocation,'alignment':'SDK zipalign -P 16 4 before signing; -c -P 16 4 passed after signing','signature':'SDK apksigner verify passed for light and final; same public certificate','public_certificate_sha256':final_certificate,'original_payload_count':len(original),'original_non_signature_payload_sha256':original,'only_added_non_signature_entry':MODEL_ENTRY,'removed_v1_signature_entries':removed,'tools':{name:{'file':str(path),**identity(path)} for name,path in [('zipalign',align),('apksigner',signer),('apksigner.jar',tools/'lib/apksigner.jar')] if path.is_file()},'recipe':['stream clone all non-signature ZIP entries; add pinned GGUF stored','zipalign -P 16 4 unaligned aligned','delete unaligned','apksigner sign in place using existing standard debug key, v4 disabled','verify signature/certificate, alignment, all payload/model hashes','atomic no-overwrite finalization without copying'],'temporary_large_copy_limit':2,'downloads':0,'phone_actions_executed':0,'runtime_verified':False}
  publish_without_overwrite(aligned,output)
  if report:
   with report.open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
  print(json.dumps(record,indent=2))
 finally:shutil.rmtree(temporary)

def self_test():
 """Small synthetic ZIP/storage regressions only; never package/sign a real APK."""
 import unittest
 class Checks(unittest.TestCase):
  def test_signature_filter_preserves_other_metadata(self):
   for name in ('META-INF/MANIFEST.MF','META-INF/CERT.SF','META-INF/CERT.RSA','META-INF/CERT.DSA','META-INF/CERT.EC'):self.assertTrue(signature_entry(name))
   for name in ('AndroidManifest.xml','META-INF/LICENSE','META-INF/services/provider.SF','assets/CERT.RSA'):self.assertFalse(signature_entry(name))
  def test_budget_aborts_before_writes_and_reserves_two_copies(self):
   self.assertEqual(2*(MODEL_BYTES+10+OVERHEAD),budget(0,10)['reserved_temporary_bytes'])
   with self.assertRaises(ValueError):budget(WORKSPACE_LIMIT,10)
  def test_streaming_payload_model_and_no_overwrite(self):
   with tempfile.TemporaryDirectory() as directory:
    base=Path(directory);light=base/'light.apk';model=base/'model';model.write_bytes(b'toy model')
    with ZipFile(light,'w') as z:z.writestr('classes.dex',b'fixture payload');z.writestr('META-INF/CERT.SF',b'signature');z.writestr('META-INF/LICENSE',b'notice')
    target=base/'clone.apk';clone_with_model(light,target,model,4096,hashlib.sha256(b'toy model').hexdigest(),9)
    with ZipFile(target) as z:self.assertEqual(ZIP_STORED,z.getinfo(MODEL_ENTRY).compress_type)
    hashes=payload_hashes(target);self.assertEqual(hashlib.sha256(b'fixture payload').hexdigest(),hashes['classes.dex']);self.assertIn('META-INF/LICENSE',hashes);self.assertNotIn('META-INF/CERT.SF',hashes)
    with self.assertRaises(FileExistsError):clone_with_model(light,target,model,4096)
    published=base/'final.apk';published.write_bytes(b'existing')
    with self.assertRaises(FileExistsError):publish_without_overwrite(target,published)
    self.assertEqual(b'existing',published.read_bytes());self.assertTrue(target.exists())
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
 if not result.wasSuccessful():raise SystemExit(1)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--light');parser.add_argument('--output');parser.add_argument('--report');parser.add_argument('--expected-light-sha256');parser.add_argument('--app-source-commit');parser.add_argument('--tools',default=str(Path.home()/'Library/Android/sdk/build-tools/36.0.0'));parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
 if args.self_test:self_test();return
 if not all((args.light,args.output,args.expected_light_sha256,args.app_source_commit)):parser.error('light/output/expected-light-sha256/app-source-commit required')
 package(args)
if __name__=='__main__':main()
