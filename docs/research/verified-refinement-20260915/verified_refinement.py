"""External finite search. Run with released EPAC and locked UCNS on PYTHONPATH.

python3 verified_refinement.py --output verified-refinement.json
Minimum means number of named observer functions, not bits or physical primitives.
Molecular intrinsic fields use sorted participant multisets (multiplicity retained).
"""
import argparse
import dataclasses
import hashlib
import itertools
import json
from pathlib import Path
import sys

import epac_boundary_probe_completeness as audit
import epac_dimensional_arity as da


def freeze(x):
    if dataclasses.is_dataclass(x):
        x = dataclasses.asdict(x)
    if isinstance(x, dict):
        return tuple(sorted((k, freeze(v)) for k, v in x.items()))
    if isinstance(x, (tuple, list)):
        return tuple(map(freeze, x))
    return x


def key(x):
    return json.dumps(freeze(x), sort_keys=True)


def search(rows, base=()):
    names = sorted(set(next(iter(rows.values()))) - set(base))
    pairs = list(itertools.combinations(sorted(rows), 2))
    def collisions(fields):
        return [(a, b) for a, b in pairs if all(rows[a][n] == rows[b][n] for n in fields)]
    baseline = collisions(base)
    masks = {n: sum(1 << i for i, (a,b) in enumerate(baseline) if rows[a][n] != rows[b][n]) for n in names}
    target = (1 << len(baseline)) - 1
    sufficient = []
    for count in range(len(names) + 1):
        for combo in itertools.combinations(names, count):
            if any(set(s) <= set(combo) for s in sufficient):
                continue
            mask = 0
            for n in combo:
                mask |= masks[n]
            if mask == target:
                sufficient.append(combo)
    minimum = min(map(len, sufficient), default=None)
    return {
        'base': base, 'pair_count': len(pairs), 'baseline_collisions': baseline,
        'candidate_names': names, 'subsets_in_search_space': 2**len(names),
        'minimum_additional_observers': minimum,
        'minimum_sets': [s for s in sufficient if len(s)==minimum],
        'inclusion_minimal_sets': [
            {'fields': s, 'collisions': collisions(base+s),
             'ablation_counterexamples': {n: collisions(base+tuple(x for x in s if x!=n)) for n in s}}
            for s in sufficient],
        'all_candidate_collisions': collisions(base+tuple(names)),
        'single_additions': {n: collisions(base+(n,)) for n in names},
        'status': 'SURVIVED' if sufficient else 'FALSIFIED',
    }


