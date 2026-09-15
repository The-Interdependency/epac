"""Search cached executed ternary witnesses; no physical meaning is assigned.

PYTHONPATH=<released EPAC>:<locked UCNS>/src python3 ternary_refinement_search.py
"""
import itertools
import json
from pathlib import Path
from verified_refinement import freeze, search

HERE = Path(__file__).resolve().parent
source = json.loads((HERE/'verified-refinement.json').read_text())
rows = {}
for index, case in enumerate(source['challenges']['cases']):
    order = tuple('epac.audit.'+x for x in 'abc')
    permutation = tuple(order.index(x) for x in case['order'])
    parity = sum(permutation[i]>permutation[j] for i in range(3) for j in range(i+1,3)) % 2
    rows[str(index)] = {
        **{k: freeze(v) for k,v in case['observers'].items()},
        'slot_assignment': permutation,
        'parity': parity,
        'first_slot_axis': permutation[0],
        'axis_charge_assignment': tuple(case['charges']),
    }
result = search(rows)
# The identity target is exact labeled ordered degree output. Check that it
# actually distinguishes every witness before asking for state separation.
behavior = [freeze(c['behavior']['degree_relations']) for c in source['challenges']['cases']]
assert len(set(behavior)) == len(rows)
assert len(rows) == 162
assert len(result['baseline_collisions']) == 13041
assert result['all_candidate_collisions'] == []
assert all(r['ablation_counterexamples'][n] for r in result['inclusion_minimal_sets'] for n in r['fields'])
# Countercheck the bijective renamer on metadata keys, substrings and charges.
from verified_refinement import rename
assert rename({'ambient_count':3, 'ids':['axis.u'], 'text':'prefix-axis.u'}, {'axis.u':'a'}) == {
    'ambient_count':3, 'ids':('a',), 'text':'prefix-axis.u'}
result['target'] = 'exact ordered degree relations on fixed ambient axes; not spatial chirality'
result['claim'] = 'finite observer-count minimum, not a global or bit-count minimum'
result['derived_fields'] = 'slot_assignment, parity and first_slot_axis are all computed from the already retained ordered coupling'
result['controls_status'] = 'SURVIVED'
(HERE/'ternary-refinement-search.json').write_text(json.dumps(result,indent=2)+'\n')
print('minimum',result['minimum_additional_observers'], result['minimum_sets'])
print('inclusion_minimal', [r['fields'] for r in result['inclusion_minimal_sets']])
