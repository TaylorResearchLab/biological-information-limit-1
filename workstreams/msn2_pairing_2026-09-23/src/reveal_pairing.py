"""Targeted descriptive constraint-reveal follow-up, not a held-out prediction.

Added after the primary run. Show the four declared reference contrasts and the
largest marginal-only uncertainty width per construct (selected by marginals,
not by joint benefit). The old plan and original analysis output are unchanged.
"""
from fractions import Fraction as F
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from analyze_msn2 import JointFamily, task_bounds, probabilities, write_json


def run(results: Path, output: Path):
    records=json.loads(results.read_text()); output_records=[]; checks=0
    for con in ('1x','2x'):
        rr=[r for r in records if r['scheme']=='primary_median' and r['construct']==con]
        widest=max(rr,key=lambda r:F(r['marginal_only_width']['exact']))
        chosen=[r for r in rr if r['reference_contrast'] or r is widest]
        for r in chosen:
            rows=[probabilities(tuple(c)) for c in r['counts']]
            a=tuple(rows[s][2]+rows[s][3] for s in (0,1)); b=tuple(rows[s][1]+rows[s][3] for s in(0,1)); t=tuple(rows[s][3] for s in(0,1))
            ranges={}
            for name,known in [('neither',()),('condition0_only',(0,)),('condition1_only',(1,)),('both',(0,1))]:
                intervals=[(t[s],t[s]) if s in known else(F(0),F(1))for s in(0,1)]
                bounds=task_bounds(JointFamily.create(a,b,joint_bounds=intervals))
                ranges[name]=(bounds['minimum_law_known_accuracy']['accuracy'],bounds['maximum_law_known_accuracy']['accuracy'])
            actual=F(r['paired_accuracy']['exact']);lo,hi=ranges['neither']
            for interval in ranges.values():
                assert lo<=interval[0]<=actual<=interval[1]<=hi
                checks+=1
            assert ranges['both']==(actual,actual)
            output_records.append({'construct':con,'condition0':r['condition0'],'condition1':r['condition1'],
                 'reference_contrast':r['reference_contrast'],'widest_marginal_interval':r is widest,
                 'paired_accuracy':actual,'ranges_by_revealed_condition':ranges})
    write_json(output,{'status':'Executed descriptive follow-up; outcome reuse is explicit, not validation.',
                'cases':output_records,'nested_interval_checks':checks})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.results,a.out)