def rename(value, inverse):
    """Inverse a known bijection on exact ID values, never prose or substrings."""
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    if isinstance(value, str):
        return inverse.get(value, value)
    if isinstance(value, dict):
        return {k: rename(v, inverse) for k,v in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(rename(v, inverse) for v in value)
    return value


def challenges():
    ids = ('epac.audit.a', 'epac.audit.b', 'epac.audit.c')
    ops = {f.__name__: f for f in (da.degree_relations, da.geometry_from_declared_couplings,
        da.structure_from_charged_couplings, da.local_three_structures, da.quaternions_from_declared_couplings)}
    cases, equivariance_failures, pairs = [], [], []
    for charges in itertools.product((-1, 0, 1), repeat=3):
        for order in itertools.permutations(ids):
            space = da.space(ids, (order,), charges=dict(zip(ids, charges)))
            structure = da.structure_from_charged_couplings(space)
            row = {n: freeze(f({'structure': structure})) for n,f in audit.OMITTED_OBSERVABLES.items()}
            cases.append({'charges': charges, 'order': order, 'observers': row,
                          'behavior': {n: freeze(op(space)) for n,op in ops.items()}})
            for renamed in itertools.permutations(('axis.u', 'axis.v', 'axis.w')):
                mapping = dict(zip(ids, renamed))
                inverse = {v:k for k,v in mapping.items()}
                transformed = da.space(renamed, (tuple(mapping[x] for x in order),),
                                       charges=dict(zip(renamed, charges)))
                for n,op in ops.items():
                    if freeze(rename(op(transformed), inverse)) != freeze(op(space)):
                        equivariance_failures.append({'operation': n, 'order': order, 'charges': charges, 'rename': mapping})
    for n in audit.OMITTED_OBSERVABLES:
        mismatches = [(i,j) for i,j in itertools.combinations(range(len(cases)),2)
                      if cases[i]['observers'][n] == cases[j]['observers'][n]
                      and cases[i]['behavior']['degree_relations'] != cases[j]['behavior']['degree_relations']]
        pairs.append({'observer': n, 'same_observer_different_degree_pairs': len(mismatches),
                      'example': [cases[i] for i in mismatches[0]] if mismatches else [],
                      'status': 'FALSIFIED' if mismatches else 'SURVIVED'})
    return {'scope': '162 abstract ordered ternary declarations; exact ordered degree output is target behavior',
            'cases': cases, 'observer_sufficiency': pairs,
            'equivariance_comparisons': len(cases)*6*len(ops),
            'equivariance_failures': equivariance_failures,
            'equivariance_status': 'FALSIFIED' if equivariance_failures else 'SURVIVED',
            'physical_chirality': 'UNRESOLVED',
            'note': 'No pairwise declaration does not establish spatial nonintersection. Ordered triples do not establish cyclic equivalence.'}


def run():
    print('Constructing 27 states from release source', flush=True)
    contexts = audit._state_contexts()
    rows, composition = {}, []
    fields = ('Z', 'A', 'period', 'group', 'electron-configuration', 'valence-electrons', 'harmonic-surviving')
    for sid, c in contexts.items():
        state = c['state']
        gonol = c['source'].receipt.gonol if state.scale == 'molecule' else c['source'].gonol
        atoms = gonol.participants if state.scale == 'molecule' else (gonol,)
        row = {'B': state.b}
        for name in fields:
            # Missing is an error, never an automatic separator.
            row[name] = tuple(sorted((dict(a.carried_options)[name] for a in atoms), key=key))
        row.update({n: freeze(f(c)) for n,f in audit.OMITTED_OBSERVABLES.items()})
        rows[sid] = row
    print('Searching subsets and all state pairs', flush=True)
    from epac_molecular import MOLECULE_COMPOSITIONS
    for formula, atoms in MOLECULE_COMPOSITIONS.items():
        for name in fields:
            expected = tuple(sorted((v for symbol,count in atoms for _ in range(count)
                            for v in rows['element:'+symbol][name]), key=key))
            composition.append({'formula': formula, 'field': name,
                                'status': 'SURVIVED' if expected == rows['molecule:'+formula][name] else 'FALSIFIED'})
    sub_to_element = [{'symbol': sid.split(':')[1], 'field': n,
                      'status': 'SURVIVED' if row[n] == rows[sid.replace('subatomic:', 'element:')][n] else 'FALSIFIED'}
                     for sid,row in rows.items() if sid.startswith('subatomic:') for n in fields]
    proposed = ('B','Z','topology_structure_readout')
    prior_collisions = [(a,b) for a,b in itertools.combinations(sorted(rows),2)
                        if all(rows[a][n] == rows[b][n] for n in proposed)]
    result = {'schema': 'epac.external.verified-refinement.v1', 'epac_source': str(Path(audit.__file__).parent),
        'release_commit': '949cb1cb304927942966c9fb396caf6227120e7f',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'state_count': len(rows), 'observer_values': rows,
        'B_refinements': search(rows, ('B',)), 'unrestricted_field_search': search(rows),
        'prior_proposal': {'fields': proposed, 'collisions': prior_collisions,
                           'status': 'FALSIFIED' if prior_collisions else 'SURVIVED'},
        'composition_field_tests': composition+sub_to_element,
        'composition_scope': 'retained intrinsic field multisets only; no structural aggregation law proved',
        'global_sufficiency': 'UNRESOLVED', 'canonicality': 'UNRESOLVED',
        'structural_composition': 'UNRESOLVED'}
    print('Running ternary and bijective-renaming challenges', flush=True)
    result['challenges'] = challenges()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = run()
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('state_count','prior_proposal')}, indent=2))
    for label in ('B_refinements', 'unrestricted_field_search'):
        print(label, result[label]['minimum_sets'])
