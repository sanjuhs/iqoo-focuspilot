import json,pathlib,tempfile,unittest
import numpy as np
from generate_data import generate,TEMPLATES
from train_evaluate import softmax,standardize,predict,choose_threshold,policy_predictions,metrics,parameter_hash
class FrozenDataTests(unittest.TestCase):
 def test_reproducible_family_split_and_known_counts(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   m=generate(a);self.assertEqual(m,generate(b));self.assertEqual({k:v['rows'] for k,v in m['splits'].items()},{'train':222,'validation':61,'heldout':90})
   sources=[t for group in TEMPLATES.values() for templates in group.values() for t in templates];self.assertEqual(len(sources),len(set(sources)))
   text={split:{r['utterance'] for r in map(json.loads,(pathlib.Path(a)/(split+'.jsonl')).read_text().splitlines())} for split in m['splits']}
   self.assertFalse(text['train']&text['heldout']);self.assertFalse(text['validation']&text['heldout'])
class ClassifierTests(unittest.TestCase):
 def test_stable_softmax_and_numerical_saturation_are_explicit(self):
  p=softmax(np.array([[1000.,0.,-1000.],[1.,2.,3.]]));self.assertTrue(np.isfinite(p).all());np.testing.assert_allclose(p.sum(axis=1),1.)
  # A finite logit gap can round to probability1; this is not calibrated certainty.
  self.assertEqual(p[0,0],1.)
 def test_threshold_selection_does_not_trade_unknown_errors_for_coverage(self):
  p=np.array([[.8,.05,.03,.03,.03,.03,.03],[.7,.05,.05,.05,.05,.05,.05],[.01,.01,.01,.01,.01,.01,.94]])
  labels=np.array([0,6,6]);choice=choose_threshold(labels,p);m=metrics(labels,policy_predictions(p,choice));self.assertEqual(m['unknown_to_supported_false_positives'],0)
  self.assertEqual(choice['threshold'],.75);self.assertEqual(m['supported_correct_accepted'],1)
 def test_validation_can_force_abstain_all(self):
  p=np.array([[1.,0.,0.,0.,0.,0.,0.]]);choice=choose_threshold(np.array([6]),p);self.assertTrue(choice['abstain_all']);self.assertEqual(policy_predictions(p,choice)[0],6)
 def test_low_probability_margin_and_unknown_class_abstain(self):
  p=np.array([[.5,.49,.002,.002,.002,.002,.002],[.01,.01,.01,.01,.01,.01,.94]])
  np.testing.assert_array_equal(predict(p,.45,.1),[6,6])
 def test_signed_contributions_and_head_only_intervention(self):
  x=np.array([[5.,-1.]]);mean=np.array([1.,1.]);std=np.array([2.,2.]);z=standardize(x,mean,std)
  w=np.array([[2.,-1.],[-3.,1.]]);b=np.array([.5,-.5]);logits=z@w+b
  self.assertEqual(logits[0,0],7.5);self.assertEqual(float(np.sum(z[0]*w[:,0])+b[0]),7.5)
  changed=z.copy();changed[0,1]=0.;np.testing.assert_allclose(changed@w+b,logits-z[0,1]*w[1])
 def test_parameter_digest_records_actual_parameter_change(self):
  w=np.zeros((1024,7));b=np.zeros(7);old=parameter_hash(w,b);w[3,2]=.125;self.assertNotEqual(old,parameter_hash(w,b));self.assertEqual(w.size+b.size,7175)
if __name__=='__main__':unittest.main()
