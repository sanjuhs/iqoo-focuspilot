"""Pure prospective training boundaries; no model, data discovery or execution."""
import json
import random

INTENTS = ('alarm', 'explain', 'open_app', 'pause_focus', 'start_focus', 'timer', 'unknown')


def balanced_order(rows, seed=20261003, epochs=2):
    groups = {intent: [] for intent in INTENTS}
    for index, row in enumerate(rows):
        groups[row['intent']].append(index)
    if any(len(indices) != 16 for indices in groups.values()) or len(rows) != 112:
        raise ValueError('Exactly 16 examples per intent required')
    rng = random.Random(seed)
    order = []
    for _ in range(epochs):
        queues = {intent: rng.sample(indices, len(indices)) for intent, indices in groups.items()}
        for offset in range(16):
            for intent in rng.sample(list(INTENTS), len(INTENTS)):
                order.append(queues[intent][offset])
    return order


def completion_weights(intent, decoded_prefixes):
    """Weight tokens overlapping the exact ASCII intent VALUE, including mixed tokens."""
    if intent not in INTENTS:
        raise ValueError('Unknown label')
    answer = json.dumps({'intent': intent}, separators=(',', ':')) + '<|im_end|>'
    start = len('{"intent":"')
    end = start + len(intent)
    before = 0
    weights = []
    overlaps = []
    for text in decoded_prefixes:
        if not answer.startswith(text) or len(text) <= before:
            raise ValueError('Tokenizer offsets must be strictly increasing exact prefixes')
        after = len(text)
        overlap = before < end and after > start
        weights.append(8.0 if overlap else 1.0)
        if overlap:
            overlaps.append([before, after])
        before = after
    if before != len(answer) or not overlaps or weights[-1] != 1.0:
        raise ValueError('Complete canonical answer and unweighted terminal EOS required')
    return weights, overlaps


def supervised_weights(prompt_tokens, weights):
    if prompt_tokens < 1 or not weights:
        raise ValueError('Nonempty prompt/completion required')
    # Logit index p-1 predicts sequence token p, the first completion token.
    return [0.0] * (prompt_tokens - 1) + list(weights)


def summary(records):
    if not records:
        raise ValueError('Full nonempty denominator required')
    return {'rows': len(records),
            'correct': sum(r['actual'] == r['expected'] for r in records),
            'canonical_eos': sum(r['canonical_eos'] for r in records),
            'per_intent': {intent: {
                'rows': sum(r['expected'] == intent for r in records),
                'correct': sum(r['expected'] == intent and r['actual'] == intent for r in records)
            } for intent in INTENTS}}
