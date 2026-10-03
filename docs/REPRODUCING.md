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

## Original fluorescence data

See [Data provenance](DATA_PROVENANCE.md) for the source DOI and pinned archive digest. The source command regenerates all five response definitions. This larger calculation is distinct from the primary binary-count entry point. The original data archive is not redistributed here.

## Interpretation

The equal input prior and binary reporter definitions are declared analysis choices. Reported bounds range over the specified compatible probability distributions. They are not confidence intervals for population parameters. These calculations are distinct from estimating the capacity of the original multilevel fluorescence channels.
