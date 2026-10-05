#!/usr/bin/env python3
"""Example 3. Reproduce Msn2 reporter comparisons (Tables 4-5, Figure 3 and 272 decision comparisons)."""
from pathlib import Path
from itertools import combinations
from fractions import Fraction as F
import json
import sys
import time
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import (ROOT, DATA, arguments, prepare_out, verify_sources, write_csv,
                     write_json, check_table, run_script, exact_reference, finish, entry)
HERE = Path(__file__).resolve().parent
TABLE4_IDS = ['1x|DM_70min_100nM|DM_70min_3uM',
              '1x|DM_70min_175nM|FM7_786minINT_690nM',
              '2x|FM7_786minINT_690nM|FM8_625minINT_690nM']
KEYS = ['construct','condition0','condition1','counts','reference_contrast','marginal_only_accuracy_bounds',
        'best_fixed_deterministic_worst_case','paired_accuracy','SIP18_MI_bits','HXK1_MI_bits',
        'paired_MI_bits','independence_completion_MI_bits']


def main():
    started = time.perf_counter()
    args = arguments(__doc__, 'msn2', full_derived=True)
    sources = verify_sources(('src/bics/', 'data/msn2/'))
    out = prepare_out(args.out)
    from bics.msn2 import CONDITIONS, REFERENCES, analyze_counts, verify_solver, encode
    verify_solver()
    counts = json.loads((DATA / 'msn2/condition_counts.json').read_text())
    indexed = {(r['construct'],r['condition']):r['counts_00_01_10_11']
               for r in counts if r['scheme']=='primary_median'}
    if len(indexed) != 34:
        raise AssertionError('Expected 34 primary count tables')
    records = []
    for construct in ('1x','2x'):
        for c0,c1 in combinations(CONDITIONS,2):
            r = analyze_counts(indexed[construct,c0], indexed[construct,c1])
            r.update(construct=construct, condition0=c0, condition1=c1)
            r['reference_contrast'] = next((name for name,a,b in REFERENCES if (a,b)==(c0,c1)),None)
            records.append(r)
    records = [encode(r) for r in records]
    write_json(out / 'primary_records.json', [{k:r[k] for k in KEYS} for r in records])
    comparisons = {'primary_records.json': exact_reference(out / 'primary_records.json', ROOT / 'artifacts/03_msn2_reporters/primary_records.json')}
    run_script('bics.comparison',
               ['--inputs',str(out / 'primary_records.json'),'--out',str(out / 'detailed_results')],out / 'run.log')
    for name in ('decision_comparison.json','information_panel.json','information_reveal.json','summary.json'):
        comparisons[name] = exact_reference(out / 'detailed_results' / name, ROOT / 'artifacts/03_msn2_reporters/detailed_results' / name)
    panel = {r['case_id']:r for r in json.loads((out / 'detailed_results/information_panel.json').read_text())}
    table4 = []
    for case in TABLE4_IDS:
        r=panel[case]
        table4.append({'comparison':case,
            'information_min_bits':float(r['information_bounds']['minimum']['bits_enclosure']['lower']),
            'information_max_bits':float(r['information_bounds']['maximum']['bits_enclosure']['upper']),
            'observed_paired_information_bits':float(r['observed_bits']['lower'])})
    reveals = json.loads((out / 'detailed_results/information_reveal.json').read_text())
    table5 = [{'pairing_sustained_retained':int(r['pairing_retained'][0]),
               'pairing_pulsed_retained':int(r['pairing_retained'][1]),
               'information_min_bits':float(r['information_bounds']['minimum']['bits_enclosure']['lower']),
               'information_max_bits':float(r['information_bounds']['maximum']['bits_enclosure']['upper'])} for r in reveals]
    decisions = [{'comparison':'|'.join(r[k] for k in ('construct','condition0','condition1')),
                  'accuracy_min':float(F(r['marginal_only_accuracy_bounds'][0]['exact'])),
                  'accuracy_max':float(F(r['marginal_only_accuracy_bounds'][1]['exact'])),
                  'observed_paired_accuracy':float(F(r['paired_accuracy']['exact'])),
                  'independence_accuracy':float(F(r['independence_completion_accuracy']['exact']))} for r in records]
    write_csv(out / 'table_4_msn2_information.csv',table4)
    write_csv(out / 'table_5_msn2_pairing.csv',table5)
    write_csv(out / 'all_272_discrimination_comparisons.csv',decisions)
    summary = json.loads((out / 'detailed_results/summary.json').read_text())
    if summary['primary_cases'] != 272 or summary['linear_programs'] != 544 or summary['max_lp_discrepancy'] > 1e-9:
        raise AssertionError('Primary comparison verification changed')
    checks = {'table_4_rows':check_table(out,'table_4_msn2_information.csv',HERE),
              'table_5_rows':check_table(out,'table_5_msn2_pairing.csv',HERE),
              'decision_rows':len(decisions), 'linear_programs':summary['linear_programs'],
              'max_lp_discrepancy':summary['max_lp_discrepancy'], 'reference_byte_checks':comparisons}
    if args.full_derived:
        run_script(ROOT / 'tools/verify_msn2_derived.py', ['--out',str(out / 'all_five_definitions_verification.json')],
                   out / 'full_derived.log')
        report = json.loads((out / 'all_five_definitions_verification.json').read_text())
        if report['status'] != 'PASS' or report['comparisons'] != 1360:
            raise AssertionError('Full derived archive did not pass')
        checks['full_derived'] = report
    if not args.skip_figures:
        from _plot import msn2
        msn2(out)
    finish(out, {'example':'Yeast Msn2 reporters', 'source_doi':'10.7554/eLife.06559',
                 'data_doi':'10.5061/dryad.97vt8', 'response_definition':'primary_median',
                 'inputs':'Two equally weighted protocols per comparison', 'input_prior':'1/2',
                 'response':'Binary SIP18 and HXK1 responses; count order 00,01,10,11',
                 'scope':'Starts from included binary counts. Raw fluorescence processing is a separate documented step.',
                 'full_derived_verification':args.full_derived}, checks, sources, started)

if __name__ == '__main__':
    entry(main)
