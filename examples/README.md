# Manuscript examples

Each folder corresponds to one biological example in the paper. Open its README for the biological question, original source, calculation and one-command instructions.

| Example | Tables and figure | Runnable script |
| --- | --- | --- |
| [1. T cell receptor proofreading](01_tcell_proofreading/) | Table 1; Figure 1 | [run_tcell_proofreading.py](01_tcell_proofreading/run_tcell_proofreading.py) |
| [2. Ribosomal tRNA selection](02_ribosome_selection/) | Tables 2–3; Figure 2 | [run_ribosome_selection.py](02_ribosome_selection/run_ribosome_selection.py) |
| [3. Yeast Msn2 reporters](03_msn2_reporters/) | Tables 4–5; Figure 3 | [run_msn2_reporters.py](03_msn2_reporters/run_msn2_reporters.py) |

[Installation](../README.md#install-once) is shared by all examples. Results are written beneath `runs/`. The calculated values are compared with [archived reference results](REFERENCE_RESULTS.md). The [Methods map](../METHODS_MAP.md) connects the examples to the underlying functions.

`_common.py` handles files and verification. `_plot.py` reads calculated CSVs to draw the figures. These shared utilities are called by the three example scripts; readers do not need to run them separately.
