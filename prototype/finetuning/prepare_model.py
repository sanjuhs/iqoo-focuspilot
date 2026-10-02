"""Download only pinned data files; verify size/SHA, never execute remote model code."""
import argparse,hashlib,json,pathlib,subprocess

def verify(path,entry):
 return path.is_file() and path.stat().st_size==entry['bytes'] and hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==entry['sha256']
def main():
 p=argparse.ArgumentParser();p.add_argument('--model-dir',default='prototype/finetuning/build/model');a=p.parse_args()
 manifest=json.loads((pathlib.Path(__file__).parent/'model-manifest.json').read_text());assert sum(f['bytes'] for f in manifest['files'])<1_000_000_000
 root=pathlib.Path(a.model_dir);root.mkdir(parents=True,exist_ok=True)
 for entry in manifest['files']:
  name=entry['file'];assert pathlib.Path(name).name==name;target=root/name
  if verify(target,entry):print('VERIFIED cached',name,flush=True);continue
  if target.exists():raise ValueError('Existing cached file failed checksum; move it aside explicitly before retry: '+str(target))
  temp=target.with_suffix(target.suffix+'.partial')
  try:
   subprocess.run(['curl','--fail','--location','--retry','2','--connect-timeout','15','--max-time','600','--max-filesize',str(entry['bytes']),'--silent','--show-error',f'https://huggingface.co/{manifest["model_id"]}/resolve/{manifest["revision"]}/{name}','-o',str(temp)],check=True)
   assert verify(temp,entry),'Downloaded data checksum mismatch: '+name
   temp.replace(target);print('VERIFIED downloaded',name,flush=True)
  finally:temp.unlink(missing_ok=True)
if __name__=='__main__':main()
