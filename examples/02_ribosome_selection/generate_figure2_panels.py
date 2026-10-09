#!/usr/bin/env python3
"""Generate publication-ready BICS Figure 2B and Figure 2C.

The script reads the verified numerical artifacts:
  - table_2_ribosome_information.csv
  - table_3_ribosome_passage.csv

It writes separate SVG and PNG files for insertion into PowerPoint.
SVG is recommended for the editable PowerPoint assembly. PNG is
written at the requested DPI for journal submission or preview.

Example
-------
python generate_figure2_panels.py \
    --artifact-dir artifacts/02_ribosome_selection \
    --outdir figures/generated
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator


TABLE2_NAME = "table_2_ribosome_information.csv"
TABLE3_NAME = "table_3_ribosome_passage.csv"
PARAMETERS_NAME = "parameters_used.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate BICS Figure 2B and Figure 2C from verified CSV artifacts."
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/02_ribosome_selection"),
        help="Directory containing the two verified CSV artifacts.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("figures/generated"),
        help="Directory for SVG, PNG, and provenance JSON outputs.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="PNG resolution. SVG output remains vector based.",
    )
    parser.add_argument(
        "--panel-labels",
        action="store_true",
        help="Include B and C panel labels inside the exported graphics.",
    )
    parser.add_argument(
        "--opaque",
        action="store_true",
        help="Use a white background. The default is transparent.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Input file contains no data rows: {path}")
    return rows


def read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


def display_number(value: object) -> str:
    """Format a numeric string or fraction from parameters_used.json."""
    text = str(value)
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        try:
            return f"{float(numerator) / float(denominator):g}"
        except ValueError:
            return text
    try:
        return f"{float(text):g}"
    except ValueError:
        return text


def as_float(row: dict[str, str], field: str, source: Path) -> float:
    try:
        value = float(row[field])
    except KeyError as exc:
        raise ValueError(f"Missing column {field!r} in {source}") from exc
    except ValueError as exc:
        raise ValueError(f"Non-numeric value in column {field!r} of {source}") from exc
    if not math.isfinite(value):
        raise ValueError(f"Non-finite value in column {field!r} of {source}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def configure_typography() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "svg.fonttype": "none",  # Preserve text as editable text in SVG.
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.8)


def save_figure(
    fig: plt.Figure,
    stem: Path,
    *,
    dpi: int,
    transparent: bool,
) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    svg_path = stem.with_suffix(".svg")
    png_path = stem.with_suffix(".png")

    common = {
        "bbox_inches": "tight",
        "pad_inches": 0.04,
        "transparent": transparent,
    }
    fig.savefig(svg_path, **common)
    fig.savefig(png_path, dpi=dpi, **common)
    plt.close(fig)
    return [svg_path, png_path]


def plot_panel_b(
    rows: list[dict[str, str]],
    source: Path,
    outdir: Path,
    *,
    dpi: int,
    transparent: bool,
    panel_label: bool,
) -> list[Path]:
    by_name = {row["ribosome_preparation"]: row for row in rows}
    expected = ("wild_type", "restrictive")
    missing = [name for name in expected if name not in by_name]
    if missing:
        raise ValueError(f"Missing expected preparation rows in {source}: {missing}")

    labels = ["Wild type", "Restrictive"]
    lows = [
        as_float(by_name["wild_type"], "information_min_bits", source),
        as_float(by_name["restrictive"], "information_min_bits", source),
    ]
    highs = [
        as_float(by_name["wild_type"], "information_max_bits", source),
        as_float(by_name["restrictive"], "information_max_bits", source),
    ]
    y = [1, 0]

    fig, ax = plt.subplots(figsize=(4.6, 3.25))
    fig.subplots_adjust(left=0.23, right=0.98, bottom=0.27, top=0.68)

    # One collection for both intervals keeps the default visual treatment consistent.
    ax.hlines(y, lows, highs, linewidth=3)
    ax.scatter(lows + highs, y + y, s=32, zorder=3)

    for yi, lo, hi in zip(y, lows, highs):
        ax.annotate(
            f"{lo:.3f}",
            (lo, yi),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )
        ax.annotate(
            f"{hi:.3f}",
            (hi, yi),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_yticks(y, labels)
    ax.set_xlim(0.58, 1.01)
    ax.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylim(-0.55, 1.55)
    ax.set_xlabel("Mutual information (bits)")
    clean_axes(ax)

    fig.suptitle(
        "Information among tRNAs\nreaching proofreading",
        x=0.56,
        y=0.98,
        ha="center",
        va="top",
    )
    fig.text(
        0.56,
        0.80,
        "Calculated bounds from published\nacceptance summaries",
        ha="center",
        va="top",
        fontsize=9,
    )
    fig.text(
        0.56,
        0.075,
        "Equal input weights at entry to proofreading",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    fig.text(
        0.56,
        0.025,
        "Extrema across the stated acceptance sensitivity ranges",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    if panel_label:
        fig.text(0.015, 0.98, "B", ha="left", va="top", fontsize=14, weight="bold")

    return save_figure(
        fig,
        outdir / "figure_2b_local_information",
        dpi=dpi,
        transparent=transparent,
    )


def plot_panel_c(
    rows: list[dict[str, str]],
    source: Path,
    parameters: dict[str, object],
    outdir: Path,
    *,
    dpi: int,
    transparent: bool,
    panel_label: bool,
) -> list[Path]:
    x = [as_float(row, "passage_probability_both_classes", source) for row in rows]
    y = [as_float(row, "terminal_information_bits", source) for row in rows]

    ordered = sorted(zip(x, y), reverse=True)
    x = [item[0] for item in ordered]
    y = [item[1] for item in ordered]

    if any(value <= 0 for value in x):
        raise ValueError(f"Passage probabilities must be positive for log scaling: {x}")
    if any(value <= 0 for value in y):
        raise ValueError(f"Information values must be positive for log scaling: {y}")

    fig, ax = plt.subplots(figsize=(4.6, 3.25))
    fig.subplots_adjust(left=0.22, right=0.97, bottom=0.27, top=0.68)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.scatter(x, y, s=38, zorder=3)

    def format_information(value: float) -> str:
        if value >= 0.1:
            return f"{value:.3f}"
        if value >= 0.01:
            return f"{value:.4f}"
        return f"{value:.5f}"

    offsets = [(0, 10)] * len(x)
    for xi, yi, offset in zip(x, y, offsets):
        label = format_information(yi)
        ax.annotate(
            label,
            (xi, yi),
            xytext=offset,
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Reverse the x-axis so passage decreases from left to right, as in the manuscript.
    ax.set_xlim(max(x) * 1.5, min(x) * 0.6)
    ax.set_ylim(min(y) * 0.55, max(y) * 1.5)

    ax.xaxis.set_major_locator(FixedLocator(x))
    ax.xaxis.set_major_formatter(FixedFormatter([f"{value:g}" for value in x]))

    low_exp = math.floor(math.log10(min(y)))
    high_exp = math.ceil(math.log10(max(y)))
    y_ticks = [10.0 ** exp for exp in range(low_exp, high_exp + 1)]
    ax.yaxis.set_major_locator(FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(FixedFormatter([f"{value:g}" for value in y_ticks]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_formatter(NullFormatter())

    ax.set_xlabel("Probability of reaching proofreading")
    ax.set_ylabel("Information (bits)")
    clean_axes(ax)

    fig.suptitle(
        "Initial-selection passage changes\ninformation per original encounter",
        x=0.56,
        y=0.98,
        ha="center",
        va="top",
    )
    fig.text(
        0.56,
        0.80,
        "Controlled model comparison",
        ha="center",
        va="top",
        fontsize=9,
    )
    fig.text(
        0.56,
        0.075,
        "Final acceptance or rejection per original encounter",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    cognate_acceptance = display_number(parameters["whole_encounter_cognate_acceptance"])
    near_acceptance = display_number(parameters["whole_encounter_near_acceptance"])
    near_prior = display_number(parameters["whole_encounter_near_prior"])
    fig.text(
        0.56,
        0.025,
        (
            f"Proofreading acceptance {cognate_acceptance} and {near_acceptance}; "
            f"near-cognate input probability {near_prior}"
        ),
        ha="center",
        va="bottom",
        fontsize=8,
    )
    if panel_label:
        fig.text(0.015, 0.98, "C", ha="left", va="top", fontsize=14, weight="bold")

    return save_figure(
        fig,
        outdir / "figure_2c_initial_selection_passage",
        dpi=dpi,
        transparent=transparent,
    )


def main() -> int:
    args = parse_args()
    configure_typography()

    table2 = args.artifact_dir / TABLE2_NAME
    table3 = args.artifact_dir / TABLE3_NAME
    parameters_path = args.artifact_dir / PARAMETERS_NAME
    args.outdir.mkdir(parents=True, exist_ok=True)

    rows2 = read_csv(table2)
    rows3 = read_csv(table3)
    parameters = read_json(parameters_path)
    transparent = not args.opaque

    outputs = []
    outputs.extend(
        plot_panel_b(
            rows2,
            table2,
            args.outdir,
            dpi=args.dpi,
            transparent=transparent,
            panel_label=args.panel_labels,
        )
    )
    outputs.extend(
        plot_panel_c(
            rows3,
            table3,
            parameters,
            args.outdir,
            dpi=args.dpi,
            transparent=transparent,
            panel_label=args.panel_labels,
        )
    )

    provenance = {
        "inputs": {
            TABLE2_NAME: {"sha256": sha256(table2), "rows": rows2},
            TABLE3_NAME: {"sha256": sha256(table3), "rows": rows3},
            PARAMETERS_NAME: {"sha256": sha256(parameters_path), "values": parameters},
        },
        "outputs": [path.name for path in outputs],
        "png_dpi": args.dpi,
        "transparent_background": transparent,
    }
    provenance_path = args.outdir / "figure_2bc_provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("Generated:")
    for path in outputs:
        print(f"  {path}")
    print(f"  {provenance_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
