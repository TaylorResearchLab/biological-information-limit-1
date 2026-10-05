'Finite information calculations with rational probability arithmetic and certified logarithm enclosures. KL coefficients are exact in the documented channel classes and bounded otherwise.'
from __future__ import annotations
from dataclasses import dataclass, replace
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations, product
from math import isqrt
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from typing import Mapping, Sequence
from .finite import Kernel, Model, total_variation


@dataclass(frozen=True)
class Interval:
    lo: F
    hi: F
    def __post_init__(self):
        if not isinstance(self.lo,F) or not isinstance(self.hi,F) or self.lo>self.hi:
            raise ValueError('Ordered rational endpoints required.')
    def __add__(self, other):
        if isinstance(other,(int,F)): other=Interval(F(other),F(other))
        return Interval(self.lo+other.lo,self.hi+other.hi)
    def scale(self, weight:F):
        if weight<0: return Interval(weight*self.hi,weight*self.lo)
        return Interval(weight*self.lo,weight*self.hi)
    def complement(self): return Interval(1-self.hi,1-self.lo)
    def multiply_nonnegative(self, other):
        if self.lo<0 or other.lo<0: raise ValueError('Nonnegative intervals required.')
        return Interval(self.lo*other.lo,self.hi*other.hi)
    def decimal(self, digits=18):
        with localcontext() as ctx:
            ctx.prec=max(60,digits+20)
            unit=Decimal(1).scaleb(-digits)
            def out(x, rounding):
                # Set directed rounding for division AND the final quantization.
                ctx.rounding=rounding
                return str((Decimal(x.numerator)/Decimal(x.denominator)).quantize(unit,rounding=rounding))
            return {'lower':out(self.lo,ROUND_FLOOR),'upper':out(self.hi,ROUND_CEILING)}


def _ln_series(t:F,terms:int):
    if not F(1)<=t<=F(2) or terms<1: raise ValueError('Series domain error.')
    u=(t-1)/(t+1); u2=u*u; power=u; total=F(0)
    for j in range(terms):
        total+=2*power/F(2*j+1); power*=u2
    tail=2*power/(F(2*terms+1)*(1-u2))
    return Interval(total,total+tail)


@lru_cache(maxsize=4096)
def log2_interval(x:F,terms:int=20)->Interval:
    if not isinstance(x,F) or x<=0: raise ValueError('Positive rational required.')
    m=x.numerator.bit_length()-x.denominator.bit_length()
    t=x/(F(2)**m)
    if t<1: m-=1; t*=2
    if t>=2: m+=1; t/=2
    a=_ln_series(t,terms); b=_ln_series(F(2),terms)
    return Interval(F(m)+a.lo/b.hi,F(m)+a.hi/b.lo)


