#!/usr/bin/env python3
"""Test Msn2 results against alternative source-window interpretations.

Hansen and O'Shea (eLife 2015;4:e06559) describe smoothing each trace with
an 11-point moving average and taking the maximum over elements 33 to 64
(1-indexed; 75 to 152.5 min). The manuscript's primary response summary uses
the maximum over all complete centered 11-frame windows. The source does not
state how its filter treats the trace ends, so this independent sensitivity
tool evaluates three plausible readings:

  A  complete centered windows whose centers lie in elements 33 to 59
  B  symmetric windows that shrink at the ends, matching MATLAB ``smooth``
     behavior, with maxima over elements 33 to 64
  C  trailing 11-point windows with outputs at elements 33 to 64

For each reading the tool reconstructs equal-protocol median thresholds,
four-state response counts, the Table 4 and Table 5 information values,
classification-accuracy bounds for every protocol pair, the widest comparison
in each strain, and conditional-independence over/under counts. It imports no
code from ``src/bics``. Classification bounds use exact rational arithmetic and
finite arrangement-vertex enumeration. Mutual-information minima use a
normalized bounded numerical search and are a sensitivity check rather than a
replacement for the certified primary bounds in ``src/bics``.

The source archive is not stored in this repository. Download the Dryad source
archive or use the publisher supplement that contains it, then run from the
repository root:

    python tools/check_msn2_source_window.py \
        --archive /path/to/Supplementary_Source_Data.zip \
        --out provenance/msn2_source_window_sensitivity.json \
        --replace
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction as F
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import zipfile

import numpy as np
import scipy
from scipy.optimize import minimize

SOURCE_SHA = "a9be1b297d4945aae3b4d0c3d1734ac8ec4788da2e4bed8d43cd380e4783fd2b"
INNER_ARCHIVE_NAME = "elife_poa_e06559_Supplementary_File_1.zip"
STRAINS = ("1x", "2x")
EXPECTED_ROWS = {"1x": 21236, "2x": 19222}
PREFIX = "_SIP18_HXK1_"
CONDITIONS = ("info_theory_untreated",) + tuple(
    "DM_70min_" + dose
    for dose in ("100nM", "175nM", "275nM", "413nM", "690nM", "1117nM", "3uM")
) + (
    "FM1_5min_690nM",
    "FM2_40minINT_690nM",
    "FM3_25minINT_690nM",
    "FM4_175minINT_690nM",
    "FM5_13minINT_690nM",
    "FM6_10minINT_690nM",
    "FM7_786minINT_690nM",
    "FM8_625minINT_690nM",
    "FM9_5minINT_690nM",
)
FEATURED = (
    ("1x", "DM_70min_100nM", "DM_70min_3uM"),
    ("1x", "DM_70min_175nM", "FM7_786minINT_690nM"),
    ("2x", "FM7_786minINT_690nM", "FM8_625minINT_690nM"),
)
REVEAL = ("1x", "DM_70min_175nM", "FM7_786minINT_690nM")
DEFINITIONS = {
    "all_complete_windows": (
        "Manuscript primary: maximum over all complete centered 11-frame windows"
    ),
    "A_centered_centers_33_to_59": (
        "Source reading A: complete centered windows, centers in elements 33 to 59"
    ),
    "B_shrinking_window_33_to_64": (
        "Source reading B: end-shrinking symmetric window, elements 33 to 64"
    ),
    "C_trailing_filter_33_to_64": (
        "Source reading C: trailing 11-point filter, outputs at elements 33 to 64"
    ),
}
DIRECTION = (F(1), F(-1), F(-1), F(1))
REFERENCE_TOLERANCE = 1e-6


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_archive_bytes(path: Path, expected_sha: str = SOURCE_SHA) -> tuple[bytes, dict[str, object]]:
    """Return the pinned inner source ZIP from a direct file or publisher bundle."""
    raw = path.read_bytes()
    outer_sha = sha256_bytes(raw)
    if outer_sha == expected_sha:
        return raw, {
            "input_kind": "pinned_source_archive",
            "input_sha256": outer_sha,
            "input_bytes": len(raw),
            "source_archive_sha256": outer_sha,
            "source_archive_bytes": len(raw),
        }

    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as outer:
            duplicate_names = len(outer.namelist()) != len(set(outer.namelist()))
            if duplicate_names:
                raise ValueError("Publisher bundle contains duplicate member names.")
            corrupt = outer.testzip()
            if corrupt is not None:
                raise ValueError(f"Publisher bundle CRC check failed at {corrupt}.")
            matches = [
                name for name in outer.namelist()
                if Path(name).name == INNER_ARCHIVE_NAME
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Publisher bundle must contain exactly one {INNER_ARCHIVE_NAME}; "
                    f"found {len(matches)}."
                )
            inner = outer.read(matches[0])
    except zipfile.BadZipFile as exc:
        raise ValueError(
            f"Archive SHA-256 {outer_sha} differs from the pinned source {expected_sha}, "
            "and the input is not a valid publisher ZIP bundle."
        ) from exc

    inner_sha = sha256_bytes(inner)
    if inner_sha != expected_sha:
        raise ValueError(
            f"Nested source SHA-256 {inner_sha} differs from the pinned source {expected_sha}."
        )
    return inner, {
        "input_kind": "publisher_bundle",
        "input_sha256": outer_sha,
        "input_bytes": len(raw),
        "nested_member": matches[0],
        "source_archive_sha256": inner_sha,
        "source_archive_bytes": len(inner),
    }


def expected_member_names(
    strains: tuple[str, ...] = STRAINS,
    conditions: tuple[str, ...] = CONDITIONS,
) -> dict[tuple[str, str], str]:
    return {
        (strain, condition): f"source_data/{strain}{PREFIX}{condition}.txt"
        for strain in strains
        for condition in conditions
    }


def load_archive(
    archive: Path,
    *,
    expected_sha: str = SOURCE_SHA,
    strains: tuple[str, ...] = STRAINS,
    conditions: tuple[str, ...] = CONDITIONS,
    expected_rows: dict[str, int] | None = EXPECTED_ROWS,
) -> tuple[dict[tuple[str, str], np.ndarray], dict[str, object]]:
    """Load and validate the paired-reporter matrices from the pinned source ZIP."""
    inner, archive_record = _source_archive_bytes(archive, expected_sha)
    expected = expected_member_names(strains, conditions)
    expected_names = set(expected.values())

    try:
        with zipfile.ZipFile(io.BytesIO(inner)) as source:
            names = source.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Source archive contains duplicate member names.")
            corrupt = source.testzip()
            if corrupt is not None:
                raise ValueError(f"Source archive CRC check failed at {corrupt}.")

            paired_names = {
                name for name in names
                if name.startswith("source_data/")
                and Path(name).name[:2] in strains
                and PREFIX in Path(name).name
                and name.endswith(".txt")
            }
            missing = sorted(expected_names - set(names))
            unexpected = sorted(paired_names - expected_names)
            if missing or unexpected:
                raise ValueError(
                    "Source paired-reporter inventory differs from the expected 34 files. "
                    f"Missing: {missing}; unexpected: {unexpected}."
                )

            data: dict[tuple[str, str], np.ndarray] = {}
            member_records = []
            for key, name in sorted(expected.items()):
                payload = source.read(name)
                matrix = np.loadtxt(io.BytesIO(payload), delimiter=",", ndmin=2)
                if matrix.ndim != 2 or matrix.shape[1] != 128 or matrix.shape[0] == 0:
                    raise ValueError(f"{name}: expected a nonempty n by 128 matrix.")
                if not np.isfinite(matrix).all():
                    raise ValueError(f"{name}: nonfinite fluorescence value found.")
                if (matrix < 0).any():
                    raise ValueError(f"{name}: negative fluorescence value found.")
                if key in data:
                    raise ValueError(f"Duplicate biological member key: {key}.")
                data[key] = matrix
                member_records.append({
                    "strain": key[0],
                    "condition": key[1],
                    "member": name,
                    "sha256": sha256_bytes(payload),
                    "rows": int(matrix.shape[0]),
                    "columns": int(matrix.shape[1]),
                })
    except zipfile.BadZipFile as exc:
        raise ValueError("Pinned source bytes are not a valid ZIP archive.") from exc

    row_totals = {
        strain: int(sum(len(matrix) for (s, _), matrix in data.items() if s == strain))
        for strain in strains
    }
    if expected_rows is not None:
        for strain in strains:
            expected_total = expected_rows[strain]
            if row_totals[strain] != expected_total:
                raise ValueError(
                    f"{strain}: expected {expected_total} rows, found {row_totals[strain]}."
                )
    archive_record.update({
        "members": member_records,
        "paired_reporter_members": len(member_records),
        "row_totals": row_totals,
    })
    return data, archive_record


def features(matrix: np.ndarray) -> dict[str, np.ndarray]:
    """Return per-cell SIP18 and HXK1 maxima under all four definitions."""
    if matrix.ndim != 2 or matrix.shape[1] != 128 or matrix.shape[0] == 0:
        raise ValueError("Require a nonempty n by 128 fluorescence matrix.")
    if not np.isfinite(matrix).all() or (matrix < 0).any():
        raise ValueError("Fluorescence matrix must contain finite nonnegative values.")

    traces = matrix.reshape(len(matrix), 2, 64)
    centered = np.lib.stride_tricks.sliding_window_view(
        traces, 11, axis=-1
    ).mean(axis=-1)
    shrinking = np.empty(traces.shape, dtype=float)
    for frame in range(64):
        half_width = min(5, frame, 63 - frame)
        shrinking[..., frame] = traces[
            ..., frame - half_width:frame + half_width + 1
        ].mean(axis=-1)

    return {
        "all_complete_windows": centered.max(axis=-1),
        "A_centered_centers_33_to_59": centered[..., 27:].max(axis=-1),
        "B_shrinking_window_33_to_64": shrinking[..., 32:].max(axis=-1),
        "C_trailing_filter_33_to_64": centered[..., 22:].max(axis=-1),
    }


def equal_group_quantile(groups: list[np.ndarray], q: F = F(1, 2)) -> float:
    """Inverse empirical CDF with exactly equal weight assigned to each group."""
    if not groups or not F(0) < q <= 1:
        raise ValueError("Require nonempty groups and a quantile in (0, 1].")
    ordered = []
    for group in groups:
        values = np.asarray(group, dtype=float)
        if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
            raise ValueError("Each quantile group must be a nonempty finite vector.")
        ordered.append(np.sort(values))
    candidates = np.unique(np.concatenate(ordered))
    lo, hi = 0, len(candidates) - 1
    while lo < hi:
        middle = (lo + hi) // 2
        value = candidates[middle]
        cdf = sum(
            (F(int(np.searchsorted(group, value, side="right")), len(group))
             for group in ordered),
            F(0),
        ) / len(ordered)
        if cdf >= q:
            hi = middle
        else:
            lo = middle + 1
    return float(candidates[lo])


def probabilities(counts: tuple[int, ...] | np.ndarray) -> tuple[F, ...]:
    integers = tuple(int(value) for value in counts)
    if len(integers) != 4 or any(value < 0 for value in integers):
        raise ValueError("Require four nonnegative response counts.")
    total = sum(integers)
    if total <= 0:
        raise ValueError("Response counts must have a positive total.")
    return tuple(F(value, total) for value in integers)


def family_exact(
    counts0: tuple[int, ...] | np.ndarray,
    counts1: tuple[int, ...] | np.ndarray,
    reveal: tuple[bool, bool] = (False, False),
) -> dict[str, object]:
    rows = (probabilities(counts0), probabilities(counts1))
    a = tuple(row[2] + row[3] for row in rows)
    b = tuple(row[1] + row[3] for row in rows)
    bounds = []
    for source in (0, 1):
        lower = max(F(0), a[source] + b[source] - 1)
        upper = min(a[source], b[source])
        if reveal[source]:
            lower = upper = rows[source][3]
        bounds.append((lower, upper))
    return {"rows": rows, "a": a, "b": b, "bounds": tuple(bounds)}


def joint_exact(a: F, b: F, t: F) -> tuple[F, ...]:
    return (1 - a - b + t, b - t, a - t, t)


def accuracy_exact(row0: tuple[F, ...], row1: tuple[F, ...]) -> F:
    return sum((max(x, y) for x, y in zip(row0, row1)), F(0)) / 2


def arrangement_candidates(family: dict[str, object]) -> tuple[tuple[F, F], ...]:
    a = family["a"]
    b = family["b"]
    bounds = family["bounds"]
    constants = tuple(
        (1 - a[source] - b[source], b[source], a[source], F(0))
        for source in (0, 1)
    )
    lines: list[tuple[F, F, F]] = []
    for value in bounds[0]:
        lines.append((F(1), F(0), value))
    for value in bounds[1]:
        lines.append((F(0), F(1), value))
    for outcome in range(4):
        direction = DIRECTION[outcome]
        lines.append((direction, -direction, constants[1][outcome] - constants[0][outcome]))

    points = {(x, y) for x in bounds[0] for y in bounds[1]}
    for (aa, bb, cc), (dd, ee, ff) in itertools.combinations(lines, 2):
        determinant = aa * ee - bb * dd
        if determinant == 0:
            continue
        x = (cc * ee - bb * ff) / determinant
        y = (aa * ff - cc * dd) / determinant
        if bounds[0][0] <= x <= bounds[0][1] and bounds[1][0] <= y <= bounds[1][1]:
            points.add((x, y))
    return tuple(sorted(points))


def accuracy_bounds(
    counts0: tuple[int, ...] | np.ndarray,
    counts1: tuple[int, ...] | np.ndarray,
) -> dict[str, object]:
    family = family_exact(counts0, counts1)
    a = family["a"]
    b = family["b"]
    bounds = family["bounds"]
    rows = family["rows"]
    candidates = arrangement_candidates(family)

    def at(point: tuple[F, F]) -> F:
        return accuracy_exact(
            joint_exact(a[0], b[0], point[0]),
            joint_exact(a[1], b[1], point[1]),
        )

    values = [(at(point), point) for point in candidates]
    minimum, minimum_point = min(values)
    corners = tuple((x, y) for x in bounds[0] for y in bounds[1])
    maximum, maximum_point = max((at(point), point) for point in corners)
    observed_point = (rows[0][3], rows[1][3])
    independent_point = (a[0] * b[0], a[1] * b[1])
    return {
        "minimum": float(minimum),
        "maximum": float(maximum),
        "observed": float(at(observed_point)),
        "independence": float(at(independent_point)),
        "candidate_vertices": len(candidates),
        "minimum_point": [str(value) for value in minimum_point],
        "maximum_point": [str(value) for value in maximum_point],
        "method": "exact rational evaluation at finite arrangement vertices",
    }


def entropy(probabilities_: np.ndarray | tuple[float, ...]) -> float:
    values = np.asarray(probabilities_, dtype=float)
    if not np.isfinite(values).all() or (values < -1e-12).any():
        raise ValueError("Invalid probability supplied to entropy.")
    values = np.clip(values, 0.0, None)
    positive = values > 0
    return float(-(values[positive] * np.log2(values[positive])).sum())


def information(row0: np.ndarray, row1: np.ndarray) -> float:
    return entropy((row0 + row1) / 2) - (entropy(row0) + entropy(row1)) / 2


def joint_float(a: float, b: float, t: float) -> np.ndarray:
    row = np.asarray((1 - a - b + t, b - t, a - t, t), dtype=float)
    if (row < -1e-10).any():
        raise ValueError("Joint probability left the compatible family.")
    row = np.clip(row, 0.0, None)
    total = float(row.sum())
    if not math.isclose(total, 1.0, abs_tol=1e-10, rel_tol=1e-10):
        raise ValueError("Joint response row does not sum to one.")
    return row / total


def information_bounds(
    counts0: tuple[int, ...] | np.ndarray,
    counts1: tuple[int, ...] | np.ndarray,
    reveal: tuple[bool, bool] = (False, False),
) -> dict[str, object]:
    family = family_exact(counts0, counts1, reveal)
    exact_rows = family["rows"]
    a = tuple(float(value) for value in family["a"])
    b = tuple(float(value) for value in family["b"])
    bounds = tuple(tuple(float(value) for value in pair) for pair in family["bounds"])
    rows = tuple(np.asarray([float(value) for value in row]) for row in exact_rows)
    variable = tuple(index for index in (0, 1) if bounds[index][1] > bounds[index][0])

    def point_from_unit(unit: np.ndarray | tuple[float, ...]) -> tuple[float, float]:
        unit_values = tuple(float(value) for value in unit)
        point = [bounds[index][0] for index in (0, 1)]
        for coordinate, index in enumerate(variable):
            lower, upper = bounds[index]
            point[index] = lower + unit_values[coordinate] * (upper - lower)
        return point[0], point[1]

    def objective(unit: np.ndarray | tuple[float, ...]) -> float:
        point = point_from_unit(unit)
        value = information(
            joint_float(a[0], b[0], point[0]),
            joint_float(a[1], b[1], point[1]),
        )
        if not math.isfinite(value):
            raise FloatingPointError("Nonfinite mutual-information objective.")
        return max(0.0, float(value))

    corners = tuple((x, y) for x in bounds[0] for y in bounds[1])
    corner_values = [
        information(joint_float(a[0], b[0], point[0]), joint_float(a[1], b[1], point[1]))
        for point in corners
    ]
    maximum = max(corner_values)

    if not variable:
        minimum = corner_values[0]
        search = {
            "algorithm": "singleton compatible family",
            "variable_dimensions": 0,
            "grid_points": 1,
            "starts": 0,
            "converged": 0,
            "grid_minimum_bits": round(float(minimum), 12),
            "best_objective_bits": round(float(minimum), 12),
            "best_unit_point": [],
            "best_message": "not applicable",
        }
    else:
        grid_axis = np.linspace(0.0, 1.0, 41)
        grid_points = list(itertools.product(grid_axis, repeat=len(variable)))
        grid_values = [(objective(point), point) for point in grid_points]
        grid_minimum, grid_point = min(grid_values, key=lambda item: item[0])
        starts = list(itertools.product((0.1, 0.5, 0.9), repeat=len(variable)))
        if tuple(float(value) for value in grid_point) not in starts:
            starts.append(tuple(float(value) for value in grid_point))
        attempts = []
        for start in starts:
            result = minimize(
                objective,
                np.asarray(start, dtype=float),
                method="L-BFGS-B",
                bounds=[(0.0, 1.0)] * len(variable),
                options={"ftol": 1e-15, "gtol": 1e-12, "maxiter": 2000, "maxls": 50},
            )
            attempts.append({
                "method": "L-BFGS-B",
                "success": bool(result.success) and math.isfinite(float(result.fun)),
                "objective": float(result.fun) if math.isfinite(float(result.fun)) else math.inf,
                "point": [float(value) for value in result.x],
                "message": str(result.message),
                "iterations": int(getattr(result, "nit", 0)),
                "evaluations": int(getattr(result, "nfev", 0)),
            })
        successful = [attempt for attempt in attempts if attempt["success"]]
        if not successful:
            for start in starts:
                result = minimize(
                    objective,
                    np.asarray(start, dtype=float),
                    method="Powell",
                    bounds=[(0.0, 1.0)] * len(variable),
                    options={"xtol": 1e-12, "ftol": 1e-15, "maxiter": 4000},
                )
                attempts.append({
                    "method": "Powell",
                    "success": bool(result.success) and math.isfinite(float(result.fun)),
                    "objective": float(result.fun) if math.isfinite(float(result.fun)) else math.inf,
                    "point": [float(value) for value in result.x],
                    "message": str(result.message),
                    "iterations": int(getattr(result, "nit", 0)),
                    "evaluations": int(getattr(result, "nfev", 0)),
                })
            successful = [attempt for attempt in attempts if attempt["success"]]
        if not successful:
            messages = "; ".join(attempt["message"] for attempt in attempts)
            raise RuntimeError(f"No mutual-information minimization run converged: {messages}")
        best = min(successful, key=lambda attempt: attempt["objective"])
        minimum = min(grid_minimum, float(best["objective"]))
        best_point = grid_point if grid_minimum <= best["objective"] else best["point"]
        search = {
            "algorithm": "normalized bounded numerical search",
            "primary_method": "L-BFGS-B",
            "fallback_method": "Powell if no L-BFGS-B run converges",
            "variable_dimensions": len(variable),
            "grid_points": len(grid_points),
            "starts": len(starts),
            "attempts": len(attempts),
            "converged": len(successful),
            "grid_minimum_bits": round(float(grid_minimum), 12),
            "best_objective_bits": round(float(minimum), 12),
            "best_unit_point": [round(float(value), 12) for value in best_point],
            "best_message": str(best["message"]),
            "best_method": str(best["method"]),
        }

    observed = information(rows[0], rows[1])
    independent = None
    if not any(reveal):
        independent = information(
            joint_float(a[0], b[0], a[0] * b[0]),
            joint_float(a[1], b[1], a[1] * b[1]),
        )
    return {
        "minimum": float(minimum),
        "maximum": float(maximum),
        "observed": float(observed),
        "independence": None if independent is None else float(independent),
        "minimum_search": search,
        "method": "numerical convex minimization; maximum evaluated at rectangle corners",
    }


def r6(value: object) -> object:
    return None if value is None else round(float(value), 6)


def analyze(data: dict[tuple[str, str], np.ndarray]) -> dict[str, object]:
    feature_values = {key: features(matrix) for key, matrix in data.items()}
    protocols = {
        strain: tuple(condition for condition in CONDITIONS if (strain, condition) in feature_values)
        for strain in STRAINS
    }
    if any(len(protocols[strain]) != len(CONDITIONS) for strain in STRAINS):
        raise AssertionError("Protocol inventory changed after archive loading.")

    def thresholds(definition: str) -> dict[str, tuple[float, float]]:
        return {
            strain: tuple(
                equal_group_quantile(
                    [feature_values[(strain, condition)][definition][:, reporter]
                     for condition in protocols[strain]],
                    F(1, 2),
                )
                for reporter in (0, 1)
            )
            for strain in STRAINS
        }

    def binary(definition: str, threshold: dict[str, tuple[float, float]]) -> dict[tuple[str, str], np.ndarray]:
        return {
            key: feature_values[key][definition] > np.asarray(threshold[key[0]])
            for key in feature_values
        }

    base_threshold = thresholds("all_complete_windows")
    base_bits = binary("all_complete_windows", base_threshold)
    results: dict[str, object] = {}
    for definition, label in DEFINITIONS.items():
        threshold = thresholds(definition)
        bits = binary(definition, threshold)
        counts = {
            key: tuple(int(value) for value in np.bincount(
                2 * values[:, 0].astype(int) + values[:, 1].astype(int), minlength=4
            ))
            for key, values in bits.items()
        }
        entry: dict[str, object] = {
            "definition": label,
            "median_thresholds": {
                strain: {"SIP18": r6(threshold[strain][0]), "HXK1": r6(threshold[strain][1])}
                for strain in STRAINS
            },
        }
        changed = sum(int((bits[key] != base_bits[key]).any(axis=1).sum()) for key in feature_values)
        total = sum(len(values) for values in bits.values())
        entry["cells_with_changed_binary_state"] = {
            "count": changed,
            "of": total,
            "percent": round(100 * changed / total, 4),
        }
        per_reporter = {}
        for strain in STRAINS:
            for reporter_index, reporter in enumerate(("SIP18", "HXK1")):
                reference = np.concatenate([
                    feature_values[(strain, condition)]["all_complete_windows"][:, reporter_index]
                    for condition in protocols[strain]
                ])
                alternative = np.concatenate([
                    feature_values[(strain, condition)][definition][:, reporter_index]
                    for condition in protocols[strain]
                ])
                per_reporter[f"{strain}_{reporter}"] = round(
                    100 * float((np.abs(reference - alternative) > 1e-9).mean()), 4
                )
        entry["percent_of_cells_with_different_maximum"] = per_reporter

        table4 = []
        for strain, condition0, condition1 in FEATURED:
            info_result = information_bounds(counts[(strain, condition0)], counts[(strain, condition1)])
            accuracy_result = accuracy_bounds(counts[(strain, condition0)], counts[(strain, condition1)])
            table4.append({
                "comparison": f"{strain}|{condition0}|{condition1}",
                "information_min_bits": r6(info_result["minimum"]),
                "information_max_bits": r6(info_result["maximum"]),
                "observed_paired_information_bits": r6(info_result["observed"]),
                "conditional_independence_information_bits": r6(info_result["independence"]),
                "accuracy_min": r6(accuracy_result["minimum"]),
                "accuracy_max": r6(accuracy_result["maximum"]),
                "observed_paired_accuracy": r6(accuracy_result["observed"]),
                "independence_accuracy": r6(accuracy_result["independence"]),
                "accuracy_candidate_vertices": accuracy_result["candidate_vertices"],
                "information_minimum_search": info_result["minimum_search"],
            })
        entry["table_4"] = table4

        strain, condition0, condition1 = REVEAL
        table5 = []
        for sustained, pulsed in ((0, 0), (1, 0), (0, 1), (1, 1)):
            info_result = information_bounds(
                counts[(strain, condition0)], counts[(strain, condition1)],
                (bool(sustained), bool(pulsed))
            )
            table5.append({
                "pairing_sustained_retained": sustained,
                "pairing_pulsed_retained": pulsed,
                "information_min_bits": r6(info_result["minimum"]),
                "information_max_bits": r6(info_result["maximum"]),
                "information_minimum_search": info_result["minimum_search"],
            })
        entry["table_5"] = table5

        summary = {}
        for strain in STRAINS:
            widths = []
            over = 0
            under = 0
            for condition0, condition1 in itertools.combinations(protocols[strain], 2):
                result = accuracy_bounds(counts[(strain, condition0)], counts[(strain, condition1)])
                width = result["maximum"] - result["minimum"]
                widths.append((width, condition0, condition1))
                over += result["independence"] > result["observed"]
                under += result["independence"] < result["observed"]
            widths.sort()
            summary[strain] = {
                "pairs": len(widths),
                "median_accuracy_width": r6(np.median([width[0] for width in widths])),
                "widest_comparison": f"{widths[-1][1]}|{widths[-1][2]}",
                "widest_accuracy_width": r6(widths[-1][0]),
                "independence_overestimates_pairs": int(over),
                "independence_underestimates_pairs": int(under),
            }
        entry["all_pairs"] = summary
        results[definition] = entry

    base = results["all_complete_windows"]
    for definition in tuple(DEFINITIONS)[1:]:
        deltas = []
        for table_name in ("table_4", "table_5"):
            for row, reference in zip(results[definition][table_name], base[table_name]):
                for field, value in row.items():
                    if (
                        field.endswith("_bits") and value is not None
                        and reference[field] is not None and "independence" not in field
                    ):
                        deltas.append(abs(float(value) - float(reference[field])))
        results[definition]["max_abs_change_in_table_4_and_5_bits"] = r6(max(deltas))
    return results


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_primary_against_repository(
    record: dict[str, object], repo_root: Path,
    tolerance: float = REFERENCE_TOLERANCE,
) -> dict[str, object]:
    required = (
        repo_root / "data/msn2/thresholds.json",
        repo_root / "data/msn2/summary.json",
        repo_root / "artifacts/03_msn2_reporters/table_4_msn2_information.csv",
        repo_root / "artifacts/03_msn2_reporters/table_5_msn2_pairing.csv",
        repo_root / "artifacts/03_msn2_reporters/primary_records.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Repository reference files are missing: {missing}")

    primary = record["results"]["all_complete_windows"]
    differences: dict[str, list[float]] = {
        "thresholds": [],
        "table_4_information": [],
        "table_5_information": [],
        "featured_accuracy": [],
        "featured_independence_information": [],
        "accuracy_width_summaries": [],
    }
    exact_checks: dict[str, bool] = {}
    thresholds_reference = json.loads(required[0].read_text(encoding="utf-8"))
    threshold_map = {
        row["construct"]: row for row in thresholds_reference
        if row["scheme"] == "primary_median"
    }
    for strain in STRAINS:
        differences["thresholds"].append(abs(
            primary["median_thresholds"][strain]["SIP18"]
            - float(threshold_map[strain]["threshold_SIP18"])
        ))
        differences["thresholds"].append(abs(
            primary["median_thresholds"][strain]["HXK1"]
            - float(threshold_map[strain]["threshold_HXK1"])
        ))

    table4_reference = {row["comparison"]: row for row in _read_csv(required[2])}
    for row in primary["table_4"]:
        reference = table4_reference[row["comparison"]]
        for field in (
            "information_min_bits", "information_max_bits",
            "observed_paired_information_bits",
        ):
            differences["table_4_information"].append(
                abs(float(row[field]) - float(reference[field]))
            )

    table5_reference = {
        (int(row["pairing_sustained_retained"]), int(row["pairing_pulsed_retained"])): row
        for row in _read_csv(required[3])
    }
    for row in primary["table_5"]:
        key = (row["pairing_sustained_retained"], row["pairing_pulsed_retained"])
        reference = table5_reference[key]
        for field in ("information_min_bits", "information_max_bits"):
            differences["table_5_information"].append(
                abs(float(row[field]) - float(reference[field]))
            )

    primary_records = json.loads(required[4].read_text(encoding="utf-8"))
    records_map = {
        (row["construct"], row["condition0"], row["condition1"]): row
        for row in primary_records
    }
    for row, key in zip(primary["table_4"], FEATURED):
        reference = records_map[key]
        differences["featured_accuracy"].extend((
            abs(float(row["accuracy_min"]) - float(reference["marginal_only_accuracy_bounds"][0]["value"])),
            abs(float(row["accuracy_max"]) - float(reference["marginal_only_accuracy_bounds"][1]["value"])),
            abs(float(row["observed_paired_accuracy"]) - float(reference["paired_accuracy"]["value"])),
        ))
        differences["featured_independence_information"].append(abs(
            float(row["conditional_independence_information_bits"])
            - float(reference["independence_completion_MI_bits"])
        ))

    summary_reference = {
        row["construct"]: row
        for row in json.loads(required[1].read_text(encoding="utf-8"))
        if row["scheme"] == "primary_median"
    }
    for strain in STRAINS:
        observed = primary["all_pairs"][strain]
        reference = summary_reference[strain]
        differences["accuracy_width_summaries"].extend((
            abs(float(observed["median_accuracy_width"]) - float(reference["median_marginal_only_width"])),
            abs(float(observed["widest_accuracy_width"]) - float(reference["max_marginal_only_width"]["value"])),
        ))
        exact_checks[f"{strain}_pair_count"] = observed["pairs"] == int(reference["pairs"])
        exact_checks[f"{strain}_independence_over_count"] = (
            observed["independence_overestimates_pairs"]
            == int(reference["independence_overestimates_pairs"])
        )
        exact_checks[f"{strain}_independence_under_count"] = (
            observed["independence_underestimates_pairs"]
            == int(reference["independence_underestimates_pairs"])
        )
        candidate_rows = [row for row in primary_records if row["construct"] == strain]
        widest = max(
            candidate_rows,
            key=lambda row: (
                float(row["marginal_only_accuracy_bounds"][1]["value"])
                - float(row["marginal_only_accuracy_bounds"][0]["value"])
            ),
        )
        exact_checks[f"{strain}_widest_comparison"] = observed["widest_comparison"] == (
            f"{widest['condition0']}|{widest['condition1']}"
        )

    maxima = {name: max(values, default=0.0) for name, values in differences.items()}
    failed_numeric = {name: value for name, value in maxima.items() if value > tolerance}
    failed_exact = [name for name, passed in exact_checks.items() if not passed]
    if failed_numeric or failed_exact:
        raise AssertionError(
            "Independent primary reconstruction differs from repository references: "
            f"numeric={failed_numeric}, exact={failed_exact}."
        )
    return {
        "status": "PASS",
        "tolerance": tolerance,
        "max_abs_difference": {name: round(value, 12) for name, value in maxima.items()},
        "exact_checks": exact_checks,
        "reference_files": [path.relative_to(repo_root).as_posix() for path in required],
    }


def build_record(
    archive: Path, repo_root: Path,
    tolerance: float = REFERENCE_TOLERANCE,
) -> dict[str, object]:
    data, archive_record = load_archive(archive)
    record: dict[str, object] = {
        "scope": "Sensitivity of Msn2 binary-response results to the window of the per-cell maximum",
        "origin": (
            "Independent source-window sensitivity implementation initiated during Claude review "
            "and hardened under separate GPT review; no imports from src/bics"
        ),
        "numerical_scope": (
            "Classification bounds are exact for the empirical rational response counts. "
            "Information minima use bounded numerical optimization and serve as a robustness check; "
            "the primary manuscript bounds retain rational certificates."
        ),
        "source_archive_sha256": SOURCE_SHA,
        "source_archive_bytes": archive_record["source_archive_bytes"],
        "archive_validation": archive_record,
        "strains": list(STRAINS),
        "cells": {
            strain: int(sum(len(matrix) for (s, _), matrix in data.items() if s == strain))
            for strain in STRAINS
        },
        "source_statement": (
            "11-point moving average; maximum over elements 33 to 64 "
            "(1-indexed, 75 to 152.5 min)"
        ),
        "software": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "results": analyze(data),
    }
    record["reference_validation"] = validate_primary_against_repository(
        record, repo_root, tolerance
    )
    return record


def write_json(path: Path, record: dict[str, object], replace: bool = False) -> None:
    if path.exists() and not replace:
        raise FileExistsError(f"Output exists: {path}. Use --replace to overwrite it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--archive", type=Path, required=True,
        help="Pinned Hansen and O'Shea source archive or publisher bundle",
    )
    parser.add_argument("--out", type=Path, required=True, help="Output JSON path")
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1],
        help="Repository root used to validate the primary calculation",
    )
    parser.add_argument(
        "--reference-tolerance", type=float, default=REFERENCE_TOLERANCE,
        help="Absolute tolerance for the independent primary-reference comparison",
    )
    parser.add_argument(
        "--replace", action="store_true", help="Replace an existing output file"
    )
    args = parser.parse_args()
    if args.reference_tolerance <= 0 or not math.isfinite(args.reference_tolerance):
        parser.error("--reference-tolerance must be a finite positive number")
    archive = args.archive.expanduser().resolve()
    repo_root = args.repo_root.expanduser().resolve()
    if not archive.is_file():
        parser.error(f"Archive not found: {archive}")
    record = build_record(archive, repo_root, args.reference_tolerance)
    write_json(args.out.expanduser().resolve(), record, args.replace)
    for name, entry in record["results"].items():
        changed = entry["cells_with_changed_binary_state"]
        print(
            f"{name}: {changed['count']} of {changed['of']} cells change state; "
            f"max Table 4/5 change "
            f"{entry.get('max_abs_change_in_table_4_and_5_bits', 0)} bits"
        )
    print("Reference validation: PASS")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AssertionError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
