"""Packaging tests. Scientific reference checks remain in each example."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'examples'))
import _common
import generate_artifacts as bundle


class OutputSafety(unittest.TestCase):
    def test_reserved_directories(self):
        for relative in ('artifacts', 'artifacts/new', 'examples/new', 'src/new', 'runs'):
            with self.subTest(path=relative), self.assertRaises(ValueError):
                _common.prepare_out(ROOT / relative)

    def test_root_and_ancestors(self):
        for path in (ROOT, ROOT.parent):
            with self.assertRaises(ValueError):
                _common.prepare_out(path)

    def test_external_output_and_repeat_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            out = _common.prepare_out(Path(directory) / 'a path with spaces')
            marker = out / 'keep.txt'
            marker.write_text('original')
            with self.assertRaises(FileExistsError):
                _common.prepare_out(out)
            self.assertEqual(marker.read_text(), 'original')

    def test_existing_file_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'file.txt'
            path.write_text('original')
            with self.assertRaises(FileExistsError):
                _common.prepare_out(path)

    def test_symlink_to_protected_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'repo'
            (root / 'artifacts').mkdir(parents=True)
            (root / 'runs').mkdir()
            try:
                (root / 'runs' / 'link').symlink_to(root / 'artifacts', target_is_directory=True)
            except OSError:
                self.skipTest('Symlink unavailable')
            with patch.object(_common, 'ROOT', root), self.assertRaises(ValueError):
                _common.prepare_out(root / 'runs' / 'link' / 'new')


class PublishedArtifacts(unittest.TestCase):
    def test_saved_manifest_and_figures(self):
        saved = ROOT / 'artifacts'
        if not saved.exists():
            self.fail('Published artifacts directory is required')
        manifest = bundle.validate_bundle(saved)
        self.assertEqual((manifest['tables'], manifest['figures']), (5, 3))

    def test_generated_results_match_saved_results(self):
        location = os.environ.get('BICS_REGENERATED_ARTIFACTS')
        if not location:
            self.skipTest('Set by CI after regeneration')
        saved = ROOT / 'artifacts'
        generated = Path(location)
        old = bundle.validate_bundle(saved)
        new = bundle.validate_bundle(generated)
        self.assertEqual(set(old['files']), set(new['files']))
        compared = 0
        for name in old['files']:
            p = Path(name)
            # Run records contain elapsed time, environment details and absolute paths.
            if p.suffix not in ('.csv', '.json') or p.name in (
                    'verification.json', 'all_five_definitions_verification.json'):
                continue
            with self.subTest(file=name):
                self.assertEqual((saved / name).read_bytes(), (generated / name).read_bytes())
                compared += 1
        self.assertGreaterEqual(compared, 20)
        # Do not require cross-platform pixel identity; figure_data.json is compared above.


if __name__ == '__main__':
    unittest.main()
