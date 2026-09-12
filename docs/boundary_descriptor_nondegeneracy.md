# EPAC Boundary-Descriptor Non-Degeneracy

Status: internal EPAC evidence result for the presently implemented stack.

Decision: **SURVIVED** for the bounded first-order control neighborhood built
around the current subatomic, element, and locked nine-formula molecule surface.

This report preserves the locked cross-scale closure and nine molecular
formulas. It does not inspect UCNS internals, import PCEA, define a continuum
theorem, make an external physics/chemistry claim, or define a runtime channel
encoding.

## Frozen Surface

The audit freezes the current construction surface before generating controls:

- subatomic states: `H`, `O`, `N`, `C`, `S`, `B`, `F`, `P`, `Si`
- element states: `H`, `O`, `N`, `C`, `S`, `B`, `F`, `P`, `Si`
- molecule states: `H2`, `H2O`, `NH3`, `CH4`, `CO2`, `H2S`, `BF3`, `PH3`, `SiH4`

Frozen state count: `27`.

Control neighborhood size: `170` first-order mutations.

## Descriptor

`B(R) = (3, d_boundary, c_boundary)`

- `3`: fixed interior mode count carried by the implemented EPAC receipts.
- `d_boundary`: count of boundary axes at the state scale.
- `c_boundary`: count of declared coupling slots.

The audit does not extend `B`. Incidence topology beyond these counts is
recorded only for collision classification.

## Controls

| control family | status | evidence |
|---|---|---|
| label invariance | SURVIVED | relabel and reorder controls preserve `B` for every frozen state |
| equivalent-path invariance | SURVIVED | existing cross-scale admissible paths remain path-independent |
| d_boundary sensitivity | SURVIVED | axis addition, deletion, participant duplication, and hierarchy/refinement perturbation change only `d_boundary` as declared |
| c_boundary sensitivity | SURVIVED | coupling addition/deletion changes only `c_boundary`; same-count rewiring is coarse-equivalent by descriptor semantics |
| non-singleton control discrimination | SURVIVED | at least one non-singleton bulk-count group is split by `B` |
| descriptor collision search | SURVIVED | all bounded same-`B` collisions are classified; no required boundary-distinct control receives the parent `B` |

## Non-Singleton Evidence

The old singleton-partition equality remains explicitly retained as a
non-evidentiary warning. On the current nine-formula surface, the bare
subatomic lifted-spiral projection and the stoichiometric control both partition
into singleton classes, so their equality is degenerate and not evidence for
boundary capacity.

The non-degeneracy audit adds non-singleton controls. For example, the
bulk-count group `CO2`, `H2O`, `H2S` is split by `B`:

- `CO2`: `(3, 3, 4)`
- `H2O`: `(3, 3, 2)`
- `H2S`: `(3, 3, 2)`

This proves `B` is not merely reproducing bulk participant count. It also shows
the descriptor is intentionally coarse: `H2O` and `H2S` still share `B` under
the present descriptor.

## Collision Classification

The bounded same-`B` collision search found only classified collisions:

- declared invariance or same-count controls, such as relabel, reorder, and
  same-count rewire controls;
- intentionally coarse equivalence classes, such as states with different
  incidence signatures that share the same three component counts.

No collision was found between a parent and a control that the declared
operation required to be boundary-distinct.

This SURVIVED result is not a descriptor-sufficiency theorem. It certifies that
`B` carries structural information beyond labels, operation order, bulk count,
and singleton partition accidents over the bounded first-order neighborhood.
It does not claim `B` fully determines boundary incidence topology.

The quotient defined by the current boundary-capacity probes is recorded in
[`boundary_capacity_quotient.md`](boundary_capacity_quotient.md). That follow-on
audit keeps the distinction explicit: `B` survives as a descriptor of the
boundary-capacity quotient, while state sufficiency remains falsified.

## Aggregate Status

| item | status |
|---|---|
| label_invariance | SURVIVED |
| equivalent_path_invariance | SURVIVED |
| d_boundary_sensitivity | SURVIVED |
| c_boundary_sensitivity | SURVIVED |
| non_singleton_control_discrimination | SURVIVED |
| descriptor_collision_search | SURVIVED |
| boundary_descriptor_non_degeneracy | SURVIVED |

## Requires More

- A richer observable would be required before claiming complete incidence
  topology discrimination.
- Future alternate construction paths must be added to this audit before
  claiming invariance over them.
- No PCEA mapping, UCNS continuum theorem, runtime channel encoding, or external
  physical interpretation is provided here.

Verification command:

```bash
PYTHONPATH="research/epac:research/epac/subatomic:libs/ucns/src" python3 -m unittest research/epac/tests/test_boundary_descriptor_nondegeneracy.py -q
```
