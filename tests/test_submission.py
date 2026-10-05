"""Check repository structure, package imports, numerical identities and output safety."""
from fractions import Fraction as F
import ast
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'examples'), str(ROOT)]
import _common
import generate_artifacts as bundle
from bics.tcell import coarse_from_competing_rates, response_metrics

class SubmissionTests(unittest.TestCase):
    def test_package_modules_import(self):
        for path in (ROOT/'src/bics').glob('*.py'):
            if path.stem != '__init__':
                importlib.import_module('bics.'+path.stem)

    def test_tcell_independent_information_calculation(self):
        def entropy(p):
            return sum(-x*math.log2(x) for x in (p,1-p) if x)
        for n in (1,2,3,4,8):
            a,b=F(1,11)**n,F(10,11)**n
            result=response_metrics(a,b,F(1,2))
            numerical=entropy(float((a+b)/2))-(entropy(float(a))+entropy(float(b)))/2
            exact=result['information_bits']
            self.assertAlmostEqual(float((exact.lo+exact.hi)/2),numerical,places=13)
            self.assertEqual(result['completion_ratio'],10**n)
            self.assertEqual(result['bayes_error'],(1-b+a)/2)

    def test_pathway_rates(self):
        self.assertEqual(coarse_from_competing_rates(F(1),F(10)),F(1,11))
        self.assertEqual(coarse_from_competing_rates(F(1),F(1,10)),F(10,11))

    def test_all_imported_local_modules_live_in_src(self):
        self.test_package_modules_import()
        for name,module in list(sys.modules.items()):
            if name.startswith('bics.') and getattr(module,'__file__',None):
                self.assertTrue(Path(module.__file__).resolve().is_relative_to(ROOT/'src/bics'),name)

    def test_runs_root_symlink_cannot_target_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'repo';(root/'artifacts').mkdir(parents=True)
            try:(root/'runs').symlink_to(root/'artifacts',target_is_directory=True)
            except OSError:self.skipTest('Symlinks unavailable')
            with patch.object(_common,'ROOT',root),self.assertRaises(ValueError):
                _common.prepare_out(root/'runs'/'new')

    def test_standalone_report_preserves_published_files(self):
        for name in ('artifacts/report.json','src/report.json','data/report.json'):
            with self.assertRaises(ValueError):_common.validate_output_file(ROOT/name)
        with tempfile.TemporaryDirectory() as d:
            out=_common.validate_output_file(Path(d)/'report.json');out.write_text('saved')
            with self.assertRaises(FileExistsError):_common.validate_output_file(out)
            self.assertEqual(out.read_text(),'saved')

    def test_tool_commands_have_help(self):
        for name in ('process_msn2_fluorescence.py','verify_msn2_derived.py'):
            result=subprocess.run([sys.executable,str(ROOT/'tools'/name),'--help'],capture_output=True,text=True,cwd='/tmp')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('--out',result.stdout)

    def test_documentation_links_resolve(self):
        paths=[*ROOT.glob('*.md')]
        for d in ('docs','examples','src','data','provenance','artifacts'):paths.extend((ROOT/d).rglob('*.md'))
        for p in paths:
            for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if '://' in link or link.startswith('#'):continue
                target=(p.parent/link.split('#')[0]).resolve()
                self.assertTrue(target.exists(),str(p)+': '+link)

    def test_source_inventory_complete(self):
        manifest=json.loads((ROOT/'provenance/source_manifest.json').read_text())
        known={r['path'] for r in manifest['files']}
        for d in ('src','examples','tools','tests'):
            for p in (ROOT/d).rglob('*.py'):
                self.assertIn(p.relative_to(ROOT).as_posix(),known)

    def test_public_instructions_are_current(self):
        paths=list(ROOT.glob('*.md'))
        for d in ('docs','examples','src','data','provenance','artifacts'):paths.extend((ROOT/d).rglob('*.md'))
        for p in paths:
            self.assertIsNone(re.search(r'\b(?:earlier|historical|draft|drafting|legacy)\b|preserved original|reviewed functions',p.read_text(),re.I),str(p))

    def test_indexes_generated_from_results(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            for folder,_,_,tables,_,_ in bundle.EXAMPLES:
                (out/folder).mkdir()
                for name in tables:shutil.copyfile(ROOT/'artifacts'/folder/name,out/folder/name)
            bundle.write_index(out)
            for p in out.rglob('*.md'):
                self.assertEqual(p.read_bytes(),(ROOT/'artifacts'/p.relative_to(out)).read_bytes())

if __name__=='__main__':unittest.main()
