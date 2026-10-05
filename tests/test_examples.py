"""Tests for example file handling, naming and reference integrity."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples'))
from _common import check_rows, prepare_out


class ExampleTests(unittest.TestCase):
    def test_exact_and_numeric_comparison(self):
        self.assertEqual(check_rows([{'label':'x','n':'2','value':'0.5000000000001'}],
                                    [{'label':'x','n':'2','value':'0.5'}]),1)

    def test_changed_value_rejected(self):
        with self.assertRaises(AssertionError):
            check_rows([{'x':'0.6'}],[{'x':'0.5'}])

    def test_nonfinite_rejected(self):
        for value in ('NaN','inf','-inf'):
            with self.assertRaises(AssertionError):
                check_rows([{'x':value}],[{'x':'0.5'}])

    def test_missing_row_or_field_rejected(self):
        with self.assertRaises(AssertionError):
            check_rows([],[{'x':'1'}])
        with self.assertRaises(AssertionError):
            check_rows([{'y':'1'}],[{'x':'1'}])

    def test_source_destinations_rejected(self):
        for p in (ROOT, ROOT.parent, ROOT/'src/new',ROOT/'examples/new', ROOT/'runs'):
            with self.assertRaises(ValueError):
                prepare_out(p)

    def test_nonempty_output_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'result';prepare_out(p);(p/'keep.txt').write_text('keep')
            with self.assertRaises(FileExistsError):prepare_out(p)
            self.assertEqual((p/'keep.txt').read_text(),'keep')

    def test_symlink_into_sources_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            link=Path(directory)/'source_link'
            try:link.symlink_to(ROOT/'examples',target_is_directory=True)
            except OSError:self.skipTest('Symlinks unavailable')
            with self.assertRaises(ValueError):prepare_out(link/'new_output')

    def test_three_scripts_have_help(self):
        for folder,script in [('01_tcell_proofreading','run_tcell_proofreading.py'),
                              ('02_ribosome_selection','run_ribosome_selection.py'),
                              ('03_msn2_reporters','run_msn2_reporters.py')]:
            p=ROOT/'examples'/folder/script
            result=subprocess.run([sys.executable,str(p),'--help'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('--out',result.stdout)
            self.assertTrue((p.parent/'README.md').is_file())

    def test_example_manifest(self):
        records=json.loads((ROOT/'provenance/source_manifest.json').read_text())['files']
        for row in records:
            p=ROOT/row['path']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'],row['path'])

if __name__=='__main__':unittest.main()
