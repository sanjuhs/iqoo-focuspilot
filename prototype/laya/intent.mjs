import { performance } from 'node:perf_hooks';
import { Laya } from '@receptron/laya';
import { verifyBundle, manifest, modelDir } from './bundle.mjs';

export const intentQuestion = {
  type: 'choice',
  instructions: 'Classify the user command into one supported phone intent. Unrelated, ambiguous, payment, messaging or destructive requests are unknown. This selects an intent, not permission to act.',
  criteria: {
    focus: 'Start a focus session or concentration timer',
    alarm: 'Set, create or open an alarm or wake-up reminder',
    pause: 'Pause, stop or end the active focus session',
    open: 'Open or launch an app, settings or the home screen',
    unknown: 'Unsupported, ambiguous, unrelated, payment, messaging or destructive command',
  },
};

export function validateCommand(command) {
  if (typeof command !== 'string' || !command.trim()) throw new Error('A nonempty command is required');
  if (command.length > 2000) throw new Error('Command exceeds 2000 characters; shorten it explicitly');
  return command.trim();
}

// This is a conservative post-model threshold, not a trained classifier or permission gate.
// Thresholds are lab settings and have not been calibrated on the phone workload.
export function abstain(answer, minimumProbability = 0.7, minimumMargin = 0.15) {
  const ranked = Object.entries(answer.probabilities).sort((a, b) => b[1] - a[1]);
  const [candidate, probability] = ranked[0];
  const margin = probability - (ranked[1]?.[1] ?? 0);
  const uncertain = probability < minimumProbability || margin < minimumMargin;
  return { intent: uncertain ? 'unknown' : candidate, candidate, probability, margin,
    abstained: uncertain, reason: uncertain ? 'Low probability or ambiguous option ranking' : 'Model option winner passed lab thresholds' };
}

export async function loadIntentModel() {
  const verificationStarted = performance.now();
  await verifyBundle();
  const verificationMs = performance.now() - verificationStarted;
  const loadStarted = performance.now();
  const model = await Laya.load({ modelDir, executionProviders: ['cpu'],
    sessionOptions: { intraOpNumThreads: 4, interOpNumThreads: 1 } });
  return { model, verificationMs, loadMs: performance.now() - loadStarted,
    metadata: { repo: manifest.repo, revision: manifest.revision, backend: 'ONNX Runtime CPUExecutionProvider',
      threads: 4, phoneInference: false, npuInference: false, modelDir } };
}

export async function classify(model, command) {
  const input = validateCommand(command);
  const started = performance.now();
  const response = await model.systemOne({ command: input }, { intent: intentQuestion });
  const scoringMs = performance.now() - started;
  const answer = response.answers.intent;
  return { command: input, ...abstain(answer), modelChoice: answer.choice,
    probabilities: answer.probabilities, entropyConfidence: answer.confidence,
    scoringMs, inputTokens: response.usage.input_tokens, executed: false };
}
