#!/usr/bin/env python3
"""Reproduce primary manuscript calculations using the preserved analysis programs."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from verify_archive import verify

ROOT = Path(__file__).resolve().parent
WS = ROOT / 'workstreams'


def run(script: Path, args: list[str], log: Path) -> None:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg')
    with log.open('w', encoding='utf-8') as handle:
        process = subprocess.run([sys.executable, str(script), *args], cwd=ROOT,
                                 env=env, stdout=handle, stderr=subprocess.STDOUT)
    if process.returncode:
        raise RuntimeError(f'{script.name} failed. Read {log}.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New or empty output directory.')
    parser.add_argument('--figures', action='store_true', help='Also reproduce the three figures.')
    parser.add_argument('--strict-bytes', action='store_true', help='Require exact reference JSON bytes.')
    args = parser.parse_args()
    out = args.out.resolve()
    if out == ROOT or out.is_relative_to(WS) or out.is_relative_to(ROOT / '.git') or ROOT.is_relative_to(out):
        parser.error('Choose an output directory separate from source and reference files.')
    integrity = verify(ROOT, json.loads((ROOT / 'provenance/import_manifest.json').read_text()))
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error('Output directory must be new or empty.')
    out.mkdir(parents=True, exist_ok=True)
    script = WS / 'paper1_checkpoint_2026-09-23/verification_2026-10-02/reproduce_primary_panel.py'
    run(script, ['--out', str(out / 'primary')], out / 'primary.log')
    numerical = json.loads((out / 'primary/verification_summary.json').read_text())
    if numerical.get('status') != 'PASS':
        raise AssertionError('Primary numerical verification did not pass.')
    reference = json.loads((ROOT / 'reference_results/expected_information_sha256.json').read_text())['outputs']
    comparisons = {}
    for name in ('decision_comparison.json', 'information_panel.json', 'information_reveal.json'):
        generated = (out / 'primary/information' / name).read_bytes()
        digest = hashlib.sha256(generated).hexdigest()
        comparisons[name] = {'byte_identical': digest == reference[name],
                             'generated_sha256': digest,
                             'archived_sha256': reference[name]}
    if args.figures:
        figures = out / 'figures'
        figures.mkdir()
        # The original program writes beside itself. Copy it unchanged so that
        # generated images stay outside the source tree and reference files.
        target = figures / 'make_manuscript_figures.py'
        shutil.copyfile(WS / 'paper1_checkpoint_2026-09-23/scripts/make_manuscript_figures.py', target)
        run(target, [], out / 'figures.log')
        if len(list(figures.glob('Figure*.png'))) != 3:
            raise AssertionError('Expected three generated figure images.')
    report = {'integrity': integrity, 'numerical_verification': numerical,
              'reference_byte_comparison': comparisons,
              'scope': 'Starts from archived primary binary counts. Raw fluorescence processing and alternate thresholds are separate commands.',
              'python': sys.version,
              'packages': {p: importlib.metadata.version(p) for p in ('numpy', 'scipy', 'mpmath', 'matplotlib')}}
    (out / 'run_manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if args.strict_bytes and not all(x['byte_identical'] for x in comparisons.values()):
        raise AssertionError('Reference bytes differ. See run_manifest.json; archived files were preserved.')


if __name__ == '__main__':
    main()
