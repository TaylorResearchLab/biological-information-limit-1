#!/usr/bin/env python3
"""Example 1. Reproduce T cell receptor proofreading (Table 1 and Figure 1)."""
from pathlib import Path
from fractions import Fraction as F
import sys
import time
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import (ROOT, arguments, prepare_out, verify_sources, write_csv,
                     write_json, check_table, run_script, finish, entry)
HERE = Path(__file__).resolve().parent


def main():
    started = time.perf_counter()
    args = arguments(__doc__, 'tcell')
    sources = verify_sources(('src/bics/',))
    out = prepare_out(args.out)
    from bics.tcell import coarse_from_competing_rates, response_metrics, build
    # McKeithan's illustrative rates with equally weighted ligand classes.
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
    # Inspect the sequential model: after survival, later steps still depend on ligand class.
    model = build([alpha_self]*2, [alpha_agonist]*2)
    later = model.motifs[2]
    if later.rows[(0, 1)][(1,)] != alpha_self or later.rows[(1, 1)][(1,)] != alpha_agonist:
        raise AssertionError('Continuing ligand dependence changed')
    write_json(out / 'ligand_dependence.json', {
        'scope': 'Conditional progression laws in the two-step model, conditional on completion of the first step.',
        'second_step_given_first_completed': {'self': str(alpha_self), 'agonist': str(alpha_agonist)},
        'input_independent_reduction_valid': alpha_self == alpha_agonist})
    (out / 'run.log').write_text('Calculated five proofreading depths from specified rates.\n')
    checks = {'table_1_rows': check_table(out, 'table_1_tcell_proofreading.csv', HERE),
              'continuing_ligand_dependence': True}
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
