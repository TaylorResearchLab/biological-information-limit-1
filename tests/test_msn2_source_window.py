"""Tests for the independent Msn2 source-window sensitivity tool."""
from __future__ import annotations

from fractions import Fraction as F
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/check_msn2_source_window.py"
SPEC = importlib.util.spec_from_file_location("check_msn2_source_window", TOOL)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load source-window sensitivity tool")
window = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(window)


class SourceWindowTests(unittest.TestCase):
    def test_equal_group_quantile_weights_protocols_equally(self):
        observed = window.equal_group_quantile(
            [np.array([0.0]), np.array([10.0, 20.0, 30.0])], F(1, 2)
        )
        self.assertEqual(observed, 0.0)

    def test_feature_window_definitions_on_monotone_trace(self):
        trace = np.arange(64, dtype=float)
        matrix = np.concatenate((trace, trace))[None, :]
        result = window.features(matrix)
        self.assertEqual(result["all_complete_windows"].tolist(), [[58.0, 58.0]])
        self.assertEqual(result["A_centered_centers_33_to_59"].tolist(), [[58.0, 58.0]])
        self.assertEqual(result["B_shrinking_window_33_to_64"].tolist(), [[63.0, 63.0]])
        self.assertEqual(result["C_trailing_filter_33_to_64"].tolist(), [[58.0, 58.0]])

    def test_accuracy_bounds_use_finite_exact_candidates(self):
        counts0 = (40, 10, 20, 30)
        counts1 = (25, 25, 10, 40)
        result = window.accuracy_bounds(counts0, counts1)
        self.assertEqual(
            result["method"],
            "exact rational evaluation at finite arrangement vertices",
        )
        self.assertGreaterEqual(result["candidate_vertices"], 4)

        family = window.family_exact(counts0, counts1)
        a = tuple(float(value) for value in family["a"])
        b = tuple(float(value) for value in family["b"])
        bounds = tuple(tuple(float(value) for value in pair) for pair in family["bounds"])
        dense_minimum = 1.0
        for t0 in np.linspace(bounds[0][0], bounds[0][1], 201):
            for t1 in np.linspace(bounds[1][0], bounds[1][1], 201):
                value = 0.5 * np.maximum(
                    window.joint_float(a[0], b[0], t0),
                    window.joint_float(a[1], b[1], t1),
                ).sum()
                dense_minimum = min(dense_minimum, float(value))
        self.assertLessEqual(result["minimum"], dense_minimum + 1e-12)
        self.assertAlmostEqual(result["minimum"], dense_minimum, places=4)

    def test_information_search_records_convergence(self):
        result = window.information_bounds((40, 10, 20, 30), (25, 25, 10, 40))
        search = result["minimum_search"]
        self.assertGreater(search["converged"], 0)
        self.assertGreater(search["grid_points"], 0)
        self.assertTrue(np.isfinite(result["minimum"]))
        self.assertLessEqual(result["minimum"], result["maximum"])

    def test_archive_loader_checks_inventory_and_values(self):
        conditions = ("condition",)
        strains = ("1x", "2x")
        expected = window.expected_member_names(strains, conditions)
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for index, name in enumerate(expected.values()):
                row = ",".join(str(float(value + index)) for value in range(128)) + "\n"
                archive.writestr(name, row)
        raw = payload.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.zip"
            path.write_bytes(raw)
            data, record = window.load_archive(
                path,
                expected_sha=digest,
                strains=strains,
                conditions=conditions,
                expected_rows={"1x": 1, "2x": 1},
            )
        self.assertEqual(set(data), set(expected))
        self.assertEqual(record["paired_reporter_members"], 2)
        self.assertEqual(record["row_totals"], {"1x": 1, "2x": 1})

    def test_archive_loader_rejects_duplicate_members(self):
        name = "source_data/1x_SIP18_HXK1_condition.txt"
        payload = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(payload, "w") as archive:
                row = ",".join("1" for _ in range(128)) + "\n"
                archive.writestr(name, row)
                archive.writestr(name, row)
        raw = payload.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.zip"
            path.write_bytes(raw)
            with self.assertRaises(ValueError):
                window.load_archive(
                    path,
                    expected_sha=digest,
                    strains=("1x",),
                    conditions=("condition",),
                    expected_rows={"1x": 1},
                )

    def test_json_writer_is_canonical_and_refuses_implicit_overwrite(self):
        record = {"b": 2, "a": 1}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            window.write_json(path, record)
            first = path.read_bytes()
            self.assertEqual(first, b'{\n  "a": 1,\n  "b": 2\n}\n')
            with self.assertRaises(FileExistsError):
                window.write_json(path, record)
            window.write_json(path, record, replace=True)
            self.assertEqual(path.read_bytes(), first)


if __name__ == "__main__":
    unittest.main()
