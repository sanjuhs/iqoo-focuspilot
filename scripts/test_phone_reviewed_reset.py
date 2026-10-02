import subprocess
import unittest
from unittest.mock import patch
from phone_reviewed_reset import require_test_application_absent

class Lab:
    base=['adb','-s','synthetic']

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

if __name__=='__main__':unittest.main()
