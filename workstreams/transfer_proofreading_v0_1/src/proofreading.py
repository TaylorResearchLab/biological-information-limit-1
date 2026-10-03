"""Single-bound-encounter proofreading, not a full T-cell population model.

Each step competes with dissociation; source identity remains a parent of each step.
No ODE/PDE solver. Coarse probabilities are declared, never inferred from topology.
"""
from fractions import Fraction as F
from math import prod
from bics_finite import Variable, Kernel, Model
from transfer import binary_channel, binary_rectangle_information, information, log2_interval, Interval


def coarse_from_competing_rates(kp:F,off:F)->F:
    """Reference crosswalk only: independent exponential clocks with these rates."""
    if not all(isinstance(x,F) for x in (kp,off)) or kp<=0 or off<0:
        raise ValueError('Positive progression and nonnegative dissociation rates required.')
    return kp/(kp+off)


def build(alphas0,alphas1)->Model:
    if len(alphas0)!=len(alphas1): raise ValueError('Two classes must have the same declared stages.')
    if any(not isinstance(a,F) or not 0<=a<=1 for a in list(alphas0)+list(alphas1)):
        raise ValueError('Exact per-stage probabilities required.')
    s=Variable('S','assumption:proofreading-ligand-class',role='context',quantity='assigned ligand class')
    a0=Variable('A0','assumption:already-formed-complex',quantity='encounter initially bound')
    ks=[Kernel('initially_bound',(),(a0,),{():{(1,):F(1)}},('assumption:single-bound-encounter',))]
    prev=a0
    for n,(p0,p1) in enumerate(zip(alphas0,alphas1),1):
        nxt=Variable(f'A{n}',f'assumption:survived-stage-{n}',quantity='stage completed before first dissociation')
        rows={}
        for source in (0,1):
            p=(p0,p1)[source]
            rows[source,0]={(0,):F(1)}
            rows[source,1]={(0,):1-p,(1,):p}
        ks.append(Kernel(f'proofread_{n:03d}',(s,prev),(nxt,),rows,
                         ('reference:McKeithan-1995-step-survival','assumption:single-bound-encounter',
                          f'assumption:stage-law:{n}:{p0}:{p1}')))
        prev=nxt
    return Model((s,),ks)


def endpoint(alphas0,alphas1):
    if len(alphas0)!=len(alphas1): raise ValueError('Stage counts differ.')
    # The builder validates probability domains.
    model=build(alphas0,alphas1)
    a=prod(alphas0,start=F(1)); b=prod(alphas1,start=F(1))
    return binary_channel(a,b,input_var=model.roots[0],output_var=model.variables[f'A{len(alphas0)}'])


def response_metrics(a:F,b:F,q:F=F(1,2))->dict:
    k=binary_channel(a,b)
    if not 0<q<1: raise ValueError('Use a nondegenerate declared prior.')
    err=min((1-q)*(1-a),q*(1-b))+min((1-q)*a,q*b)
    out={'success_self':a,'success_agonist':b,'bayes_error':err,
         'information_bits':information(k,{(0,):1-q,(1,):q}),
         'completion_ratio':None if a==0 else b/a,
         'model_false_positive':a,'model_false_negative':1-b}
    # Bhattacharyya coefficient is a Chernoff coefficient at theta=1/2, not
    # claimed to be the optimized Chernoff information.
    from transfer import sqrt_interval
    bc=sqrt_interval(a*b)+sqrt_interval((1-a)*(1-b))
    out['bhattacharyya_coefficient']=bc
    return out


def rectangle_from_stage_intervals(intervals0,intervals1,q:F=F(1,2))->dict:
    if len(intervals0)!=len(intervals1): raise ValueError('Stage counts differ.')
    for lo,hi in list(intervals0)+list(intervals1):
        if not isinstance(lo,F) or not isinstance(hi,F) or not 0<=lo<=hi<=1:
            raise ValueError('Invalid stage interval.')
    a=(prod((r[0] for r in intervals0),start=F(1)),prod((r[1] for r in intervals0),start=F(1)))
    b=(prod((r[0] for r in intervals1),start=F(1)),prod((r[1] for r in intervals1),start=F(1)))
    result=binary_rectangle_information(a,b,q)
    result['success_self_range']=a;result['success_agonist_range']=b
    result['assumptions']='Independent epistemic box across class/stage laws; conditional stage sampling as in build.'
    return result


def log_likelihood_contributions(alphas0,alphas1):
    """Evidence at terminal failure depth or completion; covers EVERY trial.

    Independent fresh step noises conditional on S and survival; observing the
    entire survival history is not the same biological readout as completion.
    """
    if any(a<=0 or a>=1 for a in list(alphas0)+list(alphas1)):
        raise ValueError('Interior probabilities needed for finite log likelihoods.')
    p0=p1=F(1); items=[]
    for n,(a,b) in enumerate(zip(alphas0,alphas1),1):
        d0=p0*(1-a);d1=p1*(1-b)
        items.append({'outcome':f'failure_at_{n}','P_self':d0,'P_agonist':d1,
                      'log2_likelihood_ratio':log2_interval(d1/d0)})
        p0*=a;p1*=b
    items.append({'outcome':'completed','P_self':p0,'P_agonist':p1,
                  'log2_likelihood_ratio':log2_interval(p1/p0)})
    return items
