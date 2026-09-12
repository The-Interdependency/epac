"""Boundary-capacity quotient evidence for EPAC.

This module asks the narrower question left by the non-degeneracy audit:
whether equality of B=(3,d_boundary,c_boundary) is exactly equality of the
presently observable boundary-capacity behavior on the frozen EPAC state
surface.

The quotient is intentionally not a state descriptor. It ignores internal
identity, labels, incidence signatures, and topology except when reporting that
B remains insufficient for those stronger claims.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Mapping

from epac_boundary_nondegeneracy import (
    BoundaryMutation,
    BoundaryState,
    build_counterfactual_neighborhood,
    freeze_current_construction_surface,
)
from epac_cross_scale_closure import FALSIFIED, SURVIVED, UNRESOLVED

# === MODULE_BUILD ===
# id: epac_boundary_capacity_quotient
#   module_name: epac_boundary_quotient
#   module_kind: experiment
#   summary: evidence-only audit comparing equality of EPAC B=(3,d_boundary,c_boundary) with equality of presently observable boundary-capacity probe behavior over frozen subatomic, element, and molecule states
#   owner: The Interdependency
#   public_surface: boundary_capacity_behavior_signature, boundary_capacity_quotient_report
#   internal_surface: _mutation_index, _probe_record, _classes_by_key, _same_B_probe_mismatches, _state_sufficiency_collisions
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_boundary_capacity_quotient
#   rollout: imported by tests/docs as a research evidence surface; no constructor, descriptor, or runtime behavior changes
#   rollback: remove this module and its tests/docs without changing boundary descriptor, non-degeneracy, or locked molecule construction
#   requires: epac_boundary_descriptor_nondegeneracy
#   since: 2026-09-07
#   unresolved: future boundary probes may refine the quotient; incidence and topology completeness are not established by count-valued boundary-capacity probes
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: boundary_quotient_freezes_current_surface
#   given: the quotient audit is run
#   then: it compares only the pre-existing frozen EPAC subatomic, element, and locked molecule states
#   class: evidence
#
# id: boundary_quotient_probe_inventory_is_existing_and_count_valued
#   given: the quotient audit defines boundary-capacity behavior
#   then: its probes are limited to observe-B and the existing non-degeneracy boundary controls, and every admissible result is a three-component B tuple
#   class: safety
#
# id: boundary_quotient_ignores_identity_incidence_and_topology
#   given: two frozen states are compared for boundary-capacity equivalence
#   then: the comparison signature omits source id, labels, axis names, coupling-slot identities, incidence signatures, and topology
#   class: safety
#
# id: boundary_quotient_relation_is_probe_signature_equality
#   given: frozen EPAC states R1 and R2
#   then: R1 is boundary-capacity equivalent to R2 exactly when every presently admissible boundary-capacity probe has the same admissibility and B-valued response
#   class: correctness
#
# id: boundary_quotient_B_matches_probe_equivalence
#   given: the frozen EPAC state surface and current boundary-capacity probe inventory
#   then: B(R1)=B(R2) if and only if R1 and R2 are boundary-capacity equivalent
#   class: evidence
#
# id: boundary_quotient_preserves_state_sufficiency_falsification
#   given: equality of B is compared with full frozen-state identity, incidence, and topology distinctions
#   then: same-B collisions remain reported as a state-sufficiency falsification rather than erased by quotient classification
#   class: doctrine
#
# id: boundary_quotient_does_not_extend_B
#   given: the quotient audit classifies boundary-capacity behavior
#   then: it does not add any component to B or define a new descriptor to rescue state sufficiency
#   class: safety
# === END CONTRACTS ===


BoundaryCapacity = tuple[int, int, int]
ProbeRecord = tuple[str, str, BoundaryCapacity | None, BoundaryCapacity | None, str | None]
ProbeSignature = tuple[ProbeRecord, ...]

OBSERVE_B_PROBE = "observe_B"
BOUNDARY_CONTROL_PROBES = (
    "relabel",
    "reorder",
    "add_axis",
    "delete_axis",
    "duplicate_participant",
    "add_coupling",
    "delete_coupling",
    "rewire_same_count",
    "hierarchy_refinement_perturbation",
)
BOUNDARY_CAPACITY_PROBES = (OBSERVE_B_PROBE, *BOUNDARY_CONTROL_PROBES)

STATE_IDENTITY_EXCLUDED_FIELDS = (
    "state_id",
    "scale",
    "source",
    "role",
    "bulk_count",
    "labels",
    "boundary_axes",
    "coupling_slots",
    "structure_signature",
    "parent_id",
    "mutation_id",
)


def _mutation_index(
    neighborhood: Mapping[str, Any],
) -> dict[str, dict[str, BoundaryMutation]]:
    indexed: dict[str, dict[str, BoundaryMutation]] = {}
    for mutation in neighborhood["mutations"]:
        indexed.setdefault(mutation.parent_id, {})[mutation.kind] = mutation
    return indexed


def _probe_record(
    state: BoundaryState,
    kind: str,
    parent_mutations: Mapping[str, BoundaryMutation],
) -> ProbeRecord:
    if kind == OBSERVE_B_PROBE:
        return (kind, "admissible", state.b, state.b, "descriptor")

    mutation = parent_mutations.get(kind)
    if mutation is None:
        return (kind, "inadmissible", None, None, None)

    return (
        kind,
        "admissible",
        mutation.expected_b,
        mutation.actual_state.b,
        mutation.expected_relation,
    )


def boundary_capacity_behavior_signature(
    state: BoundaryState,
    parent_mutations: Mapping[str, BoundaryMutation],
) -> ProbeSignature:
    """Return the current boundary-capacity behavior signature for one state.

    The signature is count-valued: probe name, admissibility, expected B, actual
    B, and declared relation. It deliberately omits state identity, labels,
    concrete axis names, concrete coupling-slot names, incidence signatures, and
    topology.
    """
    return tuple(
        _probe_record(state, kind, parent_mutations)
        for kind in BOUNDARY_CAPACITY_PROBES
    )


def _classes_by_key(
    states: Mapping[str, BoundaryState],
    key_for: Callable[[BoundaryState], Any],
) -> dict[Any, tuple[str, ...]]:
    classes: dict[Any, list[str]] = {}
    for state_id, state in states.items():
        classes.setdefault(key_for(state), []).append(state_id)
    return {
        key: tuple(sorted(state_ids))
        for key, state_ids in classes.items()
    }


def _canonical_class_sets(classes: Mapping[Any, tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted(tuple(sorted(state_ids)) for state_ids in classes.values()))


def _first_probe_difference(
    left: ProbeSignature,
    right: ProbeSignature,
) -> dict[str, Any] | None:
    for left_record, right_record in zip(left, right):
        if left_record != right_record:
            return {
                "probe": left_record[0],
                "left": left_record,
                "right": right_record,
            }
    return None


def _same_B_probe_mismatches(
    states: Mapping[str, BoundaryState],
    signatures: Mapping[str, ProbeSignature],
) -> tuple[dict[str, Any], ...]:
    mismatches: list[dict[str, Any]] = []
    for left_id, right_id in combinations(states, 2):
        left = states[left_id]
        right = states[right_id]
        if left.b != right.b:
            continue
        if signatures[left_id] == signatures[right_id]:
            continue
        mismatches.append(
            {
                "left": left_id,
                "right": right_id,
                "B": left.b,
                "first_probe_difference": _first_probe_difference(
                    signatures[left_id],
                    signatures[right_id],
                ),
            }
        )
    return tuple(mismatches)


def _unequal_B_equivalent_pairs(
    states: Mapping[str, BoundaryState],
    signatures: Mapping[str, ProbeSignature],
) -> tuple[dict[str, Any], ...]:
    pairs: list[dict[str, Any]] = []
    for left_id, right_id in combinations(states, 2):
        left = states[left_id]
        right = states[right_id]
        if left.b == right.b:
            continue
        if signatures[left_id] != signatures[right_id]:
            continue
        pairs.append(
            {
                "left": left_id,
                "right": right_id,
                "left_B": left.b,
                "right_B": right.b,
            }
        )
    return tuple(pairs)


def _state_sufficiency_collisions(
    b_classes: Mapping[BoundaryCapacity, tuple[str, ...]],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "B": b_value,
            "state_ids": state_ids,
            "classification": "same_B_distinct_frozen_states",
        }
        for b_value, state_ids in sorted(b_classes.items())
        if len(state_ids) > 1
    )


def _probe_inventory(signatures: Mapping[str, ProbeSignature]) -> dict[str, Any]:
    admissible_outputs = []
    for signature in signatures.values():
        for _kind, admissibility, expected_b, actual_b, _relation in signature:
            if admissibility == "admissible":
                admissible_outputs.extend((expected_b, actual_b))
    all_outputs_are_B = all(
        isinstance(output, tuple)
        and len(output) == 3
        and all(isinstance(component, int) for component in output)
        for output in admissible_outputs
    )
    return {
        "probe_kinds": BOUNDARY_CAPACITY_PROBES,
        "probe_source": "epac_boundary_nondegeneracy.build_counterfactual_neighborhood",
        "admissible_result_shape": "B=(interior_modes,d_boundary,c_boundary)",
        "identity_fields_excluded": STATE_IDENTITY_EXCLUDED_FIELDS,
        "uses_identity_or_incidence_fields": False,
        "admissible_output_count": len(admissible_outputs),
        "all_admissible_outputs_are_B": all_outputs_are_B,
        "status": SURVIVED if all_outputs_are_B else FALSIFIED,
    }


@lru_cache(maxsize=1)
def boundary_capacity_quotient_report() -> dict[str, Any]:
    """Compare B-equality with the present boundary-capacity behavior quotient."""
    surface = freeze_current_construction_surface()
    neighborhood = build_counterfactual_neighborhood(surface)
    states: Mapping[str, BoundaryState] = surface["states"]
    mutation_index = _mutation_index(neighborhood)

    signatures = {
        state_id: boundary_capacity_behavior_signature(
            state,
            mutation_index.get(state_id, {}),
        )
        for state_id, state in states.items()
    }
    b_classes = _classes_by_key(states, lambda state: state.b)
    behavior_classes = _classes_by_key(states, lambda state: signatures[state.state_id])
    same_b_mismatches = _same_B_probe_mismatches(states, signatures)
    unequal_b_equivalents = _unequal_B_equivalent_pairs(states, signatures)
    state_collisions = _state_sufficiency_collisions(b_classes)

    b_partition = _canonical_class_sets(b_classes)
    behavior_partition = _canonical_class_sets(behavior_classes)
    quotient_matches_B = (
        b_partition == behavior_partition
        and not same_b_mismatches
        and not unequal_b_equivalents
    )
    relation_status = SURVIVED if behavior_classes else FALSIFIED
    quotient_status = SURVIVED if quotient_matches_B else FALSIFIED
    probe_inventory = _probe_inventory(signatures)
    state_sufficiency_status = FALSIFIED if state_collisions else SURVIVED

    statuses = {
        "probe_inventory": probe_inventory["status"],
        "boundary_capacity_equivalence_relation": relation_status,
        "B_matches_boundary_capacity_quotient": quotient_status,
        "state_sufficiency": state_sufficiency_status,
        "incidence_completeness": UNRESOLVED,
        "topology_completeness": UNRESOLVED,
    }

    return {
        "decision": (
            "B=(3,d_boundary,c_boundary) is a complete descriptor of the "
            "present EPAC boundary-capacity quotient over the frozen states. "
            "It remains falsified as a complete state descriptor and does not "
            "establish incidence or topology completeness."
        ),
        "surface": {
            "surface_id": surface["surface_id"],
            "state_count": len(states),
            "state_ids": surface["state_ids"],
            "frozen_before_quotient": surface["frozen_before_controls"],
        },
        "probe_inventory": probe_inventory,
        "B_classes": b_classes,
        "boundary_capacity_behavior_classes": behavior_classes,
        "B_partition": b_partition,
        "behavior_partition": behavior_partition,
        "equal_B_pair_count": sum(
            1
            for left_id, right_id in combinations(states, 2)
            if states[left_id].b == states[right_id].b
        ),
        "same_B_probe_mismatches": same_b_mismatches,
        "unequal_B_equivalent_pairs": unequal_b_equivalents,
        "state_sufficiency_collisions": state_collisions,
        "named_collision_checks": {
            "H_subatomic_vs_H_element": (
                "subatomic:H",
                "element:H",
            ),
            "subatomic_3_3_0": (
                "subatomic:O",
                "subatomic:N",
                "subatomic:C",
                "subatomic:B",
                "subatomic:F",
            ),
            "subatomic_3_4_0": (
                "subatomic:S",
                "subatomic:P",
                "subatomic:Si",
            ),
            "H2O_vs_H2S": ("molecule:H2O", "molecule:H2S"),
            "BF3_vs_NH3_vs_PH3": (
                "molecule:BF3",
                "molecule:NH3",
                "molecule:PH3",
            ),
            "CH4_vs_SiH4": ("molecule:CH4", "molecule:SiH4"),
        },
        "statuses": statuses,
        "requires_more": (
            "future boundary-capacity probes may refine the quotient",
            "state identity, incidence signatures, and topology remain outside B",
            "do not promote B as a complete EPAC state descriptor",
            "no PCEA mapping, UCNS continuum theorem, runtime encoding, or external physical claim is made",
        ),
    }


__all__ = [
    "BOUNDARY_CAPACITY_PROBES",
    "BOUNDARY_CONTROL_PROBES",
    "OBSERVE_B_PROBE",
    "boundary_capacity_behavior_signature",
    "boundary_capacity_quotient_report",
]
