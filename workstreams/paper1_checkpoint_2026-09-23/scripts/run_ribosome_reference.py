#!/usr/bin/env python3
"""Reproduce the ribosome information families used in the manuscript."""

from pathlib import Path
from fractions import Fraction as F
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2] / "research_update_2026-09-23" / "ribosome_boundary"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "reference")]

from ribosome_boundary import AcceptanceBox, info_bounds, assembly_metrics

# Primary equal-weight local proofreading comparison.
wt = info_bounds(AcceptanceBox((F('.9'),F(1)), (F('.048'),F('.052'))), F(1,2))
restrictive = info_bounds(AcceptanceBox((F('.9'),F(1)), (F('.002'),F('.012'))), F(1,2))

print("WT local information:", wt["minimum_information_bits"], wt["maximum_information_bits"])
print("Restrictive local information:", restrictive["minimum_information_bits"], restrictive["maximum_information_bits"])

# Source-frequency sensitivity.
for q in (F(1,2), F(1,10), F(1,100)):
    print("q_near =", q)
    print(" WT:", info_bounds(AcceptanceBox((F('.9'),F(1)), (F('.048'),F('.052'))), q))
    print(" restrictive:", info_bounds(AcceptanceBox((F('.9'),F(1)), (F('.002'),F('.012'))), q))

# Whole-encounter passage control used in the manuscript.
for epsilon in (F(1), F(1,10), F(1,100), F(1,1000)):
    r = assembly_metrics(epsilon, epsilon, F('.95'), F('.007'), F(1,2))
    print("epsilon =", epsilon,
          "terminal bits =", r["terminal_information_bits"],
          "history bits =", r["history_information_bits"])
