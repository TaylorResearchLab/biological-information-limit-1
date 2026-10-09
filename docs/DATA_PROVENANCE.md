# Data provenance

## T cell receptor proofreading

McKeithan TW. Kinetic proofreading in T-cell receptor signal transduction. PNAS 92:5042–5046 (1995). DOI [10.1073/pnas.92.11.5042](https://doi.org/10.1073/pnas.92.11.5042).

The example models one encounter beginning with a bound receptor. McKeithan's illustrative dissociation rates give passage probabilities of 10/11 and 1/11. The calculation uses equally weighted ligand classes and a binary completion outcome. These are specified model conditions.

## Ribosomal tRNA selection

Zaher HS and Green R. Hyperaccurate and error-prone ribosomes exploit distinct mechanisms during tRNA selection. Molecular Cell 39:110–120 (2010). DOI [10.1016/j.molcel.2010.06.009](https://doi.org/10.1016/j.molcel.2010.06.009).

Published acceptance summaries supply the cognate and near-cognate ranges. The calculation treats these as a declared sensitivity family. The resulting information bounds describe variation across that family. Source-frequency and upstream-passage values are specified separately. The separate product-assay calculation uses independent source summaries to assess the upstream factor required for an ordering of final product ratios.

## Msn2 reporters

Hansen AS and O'Shea EK. Limits on information transduction through amplitude and frequency regulation of transcription factor activity. eLife 4:e06559 (2015). DOI [10.7554/eLife.06559](https://doi.org/10.7554/eLife.06559).

Source data are deposited at Dryad under DOI [10.5061/dryad.97vt8](https://doi.org/10.5061/dryad.97vt8). The deposit provides the fluorescence trajectories and its README. Cite the source publication and deposit alongside this analysis.

The accepted inner source ZIP has SHA-256:

```text
a9be1b297d4945aae3b4d0c3d1734ac8ec4788da2e4bed8d43cd380e4783fd2b
```

The preprocessing program accepts that archive directly or the publisher supplement containing it and verifies its checksum.

## Supplied observations

[Primary counts](../data/msn2/primary_condition_counts.json) contain 34 records covering 17 protocols for each of two reporter constructs. Each row supplies counts in the order `00, 01, 10, 11`. The construct totals are 21,236 and 19,222 deposited cell records. The experimental replicate is distinct from the recorded cell.

[Scalar fluorescence features](../data/msn2/cell_features.csv.gz) supply 40,458 records. The full derived dataset contains 170 condition-count tables and 10 reporter-threshold pairs across five response definitions. Its reference calculations contain 1,360 comparisons, 40 reference contrasts and 10 summaries. Member checksums and a numerical-zero audit retain the link to the source trajectories.

The default example starts with the primary binary response counts. `--full-derived` reconstructs all five definitions from the scalar features. The full artifact generator includes this reconstruction. The zero audit is checked against its stored checksum and source matrix dimensions.

## Process the source fluorescence trajectories

```bash
python tools/process_msn2_fluorescence.py --archive /path/to/Supplementary_Source_Data.zip --out runs/msn2_fluorescence
```

The program computes scalar features, all five response definitions and the descriptive pairing-restoration results. The primary response uses the maximum across complete 11-point moving-average windows. Reporter-specific median thresholds are calibrated using equally weighted experimental conditions. Numerical zeros are retained as deposited.

The supplied count and feature records support the default artifact calculations. Fluorescence preprocessing uses the separately downloaded source ZIP.

## Check the source maximum window

The source publication states that each trace was smoothed with an 11-point moving average and that the maximum was taken over elements 33 to 64. It does not specify how the moving average treats the ends of the trace. The independent sensitivity tool evaluates three plausible readings of that statement and compares each with the primary maximum across all complete centered windows.

```bash
python tools/check_msn2_source_window.py \
    --archive /path/to/Supplementary_Source_Data.zip \
    --out provenance/msn2_source_window_sensitivity.json \
    --replace
```

The tool verifies the pinned source archive, reconstructs the primary response independently, and checks it against the saved thresholds, Tables 4 and 5, featured accuracy values, summary widths and conditional-independence counts. Classification bounds use exact rational arithmetic. Information minima use bounded numerical optimization and serve as a robustness check; the primary manuscript bounds retain the rational certificates in `src/bics/matched_information.py`.

The recorded sensitivity result is [msn2_source_window_sensitivity.json](../provenance/msn2_source_window_sensitivity.json). Across the three source-window readings, at most 1.656% of cells changed binary state and no Table 4 or Table 5 information entry changed by more than 0.019183 bits. The source ZIP is downloaded separately and is not included in the repository, so this audit is outside `generate_artifacts.py`.

## Interpretation

The analysis describes the supplied finite records with a fixed equal prior for each protocol pair. The source publication examines multilevel fluorescence and estimates information capacity. The present calculation evaluates binary responses and asks how separate versus paired measurements constrain information and discrimination accuracy. Bounds range over the specified compatible distributions. Population uncertainty depends on an additional sampling model and biological replication.
