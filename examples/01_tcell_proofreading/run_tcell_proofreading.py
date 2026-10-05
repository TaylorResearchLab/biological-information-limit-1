#!/usr/bin/env python3
"""Example 1. Reproduce T cell receptor proofreading (Table 1 and Figure 1)."""
from pathlib import Path
from fractions import Fraction as F
import sys
import time
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import (WS, arguments, prepare_out, verify_sources, write_csv,
                     write_json, check_table, run_script, finish, entry)
HERE = Path(__file__).resolve().parent


def main():
    started = time.perf_counter()
    args = arguments(__doc__, 'tcell')
    sources = verify_sources(('workstreams/transfer_proofreading_v0_1/',
                              'workstreams/paper1_checkpoint_2026-09-23/scripts/run_tcr_reference.py'))
    out = prepare_out(args.out)
    original = WS / 'transfer_proofreading_v0_1'
    sys.path[:0] = [str(original / 'src'), str(original / 'reference')]
    from proofreading import coarse_from_competing_rates, response_metrics, build
    # The same illustrative rates and equally weighted inputs as the archived driver.
    kp, off_self, off_agonist = F(1), F(10), F(1, 10)
    alpha_self = coarse_from_competing_rates(kp, off_self)
    alpha_agonist = coarse_from_competing_rates(kp, off_agonist)
    depths = (1, 2, 3, 4, 8)
    rows, exact_rows = [], []
    for n in depths:
        m = response_metrics(alpha_self**n, alpha_agonist**n, F(1, 2))
        info = m['information_bits']
        rows.append({'proofreading_steps': n, 'agonist_completion_probability': float(m['success_agonist']),
                     'agonist_self_completion_ratio': int(m['completion_ratio']),
                     'equal_prior_classification_error': float(m['bayes_error']),
                     'mutual_information_bits': float((info.lo + info.hi)/2)})
        exact_rows.append({'proofreading_steps': n, 'self_completion_probability': str(m['success_self']),
                           'agonist_completion_probability': str(m['success_agonist']),
                           'completion_ratio': str(m['completion_ratio']), 'bayes_error': str(m['bayes_error']),
                           'information_bits_enclosure': info.decimal(18)})
    write_csv(out / 'table_1_tcell_proofreading.csv', rows)
    write_json(out / 'exact_results.json', exact_rows)
    # Inspect the existing sequential model: after survival, later steps still depend on ligand class.
    model = build([alpha_self]*2, [alpha_agonist]*2)
    later = model.motifs[2]
    if later.rows[(0, 1)][(1,)] != alpha_self or later.rows[(1, 1)][(1,)] != alpha_agonist:
        raise AssertionError('Continuing ligand dependence changed')
    write_json(out / 'ligand_dependence.json', {
        'scope': 'Conditional progression laws in the preserved two-step model; not a trajectory information calculation.',
        'second_step_given_first_completed': {'self': str(alpha_self), 'agonist': str(alpha_agonist)},
        'input_independent_reduction_valid': alpha_self == alpha_agonist})
    run_script(WS / 'paper1_checkpoint_2026-09-23/scripts/run_tcr_reference.py', [], out / 'run.log')
    import csv
    with (out / 'run.log').open() as handle:
        archived_driver = list(csv.DictReader(handle, delimiter='\t'))
    for row, direct in zip(rows, archived_driver):
        actual = [row[k] for k in row]
        wanted = [float(direct[k]) for k in direct]
        if len(actual) != len(wanted) or any(abs(float(a)-b) > 1e-12 for a,b in zip(actual,wanted)):
            raise AssertionError('Table differs from preserved driver')
    if len(archived_driver) != len(rows):
        raise AssertionError('Preserved driver row count differs')
    checks = {'table_1_rows': check_table(out, 'table_1_tcell_proofreading.csv', HERE),
              'preserved_driver_agreement': True, 'continuing_ligand_dependence': True}
    if not args.skip_figures:
        from _plot import tcell
        tcell(out)
    finish(out, {'example': 'T cell receptor proofreading', 'source_doi': '10.1073/pnas.92.11.5042',
                 'scope': 'A single already-bound encounter; binary completion outcome.',
                 'progression_rate_relative_units': str(kp), 'self_dissociation_rate': str(off_self),
                 'agonist_dissociation_rate': str(off_agonist), 'self_step_passage': str(alpha_self),
                 'agonist_step_passage': str(alpha_agonist), 'agonist_input_probability': '1/2',
                 'proofreading_steps': list(depths)}, checks, sources, started)

if __name__ == '__main__':
    entry(main)
