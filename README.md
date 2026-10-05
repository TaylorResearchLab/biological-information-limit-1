# Information limits from partially characterized biological processes

Code, data and reproducible examples accompanying the paper by Deanne M. Taylor.

## Examples and saved results

Choose an example to read its methods or run its calculations. Saved results contain figure previews and readable tables. All materials are available on `main`.

| Example | Instructions | Script | Saved results |
| --- | --- | --- | --- |
| **1. T cell receptor proofreading** | [Instructions](examples/01_tcell_proofreading/) | [run_tcell_proofreading.py](examples/01_tcell_proofreading/run_tcell_proofreading.py) | [Table 1 and Figure 1](artifacts/01_tcell_proofreading/) |
| **2. Ribosomal tRNA selection** | [Instructions](examples/02_ribosome_selection/) | [run_ribosome_selection.py](examples/02_ribosome_selection/run_ribosome_selection.py) | [Tables 2–3 and Figure 2](artifacts/02_ribosome_selection/) |
| **3. Yeast Msn2 reporters** | [Instructions](examples/03_msn2_reporters/) | [run_msn2_reporters.py](examples/03_msn2_reporters/run_msn2_reporters.py) | [Tables 4–5 and Figure 3](artifacts/03_msn2_reporters/) |

[Methods map](METHODS_MAP.md) connects each result to its implementation. [Source code](src/) contains the calculation modules. [Data](data/) contains the supplied observations. [Artifacts](artifacts/) contains the figures and full precision results.

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
python verify_sources.py
```

You can also download the repository through **Code > Download ZIP** and run the setup commands from the extracted folder.

## Recreate every table and figure

```bash
python generate_artifacts.py --out runs/my_artifacts
```

The command calculates five tables and three figures. Each figure reads the calculated CSV values. The Msn2 run includes all 1,360 comparisons across five response definitions.

```text
examples/             # One executable script and instructions per system
src/bics/             # Scientific calculation modules
data/msn2/            # Source observations and response definitions
artifacts/            # Published tables, figures and supporting results
runs/my_artifacts/    # Results from your run
```

Choose a new or empty output folder beneath `runs/` or an absolute path outside the repository. Quote paths containing spaces. Published artifacts and source files are protected. Every run has its own output directory.

Open the corresponding tables and figures to compare your results with `artifacts/`. Numerical checks also run automatically. `parameters_used.json` records the calculation settings. `verification.json` reports the checks and software versions. `figure_data.json` records the plotted values.

## Run one example

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py --out runs/tcell
python examples/02_ribosome_selection/run_ribosome_selection.py --out runs/ribosome
python examples/03_msn2_reporters/run_msn2_reporters.py --out runs/msn2
```

Use `--help` for options. Use `--skip-figures` to produce numerical results only. Each script defaults to its example folder beneath `runs/`. The combined generator defaults to `runs/all_artifacts/`.

## Data and reproducibility

All three examples use files supplied in this repository. The Msn2 example starts from 34 primary binary response tables. The repository also contains 40,458 scalar fluorescence records. [Data provenance](docs/DATA_PROVENANCE.md) identifies the source publications and deposit and provides fluorescence preprocessing instructions.

[Reproduction instructions](docs/REPRODUCING.md) describe the calculations and checks. Run the software tests with:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions checks all three examples and regenerates the published artifacts from a fresh checkout. [Source checksums](provenance/source_manifest.json) and [artifact identities](artifacts/artifact_manifest.json) identify the inputs and outputs. Numerical files and figure inputs support direct comparison across runs. Runtime and log paths describe each execution. Plotting libraries and fonts can affect image rendering.

## Citation and reuse

Use [CITATION.cff](CITATION.cff) to cite the software. Cite the source publications and data deposit identified in each example.

Software is licensed under the [MIT License](LICENSE). The author's paper, figures and scientific documentation are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Materials from other sources retain their source attribution and license. See [Licensing](LICENSING.md) for details.
