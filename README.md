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

## Saved primary inputs and reference results

The repository includes the [272 primary input records](workstreams/method_comparison_2026-09-23/inputs/primary_records.json) and the [reference result files](workstreams/method_comparison_2026-09-23/results/science). These cover the decision comparisons, information bounds, pairing-reveal calculation and summary. Each file matches the historical analysis checkpoint byte for byte. Their SHA-256 digests and Git object identities are recorded in [the materialization record](provenance/primary_reference_materialization.json).

To rerun the comparison directly from the archived input:

```bash
python workstreams/method_comparison_2026-09-23/src/run_comparison.py --inputs workstreams/method_comparison_2026-09-23/inputs/primary_records.json --out runs/information-001
```

## Files and provenance

The initial import contains all 18 Python source files from Supplementary Code S1 with their comments and docstrings unchanged. An existing verification program and its binary count inputs are included. The original directory paths are retained so that imports and manuscript paths continue to resolve.

- [Reproduction guide](docs/REPRODUCING.md) maps manuscript results to commands.
- [Data provenance](docs/DATA_PROVENANCE.md) defines the included inputs and the separate procedure for original fluorescence data.
- [Imported file manifest](provenance/import_manifest.json) records sizes, SHA-256 digests and Git object identities.
- [Reference result identities](reference_results/expected_information_sha256.json) records the exact archived outputs used for comparison.

`verify_archive.py` checks all 37 imported files and parses all 19 imported Python programs. The top-level wrapper, archive verifier, derived-data verifier and packaging tests are separate additions. Run the packaging tests with `python -m unittest discover -s tests -v`.

The GitHub Actions workflow runs archive checks, primary reproduction and verification of the complete Msn2 derived archive from a checkout of this public repository. Its output artifact contains the generated results and run records. Read the workflow's actual status rather than treating the presence of the workflow as a passed test.

## Complete Msn2 derived archive

The [saved Msn2 analysis files](workstreams/msn2_pairing_2026-09-23/results/analysis) include 40,458 rows of scalar fluorescence features, 170 condition-count records and all 1,360 comparisons across five response definitions. The archive also includes thresholds, source-member identities, zero-value audit records, reference contrasts, summaries and the [descriptive pairing-reveal results](workstreams/msn2_pairing_2026-09-23/results/constraint_reveal.json). All nine files match their historical size, SHA-256 digest and Git object identity. See [the archive manifest](provenance/msn2_archive_manifest.json).

To verify the full derived analysis:

```bash
python tools/verify_msn2_derived.py --out runs/msn2-derived-validation-001.json
```

This command starts from the saved scalar features. It reconstructs the thresholds and all 170 count records, recomputes all 1,360 comparisons and checks the saved summaries and reference contrasts. It also reproduces the pairing-reveal calculation. Exact fractions and discrete fields must match exactly. Floating values are checked with absolute and relative tolerances of 1e-12; the report separately records whether each regenerated JSON file is byte-identical. The [recorded verification](provenance/msn2_archive_validation.json) found zero numerical differences and exact byte agreement for all five regenerated analysis JSON files.

Original fluorescence preprocessing remains a separate calculation. The original programs and source-data instructions are included for that purpose. Neither the default primary command nor the derived-data verifier reruns the raw trajectories.

The analyses describe the finite records and declared model families. Numerical reproduction does not establish population confidence coverage or independent biological replication.

## Citation and reuse

Citation metadata is in [CITATION.cff](CITATION.cff). The manuscript title is given above; a preprint identifier will be added after posting.

The software is licensed under the [MIT License](LICENSE). The author-created paper, figures and scientific documentation are licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). See [Licensing](LICENSING.md) for the scope of each license. Material obtained from other sources retains its original terms and attribution. Original source data should be cited through its own DOI.
