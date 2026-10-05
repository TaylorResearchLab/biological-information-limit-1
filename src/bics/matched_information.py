'Information and decision calculations for the fixed source-reporter marginal family of Bertschinger et al. (2014). Floating optimization proposes feasible points. Rational arithmetic and logarithm enclosures certify bounds using convex supporting hyperplanes. Results describe the specified probability families at a fixed input prior.'
from __future__ import annotations
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import math
import warnings
import numpy as np
from scipy.optimize import minimize, linprog
from .joint_bounds import JointFamily, task_bounds
from .information import Interval, log2_interval

ZERO = Interval(F(0), F(0))
D = (1, -1, -1, 1)


def interval_information(fam: JointFamily, point: tuple[F, F], terms: int = 24) -> Interval:
    rows = (fam.row(0, point[0]), fam.row(1, point[1]))
    pri = (1-fam.q1, fam.q1)
    mix = tuple(sum((pri[s]*rows[s][j] for s in range(2)), F(0)) for j in range(4))
    ans = ZERO
    for s in range(2):
        if pri[s] == 0:
            continue
        for j in range(4):
            if rows[s][j]:
                ans += log2_interval(rows[s][j]/mix[j], terms).scale(pri[s]*rows[s][j])
    return Interval(max(F(0), ans.lo), max(F(0), ans.hi))


def marginal_information(fam: JointFamily, a: tuple[F, F], terms: int = 24) -> Interval:
    pri = (1-fam.q1, fam.q1)
    rows = ((1-a[0], a[0]), (1-a[1], a[1]))
    mix = tuple(sum((pri[s]*rows[s][j] for s in range(2)), F(0)) for j in range(2))
    ans = ZERO
    for s in range(2):
        if pri[s] == 0:
            continue
        for j in range(2):
            if rows[s][j]:
                ans += log2_interval(rows[s][j]/mix[j], terms).scale(pri[s]*rows[s][j])
    return Interval(max(F(0), ans.lo), max(F(0), ans.hi))


def tangent_certificate(fam: JointFamily, point: tuple[F, F], terms: int = 24) -> dict:
    """An interior rational tangent lower bound over the ENTIRE declared box.

    Coordinates fixed by a singleton constraint need no derivative. A zero
    source prior is handled explicitly. Variable rows must be positive.
    No floating-point derivatives are used in the certificate.
    """
    value = interval_information(fam, point, terms)
    if fam.q1 in (0,1):
        return {'lower':F(0), 'upper':F(0), 'point':point, 'gradient':[ZERO,ZERO]}
    rows = [fam.row(s, point[s]) for s in range(2)]
    pri = (1-fam.q1, fam.q1)
    mix = [sum((pri[s]*rows[s][j] for s in range(2)), F(0)) for j in range(4)]
    lower = value.lo
    grads = []
    for s, (lo,hi) in enumerate(fam.bounds):
        if lo == hi:
            grads.append(ZERO)
            continue
        if not lo < point[s] < hi or min(rows[s]) <= 0:
            raise ValueError('A nonconstant coordinate requires a relative-interior rational point.')
        g = ZERO
        for j in range(4):
            g += log2_interval(rows[s][j]/mix[j], terms).scale(pri[s]*D[j])
        lower += min(g.scale(lo-point[s]).lo, g.scale(hi-point[s]).lo)
        grads.append(g)
    dpi = max(marginal_information(fam, fam.a, terms).lo,
              marginal_information(fam, fam.b, terms).lo)
    return {'lower':max(F(0), lower, dpi), 'upper':value.hi,
            'point':point, 'gradient':grads}


def garbling_minimum(fam: JointFamily, terms: int = 24) -> dict | None:
    """Find a source-independent reporter garbling as a DPI equality witness.

    For an exact fixed-marginal problem this can identify the minimum without
    numerical optimization. An optional joint constraint must also admit it.
    """
    if fam.q1 in (0, 1):
        p = tuple((lo+hi)/2 for lo,hi in fam.bounds)
        return {'lower':F(0),'upper':F(0),'point':p,'method':'zero source entropy'}
    for name, parent, child in [('X',fam.a,fam.b), ('Y',fam.b,fam.a)]:
        if parent[0] == parent[1]:
            if child[0] != child[1]:
                continue
            f = g = child[0]
        else:
            slope = (child[1]-child[0])/(parent[1]-parent[0])
            f, g = child[0]-slope*parent[0], child[0]-slope*parent[0]+slope
        if 0 <= f <= 1 and 0 <= g <= 1:
            point = tuple(parent[s]*g for s in range(2))
            if not all(lo <= t <= hi for t,(lo,hi) in zip(point,fam.bounds)):
                continue
            # Exactly verify marginal preservation under the proposed garbling.
            if any((1-parent[s])*f + parent[s]*g != child[s] for s in range(2)):
                raise AssertionError('Garbling reconstruction failed')
            val = marginal_information(fam,parent,terms)
            return {'lower':val.lo, 'upper':val.hi, 'point':point,
                    'method':'exact marginal DPI equality via '+name+' garbling',
                    'garbling':{'parent':name,'child_high_given_parent_low':f,
                                'child_high_given_parent_high':g}}
    return None


