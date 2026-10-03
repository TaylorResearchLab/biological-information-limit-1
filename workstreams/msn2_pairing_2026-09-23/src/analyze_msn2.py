"""Descriptive Msn2 reporter-pairing analysis on a pinned published archive.

No population confidence intervals, independent-experiment validation, biological
intervention, or input-capacity optimization. The archived solver is unchanged.
"""
from __future__ import annotations
import argparse
import csv
from fractions import Fraction as F
import gzip
import hashlib
import io
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reference'))
from joint_task_bounds import JointFamily, task_bounds, accuracy, policy_accuracy

SOURCE_SHA = 'a9be1b297d4945aae3b4d0c3d1734ac8ec4788da2e4bed8d43cd380e4783fd2b'
SOLVER_SHA = '746cd3c9c7f3801541a2208b71f8fb53b7ebb1424f0f0de3f75bf57b08e8a7e1'
CONDITIONS = ('info_theory_untreated',) + tuple('DM_70min_'+d for d in
              ('100nM','175nM','275nM','413nM','690nM','1117nM','3uM')) + (
    'FM1_5min_690nM','FM2_40minINT_690nM','FM3_25minINT_690nM',
    'FM4_175minINT_690nM','FM5_13minINT_690nM','FM6_10minINT_690nM',
    'FM7_786minINT_690nM','FM8_625minINT_690nM','FM9_5minINT_690nM')
SCHEMES = (
    ('primary_median', 'max11', 'equal_condition', F(1,2)),
    ('sensitivity_q25','max11','equal_condition',F(1,4)),
    ('sensitivity_q75','max11','equal_condition',F(3,4)),
    ('sensitivity_control95','max11','untreated',F(19,20)),
    ('sensitivity_at120','at120','equal_condition',F(1,2)))
REFERENCES = (
    ('untreated_vs_sustained','info_theory_untreated','DM_70min_690nM'),
    ('low_vs_high_amplitude','DM_70min_100nM','DM_70min_3uM'),
    ('one_vs_nine_pulses','FM1_5min_690nM','FM9_5minINT_690nM'),
    ('sustained_vs_nine_pulses','DM_70min_690nM','FM9_5minINT_690nM'))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def encode(obj):
    if isinstance(obj,F): return {'exact':str(obj),'value':float(obj)}
    if isinstance(obj,np.generic): return obj.item()
    if isinstance(obj,dict): return {k:encode(v) for k,v in obj.items()}
    if isinstance(obj,(tuple,list)): return [encode(v) for v in obj]
    return obj


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(encode(obj), indent=2, allow_nan=False)+'\n',encoding='utf-8')


def verify_solver() -> None:
    if sha((ROOT/'reference/joint_task_bounds.py').read_bytes()) != SOLVER_SHA:
        raise ValueError('Reference solver bytes differ from reviewed delivery.')


def original_data_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if sha(raw)==SOURCE_SHA: return raw
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        key='elife_poa_e06559_Supplementary_File_1.zip'
        if key not in z.namelist(): raise ValueError('Not the pinned source archive or its publisher bundle.')
        raw=z.read(key)
    if sha(raw)!=SOURCE_SHA: raise ValueError('Nested source hash differs from the reviewed archive.')
    return raw


def features(a: np.ndarray) -> dict[str,np.ndarray]:
    if a.ndim!=2 or a.shape[1]!=128 or not len(a):
        raise ValueError('Require a nonempty n by 128 matrix.')
    if not np.isfinite(a).all() or (a<0).any():
        raise ValueError('Nonfinite or negative entries differ from the pinned source convention.')
    y=a.reshape(len(a),2,64)
    # Complete windows only: center times 7.5..140 min. No implicit padding.
    windows=np.lib.stride_tricks.sliding_window_view(y,11,axis=2).mean(axis=-1)
    return {'max11':windows.max(axis=2), 'at120':y[:,:,45:56].mean(axis=2)}


def zero_audit(a: np.ndarray) -> dict:
    out={}
    for j,label in enumerate(('SIP18_YFP','HXK1_CFP')):
        b=a[:,j*64:(j+1)*64]; z=b==0; pos=b>0
        anypos=pos.any(1); first=pos.argmax(1); last=63-pos[:,::-1].argmax(1)
        mid=(np.arange(64)[None,:]>=first[:,None])&(np.arange(64)[None,:]<=last[:,None])&anypos[:,None]
        out[label]={'zero_entries':int(z.sum()),'entries':int(b.size),
             'all_zero_rows':int(z.all(1).sum()), 'rows_with_any_zero':int(z.any(1).sum()),
             'rows_with_internal_zero':int((z&mid).any(1).sum()),
             'rows_with_zero_final_frame':int(z[:,-1].sum()),
             'rows_with_zero_in_120min_window':int(z[:,45:56].any(1).sum())}
    out['rows_with_any_zero_either_reporter']=int((a==0).any(1).sum())
    return out


