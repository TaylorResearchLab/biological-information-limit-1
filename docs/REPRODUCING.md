# Reproducing the paper

## Environment

The reference environment uses Python 3.13.5 with NumPy 2.3.5, SciPy 1.17.0, mpmath 1.3.0 and Matplotlib 3.10.8. Follow the [installation instructions](../README.md#install-once).

```bash
python verify_archive.py
```

This checks source file sizes and checksums against the manifest. It also checks Python syntax.

## Tables and figures

```bash
python generate_artifacts.py --out runs/my_artifacts
```

The output contains all five main tables and all three figures. Open its `README.md` or an example directory to inspect the results. The directory layout matches [artifacts/](../artifacts/).

For an individual example:

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py --out runs/tcell
python examples/02_ribosome_selection/run_ribosome_selection.py --out runs/ribosome
python examples/03_msn2_reporters/run_msn2_reporters.py --out runs/msn2
```

The [Methods map](../METHODS_MAP.md) identifies the script and output for each table, figure and supporting calculation.

## Output locations

Supply `--out` with a new or empty directory beneath `runs/`, or an absolute path outside the repository. Quote paths containing spaces. The programs protect published artifacts and source directories. Choose a different output folder for each run.

## Numerical checks

Each example checks the calculated tables against the [reference values](../examples/REFERENCE_RESULTS.md). Counts and exact ratios require exact agreement. Floating values use absolute and relative tolerances of 1e-12. Msn2 also checks the regenerated primary records and four analysis JSON files against their reference bytes.

Each `verification.json` reports the tests performed and the source and output hashes. Numerical information enclosures describe calculation precision. The scientific bounds describe the specified families of response distributions. Statistical confidence coverage requires a sampling model appropriate to the biological replicates.

Figures use the calculated CSV files. `figure_data.json` records their numerical inputs. Image rendering depends on plotting libraries and fonts. Run logs contain local paths and elapsed times.

## Full Msn2 derived analysis

```bash
python examples/03_msn2_reporters/run_msn2_reporters.py --full-derived --out runs/msn2_all_definitions
```

This verifies all 1,360 comparisons across five response definitions from the 40,458 included scalar fluorescence records. The checks cover the thresholds and 170 condition-count records. They also cover 10 summaries, 40 reference contrasts and the pairing calculation. The report is `all_five_definitions_verification.json`.

The combined `generate_artifacts.py` command includes this verification. To perform the derived-data check alone:

```bash
python tools/verify_msn2_derived.py --out runs/msn2_derived_verification.json
```

Processing from deposited fluorescence trajectories begins with the source-data commands in [Data provenance](DATA_PROVENANCE.md).

## Primary calculation verification

```bash
python reproduce.py --out runs/primary_checks --strict-bytes
```

This verifies the primary results from 34 included count records. It checks Tables 1–5 and the separate product-assay threshold. It also solves the 272 decision comparisons using 544 linear programs. The `--strict-bytes` option checks the SHA-256 digests of three information-analysis files against [their reference identities](../reference_results/expected_information_sha256.json).

The output includes `run_manifest.json` and `primary/verification_summary.json`. The generated `primary_pair_results.json` contains additional analysis fields beyond the compact comparison input. Its input-file hash therefore reflects that representation. Scientific results are checked separately from input serialization.

## Software tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs source checks and numerical reproduction from fresh checkouts. It compares regenerated numerical files and figure inputs with the published artifacts. Each workflow saves its run outputs for inspection.
