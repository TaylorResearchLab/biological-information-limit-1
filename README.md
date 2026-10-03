# Information limits from partially characterized biological processes

Code and reproducible analyses accompanying the manuscript by Deanne M. Taylor.

The analyses examine what incomplete measurements establish about biological information. Examples cover kinetic proofreading, ribosomal tRNA selection and joint reporter measurements in yeast stress signaling.

## Reproduce the primary results

Use Python 3.13.5 for the recorded environment.

```bash
git clone https://github.com/TaylorResearchLab/biological-information-limit-1.git
cd biological-information-limit-1
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python verify_archive.py
python reproduce.py --out runs/primary-001 --figures --strict-bytes
```

On Windows, activate the environment with `.venv\Scripts\activate`.

The command starts from the 34 included primary binary count records. It regenerates all 272 protocol comparisons and 544 linear programs. It checks the quantities reported in Tables 1–5 and the separate-output threshold, compares three full information-result files with their archived SHA-256 identities, and optionally regenerates Figures 1–3. Outputs go to a new directory. Existing source files and inputs are preserved.

Read `runs/primary-001/run_manifest.json` for the numerical checks, file comparisons and software versions. The output directory also contains the generated pair records, decision results, information bounds, pairing-reveal results and figures. The primary command needs no private repository or prior conversation files.

## Files and provenance

The initial import contains all 18 Python source files from Supplementary Code S1 with their comments and docstrings unchanged. An existing verification program and its binary count inputs are included. The original directory paths are retained so that imports and manuscript paths continue to resolve.

- [Reproduction guide](docs/REPRODUCING.md) maps manuscript results to commands.
- [Data provenance](docs/DATA_PROVENANCE.md) defines the included inputs and the separate procedure for original fluorescence data.
- [Imported file manifest](provenance/import_manifest.json) records sizes, SHA-256 digests and Git object identities.
- [Reference result identities](reference_results/expected_information_sha256.json) records the exact archived outputs used for comparison.

`verify_archive.py` checks all 23 imported files and parses all 19 imported Python programs. The top-level wrapper, archive verifier and packaging tests are separate additions. Run the packaging tests with `python -m unittest discover -s tests -v`.

The GitHub Actions workflow runs archive checks and primary reproduction from a checkout of this public repository. Its output artifact contains the generated results and run record. Read the workflow's actual status rather than treating the presence of the workflow as a passed test.

## Scope of this initial import

The primary analysis is executable from the included binary counts. The larger historical tables of derived fluorescence features and the complete set of 1,360 comparisons across all five response definitions are not yet included as saved files. The original preprocessing programs and source-data instructions are included for their regeneration. Raw fluorescence preprocessing and the alternate response definitions are separate from the default primary command.

The analyses describe the finite records and declared model families. Numerical reproduction does not establish population confidence coverage or independent biological replication.

## Citation and reuse

Citation metadata is in [CITATION.cff](CITATION.cff). The manuscript title is given above; a preprint identifier will be added after posting. The software license remains for the author to specify. No license grant is implied by this initial upload. Original source data should be cited through its own DOI.
