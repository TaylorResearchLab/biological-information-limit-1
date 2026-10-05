'Ribosome acceptance probabilities at a specified proofreading step. Published Fp summaries supply the acceptance ranges. Input priors, sensitivity families and upstream passage are stated modeling assumptions.'
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path
import sys
from typing import Sequence

from .finite import Variable, Kernel, Model, kernel
from .information import Interval, information, binary_rectangle_information

Exact = int | str | F
SOURCE = 'Zaher-Green-2010:10.1016/j.molcel.2010.06.009:Table-1-Fp'


def exact(x: Exact) -> F:
    if isinstance(x, bool) or not isinstance(x, (int, str, F)):
        raise TypeError('Use a Fraction, int, or rational/decimal string, not float.')
    return F(x)


def probability(x: Exact) -> F:
    v = exact(x)
    if not 0 <= v <= 1:
        raise ValueError('Probability outside [0,1].')
    return v


def probability_pair(values: Sequence[Exact]) -> tuple[F, F]:
    if len(values) != 2:
        raise ValueError('Supply one value for cognate and one for near-cognate.')
    return tuple(probability(x) for x in values)


@dataclass(frozen=True)
class AcceptanceBox:
    cognate: tuple[F, F]
    near_cognate: tuple[F, F]

    def __post_init__(self):
        for name in ('cognate', 'near_cognate'):
            vals = probability_pair(getattr(self, name))
            if vals[0] > vals[1]:
                raise ValueError('Reversed interval.')
            object.__setattr__(self, name, vals)
        if self.near_cognate[1] > self.cognate[0]:
            raise ValueError('This wrapper requires nonoverlapping ordered acceptance intervals.')


def source_variable() -> Variable:
    return Variable('S', 'declared:cognate-Phe-vs-near-cognate-Leu-at-UUC',
                    quantity='substrate class at the selected entrance boundary',
                    compartment='reconstituted ribosome preparation', role='context',
                    resolution='0=cognate; 1=near-cognate')


def acceptance_kernel(b_c: Exact, b_n: Exact) -> Kernel:
    c, n = probability_pair((b_c, b_n))
    s = source_variable()
    y = Variable('Y', 'declared:post-initial-selection-acceptance',
                 quantity='eventual acceptance rather than rejection',
                 compartment='reconstituted ribosome preparation',
                 resolution='0=rejection; 1=acceptance; no completion conditioning')
    return kernel('post-initial-selection', [s], [y],
                  lambda i: {(0,): 1-(c, n)[i[0]], (1,): (c, n)[i[0]]},
                  provenance=(SOURCE,
                              'assumption:source-Fp-interpreted-as-conditional-acceptance',
                              'assumption:two-outcome-eventual-fate-is-exhaustive',
                              'assumption:row-specific-preparations-transport-to-declared-ensemble'),
                  law_status='estimated')


def prior(q_near: Exact) -> dict[tuple[int], F]:
    q = probability(q_near)
    return {(0,): 1-q, (1,): q}


def bayes_accuracy(k: Kernel, q_near: Exact) -> F:
    q = probability(q_near)
    outputs = set(k.rows[(0,)]) | set(k.rows[(1,)])
    return sum((max((1-q)*k.rows[(0,)].get(y, F(0)),
                    q*k.rows[(1,)].get(y, F(0))) for y in outputs), F(0))


def accept_reject_rule_accuracy(b_c: Exact, b_n: Exact, q_near: Exact) -> F:
    c, n = probability_pair((b_c, b_n)); q = probability(q_near)
    # The descriptive decision rule calls acceptance cognate, rejection near-cognate.
    # It is not always the optimal decoder for an unbalanced source ensemble.
    return (1-q)*c + q*(1-n)


def info_bounds(box: AcceptanceBox, q_near: Exact) -> dict:
    q = probability(q_near)
    c0, c1 = box.cognate; n0, n1 = box.near_cognate
    if q in (0, 1):
        result = {'minimum': Interval(F(0), F(0)), 'maximum': Interval(F(0), F(0))}
    else:
        result = binary_rectangle_information(box.cognate, box.near_cognate, q)
    return {'q_near_at_selected_boundary': q,
            'cognate_acceptance': box.cognate, 'near_acceptance': box.near_cognate,
            'minimum_information_bits': result['minimum'],
            'maximum_information_bits': result['maximum'],
            'minimum_witness': (c0, n1), 'maximum_witness': (c1, n0),
            'scope': 'Analytic extrema over a declared closed probability rectangle, not a confidence interval',
            'source_prior_status': 'Declared comparison ensemble, not measured physiological frequency'}