def _candidate(fam: JointFamily) -> tuple[tuple[F,F],dict]:
    """Floating candidate search; correctness comes from tangent_certificate."""
    variable = [s for s in range(2) if fam.bounds[s][0] < fam.bounds[s][1]]
    mids = [(lo+hi)/2 for lo,hi in fam.bounds]
    base = np.array([[float(1-fam.a[s]-fam.b[s]),float(fam.b[s]),float(fam.a[s]),0.] for s in range(2)])
    pri = np.array([float(1-fam.q1),float(fam.q1)])
    widths = np.array([float(hi-lo) for lo,hi in fam.bounds])
    lowers = np.array([float(lo) for lo,hi in fam.bounds])
    def fg(v):
        t = np.array([float(x) for x in mids])
        t[variable] = lowers[variable]+widths[variable]*v
        rows = base + t[:,None]*np.array(D)
        if rows.min() < -1e-12:
            raise ArithmeticError('Candidate left probability domain')
        # Clipping here is for floating evaluation only, never certification.
        rows = np.maximum(rows, 0.)
        mix = pri @ rows
        val = 0.; grads=[]
        for s in range(2):
            mask=rows[s]>0
            val += pri[s]*np.sum(rows[s,mask]*np.log2(rows[s,mask]/mix[mask]))
        for s in variable:
            safe=np.maximum(rows[s],1e-300); m=np.maximum(mix,1e-300)
            grads.append(pri[s]*widths[s]*np.dot(np.array(D),np.log2(safe/m)))
        return float(val),np.array(grads)
    candidates=[]
    # Bound away from zero only in the candidate search; certify on the original box.
    eps=1e-10
    for start in product((.1,.5,.9), repeat=len(variable)):
        with warnings.catch_warnings(record=True) as ws:
            result=minimize(fg,np.array(start),jac=True,method='SLSQP',
                            bounds=[(eps,1-eps)]*len(variable),
                            options={'ftol':1e-14,'maxiter':1000})
        candidates.append((float(result.fun),tuple(result.x),bool(result.success),
                           str(result.message),len(ws)))
    winner=min(candidates,key=lambda r:r[0])
    point=list(mids)
    for s,x in zip(variable,winner[1]):
        u=F(str(float(np.clip(x,eps,1-eps))))
        point[s]=fam.bounds[s][0]+(fam.bounds[s][1]-fam.bounds[s][0])*u
    return tuple(point), {'algorithm':'SciPy SLSQP candidate only','starts':len(candidates),
                         'converged':winner[2],'message':winner[3],
                         'recorded_warning_count':sum(x[4] for x in candidates)}


def information_bounds(fam: JointFamily, terms: int = 24) -> dict:
    if not isinstance(fam, JointFamily):
        raise TypeError('A validated JointFamily is required')
    corners=fam.corners()
    maxima=[(p,interval_information(fam,p,terms)) for p in corners]
    max_interval=Interval(max(i.lo for _,i in maxima),max(i.hi for _,i in maxima))
    upper_witness=max(maxima,key=lambda x:x[1].lo)[0]
    if len(corners)==1:
        minimum={'lower':max_interval.lo,'upper':max_interval.hi,'point':corners[0],
                 'method':'singleton family'}
    else:
        minimum=garbling_minimum(fam,terms)
        if minimum is None:
            point, search=_candidate(fam)
            minimum=tangent_certificate(fam,point,terms)
            minimum.update(method='convex tangent with rational interval logarithms',search=search)
    if minimum['lower'] > minimum['upper']:
        raise AssertionError('Inverted global minimum certificate')
    return {'minimum':minimum,'maximum':{'lower':max_interval.lo,'upper':max_interval.hi,
                                        'point':upper_witness,'method':'convex objective maximum at rectangle corner'},
            'family_bounds':fam.bounds,'prior':fam.q1,'log_series_terms':terms,
            'max_corners_evaluated':len(corners)}


