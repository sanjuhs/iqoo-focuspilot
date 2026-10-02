import {mkdir,rename,rm} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import path from 'node:path';
import {manifest,verifyModel,modelPath} from './lab.mjs';
const id=process.argv[2]??manifest.defaultModel;
let temporary;
try {
  const item=manifest.models[id];
  if(!item || item.bytes>600000000) throw new Error('Unknown model or artifact exceeds 600 MB lab download limit');
  try {await verifyModel(id);console.log(`Verified cached ${id}`);process.exit(0);}catch{}
  const destination=modelPath(id);temporary=destination+'.partial';
  await mkdir(path.dirname(destination),{recursive:true});
  console.log(`Downloading only ${item.repo}@${item.revision}/${item.file} (${item.bytes} bytes)`);
  await new Promise((resolve,reject)=>{
    const child=spawn('curl',['--fail','--silent','--show-error','--location','--connect-timeout','20','--max-time','600','--retry','2',
      `https://huggingface.co/${item.repo}/resolve/${item.revision}/${item.file}`,'-o',temporary],{stdio:'inherit'});
    child.on('error',reject);child.on('exit',code=>code===0?resolve():reject(new Error(`curl exited ${code}`)));
  });
  await rename(temporary,destination);await verifyModel(id);console.log('SHA-256 verified; local GGUF ready');
}catch(error){if(temporary)await rm(temporary,{force:true}).catch(()=>{});console.error(error.message);process.exitCode=1;}
