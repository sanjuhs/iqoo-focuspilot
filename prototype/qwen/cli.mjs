import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { startServer, classify, directory, manifest } from './lab.mjs';

const [mode, id=manifest.defaultModel, ...arguments_] = process.argv.slice(2);
const quantile = (values,p) => [...values].sort((a,b)=>a-b)[Math.ceil(values.length*p)-1];
let server;
try {
  if (!['classify','benchmark','classify-slots','benchmark-slots'].includes(mode)) throw new Error('Usage: node cli.mjs classify qwen25|qwen35 "command" | benchmark qwen25|qwen35 [report.json]; append -slots to mode for the separate slot-generation experiment');
  const intentOnly=!mode.endsWith('-slots');
  server = await startServer(id);
  if (mode.startsWith('classify')) console.log(JSON.stringify(await classify(server, arguments_.join(' '),intentOnly),null,2));
  else {
    const cases = JSON.parse(await readFile(path.join(directory,intentOnly?'intent-holdout.json':'holdout.json'),'utf8'));
    const cold = await classify(server,'Begin my focus session.',intentOnly);
    const rows = [];
    for (const item of cases) {
      const result = await classify(server,item.command,intentOnly);
      rows.push({...item,...result,intentCorrect:result.output.intent===item.expected.intent,
        slotsCorrect:Object.entries(item.expected).every(([key,value])=>result.output[key]===value)});
    }
    const report = {
      status:'Pre-event laptop research, one fixed hand-written holdout; not phone/NPU inference or a broad reliability benchmark',
      measuredAt:new Date().toISOString(),intentOnly,modelId:id,model:manifest.models[id],runtime:manifest.runtime,
      runtimeVersion:server.runtimeVersion,backend:server.backend,cpu:os.cpus()[0].model,platform:process.platform,architecture:process.arch,
      context:2048,threads:4,temperature:0,thinkingEnabled:false,promptCacheEnabled:false,
      verificationMs:server.verificationMs,serverReadyMs:server.serverReadyMs,firstRequestMs:cold.requestMs,
      warmMedianMs:quantile(rows.map(r=>r.requestMs),0.5),warmP95Ms:quantile(rows.map(r=>r.requestMs),0.95),
      count:rows.length,intentsCorrect:rows.filter(r=>r.intentCorrect).length,slotsCorrect:rows.filter(r=>r.slotsCorrect).length,
      validationFailures:rows.filter(r=>r.validationError).length,rows,
    };
    if (arguments_[0]) await writeFile(arguments_[0],JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({...report,rows:undefined},null,2));
  }
} catch(error) { console.error(error.message);process.exitCode=1; }
finally { if(server) await server.close(); }
