import { mkdir, rename, rm } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { manifest, modelDir, verifyFile } from './bundle.mjs';

// curl streams directly to disk; no weights enter memory or repository history.
function download(url, destination) {
  return new Promise((resolve, reject) => {
    const child = spawn('curl', ['--fail', '--location', '--silent', '--show-error',
      '--connect-timeout', '20', '--max-time', '900', '--retry', '2',
      '--output', destination, url], { stdio: 'inherit' });
    child.on('error', reject);
    child.on('exit', code => code === 0 ? resolve() : reject(new Error(`curl exited ${code}`)));
  });
}

try {
  const bytes = manifest.files.reduce((sum, file) => sum + file.bytes, 0);
  if (bytes > 2_000_000_000) throw new Error('Manifest exceeds the lab weight budget');
  console.log(`Pinned download: ${manifest.repo}@${manifest.revision}; ${bytes} bytes.`);
  for (const entry of manifest.files) {
    try { await verifyFile(entry); console.log(`Verified cached ${entry.path}`); continue; }
    catch { /* Missing, incomplete, or mismatching files are replaced atomically. */ }
    const file = path.join(modelDir, entry.path);
    await mkdir(path.dirname(file), { recursive: true });
    const temporary = `${file}.partial`;
    console.log(`Downloading ${entry.path} (${entry.bytes} bytes)...`);
    try {
      await download(`https://huggingface.co/${manifest.repo}/resolve/${manifest.revision}/${entry.path}`, temporary);
      await rename(temporary, file);
      await verifyFile(entry);
    } catch (error) {
      await rm(temporary, { force: true });
      throw error;
    }
    console.log(`SHA-256 verified ${entry.path}`);
  }
  console.log(`Ready for offline local inference: ${modelDir}`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
