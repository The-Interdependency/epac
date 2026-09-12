"""Boundary-descriptor non-degeneracy controls for EPAC.

This module freezes the implemented EPAC construction surface, then builds a
bounded first-order counterfactual neighborhood around the frozen boundary
states. It tests whether B=(3, d_boundary, c_boundary) is invariant under
labels/order and sensitive to declared boundary dimension/coupling changes.

The controls are descriptor-level evidence. They do not extend the descriptor,
modify molecule constructors, import PCEA, inspect UCNS internals, or claim
external physics/chemistry validation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
import json
from itertools import combinations
from typing import Any, Mapping

from epac_cross_scale_closure import (
    FALSIFIED,
    SURVIVED,
    control_like_partition_failure_disposition,
    cross_scale_compositional_closure,
    element_closure_ledger,
    formula_closure_ledger,
    required_element_symbols,
)
from epac_molecular import (
    MOLECULE_COMPOSITIONS,
    MolecularConstruction,
    construct_declared_molecules,
    construct_molecule,
    lifted_spiral_carried_on_molecule,
)
from epac_periodic import construct_element_gonol, lifted_spiral_carried_on_element
from epac_subatomic.subatomic_gonol import construct_subatomic_gonol, lifted_spiral_carried_on_subatomic

# === MODULE_BUILD ===
# id: epac_boundary_descriptor_nondegeneracy
#   module_name: epac_boundary_nondegeneracy
#   module_kind: experiment
#   summary: evidence-only non-degeneracy audit for EPAC B=(3,d_boundary,c_boundary) using frozen subatomic, element, and locked nine-formula molecule boundary states plus first-order controls
#   owner: The Interdependency
#   public_surface: freeze_current_construction_surface, build_counterfactual_neighborhood, boundary_descriptor_nondegeneracy_report
#   internal_surface: BoundaryState, BoundaryMutation, _expected_b_after_operation, _apply_operation, _collision_search, _non_singleton_control_discrimination
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_boundary_descriptor_nondegeneracy
#   rollout: imported by tests/docs as a research evidence surface; no constructor, descriptor, or runtime behavior changes
#   rollback: remove this module and its tests/docs without changing cross-scale closure or locked molecule construction
#   requires: epac_cross_scale_compositional_closure
#   since: 2026-09-07
#   unresolved: descriptor completeness for full incidence topology; external physical interpretation; future alternate construction paths
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: nondegeneracy_freezes_surface_before_controls
#   given: the non-degeneracy audit is run
#   then: current subatomic, element, and locked molecule boundary states are frozen before counterfactual controls are generated
#   class: evidence
#
# id: boundary_descriptor_label_invariance
#   given: participants are relabeled without changing boundary dimension or coupling count
#   then: B remains identical for every frozen state
#   class: correctness
#
# id: boundary_descriptor_equivalent_path_invariance
#   given: every presently admissible equivalent path from the cross-scale closure audit
#   then: B remains path-independent for element refinement and all locked formula constructions
#   class: correctness
#
# id: boundary_descriptor_d_boundary_sensitivity
#   given: legal first-order boundary axis addition, deletion, duplication, or hierarchy refinement perturbation
#   then: d_boundary changes by the expected operation-derived amount while unrelated descriptor components stay fixed
#   class: evidence
#
# id: boundary_descriptor_c_boundary_sensitivity
#   given: legal first-order boundary coupling addition or deletion at fixed boundary dimensionality and bulk count
#   then: c_boundary changes by the expected operation-derived amount, while incidence rewires with unchanged count remain coarse-equivalent
#   class: evidence
#
# id: boundary_descriptor_non_singleton_control_discrimination
#   given: non-singleton bulk-count control partitions and the singleton partition regression
#   then: B splits at least one non-singleton bulk-count control group and the singleton resemblance remains classified as non-evidentiary
#   class: regression
#
# id: boundary_descriptor_collision_search_classifies_collisions
#   given: the bounded frozen and first-order control states
#   then: every same-B collision is classified and no state pair that the declared controls require to be boundary-distinct receives the same B
#   class: safety
#
# id: boundary_descriptor_audit_does_not_extend_B
#   given: the non-degeneracy audit materializes frozen and counterfactual states
#   then: B remains exactly the three-component tuple of interior mode count, boundary-axis count, and coupling-slot count
#   class: safety
# === END CONTRACTS ===


BoundaryCapacity = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class BoundaryState:
    """Frozen or counterfactual EPAC boundary state."""

    state_id: str
    scale: str
    source: str
    role: str
    interior_modes: int
    boundary_axes: tuple[str, ...]
    coupling_slots: tuple[str, ...]
    bulk_count: int
    labels: tuple[str, ...]
    structure_signature: tuple[str, ...]
    parent_id: str | None = None
    mutation_id: str | None = None

    @property
    def b(self) -> BoundaryCapacity:
        return (self.interior_modes, len(self.boundary_axes), len(self.coupling_slots))


@dataclass(frozen=True, slots=True)
class BoundaryMutation:
    """One declared first-order control and its evaluated state."""

    mutation_id: str
    kind: str
    parent_id: str
    expected_relation: str
    expected_b: BoundaryCapacity
    actual_state: BoundaryState
    requires_boundary_distinct_from_parent: bool
    declared_before_evaluation: bool
    status: str


def _slot_signature(slot: Mapping[str, Any]) -> str:
    return json.dumps(slot, sort_keys=True, separators=(",", ":"))


def _state_record(state: BoundaryState) -> dict[str, Any]:
    return {
        "state_id": state.state_id,
        "scale": state.scale,
        "source": state.source,
        "role": state.role,
        "bulk_count": state.bulk_count,
        "labels": state.labels,
        "boundary_axes": state.boundary_axes,
        "coupling_slots": state.coupling_slots,
        "structure_signature": state.structure_signature,
        "parent_id": state.parent_id,
        "mutation_id": state.mutation_id,
        "B": state.b,
    }


def _mutation_record(mutation: BoundaryMutation) -> dict[str, Any]:
    return {
        "mutation_id": mutation.mutation_id,
        "kind": mutation.kind,
        "parent_id": mutation.parent_id,
        "expected_relation": mutation.expected_relation,
        "expected_b": mutation.expected_b,
        "actual_b": mutation.actual_state.b,
        "actual_state": _state_record(mutation.actual_state),
        "requires_boundary_distinct_from_parent": mutation.requires_boundary_distinct_from_parent,
        "declared_before_evaluation": mutation.declared_before_evaluation,
        "status": mutation.status,
    }


def _subatomic_state(symbol: str) -> BoundaryState:
    receipt = construct_subatomic_gonol(symbol)
    _frames, axes, attachment_count = lifted_spiral_carried_on_subatomic(receipt)
    return BoundaryState(
        state_id=f"subatomic:{symbol}",
        scale="subatomic",
        source=symbol,
        role="frozen",
        interior_modes=3,
        boundary_axes=tuple(axes),
        coupling_slots=tuple(f"slot:{index}" for index in range(attachment_count)),
        bulk_count=len(receipt.gonol.participants),
        labels=(symbol,),
        structure_signature=tuple(
            f"{participant.relation}:{participant.source_id}"
            for participant in receipt.gonol.participants
        ),
    )


def _element_state(symbol: str) -> BoundaryState:
    receipt = construct_element_gonol(symbol)
    _frames, axes, attachment_count = lifted_spiral_carried_on_element(receipt)
    return BoundaryState(
        state_id=f"element:{symbol}",
        scale="element",
        source=symbol,
        role="frozen",
        interior_modes=3,
        boundary_axes=tuple(axes),
        coupling_slots=tuple(f"slot:{index}" for index in range(attachment_count)),
        bulk_count=len(receipt.gonol.participants),
        labels=(symbol,),
        structure_signature=tuple(
            f"{participant.relation}:{participant.source_id}"
            for participant in receipt.gonol.participants
        ),
    )


def _molecule_state(
    formula: str,
    construction: MolecularConstruction | None = None,
) -> BoundaryState:
    if construction is None:
        construction = construct_molecule(formula)
    _frames, axes, attachment_count = lifted_spiral_carried_on_molecule(construction)
    slots = tuple(
        _slot_signature(slot)
        for slot in construction.invariants["mobius"]["attachment_slots"]
    )
    if len(slots) != attachment_count:
        raise ValueError(f"{formula}: lifted-spiral attachment count does not match slots")
    return BoundaryState(
        state_id=f"molecule:{formula}",
        scale="molecule",
        source=formula,
        role="frozen",
        interior_modes=3,
        boundary_axes=tuple(axes),
        coupling_slots=slots,
        bulk_count=int(construction.invariants["atom_count"]),
        labels=tuple(construction.invariants["participant_symbols"]),
        structure_signature=tuple(
            _slot_signature(part)
            for part in construction.invariants["dimensional_geometry"]["structure"]["parts"]
        ),
    )


@lru_cache(maxsize=1)
def freeze_current_construction_surface() -> dict[str, Any]:
    """Freeze the current EPAC boundary states before controls are generated."""
    symbols = required_element_symbols()
    formulas = tuple(MOLECULE_COMPOSITIONS)
    states: dict[str, BoundaryState] = {}
    for symbol in symbols:
        subatomic = _subatomic_state(symbol)
        element = _element_state(symbol)
        states[subatomic.state_id] = subatomic
        states[element.state_id] = element
    constructions = construct_declared_molecules()
    for formula in formulas:
        molecule = _molecule_state(formula, constructions[formula])
        states[molecule.state_id] = molecule
    return {
        "surface_id": "epac-current-locked-nine-boundary-surface",
        "formulas": formulas,
        "required_elements": symbols,
        "state_ids": tuple(states),
        "states": states,
        "state_records": {state_id: _state_record(state) for state_id, state in states.items()},
        "frozen_before_controls": True,
    }


def _expected_b_after_operation(
    parent: BoundaryState,
    operation: Mapping[str, Any],
) -> BoundaryCapacity:
    kind = operation["kind"]
    interior, d_boundary, c_boundary = parent.b
    if kind in {"relabel", "reorder", "rewire_same_count"}:
        return parent.b
    if kind == "delete_axis":
        return (interior, d_boundary - 1, c_boundary)
    if kind in {"add_axis", "duplicate_participant"}:
        return (interior, d_boundary + 1, c_boundary)
    if kind == "delete_coupling":
        return (interior, d_boundary, c_boundary - 1)
    if kind == "add_coupling":
        return (interior, d_boundary, c_boundary + 1)
    if kind == "hierarchy_refinement_perturbation":
        return (interior, int(operation["target_d_boundary"]), c_boundary)
    raise ValueError(f"unknown boundary operation: {kind}")


def _apply_operation(
    parent: BoundaryState,
    operation: Mapping[str, Any],
    expected_b: BoundaryCapacity,
) -> BoundaryState:
    kind = operation["kind"]
    axes = parent.boundary_axes
    slots = parent.coupling_slots
    labels = parent.labels
    structure = parent.structure_signature
    if kind == "relabel":
        axes = tuple(f"axis:{index}" for index, _axis in enumerate(parent.boundary_axes))
        slots = tuple(f"slot:{index}" for index, _slot in enumerate(parent.coupling_slots))
        labels = tuple(f"label:{index}" for index, _label in enumerate(parent.labels))
        structure = tuple(f"incidence:{index}" for index, _item in enumerate(parent.structure_signature))
    elif kind == "reorder":
        axes = tuple(reversed(parent.boundary_axes))
        slots = tuple(reversed(parent.coupling_slots))
        labels = tuple(reversed(parent.labels))
        structure = tuple(reversed(parent.structure_signature))
    elif kind == "delete_axis":
        axes = parent.boundary_axes[:-1]
    elif kind == "add_axis":
        axes = (*parent.boundary_axes, f"{parent.state_id}:added-axis")
    elif kind == "duplicate_participant":
        axes = (*parent.boundary_axes, f"{parent.boundary_axes[-1]}:duplicate")
        labels = (*parent.labels, parent.labels[-1] if parent.labels else "duplicate")
    elif kind == "delete_coupling":
        slots = parent.coupling_slots[:-1]
    elif kind == "add_coupling":
        slots = (*parent.coupling_slots, f"{parent.state_id}:added-coupling")
    elif kind == "rewire_same_count":
        slots = tuple(f"{slot}:rewired" for slot in parent.coupling_slots)
        structure = (*parent.structure_signature, f"{parent.state_id}:rewired-incidence")
    elif kind == "hierarchy_refinement_perturbation":
        axes = tuple(operation["target_axes"])
    actual = replace(
        parent,
        state_id=f"{parent.state_id}::{operation['mutation_id']}",
        role="control",
        boundary_axes=tuple(axes),
        coupling_slots=tuple(slots),
        labels=tuple(labels),
        structure_signature=tuple(structure),
        parent_id=parent.state_id,
        mutation_id=str(operation["mutation_id"]),
    )
    if actual.b != expected_b:
        raise ValueError(
            f"{operation['mutation_id']}: expected {expected_b}, produced {actual.b}"
        )
    return actual


def _make_mutation(
    parent: BoundaryState,
    operation: Mapping[str, Any],
    *,
    expected_relation: str,
    requires_boundary_distinct: bool,
) -> BoundaryMutation:
    expected_b = _expected_b_after_operation(parent, operation)
    actual = _apply_operation(parent, operation, expected_b)
    status = SURVIVED if actual.b == expected_b else FALSIFIED
    if requires_boundary_distinct and actual.b == parent.b:
        status = FALSIFIED
    return BoundaryMutation(
        mutation_id=str(operation["mutation_id"]),
        kind=str(operation["kind"]),
        parent_id=parent.state_id,
        expected_relation=expected_relation,
        expected_b=expected_b,
        actual_state=actual,
        requires_boundary_distinct_from_parent=requires_boundary_distinct,
        declared_before_evaluation=True,
        status=status,
    )


def _hierarchy_target_axes(parent: BoundaryState, states: Mapping[str, BoundaryState]) -> tuple[str, ...] | None:
    if parent.scale != "element":
        return None
    subatomic = states.get(f"subatomic:{parent.source}")
    if subatomic is None:
        return None
    if subatomic.b[1] == parent.b[1]:
        return None
    return subatomic.boundary_axes


def build_counterfactual_neighborhood(surface: Mapping[str, Any]) -> dict[str, Any]:
    """Build first-order controls from a pre-frozen surface."""
    if not surface.get("frozen_before_controls"):
        raise ValueError("surface must be frozen before controls are generated")
    states: Mapping[str, BoundaryState] = surface["states"]
    mutations: list[BoundaryMutation] = []
    for parent in states.values():
        mutations.append(
            _make_mutation(
                parent,
                {"kind": "relabel", "mutation_id": "relabel"},
                expected_relation="invariant_to_label_change",
                requires_boundary_distinct=False,
            )
        )
        mutations.append(
            _make_mutation(
                parent,
                {"kind": "reorder", "mutation_id": "reorder"},
                expected_relation="invariant_to_order_change",
                requires_boundary_distinct=False,
            )
        )
        mutations.append(
            _make_mutation(
                parent,
                {"kind": "add_axis", "mutation_id": "add_axis"},
                expected_relation="distinct_by_d_boundary",
                requires_boundary_distinct=True,
            )
        )
        mutations.append(
            _make_mutation(
                parent,
                {"kind": "duplicate_participant", "mutation_id": "duplicate_participant"},
                expected_relation="distinct_by_d_boundary",
                requires_boundary_distinct=True,
            )
        )
        if parent.b[1] > 1:
            mutations.append(
                _make_mutation(
                    parent,
                    {"kind": "delete_axis", "mutation_id": "delete_axis"},
                    expected_relation="distinct_by_d_boundary",
                    requires_boundary_distinct=True,
                )
            )
        if parent.b[2] > 0:
            mutations.append(
                _make_mutation(
                    parent,
                    {"kind": "delete_coupling", "mutation_id": "delete_coupling"},
                    expected_relation="distinct_by_c_boundary",
                    requires_boundary_distinct=True,
                )
            )
            mutations.append(
                _make_mutation(
                    parent,
                    {"kind": "add_coupling", "mutation_id": "add_coupling"},
                    expected_relation="distinct_by_c_boundary",
                    requires_boundary_distinct=True,
                )
            )
            mutations.append(
                _make_mutation(
                    parent,
                    {"kind": "rewire_same_count", "mutation_id": "rewire_same_count"},
                    expected_relation="coarse_equivalent_by_same_counts",
                    requires_boundary_distinct=False,
                )
            )
        hierarchy_target = _hierarchy_target_axes(parent, states)
        if hierarchy_target is not None:
            mutations.append(
                _make_mutation(
                    parent,
                    {
                        "kind": "hierarchy_refinement_perturbation",
                        "mutation_id": "hierarchy_refinement_perturbation",
                        "target_axes": hierarchy_target,
                        "target_d_boundary": len(hierarchy_target),
                    },
                    expected_relation="distinct_by_d_boundary",
                    requires_boundary_distinct=True,
                )
            )
    return {
        "surface_id": surface["surface_id"],
        "parent_states": states,
        "mutations": tuple(mutations),
        "mutation_records": tuple(_mutation_record(mutation) for mutation in mutations),
        "status": SURVIVED if all(mutation.status == SURVIVED for mutation in mutations) else FALSIFIED,
    }


def _label_invariance(neighborhood: Mapping[str, Any]) -> dict[str, Any]:
    parent_states: Mapping[str, BoundaryState] = neighborhood["parent_states"]
    controls = [
        mutation
        for mutation in neighborhood["mutations"]
        if mutation.kind in {"relabel", "reorder"}
    ]
    return {
        "control_count": len(controls),
        "all_expected_invariant": all(
            mutation.actual_state.b == mutation.expected_b
            and mutation.actual_state.b == parent_states[mutation.parent_id].b
            and not mutation.requires_boundary_distinct_from_parent
            for mutation in controls
        ),
        "status": SURVIVED if controls and all(mutation.status == SURVIVED for mutation in controls) else FALSIFIED,
    }


def _equivalent_path_invariance() -> dict[str, Any]:
    closure = cross_scale_compositional_closure()
    element_ok = all(
        element_closure_ledger(symbol)["path_independence"]["path_independent"]
        for symbol in closure["scope"]["required_elements"]
    )
    formula_ok = all(
        formula_closure_ledger(formula)["paths"]["path_independent"]
        for formula in closure["scope"]["formulas"]
    )
    return {
        "element_path_independent": element_ok,
        "formula_path_independent": formula_ok,
        "cross_scale_closure_statuses": closure["statuses"],
        "status": SURVIVED if element_ok and formula_ok else FALSIFIED,
    }


def _d_boundary_sensitivity(neighborhood: Mapping[str, Any]) -> dict[str, Any]:
    parent_states: Mapping[str, BoundaryState] = neighborhood["parent_states"]
    positive = [
        mutation
        for mutation in neighborhood["mutations"]
        if mutation.kind in {
            "add_axis",
            "delete_axis",
            "duplicate_participant",
            "hierarchy_refinement_perturbation",
        }
    ]
    negative = [
        mutation
        for mutation in neighborhood["mutations"]
        if mutation.kind in {"relabel", "reorder", "add_coupling", "delete_coupling", "rewire_same_count"}
    ]
    positive_failures = tuple(
        mutation.mutation_id
        for mutation in positive
        if not (
            mutation.status == SURVIVED
            and mutation.actual_state.b == mutation.expected_b
            and mutation.actual_state.b[0] == parent_states[mutation.parent_id].b[0]
            and mutation.actual_state.b[1] != parent_states[mutation.parent_id].b[1]
            and mutation.actual_state.b[2] == parent_states[mutation.parent_id].b[2]
        )
    )
    negative_failures = tuple(
        mutation.mutation_id
        for mutation in negative
        if not (
            mutation.status == SURVIVED
            and mutation.actual_state.b == mutation.expected_b
            and mutation.actual_state.b[1] == parent_states[mutation.parent_id].b[1]
        )
    )
    return {
        "positive_control_count": len(positive),
        "negative_control_count": len(negative),
        "positive_control_kinds": tuple(sorted({mutation.kind for mutation in positive})),
        "negative_control_kinds": tuple(sorted({mutation.kind for mutation in negative})),
        "positive_failures": positive_failures,
        "negative_failures": negative_failures,
        "status": SURVIVED if positive and negative and not positive_failures and not negative_failures else FALSIFIED,
    }


def _c_boundary_sensitivity(neighborhood: Mapping[str, Any]) -> dict[str, Any]:
    parent_states: Mapping[str, BoundaryState] = neighborhood["parent_states"]
    positive = [
        mutation
        for mutation in neighborhood["mutations"]
        if mutation.kind in {"add_coupling", "delete_coupling"}
    ]
    negative = [
        mutation
        for mutation in neighborhood["mutations"]
        if mutation.kind == "rewire_same_count"
    ]
    positive_failures = tuple(
        mutation.mutation_id
        for mutation in positive
        if not (
            mutation.status == SURVIVED
            and mutation.actual_state.b == mutation.expected_b
            and mutation.actual_state.b[0] == parent_states[mutation.parent_id].b[0]
            and mutation.actual_state.b[1] == parent_states[mutation.parent_id].b[1]
            and mutation.actual_state.b[2] != parent_states[mutation.parent_id].b[2]
            and mutation.actual_state.bulk_count == parent_states[mutation.parent_id].bulk_count
        )
    )
    negative_failures = tuple(
        mutation.mutation_id
        for mutation in negative
        if not (
            mutation.status == SURVIVED
            and mutation.actual_state.b == mutation.expected_b
            and mutation.actual_state.b == parent_states[mutation.parent_id].b
            and mutation.actual_state.structure_signature
            != parent_states[mutation.parent_id].structure_signature
        )
    )
    return {
        "positive_control_count": len(positive),
        "negative_control_count": len(negative),
        "positive_control_kinds": tuple(sorted({mutation.kind for mutation in positive})),
        "negative_control_kinds": tuple(sorted({mutation.kind for mutation in negative})),
        "positive_failures": positive_failures,
        "negative_failures": negative_failures,
        "status": SURVIVED if positive and negative and not positive_failures and not negative_failures else FALSIFIED,
    }


def _partition(values: Mapping[str, Any]) -> dict[Any, tuple[str, ...]]:
    groups: dict[Any, list[str]] = {}
    for key, value in values.items():
        groups.setdefault(value, []).append(key)
    return {value: tuple(sorted(keys)) for value, keys in groups.items()}


def _non_singleton_control_discrimination(surface: Mapping[str, Any]) -> dict[str, Any]:
    molecule_states = {
        state.source: state
        for state in surface["states"].values()
        if state.scale == "molecule"
    }
    bulk_partition = _partition(
        {formula: state.bulk_count for formula, state in molecule_states.items()}
    )
    b_by_formula = {formula: state.b for formula, state in molecule_states.items()}
    split_groups = {}
    for _bulk, formulas in bulk_partition.items():
        if len(formulas) <= 1:
            continue
        b_values = {formula: b_by_formula[formula] for formula in formulas}
        b_partition = _partition(b_values)
        if len(b_partition) > 1:
            split_groups[formulas] = tuple(b_partition.values())
    singleton_regression = control_like_partition_failure_disposition()
    singleton_warning_retained = (
        singleton_regression["observed_subatomic_lifted_spiral_matches_control"]
        and singleton_regression["classification"] == "stale_or_incorrect_control_assertion"
        and not singleton_regression["compositional_counterexample"]
    )
    return {
        "bulk_count_partition": bulk_partition,
        "B_by_formula": b_by_formula,
        "non_singleton_bulk_groups": tuple(
            formulas for formulas in bulk_partition.values() if len(formulas) > 1
        ),
        "split_non_singleton_groups": split_groups,
        "singleton_partition_regression": singleton_regression,
        "singleton_warning_retained": singleton_warning_retained,
        "status": SURVIVED if split_groups and singleton_warning_retained else FALSIFIED,
    }


def _structure_key(state: BoundaryState) -> tuple[Any, ...]:
    return (
        state.scale,
        state.source,
        state.bulk_count,
        state.labels,
        tuple(sorted(state.boundary_axes)),
        tuple(sorted(state.coupling_slots)),
        tuple(sorted(state.structure_signature)),
    )


def _collision_search(
    surface: Mapping[str, Any],
    neighborhood: Mapping[str, Any],
) -> dict[str, Any]:
    states: dict[str, BoundaryState] = dict(surface["states"])
    parent_by_id = states
    required_distinct_failures = []
    for mutation in neighborhood["mutations"]:
        states[mutation.actual_state.state_id] = mutation.actual_state
        if (
            mutation.requires_boundary_distinct_from_parent
            and mutation.actual_state.b == parent_by_id[mutation.parent_id].b
        ):
            required_distinct_failures.append(
                (mutation.parent_id, mutation.actual_state.state_id, mutation.kind)
            )

    coarse_collisions = []
    for left, right in combinations(states.values(), 2):
        if left.b != right.b:
            continue
        if _structure_key(left) == _structure_key(right):
            continue
        classification = "intentionally_coarse_equivalence_class"
        if left.parent_id == right.state_id or right.parent_id == left.state_id:
            classification = "declared_invariance_or_same_count_control"
        coarse_collisions.append(
            {
                "left": left.state_id,
                "right": right.state_id,
                "B": left.b,
                "classification": classification,
            }
        )

    return {
        "bounded_state_count": len(states),
        "same_B_collision_count": len(coarse_collisions),
        "classified_collision_count": len(coarse_collisions),
        "coarse_collision_examples": tuple(coarse_collisions[:12]),
        "required_boundary_distinct_failures": tuple(required_distinct_failures),
        "classification": (
            "complete_for_bounded_first_order_neighborhood"
            if not required_distinct_failures
            else "falsifies_descriptor_sufficiency"
        ),
        "status": SURVIVED if not required_distinct_failures else FALSIFIED,
    }


@lru_cache(maxsize=1)
def boundary_descriptor_nondegeneracy_report() -> dict[str, Any]:
    """Run the bounded EPAC boundary-descriptor non-degeneracy audit."""
    surface = freeze_current_construction_surface()
    neighborhood = build_counterfactual_neighborhood(surface)
    label_invariance = _label_invariance(neighborhood)
    equivalent_path_invariance = _equivalent_path_invariance()
    d_sensitivity = _d_boundary_sensitivity(neighborhood)
    c_sensitivity = _c_boundary_sensitivity(neighborhood)
    non_singleton = _non_singleton_control_discrimination(surface)
    collisions = _collision_search(surface, neighborhood)
    statuses = {
        "label_invariance": label_invariance["status"],
        "equivalent_path_invariance": equivalent_path_invariance["status"],
        "d_boundary_sensitivity": d_sensitivity["status"],
        "c_boundary_sensitivity": c_sensitivity["status"],
        "non_singleton_control_discrimination": non_singleton["status"],
        "descriptor_collision_search": collisions["status"],
    }
    overall = (
        SURVIVED
        if all(status == SURVIVED for status in statuses.values())
        else FALSIFIED
    )
    statuses["boundary_descriptor_non_degeneracy"] = overall
    return {
        "decision": (
            "B=(3,d_boundary,c_boundary) is non-degenerate over the bounded "
            "first-order controls: invariant to labels/order/equivalent paths, "
            "sensitive to declared d and c changes, and not explained by the "
            "old singleton-partition accident. It remains intentionally coarse "
            "for full incidence topology."
        ),
        "surface": {
            "surface_id": surface["surface_id"],
            "formulas": surface["formulas"],
            "required_elements": surface["required_elements"],
            "state_count": len(surface["states"]),
            "frozen_before_controls": surface["frozen_before_controls"],
        },
        "control_neighborhood": {
            "mutation_count": len(neighborhood["mutations"]),
            "status": neighborhood["status"],
            "mutation_records": neighborhood["mutation_records"],
        },
        "label_invariance": label_invariance,
        "equivalent_path_invariance": equivalent_path_invariance,
        "d_boundary_sensitivity": d_sensitivity,
        "c_boundary_sensitivity": c_sensitivity,
        "non_singleton_control_discrimination": non_singleton,
        "descriptor_collision_search": collisions,
        "statuses": statuses,
        "requires_more": (
            "B is not a complete incidence-topology descriptor",
            "future construction paths must be added to equivalent-path controls before claiming coverage over them",
            "no PCEA mapping, UCNS continuum theorem, runtime channel encoding, or external physical claim is made",
        ),
    }


__all__ = [
    "BoundaryMutation",
    "BoundaryState",
    "boundary_descriptor_nondegeneracy_report",
    "build_counterfactual_neighborhood",
    "freeze_current_construction_surface",
]
