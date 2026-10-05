# Data provenance

## Published source

Hansen AS and O'Shea EK. Limits on information transduction through amplitude and frequency regulation of transcription factor activity. eLife 4:e06559 (2015). DOI [10.7554/eLife.06559](https://doi.org/10.7554/eLife.06559).

Source data are deposited at Dryad under DOI [10.5061/dryad.97vt8](https://doi.org/10.5061/dryad.97vt8). The deposit lists `Supplementary_Source_Data.zip` and its README. Cite this source separately from the present analysis.

The preprocessing program uses an inner source-data archive with SHA-256

```text
a9be1b297d4945aae3b4d0c3d1734ac8ec4788da2e4bed8d43cd380e4783fd2b
```

The preprocessing program accepts that archive directly or a publisher supplement containing it. It checks this identity before analysis. Obtain the fluorescence trajectories from the data deposit. The repository includes the derived features and count records described below.

## Included primary inputs

`workstreams/paper1_checkpoint_2026-09-23/verification_2026-10-02/primary_condition_counts.json` contains 34 records. Each record identifies the reporter construct, input protocol and four counts in the order `00, 01, 10, 11`. The records cover 17 protocols for each of two constructs and use the primary binary response definition.

The count totals are 21,236 cells for the one-copy construct and 19,222 for the two-copy construct. These totals count deposited cell records. Independent experimental units require the corresponding experimental metadata. `primary_counts_provenance.json` records the source and extraction scope.

The primary reproduction command derives all 272 within-construct protocol-pair comparisons from these counts. Its generated pair file is the complete input for the information and decision comparison program. All required count records are included in this repository.

## Included derived data

The saved files under `workstreams/msn2_pairing_2026-09-23/results/analysis/` contain 40,458 rows of scalar fluorescence features, 170 condition-count records, 10 threshold records with two reporter thresholds each, 1,360 comparisons across five response definitions, 40 reference contrasts and 10 summaries. Source-member provenance and the zero-value audit are included. The saved `results/constraint_reveal.json` contains 10 descriptive cases and 40 checks of nested accuracy intervals.

[The derived-data manifest](../provenance/msn2_archive_manifest.json) records the size, SHA-256 digest and Git object identity of each of the nine files.

`tools/verify_msn2_derived.py` reconstructs all five response definitions from the saved scalar features using the analysis functions. It verifies the thresholds, counts, pair comparisons, summaries, reference contrasts and pairing-reveal results. This check starts with features extracted from smoothed trajectories. For the saved zero-value audit it checks file identity and dimensions. Processing the deposited traces produces that audit.

## Process deposited fluorescence trajectories

```bash
python workstreams/msn2_pairing_2026-09-23/src/analyze_msn2.py --archive /path/to/Supplementary_Source_Data.zip --out runs/msn2-from-source-001
python workstreams/msn2_pairing_2026-09-23/src/reveal_pairing.py --results runs/msn2-from-source-001/pair_results.json --out runs/pairing-reveal-001.json
```

The preprocessing program defines the smoothing and trace summary. It also specifies thresholds and the treatment of zero values. The primary response uses the maximum of complete 11-point moving-average windows and median thresholds calibrated separately for each reporter. Four alternate response definitions are available in the same program.

These commands generate the derived files from the deposited fluorescence trajectories. The example scripts start with the included count records. The full derived-data verification starts with the included scalar features.

## Measurement scope

Rows are deposited cell records. Assigning cells to independent experiments requires experimental metadata. Numerical zeros are retained as deposited. Binary outcomes reflect reporter properties, measurement noise and source preprocessing as well as biological response.

The analysis uses binary reporter responses and a fixed equal prior for each protocol pair. It asks what separate and paired observations establish under these definitions. Hansen and O'Shea studied joint reporter information using multilevel responses and a bias-corrected channel-capacity estimator. These choices define different information quantities.
