import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { loadIntentModel, classify, validateCommand } from './intent.mjs';

function percentile(values, p) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.ceil(p * sorted.length) - 1];
}

export async function run(args) {
  const [mode, ...rest] = args;
  if (mode !== 'classify' && mode !== 'benchmark') {
    throw new Error('Usage: npm run classify -- "command" | npm run benchmark -- [results.json]');
  }
  const command = mode === 'classify' ? validateCommand(rest.join(' ')) : null;
  const { model, verificationMs, loadMs, metadata } = await loadIntentModel();
  try {
    if (mode === 'classify') {
      const result = await classify(model, command);
      console.log(JSON.stringify({ status: 'pre-event laptop lab', ...metadata,
        verificationMs, loadMs, ...result }, null, 2));
      return;
    }
    const directory = path.dirname(fileURLToPath(import.meta.url));
    const cases = JSON.parse(await readFile(path.join(directory, 'cases.json'), 'utf8'));
    const cold = await classify(model, 'Start a focus session for 25 minutes.');
    const rows = [];
    for (const item of cases) {
      const result = await classify(model, item.command);
      rows.push({ id: item.id, expected: item.expected, ...result,
        rawCorrect: result.modelChoice === item.expected, selectedCorrect: result.intent === item.expected });
    }
    const actionable = rows.filter(row => row.intent !== 'unknown');
    const report = {
      status: 'Pre-event laptop research lab. These hand-written cases are a smoke set, not an untouched holdout.',
      measuredAt: new Date().toISOString(), platform: process.platform, architecture: process.arch,
      cpu: os.cpus()[0].model, node: process.version, ...metadata,
      downloadMs: null, verificationMs, sessionLoadMs: loadMs, firstScoringMs: cold.scoringMs,
      warmMedianMs: percentile(rows.map(row => row.scoringMs), 0.5),
      warmP95Ms: percentile(rows.map(row => row.scoringMs), 0.95),
      rssBytesAfterScoring: process.memoryUsage().rss,
      cases: rows.length, rawAccuracy: rows.filter(row => row.rawCorrect).length / rows.length,
      selectedAccuracy: rows.filter(row => row.selectedCorrect).length / rows.length,
      actionableCoverage: actionable.length / rows.length,
      actionableAccuracy: actionable.length ? actionable.filter(row => row.selectedCorrect).length / actionable.length : null,
      rows,
    };
    if (rest[0]) await writeFile(rest[0], JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally { await model.close(); }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  run(process.argv.slice(2)).catch(error => { console.error(error.message); process.exitCode = 1; });
}
