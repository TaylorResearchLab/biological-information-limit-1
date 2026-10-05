# Information limits from partially characterized biological processes

Code, data and reproducible examples accompanying the manuscript by Deanne M. Taylor.

## Examples and saved results

Choose the biological example you are reading in the paper. Open **Saved results** to inspect the tables and figure without running Python. Open **Instructions** to reproduce them. Everything is available on this repository's default `main` branch.

| Example | Instructions | Script | Saved results |
| --- | --- | --- | --- |
| **1. T cell receptor proofreading** | [Instructions](examples/01_tcell_proofreading/) | [run_tcell_proofreading.py](examples/01_tcell_proofreading/run_tcell_proofreading.py) | [Table 1 and Figure 1](artifacts/01_tcell_proofreading/) |
| **2. Ribosomal tRNA selection** | [Instructions](examples/02_ribosome_selection/) | [run_ribosome_selection.py](examples/02_ribosome_selection/run_ribosome_selection.py) | [Tables 2-3, Figure 2 and supporting results](artifacts/02_ribosome_selection/) |
| **3. Yeast Msn2 reporters** | [Instructions](examples/03_msn2_reporters/) | [run_msn2_reporters.py](examples/03_msn2_reporters/run_msn2_reporters.py) | [Tables 4-5, Figure 3 and all 272 primary comparisons](artifacts/03_msn2_reporters/) |

The [Methods map](METHODS_MAP.md) links each result to its implementation. [Artifacts](artifacts/) contains full precision CSV tables, generated PNG figures, detailed JSON results, parameters and verification records. Its [manifest](artifacts/artifact_manifest.json) identifies the generating source version and file hashes.

## Install once

Download the complete repository using **Code > Download ZIP**, then unzip it. Alternatively:

```bash
git clone https://github.com/TaylorResearchLab/biological-information-limit-1.git
cd biological-information-limit-1
```

Open a terminal in the downloaded repository folder. The recorded environment uses **Python 3.13.5**. Create an environment:

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

## Recreate every table and figure

```bash
python generate_artifacts.py --out runs/my_artifacts
```

This runs all three examples, including the full Msn2 derived-data verification. The output directory mirrors the published `artifacts/` directory. It contains all five tables, all three figures and supporting outputs. The figures read the newly calculated CSV tables. Nothing is copied from the published artifact results to stand in for a calculation.

```text
artifacts/                          # Published results for reading and comparison
    01_tcell_proofreading/
    02_ribosome_selection/
    03_msn2_reporters/
runs/my_artifacts/                  # Your newly generated results
    01_tcell_proofreading/
    02_ribosome_selection/
    03_msn2_reporters/
```

You can specify a new absolute output path outside the repository instead. Quote paths containing spaces. Without `--out`, the combined command uses `runs/all_artifacts/`.

**The scripts refuse to overwrite published artifacts, source directories or a nonempty output directory.** Choose a new name for each run. Compare the CSV tables and figures directly; no separate comparison command is needed. Each example runs numerical reference checks automatically.

The scientific CSV/JSON values and figure inputs are reproducible. Runtime, absolute paths and software-version records can differ between runs. Image bytes can also depend on plotting-library and font versions. Each `figure_data.json` records exactly which calculated values were plotted. The PNGs are generated renderings, not a claim of pixel identity with images in an earlier manuscript draft.

## Run one example

```bash
python examples/01_tcell_proofreading/run_tcell_proofreading.py --out runs/tcell_review
python examples/02_ribosome_selection/run_ribosome_selection.py --out runs/ribosome_review
python examples/03_msn2_reporters/run_msn2_reporters.py --out runs/msn2_review
```

When `--out` is omitted, the individual defaults are `runs/tcell/`, `runs/ribosome/` and `runs/msn2/`. Use `--help` for options or `--skip-figures` for numerical results only. These scripts require the included repository files but no separate raw-data download.

## Msn2 inputs and scope

The Msn2 example reconstructs the 272 primary comparisons from 34 binary count tables. The repository also includes 40,458 scalar fluorescence rows and all 1,360 comparisons across five response definitions. To verify that full derived archive when running Msn2 alone:

```bash
python examples/03_msn2_reporters/run_msn2_reporters.py --full-derived --out runs/msn2_all_definitions
```

The combined artifact command already includes this check. Processing original fluorescence trajectories is a separate calculation described in [Data provenance](docs/DATA_PROVENANCE.md). The primary information analyses use the included derived observations. The original source data retain their source DOI and license.

## Reproduction and provenance

The earlier complete reproduction command remains available:

```bash
python reproduce.py --out runs/primary-001 --figures --strict-bytes
```

It verifies Tables 1-5, the 272 primary comparisons, 544 linear programs and the separate product-assay threshold. It runs the preserved manuscript figure program. `generate_artifacts.py` is the reader entry point for regenerating the published artifact directory using figures drawn from calculated outputs.

The [reproduction guide](docs/REPRODUCING.md) documents the earlier commands. Reviewed calculation programs remain unchanged in [workstreams/](workstreams/). The example scripts call those programs and functions. Their original comments and caveat docstrings are preserved.

[Imported file identities](provenance/import_manifest.json) cover all 37 imported scientific files. [Example file identities](provenance/examples_manifest.json) cover the example entry points and reference CSVs. [Complete Msn2 archive identities](provenance/msn2_archive_manifest.json) document the nine saved derived files. [Saved primary inputs](workstreams/method_comparison_2026-09-23/inputs/primary_records.json) and [reference outputs](workstreams/method_comparison_2026-09-23/results/science/) remain available directly.

Run software tests with `python -m unittest discover -s tests -v`. The read-only GitHub Actions workflows reproduce the original calculations, individual examples and full artifact bundle. They check saved artifact integrity and compare regenerated numerical files and figure inputs against the published snapshot. These runs do not update the published results. Numerical reproduction concerns the declared model families and finite observed records. Population confidence coverage and biological replication are separate questions.

## Citation and reuse

Citation metadata is in [CITATION.cff](CITATION.cff). A preprint identifier will be added after posting.

The software is licensed under the [MIT License](LICENSE). The author-created paper, figures and scientific documentation are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Licensing](LICENSING.md) defines the scope. Material obtained from other sources retains its original terms and attribution. Cite the original studies and source data as well as this paper.
