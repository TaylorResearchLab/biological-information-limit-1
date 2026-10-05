# Example 1. T cell receptor proofreading

**Run [run_tcell_proofreading.py](run_tcell_proofreading.py) to reproduce Table 1 and Figure 1.**

## Biological question

Does adding proofreading steps make completion more selective for an agonist while increasing information in the completion or noncompletion outcome? The comparison distinguishes the completion ratio from information about ligand identity.

## Source publication and reference calculation

McKeithan TW. *Kinetic proofreading in T-cell receptor signal transduction.* PNAS (1995). [DOI 10.1073/pnas.92.11.5042](https://doi.org/10.1073/pnas.92.11.5042).

McKeithan's model uses sequential molecular modifications competing with receptor–ligand dissociation. His illustrative example compares a specific foreign antigenic peptide with a moderate-affinity self peptide, each presented by MHC. We label these classes agonist and self ligand in the reference calculation.

Our calculation starts with an already bound complex and follows one encounter until completion or first dissociation. It uses the source's illustrative relative rates. Progression is 1; dissociation is 0.1 for agonist and 10 for self ligand. The competing-rate calculation gives per-step passage probabilities 10/11 and 1/11. The number of required steps is 1, 2, 3, 4 or 8.

We give the two ligand classes equal probability. This weighting is an analysis choice. The output used for mutual information is completion versus noncompletion. Table 1 quantifies information in this binary endpoint. Information in intermediate timing or the full sequence of states would require a different response definition. Conditioning on an already bound complex specifies the encounter considered here.

## Run

First follow the [installation instructions](../../README.md#install-once). From the repository folder:

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py
```

The program calculates completion probabilities and their agonist/self ratio. It calculates equal-prior Bayes classification error and Shannon mutual information from the same response probabilities. It checks the saved table and the output of `run_tcr_reference.py`.

## Outputs in `runs/tcell/`

| File | Meaning |
| --- | --- |
| `table_1_tcell_proofreading.csv` | Full precision values for Table 1. [View the expected table](expected_results/table_1_tcell_proofreading.csv). |
| `figure_1_tcell_proofreading.png` | Figure 1 rendered from the calculated CSV. |
| `exact_results.json` | Exact rational probabilities and numerical enclosures for information. |
| `ligand_dependence.json` | Check that progression after the first step still depends on ligand class in the sequential model. |
| `parameters_used.json` | Actual rates, passage probabilities, input weights and sequence lengths. |
| `verification.json` | Numerical checks, file hashes, environment and elapsed time. |
| `run.log` | Output of the Table 1 reference calculation. |

Table previews round probabilities, errors and information to three decimal places. The CSV retains the calculated precision. Information enclosures bound numerical evaluation error under the specified model.

## Where the methods are implemented

The example calls `coarse_from_competing_rates()`, `response_metrics()` and `build()` in [proofreading.py](../../workstreams/transfer_proofreading_v0_1/src/proofreading.py). The `information()` function in [transfer.py](../../workstreams/transfer_proofreading_v0_1/src/transfer.py) evaluates mutual information. The Table 1 reference script is [run_tcr_reference.py](../../workstreams/paper1_checkpoint_2026-09-23/scripts/run_tcr_reference.py).

For another run use `--out runs/tcell_second_run`. Use `--help` for options.
