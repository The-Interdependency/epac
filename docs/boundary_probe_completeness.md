# EPAC Boundary-Probe Completeness Audit

Status: internal EPAC evidence result for the presently implemented frozen
state surface.

Preregistered question:

> Does the current boundary-capacity probe inventory include every
> already-declared EPAC operation whose outcome can depend on boundary
> incidence, attachment availability, coupling structure, or boundary state?

Decision: **FALSIFIED**.

## Scope

The audit stays inside the 27 frozen states used by the quotient audit:

- 9 subatomic states
- 9 element states
- 9 locked molecule states

No new probe, coordinate, descriptor component, operation, physics claim, UCNS
continuum result, PCEA mapping, or runtime encoding is introduced.

The operation inventory covers exported callables from the bounded EPAC
construction/evidence modules. Each operation is classified as one of:

- boundary-observing
- boundary-transforming
- provenance/identity only
- internal/non-boundary
- ambiguous

## Inventory Result

| item | count |
|---|---:|
| declared operations classified | 104 |
| boundary-relevant operations | 59 |
| omitted boundary-relevant operations | 14 |
| omitted operations that distinguish same-B frozen states | 13 |
| ambiguous operations | 0 |

## Partition Result

The prior quotient audit had:

- baseline B classes: `16`
- equal-B frozen state pairs: `19`
- state-sufficiency collision groups: `6`

Adding omitted existing structural observables changes the partition:

- combined augmented class count: `21`
- quotient partition changes: `true`

Therefore the current boundary-capacity probe inventory is not complete for the
full presently declared EPAC operational surface.

## Omitted Existing Observables

The decisive omissions are already-declared dimensional-arity operations. The
audit evaluates them with source ids, labels, concrete axis names, and coupling
ids excluded as discriminators.

Examples:

- `topology_structure_readout` refines the quotient from 16 to 17 classes by
  distinguishing `subatomic:H` from `element:H` through coupling-structure
  presence, not through labels.
- `charged_structure_readout` refines the quotient from 16 to 21 classes by
  distinguishing same-B molecule groups through existing slot-charge and degree
  structure.
- `quaternion_structure_readout` also refines the quotient from 16 to 21
  classes through existing quaternion component structure.

Other omitted structural operations with quotient-refining effects include
`degree_relations`, `geometry_from_declared_couplings`,
`structure_from_charged_couplings`, `oriented_instance_couplings`,
`local_three_structures`, `quaternion_of_local_three`,
`quaternions_from_declared_couplings`, `has_declared_coupling`,
`instances_missing_oriented_hub_coupling`, and
`require_every_instance_has_oriented_hub_coupling`.

## Status Matrix

| item | status |
|---|---|
| declared_operation_inventory | SURVIVED |
| ambiguous_boundary_semantics | SURVIVED |
| omitted_boundary_relevant_operations | FALSIFIED |
| quotient_partition_stability_under_omitted_existing_observables | FALSIFIED |
| boundary_probe_completeness | FALSIFIED |

## Interpretation

The earlier quotient result remains valid only relative to its narrower
count-valued probe inventory. It does not survive promotion to the full
presently declared EPAC operational surface, because EPAC already has
coupling-structure observers that see distinctions B does not encode.

This does not require adding anything to `B=(3,d_boundary,c_boundary)`. It
reduces the claim:

- `B` remains compositional, path-independent, label-invariant, sensitive, and
  non-degenerate for the bounded boundary-capacity controls.
- `B` remains a descriptor of the previously defined count-valued
  boundary-capacity quotient.
- `B` is not complete for all declared EPAC boundary-relevant operations.
- state sufficiency remains FALSIFIED.
- incidence/topology completeness remains outside `B`.

Verification command:

```bash
PYTHONPATH="research/epac:research/epac/subatomic:libs/ucns/src" python3 -m unittest research/epac/tests/test_boundary_probe_completeness.py -q
```

## Follow-On Minimal Refinement

The minimal-refinement audit is recorded in
[`boundary_minimal_refinement.md`](boundary_minimal_refinement.md). It finds
that the 21-class partition can be reproduced by a singleton existing
structural observable, but the minimum is not unique: eight singleton
observables reproduce the same finite partition. Descriptor promotion remains
UNRESOLVED because EPAC has not selected a canonical semantic representative or
declared a cross-scale aggregation law for the refined structural observable.
