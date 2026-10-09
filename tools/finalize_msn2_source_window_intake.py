#!/usr/bin/env python3
"""Finalize the reviewed Msn2 source-window sensitivity intake.

This is a one-run branch utility. It copies the independently generated
sensitivity record into provenance, updates the public documentation and
manifests, refreshes generated artifact indexes, and removes itself and the
temporary intake workflow before the final commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import generate_artifacts as bundle


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"Expected one documentation anchor in {path}, found {text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def manifest_entry(relative_path: str) -> dict[str, object]:
    path = ROOT / relative_path
    data = path.read_bytes()
    return {
        "path": relative_path,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob": hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest(),
    }


def update_documentation() -> None:
    methods = ROOT / "METHODS_MAP.md"
    anchor = (
        "| Source fluorescence preprocessing | "
        "[process_msn2_fluorescence.py](tools/process_msn2_fluorescence.py) | "
        "Scalar features, count tables and comparisons |\n"
    )
    replace_once(
        methods,
        anchor,
        anchor
        + "| Source-window sensitivity | "
        "[check_msn2_source_window.py](tools/check_msn2_source_window.py) | "
        "[msn2_source_window_sensitivity.json]"
        "(provenance/msn2_source_window_sensitivity.json) |\n",
    )

    provenance = ROOT / "docs/DATA_PROVENANCE.md"
    anchor = (
        "The supplied count and feature records support the default artifact "
        "calculations. Fluorescence preprocessing uses the separately downloaded "
        "source ZIP.\n\n"
    )
    replace_once(
        provenance,
        anchor,
        anchor
        + "## Check the source maximum window\n\n"
        "The source publication states that each trace was smoothed with an "
        "11-point moving average and that the maximum was taken over elements 33 "
        "to 64. It does not specify how the moving average treats the ends of the "
        "trace. The independent sensitivity tool evaluates three plausible readings "
        "of that statement and compares each with the primary maximum across all "
        "complete centered windows.\n\n"
        "```bash\n"
        "python tools/check_msn2_source_window.py \\\n"
        "    --archive /path/to/Supplementary_Source_Data.zip \\\n"
        "    --out provenance/msn2_source_window_sensitivity.json \\\n"
        "    --replace\n"
        "```\n\n"
        "The tool verifies the pinned source archive, reconstructs the primary "
        "response independently, and checks it against the saved thresholds, Tables "
        "4 and 5, featured accuracy values, summary widths and conditional-independence "
        "counts. Classification bounds use exact rational arithmetic. Information "
        "minima use bounded numerical optimization and serve as a robustness check; "
        "the primary manuscript bounds retain the rational certificates in "
        "`src/bics/matched_information.py`.\n\n"
        "The recorded sensitivity result is "
        "[msn2_source_window_sensitivity.json]"
        "(../provenance/msn2_source_window_sensitivity.json). Across the three "
        "source-window readings, at most 1.656% of cells changed binary state and no "
        "Table 4 or Table 5 information entry changed by more than 0.019183 bits. "
        "The source ZIP is downloaded separately and is not included in the "
        "repository, so this audit is outside `generate_artifacts.py`.\n\n",
    )

    reproducing = ROOT / "docs/REPRODUCING.md"
    anchor = (
        "[Data provenance](DATA_PROVENANCE.md) describes the source publications "
        "and the optional reconstruction from fluorescence trajectories. The "
        "primary artifact calculations use the files supplied in `data/`.\n"
    )
    replace_once(
        reproducing,
        anchor,
        anchor
        + "\nThe independent source-window sensitivity analysis requires the "
        "separately downloaded Hansen and O'Shea fluorescence archive:\n\n"
        "```bash\n"
        "python tools/check_msn2_source_window.py \\\n"
        "    --archive /path/to/Supplementary_Source_Data.zip \\\n"
        "    --out provenance/msn2_source_window_sensitivity.json \\\n"
        "    --replace\n"
        "```\n\n"
        "The committed sensitivity record validates the primary reconstruction "
        "against repository references with an absolute tolerance of `1e-6`. A "
        "repeated run writes canonical JSON and can be compared byte for byte when "
        "the pinned environment is used.\n",
    )

    provenance_readme = ROOT / "provenance/README.md"
    replace_once(
        provenance_readme,
        "`source_manifest.json` records file paths, sizes and checksums for the "
        "executable code and supplied data. `msn2_manifest.json` identifies the nine "
        "files used in the full Msn2 reconstruction. The artifact manifest records "
        "generated file identities.\n",
        "`source_manifest.json` records file paths, sizes and checksums for the "
        "executable code, supplied data and source-window sensitivity record. "
        "`msn2_manifest.json` identifies the nine files used in the full Msn2 "
        "reconstruction. `msn2_source_window_sensitivity.json` records the independent "
        "check of alternative readings of the source maximum window. The artifact "
        "manifest records generated file identities.\n",
    )

    example = ROOT / "examples/03_msn2_reporters/README.md"
    anchor = (
        "Add `--full-derived` to reconstruct all 1,360 comparisons across five "
        "response definitions from the 40,458 supplied scalar fluorescence records. "
        "The full artifact generator includes this check. "
        "[Data provenance](../../docs/DATA_PROVENANCE.md) provides the source "
        "trajectory preprocessing command.\n\n"
    )
    replace_once(
        example,
        anchor,
        anchor
        + "## Source-window sensitivity\n\n"
        "The source paper specifies an 11-point moving average and a maximum over "
        "elements 33 to 64 but does not state how smoothing treats the trace ends. "
        "[check_msn2_source_window.py]"
        "(../../tools/check_msn2_source_window.py) independently evaluates three "
        "plausible readings of that definition. It validates the primary "
        "all-complete-window reconstruction against the repository results before "
        "reporting the sensitivity analysis.\n\n"
        "```bash\n"
        "python tools/check_msn2_source_window.py \\\n"
        "    --archive /path/to/Supplementary_Source_Data.zip \\\n"
        "    --out provenance/msn2_source_window_sensitivity.json \\\n"
        "    --replace\n"
        "```\n\n"
        "The validated record is [msn2_source_window_sensitivity.json]"
        "(../../provenance/msn2_source_window_sensitivity.json). The source archive "
        "is not stored in this repository.\n\n",
    )


def update_generator_and_tests() -> None:
    generator = ROOT / "generate_artifacts.py"
    anchor = """        lines += ['## Supporting outputs', '',
                  'The figure reads the calculated CSV tables. `figure_data.json` records the plotted rows and their hashes.', '',
                  '[Parameters used](parameters_used.json) and [verification record](verification.json).', '',
                  'Other CSV and JSON files in this directory contain the accompanying calculations. '
                  'The verification record identifies every source file checked and output produced.', '']
