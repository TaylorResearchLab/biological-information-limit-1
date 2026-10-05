'Finite acyclic biological process models with exact rational probabilities. Transition laws and biological scope are specified by the modeler.'
from __future__ import annotations
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import product
from math import log2
from typing import Callable, Iterable, Mapping, Sequence

F = Fraction
State = tuple[int, ...]
Distribution = dict[State, F]

@dataclass(frozen=True)
class Variable:
    name: str
    identity: str
    quantity: str = 'binary activity'
    compartment: str = 'declared toy compartment'
    role: str = 'state'
    domain: tuple[int, ...] = (0, 1)
    units: str = 'dimensionless'
    resolution: str = 'stipulated binary state'

    def validate(self) -> None:
        if not self.name or not self.identity or not self.quantity or not self.compartment:
            raise ValueError('Variables need explicit names, identities, quantities and compartments.')
        if self.role not in {'state', 'context', 'observation'}:
            raise ValueError(f'Invalid role: {self.role}')
        if not self.domain or len(set(self.domain)) != len(self.domain):
            raise ValueError('A finite domain must be nonempty and have unique states.')

@dataclass(frozen=True)
class Kernel:
    instance_id: str
    inputs: tuple[Variable, ...]
    outputs: tuple[Variable, ...]
    rows: Mapping[State, Mapping[State, F]]
    provenance: tuple[str, ...]
    kind: str = 'mechanism'
    admissible: bool = True
    law_status: str = 'stipulated'

    def validate(self) -> None:
        if not self.instance_id or not self.provenance:
            raise ValueError('A kernel needs an instance ID and an explicit source/assumption reference.')
        if not self.admissible:
            raise ValueError(f'{self.instance_id}: declared inadmissible.')
        if self.kind not in {'mechanism', 'observation'}:
            raise ValueError('Only mechanism and passive observation kernels are executable here.')
        if self.law_status not in {'stipulated', 'derived', 'estimated'}:
            raise ValueError('Declare whether the law is stipulated, derived or estimated.')
        allvars = self.inputs + self.outputs
        for v in allvars:
            v.validate()
        if len({v.name for v in allvars}) != len(allvars):
            raise ValueError('Each input/output port names a distinct variable. Use a new time index for updates.')
        if not self.outputs:
            raise ValueError('An executable motif must have at least one output.')
        if self.kind == 'mechanism':
            if any(v.role == 'observation' for v in self.inputs):
                raise ValueError('Passive observations cannot drive a mechanism in this realization.')
            if any(v.role != 'state' for v in self.outputs):
                raise ValueError('Mechanism outputs must be biological state variables.')
        elif any(v.role != 'observation' for v in self.outputs):
            raise ValueError('Observation kernels must output observation variables.')
        expected_inputs = set(product(*(v.domain for v in self.inputs)))
        expected_outputs = set(product(*(v.domain for v in self.outputs)))
        if set(self.rows) != expected_inputs:
            raise ValueError('Every input state, including off-support states, needs an explicit row.')
        for inp, row in self.rows.items():
            if not set(row) <= expected_outputs:
                raise ValueError(f'Output state outside declared domain at {inp}.')
            if any(not isinstance(p, F) or p < 0 for p in row.values()):
                raise ValueError('Probabilities must be nonnegative Fraction values.')
            if sum(row.values(), F(0)) != 1:
                raise ValueError(f'Unnormalized row at {inp}. Gates require an inactive law, not missing mass.')

    def fingerprint(self) -> tuple:
        return (self.inputs, self.outputs, self.kind, self.admissible, self.law_status,
                tuple(sorted((i, tuple(sorted((o,p) for o,p in row.items() if p)))
                             for i,row in self.rows.items())))


def kernel(instance_id: str, inputs: Sequence[Variable], outputs: Sequence[Variable],
           rule: Callable[[State], Mapping[State, F]], *, kind: str = 'mechanism',
           provenance: tuple[str, ...] = ('assumption:synthetic-test-law',),
           law_status: str = 'stipulated') -> Kernel:
    k = Kernel(instance_id, tuple(inputs), tuple(outputs),
               {i: dict(rule(i)) for i in product(*(v.domain for v in inputs))},
               provenance, kind=kind, law_status=law_status)
    k.validate()
    return k


def deterministic(instance_id: str, inputs: Sequence[Variable], outputs: Sequence[Variable],
                  rule: Callable[[State], State], **kwargs) -> Kernel:
    return kernel(instance_id, inputs, outputs, lambda i: {rule(i): F(1)}, **kwargs)


def bsc(instance_id: str, source: Variable, target: Variable, epsilon: F,
        *, kind: str = 'mechanism') -> Kernel:
    if not isinstance(epsilon,F) or not 0 <= epsilon <= 1:
        raise ValueError('epsilon must be a Fraction in [0,1].')
    return kernel(instance_id, [source], [target],
                  lambda i: {(i[0],): 1-epsilon, (1-i[0],): epsilon}, kind=kind,
                  provenance=(f'assumption:binary-symmetric-error={epsilon}',))

