# EPAC Boundary Minimal-Refinement Audit

Status: internal EPAC evidence result for the presently implemented frozen
state surface.

Preregistered question:

> What is the minimal refinement of `B=(3,d_boundary,c_boundary)` required to
> reproduce the full 21-class partition exposed by the boundary-probe
> completeness audit?

Decision: **UNRESOLVED** for canonical descriptor promotion.

The finite partition result is stronger:

- minimal refinement size: `1`
- full refined quotient class count: `21`
- singleton refinements reproducing the full partition: `8`
- minimum unique: `false`

## Scope

The audit uses only the 13 existing omitted observables that the
probe-completeness audit already found to distinguish same-`B` frozen states.
It does not add a new operation, probe, coordinate, descriptor component,
PCEA mapping, UCNS claim, runtime encoding, or external physics assertion.

The surface remains the same 27 frozen states:

- 9 subatomic states
- 9 element states
- 9 locked molecule states

## Minimal Sets

Each of these singleton sets reproduces the full 21-class partition:

| minimal set | class count | intrinsic boundary semantics |
|---|---:|---|
| `charged_structure_readout` | 21 | yes |
| `quaternion_structure_readout` | 21 | yes |
| `geometry_from_declared_couplings` | 21 | yes |
| `structure_from_charged_couplings` | 21 | yes |
| `degree_relations` | 21 | yes |
| `oriented_instance_couplings` | 21 | yes |
| `quaternion_of_local_three` | 21 | yes |
| `quaternions_from_declared_couplings` | 21 | yes |

The remaining distinguishing observables are not minimal singleton
refinements for this partition:

| singleton | class count |
|---|---:|
| `topology_structure_readout` | 17 |
| `local_three_structures` | 17 |
| `has_declared_coupling` | 17 |
| `instances_missing_oriented_hub_coupling` | 17 |
| `require_every_instance_has_oriented_hub_coupling` | 17 |

## Canonicality

Canonicality is **UNRESOLVED**.

Minimality does not select a unique semantic representative. The surviving
singletons include charge/degree structure, quaternion representations,
oriented instance-coupling views, and aggregate geometry envelopes. Current
EPAC canon does not state which of those should become the canonical refined
descriptor component.

## Compositionality

Local reproducibility from each frozen state's existing boundary structure:
**SURVIVED**.

Cross-scale compositionality as a promoted descriptor component:
**UNRESOLVED**.

The existing cross-scale closure derives and carries `B`; it does not yet
declare a local aggregation law carrying any one of these structural readouts
from subatomic source through element refinement and molecule affixiation.

## Label And History Exclusion

For the minimal singleton candidates, normalized observables exclude source
ids, state labels, concrete axis names, coupling ids, receipt digests,
constructor ids, and construction-history markers.

No minimal candidate is classified as merely encoding labels or construction
history.

## Status Matrix

| item | status |
|---|---|
| minimal_refinement_size | SURVIVED |
| all_minimal_equivalent_sets | SURVIVED |
| intrinsic_boundary_semantics | SURVIVED |
| history_or_label_encoding | SURVIVED |
| canonicality | UNRESOLVED |
| compositionality | UNRESOLVED |
| refined_quotient_class_count | SURVIVED |
| descriptor_sufficiency | UNRESOLVED |
| pcea_mapping | BLOCKED |

## Interpretation

`B` is still not modified. Adding all omitted observables by default would be
unjustified. The finite 21-class quotient can be reproduced with one existing
structural observable, but EPAC has not yet selected a canonical observable or
proved that any candidate composes across the full subatomic -> element ->
molecule path.

PCEA mapping remains blocked until canonicality and compositionality close.

Verification command:

```bash
PYTHONPATH="research/epac:research/epac/subatomic:libs/ucns/src" python3 -m unittest research/epac/tests/test_boundary_minimal_refinement.py -q
```
