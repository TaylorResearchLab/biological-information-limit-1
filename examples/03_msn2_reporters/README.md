# Example 3. Yeast Msn2 reporters

**Run [run_msn2_reporters.py](run_msn2_reporters.py) to reproduce Tables 4–5, Figure 3 and all 272 primary discrimination comparisons.**

## Biological question

Do the separate frequencies of two reporter responses establish how well their combined response distinguishes two stimulation protocols? How much is resolved when their pairing within the same cells is retained?

## Original source and included data

Hansen AS and O'Shea EK. *Limits on information transduction through amplitude and frequency regulation of transcription factor activity.* eLife (2015). [DOI 10.7554/eLife.06559](https://doi.org/10.7554/eLife.06559). Original data: [Dryad 10.5061/dryad.97vt8](https://doi.org/10.5061/dryad.97vt8).

The primary example starts with the included binary counts of SIP18 and HXK1 responses. There are 17 protocols for each of two reporter constructs. Each count table has four outcomes in the order 00, 01, 10, 11. The primary response definition is `primary_median`. The two protocols in each comparison are equally weighted.

The example regenerates 272 pairwise comparison records using the preserved count-analysis function. It checks the resulting compact records against the archived input bytes. It then executes the original comparison program. That program solves 544 linear programs for decision comparisons. It calculates certified mutual-information bounds for the declared panel of 10 selected comparisons and four pairing-reveal states. Mutual-information bounds are not calculated for all 272 cases by this command.

## Run

Follow the [installation instructions](../../README.md#install-once). From the repository folder:

```bash
python examples/03_msn2_reporters/run_msn2_reporters.py
```

The required counts are already in the repository. An original fluorescence archive download is not required for this command.

## Outputs in `runs/msn2/`

| File | Meaning |
| --- | --- |
| `table_4_msn2_information.csv` | The three comparisons reported in Table 4. [Expected values](expected_results/table_4_msn2_information.csv). |
| `table_5_msn2_pairing.csv` | The four pairing-reveal states in Table 5. [Expected values](expected_results/table_5_msn2_pairing.csv). |
| `all_272_discrimination_comparisons.csv` | Accuracy bounds, observed paired accuracy and the independence-completion accuracy for each primary comparison. |
| `primary_records.json` | Regenerated input records, checked for exact agreement with the archived compact input. |
| `detailed_results/` | The original decision, information-panel, information-reveal and summary JSON outputs with exact byte checks. |
| `figure_3_msn2_information.png` | Figure 3 rendered from the calculated Tables 4–5. |
| `parameters_used.json` / `verification.json` | Response definitions, input weighting, numerical verification, hashes and elapsed time. |

`comparison` fields retain source condition identifiers. `1x` and `2x` denote reporter copy constructs. `DM_70min_175nM` denotes the sustained 175 nM condition. `FM7_786minINT_690nM` and `FM8_625minINT_690nM` identify the seven- and eight-pulse protocols. The numeric labels describe the original experimental protocols; they are not inferred intracellular Msn2 concentrations.

## Full derived archive and original fluorescence processing

To additionally verify the 40,458 archived scalar-feature rows, 170 condition records and all 1,360 comparisons across five definitions:

```bash
python examples/03_msn2_reporters/run_msn2_reporters.py --full-derived --out runs/msn2_all_definitions
```

This adds `all_five_definitions_verification.json`. Original fluorescence smoothing and scalar-feature extraction are upstream of that verification. The [data provenance guide](../../docs/DATA_PROVENANCE.md) provides the source archive identity and separate preprocessing command.

Bounds describe response distributions compatible with the supplied empirical probabilities under the stated choices. They are not population confidence intervals. Withholding pairing changes the available information about the records, not the underlying cell responses.

## Where the methods are implemented

`analyze_counts()` in [analyze_msn2.py](../../workstreams/msn2_pairing_2026-09-23/src/analyze_msn2.py) regenerates the primary records. [run_comparison.py](../../workstreams/method_comparison_2026-09-23/src/run_comparison.py) runs the comparisons. `information_bounds()` and `matched_decision_lps()` are in [matched_information.py](../../workstreams/method_comparison_2026-09-23/src/matched_information.py). The full derived check uses [verify_msn2_derived.py](../../tools/verify_msn2_derived.py).

For another run use `--out runs/msn2_second_run`. Use `--help` for options.
