import subprocess
import unittest
from unittest.mock import patch
from phone_reviewed_reset import require_test_application_absent

class Lab:
    base=['adb','-s','synthetic']
    def adb(self,*args):return 'abc123  /synthetic/base.apk\n'

class TestApplicationBoundary(unittest.TestCase):
    def test_absent_package_may_return_one_with_no_output(self):
        with patch('phone_reviewed_reset.subprocess.run',return_value=subprocess.CompletedProcess([],1,'','')):
            require_test_application_absent(Lab())
    def test_existing_package_never_replaced(self):
        with patch('phone_reviewed_reset.subprocess.run',return_value=subprocess.CompletedProcess([],0,'package:/synthetic/base.apk\n','')):
            with self.assertRaisesRegex(RuntimeError,'Existing test application'):require_test_application_absent(Lab())
    def test_transport_error_does_not_imply_absence(self):
        for code,err in [(2,''),(1,'device offline'),(0,'permission denied')]:
            with self.subTest(code=code,err=err):
                with patch('phone_reviewed_reset.subprocess.run',return_value=subprocess.CompletedProcess([],code,'',err)):
                    with self.assertRaisesRegex(RuntimeError,'Cannot establish'):require_test_application_absent(Lab())
    def test_explicit_reuse_requires_exact_installed_hash(self):
        with patch('phone_reviewed_reset.subprocess.run',return_value=subprocess.CompletedProcess([],0,'package:/data/app/synthetic/base.apk\n','')):
            self.assertTrue(require_test_application_absent(Lab(),reuse_sha='abc123'))
            with self.assertRaisesRegex(RuntimeError,'differs'):require_test_application_absent(Lab(),reuse_sha='different')
    def test_explicit_reuse_rejects_ambiguous_path(self):
        for path in ['package:/unexpected/base.apk','package:/data/app/one.apk\npackage:/data/app/two.apk']:
            with self.subTest(path=path):
                with patch('phone_reviewed_reset.subprocess.run',return_value=subprocess.CompletedProcess([],0,path,'')):
                    with self.assertRaisesRegex(RuntimeError,'path is not exact'):require_test_application_absent(Lab(),reuse_sha='abc123')

if __name__=='__main__':unittest.main()
