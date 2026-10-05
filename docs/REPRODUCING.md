# Reproducing the paper

## Setup

Use Python 3.13.5 and install `requirements.txt` in a virtual environment as described in the [README](../README.md#install-once). Run `python verify_sources.py` to check the source and data checksums.

## Tables and figures

```bash
python generate_artifacts.py --out runs/my_artifacts
```

This command runs all three examples. Results follow the same structure as [artifacts](../artifacts/). Each figure uses the newly calculated CSV values. The [Methods map](../METHODS_MAP.md) identifies the script, functions and output for each result.

Each example can also be run separately. Use `--out` to select a new or empty folder beneath `runs/` or an absolute path outside the repository. A repeated run requires a new folder name. Published results and source files are protected.

## Numerical checks

```bash
python -m unittest discover -s tests -v
```

Each example compares its numerical output with the corresponding published results. The Msn2 calculations include 272 primary comparisons and 544 linear programs. The full derived check reconstructs 1,360 comparisons across five response definitions.

```bash
python examples/03_msn2_reporters/run_msn2_reporters.py --full-derived --out runs/msn2_full
```

Exact fractions and discrete fields use exact comparison. Floating checks use the tolerances stated in the code. The information outputs retain certified numerical enclosures. These enclosures quantify numerical precision; the compatible-distribution ranges describe uncertainty about unmeasured relationships.

## Comparing your output

Open the CSV files and figure previews beside those in `artifacts/`. Checks also run automatically during calculation. A software test can compare a complete local bundle with the saved bundle:

```bash
BICS_REGENERATED_ARTIFACTS=runs/my_artifacts python -m unittest discover -s tests -p test_artifacts.py -v
```

Logs and environment records describe the individual run. Image bytes can vary across plotting libraries or fonts. `figure_data.json` supplies the exact values used for plotting.

## Source observations

[Data provenance](DATA_PROVENANCE.md) describes the source publications and the optional reconstruction from fluorescence trajectories. The primary artifact calculations use the files supplied in `data/`.
