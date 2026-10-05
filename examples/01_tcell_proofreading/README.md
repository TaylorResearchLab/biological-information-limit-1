# T cell receptor proofreading

[Saved results](../../artifacts/01_tcell_proofreading/) | [Source code](../../src/)

## Biological source and question

McKeithan proposed a sequential kinetic proofreading model to explain T cell antigen discrimination. [McKeithan, PNAS (1995), DOI 10.1073/pnas.92.11.5042](https://doi.org/10.1073/pnas.92.11.5042).

This example asks whether a completion response that becomes more selective also carries more information about ligand identity. It models one encounter beginning with a bound receptor. The two ligand classes correspond to McKeithan's specific foreign peptide and moderate-affinity self peptide examples.

## Calculation

The progression rate is 1 in relative units. Dissociation rates are 0.1 and 10 for the agonist and self classes. The probability of completing a modification before dissociation is the progression rate divided by the sum of the two rates. This gives 10/11 and 1/11. A sequence of N steps has completion probability equal to the corresponding passage probability raised to N.

The script evaluates N = 1, 2, 3, 4 and 8 with equally weighted inputs. It calculates Shannon mutual information between ligand class and completion or noncompletion. The completion ratio and optimal classification error are reported separately. The observed response is the binary endpoint. Its scope is one already-bound encounter.

The implementation is [tcell.py](../../src/bics/tcell.py), using `coarse_from_competing_rates`, `response_metrics` and `build`. [information.py](../../src/bics/information.py) implements Shannon information. The calculation also checks that ligand identity conditions the second step after successful passage through the first.

## Outputs

`table_1_tcell_proofreading.csv` contains full precision values. `figure_1_tcell_proofreading.png` plots those values. `exact_results.json` retains rational probabilities and certified numerical enclosures. `ligand_dependence.json` records the conditional progression check.

## Run

After [installation](../../README.md#install-once), run from the repository folder:

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py --out runs/01_tcell_proofreading
```

Choose a new output directory for each run. Use `--help` for options or `--skip-figures` for numerical results only. Each run records its parameters and source identities. Read `verification.json` for the result checks.
