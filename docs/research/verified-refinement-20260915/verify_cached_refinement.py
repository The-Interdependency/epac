"""Independent direct enumeration check: python3 verify_cached_refinement.py."""
import itertools
import json
from pathlib import Path

p = json.loads(Path(__file__).with_name('verified-refinement.json').read_text())
rows = p['observer_values']
pairs = list(itertools.combinations(rows, 2))
assert len(rows) == 27 and len(pairs) == 351
for label in ('B_refinements', 'unrestricted_field_search'):
    r = p[label]
    minimal = [set(x['fields']) for x in r['inclusion_minimal_sets']]
    checked = 0
    for size in range(len(r['candidate_names'])+1):
        for subset in itertools.combinations(r['candidate_names'], size):
            fields = tuple(r['base'])+subset
            direct = not any(all(rows[a][n] == rows[b][n] for n in fields) for a,b in pairs)
            assert direct == any(s <= set(subset) for s in minimal), subset
            checked += 1
    for m in r['inclusion_minimal_sets']:
        assert not m['collisions']
        assert all(m['ablation_counterexamples'].values())
    print(label, checked, 'subsets independently verified: SURVIVED')
assert not p['challenges']['equivariance_failures']
assert all(r['status'] == 'SURVIVED' for r in p['composition_field_tests'])
print('Recorded equivariance and retained-field composition checks: SURVIVED')
