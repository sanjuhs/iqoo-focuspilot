import unittest
import build_exclusions as tool

class ExclusionTest(unittest.TestCase):
    def test_lexical_boundaries(self):
        source='// "ignored"\nchar c=\'"\'; String a="hello"; /* "ignored" */ String b="go\\nnow";'
        self.assertEqual(tool.java_strings(source),['hello','go\nnow'])
    def test_java_specific_escapes(self):
        self.assertEqual(tool.java_strings(r'"space\squote\"tab\tunicode\u0041octal\101"'),['space quote"tab\tunicodeAoctalA'])
    def test_invalid_escape(self):
        with self.assertRaises(ValueError): tool.java_strings(r'"bad\q"')

if __name__=='__main__': unittest.main()