def two_gate_model(a_c: Exact, a_n: Exact, b_c: Exact, b_n: Exact) -> Model:
    """Finite single-attempt assembly. Continuing dependence on S is retained.

    Earlier acceptance a is supplied, never inferred from the competition ratio.
    A=0 forces Y=0. The distinct history outcomes are (0,0), (1,0), (1,1).
    """
    ac, an = probability_pair((a_c, a_n)); bc, bn = probability_pair((b_c, b_n))
    s = source_variable()
    a = Variable('A', 'declared:initial-selection-pass',
                 quantity='passage through initial selection in one eligible attempt',
                 compartment='reconstituted ribosome preparation')
    y = Variable('Y', 'declared:terminal-acceptance',
                 quantity='eventual terminal acceptance in one eligible attempt',
                 compartment='reconstituted ribosome preparation')
    early = kernel('early-selection', [s], [a],
                   lambda i: {(0,): 1-(ac, an)[i[0]], (1,): (ac, an)[i[0]]},
                   provenance=('assumption:supplied-upstream-gate;specified',))
    later = kernel('later-selection', [s, a], [y],
                   lambda i: {(0,): F(1)} if i[1] == 0 else
                             {(0,): 1-(bc, bn)[i[0]], (1,): (bc, bn)[i[0]]},
                   provenance=(SOURCE, 'assumption:source-Fp-conditional-law',
                               'assumption:single-attempt-start-and-exhaustive-outcomes'),
                   law_status='estimated')
    return Model([s], [early, later])


def assembly_metrics(a_c: Exact, a_n: Exact, b_c: Exact, b_n: Exact,
                     q_near: Exact) -> dict:
    ac, an = probability_pair((a_c, a_n)); bc, bn = probability_pair((b_c, b_n))
    q = probability(q_near); pi = prior(q)
    model = two_gate_model(ac, an, bc, bn)
    full = model.boundary(['A', 'Y']); terminal = model.boundary(['Y'])
    early = model.boundary(['A'])
    z = (1-q)*ac + q*an
    early_info = information(early, pi)
    if z:
        q_cut = q*an/z
        cut_info = information(acceptance_kernel(bc, bn), prior(q_cut))
        cut_contribution = cut_info.scale(z)
    else:
        q_cut = None; cut_info = None
        cut_contribution = Interval(F(0), F(0))
    full_info = information(full, pi); terminal_info = information(terminal, pi)
    loss = Interval(full_info.lo-terminal_info.hi, full_info.hi-terminal_info.lo)
    return {'a': (ac, an), 'b': (bc, bn), 'q_near_at_attempt_start': q,
            'passage_probability': z, 'q_near_among_passed_attempts': q_cut,
            'history_channel': full.rows, 'terminal_channel': terminal.rows,
            'early_information_bits': early_info,
            'cut_information_bits_per_passed_attempt': cut_info,
            'weighted_cut_information_bits_per_original_attempt': cut_contribution,
            'history_information_bits': full_info,
            'chain_rule_rhs_bits': early_info + cut_contribution,
            'terminal_information_bits': terminal_info,
            'information_lost_by_merging_rejection_stages_bits': loss,
            'scope': 'Supplied single-attempt model; no inference of a biological upstream gate'}


def shared_cognate_garbling(c: Exact, n_better: Exact, n_worse: Exact) -> dict:
    """Map better accept/reject output to worse via source-independent noise.

    This mathematical comparison requires the SAME cognate acceptance and source
    ensemble, and proves a channel ordering only under that extra restriction.
    """
    c = probability(c); nb = probability(n_better); nw = probability(n_worse)
    if not nb <= nw < c:
        raise ValueError('Require n_better <= n_worse < shared c.')
    g = (c-nw)/(c-nb)
    f = c*(1-g)
    return {'accept_after_reject': f, 'accept_after_accept': f+g,
            'slope': g, 'maps_cognate_to': f+g*c,
            'maps_near_to': f+g*nb}


def survival_comparison(kp: Exact) -> dict:
    kp = exact(kp)
    if kp <= 0:
        raise ValueError('The survival ratio requires strictly positive kp.')
    kh, kw = F('0.04'), F('0.2')
    ah, aw = kp/(kp+kh), kp/(kp+kw)
    return {'kp_per_second': kp, 'H84A_like_survival': ah,
            'WT_like_survival': aw, 'survival_ratio': ah/aw,
            'survival_odds_ratio': (ah/(1-ah))/(aw/(1-aw)),
            'scope': 'Algebraic illustration at fixed analyst-selected kp, not an assay-transfer correction'}


