# Example 2. Ribosomal tRNA selection

**Run [run_ribosome_selection.py](run_ribosome_selection.py) to reproduce Tables 2–3, Figure 2 and the separate product-assay threshold.**

## Biological question

What does acceptance measured at proofreading establish about tRNA discrimination? What additional information is required to connect that checkpoint to the final outcome of an original encounter?

## Original source and declared comparisons

Zaher HS and Green R. *Hyperaccurate and error-prone ribosomes exploit distinct mechanisms during tRNA selection.* Molecular Cell (2010). [DOI 10.1016/j.molcel.2010.06.009](https://doi.org/10.1016/j.molcel.2010.06.009).

The source compares cognate Phe-tRNA and near-cognate Leu-tRNA at the UUC codon. Its proofreading acceptance summaries are interpreted as conditional probabilities among tRNAs that reached proofreading. The analysis uses a closed cognate acceptance interval of 0.9–1.0, conservatively relaxing the source's statement of acceptance above 0.9. Near-cognate intervals are 0.048–0.052 for wild type and 0.002–0.012 for restrictive ribosomes.

These rectangles are declared sensitivity families based on the displayed summaries. They are not population confidence regions. Equal weighting of the two substrate classes is a standardized comparison, not a measured cellular mixture. Source-frequency sensitivity also uses near-cognate frequencies of 1/10 and 1/100.

For the whole-encounter calculation, proofreading acceptance is fixed at 0.95 for cognate and 0.007 for near-cognate tRNA. Equal upstream passage for both classes is varied through 1, 1/10, 1/100 and 1/1000. These upstream values are controlled model settings. The first three rows are Table 3. The fourth is an additional reference sweep value.

## Run

Follow the [installation instructions](../../README.md#install-once). From the repository folder:

```bash
python examples/02_ribosome_selection/run_ribosome_selection.py
```

The script calls the preserved local-information and two-stage functions. It also runs the separate peptide-product calculation. That calculation identifies the condition `U < 3.6` for a guaranteed ordering within its declared sensitivity family. It keeps the rate-based comparator separate from the rate-free result.

## Outputs in `runs/ribosome/`

| File | Meaning |
| --- | --- |
| `table_2_ribosome_information.csv` | Equal-weight local information bounds. [Expected values](expected_results/table_2_ribosome_information.csv). |
| `table_3_ribosome_passage.csv` | Terminal information per original encounter as upstream passage changes. [Expected values](expected_results/table_3_ribosome_passage.csv). |
| `source_frequency_sensitivity.csv` | Both preparations under three input mixtures. [Expected values](expected_results/source_frequency_sensitivity.csv). |
| `extended_passage_sweep.csv` | All four upstream passage settings. [Expected values](expected_results/extended_passage_sweep.csv). |
| `separate_product_assay.json` | Product-assay threshold, model assumptions and separate rate-based comparator. |
| `figure_2_ribosome_selection.png` | Stage diagram annotated from the calculated Tables 2–3. |
| `local_information_enclosures.json` | Numerical enclosures for local extrema. |
| `parameters_used.json` / `verification.json` | Input settings, reference comparisons, hashes, versions and elapsed time. |

## Where the methods are implemented

`AcceptanceBox`, `info_bounds()` and `assembly_metrics()` are in [ribosome_boundary.py](../../workstreams/research_update_2026-09-23/ribosome_boundary/src/ribosome_boundary.py). Mutual information and rectangular extrema use [transfer.py](../../workstreams/research_update_2026-09-23/ribosome_boundary/reference/transfer.py). The product-assay calculation runs [evaluate_separate_output.py](../../workstreams/ribosome_separate_output_2026-09-24/src/evaluate_separate_output.py). The preserved original driver is [run_ribosome_reference.py](../../workstreams/paper1_checkpoint_2026-09-23/scripts/run_ribosome_reference.py).

For another run use `--out runs/ribosome_second_run`. Use `--help` for options.
