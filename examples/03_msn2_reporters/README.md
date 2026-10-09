# Yeast Msn2 reporters

[Saved results](../../artifacts/03_msn2_reporters/) | [Source code](../../src/)

## Biological source and question

[Hansen and O'Shea, eLife (2015), DOI 10.7554/eLife.06559](https://doi.org/10.7554/eLife.06559) measured paired SIP18 and HXK1 reporter responses under controlled Msn2 stimulation. The source observations are deposited at [Dryad, DOI 10.5061/dryad.97vt8](https://doi.org/10.5061/dryad.97vt8).

The example asks what separate response frequencies establish about joint discrimination between stimuli. It then restores pairing within individual cells to determine how that observation reduces the compatible range.

## Calculation

The primary input is 34 binary count tables spanning 17 protocols and two constructs. Outcomes are ordered 00, 01, 10 and 11. Each pair of protocols receives equal weight. The script reconstructs all 272 within-construct comparisons and evaluates classification bounds. The information panel contains 10 selected comparisons. Tables 4–5 and Fig. 3 display the specified contrasts and the progressive restoration of pairing.

The bounds describe compatible probability distributions for the observed finite counts. Numerical certificate widths describe calculation precision. Biological sampling uncertainty is a separate inference problem.

[msn2.py](../../src/bics/msn2.py) implements feature extraction and binary count analysis. [joint_bounds.py](../../src/bics/joint_bounds.py) implements exact classification bounds. [matched_information.py](../../src/bics/matched_information.py) provides certified information bounds and independent linear programs. [comparison.py](../../src/bics/comparison.py) evaluates the primary panel.

## Full derived-data check

Add `--full-derived` to reconstruct all 1,360 comparisons across five response definitions from the 40,458 supplied scalar fluorescence records. The full artifact generator includes this check. [Data provenance](../../docs/DATA_PROVENANCE.md) provides the source trajectory preprocessing command.

## Source-window sensitivity

The source paper specifies an 11-point moving average and a maximum over elements 33 to 64 but does not state how smoothing treats the trace ends. [check_msn2_source_window.py](../../tools/check_msn2_source_window.py) independently evaluates three plausible readings of that definition. It validates the primary all-complete-window reconstruction against the repository results before reporting the sensitivity analysis.

```bash
python tools/check_msn2_source_window.py \
    --archive /path/to/Supplementary_Source_Data.zip \
    --out provenance/msn2_source_window_sensitivity.json \
    --replace
```

The validated record is [msn2_source_window_sensitivity.json](../../provenance/msn2_source_window_sensitivity.json). The source archive is not stored in this repository.

## Outputs

`table_4_msn2_information.csv` gives the selected information ranges. `table_5_msn2_pairing.csv` records the pairing-restoration comparison. `figure_3_msn2_information.png` reads those tables. `all_272_discrimination_comparisons.csv` and `detailed_results/` provide the complete primary results.

## Run

After [installation](../../README.md#install-once), run from the repository folder:

```bash
python examples/03_msn2_reporters/run_msn2_reporters.py --out runs/03_msn2_reporters
```

Choose a new output directory for each run. Use `--help` for options or `--skip-figures` for numerical results only. Each run records its parameters and source identities. Read `verification.json` for the result checks.
