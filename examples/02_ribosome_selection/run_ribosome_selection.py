#!/usr/bin/env python3
"""Example 2. Reproduce ribosome selection (Tables 2-3, Figure 2 and product-assay threshold)."""
from pathlib import Path
from fractions import Fraction as F
import json
import sys
import time
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import (ROOT, arguments, prepare_out, verify_sources, write_csv,
                     write_json, check_table, run_script, finish, entry)
HERE = Path(__file__).resolve().parent


def main():
    started = time.perf_counter()
    args = arguments(__doc__, 'ribosome')
    sources = verify_sources(('src/bics/',))
    out = prepare_out(args.out)
    from bics.ribosome import AcceptanceBox, info_bounds, assembly_metrics
    boxes = {'wild_type': AcceptanceBox((F('.9'), F(1)), (F('.048'), F('.052'))),
             'restrictive': AcceptanceBox((F('.9'), F(1)), (F('.002'), F('.012')))}
    local, sensitivity, exact = [], [], []
    for q in (F(1,2), F(1,10), F(1,100)):
        for name, box in boxes.items():
            result = info_bounds(box, q)
            row = {'ribosome_preparation': name, 'near_cognate_input_probability': float(q),
                   'cognate_acceptance_min': float(box.cognate[0]), 'cognate_acceptance_max': float(box.cognate[1]),
                   'near_cognate_acceptance_min': float(box.near_cognate[0]),
                   'near_cognate_acceptance_max': float(box.near_cognate[1]),
                   'information_min_bits': float(result['minimum_information_bits'].lo),
                   'information_max_bits': float(result['maximum_information_bits'].hi)}
            sensitivity.append(row)
            if q == F(1,2):
                local.append(row)
            exact.append({'ribosome_preparation': name, 'near_cognate_input_probability': str(q),
                          'minimum_information_bits': result['minimum_information_bits'].decimal(18),
                          'maximum_information_bits': result['maximum_information_bits'].decimal(18)})
    passage = []
    for epsilon in (F(1), F(1,10), F(1,100), F(1,1000)):
        result = assembly_metrics(epsilon, epsilon, F('.95'), F('.007'), F(1,2))
        interval = result['terminal_information_bits']
        passage.append({'passage_probability_both_classes': float(epsilon),
                        'terminal_information_bits': float((interval.lo+interval.hi)/2)})
    write_csv(out / 'table_2_ribosome_information.csv', local)
    write_csv(out / 'table_3_ribosome_passage.csv', passage[:3])
    write_csv(out / 'source_frequency_sensitivity.csv', sensitivity)
    write_csv(out / 'extended_passage_sweep.csv', passage)
    write_json(out / 'local_information_enclosures.json', exact)
    run_script('bics.ribosome_product',
               [str(out / 'separate_product_assay.json')], out / 'run.log')
    product = json.loads((out / 'separate_product_assay.json').read_text())
    threshold = product['rate_free_late_stage']['U_threshold_for_guaranteed_res_lt_wt_under_one_uncertainty_family']
    if abs(threshold-3.6) > 1e-12:
        raise AssertionError('Separate product-assay threshold changed')
    if any(r['information_max_bits'] >= .081 for r in sensitivity if r['near_cognate_input_probability'] == .01):
        raise AssertionError('Rare-source bound changed')
    checks = {'table_2_rows': check_table(out, 'table_2_ribosome_information.csv', HERE),
              'table_3_rows': check_table(out, 'table_3_ribosome_passage.csv', HERE),
              'source_frequency_rows': check_table(out, 'source_frequency_sensitivity.csv', HERE),
              'extended_passage_rows': check_table(out, 'extended_passage_sweep.csv', HERE),
              'separate_product_assay_U_threshold': threshold}
    if not args.skip_figures:
        from _plot import ribosome
        ribosome(out)
    finish(out, {'example': 'Ribosomal tRNA selection', 'source_doi': '10.1016/j.molcel.2010.06.009',
                 'scope': 'Information ranges across declared acceptance sensitivity families.',
                 'cognate_interval': ['9/10','1'], 'wild_type_near_interval': ['0.048','0.052'],
                 'restrictive_near_interval': ['0.002','0.012'], 'near_cognate_input_probabilities': ['1/2','1/10','1/100'],
                 'whole_encounter_cognate_acceptance': '0.95', 'whole_encounter_near_acceptance': '0.007',
                 'whole_encounter_near_prior': '1/2', 'equal_passage_probabilities': ['1','1/10','1/100','1/1000']},
           checks, sources, started)

if __name__ == '__main__':
    entry(main)
