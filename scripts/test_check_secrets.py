"""Synthetic credential boundaries and index-only scanning; no credentials or Git writes."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('secret_checker', Path(__file__).with_name('check_secrets.py'))
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def detected(payload):
    return any(pattern.search(payload) for pattern in CHECKER.PATTERNS)


def synthetic_tokens():
    # Construct shapes in memory so this test source does not look like a secret.
    return [b'sk-' + b'A' * 24, b'sk-proj-' + b'P' * 30,
            b'sk-svcacct-' + b'S' * 30, b'github_pat_' + b'G' * 40,
            *[b'gh' + kind + b'_' + b'T' * 32 for kind in [b'p', b'o', b'u', b's', b'r']]]


class CredentialBoundaries(unittest.TestCase):
    def test_known_path_words_and_document_links_are_not_tokens(self):
        for payload in [b'prototype/task-draft-v21-compatible/README.md',
                        b'[research](../prototype/task-draft-v21-compatible/qualification.json)',
                        b'https://example.test/prototype/task-draft-v21-compatible/README.md',
                        b'"prototype/task-draft-v21-compatible/author-review.json"']:
            self.assertFalse(detected(payload))

    def test_standalone_assignment_quotes_and_url_tokens_remain_detected(self):
        prefixes = [b'', b'API_KEY=', b'export TOKEN="', b"'", b'Bearer ', b'(',
                    b'https://example.test/?key=', b'https://example.test/keys/',
                    b'https://user:']
        for token in synthetic_tokens():
            for prefix in prefixes:
                with self.subTest(prefix=prefix, token_kind=token.split(b'-')[0].split(b'_')[0]):
                    self.assertTrue(detected(prefix + token + b'"&next=value'))

    def test_embedded_identifier_or_hyphenated_word_prefix_is_not_a_token(self):
        for token in synthetic_tokens():
            for prefix in [b'a', b'9', b'_', b'branch-', b'task-']:
                self.assertFalse(detected(prefix + token))

    def test_real_token_after_benign_path_is_still_scanned(self):
        payload = b'prototype/task-draft-v21-compatible/README.md key=' + synthetic_tokens()[0]
        self.assertTrue(detected(payload))

    def test_binary_blob_delimiter_and_private_key_markers_remain_detected(self):
        self.assertTrue(detected(b'\x00\xff' + synthetic_tokens()[0] + b'\x00'))
        for kind in [b'', b'RSA ', b'EC ', b'OPENSSH ']:
            marker = b'-----BEGIN ' + kind + b'PRIVATE KEY' + b'-----'
            self.assertTrue(detected(marker))


class IndexScanning(unittest.TestCase):
    def run_index(self, blobs):
        calls = []

        def git_output(command):
            calls.append(command)
            if command == ['git', 'ls-files', '-z']:
                return b'\0'.join(name.encode() for name in blobs) + b'\0'
            if command[:2] == ['git', 'show'] and command[2].startswith(':'):
                return blobs[command[2][1:]]
            raise AssertionError('Expected only index reads')

        out = io.StringIO(); err = io.StringIO()
        with patch.object(CHECKER.subprocess, 'check_output', side_effect=git_output), redirect_stdout(out), redirect_stderr(err):
            code = CHECKER.main()
        return code, out.getvalue(), err.getvalue(), calls

    def test_path_only_index_passes(self):
        code, out, err, _ = self.run_index({'docs/research.md': b'prototype/task-draft-v21-compatible/README.md'})
        self.assertEqual(code, 0)
        self.assertIn('passed', out)
        self.assertEqual(err, '')

    def test_credential_fails_without_disclosing_value_and_reads_index(self):
        token = synthetic_tokens()[0]
        code, out, err, calls = self.run_index({'docs/example.md': b'KEY=' + token})
        self.assertEqual(code, 1)
        self.assertIn('docs/example.md: possible secret', err)
        self.assertNotIn(token.decode(), out + err)
        self.assertEqual(calls, [['git', 'ls-files', '-z'], ['git', 'show', ':docs/example.md']])

    def test_env_model_and_private_artifact_blocks_remain_intact(self):
        code, _, err, calls = self.run_index({'.env': b'', 'models/test.gguf': b'', 'artifacts/private.json': b''})
        self.assertEqual(code, 1)
        self.assertEqual(err.count('prohibited file'), 3)
        self.assertEqual(calls, [['git', 'ls-files', '-z']])

    def test_env_example_and_artifact_placeholder_exceptions_are_still_scanned(self):
        token = synthetic_tokens()[0]
        code, _, err, _ = self.run_index({'.env.example': b'KEY=' + token, 'artifacts/.gitkeep': b''})
        self.assertEqual(code, 1)
        self.assertIn('.env.example: possible secret', err)
        self.assertNotIn('prohibited file', err)


if __name__ == '__main__':
    unittest.main()
