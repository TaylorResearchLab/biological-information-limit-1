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

## Regenerate from the original archive

```bash
python workstreams/msn2_pairing_2026-09-23/src/analyze_msn2.py --archive /path/to/Supplementary_Source_Data.zip --out runs/msn2-from-source-001
python workstreams/msn2_pairing_2026-09-23/src/reveal_pairing.py --results runs/msn2-from-source-001/pair_results.json --out runs/pairing-reveal-001.json
```

The original program defines its smoothing, trace summary, thresholds, zeros and outcome ordering explicitly. The primary response uses the maximum of complete 11-point moving-average windows and median thresholds calibrated separately for each reporter. Four alternate response definitions are available in the same program.

The larger historical outputs include the derived fluorescence feature table, 170 condition-count records and 1,360 comparisons across five response definitions. Those saved tables are a separate archival addition and are not part of this initial public import. The commands above provide their generation path; they are not run by the default binary-count reproduction command.

## Measurement scope

Rows are deposited cell records. The analysis does not infer cell-to-independent-experiment membership from filenames or row order. Numerical zeros are retained as deposited. Binary outcomes reflect reporter properties, measurement noise and source preprocessing as well as biological response.

The analysis uses a fixed equal prior for each protocol pair. It does not reproduce the source publication's multilevel, bias-corrected channel-capacity estimator. The published source already considered joint reporter information; the present analysis asks what separate versus paired observations establish under the stated binary definitions.
