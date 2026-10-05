# Manuscript methods and scripts

Start with [Examples](examples/). Each primary script runs on its own after the common [installation](README.md#install-once).

| Manuscript result | Primary script | Output beneath the chosen `--out` folder |
| --- | --- | --- |
| Table 1: T cell completion, selectivity, classification error and mutual information | [run_tcell_proofreading.py](examples/01_tcell_proofreading/run_tcell_proofreading.py) | `table_1_tcell_proofreading.csv` |
| Continuing ligand dependence in the sequential T cell model | Same T cell script; `build()` function | `ligand_dependence.json` |
| Figure 1 | Same T cell script | `figure_1_tcell_proofreading.png` |
| Table 2: ribosome information at proofreading | [run_ribosome_selection.py](examples/02_ribosome_selection/run_ribosome_selection.py) | `table_2_ribosome_information.csv` |
| Table 3: information per original encounter | Same ribosome script | `table_3_ribosome_passage.csv` |
| Ribosome source-frequency sensitivity | Same ribosome script | `source_frequency_sensitivity.csv` |
| Separate product-assay threshold and rate-based comparison | Same ribosome script | `separate_product_assay.json` |
| Figure 2 | Same ribosome script | `figure_2_ribosome_selection.png` |
| Table 4: selected Msn2 information ranges | [run_msn2_reporters.py](examples/03_msn2_reporters/run_msn2_reporters.py) | `table_4_msn2_information.csv` |
| Table 5: restoration of same-cell pairing | Same Msn2 script | `table_5_msn2_pairing.csv` |
| All 272 primary accuracy comparisons | Same Msn2 script | `all_272_discrimination_comparisons.csv` and `detailed_results/decision_comparison.json` |
| The complete 10-case information panel | Same Msn2 script | `detailed_results/information_panel.json` |
| Figure 3 | Same Msn2 script | `figure_3_msn2_information.png` |
| All five Msn2 response definitions | Same Msn2 script with `--full-derived` | `all_five_definitions_verification.json` |
| Fluorescence preprocessing | `analyze_msn2.py --archive ... --out ...` | See [Data provenance](docs/DATA_PROVENANCE.md) |

## Scientific implementation

T cell rates and response metrics use [proofreading.py](workstreams/transfer_proofreading_v0_1/src/proofreading.py). Shannon mutual information uses `information()` in [transfer.py](workstreams/transfer_proofreading_v0_1/src/transfer.py).

Ribosome local bounds and encounter assembly use [ribosome_boundary.py](workstreams/research_update_2026-09-23/ribosome_boundary/src/ribosome_boundary.py). The product assay uses [evaluate_separate_output.py](workstreams/ribosome_separate_output_2026-09-24/src/evaluate_separate_output.py).

Msn2 count analysis uses [analyze_msn2.py](workstreams/msn2_pairing_2026-09-23/src/analyze_msn2.py). The information and decision formulations use [matched_information.py](workstreams/method_comparison_2026-09-23/src/matched_information.py), executed by [run_comparison.py](workstreams/method_comparison_2026-09-23/src/run_comparison.py).

## Output verification

Each example checks its inputs against the [source manifest](provenance/import_manifest.json). It then calculates results and compares the CSV values with the [reference tables](examples/REFERENCE_RESULTS.md). Every figure reads calculated CSVs. `figure_data.json` records the plotted rows and input hashes.

Detailed JSON files contain exact probability fractions and certified numerical information enclosures. CSV files retain full numerical precision. The table previews use rounded values for reading.

## Saved results

[Artifacts](artifacts/) contains the five tables and three figures with their supporting outputs. Run `python generate_artifacts.py --out runs/my_artifacts` to generate the same directory structure. Each run records its source file identities and calculation settings.
