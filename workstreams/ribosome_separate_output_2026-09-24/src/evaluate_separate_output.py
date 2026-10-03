#!/usr/bin/env python3
"""Outcome-excluded ribosome composition audit.

This module evaluates only algebraic consequences of explicitly declared
source summaries. It does not fit the competition endpoint.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import json
from pathlib import Path

@dataclass(frozen=True)
class Interval:
    lo: float
    hi: float
    def __post_init__(self):
        if self.lo < 0 or self.hi < self.lo:
            raise ValueError((self.lo, self.hi))

def ratio_interval(num: Interval, den: Interval) -> Interval:
    if den.lo <= 0:
        raise ValueError("denominator interval must be strictly positive")
    return Interval(num.lo / den.hi, num.hi / den.lo)

def mul_interval(a: Interval, b: Interval) -> Interval:
    vals=[a.lo*b.lo,a.lo*b.hi,a.hi*b.lo,a.hi*b.hi]
    return Interval(min(vals),max(vals))

def inv_interval(a: Interval) -> Interval:
    if a.lo <= 0:
        raise ValueError("interval must be strictly positive")
    return Interval(1/a.hi,1/a.lo)

def passage(k_forward: float, k_reject: float) -> float:
    if k_forward < 0 or k_reject < 0 or k_forward+k_reject <= 0:
        raise ValueError
    return k_forward/(k_forward+k_reject)

def kinetic_u(point: dict[str,float]) -> float:
    wt_n=passage(point['wt_near_k3'],point['wt_near_km2'])
    wt_c=passage(point['wt_cog_k3'],point['wt_cog_km2'])
    rs_n=passage(point['res_near_k3'],point['res_near_km2'])
    rs_c=passage(point['res_cog_k3'],point['res_cog_km2'])
    return (rs_n/rs_c)/(wt_n/wt_c)

def corner_range(intervals: dict[str,Interval]) -> Interval:
    keys=list(intervals)
    vals=[]
    for bits in product((0,1), repeat=len(keys)):
        d={k:(intervals[k].hi if b else intervals[k].lo) for k,b in zip(keys,bits)}
        vals.append(kinetic_u(d))
    return Interval(min(vals),max(vals))

def main(out_path: str | None=None) -> dict:
    # Zaher & Green 2010, Table 1 / Figure 3B values.
    observed = {
        'wt_error_ratio': 1.6e-3,
        'res_error_ratio': 2.3e-4,
    }
    observed_relative = observed['res_error_ratio']/observed['wt_error_ratio']

    # Later proofreading acceptance summaries. One displayed uncertainty amount
    # is represented as a declared rectangular sensitivity family, not CI coverage.
    b_near_wt_point=0.05
    b_near_res_point=0.007
    b_near_wt_1u=Interval(0.048,0.052)
    b_near_res_1u=Interval(0.002,0.012)
    b_cog=Interval(0.9,1.0)  # conservative closed relaxation of source >0.9

    cog_ratio = ratio_interval(b_cog,b_cog)  # b_cog_WT / b_cog_res
    near_point_ratio=Interval(b_near_res_point/b_near_wt_point,
                              b_near_res_point/b_near_wt_point)
    near_1u_ratio=ratio_interval(b_near_res_1u,b_near_wt_1u)
    f_point=mul_interval(near_point_ratio,cog_ratio)
    f_1u=mul_interval(near_1u_ratio,cog_ratio)

    # Relative competition error = U * later-stage factor F.
    u1_point=mul_interval(Interval(1,1), f_point)
    u1_1u=mul_interval(Interval(1,1), f_1u)
    directional_u_threshold=1.0/f_1u.hi

    # Explicit rate-based comparator, not the rate-free BICS result.
    rates_point={
        'wt_cog_k3':25.0,'wt_near_k3':1.2,
        'res_cog_k3':14.0,'res_near_k3':0.49,
        'wt_cog_km2':0.50,'wt_near_km2':47.0,
        'res_cog_km2':0.41,'res_near_km2':46.0,
    }
    rates_1u={
        'wt_cog_k3':Interval(23.2,26.8),
        'wt_near_k3':Interval(1.08,1.32),
        'res_cog_k3':Interval(13.4,14.6),
        'res_near_k3':Interval(0.461,0.519),
        'wt_cog_km2':Interval(0.493,0.507),
        'wt_near_km2':Interval(44.9,49.1),
        'res_cog_km2':Interval(0.402,0.418),
        'res_near_km2':Interval(44.1,47.9),
    }
    u_kin_point=kinetic_u(rates_point)
    u_kin_1u=corner_range(rates_1u)
    kinetic_point_b=mul_interval(Interval(u_kin_point,u_kin_point), f_point)
    kinetic_1u_b=mul_interval(u_kin_1u, f_1u)

    result={
        'status':'executed algebraic calibration-ledger analysis; not scientific acceptance',
        'observed_competition':{
            **observed,
            'res_over_wt':observed_relative,
            'used_for_calibration':False,
        },
        'rate_free_late_stage':{
            'factor_point_with_cognate_envelope':[f_point.lo,f_point.hi],
            'factor_one_displayed_uncertainty_family':[f_1u.lo,f_1u.hi],
            'if_U_equals_1_point':[u1_point.lo,u1_point.hi],
            'if_U_equals_1_one_uncertainty_family':[u1_1u.lo,u1_1u.hi],
            'U_threshold_for_guaranteed_res_lt_wt_under_one_uncertainty_family':directional_u_threshold,
            'unconditional_quantitative_prediction':'not identified because no numerical source-derived bound on U was found independent of the competition endpoint',
        },
        'rate_based_comparator':{
            'definition':'codon-recognition-state two-exit approximation a=k3/(k3+k_-2), using observed k_GTP as k3 proxy',
            'U_point':u_kin_point,
            'U_one_uncertainty_rectangle':[u_kin_1u.lo,u_kin_1u.hi],
            'relative_error_with_point_late_acceptance_and_cognate_envelope':[kinetic_point_b.lo,kinetic_point_b.hi],
            'relative_error_with_one_uncertainty_rate_and_acceptance_rectangles':[kinetic_1u_b.lo,kinetic_1u_b.hi],
            'observed_relative_error':observed_relative,
            'point_late_family_contains_observed': kinetic_point_b.lo <= observed_relative <= kinetic_point_b.hi,
            'broad_sensitivity_family_contains_observed': kinetic_1u_b.lo <= observed_relative <= kinetic_1u_b.hi,
            'interpretation':'matched mechanistic sensitivity comparator only; not a rate-free BICS prediction and not a confidence interval',
        },
    }
    if out_path:
        Path(out_path).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

if __name__=='__main__':
    import sys
    out=sys.argv[1] if len(sys.argv)>1 else None
    r=main(out)
    print(json.dumps(r,indent=2,sort_keys=True))
