"""Check public documentation and generated artifact indexes."""
from pathlib import Path
import json
import re
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import generate_artifacts as bundle


class DocumentationTests(unittest.TestCase):
    def test_public_prose_describes_the_paper_and_commands(self):
        paths = list(ROOT.glob('*.md'))
        for folder in ('docs', 'examples', 'artifacts'):
            paths.extend((ROOT / folder).rglob('*.md'))
        pattern = r'\b(?:earlier|historical|draft|drafting|legacy)\b|preserved original|reviewed functions'
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertIsNone(re.search(pattern, path.read_text(), re.I))

    def test_saved_indexes_match_the_generator(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            for folder, _, _, tables, _, _ in bundle.EXAMPLES:
                (out / folder).mkdir()
                for name in tables:
                    shutil.copyfile(ROOT / 'artifacts' / folder / name, out / folder / name)
            bundle.write_index(out)
            for path in out.rglob('*.md'):
                self.assertEqual(path.read_bytes(),
                                 (ROOT / 'artifacts' / path.relative_to(out)).read_bytes())

    def test_index_generator_identity(self):
        manifest = json.loads((ROOT / 'artifacts/artifact_manifest.json').read_text())
        self.assertEqual(manifest['documentation_generator_sha256'],
                         bundle.sha256(ROOT / 'generate_artifacts.py'))


if __name__ == '__main__':
    unittest.main()