class Model:
    def __init__(self, roots: Sequence[Variable], motifs: Sequence[Kernel]):
        self.roots = tuple(roots)
        if len({v.name for v in self.roots}) != len(self.roots):
            raise ValueError('Duplicate root variable.')
        self.variables = {v.name: v for v in self.roots}
        for v in self.roots:
            v.validate()
            if v.role == 'observation':
                raise ValueError('Passive observations are not exogenous biological inputs here.')
        canonical: dict[str, Kernel] = {}
        for k in motifs:
            k.validate()
            if k.instance_id in canonical:
                prev = canonical[k.instance_id]
                if prev.fingerprint() != k.fingerprint():
                    raise ValueError('Same instance ID carries contradictory laws or interfaces.')
                canonical[k.instance_id] = replace(prev, provenance=tuple(sorted(set(prev.provenance+k.provenance))))
            else:
                canonical[k.instance_id] = k
            for v in k.inputs+k.outputs:
                if v.name in self.variables and self.variables[v.name] != v:
                    raise ValueError(f'Incompatible interface descriptors for {v.name}.')
                self.variables[v.name] = v
        writers: dict[str,str] = {}
        roots_set = {v.name for v in roots}
        for k in canonical.values():
            for v in k.outputs:
                if v.name in roots_set or v.name in writers:
                    raise ValueError(f'Duplicate writer for {v.name}; evidence is not another transition.')
                writers[v.name] = k.instance_id
        pending = sorted(canonical.values(), key=lambda k:k.instance_id)
        available = set(roots_set)
        ordered = []
        while pending:
            ready = [k for k in pending if all(v.name in available for v in k.inputs)]
            if not ready:
                raise ValueError('Cyclic dependencies or undeclared input variables.')
            for k in ready:
                ordered.append(k)
                available.update(v.name for v in k.outputs)
                pending.remove(k)
        self.motifs = tuple(ordered)
        self.order = tuple(v.name for v in self.roots)+tuple(v.name for k in self.motifs for v in k.outputs)

    def evaluate(self, root_distribution: Mapping[State,F], max_assignments: int = 1000000) -> Distribution:
        expected = set(product(*(v.domain for v in self.roots)))
        if not set(root_distribution) <= expected or any(not isinstance(p,F) or p < 0 for p in root_distribution.values()):
            raise ValueError('Invalid root distribution.')
        if sum(root_distribution.values(),F(0)) != 1:
            raise ValueError('Root distribution must sum to one.')
        dist = {x:p for x,p in root_distribution.items() if p}
        names = [v.name for v in self.roots]
        for k in self.motifs:
            positions = [names.index(v.name) for v in k.inputs]
            out: Distribution = {}
            for assignment, p in dist.items():
                inp = tuple(assignment[j] for j in positions)
                for value,q in k.rows[inp].items():
                    if q:
                        key = assignment+value
                        out[key] = out.get(key,F(0))+p*q
            if len(out) > max_assignments:
                raise ValueError('Exact enumeration limit exceeded; choose a smaller finite example.')
            dist = out
            names.extend(v.name for v in k.outputs)
        return dist

    def marginal(self, distribution: Mapping[State,F], names: Sequence[str]) -> Distribution:
        positions = [self.order.index(n) for n in names]
        out: Distribution = {}
        for assignment,p in distribution.items():
            key = tuple(assignment[j] for j in positions)
            out[key] = out.get(key,F(0))+p
        return {x:p for x,p in out.items() if p}

    def boundary(self, output_names: Sequence[str], instance_id: str = 'effective') -> Kernel:
        outs = tuple(self.variables[n] for n in output_names)
        kinds = {v.role for v in outs}
        if len(kinds) != 1 or not kinds <= {'state','observation'}:
            raise ValueError('A boundary kernel must have uniformly state or observation outputs.')
        rows = {i: self.marginal(self.evaluate({i:F(1)}), output_names)
                for i in product(*(v.domain for v in self.roots))}
        result = Kernel(instance_id, self.roots, outs, rows,
                        tuple('derived-from:'+k.instance_id for k in self.motifs),
                        kind='observation' if kinds == {'observation'} else 'mechanism',
                        law_status='derived')
        result.validate()
        return result


def total_variation(p: Mapping[State,F], q: Mapping[State,F]) -> F:
    return sum((abs(p.get(x,F(0))-q.get(x,F(0))) for x in set(p)|set(q)),F(0))/2


def kernel_distance(k: Kernel, l: Kernel) -> F:
    if k.inputs != l.inputs or k.outputs != l.outputs:
        raise ValueError('Kernel comparison requires identical declared interfaces.')
    return max(total_variation(k.rows[i],l.rows[i]) for i in k.rows)


def mutual_information(joint: Mapping[State,F], x_indices: Sequence[int], y_indices: Sequence[int]) -> float:
    if set(x_indices)&set(y_indices):
        raise ValueError('Use disjoint coordinate sets for this MI helper.')
    if sum(joint.values(),F(0)) != 1 or any(p < 0 for p in joint.values()):
        raise ValueError('Invalid joint distribution.')
    px: dict[State,F] = {}; py: dict[State,F] = {}; pxy: dict[tuple[State,State],F] = {}
    for a,p in joint.items():
        x=tuple(a[i] for i in x_indices); y=tuple(a[i] for i in y_indices)
        px[x]=px.get(x,F(0))+p; py[y]=py.get(y,F(0))+p
        pxy[x,y]=pxy.get((x,y),F(0))+p
    return sum(float(p)*log2(float(p/(px[x]*py[y]))) for (x,y),p in pxy.items() if p)


def uniform(variables: Sequence[Variable]) -> Distribution:
    states = list(product(*(v.domain for v in variables)))
    return {s:F(1,len(states)) for s in states}


def source_joint(k: Kernel, prior: Mapping[State,F]) -> Distribution:
    return {i+o:p*q for i,p in prior.items() for o,q in k.rows[i].items() if p*q}
