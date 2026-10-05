# Ribosomal tRNA selection

[Saved results](../../artifacts/02_ribosome_selection/) | [Source code](../../src/)

## Biological source and question

[Zaher and Green, Molecular Cell (2010), DOI 10.1016/j.molcel.2010.06.009](https://doi.org/10.1016/j.molcel.2010.06.009) measured tRNA selection in wild-type and restrictive ribosomes. Their UUC-codon experiments compared cognate Phe-tRNA with near-cognate Leu-tRNA.

The example asks what acceptance and rejection at proofreading establish about tRNA identity and what remains unresolved about the complete encounter.

## Calculation

Cognate acceptance ranges from 0.9 to 1. Near-cognate acceptance ranges from 0.048 to 0.052 for wild type and from 0.002 to 0.012 for restrictive ribosomes. These are declared sensitivity ranges based on the reported summaries. The information intervals describe that probability family. Input frequencies are specified independently.

The script calculates local information bounds at equally weighted inputs, then at near-cognate frequencies of 0.1 and 0.01. The whole-encounter comparison holds cognate acceptance at 0.95 and near-cognate acceptance at 0.007 while varying equal upstream passage through 1, 0.1, 0.01 and 0.001. Tables 2–3 and Fig. 2 summarize the local bounds and the first three upstream conditions.

The separate product-assay calculation evaluates how an upstream factor U affects the ordering of product ratios. It reports the threshold U < 3.6 under its specified sensitivity family and a comparison based on the source rate summaries.

The implementation is [ribosome.py](../../src/bics/ribosome.py), including `info_bounds` and `assembly_metrics`. [ribosome_product.py](../../src/bics/ribosome_product.py) implements the product-assay comparison.

## Outputs

The directory contains Tables 2–3 and Fig. 2. `source_frequency_sensitivity.csv` and `extended_passage_sweep.csv` provide the additional conditions. `local_information_enclosures.json` retains the certified numerical bounds. `separate_product_assay.json` records the upstream threshold and rate comparison.

## Run

After [installation](../../README.md#install-once), run from the repository folder:

```bash
python examples/02_ribosome_selection/run_ribosome_selection.py --out runs/02_ribosome_selection
```

Choose a new output directory for each run. Use `--help` for options or `--skip-figures` for numerical results only. Each run records its parameters and source identities. Read `verification.json` for the result checks.