def inverse_mixture_quantile(groups: list[np.ndarray], q: F) -> float:
    """Inverse empirical CDF with exactly equal group weights, not pooled rows."""
    if not groups or not F(0)<q<=1: raise ValueError('Nonempty groups and 0<q<=1 required.')
    if any(g.ndim!=1 or not len(g) or not np.isfinite(g).all() for g in groups):
        raise ValueError('All quantile groups must be nonempty finite vectors.')
    ordered=[np.sort(g) for g in groups]
    candidates=np.unique(np.concatenate(ordered))
    lo,hi=0,len(candidates)-1
    while lo<hi:
        k=(lo+hi)//2; v=candidates[k]
        cdf=sum((F(int(np.searchsorted(g,v,side='right')),len(g)) for g in ordered),F(0))/len(ordered)
        if cdf>=q: hi=k
        else: lo=k+1
    return float(candidates[lo])


def binary_counts(values: np.ndarray, threshold: tuple[float,float]) -> tuple[int,...]:
    if values.ndim!=2 or values.shape[1]!=2 or not len(values) or not np.isfinite(values).all():
        raise ValueError('Require finite nonempty paired scalar matrix.')
    if len(threshold)!=2 or not np.isfinite(threshold).all(): raise ValueError('Two finite thresholds required.')
    bits=values>np.asarray(threshold)
    return tuple(int(n) for n in np.bincount(2*bits[:,0].astype(int)+bits[:,1],minlength=4))


def probabilities(counts: tuple[int,...]) -> tuple[F,...]:
    if len(counts)!=4 or any(isinstance(n,bool) or not isinstance(n,int) or n<0 for n in counts) or not sum(counts):
        raise ValueError('Require four nonnegative integer counts with a positive sum.')
    return tuple(F(n,sum(counts)) for n in counts)


def mutual_information(rows: tuple[tuple[F,...],...], q: F=F(1,2)) -> float:
    """Numerical log functional of exact empirical probabilities, not an estimator CI."""
    weights=(1-q,q); mixture=[sum(weights[s]*rows[s][k] for s in (0,1)) for k in range(len(rows[0]))]
    return math.fsum(float(weights[s]*p)*math.log2(float(p/mixture[k]))
        for s in (0,1) for k,p in enumerate(rows[s]) if p and weights[s])


def analyze_counts(count0: tuple[int,...], count1: tuple[int,...]) -> dict:
    rows=tuple(probabilities(c) for c in (count0,count1))
    a=tuple(r[2]+r[3] for r in rows); b=tuple(r[1]+r[3] for r in rows)
    family=JointFamily.create(a,b)
    observed=tuple(r[3] for r in rows); independent=tuple(a[s]*b[s] for s in (0,1))
    bounds=task_bounds(family); obs=accuracy(family,observed); ind=accuracy(family,independent)
    single_a=(1+abs(a[1]-a[0]))/2; single_b=(1+abs(b[1]-b[0]))/2
    best_single=max(single_a,single_b)
    independent_rows=tuple(family.row(s,independent[s]) for s in (0,1))
    policy=tuple(int(independent_rows[1][k]>independent_rows[0][k]) for k in range(4))
    lo=bounds['minimum_law_known_accuracy']['accuracy']; hi=bounds['maximum_law_known_accuracy']['accuracy']
    if not (lo<=obs<=hi and lo<=ind<=hi and best_single<=obs):
        raise AssertionError('Exact family/monotonicity check failed.')
    if tuple(family.row(s,observed[s]) for s in (0,1))!=rows:
        raise AssertionError('Joint marginal reconstruction failed.')
    single_rows_a=tuple((1-v,v) for v in a); single_rows_b=tuple((1-v,v) for v in b)
    return {'counts':[count0,count1], 'cell_rows':[sum(count0),sum(count1)],
        'marginal_SIP18':a,'marginal_HXK1':b,'paired_probability_11':observed,
        'marginal_only_accuracy_bounds':[lo,hi], 'marginal_only_width':hi-lo,
        'paired_accuracy':obs, 'SIP18_accuracy':single_a,'HXK1_accuracy':single_b,
        'gain_over_best_single':obs-best_single,
        'independence_completion_accuracy':ind,
        'independence_decoder':policy,
        'independence_decoder_actual_accuracy':policy_accuracy(family,observed,policy),
        'independence_completion_error_in_accuracy':ind-obs,
        'best_fixed_deterministic_worst_case':bounds['best_fixed_deterministic_decoder'],
        'paired_MI_bits':mutual_information(rows),
        'SIP18_MI_bits':mutual_information(single_rows_a),
        'HXK1_MI_bits':mutual_information(single_rows_b),
        'independence_completion_MI_bits':mutual_information(independent_rows),
        'minimum_witness':bounds['minimum_law_known_accuracy'],
        'maximum_witness':bounds['maximum_law_known_accuracy']}


