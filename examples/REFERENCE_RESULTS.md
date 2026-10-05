# Reference results

The CSV files in each `expected_results/` folder are readable exports of the saved results from public commit `79157d10c2013a6445fd92c4602124c0a6c16fa6`. They are comparison targets, not inputs used to calculate new results. The new example commands preserve numerical precision and check every CSV value with absolute and relative tolerances of 1e-12. Integer counts and completion ratios must match exactly.

Table 1 was exported from the archived TCR driver output. Tables 2–3 and the ribosome sensitivity files were exported from the archived ribosome driver output. Tables 4–5 were exported from the archived information panel and pairing-reveal JSON files. The transfer verification artifact has SHA-256 `1b7269bc5ca776cd3ea7a8f6062f161d7b57ebe8505f88791f7969848da949eb`.

Msn2 additionally checks exact bytes for the regenerated compact input and all four information-analysis JSON files against the existing historical archive. The original scientific files, data and checksums remain unchanged. Generated figures read the new CSV outputs. They are new renderings of the same scientific results and are not claimed to be pixel-identical to the original manuscript figures.
