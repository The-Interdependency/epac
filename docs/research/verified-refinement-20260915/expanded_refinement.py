"""Freeze then execute the next-domain challenge, against exact v0.1.0.

python3 expanded_refinement.py --plan expansion-plan.json
python3 expanded_refinement.py --run expansion-plan.json --output expansion-results.json
Keep the same released EPAC/UCNS PYTHONPATH as reproduce.sh.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import epac_atomic
import epac_molecular as molecular
import epac_periodic as periodic
import epac_boundary_probe_completeness as probes
from epac_subatomic import subatomic_gonol as subatomic
from epac_public_gonol import construct_public_gonol, replay_public_gonol
from verified_refinement import freeze, key, search

HERE = Path(__file__).resolve().parent
FIELDS = ('Z','A','period','group','electron-configuration','valence-electrons','harmonic-surviving')


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def plan():
    prior = json.loads((HERE/'verified-refinement.json').read_text())
    states = ([('subatomic',s) for s in subatomic.SUPPORTED_SYMBOLS]
              + [('element',s) for s in epac_atomic.SYMBOLS]
              + [('molecule',s) for s in molecular.MOLECULE_COMPOSITIONS])
    return {
        'schema':'epac.external.expansion-plan.v1',
        'release_commit':'949cb1cb304927942966c9fb396caf6227120e7f',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'prior_results_sha256':hashlib.sha256((HERE/'verified-refinement.json').read_bytes()).hexdigest(),
        'states': states, 'state_count':len(states), 'pair_count':len(states)*(len(states)-1)//2,
        'new_states':[s+':'+n for s,n in states if s+':'+n not in prior['observer_values']],
        'frozen_candidates':prior['unrestricted_field_search']['minimum_sets'],
        'identity_target':'each declared scale/symbol-or-formula state; occurrences are fixed at zero',
        'failure_rule':'any distinct states with equal candidate descriptor falsify expanded identity sufficiency',
        'post_failure_search_pool':sorted(next(iter(prior['observer_values'].values()))),
        'composition_operation':'construct_public_gonol with one source gonol participant; same source_id, relation, occurrence, glyph, carried options and couplings',
        'composition_readout':'retained participant intrinsic fields and identity-excluded structure; digests are never the behavioral discriminator',
        'composition_failure_rule':'equal input candidate but different post-construction named readout falsifies sufficiency for that composed readout',
        'vacuity_rule':'no nontrivial equal-descriptor inputs means substitution sufficiency UNRESOLVED',
        'physical_target':'repository molecular known_shape equivalence classes',
        'physical_mapping':'candidate descriptor equality predicts equal repository shape; inequivalence predicts unequal shape',
        'physical_failure_rule':'any same-shape split or different-shape merge falsifies exact shape-equivalence prediction',
        'physical_evidence_scope':'retrospective comparison on previously exposed repository labels; NOT held-out validation or independent experimental evidence',
        'fresh_physical_validation':'UNRESOLVED: no new independent outcomes or calibrated physical mapping selected',
    }


def observe(gonol, scale, b=None):
    atoms = gonol.participants if scale=='molecule' else (gonol,)
    row={n:tuple(sorted((dict(a.carried_options)[n] for a in atoms),key=key)) for n in FIELDS}
    row.update({n:freeze(f({'structure':gonol.structure})) for n,f in probes.OMITTED_OBSERVABLES.items()})
    if b is not None:
        row['B']=tuple(b)
    return row


def run(config):
    assert freeze(config)==freeze(plan()), 'Plan, script or inputs changed since freezing'
    prior=json.loads((HERE/'verified-refinement.json').read_text())
    rows, receipts, constructions, executions={},{},{},[]
    for i,(scale,name) in enumerate(config['states'],1):
        sid=scale+':'+name
        print(f'construct {i}/{len(config["states"])} {sid}',flush=True)
        if scale=='subatomic':
            receipt=subatomic.construct_subatomic_gonol(name)
            b=subatomic.boundary_capacity_from_subatomic_receipt(receipt)
        elif scale=='element':
            receipt=periodic.construct_element_gonol(name)
            b=periodic.boundary_capacity_from_element_receipt(receipt)
        else:
            construction=molecular.construct_molecule(name)
            constructions[name]=construction
            receipt=construction.receipt
            b=molecular.boundary_capacity_carried_on_molecule(construction)
        rows[sid]=observe(receipt.gonol,scale,b)
        receipts[sid]=receipt
        executions.append({'state':sid,'status':'SURVIVED'})
    for sid,old in prior['observer_values'].items():
        assert freeze(old)==freeze(rows[sid]), 'Frozen baseline drift: '+sid
    pairs=list(itertools.combinations(sorted(rows),2))
    candidates=[]
    all_collisions=set()
    for candidate in config['frozen_candidates']:
        collisions=[(a,b) for a,b in pairs if all(rows[a][n]==rows[b][n] for n in candidate)]
        all_collisions.update(collisions)
        candidates.append({'fields':candidate,'collisions':collisions,
                           'status':'FALSIFIED' if collisions else 'SURVIVED'})
    print('All states built; executing matched-parameter composition on collision witnesses',flush=True)
    parents={}
    for sid in sorted({s for pair in all_collisions for s in pair}):
        parent=construct_public_gonol(source_id='epac.audit.expansion.parent',
            relation='epac.audit.singleton-composition', participants=(receipts[sid].gonol,))
        replayed=replay_public_gonol(parent)
        assert replayed.receipt_digest==parent.receipt_digest
        # Observe the actual retained child after composition, not the input.
        parents[sid]={'readout':observe(parent.gonol.participants[0],sid.split(':')[0]),
                      'receipt_digest':parent.receipt_digest, 'replay':'SURVIVED'}
    for record in candidates:
        witnesses=[]
        for a,b in record['collisions']:
            left,right=parents[a]['readout'],parents[b]['readout']
            diff={n:{'left':left[n],'right':right[n]} for n in left if left[n]!=right[n]}
            witnesses.append({'left':a,'right':b,'post_composition_differences':diff})
        record['composition']={'matched_parameter_witnesses':witnesses,
            'status':'FALSIFIED' if any(w['post_composition_differences'] for w in witnesses) else 'UNRESOLVED',
            'candidate_output_status':'SURVIVED' if witnesses and all(
                all(parents[a]['readout'][n]==parents[b]['readout'][n] for n in record['fields'])
                for a,b in record['collisions']) else 'UNRESOLVED',
            'scope':'parent-retained child field behavior; not a derived molecular or physical law'}
    composition=[]
    for s in epac_atomic.SYMBOLS:
        for f in FIELDS:
            composition.append({'edge':f'subatomic:{s}->element:{s}','field':f,
                'status':'SURVIVED' if rows['subatomic:'+s][f]==rows['element:'+s][f] else 'FALSIFIED'})
    for formula,comp in molecular.MOLECULE_COMPOSITIONS.items():
        for f in FIELDS:
            expected=tuple(sorted((v for symbol,count in comp for _ in range(count)
                for v in rows['element:'+symbol][f]),key=key))
            composition.append({'edge':formula,'field':f,
                'status':'SURVIVED' if rows['molecule:'+formula][f]==expected else 'FALSIFIED'})
    print('Scoring fixed shape-equivalence mapping on previously exposed repository labels',flush=True)
    sealed=Path(molecular.__file__).parent/'data/sealed_known_molecular_geometry.json'
    shapes={k:v['known_shape'] for k,v in json.loads(sealed.read_text())['molecules'].items()}
    shape_rows=[]
    for candidate in config['frozen_candidates']:
        mismatches=[]
        for a,b in itertools.combinations(sorted(constructions),2):
            descriptor_equal=all(rows['molecule:'+a][n]==rows['molecule:'+b][n] for n in candidate)
            label_equal=shapes[a]==shapes[b]
            if descriptor_equal!=label_equal:
                mismatches.append({'left':a,'right':b,'left_label':shapes[a],'right_label':shapes[b],
                    'descriptor_equal':descriptor_equal,'failure':'same-shape split' if label_equal else 'different-shape merge'})
        shape_rows.append({'fields':candidate,'compared_pairs':36,'mismatches':mismatches,
            'status':'FALSIFIED' if mismatches else 'SURVIVED'})
    print('Searching preregistered observer pool on expanded domain',flush=True)
    return {'schema':'epac.external.expansion-results.v1','plan':config,
        'state_count':len(rows),'pair_count':len(pairs),'execution':executions,
        'observer_values':rows,'frozen_baseline_reproduction':'SURVIVED',
        'frozen_candidate_results':candidates,'parents':parents,
        'expanded_minimum_search':search(rows),
        'retained_field_composition':composition,
        'shape_comparison':{'sealed_sha256':hashlib.sha256(sealed.read_bytes()).hexdigest(),
            'scope':config['physical_evidence_scope'],'candidates':shape_rows},
        'global_sufficiency':'UNRESOLVED','canonicality':'UNRESOLVED',
        'fresh_physical_validation':config['fresh_physical_validation']}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--plan'); g.add_argument('--run')
    p.add_argument('--output')
    args=p.parse_args()
    if args.plan:
        result=plan(); write(args.plan,result)
        print('Plan frozen:',result['state_count'],'states;',len(result['new_states']),'new;',result['pair_count'],'pairs')
    else:
        if not args.output: p.error('--output required with --run')
        result=run(json.loads(Path(args.run).read_text()))
        write(args.output,result)
        print('Completed',result['state_count'],'states,',result['pair_count'],'pairs')
        print('Minimum pairs', result['expanded_minimum_search']['minimum_sets'])
