# Boundary Capacity Principle — Survival within EPAC Construction

Status (internal to EPAC): **construction result for the present molecule-level
surface**.

The boundary-capacity principle SURVIVED within the present EPAC molecule-level
construction.

With interior modes fixed, boundary dimensionality and coupling capacity distinguish composite states; bare projections revert to the control-like partition.

It preserves the existing molecular-shape falsification and makes no external physics/chemistry claim.

EPAC already explicitly separates internal research constructions from external truth claims.

## Canonical Descriptor

\[
B(R) = (3,\ d_{\partial},\ c_{\partial})
\]

The leading 3 is the fixed interior mode count (canonical two-turn double cover with constant visible phase) for every closed gonol in this construction.

- \(d_{\partial}\): boundary dimensionality (count of participant axes declared for the configuration).
- \(c_{\partial}\): boundary coupling capacity (count of valence attachment slots).

## Survival Summary (internal to this construction)

- Interior modes held fixed at 3.
- On the frozen ORIGINAL_PREREG set (H₂, H₂O, NH₃, CH₄, CO₂), the molecule view of boundary capacity (sourced from carried lifted-spiral facts that include declared attachments) yields distinct classes that do not match the known-shape partition and do not match the stoichiometric control partition.
- Bare projections (periodic element gonols and subatomic gonols, both carrying attachment capacity 0) produce control-like partitions under the quantify surfaces (exact match to control on the known-side evaluation for those views).
- Prior falsifications (charged structure, topology, harmonic survival, lifted spiral) of sealed molecular shape prediction on the prereg set remain unchanged. Boundary capacity is an additional first-class internal descriptor family derived from already-present carried facts.

Observed B values on ORIGINAL_PREREG (molecule view, after construction):

- H₂:  (3, 2, 2)
- H₂O: (3, 3, 2)
- NH₃: (3, 4, 3)
- CH₄: (3, 5, 4)
- CO₂: (3, 3, 4)

On the full declared 9-formula surface the molecule boundary_capacity family partitions into 5 classes.

## Explicit Non-Claims

- No external physics, chemistry, or laboratory claim.
- No assertion that B(R) will continue to distinguish under different preregistrations, different Z ranges, or different construction rules.
- No mapping is performed here from boundary_dim or coupling_capacity onto any UCNS continuum or gonal quantity (modulus, covering degree, etc.).
- The separation of internal EPAC research constructions from external truth claims is maintained.

## Relation to Next Research Step

Canon is the floor we can now stand on, not a lid on the laboratory.

The immediate next bounded maximal research step (recorded separately) moves beyond final-state classification to recording actual valid EPAC construction transformations R₀ → R₁ together with the corresponding B(R₀) → B(R₁), then testing whether the change is reproducible from the source state plus the declared coupling operation alone, without inspecting the finished target receipt or any known empirical label.

No monotonicity, conservation rule, or composition formula is assumed in advance. The test distinguishes whether boundary capacity functions only as a useful final-state descriptor or begins to exhibit lawful transformation structure as an EPAC state variable.

## Provenance and Reproducibility

- Pure projection from the carried "lifted-spiral" facts (molecule, element, subatomic) that predate this work.
- All known-side metrics, standings, and quantify respect the frozen ORIGINAL_PREREG policy.
- Verification is now split between the molecule-level comparison tests and the
  cross-scale closure tests. The previous `subatomic_lifted_spiral_matches_control`
  false expectation has been classified as a stale control assertion on the
  current nine-formula surface, not as a boundary-compositionality counterexample.

## Compositional Transition Closure (stronger internal result)

The boundary-capacity descriptor \(B(R)=(3,d_{\partial},c_{\partial})\) was further tested under strictly local affixation steps only:

- Each step supplies only its local information: introduce a named atom instance (+1 to \(d_{\partial}\)) or affix one ligand using solely that ligand's ground-state unpaired valence count (+K to \(c_{\partial}\)).
- Valid paths are all orderings of the introduce steps followed by all orderings of the affix steps.
- For every declared formula (including the frozen ORIGINAL_PREREG set), across every valid path:
  - Final \(B\) is path-independent.
  - Identical local steps are reproducible (same delta regardless of history).
  - \(B\) accumulated from the local steps exactly equals the \(B\) carried on the closed molecule receipt.
  - \(B\) is sufficient for deciding the effect of each admissible local operation (no additional coordinate required for these steps).