"""
    replacement = anchor + """        if directory == '03_msn2_reporters':
            lines += ['## Source-window sensitivity', '',
                      'An independent check of three plausible readings of the source maximum window is recorded in '
                      '[`provenance/msn2_source_window_sensitivity.json`](../../provenance/msn2_source_window_sensitivity.json). '
                      'The separately downloaded fluorescence archive is required to rerun '
                      '[`tools/check_msn2_source_window.py`](../../tools/check_msn2_source_window.py).', '']
"""
    replace_once(generator, anchor, replacement)

    test_path = ROOT / "tests/test_msn2_source_window.py"
    anchor = '''    def test_json_writer_is_canonical_and_refuses_implicit_overwrite(self):
        record = {"b": 2, "a": 1}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            window.write_json(path, record)
            first = path.read_bytes()
            self.assertEqual(first, b'{\\n  "a": 1,\\n  "b": 2\\n}\\n')
            with self.assertRaises(FileExistsError):
                window.write_json(path, record)
            window.write_json(path, record, replace=True)
            self.assertEqual(path.read_bytes(), first)


if __name__ == "__main__":
'''
    replacement = '''    def test_json_writer_is_canonical_and_refuses_implicit_overwrite(self):
        record = {"b": 2, "a": 1}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            window.write_json(path, record)
            first = path.read_bytes()
            self.assertEqual(first, b'{\\n  "a": 1,\\n  "b": 2\\n}\\n')
            with self.assertRaises(FileExistsError):
                window.write_json(path, record)
            window.write_json(path, record, replace=True)
            self.assertEqual(path.read_bytes(), first)

    def test_committed_sensitivity_record(self):
        path = ROOT / "provenance/msn2_source_window_sensitivity.json"
        record = __import__("json").loads(path.read_text(encoding="utf-8"))
        self.assertEqual(record["reference_validation"]["status"], "PASS")
        self.assertEqual(record["reference_validation"]["tolerance"], 1e-6)
        expected = {
            "A_centered_centers_33_to_59": (30, 0.001636),
            "B_shrinking_window_33_to_64": (670, 0.019183),
            "C_trailing_filter_33_to_64": (7, 0.00169),
        }
        for name, (changed, maximum_delta) in expected.items():
            result = record["results"][name]
            self.assertEqual(result["cells_with_changed_binary_state"]["count"], changed)
            self.assertEqual(result["max_abs_change_in_table_4_and_5_bits"], maximum_delta)
        for strain in ("1x", "2x"):
            primary = record["results"]["all_complete_windows"]["all_pairs"][strain]
            self.assertEqual(primary["pairs"], 136)


if __name__ == "__main__":
'''
    replace_once(test_path, anchor, replacement)


def refresh_source_manifest() -> None:
    manifest_path = ROOT / "provenance/source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = {item["path"] for item in manifest["files"]}
    paths.update({
        "provenance/README.md",
        "provenance/msn2_source_window_sensitivity.json",
        "tests/test_msn2_source_window.py",
        "tools/check_msn2_source_window.py",
    })
    paths.discard("provenance/source_manifest.json")
    missing = [path for path in sorted(paths) if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing source-manifest paths: {missing}")
    manifest["files"] = [manifest_entry(path) for path in sorted(paths)]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def refresh_artifact_indexes() -> None:
    bundle.write_index(ROOT / "artifacts")
    manifest_path = ROOT / "artifacts/artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_manifest_sha256"] = bundle.sha256(
        ROOT / "provenance/source_manifest.json"
    )
    manifest["source_sha256"] = bundle.source_records()
    manifest["documentation_generator_sha256"] = bundle.sha256(
        ROOT / "generate_artifacts.py"
    )
    for relative in (
        "README.md",
        "01_tcell_proofreading/README.md",
        "02_ribosome_selection/README.md",
        "03_msn2_reporters/README.md",
    ):
        path = ROOT / "artifacts" / relative
        manifest["files"][relative] = {
            "bytes": path.stat().st_size,
            "sha256": bundle.sha256(path),
        }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", type=Path, required=True)
    args = parser.parse_args()
    generated = args.generated.expanduser().resolve()
    if not generated.is_file():
        parser.error(f"Generated sensitivity record not found: {generated}")
    record = json.loads(generated.read_text(encoding="utf-8"))
    if record.get("reference_validation", {}).get("status") != "PASS":
        raise ValueError("Generated sensitivity record did not pass repository validation")
    destination = ROOT / "provenance/msn2_source_window_sensitivity.json"
    shutil.copyfile(generated, destination)

    update_documentation()
    update_generator_and_tests()

    temporary = (
        ROOT / ".github/workflows/msn2-source-window-intake.yml",
        Path(__file__).resolve(),
    )
    for path in temporary:
        if path.exists():
            path.unlink()

    refresh_source_manifest()
    refresh_artifact_indexes()
    print("Final source-window sensitivity files integrated.")


if __name__ == "__main__":
    main()
