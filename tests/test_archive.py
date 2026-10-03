"""Tests of public archive verification, separate from the scientific tests."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from verify_archive import verify


def entry(name, data):
    return {'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}


class ArchiveTests(unittest.TestCase):
    def test_valid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = b'x = 1\n'; (root / 'code.py').write_bytes(data)
            self.assertEqual(verify(root, {'files': [entry('code.py', data)]})['python_sources'], 1)

    def test_changed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'code.py').write_bytes(b'x = 2\n')
            with self.assertRaises(ValueError):
                verify(root, {'files': [entry('code.py', b'x = 1\n')]})

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                verify(Path(tmp), {'files': [entry('missing.py', b'x=1\n')]})

    def test_duplicate_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = b'x=1\n'; (root / 'code.py').write_bytes(data)
            with self.assertRaises(ValueError):
                verify(root, {'files': [entry('code.py', data), entry('code.py', data)]})

    def test_parent_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                verify(Path(tmp), {'files': [entry('../outside.py', b'x=1\n')]})

    def test_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = b'bad syntax =\n'; (root / 'code.py').write_bytes(data)
            with self.assertRaises(SyntaxError):
                verify(root, {'files': [entry('code.py', data)]})


if __name__ == '__main__':
    unittest.main()
