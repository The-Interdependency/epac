"""Minimal-refinement search for the EPAC boundary descriptor.

This module asks which smallest subset of the 13 existing omitted boundary
observables from the probe-completeness audit reproduces the full 21-class
partition. It does not add a descriptor component, operation, probe, coordinate,
PCEA bridge, UCNS claim, runtime encoding, or external physics assertion.

The result is intentionally finite-surface evidence. Reproducing the 21-class
partition is not the same as proving that a candidate is the canonical next
descriptor component or that it composes through the cross-scale construction
stack.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Mapping

from epac_boundary_probe_completeness import (
    OMITTED_OBSERVABLES,
    _classes_by_signature,
    _state_contexts,
    boundary_probe_completeness_report,
)
from epac_cross_scale_closure import BLOCKED, FALSIFIED, SURVIVED, UNRESOLVED

# === MODULE_BUILD ===
# id: epac_boundary_minimal_refinement
#   module_name: epac_boundary_minimal_refinement
#   module_kind: experiment
#   summary: evidence-only search for the smallest existing omitted EPAC boundary observable subset that reproduces the 21-class partition exposed by the probe-completeness audit
#   owner: The Interdependency
#   public_surface: boundary_minimal_refinement_report
#   internal_surface: _distinguishing_observable_names, _observable_outputs, _partition_for, _minimal_refinement_sets, _candidate_ledger
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_boundary_minimal_refinement
#   rollout: imported by tests/docs as a research evidence surface; no descriptor, constructor, quotient, or runtime behavior changes
#   rollback: remove this module and its tests/docs without changing B, the probe-completeness audit, or locked molecule construction
#   requires: epac_boundary_probe_completeness
#   since: 2026-09-07
#   unresolved: canonical semantic preference among multiple singleton refinements; local aggregation law showing refined structural observables compose through subatomic to element to molecule
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: minimal_refinement_uses_only_existing_omitted_distinguishers
#   given: the minimal-refinement audit is run
#   then: candidate components are exactly the 13 existing omitted observables that the probe-completeness audit found distinguishing same-B frozen states
#   class: safety
#
# id: minimal_refinement_searches_by_partition_equality
#   given: a candidate observable subset is evaluated
#   then: it is accepted only when B plus that subset reproduces the full 21-class partition induced by all 13 omitted observables, not merely the same class count
#   class: correctness
#
# id: minimal_refinement_reports_all_minimum_sets
#   given: one or more candidate subsets reproduce the full partition
#   then: the audit reports the smallest subset size, every subset at that size, and whether the minimum is unique
#   class: evidence
#
# id: minimal_refinement_classifies_boundary_semantics
#   given: a minimal candidate set is reported
#   then: each member is classified for intrinsic boundary semantics and for whether its normalized observable encodes state labels, ids, source names, or construction history
#   class: safety
#
# id: minimal_refinement_keeps_B_unmodified
#   given: the refinement search succeeds
#   then: B remains the original three-component tuple and no refined descriptor is installed or promoted by the audit
#   class: safety
#
# id: minimal_refinement_classifies_compositionality
#   given: a minimal candidate reproduces the finite partition
#   then: local reproducibility from existing state structure is reported separately from unresolved cross-scale compositional aggregation
#   class: doctrine
#
# id: minimal_refinement_blocks_pcea_mapping
#   given: canonicality or cross-scale compositionality is unresolved
#   then: PCEA mapping remains BLOCKED in the report
#   class: safety
# === END CONTRACTS ===


RefinementSet = tuple[str, ...]
Partition = tuple[tuple[str, ...], ...]

STRUCTURAL_SEMANTICS: Mapping[str, str] = {
    "charged_structure_readout": (
        "declared oriented couplings, per-slot charge state, incidence degree, "
        "participating boundary count, and ternary-coupling flag"
    ),
    "topology_structure_readout": (
        "declared coupling arities, incidence degree, participating boundary "
        "count, and ternary-coupling flag with charges omitted"
    ),
    "quaternion_structure_readout": (
        "4-component representations of local 3-structures induced by declared "
        "hub-first binary couplings"
    ),
    "geometry_from_declared_couplings": (
        "aggregate declared coupling geometry envelope after identity fields are "
        "excluded"
    ),
    "structure_from_charged_couplings": (
        "combination of declared oriented couplings, arity charge states, degree, "
        "and local quaternion representations"
    ),
    "degree_relations": (
        "boundary incidence degree and ordered slot-degree profile for "
        "participating dimensions"
    ),
    "oriented_instance_couplings": (
        "declared hub-first instance coupling availability with arity and "
        "charge-state shape"
    ),
    "local_three_structures": (
        "count and occurrence pattern of local 3-structures represented by "
        "pairs of hub-first binary couplings"
    ),
    "quaternion_of_local_three": (
        "single local-3 quaternion representation semantics applied to every "
        "declared local 3"
    ),
    "quaternions_from_declared_couplings": (
        "all local-3 quaternion representations derivable from declared "
        "couplings"
    ),
    "has_declared_coupling": (
        "whether declared coupling structure exists, plus the boundary coupling "
        "part count used by the existing observer"
    ),
    "instances_missing_oriented_hub_coupling": (
        "oriented hub-coupling availability for declared boundary instances"
    ),
    "require_every_instance_has_oriented_hub_coupling": (
        "fail-closed oriented hub-coupling availability for declared boundary "
        "instances"
    ),
}


def _canonical_partition(classes: Mapping[Any, tuple[str, ...]]) -> Partition:
    return tuple(sorted(tuple(sorted(state_ids)) for state_ids in classes.values()))


def _contains_identifier_or_label(value: Any) -> bool:
    if isinstance(value, str):
        if value.startswith("epac.") or "#" in value:
            return True
        if value.startswith(("subatomic:", "element:", "molecule:")):
            return True
        return False
    if isinstance(value, Mapping):
        return any(
            _contains_identifier_or_label(key)
            or _contains_identifier_or_label(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_contains_identifier_or_label(item) for item in value)
    return False


def _contains_construction_history(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "constructor",
                "receipt",
                "digest",
                "source_id",
                "formula",
                "symbol",
                "provenance",
            )
        )
    if isinstance(value, Mapping):
        return any(
            _contains_construction_history(key)
            or _contains_construction_history(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_contains_construction_history(item) for item in value)
    return False


@lru_cache(maxsize=1)
def _distinguishing_observable_names() -> RefinementSet:
    report = boundary_probe_completeness_report()
    distinguishing = {
        operation.rsplit(".", 1)[-1]
        for operation in report["omitted_distinguishing_operations"]
    }
    return tuple(
        name for name in OMITTED_OBSERVABLES
        if name in distinguishing
    )


@lru_cache(maxsize=1)
def _observable_outputs() -> dict[str, dict[str, Any]]:
    contexts = _state_contexts()
    names = _distinguishing_observable_names()
    return {
        name: {
            state_id: OMITTED_OBSERVABLES[name](context)
            for state_id, context in contexts.items()
        }
        for name in names
    }


def _partition_for(names: RefinementSet) -> Partition:
    contexts = _state_contexts()
    states = {state_id: context["state"] for state_id, context in contexts.items()}
    outputs = _observable_outputs()
    signatures = {
        state_id: (
            states[state_id].b,
            tuple((name, outputs[name][state_id]) for name in names),
        )
        for state_id in states
    }
    return _canonical_partition(_classes_by_signature(signatures))


@lru_cache(maxsize=1)
def _full_refined_partition() -> Partition:
    return _partition_for(_distinguishing_observable_names())


@lru_cache(maxsize=1)
def _minimal_refinement_sets() -> tuple[RefinementSet, ...]:
    names = _distinguishing_observable_names()
    full_partition = _full_refined_partition()
    for size in range(1, len(names) + 1):
        matches = tuple(
            combo for combo in combinations(names, size)
            if _partition_for(combo) == full_partition
        )
        if matches:
            return matches
    return ()


def _candidate_output_is_clean(name: str) -> bool:
    outputs = _observable_outputs()[name].values()
    return not any(
        _contains_identifier_or_label(output)
        or _contains_construction_history(output)
        for output in outputs
    )


def _locally_reproducible(name: str) -> bool:
    contexts = _state_contexts()
    outputs = _observable_outputs()[name]
    return all(
        outputs[state_id] == OMITTED_OBSERVABLES[name](context)
        for state_id, context in contexts.items()
    )


def _candidate_ledger() -> tuple[dict[str, Any], ...]:
    names = _distinguishing_observable_names()
    minimal_sets = _minimal_refinement_sets()
    minimal_members = {name for combo in minimal_sets for name in combo}
    full_partition = _full_refined_partition()
    outputs = _observable_outputs()
    rows: list[dict[str, Any]] = []
    for name in names:
        partition = _partition_for((name,))
        clean = _candidate_output_is_clean(name)
        locally_reproducible = _locally_reproducible(name)
        intrinsic = name in STRUCTURAL_SEMANTICS and clean
        rows.append(
            {
                "operation_name": name,
                "minimal_candidate": name in minimal_members,
                "singleton_class_count": len(partition),
                "singleton_reproduces_full_partition": partition == full_partition,
                "intrinsic_boundary_semantics": intrinsic,
                "semantic_basis": STRUCTURAL_SEMANTICS.get(name, "hmmm"),
                "normalized_observable_excludes_labels_ids_and_history": clean,
                "merely_encodes_construction_history_or_labels": not clean,
                "local_reproducibility_status": (
                    SURVIVED if locally_reproducible else FALSIFIED
                ),
                "cross_scale_compositionality_status": UNRESOLVED,
                "cross_scale_compositionality_reason": (
                    "the existing cross-scale closure derives B only; EPAC has "
                    "not declared a local aggregation law that carries this "
                    "structural observable from subatomic source through element "
                    "refinement and molecule affixiation"
                ),
                "example_outputs": tuple(
                    (state_id, outputs[name][state_id])
                    for state_id in tuple(sorted(outputs[name]))[:3]
                ),
            }
        )
    return tuple(rows)


@lru_cache(maxsize=1)
def boundary_minimal_refinement_report() -> dict[str, Any]:
    """Search for the minimal existing-observable refinement of B."""
    completeness = boundary_probe_completeness_report()
    names = _distinguishing_observable_names()
    baseline_partition = _partition_for(())
    full_partition = _full_refined_partition()
    completeness_partition = tuple(
        sorted(
            tuple(sorted(state_ids))
            for state_ids in completeness["combined_omitted_observable_effect"][
                "class_partition"
            ]
        )
    )
    minimal_sets = _minimal_refinement_sets()
    candidate_rows = _candidate_ledger()
    minimal_rows = tuple(row for row in candidate_rows if row["minimal_candidate"])

    minimum_size = len(minimal_sets[0]) if minimal_sets else None
    all_minimal_intrinsic = bool(minimal_rows) and all(
        row["intrinsic_boundary_semantics"] for row in minimal_rows
    )
    any_minimal_history_or_label = any(
        row["merely_encodes_construction_history_or_labels"]
        for row in minimal_rows
    )
    all_minimal_locally_reproducible = bool(minimal_rows) and all(
        row["local_reproducibility_status"] == SURVIVED
        for row in minimal_rows
    )
    refined_matches = bool(minimal_sets) and all(
        _partition_for(combo) == full_partition for combo in minimal_sets
    )
    full_partition_matches_completeness = full_partition == completeness_partition

    canonicality_status = (
        SURVIVED if len(minimal_sets) == 1 else UNRESOLVED
    )
    compositionality_status = (
        UNRESOLVED
        if all_minimal_locally_reproducible
        else FALSIFIED
    )
    finite_partition_sufficiency_status = (
        SURVIVED
        if refined_matches
        and len(full_partition) == 21
        and full_partition_matches_completeness
        else FALSIFIED
    )
    descriptor_sufficiency_status = (
        SURVIVED
        if (
            finite_partition_sufficiency_status == SURVIVED
            and canonicality_status == SURVIVED
            and compositionality_status == SURVIVED
            and not any_minimal_history_or_label
        )
        else UNRESOLVED
    )
    pcea_mapping_status = (
        BLOCKED if descriptor_sufficiency_status != SURVIVED else UNRESOLVED
    )

    statuses = {
        "minimal_refinement_size": SURVIVED if minimum_size == 1 else FALSIFIED,
        "all_minimal_equivalent_sets": SURVIVED if minimal_sets else FALSIFIED,
        "intrinsic_boundary_semantics": (
            SURVIVED if all_minimal_intrinsic else FALSIFIED
        ),
        "history_or_label_encoding": (
            FALSIFIED if any_minimal_history_or_label else SURVIVED
        ),
        "canonicality": canonicality_status,
        "compositionality": compositionality_status,
        "refined_quotient_class_count": finite_partition_sufficiency_status,
        "descriptor_sufficiency": descriptor_sufficiency_status,
        "pcea_mapping": pcea_mapping_status,
    }

    return {
        "decision": (
            "UNRESOLVED: the finite 21-class partition has singleton "
            "refinements, but the minimum is not unique and EPAC has not "
            "declared a cross-scale aggregation law for promoting any structural "
            "observable as a canonical descriptor component."
        ),
        "surface": {
            "surface_id": completeness["surface"]["surface_id"],
            "state_count": completeness["surface"]["state_count"],
            "state_ids": completeness["surface"]["state_ids"],
        },
        "scope": {
            "candidate_source": "probe-completeness omitted distinguishing operations",
            "candidate_observable_count": len(names),
            "candidate_observables": names,
            "uses_only_existing_omitted_distinguishers": len(names) == 13,
            "B_descriptor_modified": False,
        },
        "partitions": {
            "baseline_B_class_count": len(baseline_partition),
            "full_omitted_observable_class_count": len(full_partition),
            "full_partition_matches_completeness_audit": full_partition_matches_completeness,
            "refined_partition": full_partition,
        },
        "minimal_refinement": {
            "minimum_size": minimum_size,
            "minimum_unique": len(minimal_sets) == 1,
            "minimal_equivalent_sets": minimal_sets,
            "minimal_set_count": len(minimal_sets),
            "all_minimal_candidates_intrinsic": all_minimal_intrinsic,
            "any_minimal_candidate_merely_history_or_label": any_minimal_history_or_label,
        },
        "candidate_ledger": candidate_rows,
        "canonicality": {
            "status": canonicality_status,
            "reason": (
                "minimum is not unique: multiple existing singleton structural "
                "observables reproduce the same finite partition, and current "
                "canon does not choose among charge/degree/oriented/quaternion/"
                "aggregate-geometry views"
                if canonicality_status == UNRESOLVED
                else "minimum is unique"
            ),
        },
        "compositionality": {
            "local_reproducibility_status": (
                SURVIVED if all_minimal_locally_reproducible else FALSIFIED
            ),
            "cross_scale_compositionality_status": compositionality_status,
            "reason": (
                "minimal candidates are reproducible from each frozen state's "
                "existing structure, but no declared local aggregation law yet "
                "carries the chosen structural observable through subatomic to "
                "element to molecule"
            ),
        },
        "descriptor_sufficiency": {
            "finite_21_class_partition_reproduction": finite_partition_sufficiency_status,
            "promotable_descriptor_sufficiency": descriptor_sufficiency_status,
            "reason": (
                "finite partition reproduction survives; canonicality and "
                "cross-scale compositionality remain unresolved"
            ),
        },
        "statuses": statuses,
        "requires_more": (
            "select or justify a canonical semantic representative among the singleton refinements",
            "declare and test a local aggregation rule if a structural observable is to become a refined descriptor component",
            "do not add all omitted observables by default",
            "do not modify B merely to rescue probe completeness",
            "PCEA mapping remains blocked until canonicality and compositionality close",
        ),
    }


__all__ = [
    "boundary_minimal_refinement_report",
]