Compositional closure holds for all 9 formulas. This strengthens the claim inside the construction: \(B\) functions as a closed transition variable under local steps for this class, not merely a descriptor recoverable from global operation totals.

The UCNS/PCEA mapping remains downstream. No assignment of \(d_{\partial}\) or \(c_{\partial}\) to continuum/gonal quantities has been performed.

Provenance for this stronger molecule-level result lives in
`tests/test_geometry_comparison_after_construction.py`; cross-scale provenance
is recorded separately in `tests/test_cross_scale_compositional_closure.py`.

This remains an internal EPAC construction result only. No external physics or chemistry claim.

hmmm: a receipt can tell you where you arrived; the odometer (local steps) gets you there without reading the destination sign.

This document is part of the EPAC research record inside the placeholder. It is not an org-wide external claim.

## Cross-Scale Addendum

The bounded cross-scale audit is recorded in
[`cross_scale_compositional_closure.md`](cross_scale_compositional_closure.md).
It leaves the locked nine-formula molecular closure unchanged and tests the
implemented internal stack from subatomic sources through periodic element
states and molecule formation.

Aggregate statuses from `epac_cross_scale_closure.py`:

- subatomic_to_element_closure: SURVIVED
- element_state_compatibility: SURVIVED
- end_to_end_subatomic_to_molecule_closure: SURVIVED
- boundary_capacity_compositionality: SURVIVED

The cross-scale result depends on two explicit scale-local rules: subatomic
shell axes refine into periodic electron axes at element scale, and closed
element gonols project as atom axes at molecule scale. It does not claim a
continuum theorem, external physical validation, PCEA mapping, or runtime
channel encoding.

## Non-Degeneracy Addendum

The bounded first-order non-degeneracy audit is recorded in
[`boundary_descriptor_nondegeneracy.md`](boundary_descriptor_nondegeneracy.md).
It freezes the current subatomic, element, and locked nine-formula molecule
surface, then applies label/order invariance controls, implemented
equivalent-path controls, positive `d_boundary` and `c_boundary` sensitivity
controls, non-singleton partition controls, and a same-`B` collision search.

Aggregate statuses from `epac_boundary_nondegeneracy.py`:

- label_invariance: SURVIVED
- equivalent_path_invariance: SURVIVED
- d_boundary_sensitivity: SURVIVED
- c_boundary_sensitivity: SURVIVED
- non_singleton_control_discrimination: SURVIVED
- descriptor_collision_search: SURVIVED
- boundary_descriptor_non_degeneracy: SURVIVED

The result certifies that `B=(3,d_boundary,c_boundary)` carries structural
information beyond labels, operation order, raw bulk count, and the prior
singleton-partition accident over the bounded first-order neighborhood. It does
not claim complete boundary-incidence topology discrimination.

## Quotient Addendum

The boundary-capacity quotient audit is recorded in
[`boundary_capacity_quotient.md`](boundary_capacity_quotient.md). It compares
two equivalence relations over the frozen EPAC states:

- equality of `B(R)`;
- equality of every presently admissible boundary-capacity probe response.

Aggregate statuses from `epac_boundary_quotient.py`:

- probe_inventory: SURVIVED
- boundary_capacity_equivalence_relation: SURVIVED
- B_matches_boundary_capacity_quotient: SURVIVED
- state_sufficiency: FALSIFIED
- incidence_completeness: UNRESOLVED
- topology_completeness: UNRESOLVED

This sharpens the claim. `B` is a complete descriptor of the current
boundary-capacity quotient, not a complete EPAC state descriptor. Same-`B`
collisions such as `subatomic:H` versus `element:H`, `H2O` versus `H2S`,
`BF3` versus `NH3` versus `PH3`, and `CH4` versus `SiH4` remain state-level
collisions.

## Probe-Completeness Addendum

The boundary-probe completeness audit is recorded in
[`boundary_probe_completeness.md`](boundary_probe_completeness.md). It audits
whether the quotient probe inventory covers every already-declared EPAC
operation whose outcome can depend on boundary incidence, attachment
availability, coupling structure, or boundary state.

Aggregate statuses from `epac_boundary_probe_completeness.py`:

- declared_operation_inventory: SURVIVED
- ambiguous_boundary_semantics: SURVIVED
- omitted_boundary_relevant_operations: FALSIFIED
- quotient_partition_stability_under_omitted_existing_observables: FALSIFIED
- boundary_probe_completeness: FALSIFIED

