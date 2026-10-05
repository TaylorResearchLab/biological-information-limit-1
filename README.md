# Information limits from partially characterized biological processes

Code, data and reproducible examples accompanying the paper by Deanne M. Taylor.

## Examples and saved results

Choose an example to read its methods or run its calculations. The saved results contain figure previews and readable tables. All materials are available on `main`.

| Example | Instructions | Script | Saved results |
| --- | --- | --- | --- |
| **1. T cell receptor proofreading** | [Instructions](examples/01_tcell_proofreading/) | [run_tcell_proofreading.py](examples/01_tcell_proofreading/run_tcell_proofreading.py) | [Table 1 and Figure 1](artifacts/01_tcell_proofreading/) |
| **2. Ribosomal tRNA selection** | [Instructions](examples/02_ribosome_selection/) | [run_ribosome_selection.py](examples/02_ribosome_selection/run_ribosome_selection.py) | [Tables 2–3 and Figure 2](artifacts/02_ribosome_selection/) |
| **3. Yeast Msn2 reporters** | [Instructions](examples/03_msn2_reporters/) | [run_msn2_reporters.py](examples/03_msn2_reporters/run_msn2_reporters.py) | [Tables 4–5 and Figure 3](artifacts/03_msn2_reporters/) |

The [Methods map](METHODS_MAP.md) connects each result to its calculation functions and output files. [Artifacts](artifacts/) contains the full precision tables and supporting results.

## Install once

Use Python 3.13.5 with the versions specified in `requirements.txt`.

```bash
git clone https://github.com/TaylorResearchLab/biological-information-limit-1.git
cd biological-information-limit-1
python -m venv .venv
```

Activate the environment on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies and check the source files:

```bash
python -m pip install -r requirements.txt
python verify_archive.py
```

You can also download the repository through **Code > Download ZIP** and run these setup commands from the extracted folder.

## Recreate every table and figure

```bash
python generate_artifacts.py --out runs/my_artifacts
```

The command runs all three examples and generates five tables and three figures. Each figure uses the calculated CSV values. The Msn2 run includes verification of all 1,360 comparisons across five response definitions.

```text
artifacts/                          # Published results
    01_tcell_proofreading/
    02_ribosome_selection/
    03_msn2_reporters/
runs/my_artifacts/                  # Results from your run
    01_tcell_proofreading/
    02_ribosome_selection/
    03_msn2_reporters/
```

**Choose a new or empty output folder beneath `runs/`, or an absolute path outside the repository.** Quote paths containing spaces. The scripts protect the source files and published artifacts. Each run has its own output folder.

Open the corresponding CSV files and figures to compare your results with `artifacts/`. Numerical reference checks also run automatically. `parameters_used.json` records the calculation settings. `verification.json` reports the checks and software versions. Each `figure_data.json` contains the plotted data and input hashes.

Numerical files and figure inputs support direct comparison across runs. Log paths and elapsed times describe each run. Image rendering can vary with plotting libraries and fonts.

## Run one example

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py --out runs/tcell
python examples/02_ribosome_selection/run_ribosome_selection.py --out runs/ribosome
python examples/03_msn2_reporters/run_msn2_reporters.py --out runs/msn2
```

Use `--help` for options. Use `--skip-figures` to produce numerical results only. The default output folders are `runs/tcell/`, `runs/ribosome/` and `runs/msn2/`. The combined command defaults to `runs/all_artifacts/`.

## Data and reproducibility

All three examples run from files included in the repository. The Msn2 example begins with 34 binary count tables. The repository also contains 40,458 scalar fluorescence records. The [data provenance guide](docs/DATA_PROVENANCE.md) identifies the source publication and data deposit. It provides the commands for processing fluorescence trajectories from that deposit.

The [reproduction guide](docs/REPRODUCING.md) describes numerical verification and the full Msn2 analysis. Run the software tests with:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions checks each example and regenerates the artifact bundle from a fresh checkout. [File manifests](provenance/) record source identities and checksums. The [artifact manifest](artifacts/artifact_manifest.json) records the numerical run and generated file identities.

## Citation and reuse

Use [CITATION.cff](CITATION.cff) to cite the software. Cite the experimental publications and data deposits identified in each example.

Software is licensed under the [MIT License](LICENSE). The author's paper, figures and scientific documentation are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Materials from other sources retain their source attribution and license. See [Licensing](LICENSING.md) for details.
