# Example 1. T cell receptor proofreading

**Run [run_tcell_proofreading.py](run_tcell_proofreading.py) to reproduce Table 1 and Figure 1.**

## Biological question

Does adding proofreading steps make completion more selective for an agonist while increasing information in the completion or noncompletion outcome? The comparison distinguishes the completion ratio from information about ligand identity.

## Original source and our reference calculation

McKeithan TW. *Kinetic proofreading in T-cell receptor signal transduction.* PNAS (1995). [DOI 10.1073/pnas.92.11.5042](https://doi.org/10.1073/pnas.92.11.5042).

McKeithan's model uses sequential molecular modifications competing with receptor–ligand dissociation. His illustrative example compares a specific foreign antigenic peptide with a moderate-affinity self peptide, each presented by MHC. We label these classes agonist and self ligand in the reference calculation.

Our calculation starts with an already bound complex and follows one encounter until completion or first dissociation. It uses the source's illustrative relative rates. Progression is 1; dissociation is 0.1 for agonist and 10 for self ligand. The competing-rate calculation gives per-step passage probabilities 10/11 and 1/11. The number of required steps is 1, 2, 3, 4 or 8.

We give the two ligand classes equal probability. This weighting is an analysis choice. The output used for mutual information is completion versus noncompletion. Intermediate timing and the complete survival history are distinct observations and are outside this Table 1 calculation. The model's initial binding and steady-state population behavior remain distinct from this encounter calculation.

## Run

First follow the [installation instructions](../../README.md#install-once). From the repository folder:

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py
```

The program uses the reviewed functions to calculate completion probabilities, the agonist/self completion ratio, equal-prior Bayes classification error and Shannon mutual information. It checks the saved reference table and repeats the preserved original driver for a direct comparison.

## Outputs in `runs/tcell/`

| File | Meaning |
| --- | --- |
| `table_1_tcell_proofreading.csv` | Full precision values for Table 1. [View the expected table](expected_results/table_1_tcell_proofreading.csv). |
| `figure_1_tcell_proofreading.png` | Figure 1 rendered from the calculated CSV. |
| `exact_results.json` | Exact rational probabilities and numerical enclosures for information. |
| `ligand_dependence.json` | Check that progression after the first step still depends on ligand class in the preserved model. |
| `parameters_used.json` | Actual rates, passage probabilities, input weights and sequence lengths. |
| `verification.json` | Numerical checks, file hashes, environment and elapsed time. |
| `run.log` | Output of the preserved Table 1 driver. |

The manuscript may round probabilities, errors and information to three decimal places. The CSV retains the calculated precision. Information enclosures express numerical evaluation accuracy rather than biological confidence intervals.

## Where the methods are implemented

The example calls `coarse_from_competing_rates()`, `response_metrics()` and `build()` in [proofreading.py](../../workstreams/transfer_proofreading_v0_1/src/proofreading.py). The `information()` function in [transfer.py](../../workstreams/transfer_proofreading_v0_1/src/transfer.py) evaluates mutual information. The preserved Table 1 driver is [run_tcr_reference.py](../../workstreams/paper1_checkpoint_2026-09-23/scripts/run_tcr_reference.py).

For another run use `--out runs/tcell_second_run`. Use `--help` for options.