def sqrt_interval(x:F, digits:int=24)->Interval:
    if x<0: raise ValueError('Negative square root.')
    scale=10**digits
    a=isqrt((x.numerator*scale*scale)//x.denominator)
    lo=F(a,scale)
    return Interval(lo,lo if lo*lo==x else F(a+1,scale))


def validate_prior(k:Kernel,prior:Mapping[tuple,F]):
    k.validate()
    if not prior or not set(prior)<=set(k.rows): raise ValueError('Unsupported source preparation.')
    if any(not isinstance(p,F) or p<0 for p in prior.values()) or sum(prior.values(),F(0))!=1:
        raise ValueError('Normalized exact source preparation required.')


def information(k:Kernel,prior:Mapping[tuple,F],terms:int=20)->Interval:
    validate_prior(k,prior)
    outputs=set().union(*(set(row) for row in k.rows.values()))
    marginal={y:sum((prior.get(x,F(0))*row.get(y,F(0)) for x,row in k.rows.items()),F(0)) for y in outputs}
    result=Interval(F(0),F(0))
    for x,px in prior.items():
        if not px: continue
        for y,pyx in k.rows[x].items():
            if pyx:
                result+=log2_interval(pyx/marginal[y],terms).scale(px*pyx)
    return Interval(max(F(0),result.lo),max(F(0),result.hi))


def eta_tv(k:Kernel):
    k.validate(); keys=list(k.rows)
    best=F(0); witness=(keys[0],keys[0])
    for a,b in combinations(keys,2):
        value=total_variation(k.rows[a],k.rows[b])
        if value>best: best=value; witness=(a,b)
    return best,witness


def eta_kl(k:Kernel)->dict:
    """Input-unrestricted KL coefficient. Never confuse it with I for a fixed prior.

    Binary output: exact radical from extreme Bernoulli rows, all input sizes.
    Two distinct rows with exchange symmetry: exact rational Le Cam maximum.
    Other finite channels: safe lower/upper bounds, explicitly marked non-exact.
    """
    k.validate(); outputs=sorted(set().union(*(set(row) for row in k.rows.values())))
    rows=sorted(set(tuple(row.get(y,F(0)) for y in outputs) for row in k.rows.values()))
    tv,_=eta_tv(k)
    if len(rows)==1:
        return {'interval':Interval(F(0),F(0)),'method':'constant','exact_expression':'0','identified':True}
    if len(outputs)==2:
        a=min(row[1] for row in rows); b=max(row[1] for row in rows)
        A=b*(1-a); B=a*(1-b); root=sqrt_interval(A*B)
        interval=Interval(A+B-2*root.hi,A+B-2*root.lo)
        interval=Interval(max(F(0),interval.lo),min(tv,interval.hi))
        return {'interval':interval,'method':'binary_output_extreme_rows',
                'exact_expression':f'{A+B} - 2*sqrt({A*B})','identified':True,
                'extreme_probabilities':[str(a),str(b)]}
    if len(rows)==2:
        p,q=rows
        pairs=sorted(zip(p,q))
        if pairs==sorted((b,a) for a,b in pairs):
            value=sum(((a-b)**2/(2*(a+b)) for a,b in pairs if a+b),F(0))
            return {'interval':Interval(value,value),'method':'two_row_exchange_symmetry',
                    'exact_expression':str(value),'identified':True}
    lower=F(0)
    for p,q in combinations(rows,2):
        value=sum(((a-b)**2/(2*(a+b)) for a,b in zip(p,q) if a+b),F(0))
        lower=max(lower,value)
    return {'interval':Interval(lower,tv),'method':'pair_midpoint_lower_TV_upper',
            'exact_expression':None,'identified':lower==tv}


def restrict_inputs(k:Kernel,fixed:Mapping[str,int])->Kernel:
    allowed={v.name for v in k.inputs}
    if not set(fixed)<=allowed: raise ValueError('Unknown context port.')
    for v in k.inputs:
        if v.name in fixed and fixed[v.name] not in v.domain: raise ValueError('Context outside domain.')
    remaining=tuple(v for v in k.inputs if v.name not in fixed)
    rows={}
    for x,row in k.rows.items():
        if all(x[i]==fixed[v.name] for i,v in enumerate(k.inputs) if v.name in fixed):
            rows[tuple(x[i] for i,v in enumerate(k.inputs) if v.name not in fixed)]=dict(row)
    ans=replace(k,inputs=remaining,rows=rows,
                provenance=k.provenance+('assumption:fixed-preparation:'+repr(sorted(fixed.items())),))
    ans.validate(); return ans


def compose(k:Kernel,l:Kernel,instance_id='composed')->Kernel:
    k.validate(); l.validate()
    if k.outputs!=l.inputs:
        raise ValueError('SERIAL_INTERFACE_MISMATCH: downstream law needs other inputs or another grain.')
    rows={}
    for x,row in k.rows.items():
        out={}
        for y,p in row.items():
            for z,q in l.rows[y].items(): out[z]=out.get(z,F(0))+p*q
        rows[x]=out
    ans=Kernel(instance_id,k.inputs,l.outputs,rows,k.provenance+l.provenance,kind=l.kind,law_status='derived')
    ans.validate(); return ans


def percolation_bound(model:Model,source:str,targets:Sequence[str],max_motifs=18)->Interval:
    """Polyanskiy-Wu Theorem 5 finite Bayesian-network bound by site enumeration.

    Single exogenous source; single-output nodes; any contexts must be fixed first.
    Joint-output blocks require a separately justified block graph, not this helper.
    Returned interval encloses the percolation expression using certified local bounds.
    """
    model=Model(model.roots,model.motifs)  # revalidate mutable nested row maps
    if len(model.roots)!=1 or model.roots[0].name!=source:
        raise ValueError('SINGLE_SOURCE_REQUIRED: fix contexts and retain side inputs explicitly.')
    if not targets or not set(targets)<=set(model.order): raise ValueError('Unknown or empty receiver.')
    if any(len(k.outputs)!=1 for k in model.motifs): raise ValueError('Joint-output block graph not implemented.')
    if len(model.motifs)>max_motifs: raise ValueError('Exact site enumeration size limit.')
    weights=[eta_kl(k)['interval'] for k in model.motifs]
    def evaluate(use_upper):
        total=F(0)
        for mask in product((False,True),repeat=len(weights)):
            reached={source}; probability=F(1)
            for k,iv,is_open in zip(model.motifs,weights,mask):
                p=iv.hi if use_upper else iv.lo
                probability*=p if is_open else 1-p
                if is_open and any(v.name in reached for v in k.inputs): reached.add(k.outputs[0].name)
            if reached.intersection(targets): total+=probability
        return total
    return Interval(evaluate(False),evaluate(True))


def decision_values(k:Kernel,prior:Mapping[tuple,F],actions:Sequence[int],
                    reward:Mapping[tuple,F],policy:Mapping[tuple,Mapping[int,F]])->dict:
    """Best and achieved expected task reward. Biological meaning supplied externally.

    reward[(input_tuple, action)] ; policy[output_tuple][action].
    No observation is inserted as a mechanism input by this mathematical benchmark.
    """
    validate_prior(k,prior)
    if not actions or len(set(actions))!=len(actions): raise ValueError('Distinct actions required.')
    outputs=set().union(*(set(r) for r in k.rows.values()))
    if set(policy)!=outputs: raise ValueError('A response rule is required for every output.')
    if set(reward)!={(x,a) for x in k.rows for a in actions}: raise ValueError('Complete task payoff required.')
    if any(not isinstance(v,F) for v in reward.values()): raise ValueError('Exact rewards required.')
    best=F(0); achieved=F(0); best_policy={}
    for y in sorted(outputs):
        py=policy[y]
        if not set(py)<=set(actions) or any(not isinstance(v,F) or v<0 for v in py.values()) or sum(py.values(),F(0))!=1:
            raise ValueError('Each response policy row must be normalized and exact.')
        scores={a:sum((prior.get(x,F(0))*row.get(y,F(0))*reward[x,a] for x,row in k.rows.items()),F(0)) for a in actions}
        optimum=max(scores.values()); best+=optimum
        best_policy[str(y)]=[a for a in actions if scores[a]==optimum]
        achieved+=sum((py.get(a,F(0))*scores[a] for a in actions),F(0))
    baseline=max(sum((prior.get(x,F(0))*reward[x,a] for x in k.rows),F(0)) for a in actions)
    return {'baseline':baseline,'optimal':best,'achieved':achieved,'gap':best-achieved,
            'optimal_gain':best-baseline,'achieved_gain':achieved-baseline,'optimal_actions':best_policy}


def binary_channel(a:F,b:F,input_var=None,output_var=None)->Kernel:
    from .finite import Variable
    if not all(isinstance(x,F) and 0<=x<=1 for x in (a,b)): raise ValueError('Probabilities outside [0,1].')
    x=input_var or Variable('S','assumption:binary-source',role='context')
    y=output_var or Variable('B','assumption:binary-readout')
    return Kernel('binary-response',(x,),(y,),{(0,):{(0,):1-a,(1,):a},(1,):{(0,):1-b,(1,):b}},
                  ('assumption:declared-binary-response',),law_status='derived')


def binary_rectangle_information(a_range:tuple[F,F],b_range:tuple[F,F],q:F=F(1,2))->dict:
    """Global extrema on a full rectangular binary-response family, fixed q.

    Not valid as exact extrema for a nonrectangular coupled parameter family.
    Maxima: vertices by convexity. Minimum: nearest endpoints, or zero on overlap.
    """
    al,ah=a_range; bl,bh=b_range
    if not (0<=al<=ah<=1 and 0<=bl<=bh<=1 and 0<q<1): raise ValueError('Invalid rectangle or prior.')
    prior={(0,):1-q,(1,):q}
    points=list(dict.fromkeys(product((al,ah),(bl,bh))))
    vals=[information(binary_channel(a,b),prior) for a,b in points]
    upper=Interval(max(v.lo for v in vals),max(v.hi for v in vals))
    if max(al,bl)<=min(ah,bh):
        low=Interval(F(0),F(0)); witness=(max(al,bl),max(al,bl))
    elif ah<bl:
        witness=(ah,bl); low=information(binary_channel(*witness),prior)
    else:
        witness=(al,bh); low=information(binary_channel(*witness),prior)
    max_index=max(range(len(vals)),key=lambda i:(vals[i].lo+vals[i].hi))
    # Numerical tie/witness ambiguity cannot alter the certified extrema enclosure.
    return {'minimum':low,'maximum':upper,'minimum_witness':tuple(map(str,witness)),
            'maximum_candidate':tuple(map(str,points[max_index])),
            'method':'analytic-global-extrema-on-full-binary-rectangle'}
