# EPAC Boundary-Capacity Quotient

Status: internal EPAC evidence result for the presently implemented frozen
state surface.

Preregistered decision:

> Among the frozen EPAC states, does equality of `B(R)` coincide exactly with
> equality of the presently defined boundary-capacity behavior, independent of
> internal identity, incidence, and topology?

Decision: **SURVIVED** for the current probe inventory.

Follow-on audit: the boundary-probe completeness audit later FALSIFIED
promotion of this result to the full presently declared EPAC operational
surface. See
[`boundary_probe_completeness.md`](boundary_probe_completeness.md). The
SURVIVED result in this file is therefore probe-inventory-relative.

## Scope

The audit compares only the frozen EPAC states already used by the
non-degeneracy audit:

- 9 subatomic states: `H`, `O`, `N`, `C`, `S`, `B`, `F`, `P`, `Si`
- 9 element states: `H`, `O`, `N`, `C`, `S`, `B`, `F`, `P`, `Si`
- 9 molecule states: `H2`, `H2O`, `NH3`, `CH4`, `CO2`, `H2S`, `BF3`,
  `PH3`, `SiH4`

Frozen state count: `27`.

## Equivalence Relation

`R1 ==boundary R2` iff every presently admissible boundary-capacity probe has
the same admissibility and B-valued response for `R1` and `R2`.

The probe inventory is count-valued and intentionally narrow:

- observe `B`
- relabel
- reorder
- add boundary axis
- delete boundary axis
- duplicate participant as a boundary-axis perturbation
- add coupling
- delete coupling
- rewire coupling at the same count
- hierarchy/refinement perturbation where the existing non-degeneracy audit
  already generates it

The signature omits state id, scale, source, labels, concrete axis names,
concrete coupling-slot identities, incidence signatures, and topology.

## Result

| item | result |
|---|---:|
| frozen states | 27 |
| B classes | 16 |
| boundary-capacity behavior classes | 16 |
| equal-B frozen state pairs | 19 |
| equal-B probe mismatches | 0 |
| unequal-B behavior-equivalent pairs | 0 |
| state-sufficiency collision groups | 6 |

Equality of `B` exactly matches equality of the present boundary-capacity
behavior quotient. This is the narrow result earned by the audit.

## Preserved Falsification

`B` remains FALSIFIED as a complete state descriptor. These same-B frozen-state
collisions remain live:

- `subatomic:H` and `element:H`
- `subatomic:B`, `subatomic:C`, `subatomic:F`, `subatomic:N`, `subatomic:O`
- `subatomic:P`, `subatomic:S`, `subatomic:Si`
- `molecule:H2O` and `molecule:H2S`
- `molecule:BF3`, `molecule:NH3`, `molecule:PH3`
- `molecule:CH4` and `molecule:SiH4`

The quotient result does not erase those collisions. It says only that the
current boundary-capacity probes cannot observe a boundary-capacity distinction
inside those same-`B` classes.

## Aggregate Status

| item | status |
|---|---|
| probe_inventory | SURVIVED |
| boundary_capacity_equivalence_relation | SURVIVED |
| B_matches_boundary_capacity_quotient | SURVIVED |
| state_sufficiency | FALSIFIED |
| incidence_completeness | UNRESOLVED |
| topology_completeness | UNRESOLVED |

## Requires More

- Future boundary-capacity probes may refine the quotient.
- State identity, incidence signatures, and topology remain outside `B`.
- `B` should not be promoted as a complete EPAC state descriptor.
- Existing coupling-structure observers already refine the quotient when the
  audit scope is widened beyond the count-valued probe inventory.
- No PCEA mapping, UCNS continuum theorem, runtime encoding, or external
  physical claim is made.

Verification command:

```bash
PYTHONPATH="research/epac:research/epac/subatomic:libs/ucns/src" python3 -m unittest research/epac/tests/test_boundary_capacity_quotient.py -q
```