def matched_decision_lps(fam: JointFamily) -> dict:
    """Match the existing reduced family to an 8-cell polytope and minimax LP.

    First LP minimizes law-known Bayes accuracy over eight joint conditional
    cells. Second LP selects a fixed randomized decoder against corner laws.
    Not a reimplementation of Farnia/Tse's trained minimax SVM or its Gamma.
    """
    pri=[float(1-fam.q1),float(fam.q1)]
    # 8 conditional probabilities and 4 epigraph variables.
    eq=[]; rhs=[]
    for s in range(2):
        for mask,b in [([1,1,1,1],1),([0,0,1,1],fam.a[s]),([0,1,0,1],fam.b[s])]:
            row=np.zeros(12);row[s*4:s*4+4]=mask;eq.append(row);rhs.append(float(b))
    bounds=[(0,None)]*12
    for s in range(2):
        bounds[s*4+3]=tuple(float(x) for x in fam.bounds[s])
    ub=[]
    for s in range(2):
        for j in range(4):
            row=np.zeros(12);row[s*4+j]=pri[s];row[8+j]=-1;ub.append(row)
    objective=np.zeros(12);objective[8:]=1
    law=linprog(objective,A_ub=np.array(ub),b_ub=np.zeros(8),
                A_eq=np.array(eq),b_eq=np.array(rhs),bounds=bounds,method='highs')
    # d_j=P(predict S=1 | response j), and v=guaranteed accuracy.
    # v <= sum q0*k0*(1-d) + q1*k1*d for every corner.
    rub=[]; rrhs=[]
    for point in fam.corners():
        k0=np.array([float(v) for v in fam.row(0,point[0])]);k1=np.array([float(v) for v in fam.row(1,point[1])])
        rub.append(np.r_[pri[0]*k0-pri[1]*k1,1.]);rrhs.append(pri[0])
    rob=linprog(np.array([0.,0.,0.,0.,-1.]),A_ub=np.array(rub),b_ub=np.array(rrhs),
                bounds=[(0,1)]*5,method='highs')
    if not law.success or not rob.success:
        raise RuntimeError('Matched LP failed: '+str((law.message,rob.message)))
    exact=task_bounds(fam)
    lo=float(exact['minimum_law_known_accuracy']['accuracy'])
    det=float(exact['best_fixed_deterministic_decoder']['worst_case_accuracy'])
    residual=float(max(np.max(np.abs(np.array(eq)@law.x-np.array(rhs))),
                       np.max(np.array(ub)@law.x),0.))
    return {'law_known_minimum_8cell_lp':float(law.fun),
            'randomized_fixed_decoder_guarantee':float(-rob.fun),
            'randomized_decoder_probability_class1':rob.x[:4].tolist(),
            'exact_minimum':lo,'exact_deterministic_guarantee':det,
            'absolute_discrepancy':max(abs(float(law.fun)-lo),abs(float(-rob.fun)-lo)),
            'lp_primal_constraint_residual':residual,'solves':2}


def encode(obj):
    if isinstance(obj,F):
        return str(obj)
    if isinstance(obj,Interval):
        return obj.decimal(18)
    if isinstance(obj,dict):
        return {k:encode(v) for k,v in obj.items()}
    if isinstance(obj,(tuple,list)):
        return [encode(v) for v in obj]
    return obj


def compact_bounds(res: dict) -> dict:
    # Omit large internal rational endpoints BEFORE encoding. Directed decimal
    # enclosures suffice for the specified bounds; retain all rational witnesses.
    trimmed={k:({a:b for a,b in v.items() if a not in ('lower','upper')}
                if k in ('minimum','maximum') else v) for k,v in res.items()}
    out=encode(trimmed)
    for role in ('minimum','maximum'):
        r=res[role]; iv=Interval(r['lower'],r['upper'])
        out[role]['bits_enclosure']=iv.decimal(15)
        out[role]['certificate_width_bits']=float(r['upper']-r['lower'])
        # Full enormous rational log bounds are unnecessary; decimal endpoints
        # are rigorously outward rounded. Rational candidate points are retained.
        out[role].pop('lower',None);out[role].pop('upper',None)
    return out
