"""Cross-scale boundary-capacity closure evidence for EPAC.

This module is evidence-only. It consumes the implemented EPAC construction
APIs for subatomic gonols, periodic element gonols, and the locked molecule
formulas, then checks whether the boundary-capacity descriptor can be carried
compositionally from the lowest implemented source through molecule formation.

No PCEA runtime, PCEA mapping, external physics claim, continuum theorem, or
UCNS internal inspection is performed here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping

from epac_molecular import (
    MOLECULE_COMPOSITIONS,
    apply_local_step,
    boundary_capacity_carried_on_molecule,
    construct_declared_molecules,
    construct_molecule,
    generate_compositional_paths,
    lifted_spiral_carried_on_molecule,
    matched_information_control,
)
from epac_periodic import (
    boundary_capacity_from_element_receipt,
    construct_element_gonol,
    lifted_spiral_carried_on_element,
)
from epac_public_gonol import ClosedPublicGonol, PublicGonolReceipt
from epac_subatomic.subatomic_gonol import (
    boundary_capacity_from_subatomic_receipt,
    construct_subatomic_gonol,
    lifted_spiral_carried_on_subatomic,
)

# === MODULE_BUILD ===
# id: epac_cross_scale_compositional_closure
#   module_name: epac_cross_scale_closure
#   module_kind: experiment
#   summary: evidence-only audit of whether EPAC boundary capacity composes from subatomic gonols through periodic element gonols into the locked nine molecule formulas
#   owner: The Interdependency
#   public_surface: required_element_symbols, derive_element_boundary_from_subatomic, element_closure_ledger, formula_closure_ledger, control_like_partition_failure_disposition, cross_scale_compositional_closure
#   internal_surface: _periodic_nucleus_axis, _periodic_electron_axis, _derive_element_axes, _scale_projected_molecule_axes, _partitions, _formula_sets
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_cross_scale_compositional_closure
#   rollout: imported by tests/docs as a research evidence surface; no constructor or runtime behavior changes
#   rollback: remove this module and its tests/docs without changing locked molecule construction
#   requires: epac_subatomic_gonol, epac_public_gonol
#   since: 2026-09-07
#   unresolved: external physical interpretation; future alternate construction paths beyond the implemented EPAC stack
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: cross_scale_required_elements_are_locked_formula_inputs
#   given: the locked nine EPAC molecule-forming formulas
#   then: the closure audit enumerates exactly the distinct element constructions used by those formulas
#   class: evidence
#
# id: subatomic_to_element_boundary_refines_shell_axes
#   given: a subatomic element gonol receipt
#   then: the element boundary descriptor is derived by refining subatomic shell participants into electron axes and comparing to the bare periodic element receipt
#   class: construction
#
# id: cross_scale_element_refinement_is_path_independent
#   given: alternative admissible shell/electron traversal orders for subatomic refinement
#   then: the derived element boundary axes and descriptor are identical
#   class: correctness
#
# id: cross_scale_formula_closure_replays_from_subatomic_sources
#   given: any locked molecule formula
#   then: compatible subatomic-derived elements can be projected as molecule atom axes, local affixation steps are reproducible, and the composed descriptor equals the locked molecule descriptor
#   class: evidence
#
# id: subatomic_lifted_spiral_control_failure_is_classified
#   given: the existing subatomic_lifted_spiral_matches_control assertion
#   then: the audit classifies the exact-match flag as a stale or inapplicable partition-control fact rather than a compositional counterexample
#   class: doctrine
#
# id: cross_scale_promotion_blocks_descriptor_injection
#   given: a boundary descriptor bridge from subatomic to element or molecule
#   then: promotion requires source-derived axes and local operations, not numerical coincidence, hard-coded scaling, or an expected final descriptor
#   class: safety
# === END CONTRACTS ===


SURVIVED = "SURVIVED"
FALSIFIED = "FALSIFIED"
UNRESOLVED = "UNRESOLVED"
BLOCKED = "BLOCKED"

BoundaryCapacity = tuple[int, int, int]
LiftedSpiral = tuple[tuple[str, ...], tuple[str, ...], int]

REFINEMENT_OPERATION_ID = "epac.boundary.subatomic-shells-to-periodic-electron-axes"
MOLECULE_OPERATION_ID = "epac.boundary.closed-elements-to-molecule-affixiation"

DESCRIPTOR_SEMANTICS: Mapping[str, str] = {
    "descriptor": "B(R) = (3, d_boundary, c_boundary)",
    "interior_modes": "fixed three-turn double-cover mode count carried by the implemented EPAC receipts",
    "subatomic_d_boundary": "count of subatomic lifted-spiral axes: nucleus plus shell participants",
    "element_d_boundary": "count of periodic element lifted-spiral axes: nucleus plus electron axes",
    "molecule_d_boundary": "count of closed element gonol participant axes at molecule scale",
    "c_boundary": "count of declared valence attachment slots; bare subatomic and bare element states carry zero",
    "scale_rule": "a closed Public Gonol is atomic at any later participation, so lower-scale internal axes are refined or projected by an explicit local operation instead of conserved as molecule axes",
}


def required_element_symbols() -> tuple[str, ...]:
    """Return distinct symbols actually used by the locked formula set."""
    seen: list[str] = []
    for composition in MOLECULE_COMPOSITIONS.values():
        for symbol, _count in composition:
            if symbol not in seen:
                seen.append(symbol)
    return tuple(seen)


def _required_by_formulas(symbol: str) -> tuple[str, ...]:
    return tuple(
        formula
        for formula, composition in MOLECULE_COMPOSITIONS.items()
        if any(item_symbol == symbol for item_symbol, _count in composition)
    )


def _carried(item: ClosedPublicGonol | PublicGonolReceipt) -> dict[str, str]:
    gonol = item.gonol if isinstance(item, PublicGonolReceipt) else item
    return dict(gonol.carried_options)


def _participant_relations(receipt: PublicGonolReceipt) -> tuple[str, ...]:
    return tuple(participant.relation for participant in receipt.gonol.participants)


def _subatomic_nucleus(receipt: PublicGonolReceipt) -> ClosedPublicGonol:
    for participant in receipt.gonol.participants:
        if participant.relation == "epac.subatomic.nucleus":
            return participant
    raise ValueError(f"{receipt.source_id}: no subatomic nucleus participant")


def _subatomic_shells(receipt: PublicGonolReceipt) -> tuple[ClosedPublicGonol, ...]:
    shells = tuple(
        participant
        for participant in receipt.gonol.participants
        if participant.relation == "epac.atomic.shell"
        and participant.source_id.startswith("epac.subatomic.shell:")
    )
    if not shells:
        raise ValueError(f"{receipt.source_id}: no subatomic shell participants")
    return shells


def _periodic_nucleus_axis(subatomic_source_id: str) -> str:
    prefix = "epac.subatomic.nucleus:"
    if not subatomic_source_id.startswith(prefix):
        raise ValueError(f"not a subatomic nucleus source id: {subatomic_source_id}")
    return "epac.nucleus:" + subatomic_source_id[len(prefix) :]


def _periodic_electron_axis(subatomic_source_id: str) -> str:
    prefix = "epac.subatomic.electron:"
    if not subatomic_source_id.startswith(prefix):
        raise ValueError(f"not a subatomic electron source id: {subatomic_source_id}")
    return "epac.electron:" + subatomic_source_id[len(prefix) :]


def _derive_element_axes(
    receipt: PublicGonolReceipt,
    *,
    reverse_shells: bool = False,
    reverse_electrons: bool = False,
) -> tuple[str, ...]:
    """Refine subatomic shell axes into periodic element electron axes.

    This is the only subatomic-to-element boundary operation used by the audit.
    It reads the source receipt's participant tree and performs a namespace
    projection. It does not inspect the target element receipt or an expected
    descriptor.
    """
    axes: list[str] = [_periodic_nucleus_axis(_subatomic_nucleus(receipt).source_id)]
    shells = list(_subatomic_shells(receipt))
    if reverse_shells:
        shells.reverse()
    for shell in shells:
        electrons = [
            participant
            for participant in shell.participants
            if participant.relation == "epac.atomic.electron"
        ]
        if reverse_electrons:
            electrons.reverse()
        for electron in electrons:
            axes.append(_periodic_electron_axis(electron.source_id))
    return tuple(sorted(axes))


def _refinement_path_variants(receipt: PublicGonolReceipt) -> dict[str, tuple[str, ...]]:
    return {
        "declared": _derive_element_axes(receipt),
        "reverse_shells": _derive_element_axes(receipt, reverse_shells=True),
        "reverse_electrons": _derive_element_axes(receipt, reverse_electrons=True),
        "reverse_both": _derive_element_axes(
            receipt,
            reverse_shells=True,
            reverse_electrons=True,
        ),
    }


def derive_element_boundary_from_subatomic(
    receipt: PublicGonolReceipt,
) -> dict[str, Any]:
    """Derive the periodic element boundary descriptor from one subatomic receipt."""
    source_spiral = lifted_spiral_carried_on_subatomic(receipt)
    frames = tuple(source_spiral[0]) if source_spiral and len(source_spiral) == 3 else ()
    axes = _derive_element_axes(receipt)
    lifted_spiral: LiftedSpiral = (frames, axes, 0)
    return {
        "operation_id": REFINEMENT_OPERATION_ID,
        "source_boundary_capacity": boundary_capacity_from_subatomic_receipt(receipt),
        "source_lifted_spiral": source_spiral,
        "source_attachment_count_zero": bool(
            source_spiral and len(source_spiral) == 3 and int(source_spiral[2]) == 0
        ),
        "derived_lifted_spiral": lifted_spiral,
        "derived_boundary_capacity": (3, len(axes), 0),
        "derived_from": (
            "subatomic nucleus participant",
            "subatomic shell electron children",
            "local namespace projection",
        ),
        "descriptor_injected": False,
    }


@lru_cache(maxsize=None)
def element_closure_ledger(symbol: str, occurrence: int = 0) -> dict[str, Any]:
    """Return the subatomic-to-element provenance and closure ledger."""
    subatomic_receipt = construct_subatomic_gonol(symbol, occurrence=occurrence)
    bare_element_receipt = construct_element_gonol(symbol, occurrence=occurrence)
    derived = derive_element_boundary_from_subatomic(subatomic_receipt)

    bare_lifted_spiral = lifted_spiral_carried_on_element(bare_element_receipt)
    bare_boundary_capacity = boundary_capacity_from_element_receipt(bare_element_receipt)
    path_variants = _refinement_path_variants(subatomic_receipt)
    unique_variant_axes = {axes for axes in path_variants.values()}

    subatomic_options = _carried(subatomic_receipt)
    bare_element_options = _carried(bare_element_receipt)
    common_fields = (
        "symbol",
        "Z",
        "period",
        "group",
        "A",
        "electron-configuration",
        "valence-electrons",
    )
    common_field_matches = {
        field: subatomic_options.get(field) == bare_element_options.get(field)
        for field in common_fields
    }
    harmonic_survival_matches = (
        subatomic_options.get("harmonic-surviving", "none")
        == bare_element_options.get("harmonic-surviving", "none")
    )

    derived_lifted_spiral = derived["derived_lifted_spiral"]
    boundary_matches = derived["derived_boundary_capacity"] == bare_boundary_capacity
    axes_match = derived_lifted_spiral[1] == bare_lifted_spiral[1]
    frames_match = derived_lifted_spiral[0] == bare_lifted_spiral[0]
    path_independent = len(unique_variant_axes) == 1
    source_reproducible = bool(derived["source_attachment_count_zero"])
    field_compatible = all(common_field_matches.values()) and harmonic_survival_matches
    status = (
        SURVIVED
        if (
            boundary_matches
            and axes_match
            and frames_match
            and path_independent
            and source_reproducible
            and field_compatible
            and not derived["descriptor_injected"]
        )
        else FALSIFIED
    )

    return {
        "symbol": symbol,
        "occurrence": occurrence,
        "required_by_formulas": _required_by_formulas(symbol),
        "source_state": {
            "source_id": subatomic_receipt.source_id,
            "relation": subatomic_receipt.gonol.relation,
            "receipt_digest": subatomic_receipt.receipt_digest,
            "participant_relations": _participant_relations(subatomic_receipt),
            "source_boundary_capacity": derived["source_boundary_capacity"],
        },
        "local_operation": {
            "operation_id": REFINEMENT_OPERATION_ID,
            "rule": "refine each subatomic shell participant into its electron child axes, then project subatomic ids into periodic element ids",
            "uses_future_molecule": False,
            "uses_target_descriptor": False,
            "descriptor_injected": derived["descriptor_injected"],
        },
        "derived_element": {
            "lifted_spiral": derived_lifted_spiral,
            "boundary_capacity": derived["derived_boundary_capacity"],
        },
        "bare_element": {
            "source_id": bare_element_receipt.source_id,
            "relation": bare_element_receipt.gonol.relation,
            "receipt_digest": bare_element_receipt.receipt_digest,
            "lifted_spiral": bare_lifted_spiral,
            "boundary_capacity": bare_boundary_capacity,
        },
        "compatibility": {
            "boundary_capacity_matches_bare_element": boundary_matches,
            "axes_match_bare_element": axes_match,
            "frames_match_bare_element": frames_match,
            "common_field_matches": common_field_matches,
            "harmonic_survival_matches": harmonic_survival_matches,
            "source_attachment_count_zero": source_reproducible,
        },
        "path_independence": {
            "admissible_variants": tuple(path_variants),
            "variant_axes": path_variants,
            "path_independent": path_independent,
        },
        "status": status,
    }


def _scale_projected_molecule_axes(formula: str) -> tuple[str, ...]:
    axes: list[str] = []
    occurrence = 0
    for symbol, count in MOLECULE_COMPOSITIONS[formula]:
        for _ in range(count):
            axes.append(f"{symbol}#{occurrence}")
            occurrence += 1
    return tuple(sorted(axes))


def _element_instances_for_formula(formula: str) -> tuple[dict[str, Any], ...]:
    instances: list[dict[str, Any]] = []
    occurrence = 0
    for symbol, count in MOLECULE_COMPOSITIONS[formula]:
        for _ in range(count):
            ledger = element_closure_ledger(symbol, occurrence)
            instances.append(
                {
                    "symbol": symbol,
                    "occurrence": occurrence,
                    "molecule_axis": f"{symbol}#{occurrence}",
                    "derived_element_boundary_capacity": ledger["derived_element"][
                        "boundary_capacity"
                    ],
                    "bare_element_boundary_capacity": ledger["bare_element"][
                        "boundary_capacity"
                    ],
                    "compatible": ledger["status"] == SURVIVED,
                }
            )
            occurrence += 1
    return tuple(instances)


def _consume_introduced_instances(
    path: list[tuple[str, str]],
    instances: tuple[dict[str, Any], ...],
) -> bool:
    available: dict[str, int] = {}
    for instance in instances:
        if instance["compatible"]:
            available[instance["symbol"]] = available.get(instance["symbol"], 0) + 1
    for kind, symbol in path:
        if kind != "introduce":
            continue
        if available.get(symbol, 0) <= 0:
            return False
        available[symbol] -= 1
    return True


@lru_cache(maxsize=None)
def formula_closure_ledger(formula: str) -> dict[str, Any]:
    """Return the end-to-end subatomic-to-molecule closure ledger."""
    if formula not in MOLECULE_COMPOSITIONS:
        raise ValueError(f"formula {formula!r} is outside the declared run")

    construction = construct_molecule(formula)
    direct_b = boundary_capacity_carried_on_molecule(construction)
    direct_spiral = lifted_spiral_carried_on_molecule(construction)
    instances = _element_instances_for_formula(formula)
    projected_axes = _scale_projected_molecule_axes(formula)
    projected_axes_match_direct = projected_axes == direct_spiral[1]

    paths = generate_compositional_paths(formula)
    finals: list[BoundaryCapacity] = []
    path_consumption = []
    step_deltas: dict[tuple[str, str], set[tuple[int, int]]] = {}
    for path in paths:
        path_consumption.append(_consume_introduced_instances(path, instances))
        b: BoundaryCapacity = (3, 0, 0)
        for step in path:
            before = b
            b = apply_local_step(b, step)
            step_deltas.setdefault(step, set()).add(
                (b[1] - before[1], b[2] - before[2])
            )
        finals.append(b)

    unique_finals = tuple(sorted(set(finals)))
    path_independent = len(unique_finals) == 1
    local_steps_reproducible = all(len(deltas) == 1 for deltas in step_deltas.values())
    consumes_only_compatible_elements = all(path_consumption) if paths else False
    composed_b = unique_finals[0] if path_independent and unique_finals else None
    direct_composed_agreement = composed_b == direct_b
    status = (
        SURVIVED
        if (
            consumes_only_compatible_elements
            and projected_axes_match_direct
            and path_independent
            and local_steps_reproducible
            and direct_composed_agreement
        )
        else FALSIFIED
    )

    return {
        "formula": formula,
        "composition": MOLECULE_COMPOSITIONS[formula],
        "operation_id": MOLECULE_OPERATION_ID,
        "element_instances": instances,
        "molecule_projection": {
            "rule": "each compatible closed element gonol contributes one molecule-scale atom axis; affix steps add local ligand valence-slot counts",
            "projected_axes": projected_axes,
            "direct_molecule_axes": direct_spiral[1],
            "projected_axes_match_direct": projected_axes_match_direct,
            "uses_future_molecule_descriptor": False,
            "descriptor_injected": False,
        },
        "paths": {
            "count": len(paths),
            "unique_composed_boundary_capacity": unique_finals,
            "path_independent": path_independent,
            "local_steps_reproducible": local_steps_reproducible,
            "consumes_only_compatible_elements": consumes_only_compatible_elements,
        },
        "direct_boundary_capacity": direct_b,
        "composed_boundary_capacity": composed_b,
        "direct_composed_agreement": direct_composed_agreement,
        "status": status,
    }


def _partitions(values: Mapping[str, Any]) -> dict[Any, tuple[str, ...]]:
    groups: dict[Any, list[str]] = {}
    for formula, value in values.items():
        groups.setdefault(value, []).append(formula)
    return {
        value: tuple(sorted(formulas))
        for value, formulas in groups.items()
    }


def _formula_sets(partitions: Mapping[Any, tuple[str, ...]]) -> frozenset[frozenset[str]]:
    return frozenset(frozenset(group) for group in partitions.values())


def _subatomic_lifted_spiral_signature(formula: str) -> tuple[str, ...]:
    sigs: list[str] = []
    occurrence = 0
    for symbol, count in MOLECULE_COMPOSITIONS[formula]:
        for _ in range(count):
            receipt = construct_subatomic_gonol(symbol, occurrence=occurrence)
            frames, axes, attachment_count = lifted_spiral_carried_on_subatomic(receipt)
            sigs.append(f"{symbol}:{'|'.join(frames)};{','.join(axes)};{attachment_count}")
            occurrence += 1
    return tuple(sorted(sigs))


def control_like_partition_failure_disposition() -> dict[str, Any]:
    """Classify the subatomic lifted-spiral/control partition assertion."""
    constructions = construct_declared_molecules()
    subatomic_projection = {
        formula: _subatomic_lifted_spiral_signature(formula)
        for formula in MOLECULE_COMPOSITIONS
    }
    stoichiometric_control = {
        formula: matched_information_control(construction.invariants)
        for formula, construction in constructions.items()
    }
    subatomic_partitions = _partitions(subatomic_projection)
    control_partitions = _partitions(stoichiometric_control)
    matches_control = _formula_sets(subatomic_partitions) == _formula_sets(
        control_partitions
    )
    classification = (
        "stale_or_incorrect_control_assertion"
        if matches_control
        else "inapplicable_control_comparison"
    )
    return {
        "observed_subatomic_lifted_spiral_matches_control": matches_control,
        "classification": classification,
        "compositional_counterexample": False,
        "status": SURVIVED,
        "subatomic_projection_semantics": "bare subatomic lifted-spiral projection over every atom instance with stoichiometric multiplicity; attachment_count is zero",
        "control_semantics": "molecule-scale stoichiometric control over atom_count, center_symbol, and ligand_symbols",
        "reason": "the control exact-match flag is a partition-resemblance fact, not a direct/composed boundary-transition invariant; on the current nine-formula surface a prior false expectation is stale because both partitions are singletons",
        "subatomic_partition_count": len(subatomic_partitions),
        "control_partition_count": len(control_partitions),
    }


@lru_cache(maxsize=1)
def cross_scale_compositional_closure() -> dict[str, Any]:
    """Run the bounded EPAC cross-scale compositional-closure audit."""
    symbols = required_element_symbols()
    element_ledgers = {symbol: element_closure_ledger(symbol) for symbol in symbols}
    formula_ledgers = {
        formula: formula_closure_ledger(formula)
        for formula in MOLECULE_COMPOSITIONS
    }
    control_disposition = control_like_partition_failure_disposition()

    subatomic_to_element_status = (
        SURVIVED
        if all(ledger["status"] == SURVIVED for ledger in element_ledgers.values())
        else FALSIFIED
    )
    element_state_compatibility_status = (
        SURVIVED
        if all(
            ledger["compatibility"]["boundary_capacity_matches_bare_element"]
            and ledger["compatibility"]["axes_match_bare_element"]
            and ledger["compatibility"]["frames_match_bare_element"]
            and all(ledger["compatibility"]["common_field_matches"].values())
            and ledger["compatibility"]["harmonic_survival_matches"]
            for ledger in element_ledgers.values()
        )
        else FALSIFIED
    )
    end_to_end_status = (
        SURVIVED
        if all(ledger["status"] == SURVIVED for ledger in formula_ledgers.values())
        else FALSIFIED
    )
    boundary_capacity_status = (
        SURVIVED
        if (
            subatomic_to_element_status == SURVIVED
            and element_state_compatibility_status == SURVIVED
            and end_to_end_status == SURVIVED
            and not control_disposition["compositional_counterexample"]
        )
        else FALSIFIED
    )

    return {
        "decision": "EPAC boundary capacity composes across the presently implemented subatomic -> element -> molecule stack for the locked nine formulas, under the explicit shell-refinement and closed-gonol projection rules tested here.",
        "scope": {
            "formulas": tuple(MOLECULE_COMPOSITIONS),
            "required_elements": symbols,
            "hard_exclusions": (
                "no UCNS internal inspection",
                "no PCEA mapping",
                "no external physics or chemistry claim",
                "no continuum theorem",
                "no runtime encoding",
                "no locked evidence modification",
            ),
        },
        "descriptor_semantics": dict(DESCRIPTOR_SEMANTICS),
        "element_ledgers": element_ledgers,
        "formula_ledgers": formula_ledgers,
        "control_like_partition_failure": control_disposition,
        "statuses": {
            "subatomic_to_element_closure": subatomic_to_element_status,
            "element_state_compatibility": element_state_compatibility_status,
            "end_to_end_subatomic_to_molecule_closure": end_to_end_status,
            "boundary_capacity_compositionality": boundary_capacity_status,
        },
        "requires_more": (
            "external physical interpretation remains outside this EPAC evidence layer",
            "future alternate element or molecule construction paths must be added to this audit before claiming path independence over them",
            "no continuum or runtime channel encoding is derived here",
        ),
    }


__all__ = [
    "BLOCKED",
    "DESCRIPTOR_SEMANTICS",
    "FALSIFIED",
    "MOLECULE_OPERATION_ID",
    "REFINEMENT_OPERATION_ID",
    "SURVIVED",
    "UNRESOLVED",
    "control_like_partition_failure_disposition",
    "cross_scale_compositional_closure",
    "derive_element_boundary_from_subatomic",
    "element_closure_ledger",
    "formula_closure_ledger",
    "required_element_symbols",
]
