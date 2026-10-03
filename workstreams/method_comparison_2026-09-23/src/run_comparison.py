"""Execute matched formulations on all primary cases and a fixed MI panel."""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import hashlib
from collections import Counter
import sys
from matched_information import (JointFamily, information_bounds, interval_information,
                                 matched_decision_lps, compact_bounds, encode, Interval)


def family_from_counts(counts, q1=F(1,2), bounds=None):
    if len(counts)!=2 or any(len(r)!=4 for r in counts):
        raise ValueError('Two rows of four nonnegative integer counts required')
    if any(isinstance(c,bool) or not isinstance(c,int) or c<0 for row in counts for c in row):
        raise ValueError('Counts must be nonnegative integers')
    if any(sum(row)<=0 for row in counts):
        raise ValueError('Each protocol must have counted observations')
    a=tuple(F(c[2]+c[3],sum(c)) for c in counts)
    b=tuple(F(c[1]+c[3],sum(c)) for c in counts)
    return JointFamily.create(a,b,q1,joint_bounds=bounds)


def record_id(r):
    return '|'.join(r[k] for k in ('construct','condition0','condition1'))


def run(inputs: Path, out: Path):
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Refusing nonempty output directory')
    out.mkdir(parents=True,exist_ok=True)
    raw=inputs.read_bytes(); records=json.loads(raw)
    if len(records)!=272:
        raise ValueError('This comparison expects the declared full 272-case primary panel')
    lp_records=[]; selected=[]
    for r in records:
        family=family_from_counts(r['counts'])
        lp=matched_decision_lps(family)
        oldlo=float(F(r['marginal_only_accuracy_bounds'][0]['exact']))
        olddet=float(F(r['best_fixed_deterministic_worst_case']['worst_case_accuracy']['exact']))
        if lp['historical_exact_minimum'] != oldlo or lp['historical_exact_deterministic_guarantee'] != olddet:
            raise AssertionError('Historical exact target changed')
        if lp['absolute_discrepancy']>1e-9:
            raise AssertionError('LP fails matched tolerance')
        lp_records.append({'case_id':record_id(r),**lp})
        if r['reference_contrast'] is not None:
            selected.append((r,'previously declared reference contrast'))
    for construct in ('1x','2x'):
        subset=[r for r in records if r['construct']==construct]
        winner=max(subset,key=lambda r:F(r['marginal_only_accuracy_bounds'][1]['exact'])-F(r['marginal_only_accuracy_bounds'][0]['exact']))
        if record_id(winner) not in [record_id(x) for x,_ in selected]:
            selected.append((winner,'previously reported widest marginal-only accuracy interval'))
    if len(selected)!=10:
        raise AssertionError('Declared 10-case panel changed')
    mi_records=[]
    for r,selection in selected:
        fam=family_from_counts(r['counts']); res=information_bounds(fam)
        paired=tuple(F(c[3],sum(c)) for c in r['counts'])
        observed=interval_information(fam,paired)
        independent=interval_information(fam,tuple(fam.a[s]*fam.b[s] for s in (0,1)))
        if res['minimum']['lower']>observed.hi or observed.lo>res['maximum']['upper']:
            raise AssertionError('Observed MI outside certified family enclosure')
        syn=Interval(max(F(0),observed.lo-res['minimum']['upper']),
                     max(F(0),observed.hi-res['minimum']['lower']))
        mi_records.append({'case_id':record_id(r),'selection':selection,'counts':r['counts'],
                           'information_bounds':compact_bounds(res),'observed_bits':observed.decimal(15),
                           'independent_completion_bits':independent.decimal(15),
                           'BROJA_complementary_information_bits':syn.decimal(15)})
        print(record_id(r),compact_bounds(res)['minimum']['bits_enclosure'],
              compact_bounds(res)['maximum']['bits_enclosure'],'gap',float(res['minimum']['upper']-res['minimum']['lower']))
    # Previously reported one-copy FM7 example, same four reveal states.
    r=next(r for r,_ in selected if r['construct']=='1x' and r['condition0']=='DM_70min_175nM' and r['condition1'].startswith('FM7'))
    base=family_from_counts(r['counts']); paired=tuple(F(c[3],sum(c)) for c in r['counts'])
    reveals=[]
    for flag in [(False,False),(True,False),(False,True),(True,True)]:
        b=tuple((paired[s],paired[s]) if flag[s] else base.bounds[s] for s in (0,1))
        fam=family_from_counts(r['counts'],bounds=b);res=information_bounds(fam)
        reveals.append({'case_id':record_id(r),'pairing_retained':flag,
                        'information_bounds':compact_bounds(res)})
        print('reveal',flag,compact_bounds(res)['minimum']['bits_enclosure'],compact_bounds(res)['maximum']['bits_enclosure'],float(res['minimum']['upper']-res['minimum']['lower']))
    summary={'scope':'Established-framework comparison on previously derived empirical counts; no new sampling claims',
             'input_sha256':hashlib.sha256(raw).hexdigest(),'primary_cases':len(records),
             'new_linear_programs':sum(r['solves'] for r in lp_records),
             'max_lp_discrepancy':max(r['absolute_discrepancy'] for r in lp_records),
             'max_lp_constraint_residual':max(r['lp_primal_constraint_residual'] for r in lp_records),
             'primary_cases_randomized_equals_historical_deterministic_within_1e_9':sum(abs(r['randomized_fixed_decoder_guarantee']-r['historical_exact_deterministic_guarantee'])<1e-9 for r in lp_records),
             'information_panel':len(mi_records),'reveal_records':len(reveals),
             'unique_information_families':len(mi_records)+len(reveals)-1,
             'max_minimum_certificate_width_bits':max(r['information_bounds']['minimum']['certificate_width_bits'] for r in mi_records+reveals),
             'minimum_methods':dict(Counter(r['information_bounds']['minimum']['method'] for r in mi_records+reveals)),
             'external_software_status':'No JavaBayes, BROJA-2PID or minimax-SVM implementation was run. Matched mathematical reductions with separately formulated LPs.'}
    for name,value in [('decision_comparison.json',lp_records),('information_panel.json',mi_records),('information_reveal.json',reveals),('summary.json',summary)]:
        (out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); run(args.inputs,args.out)