The audit classified 104 exported callable operations and found 14 omitted
boundary-relevant operations. Existing dimensional-arity observers such as
`topology_structure_readout`, `charged_structure_readout`, and
`quaternion_structure_readout` refine the 16-class B quotient to 21 classes
with identifiers and labels excluded. The quotient result therefore remains
valid only for the narrower count-valued probe inventory; it is not complete
for the full presently declared EPAC operational surface.

## Minimal-Refinement Addendum

The boundary minimal-refinement audit is recorded in
[`boundary_minimal_refinement.md`](boundary_minimal_refinement.md). It searches
only the 13 omitted observables that already distinguished same-`B` frozen
states in the probe-completeness audit.

Aggregate statuses from `epac_boundary_minimal_refinement.py`:

- minimal_refinement_size: SURVIVED
- all_minimal_equivalent_sets: SURVIVED
- intrinsic_boundary_semantics: SURVIVED
- history_or_label_encoding: SURVIVED
- canonicality: UNRESOLVED
- compositionality: UNRESOLVED
- refined_quotient_class_count: SURVIVED
- descriptor_sufficiency: UNRESOLVED
- pcea_mapping: BLOCKED

The minimal subset size is `1`, but it is not unique. Eight singleton
observables independently reproduce the 21-class partition:
`charged_structure_readout`, `quaternion_structure_readout`,
`geometry_from_declared_couplings`, `structure_from_charged_couplings`,
`degree_relations`, `oriented_instance_couplings`,
`quaternion_of_local_three`, and `quaternions_from_declared_couplings`.
No singleton is promoted as canonical because EPAC has not declared a semantic
priority rule or a cross-scale aggregation law for a refined structural
descriptor component.

## Descriptor Sufficiency / Collision Falsifier (bounded maximal step)

Preregistered exhaustive EPAC-local sweep over the declared source states and
operations, restricted to the frozen nine locked formulas. B(R) computed
exclusively from locked receipt projections and local apply rules. States
grouped by identical B(R). Collisions tested for operational equivalence
under the EPAC replay/transition contract (identical receipt digests or
identical construction invariants + control signature). Bare and control
views included. No new coordinate invented.

Result (sealed):

- Enumerated B-carrying states: 27 (9 bare subatomic + 9 bare element + 9 locked molecules).
- Collisions: 6.
  - (3, 2, 0): subatomic:H, element:H (FALSIFIED — distinct bare views of same symbol)
  - (3, 3, 0): subatomic:O/N/C/B/F (FALSIFIED — multiple bare subatomic symbols share shell axis count)
  - (3, 4, 0): subatomic:S/P/Si (FALSIFIED)
  - (3, 3, 2): molecule:H2O, molecule:H2S (FALSIFIED — distinct formulas, same d and total attachment slots)
  - (3, 4, 3): molecule:BF3, molecule:NH3, molecule:PH3 (FALSIFIED)
  - (3, 5, 4): molecule:CH4, molecule:SiH4 (FALSIFIED)
- Aggregate:
  - boundary_capacity_sufficiency: FALSIFIED
  - subatomic_to_element_closure: SURVIVED (cross-scale ledger)
  - end_to_end_subatomic_to_molecule_closure: SURVIVED (locked compositional closure)
  - boundary_capacity_compositionality: FALSIFIED (sufficiency fails)
- Control failure disposition (subatomic_lifted_spiral_matches_control): classified
  as stale_or_incorrect_control_assertion. Both bare subatomic lifted-spiral
  and stoichiometric control partition the nine formulas into nine singletons.
  The flag is a partition-resemblance fact on bare projections; it is not a
  direct/composed boundary-capacity transition invariant and does not falsify
  the transition results. impacts_b_sufficiency: false.

Per-element provenance/closure ledger and per-formula end-to-end closure
remain as recorded in the cross-scale and compositional closure sections
(SURVIVED where previously established).

The descriptor is closed under the admissible local steps for the locked
surface but does not separate all distinct reachable construction states.
The collisions themselves record the information the present B(R) misses
under the current EPAC rules (primarily bare-layer symbol sharing of axis
counts, and molecule-layer formulas that happen to declare the same total
attachment capacity after the same number of atom instances).

This is an internal EPAC construction result. No external claim. The nine
locked formulas and all direct carried B values remain untouched.

hmmm: a map that never loses anything may be the territory wearing a fake mustache.
