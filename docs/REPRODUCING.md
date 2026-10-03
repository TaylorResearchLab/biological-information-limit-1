# Reproducing the manuscript calculations

## Environment and integrity

The pinned environment uses Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, mpmath 1.3.0 and Matplotlib 3.10.8. Install `requirements.txt` in a virtual environment. Run `python verify_archive.py` before computation.

The verifier checks file size, SHA-256, Git blob identity and Python syntax. The 18 supplementary source programs and the existing verification program retain their original bytes. New public entry points are separate files.

## Primary reproduction

```bash
python reproduce.py --out runs/primary-001 --figures --strict-bytes
```

Choose a new or empty output directory. The command refuses to write into the source tree or replace a previous run. The `--figures` option is optional. The `--strict-bytes` option requires all three information-result files to have their recorded SHA-256 digests. Without that option, byte differences are recorded after the numerical tests and can be investigated without changing the archived identities.

| Manuscript result | Program or output |
| --- | --- |
| Table 1, kinetic proofreading | `workstreams/paper1_checkpoint_2026-09-23/scripts/run_tcr_reference.py`; output `primary/tcr.tsv` |
| Tables 2 and 3, ribosome information | `workstreams/paper1_checkpoint_2026-09-23/scripts/run_ribosome_reference.py`; numerical checks in `primary/verification_summary.json` |
| Separate product assay and threshold | `workstreams/ribosome_separate_output_2026-09-24/src/evaluate_separate_output.py`; output `primary/separate_output.json` |
| Table 4, joint-reporter information | `primary/information/information_panel.json` |
| Table 5, restored pairing | `primary/information/information_reveal.json` |
| All 272 primary decision comparisons | `primary/information/decision_comparison.json` |
| Figures 1–3 | `figures/` beneath the selected output directory |

The existing verification program also regenerates `primary/primary_pair_results.json` from the 34 included count tables. This supplies every input needed by `run_comparison.py`.

## Individual commands

```bash
python workstreams/paper1_checkpoint_2026-09-23/scripts/run_tcr_reference.py
python workstreams/paper1_checkpoint_2026-09-23/scripts/run_ribosome_reference.py
python workstreams/ribosome_separate_output_2026-09-24/src/evaluate_separate_output.py runs/separate_output.json
python workstreams/method_comparison_2026-09-23/src/run_comparison.py --inputs runs/primary-001/primary/primary_pair_results.json --out runs/information-002
```

Create `runs/` before using the separate-output command. Each calculation preserves the original scientific program. The figure wrapper copies the original figure program into the selected output directory before running it, because that program writes beside itself. The original figure source is unchanged.

## Comparison with archived outputs

The archived result identities are in `reference_results/expected_information_sha256.json`. Local reproduction of the public primary entry point matched all three recorded outputs exactly. The run manifest records each generated digest so the result can be checked independently.

The generated primary-pair file contains more fields than the historical compact input file. Consequently, the input-file hash in the newly generated `summary.json` can differ from the historical summary while the three scientific result files remain byte-identical. Input-file identity and numerical result identity are recorded separately.

## Complete Msn2 derived analysis

```bash
python tools/verify_msn2_derived.py --out runs/msn2-derived-validation-001.json
```

Choose a new output file. The verifier first checks the archived identities of all nine Msn2 data and result files. It then reconstructs thresholds and counts from all 40,458 saved scalar-feature rows and recomputes all 1,360 comparisons across the five response definitions. It checks 170 condition records, 10 threshold records, 10 summaries, 40 reference contrasts and the pairing-reveal calculation with its 40 nested-interval checks. The 34 primary count records are also compared with those used by the primary reproduction command.

Exact fractions, count values, labels and other discrete fields must match exactly. Floating values use absolute and relative tolerances of 1e-12. The report records the largest floating difference and byte agreement for each regenerated analysis JSON file. It separately requires exact byte agreement for the descriptive pairing-reveal output. Archived files are preserved.

The transfer verification found zero numerical differences and exact byte agreement for all five regenerated analysis JSON files. The report in `provenance/msn2_archive_validation.json` records that execution. The automated workflow repeats this check from the public checkout and stores its new report in the workflow output artifact.

The six additional comparison-guard tests cover exact values, floating tolerances, missing fields, missing rows and nonfinite values. These are software tests, separate from scientific or biological validation.

## Original fluorescence data

See [Data provenance](DATA_PROVENANCE.md) for the source DOI and pinned archive digest. The source command regenerates all five response definitions from the original trajectories. This calculation is distinct from both the primary binary-count entry point and the scalar-feature verification above. The original data archive is not redistributed here.

## Interpretation

The equal input prior and binary reporter definitions are declared analysis choices. Reported bounds range over the specified compatible probability distributions. They are not confidence intervals for population parameters. These calculations are distinct from estimating the capacity of the original multilevel fluorescence channels.
