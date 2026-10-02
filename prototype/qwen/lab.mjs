import { readFile, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import { spawn, spawnSync } from 'node:child_process';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';

export const directory = path.dirname(fileURLToPath(import.meta.url));
export const manifest = JSON.parse(await readFile(path.join(directory, 'model-manifest.json'), 'utf8'));
export const schema = JSON.parse(await readFile(path.join(directory, 'schema.json'), 'utf8'));
export const systemPrompt = await readFile(path.join(directory, 'system-prompt.txt'), 'utf8');
export const intentSchema = JSON.parse(await readFile(path.join(directory,'intent-schema.json'),'utf8'));
export const intentPrompt = await readFile(path.join(directory,'intent-prompt.txt'),'utf8');
export function modelPath(id) { return path.resolve(directory, '../../models/qwen', manifest.models[id].file); }

export async function verifyModel(id) {
  const entry = manifest.models[id];
  if (!entry) throw new Error('Model ID must be qwen25 or qwen35');
  const file = modelPath(id);
  if ((await stat(file)).size !== entry.bytes) throw new Error('Model size mismatch');
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(file)) hash.update(chunk);
  if (hash.digest('hex') !== entry.sha256) throw new Error('Model SHA-256 mismatch');
}

export function validateResult(value) {
  const keys = Object.keys(value).sort().join(',');
  if (keys !== 'app,hour,intent,minute,minutes') throw new Error('Unexpected or missing slots');
  for (const [name, rule] of Object.entries(schema.properties)) {
    const item = value[name];
    if (rule.type === 'integer' && (!Number.isInteger(item) || item < rule.minimum || item > rule.maximum)) throw new Error(`Invalid ${name}`);
    if (rule.enum && !rule.enum.includes(item)) throw new Error(`Invalid ${name}`);
  }
  if (value.intent === 'focus' && value.minutes < 1) throw new Error('Focus duration is required');
  if (value.intent !== 'focus' && value.minutes !== 0) throw new Error('Unexpected focus duration');
  if (value.intent === 'alarm' && ((value.hour === -1) !== (value.minute === -1))) throw new Error('Partial alarm time');
  if (value.intent !== 'alarm' && (value.hour !== -1 || value.minute !== -1)) throw new Error('Unexpected alarm time');
  if (value.intent === 'open' && value.app === 'none') throw new Error('Supported app required');
  if (value.intent !== 'open' && value.app !== 'none') throw new Error('Unexpected app');
  return value;
}

export const unknown = { intent: 'unknown', minutes: 0, hour: -1, minute: -1, app: 'none' };

export async function startServer(id) {
  const verifyStarted = performance.now();
  await verifyModel(id);
  const verificationMs = performance.now() - verifyStarted;
  const binary = process.env.LLAMA_SERVER ?? 'llama-server';
  const versionProcess = spawnSync(binary, ['--version'], { encoding:'utf8' });
  const runtimeVersion = versionProcess.stdout + versionProcess.stderr;
  if (!runtimeVersion.includes(manifest.runtime.commit.slice(0, 9))) throw new Error(`Expected pinned llama.cpp commit ${manifest.runtime.commit}`);
  const port = await new Promise((resolve, reject) => {
    const socket = net.createServer(); socket.on('error', reject);
    socket.listen(0, '127.0.0.1', () => { const p = socket.address().port; socket.close(() => resolve(p)); });
  });
  const arguments_ = ['-m',modelPath(id),'--device','none','-ngl','0','--no-op-offload','-t','4','-tb','4','-c','2048',
    '--parallel','1','--host','127.0.0.1','--port',String(port),'--no-webui','--no-warmup'];
  if (id === 'qwen35') arguments_.push('--chat-template-kwargs','{"enable_thinking":false}');
  const started = performance.now();
  const process_ = spawn(binary, arguments_, { stdio:['ignore','pipe','pipe'] });
  let log = '';
  for (const stream of [process_.stdout, process_.stderr]) stream.on('data', bytes => { log = (log + bytes.toString()).slice(-16000); });
  let spawnError;
  process_.on('error', error => { spawnError = error; });
  const url = `http://127.0.0.1:${port}`;
  try {
    while (performance.now() - started < 60000) {
      if (spawnError) throw spawnError;
      if (process_.exitCode !== null) throw new Error(`Server exited ${process_.exitCode}: ${log}`);
      try { const response = await fetch(`${url}/health`, {signal:AbortSignal.timeout(1000)}); if (response.ok) return {
        url, id, process: process_, verificationMs, serverReadyMs:performance.now()-started, runtimeVersion:runtimeVersion.trim(),
        backend:'llama.cpp CPU, device none, 0 GPU layers, operation offload disabled', getLog: () => log,
        async close() { if (process_.exitCode === null) { process_.kill('SIGTERM'); await new Promise(resolve => process_.once('exit', resolve)); } },
      }; } catch { /* readiness not yet reached */ }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error(`Server readiness timeout: ${log}`);
  } catch (error) { process_.kill('SIGTERM'); throw error; }
}

export async function classify(server, command, intentOnly=false) {
  if (typeof command !== 'string' || !command.trim() || command.length > 500) throw new Error('Command must contain 1 to 500 characters');
  const started = performance.now();
  const response = await fetch(`${server.url}/v1/chat/completions`, {
    method:'POST', headers:{'content-type':'application/json'}, signal:AbortSignal.timeout(45000),
    body:JSON.stringify({ model:'local', messages:[{role:'system',content:intentOnly?intentPrompt:systemPrompt},
      {role:'user',content:command.replaceAll('<|','< | ').replaceAll('|>',' | >')}],
      temperature:0, seed:42, max_tokens:intentOnly?64:160, cache_prompt:false,
      chat_template_kwargs:{enable_thinking:false},
      response_format:{type:'json_schema',json_schema:{name:'phone_intent',strict:true,schema:intentOnly?intentSchema:schema}} }),
  });
  if (!response.ok) throw new Error(`Inference HTTP ${response.status}: ${await response.text()}`);
  const raw = await response.json();
  const content = raw.choices?.[0]?.message?.content;
  let parsed;
  let validationError = null;
  try {
    if (raw.choices?.[0]?.finish_reason === 'length') throw new Error('Generation limit reached');
    parsed = JSON.parse(content);
    if(intentOnly) {
      if(Object.keys(parsed).join(',')!=='intent' || !intentSchema.properties.intent.enum.includes(parsed.intent)) throw new Error('Invalid intent schema');
    } else parsed=validateResult(parsed);
  } catch (error) { validationError = error.message; parsed = intentOnly?{intent:'unknown'}:{...unknown}; }
  return { command, output:parsed, rawContent:content, validationError, requestMs:performance.now()-started,
    usage:raw.usage, timings:raw.timings ?? null, executed:false };
}
