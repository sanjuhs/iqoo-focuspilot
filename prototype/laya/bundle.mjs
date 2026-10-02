import { createReadStream } from 'node:fs';
import { readFile, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const labDir = path.dirname(fileURLToPath(import.meta.url));
export const projectDir = path.resolve(labDir, '../..');
export const manifest = JSON.parse(await readFile(path.join(labDir, 'model-manifest.json'), 'utf8'));
export const modelDir = path.resolve(projectDir, manifest.cacheDirectory);

export async function hashFile(file) {
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
}

export async function verifyFile(entry) {
  const file = path.join(modelDir, entry.path);
  const info = await stat(file);
  if (info.size !== entry.bytes) throw new Error(`Wrong byte count: ${entry.path}`);
  if (await hashFile(file) !== entry.sha256) throw new Error(`SHA-256 mismatch: ${entry.path}`);
}

export async function verifyBundle() {
  for (const entry of manifest.files) await verifyFile(entry);
  return modelDir;
}
