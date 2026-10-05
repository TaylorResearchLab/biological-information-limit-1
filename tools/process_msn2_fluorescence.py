#!/usr/bin/env python3
"""Prepare Msn2 reporter features and binary response definitions from source fluorescence."""
import argparse
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples'))
from _common import entry, prepare_out, verify_sources
from bics.msn2 import run
from bics.pairing import run as reveal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    archive = args.archive.expanduser().resolve()
    if not archive.is_file():
        parser.error('Select the source fluorescence ZIP archive.')
    verify_sources(('src/bics/',))
    out = prepare_out(args.out)
    run(archive, out)
    reveal(out / 'pair_results.json', out / 'constraint_reveal.json')


if __name__ == '__main__':
    entry(main)
