# Information limits from partially characterized biological processes

Code, data and reproducible examples accompanying the manuscript by Deanne M. Taylor.

## Examples

Choose the biological example you are reading in the paper. Each folder explains the original study, our calculation, the inputs and the outputs. The script produces the named tables and figure and checks the results.

| Example | Start here | Run this script | Manuscript results |
| --- | --- | --- | --- |
| **1. T cell receptor proofreading** | [Explanation and instructions](examples/01_tcell_proofreading/) | [run_tcell_proofreading.py](examples/01_tcell_proofreading/run_tcell_proofreading.py) | Table 1 and Figure 1 |
| **2. Ribosomal tRNA selection** | [Explanation and instructions](examples/02_ribosome_selection/) | [run_ribosome_selection.py](examples/02_ribosome_selection/run_ribosome_selection.py) | Tables 2–3, Figure 2 and product-assay threshold |
| **3. Yeast Msn2 reporters** | [Explanation and instructions](examples/03_msn2_reporters/) | [run_msn2_reporters.py](examples/03_msn2_reporters/run_msn2_reporters.py) | Tables 4–5, Figure 3 and all 272 primary discrimination comparisons |

The [Methods map](METHODS_MAP.md) links each manuscript result to its script, calculation functions and output. The [example reference tables](examples/REFERENCE_RESULTS.md) can be read without running Python.

## Install once

Download the complete repository using **Code → Download ZIP**, then unzip it. Alternatively:

```bash
git clone https://github.com/TaylorResearchLab/biological-information-limit-1.git
cd biological-information-limit-1
```

Open a terminal in the downloaded repository folder. The recorded environment uses **Python 3.13.5**. Create an environment and install the supplied dependencies:

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install and check the archived files:

```bash
python -m pip install -r requirements.txt
python verify_archive.py
```

## Run an example

From the repository folder, run any one of these commands:

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py
python examples/02_ribosome_selection/run_ribosome_selection.py
python examples/03_msn2_reporters/run_msn2_reporters.py
```

Results appear in `runs/tcell/`, `runs/ribosome/` or `runs/msn2/`. Each contains clearly named CSV tables, a PNG figure, `parameters_used.json` and `verification.json`. A successful run prints `PASS`. The numerical CSV values retain full precision. The figures read those calculated CSV values rather than a stored list of manuscript numbers.

Choose a new folder when repeating a run:

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py --out runs/tcell_second_run
```

Existing results are preserved. Use `--help` for options. Use `--skip-figures` for numerical results only. These examples use the included inputs; no original fluorescence download is needed.

## Full Msn2 derived-data verification

The default Msn2 example reconstructs the 272 primary comparisons from 34 binary count tables. The repository also includes the complete derived archive of 40,458 scalar fluorescence rows and 1,360 comparisons across five response definitions. To verify that larger archive in the same example:

```bash
python examples/03_msn2_reporters/run_msn2_reporters.py --full-derived --out runs/msn2_all_definitions
```

This additional check starts from the saved scalar features. Processing the original fluorescence trajectories is a separate calculation described in [Data provenance](docs/DATA_PROVENANCE.md). Original source data retain their source DOI and license.

## Complete archived reproduction and provenance

The existing command for the complete archived calculation remains available:

```bash
python reproduce.py --out runs/primary-001 --figures --strict-bytes
```

It verifies Tables 1–5, the 272 primary comparisons, 544 linear programs and the separate product-assay threshold. It also runs the preserved manuscript figure program. The example commands above provide new figure renderings from calculated outputs; they do not replace the figure files in an author's manuscript.

The [reproduction guide](docs/REPRODUCING.md) documents the original commands. The reviewed calculation programs remain unchanged in [workstreams/](workstreams/). The new `examples/` scripts call those programs and functions. Their original comments and caveat docstrings are preserved.

[Imported file identities](provenance/import_manifest.json) cover all 37 imported scientific files. [Example file identities](provenance/examples_manifest.json) cover the new entry points and reference CSVs. [Complete Msn2 archive identities](provenance/msn2_archive_manifest.json) document the nine saved derived files. [Saved primary inputs](workstreams/method_comparison_2026-09-23/inputs/primary_records.json) and [reference outputs](workstreams/method_comparison_2026-09-23/results/science/) remain available directly.

Run software tests with `python -m unittest discover -s tests -v`. GitHub Actions runs the original reproduction and each example from a fresh checkout. Numerical reproduction concerns the declared model families and finite observed records. Population confidence coverage and biological replication are separate questions.

## Citation and reuse

Citation metadata is in [CITATION.cff](CITATION.cff). A preprint identifier will be added after posting.

The software is licensed under the [MIT License](LICENSE). The author-created paper, figures and scientific documentation are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Licensing](LICENSING.md) defines the scope. Material obtained from other sources retains its original terms and attribution. Cite the original studies and source data as well as this paper.
