import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validateCommand, abstain } from '../intent.mjs';

test('invalid CLI requests fail before loading the model', () => {
  const cli = fileURLToPath(new URL('../cli.mjs', import.meta.url));
  for (const args of [[], ['invent'], ['classify'], ['classify', ' '.repeat(3)]]) {
    const child = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8' });
    assert.equal(child.status, 1);
    assert.match(child.stderr, /Usage|nonempty/);
  }
});

test('overlong inputs are rejected explicitly instead of silently trimmed', () => {
  assert.throws(() => validateCommand('x'.repeat(2001)), /shorten/);
});

test('ambiguous model output abstains; strong unsupported output remains unknown', () => {
  // Synthetic probabilities test only the post-model gate, not model quality.
  assert.equal(abstain({ probabilities: { focus: 0.45, alarm: 0.40, unknown: 0.15 } }).intent, 'unknown');
  assert.equal(abstain({ probabilities: { focus: 0.03, unknown: 0.97 } }).intent, 'unknown');
});

test('real pinned model provides normalized finite probabilities without executing phone actions',
  { skip: process.env.LAYA_INTEGRATION !== '1' }, async () => {
    const { loadIntentModel, classify } = await import('../intent.mjs');
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => { throw new Error('Network fetch disabled for the local-model test'); };
    let model;
    try {
      const loaded = await loadIntentModel();
      model = loaded.model;
      const metadata = loaded.metadata;
      const result = await classify(model, 'Start a focus session for 25 minutes.');
      assert.equal(metadata.backend, 'ONNX Runtime CPUExecutionProvider');
      assert.equal(result.executed, false);
      assert.equal(Object.keys(result.probabilities).length, 5);
      const values = Object.values(result.probabilities);
      assert.ok(values.every(p => Number.isFinite(p) && p >= 0 && p <= 1));
      assert.ok(Math.abs(values.reduce((a, b) => a + b, 0) - 1) < 0.001);
      assert.ok(result.scoringMs > 0);
      assert.equal(result.modelChoice, 'focus');
    } finally {
      globalThis.fetch = originalFetch;
      if (model) await model.close();
    }
  });
