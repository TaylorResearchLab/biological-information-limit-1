#!/usr/bin/env python3
"""Reproduce the TCR proofreading values reported in the manuscript."""

from pathlib import Path
from fractions import Fraction as F
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2] / "transfer_proofreading_v0_1"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "reference")]

from proofreading import coarse_from_competing_rates, response_metrics

alpha_self = coarse_from_competing_rates(F(1), F(10))       # 1/11
alpha_agonist = coarse_from_competing_rates(F(1), F(1,10)) # 10/11
depths = (1, 2, 3, 4, 8)

print("N\tP_complete_agonist\tAgonist/Self_ratio\tBayes_error\tInformation_bits")
for n in depths:
    p_self = alpha_self ** n
    p_agonist = alpha_agonist ** n
    m = response_metrics(p_self, p_agonist, F(1,2))
    info = (float(m["information_bits"].lo) + float(m["information_bits"].hi)) / 2
    print(n, float(p_agonist), float(m["completion_ratio"]),
          float(m["bayes_error"]), info, sep="\t")