def run(archive: Path, out: Path) -> None:
    verify_solver()
    if out.exists() and any(out.iterdir()): raise ValueError('Use an empty/new output directory; saved results are not overwritten.')
    out.mkdir(parents=True,exist_ok=True)
    raw=original_data_bytes(archive); matrices={}; feature_map={}; provenance=[]; qc=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None: raise ValueError('Archive CRC error.')
        for construct in ('1x','2x'):
            for cond in CONDITIONS:
                name=f'source_data/{construct}_SIP18_HXK1_{cond}.txt'; payload=z.read(name)
                a=np.loadtxt(io.BytesIO(payload),delimiter=','); matrices[(construct,cond)]=a
                feature_map[(construct,cond)]=features(a)
                provenance.append({'construct':construct,'condition':cond,'member':name,'sha256':sha(payload),'shape':list(a.shape),'bytes':len(payload)})
                qc.append({'construct':construct,'condition':cond,'rows':len(a),**zero_audit(a)})
    if sum(len(v) for v in matrices.values())!=40458: raise AssertionError('Unexpected row count for pinned data.')
    thresholds=[]; records=[]; per_condition=[]
    for scheme,feature,method,q in SCHEMES:
        for construct in ('1x','2x'):
            groups=CONDITIONS if method=='equal_condition' else (CONDITIONS[0],)
            threshold=tuple(inverse_mixture_quantile([feature_map[(construct,c)][feature][:,j] for c in groups],q) for j in (0,1))
            thresholds.append({'scheme':scheme,'construct':construct,'feature':feature,'method':method,'quantile':q,'threshold_SIP18':threshold[0],'threshold_HXK1':threshold[1]})
            counts={c:binary_counts(feature_map[(construct,c)][feature],threshold) for c in CONDITIONS}
            for c in CONDITIONS:
                per_condition.append({'scheme':scheme,'construct':construct,'condition':c,'counts_00_01_10_11':counts[c]})
            for c0,c1 in combinations(CONDITIONS,2):
                r=analyze_counts(counts[c0],counts[c1])
                r.update(scheme=scheme,construct=construct,condition0=c0,condition1=c1)
                r['reference_contrast']=next((name for name,a,b in REFERENCES if (a,b)==(c0,c1)),None)
                records.append(r)
            print(f'{scheme} {construct}: 136 pairs complete; thresholds {threshold}',flush=True)
    with (out/'cell_features.csv.gz').open('wb') as rawf:
        with gzip.GzipFile(filename='',mode='wb',fileobj=rawf,mtime=0) as compressed:
            with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as f:
                w=csv.writer(f,lineterminator='\n');w.writerow(('construct','condition','source_row_1based','SIP18_max11','HXK1_max11','SIP18_at120','HXK1_at120'))
                for (construct,c),fs in feature_map.items():
                    for i in range(len(fs['max11'])):
                        w.writerow((construct,c,i+1,*[format(float(v),'.17g') for key in ('max11','at120') for v in fs[key][i]]))
    write_json(out/'member_provenance.json',{'archive_sha256':sha(raw),'archive_bytes':len(raw),'solver_sha256':SOLVER_SHA,'members':provenance})
    write_json(out/'zero_audit.json',qc);write_json(out/'thresholds.json',thresholds)
    write_json(out/'condition_counts.json',per_condition);write_json(out/'pair_results.json',records)
    write_json(out/'reference_contrasts.json',[r for r in records if r['reference_contrast']])
    summary=[]
    for scheme,*_ in SCHEMES:
        for construct in ('1x','2x'):
            rr=[r for r in records if r['scheme']==scheme and r['construct']==construct]
            summary.append({'scheme':scheme,'construct':construct,'pairs':len(rr),
                'positive_gain_pairs':sum(r['gain_over_best_single']>0 for r in rr),
                'gain_at_least_one_percentage_point':sum(r['gain_over_best_single']>=F(1,100) for r in rr),
                'median_pairing_gain':float(np.median([float(r['gain_over_best_single']) for r in rr])),
                'max_pairing_gain':max(r['gain_over_best_single'] for r in rr),
                'median_marginal_only_width':float(np.median([float(r['marginal_only_width']) for r in rr])),
                'max_marginal_only_width':max(r['marginal_only_width'] for r in rr),
                'independence_overestimates_pairs':sum(r['independence_completion_error_in_accuracy']>0 for r in rr),
                'independence_underestimates_pairs':sum(r['independence_completion_error_in_accuracy']<0 for r in rr),
                'max_abs_independence_accuracy_error':max(abs(r['independence_completion_error_in_accuracy']) for r in rr)})
    write_json(out/'summary.json',summary)
    print('Completed 1360 descriptive probability-completion comparisons on 40458 cell rows.',flush=True)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();run(args.archive,args.out)

if __name__=='__main__':
    main()
