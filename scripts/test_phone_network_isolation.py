import unittest
from phone_network_isolation import restore_mode,parse_raw,instrumentation_entries

class NativeProbeBoundary(unittest.TestCase):
    def test_restores_only_exact_owned_candidate(self):
        self.assertEqual('restore',restore_mode('original','candidate','candidate'))
        self.assertEqual('already_restored',restore_mode('original','original','candidate'))
        with self.assertRaisesRegex(RuntimeError,'Unknown'):restore_mode('original','other','candidate')
    def test_requires_single_complete_structured_record(self):
        line='INSTRUMENTATION_RESULT: report_json={"passed":true}'
        self.assertEqual({'passed':True},parse_raw(line))
        for raw in ['formatted summary only',line+'\n'+line,'INSTRUMENTATION_RESULT: report_json={']:
            with self.subTest(raw=raw),self.assertRaises((RuntimeError,ValueError)):parse_raw(raw)
    def test_runner_attributes_do_not_leak_from_other_manifest_elements(self):
        tree='''E: manifest (line=1)
  E: instrumentation (line=2)
    A: android:name(0x01010003)="safe.Runner"
    A: android:targetPackage(0x01010021)="safe.target"
  E: application (line=3)
    E: uses-library (line=4)
      A: android:name(0x01010003)="unrelated.library"
'''
        self.assertEqual([{'name':'safe.Runner','targetPackage':'safe.target'}],instrumentation_entries(tree))
        duplicate=tree.replace('  E: application','    A: android:name(0x01010003)="second.Runner"\n  E: application')
        with self.assertRaisesRegex(RuntimeError,'Duplicate'):instrumentation_entries(duplicate)

if __name__=='__main__':unittest.main()
