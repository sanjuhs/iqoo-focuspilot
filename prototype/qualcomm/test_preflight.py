import hashlib,tempfile,unittest
from pathlib import Path
from preflight import assess,MODEL_HASH
class EvidenceGates(unittest.TestCase):
 def setUp(self): self.props={'ro.soc.model':'SM8850','ro.product.cpu.abi':'arm64-v8a','ro.build.version.sdk':'36'}
 def test_validated_device_never_implies_npu(self): self.assertTrue(assess(self.props)['sdk_validated_device']); self.assertFalse(assess(self.props)['npu_verified'])
 def test_nothing_retains_cpu(self): self.props['ro.soc.model']='SM7635';self.assertFalse(assess(self.props)['sdk_validated_device'])
 def test_abi_and_api_prerequisites(self): self.props['ro.product.cpu.abi']='x86_64';self.assertFalse(assess(self.props)['sdk_validated_device']);self.props['ro.product.cpu.abi']='arm64-v8a';self.props['ro.build.version.sdk']='26';self.assertFalse(assess(self.props)['sdk_validated_device'])
 def test_setting_and_library_load_are_insufficient(self): self.assertFalse(assess(self.props,{'requested_compute':'npu','loaded_library':'libggml-hexagon.so'})['evidence_complete'])
 def test_cpu_only_request_rejects_htp_counts(self):
  e={'requested_compute':'cpu','executed_operators':{'HTP':2,'CPU':3}}
  self.assertIn('CPU-only request contradicts model HTP execution count',assess(self.props,e)['missing'])
 def test_full_trace_is_still_subject_to_review(self):
  with tempfile.TemporaryDirectory() as d:
   file=Path(d)/'synthetic-test.trace';file.write_text('Synthetic fixture, not device evidence')
   e={'model_sha256':MODEL_HASH,'soc':'SM8850','session_id':'synthetic-fixture','runtime':'llama_cpp','requested_compute':'hybrid','executed_operators':{'HTP':3,'CPU':1},'trace_artifacts':[{'path':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}],'output_checked':True}
   r=assess(self.props,e);self.assertTrue(r['evidence_complete']);self.assertFalse(r['npu_verified']);self.assertIn('mixed',r['operator_coverage'])
   e['model_sha256']='wrong';self.assertFalse(assess(self.props,e)['evidence_complete']);e['model_sha256']=MODEL_HASH
   e['trace_artifacts'][0]['sha256']='wrong';self.assertFalse(assess(self.props,e)['evidence_complete'])
if __name__=='__main__':unittest.main()
