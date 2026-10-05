# Manuscript methods and scripts

Each example has one primary script. [Installation](README.md#install-once) is shared by all examples.

| Result | Script | Output |
| --- | --- | --- |
| Table 1 and Fig. 1 | [T cell proofreading](examples/01_tcell_proofreading/run_tcell_proofreading.py) | `table_1_tcell_proofreading.csv`, `figure_1_tcell_proofreading.png` |
| Continuing ligand dependence | Same T cell script | `ligand_dependence.json` |
| Tables 2–3 and Fig. 2 | [Ribosome selection](examples/02_ribosome_selection/run_ribosome_selection.py) | `table_2_ribosome_information.csv`, `table_3_ribosome_passage.csv`, `figure_2_ribosome_selection.png` |
| Source frequencies and upstream passage | Same ribosome script | `source_frequency_sensitivity.csv`, `extended_passage_sweep.csv` |
| Separate product-assay calculation | Same ribosome script | `separate_product_assay.json` |
| Tables 4–5 and Fig. 3 | [Msn2 reporters](examples/03_msn2_reporters/run_msn2_reporters.py) | `table_4_msn2_information.csv`, `table_5_msn2_pairing.csv`, `figure_3_msn2_information.png` |
| All 272 primary comparisons | Same Msn2 script | `all_272_discrimination_comparisons.csv`, `detailed_results/` |
| All five response definitions | Same Msn2 script with `--full-derived` | `all_five_definitions_verification.json` |
| Source fluorescence preprocessing | [process_msn2_fluorescence.py](tools/process_msn2_fluorescence.py) | Scalar features, count tables and comparisons |

## Scientific implementation

T cell calculations use `coarse_from_competing_rates`, `response_metrics` and `build` in [tcell.py](src/bics/tcell.py). Shannon mutual information is implemented in [information.py](src/bics/information.py).

Ribosome bounds use `info_bounds` and `assembly_metrics` in [ribosome.py](src/bics/ribosome.py). The separate product assay uses [ribosome_product.py](src/bics/ribosome_product.py).

Msn2 processing and count analysis use [msn2.py](src/bics/msn2.py). Exact classification bounds use [joint_bounds.py](src/bics/joint_bounds.py). Certified information bounds and independent linear programs use [matched_information.py](src/bics/matched_information.py). [comparison.py](src/bics/comparison.py) runs the primary panel.

## Saved results

[Artifacts](artifacts/) contains the figures, full precision CSV tables and supporting results. Generate a separate copy with `python generate_artifacts.py --out runs/my_artifacts`. Every figure reads calculated CSVs. Parameters and source identities accompany each run.
