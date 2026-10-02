import hashlib,json,pathlib,tempfile,unittest
from generate_data import build,FAMILIES,SYSTEM
from token_trie import allowed_next
class FrozenDataTests(unittest.TestCase):
 def test_reproducible_split_hashes_and_families(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   first=build(a);second=build(b);self.assertEqual(first,second)
   self.assertEqual({k:v['rows'] for k,v in first['splits'].items()},{'train':116,'valid':14,'heldout':41})
   texts={};groups={}
   for split in first['splits']:
    records=[json.loads(x) for x in (pathlib.Path(a)/(split+'.jsonl')).read_text().splitlines()]
    texts[split]={r['utterance'] for r in records};groups[split]={r['group'] for r in records}
    for g in groups[split]:
     raw=''.join(json.dumps(r,sort_keys=True)+'\n' for r in records if r['group']==g).encode();self.assertEqual(hashlib.sha256(raw).hexdigest(),first['splits'][split]['group_hashes'][g])
   self.assertFalse(texts['train'] & texts['heldout']);self.assertFalse(texts['valid'] & texts['heldout']);self.assertFalse(groups['train'] & groups['heldout'])
 def test_response_schema_and_negation_policy(self):
  self.assertIn('negated',SYSTEM)
  with tempfile.TemporaryDirectory() as d:
   build(d)
   for r in map(json.loads,(pathlib.Path(d)/'train.jsonl').read_text().splitlines()):
    self.assertEqual(json.loads(r['messages'][-1]['content']),{'intent':r['intent']})
    if r['utterance'].startswith('Do not'):self.assertEqual(r['intent'],'unknown')
class TokenTrieTests(unittest.TestCase):
 def test_branching_prefixes_and_terminal_prefetch(self):
  seqs=[[1,2,4,9],[1,3,5,9]]
  self.assertEqual(allowed_next(seqs,[]),[1]);self.assertEqual(allowed_next(seqs,[1]),[2,3]);self.assertEqual(allowed_next(seqs,[1,3]),[5]);self.assertEqual(allowed_next(seqs,[1,2,4]),[9]);self.assertEqual(allowed_next(seqs,[1,2,4,9]),[9])
 def test_unapproved_prefix_abstains_by_error(self):
  with self.assertRaises(ValueError):allowed_next([[1,2,9]],[1,7])
  with self.assertRaises(ValueError):allowed_next([[1,2,9]],[1,2,9,6])
if __name__=='__main__':unittest.main()