def encode(x):
    if isinstance(x, F):
        return {'fraction': str(x), 'decimal': float(x)}
    if isinstance(x, Interval):
        return {'certified_decimal_enclosure': x.decimal(18),
                'width_upper_decimal': Interval(x.hi-x.lo,x.hi-x.lo).decimal(24)['upper']}
    if isinstance(x, dict):
        return {str(k): encode(v) for k,v in x.items()}
    if isinstance(x, (tuple,list)):
        return [encode(v) for v in x]
    return x


def research_results() -> dict:
    definitions = {
        'point_summaries': ((F('.05'), F('.05')), (F('.007'), F('.007'))),
        'one_displayed_error_unit': ((F('.048'), F('.052')), (F('.002'), F('.012'))),
        'two_displayed_error_units': ((F('.046'), F('.054')), (F(0), F('.017'))),
    }
    summaries = {}
    for label, (wt, res) in definitions.items():
        w = info_bounds(AcceptanceBox((F('.9'),F(1)),wt), F(1,2))
        r = info_bounds(AcceptanceBox((F('.9'),F(1)),res), F(1,2))
        low = Interval(r['minimum_information_bits'].lo-w['maximum_information_bits'].hi,
                       r['minimum_information_bits'].hi-w['maximum_information_bits'].lo)
        high = Interval(r['maximum_information_bits'].lo-w['minimum_information_bits'].hi,
                        r['maximum_information_bits'].hi-w['minimum_information_bits'].lo)
        summaries[label] = {'WT': w, 'restrictive': r,
                            'minimum_difference_bits': low, 'maximum_difference_bits': high,
                            'difference_family': 'Genotype-specific acceptance intervals vary separately; shared q=1/2'}
    q_sweep = {str(q): {g: info_bounds(AcceptanceBox((F('.9'),F(1)),n),q)
                        for g,n in [('WT',definitions['one_displayed_error_unit'][0]),
                                    ('restrictive',definitions['one_displayed_error_unit'][1])]}
               for q in (F(1,2),F(1,10),F(1,100))}
    controls = []
    for epsilon in (F(1),F(1,10),F(1,100),F(1,1000)):
        r = assembly_metrics(epsilon,epsilon,F('.95'),F('.007'),F(1,2))
        r['control_status'] = 'Synthetic upstream passage and cognate midpoint; published near-acceptance point'
        r['wrong_to_correct_product_ratio'] = F('.007')/F('.95')
        controls.append(r)
    ranking_counterexample = {}
    for label, (wc,rc) in {'restrictive_less_information':(F(1),F('.91')),
                           'restrictive_more_information':(F('.91'),F(1))}.items():
        wk, rk = acceptance_kernel(wc,F('.05')), acceptance_kernel(rc,F('.007'))
        wi,ri = information(wk,prior(F(1,2))),information(rk,prior(F(1,2)))
        ranking_counterexample[label] = {
            'WT_cognate': wc, 'restrictive_cognate':rc,
            'WT_information_bits':wi, 'restrictive_information_bits':ri,
            'difference_bits':Interval(ri.lo-wi.hi,ri.hi-wi.lo),
            'status':'Admissible model witness, not a measured genotype comparison'}
    return {
        'scope':'Source-interpreted post-initial-selection channels; model-implied, not measured cellular bits',
        'source': SOURCE,
        'input_convention':'S=0 cognate Phe; S=1 near-cognate Leu, at UUC; q denotes near-cognate frequency at declared boundary',
        'outcome_convention':'Y=0 rejection/nonacceptance; Y=1 acceptance; both outcomes included',
        'cognate_interval_status':'Closed conservative relaxation [0.9,1] of source >0.9 statement; lower boundary need not be attained by strict original family',
        'summary_families':summaries, 'source_prior_sensitivity':q_sweep,
        'ranking_counterexamples':ranking_counterexample,
        'shared_cognate_order_example':shared_cognate_garbling('.95','.007','.05'),
        'missing_upstream_gate_controls': controls,
        'changed_cut_prior_example':assembly_metrics('4/5','1/5','.95','.007','1/2'),
        'no_pass_example':assembly_metrics(0,0,'.95','.007','1/2'),
        'survival_algebra_correction':[survival_comparison(p) for p in ('1/1000','1/25','1/10','1')],
        'novelty_status':'Established Shannon information and probability identities; biological interpretation and partial-identification instantiation for review; no priority claim'
    }
