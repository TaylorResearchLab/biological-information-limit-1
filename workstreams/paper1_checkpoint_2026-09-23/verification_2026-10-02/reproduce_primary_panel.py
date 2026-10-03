#!/usr/bin/env python3
"""Verify manuscript calculations using preserved source and archived binary counts.

This entry starts after fluorescence preprocessing. To repeat preprocessing, run
analyze_msn2.py with the original publisher archive as described in README.md.
All original scientific source modules are used without edits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from itertools import combinations
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'workstreams').is_dir())
WS = ROOT / 'workstreams'


def capture(script: Path, args: list[str], log: Path) -> None:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run([sys.executable, str(script), *args], cwd=ROOT,
                          env=env, text=True, capture_output=True)
    log.write_text(proc.stdout + proc.stderr, encoding='utf-8')
    if proc.returncode:
        raise RuntimeError(f'{script.name} failed; see {log}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Use a new or empty output directory.')
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text())
    for entry in manifest['files']:
        path = ROOT / entry['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f'File hash mismatch: {entry["path"]}')
    sys.path.insert(0, str(WS / 'msn2_pairing_2026-09-23/src'))
    from analyze_msn2 import CONDITIONS, REFERENCES, analyze_counts, write_json, verify_solver
    verify_solver()
    rows = json.loads((HERE / 'primary_condition_counts.json').read_text())
    indexed = {(r['construct'], r['condition']): r['counts_00_01_10_11'] for r in rows}
    if len(indexed) != 34:
        raise ValueError('Expected 34 distinct primary condition records.')
    records = []
    for construct, total in [('1x', 21236), ('2x', 19222)]:
        if sum(sum(indexed[(construct, c)]) for c in CONDITIONS) != total:
            raise ValueError('Archived condition counts do not match the manuscript total.')
        for c0, c1 in combinations(CONDITIONS, 2):
            r = analyze_counts(indexed[(construct, c0)], indexed[(construct, c1)])
            r.update(scheme='primary_median', construct=construct, condition0=c0, condition1=c1)
            r['reference_contrast'] = next((name for name, a, b in REFERENCES if (a, b) == (c0, c1)), None)
            records.append(r)
    input_path = out / 'primary_pair_results.json'
    write_json(input_path, records)
    scripts = WS / 'paper1_checkpoint_2026-09-23/scripts'
    capture(scripts / 'run_tcr_reference.py', [], out / 'tcr.tsv')
    capture(scripts / 'run_ribosome_reference.py', [], out / 'ribosome.txt')
    capture(WS / 'ribosome_separate_output_2026-09-24/src/evaluate_separate_output.py',
            [str(out / 'separate_output.json')], out / 'separate_output.log')
    capture(WS / 'method_comparison_2026-09-23/src/run_comparison.py',
            ['--inputs', str(input_path), '--out', str(out / 'information')], out / 'information.log')
    info = json.loads((out / 'information/summary.json').read_text())
    if info['primary_cases'] != 272 or info['new_linear_programs'] != 544 or info['max_lp_discrepancy'] > 1e-9:
        raise AssertionError('Primary panel or independent LP checks changed.')
    expected = [0.560503, 0.612789, 0.546158, 0.475227, 0.285260]
    tcr_rows = (out / 'tcr.tsv').read_text().strip().splitlines()[1:]
    if len(tcr_rows) != 5 or any(abs(float(line.split('\t')[-1])-value) > 5e-7 for line, value in zip(tcr_rows, expected)):
        raise AssertionError('TCR information no longer matches Table 1.')
    separate = json.loads((out / 'separate_output.json').read_text())
    threshold = separate['rate_free_late_stage']['U_threshold_for_guaranteed_res_lt_wt_under_one_uncertainty_family']
    if abs(threshold-3.6) > 1e-12:
        raise AssertionError('Separate-output threshold changed.')
    panel = {r['case_id']: r for r in json.loads((out / 'information/information_panel.json').read_text())}
    table4 = {
        '1x|DM_70min_100nM|DM_70min_3uM': (0.618, 0.944, 0.776),
        '1x|DM_70min_175nM|FM7_786minINT_690nM': (0.009, 0.916, 0.014),
        '2x|FM7_786minINT_690nM|FM8_625minINT_690nM': (0.008, 0.727, 0.009)}
    for case, expected_values in table4.items():
        item = panel[case]
        actual = [item['information_bounds']['minimum']['bits_enclosure']['lower'],
                  item['information_bounds']['maximum']['bits_enclosure']['upper'],
                  item['observed_bits']['lower']]
        if any(abs(float(a)-b) > 0.0005 for a, b in zip(actual, expected_values)):
            raise AssertionError(f'Table 4 changed: {case}')
    table5 = {(False, False): (0.009, 0.916), (True, False): (0.013, 0.396),
              (False, True): (0.012, 0.281), (True, True): (0.014, 0.014)}
    for item in json.loads((out / 'information/information_reveal.json').read_text()):
        actual = [item['information_bounds']['minimum']['bits_enclosure']['lower'],
                  item['information_bounds']['maximum']['bits_enclosure']['upper']]
        if any(abs(float(a)-b) > 0.0005 for a, b in zip(actual, table5[tuple(item['pairing_retained'])])):
            raise AssertionError('Table 5 changed.')
    rib = WS / 'research_update_2026-09-23/ribosome_boundary'
    sys.path[:0] = [str(rib / 'src'), str(rib / 'reference')]
    from ribosome_boundary import AcceptanceBox, info_bounds, assembly_metrics
    ribosome_values = {}
    for name, near, expected_bounds in [('WT', ('.048', '.052'), (0.616, 0.859)),
                                         ('restrictive', ('.002', '.012'), (0.713, 0.990))]:
        bounds = info_bounds(AcceptanceBox((F('.9'), F(1)), tuple(map(F, near))), F(1, 2))
        values = [float(bounds['minimum_information_bits'].lo), float(bounds['maximum_information_bits'].hi)]
        if any(abs(a-b) > 0.0005 for a, b in zip(values, expected_bounds)):
            raise AssertionError(f'Table 2 changed: {name}')
        ribosome_values[name] = values
    passage_values = []
    for epsilon, expected_bits in [(F(1), 0.825381), (F(1, 10), 0.046549), (F(1, 100), 0.004502)]:
        val = assembly_metrics(epsilon, epsilon, F('.95'), F('.007'), F(1, 2))['terminal_information_bits']
        bits = float((val.lo+val.hi)/2)
        if abs(bits-expected_bits) > 0.0000005:
            raise AssertionError('Table 3 changed.')
        passage_values.append(bits)
    report = {'status': 'PASS', 'scope': 'Reproduction from archived primary binary counts; source fluorescence preprocessing was not rerun.',
              'primary_comparisons': 272, 'linear_programs': 544, 'max_lp_discrepancy': info['max_lp_discrepancy'],
              'tcr_table_information_matches': True, 'msn2_tables_4_and_5_match': True, 'ribosome_drivers_completed': True, 'ribosome_tables_2_and_3_match': True,
              'ribosome_local_bounds': ribosome_values, 'passage_control_bits': passage_values,
              'separate_output_U_threshold': threshold, 'python': sys.version}
    (out / 'verification_summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
