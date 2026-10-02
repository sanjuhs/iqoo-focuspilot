"""Finite canonical answer prefixes; format constraint, not a safety classifier."""
def allowed_next(sequences,generated):
 choices={s[len(generated)] for s in sequences if len(s)>len(generated) and s[:len(generated)]==generated}
 if not choices:
  # MLX may compute one speculative next logit after emitting EOS.
  if generated in sequences:return [generated[-1]]
  raise ValueError('Generation left bounded intent-token trie')
 return sorted(choices)
