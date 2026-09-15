"""Independent result check; no EPAC import or constructors.

python3 verify_expansion.py <released data/sealed_known_molecular_geometry.json>
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
result=json.loads((HERE/'expansion-results.json').read_text())
plan=json.loads((HERE/'expansion-plan.json').read_text())
prior=json.loads((HERE/'verified-refinement.json').read_text())
assert result['plan']==plan
assert hashlib.sha256((HERE/'expanded_refinement.py').read_bytes()).hexdigest()==plan['script_sha256']
assert hashlib.sha256((HERE/'verified-refinement.json').read_bytes()).hexdigest()==plan['prior_results_sha256']
rows=result['observer_values']
assert len(rows)==63 and len(plan['new_states'])==36
assert set(rows)=={scale+':'+name for scale,name in plan['states']}
assert all(rows[k]==v for k,v in prior['observer_values'].items())
pairs=list(itertools.combinations(sorted(rows),2))
assert len(pairs)==1953
for r in result['frozen_candidate_results']:
    coll=[[a,b] for a,b in pairs if all(rows[a][n]==rows[b][n] for n in r['fields'])]
    assert coll==r['collisions']
    assert r['status']==('FALSIFIED' if coll else 'SURVIVED')
    witnesses=r['composition']['matched_parameter_witnesses']
    assert len(witnesses)==len(coll)
    for w in witnesses:
        a,b=w['left'],w['right']
        left,right=result['parents'][a]['readout'],result['parents'][b]['readout']
        expected={n:{'left':left[n],'right':right[n]} for n in left if left[n]!=right[n]}
        assert expected==w['post_composition_differences']
        # Actual constructor-retained values also agree with the source values.
        assert left=={n:v for n,v in rows[a].items() if n!='B'}
        assert right=={n:v for n,v in rows[b].items() if n!='B'}
    expected='FALSIFIED' if any(w['post_composition_differences'] for w in witnesses) else 'UNRESOLVED'
    assert r['composition']['status']==expected
search=result['expanded_minimum_search']
minimums=[set(r['fields']) for r in search['inclusion_minimal_sets']]
checked=0
for size in range(len(search['candidate_names'])+1):
    for combo in itertools.combinations(search['candidate_names'],size):
        direct=not any(all(rows[a][n]==rows[b][n] for n in combo) for a,b in pairs)
        assert direct==any(s<=set(combo) for s in minimums),combo
        checked+=1
for r in search['inclusion_minimal_sets']:
    assert not r['collisions'] and all(r['ablation_counterexamples'].values())
sealed=Path(sys.argv[1])
assert hashlib.sha256(sealed.read_bytes()).hexdigest()==result['shape_comparison']['sealed_sha256']
shapes={k:v['known_shape'] for k,v in json.loads(sealed.read_text())['molecules'].items()}
for r in result['shape_comparison']['candidates']:
    failures=[]
    for a,b in itertools.combinations(sorted(shapes),2):
        equal=all(rows['molecule:'+a][n]==rows['molecule:'+b][n] for n in r['fields'])
        if equal != (shapes[a]==shapes[b]):
            failures.append((a,b))
    assert failures==[(w['left'],w['right']) for w in r['mismatches']]
    assert r['status']==('FALSIFIED' if failures else 'SURVIVED')
assert len(result['retained_field_composition'])==189
assert all(r['status']=='SURVIVED' for r in result['retained_field_composition'])
print('SURVIVED: 63 states, 1953 pairs,',checked,'subsets, nine candidate results, composition witnesses and fixed shape comparisons verified')
