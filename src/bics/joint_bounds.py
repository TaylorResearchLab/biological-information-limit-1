'Two input classes and two binary reporters with exact marginal constraints. Unknown pairing is represented by the two conditional joint probabilities. The calculations distinguish the range of optimal accuracy across compatible laws from the guarantee of a fixed deterministic decoder. The supplied probabilities define a finite sensitivity family.'
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
from typing import Sequence, Union

Exact = Union[int, str, Fraction]
OUTCOMES = ((0, 0), (0, 1), (1, 0), (1, 1))


def exact(x: Exact) -> Fraction:
    """Reject binary floats rather than quietly treat rounded values as exact."""
    if isinstance(x, bool) or not isinstance(x, (int, str, Fraction)):
        raise TypeError('Use int, Fraction, or a decimal/rational string, not float.')
    return Fraction(x)


def probability(x: Exact) -> Fraction:
    x = exact(x)
    if not 0 <= x <= 1:
        raise ValueError('Probability must be in [0,1].')
    return x


@dataclass(frozen=True)
class JointFamily:
    # a[s]=P(X=1|s); b[s]=P(Y=1|s); q1=P(S=1).
    a: tuple[Fraction, Fraction]
    b: tuple[Fraction, Fraction]
    q1: Fraction
    bounds: tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]

    @classmethod
    def create(cls, a: Sequence[Exact], b: Sequence[Exact], q1: Exact = '1/2',
               joint_bounds: Sequence[Sequence[Exact]] | None = None) -> 'JointFamily':
        if len(a) != 2 or len(b) != 2:
            raise ValueError('Exactly two source classes are supported.')
        aa = tuple(probability(x) for x in a)
        bb = tuple(probability(x) for x in b)
        q = probability(q1)
        if joint_bounds is not None and len(joint_bounds) != 2:
            raise ValueError('One joint-probability interval per source class is needed.')
        out = []
        for s in range(2):
            lo, hi = max(Fraction(0), aa[s] + bb[s] - 1), min(aa[s], bb[s])
            if joint_bounds is not None:
                if len(joint_bounds[s]) != 2:
                    raise ValueError('Each interval must have two endpoints.')
                l, h = map(probability, joint_bounds[s])
                if l > h:
                    raise ValueError('Reversed interval.')
                lo, hi = max(lo, l), min(hi, h)
            if lo > hi:
                raise ValueError('Empty admissible family: joint and marginal constraints conflict.')
            out.append((lo, hi))
        return cls(aa, bb, q, tuple(out))

    def row(self, s: int, t: Fraction) -> tuple[Fraction, ...]:
        if s not in (0, 1):
            raise ValueError('Source class must be 0 or 1.')
        lo, hi = self.bounds[s]
        if not lo <= t <= hi:
            raise ValueError('Joint probability lies outside the admissible family.')
        a, b = self.a[s], self.b[s]
        return (1-a-b+t, b-t, a-t, t)

    def affine_row(self, s: int) -> tuple[tuple[Fraction, Fraction], ...]:
        # Each outcome probability is intercept + slope * t_s.
        a, b = self.a[s], self.b[s]
        return ((1-a-b, Fraction(1)), (b, Fraction(-1)),
                (a, Fraction(-1)), (Fraction(0), Fraction(1)))

    def corners(self) -> tuple[tuple[Fraction, Fraction], ...]:
        return tuple(sorted(set(product(*self.bounds))))


def accuracy(family: JointFamily, point: tuple[Fraction, Fraction]) -> Fraction:
    r0, r1 = family.row(0, point[0]), family.row(1, point[1])
    q0, q1 = 1-family.q1, family.q1
    return sum((max(q0*x, q1*y) for x, y in zip(r0, r1)), Fraction(0))


def policy_accuracy(family: JointFamily, point: tuple[Fraction, Fraction],
                    policy: Sequence[int]) -> Fraction:
    if len(policy) != 4 or any(x not in (0, 1) for x in policy):
        raise ValueError('Specify one class prediction (0 or 1) per joint outcome.')
    r0, r1 = family.row(0, point[0]), family.row(1, point[1])
    return sum(((1-family.q1)*r0[k] if action == 0 else family.q1*r1[k]
                for k, action in enumerate(policy)), Fraction(0))


def _candidate_points(family: JointFamily) -> tuple[tuple[Fraction, Fraction], ...]:
    # Boundary/kink lines A*t0 + B*t1 = C. Each resulting cell has an affine
    # objective, so a global minimum occurs at an arrangement vertex.
    lines = []
    for x in family.bounds[0]:
        lines.append((Fraction(1), Fraction(0), x))
    for y in family.bounds[1]:
        lines.append((Fraction(0), Fraction(1), y))
    q0, q1 = 1-family.q1, family.q1
    for (c0, d0), (c1, d1) in zip(family.affine_row(0), family.affine_row(1)):
        lines.append((q0*d0, -q1*d1, q1*c1-q0*c0))
    points = set(family.corners())
    for (a,b,c), (d,e,f) in combinations(lines, 2):
        det = a*e-b*d
        if det == 0:
            continue
        x, y = (c*e-b*f)/det, (a*f-c*d)/det
        if (family.bounds[0][0] <= x <= family.bounds[0][1] and
            family.bounds[1][0] <= y <= family.bounds[1][1]):
            points.add((x, y))
    return tuple(sorted(points))


def task_bounds(family: JointFamily) -> dict:
    points = _candidate_points(family)
    minimum = min((accuracy(family, p), p) for p in points)
    maximum = max((accuracy(family, p), p) for p in family.corners())
    # One deterministic decoder must be selected before the unknown coupling.
    policies = tuple(product((0, 1), repeat=4))
    robust = max((min(policy_accuracy(family, p, d) for p in family.corners()), d)
                 for d in policies)
    def witness(record):
        val, p = record
        return {'accuracy': val, 't': p,
                'channel': [family.row(s, p[s]) for s in (0,1)]}
    return {'minimum_law_known_accuracy': witness(minimum),
            'maximum_law_known_accuracy': witness(maximum),
            'best_fixed_deterministic_decoder': {'worst_case_accuracy': robust[0],
                                                 'decisions': robust[1]},
            'arrangement_candidates': len(points),
            'outcome_order': OUTCOMES,
            'numerical_status': 'Exact rational arithmetic on supplied rational constraints',
            'scope': 'Two source classes; two binary reporters; fixed marginals/prior; no empirical inference'}
