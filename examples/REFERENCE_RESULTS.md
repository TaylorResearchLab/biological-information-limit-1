# Reference results

The CSV files in each `expected_results/` directory supply reference values for the example scripts. [Artifacts](../artifacts/) provides figure previews and tables for reading alongside the full precision output files.

Each example calculates its outputs from the model settings or included observations. It then compares the results with the reference CSVs using absolute and relative tolerances of 1e-12. Integer counts and completion ratios require exact agreement.

| Result | Reference source |
| --- | --- |
| Table 1 | [T cell reference calculation](../workstreams/paper1_checkpoint_2026-09-23/scripts/run_tcr_reference.py) |
| Tables 2–3 and ribosome sensitivity analyses | [Ribosome reference calculation](../workstreams/paper1_checkpoint_2026-09-23/scripts/run_ribosome_reference.py) |
| Tables 4–5 | [Msn2 information and pairing results](../workstreams/method_comparison_2026-09-23/results/science/) |

The Msn2 example also checks the exact bytes of the regenerated compact input and four analysis JSON files. Source checksums are recorded in [the source manifest](../provenance/import_manifest.json). The [example manifest](../provenance/examples_manifest.json) identifies scripts and reference CSVs.

Figures read the calculated CSV outputs. Each `figure_data.json` records the plotted values and input hashes. Numerical comparisons use the data; rendering also depends on the plotting environment.
