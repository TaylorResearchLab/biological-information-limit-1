# Data provenance

## Published source

Hansen AS and O'Shea EK. Limits on information transduction through amplitude and frequency regulation of transcription factor activity. eLife 4:e06559 (2015). DOI [10.7554/eLife.06559](https://doi.org/10.7554/eLife.06559).

Source data are deposited at Dryad under DOI [10.5061/dryad.97vt8](https://doi.org/10.5061/dryad.97vt8). The deposit lists `Supplementary_Source_Data.zip` and its README. Cite this source separately from the present analysis.

The reviewed analysis requires an inner source-data archive with SHA-256

```text
a9be1b297d4945aae3b4d0c3d1734ac8ec4788da2e4bed8d43cd380e4783fd2b
```

The original source program accepts that archive directly or a publisher supplement containing it. It verifies the pinned identity before analysis. A differently packaged download must be investigated rather than silently treated as the same input. Raw source data are not redistributed in this repository.

## Included primary inputs

`workstreams/paper1_checkpoint_2026-09-23/verification_2026-10-02/primary_condition_counts.json` contains 34 records. Each record identifies the reporter construct, input protocol and four counts in the order `00, 01, 10, 11`. The records cover 17 protocols for each of two constructs and use the primary binary response definition.

The count totals are 21,236 cells for the one-copy construct and 19,222 for the two-copy construct. These are descriptive counts of deposited cell records, not numbers of independent experiments. `primary_counts_provenance.json` records the source and extraction scope.

The primary reproduction command derives all 272 within-construct protocol-pair comparisons from these counts. Its generated pair file is the complete input for the information and decision comparison program. No private repository access is required for that command.

## Included full derived archive

The saved files under `workstreams/msn2_pairing_2026-09-23/results/analysis/` contain 40,458 rows of scalar fluorescence features, 170 condition-count records, 10 threshold records with two reporter thresholds each, 1,360 comparisons across five response definitions, 40 reference contrasts and 10 summaries. Source-member provenance and the zero-value audit are included. The saved `results/constraint_reveal.json` contains 10 descriptive cases and 40 checks of nested accuracy intervals.

`provenance/msn2_archive_manifest.json` records the size, SHA-256 digest and Git object identity of each of the nine files against scientific checkpoint `32b0e6633ed2f2d9c8a46f98057382bf765822d4`. All transferred bytes match these historical identities. `provenance/msn2_archive_transfer.json` records the transfer method separately from scientific computation.

`tools/verify_msn2_derived.py` reconstructs all five response definitions from the archived scalar features using the unchanged analysis functions. It verifies the thresholds, counts, pair comparisons, summaries, reference contrasts and pairing-reveal results. This check starts after the original trajectory smoothing and feature extraction. The archived zero-value audit is checked for byte identity and dimensions rather than recomputed from raw traces.

## Regenerate from the original archive

```bash
python workstreams/msn2_pairing_2026-09-23/src/analyze_msn2.py --archive /path/to/Supplementary_Source_Data.zip --out runs/msn2-from-source-001
python workstreams/msn2_pairing_2026-09-23/src/reveal_pairing.py --results runs/msn2-from-source-001/pair_results.json --out runs/pairing-reveal-001.json
```

The original program defines its smoothing, trace summary, thresholds, zeros and outcome ordering explicitly. The primary response uses the maximum of complete 11-point moving-average windows and median thresholds calibrated separately for each reporter. Four alternate response definitions are available in the same program.

The commands above provide the generation path from the original source archive for the saved derived files. They are separate from the default binary-count reproduction command and the scalar-feature verification command. Original fluorescence preprocessing was not repeated during the public archive transfer.

## Measurement scope

Rows are deposited cell records. The analysis does not infer cell-to-independent-experiment membership from filenames or row order. Numerical zeros are retained as deposited. Binary outcomes reflect reporter properties, measurement noise and source preprocessing as well as biological response.

The analysis uses a fixed equal prior for each protocol pair. It does not reproduce the source publication's multilevel, bias-corrected channel-capacity estimator. The published source already considered joint reporter information; the present analysis asks what separate versus paired observations establish under the stated binary definitions.
