"""Completeness audit for the EPAC boundary-capacity probe inventory.

This module audits whether the probe inventory used by
``epac_boundary_quotient`` covers every already-declared EPAC operation whose
observable outcome can depend on boundary incidence, attachment availability,
coupling structure, or boundary state.

No new probe, coordinate, descriptor component, physics claim, PCEA bridge, or
UCNS continuum result is introduced. Existing structural readouts are evaluated
only with identifiers and labels excluded as discriminators.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from epac_evidence_cache import _independent_cached
from importlib.resources import files
from itertools import combinations
from pathlib import Path
from typing import Any, Callable, Mapping

from epac_boundary_nondegeneracy import BoundaryState, freeze_current_construction_surface
from epac_boundary_quotient import (
    BOUNDARY_CAPACITY_PROBES,
    boundary_capacity_quotient_report,
)
from epac_cross_scale_closure import FALSIFIED, SURVIVED, UNRESOLVED
from epac_dimensional_arity import (
    charged_structure_readout,
    quaternion_structure_readout,
    topology_structure_readout,
)
from epac_molecular import construct_declared_molecules
from epac_periodic import construct_element_gonol
from epac_subatomic.subatomic_gonol import construct_subatomic_gonol

# === MODULE_BUILD ===
# id: epac_boundary_probe_completeness
#   module_name: epac_boundary_probe_completeness
#   module_kind: experiment
#   summary: evidence-only audit of whether the current boundary-capacity quotient probe inventory covers every already-declared EPAC boundary-relevant operation on the frozen state surface
#   owner: The Interdependency
#   public_surface: declared_operation_ledger, omitted_boundary_operation_effects, boundary_probe_completeness_report
#   internal_surface: _declared_operations, _classify_operation, _state_contexts, _observable_effect, _identity_excluded_charged_structure, _combined_omitted_partition
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_boundary_probe_completeness
#   rollout: imported by tests/docs as a research evidence surface; no constructor, descriptor, quotient, or runtime behavior changes
#   rollback: remove this module and its tests/docs without changing the quotient or locked molecule construction
#   requires: epac_boundary_capacity_quotient
#   since: 2026-09-07
#   unresolved: future operation surfaces can refine this audit; structural readouts remain existing EPAC operations rather than boundary-capacity descriptor components
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: boundary_probe_audit_freezes_current_surface
#   given: the boundary-probe completeness audit is run
#   then: it evaluates only the 27 frozen subatomic, element, and locked molecule states already used by the quotient audit
#   class: evidence
#
# id: boundary_probe_audit_inventory_covers_declared_operations
#   given: the audit inventories EPAC operations
#   then: every exported callable from the bounded EPAC construction/evidence source files is classified as boundary-observing, boundary-transforming, provenance/identity only, internal/non-boundary, or ambiguous
#   class: safety
#
# id: boundary_probe_audit_uses_no_new_probe_or_descriptor
#   given: omitted operations are evaluated
#   then: only existing EPAC operation outputs are added to the comparison signature and B remains exactly three components
#   class: safety
#
# id: boundary_probe_audit_excludes_identity_discriminators
#   given: existing structural outputs contain concrete ids or labels
#   then: same-B distinctions are counted only after source ids, labels, axis names, and coupling ids are excluded from the observable
#   class: safety
#
# id: boundary_probe_audit_imports_no_ucns_or_pcea
#   given: the boundary-probe completeness audit module is loaded
#   then: it has no direct UCNS or PCEA import; it consumes only EPAC-local evidence surfaces
#   class: safety
#
# id: boundary_probe_audit_reruns_same_B_and_unequal_B_comparisons
#   given: an existing boundary-relevant operation is not represented in the current quotient probe inventory
#   then: the audit reruns the six same-B collision groups and all unequal-B comparisons with that existing observable
#   class: correctness
#
# id: boundary_probe_audit_reports_partition_change
#   given: omitted existing observables are added to the quotient comparison
#   then: the audit reports whether the 16-class quotient partition changes
#   class: evidence
#
# id: boundary_probe_audit_classifies_completeness
#   given: all operation ledger rows and omitted-observable effects
#   then: the aggregate status is FALSIFIED for an observed quotient-refining counterexample, otherwise UNRESOLVED for ambiguous operation semantics, and SURVIVED only when neither remains
#   class: correctness
# === END CONTRACTS ===


EPAC_ROOT = Path(__file__).resolve().parent

BOUNDARY_OBSERVING = "boundary-observing"
BOUNDARY_TRANSFORMING = "boundary-transforming"
PROVENANCE_IDENTITY = "provenance/identity only"
INTERNAL_NON_BOUNDARY = "internal/non-boundary"
AMBIGUOUS = "ambiguous"

OperationRecord = dict[str, Any]
StateContext = dict[str, Any]
Observable = Any
ObservableFn = Callable[[StateContext], Observable]

OPERATION_SOURCE_FILES = (
    "epac_evidence_cache.py",
    "viz/__init__.py",
    "subatomic/__init__.py",
    "data/__init__.py",
    "epac_atomic.py",
    "epac_ucns_provenance.py",
    "viz/spiral_viz.py",
    "viz/cli.py",
    "viz/__main__.py",
    "epac_public_gonol.py",
    "epac_dimensional_arity.py",
    "epac_periodic.py",
    "epac_molecular.py",
    "epac_cross_scale_closure.py",
    "epac_boundary_nondegeneracy.py",
    "epac_boundary_quotient.py",
    "epac_boundary_minimal_refinement.py",
    "epac_boundary_probe_completeness.py",
    "epac_comparison.py",
    "subatomic/subatomic_gonol.py",
    "subatomic/element_affixiation_candidate.py",
    "subatomic/extended_atomic.py",
    "subatomic/nuclear_harmonic_candidates.py",
    "subatomic/symbol_coupling.py",
)

STRUCTURAL_OBSERVER_NAMES = frozenset(
    {
        "charged_structure_readout",
        "topology_structure_readout",
        "quaternion_structure_readout",
        "geometry_from_declared_couplings",
        "structure_from_charged_couplings",
        "degree_relations",
        "oriented_instance_couplings",
        "local_three_structures",
        "quaternion_of_local_three",
        "quaternions_from_declared_couplings",
        "has_declared_coupling",
        "instances_missing_oriented_hub_coupling",
        "require_every_instance_has_oriented_hub_coupling",
    }
)

BOUNDARY_CAPACITY_OPERATION_NAMES = frozenset(
    {
        "boundary_capacity_from_subatomic_receipt",
        "boundary_capacity_from_element_receipt",
        "boundary_capacity_from_receipt",
        "boundary_capacity_carried_on_molecule",
        "boundary_capacity_transition_for_molecule",
        "boundary_capacity_behavior_signature",
        "boundary_capacity_quotient_report",
        "boundary_capacity_quotient_test",
        "boundary_capacity_descriptor_sufficiency_sweep",
        "boundary_capacity_information_loss_localization",
        "boundary_descriptor_nondegeneracy_report",
        "build_counterfactual_neighborhood",
        "freeze_current_construction_surface",
        "observed_local_boundary_deltas",
        "predict_boundary_capacity_from_source_and_op",
        "source_element_boundary_capacities",
        "declared_valence_attachment_count",
        "apply_local_step",
        "accumulate_from_local_path",
        "compositional_boundary_closure",
        "derive_element_boundary_from_subatomic",
        "element_closure_ledger",
        "formula_closure_ledger",
        "cross_scale_compositional_closure",
    }
)

CONSTRUCTION_OPERATION_NAMES = frozenset(
    {
        "construct_public_gonol",
        "construct_subatomic_gonol",
        "construct_element_gonol",
        "construct_periodic_table",
        "construct_molecule",
        "construct_declared_molecules",
        "Dimension",
        "Coupling",
        "CouplingProof",
        "DimensionalSpace",
        "dimension",
        "coupling",
        "space",
        "install_proven_coupling",
    }
)

BOUNDARY_REPRESENTED_NAMES = BOUNDARY_CAPACITY_OPERATION_NAMES | frozenset(
    {
        "lifted_spiral_carried_on_subatomic",
        "lifted_spiral_carried_on_element",
        "lifted_spiral_from_receipt",
        "lifted_spiral_carried_on_molecule",
        "BoundaryState",
        "BoundaryMutation",
    }
)

PROVENANCE_NAMES = frozenset(
    {
        "ClosedPublicGonol",
        "PublicGonolReceipt",
        "PublicGonolConstructionError",
        "DimensionalArityError",
        "canonical_receipt_bytes",
        "replay_public_gonol",
        "replay_subatomic_gonol",
        "replay_element_gonol",
        "replay_molecule",
        "replay_element",
        "replay_symbol_coupling",
        "ElementCandidate",
        "HarmonicCandidate",
        "element_receipt",
        "harmonic_receipt",
        "recurrence_test",
        "atomic_record",
        "iter_table",
        "atomic_of",
        "symbol_of",
        "carried",
        "subatomic_receipt_record",
        "matched_information_control",
        "harmonic_survival_from_receipt",
        "harmonic_survival_carried_on_molecule",
        "per_symbol_harmonic_survival_from_receipt",
        "per_symbol_harmonic_survival_carried_on_molecule",
        "harmonic_survival_carried_on_element",
        "control_like_partition_failure_disposition",
        "required_element_symbols",
        "construction_sources_omit_sealed_labels",
        "_harmonic_survival_signature",
        "_subatomic_harmonic_survival_signature",
        "_periodic_element_harmonic_survival_signature",
        "_per_symbol_harmonic_survival_from_molecule",
        "_quantify_distinguishing_power",
        "construct_symbol_gonol",
        "couple_symbol",
        "affixiate_element",
    }
)

OMITTED_OBSERVABLE_OPERATION_NAMES = frozenset(
    {
        "charged_structure_readout",
        "topology_structure_readout",
        "quaternion_structure_readout",
        "geometry_from_declared_couplings",
        "structure_from_charged_couplings",
        "degree_relations",
        "oriented_instance_couplings",
        "local_three_structures",
        "quaternion_of_local_three",
        "quaternions_from_declared_couplings",
        "has_declared_coupling",
        "instances_missing_oriented_hub_coupling",
        "require_every_instance_has_oriented_hub_coupling",
    }
)


def _module_label(relative_path: str) -> str:
    parts = relative_path[:-3].split("/")
    parts[0] = {"subatomic": "epac_subatomic", "viz": "epac_viz", "data": "epac_data"}.get(parts[0], parts[0])
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _declared_names(path: Path, seen: tuple[Path, ...] = ()) -> tuple[str, ...]:
    path = path.resolve()
    if path in seen:
        raise ValueError("cyclic public re-export inventory")
    seen = (*seen, path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top_level_defs = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    exported: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "__all__":
                continue
            try:
                exported = list(ast.literal_eval(node.value))
            except (SyntaxError, ValueError):
                exported = []
    if exported:
        # Follow explicitly exported relative bindings without importing code.
        # Initializer aliases are public addresses even when the implementation
        # already appears under the defining module's address.
        public_callables = set(top_level_defs)
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.level or not node.module:
                continue
            base = path.parent
            for _ in range(node.level - 1):
                base = base.parent
            module_path = base.joinpath(*node.module.split("."))
            target = module_path.with_suffix(".py")
            if not target.is_file():
                target = module_path / "__init__.py"
            selected = [alias for alias in node.names if (alias.asname or alias.name) in exported]
            if not selected:
                continue
            definitions = set(_declared_names(target, seen))
            public_callables.update(alias.asname or alias.name for alias in selected if alias.name in definitions)
        return tuple(name for name in exported if name in public_callables)
    return tuple(name for name in top_level_defs if not name.startswith("_"))


def _declared_operations() -> tuple[dict[str, str], ...]:
    operations: list[dict[str, str]] = []
    for relative_path in OPERATION_SOURCE_FILES:
        package = {"subatomic": "epac_subatomic", "viz": "epac_viz", "data": "epac_data"}.get(relative_path.split("/", 1)[0])
        path = (Path(str(files(package).joinpath(relative_path.split("/", 1)[1])))
                if package else EPAC_ROOT / relative_path)
        module = _module_label(relative_path)
        for name in _declared_names(path):
            operations.append(
                {
                    "operation": f"{module}.{name}",
                    "module": module,
                    "name": name,
                    "path": relative_path,
                }
            )
    return tuple(sorted(operations, key=lambda item: item["operation"]))


def _classify_operation(module: str, name: str) -> str:
    if name in _UNMAPPED_OPERATION_PROBES:
        return AMBIGUOUS
    if module in {"epac_atomic", "epac_ucns_provenance", "epac_viz", "epac_viz.spiral_viz", "epac_viz.cli"}:
        return AMBIGUOUS

    if name in OmittedButNomenclature.NAMES:
        return PROVENANCE_IDENTITY
    if name in STRUCTURAL_OBSERVER_NAMES:
        return BOUNDARY_OBSERVING
    if name in BOUNDARY_CAPACITY_OPERATION_NAMES:
        if name in {
            "apply_local_step",
            "accumulate_from_local_path",
            "build_counterfactual_neighborhood",
            "derive_element_boundary_from_subatomic",
            "compositional_boundary_closure",
        }:
            return BOUNDARY_TRANSFORMING
        return BOUNDARY_OBSERVING
    if name in CONSTRUCTION_OPERATION_NAMES:
        return BOUNDARY_TRANSFORMING
    if name in {"lifted_spiral_carried_on_subatomic", "lifted_spiral_carried_on_element",
                "lifted_spiral_from_receipt", "lifted_spiral_carried_on_molecule"}:
        return BOUNDARY_OBSERVING
    if name in PROVENANCE_NAMES:
        return PROVENANCE_IDENTITY
    if name in {"get_compositional_local_steps", "generate_compositional_paths"}:
        return BOUNDARY_TRANSFORMING
    if name in {"compare_after_construction"}:
        return BOUNDARY_OBSERVING
    return AMBIGUOUS


class OmittedButNomenclature:
    NAMES = frozenset(
        {
            "construct_symbol_gonol",
            "couple_symbol",
            "replay_symbol_coupling",
        }
    )


def _is_currently_probed(module: str, name: str, relevance: str) -> bool | None:
    if relevance not in {BOUNDARY_OBSERVING, BOUNDARY_TRANSFORMING}:
        return None
    if name in OMITTED_OBSERVABLE_OPERATION_NAMES:
        return False
    if name == "compare_after_construction":
        return False
    return True


def _represented_by(name: str, currently_probed: bool | None, relevance: str) -> str:
    if relevance == AMBIGUOUS:
        return "unresolved_boundary_relevance"
    if currently_probed is None:
        return "not_applicable"
    if currently_probed:
        if name in BOUNDARY_REPRESENTED_NAMES:
            return "current_boundary_capacity_probe_inventory"
        if name in CONSTRUCTION_OPERATION_NAMES:
            return "B_projection_of_existing_construction_output"
        return "B_valued_transition_or_report"
    if name in OMITTED_OBSERVABLE_OPERATION_NAMES:
        return "omitted_existing_coupling_structure_observable"
    return "omitted_aggregate_existing_observer"


def _observable_carried(name: str, relevance: str) -> str:
    if relevance == AMBIGUOUS:
        return "unresolved_boundary_relevance"
    if relevance not in {BOUNDARY_OBSERVING, BOUNDARY_TRANSFORMING}:
        return "not_applicable"
    if name in OMITTED_OBSERVABLE_OPERATION_NAMES:
        return "identifier-excluded declared coupling/incidence/charge/topology observable"
    if "lifted_spiral" in name:
        return "lifted-spiral frames, boundary axes, and attachment count; identifier-excluded quotient keeps count response"
    if "boundary_capacity" in name or name.startswith("boundary_"):
        return "B=(interior_modes,d_boundary,c_boundary) or B-valued probe signature"
    if name in {"apply_local_step", "accumulate_from_local_path"}:
        return "B-valued local transition delta"
    if name in CONSTRUCTION_OPERATION_NAMES:
        return "constructed boundary state and its B-valued projection"
    return "existing aggregate observer over frozen construction records"


def _strip_identifiers(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith("epac.") or "#" in value:
            return "<id>"
        return value
    if isinstance(value, Mapping):
        return tuple(
            sorted((str(key), _strip_identifiers(item)) for key, item in value.items())
        )
    if isinstance(value, (tuple, list)):
        return tuple(_strip_identifiers(item) for item in value)
    return value


@lru_cache(maxsize=1)
def _state_contexts() -> dict[str, StateContext]:
    surface = freeze_current_construction_surface()
    constructions = construct_declared_molecules()
    contexts: dict[str, StateContext] = {}
    for state_id, state in surface["states"].items():
        structure = None
        source = None
        if state.scale == "molecule":
            source = constructions[state.source]
            structure = source.invariants["dimensional_geometry"]["structure"]
        elif state.scale == "element":
            source = construct_element_gonol(state.source)
            structure = source.gonol.structure
        elif state.scale == "subatomic":
            source = construct_subatomic_gonol(state.source)
            structure = source.gonol.structure
        contexts[state_id] = {
            "state": state,
            "structure": structure,
            "source": source,
        }
    return contexts


def _identity_excluded_topology(context: StateContext) -> Observable:
    structure = context["structure"]
    if not structure:
        return ("no_structure",)
    return topology_structure_readout(structure)


def _identity_excluded_charged_structure(context: StateContext) -> Observable:
    structure = context["structure"]
    if not structure:
        return ("no_structure",)
    return _strip_identifiers(charged_structure_readout(structure))


def _identity_excluded_quaternion_structure(context: StateContext) -> Observable:
    structure = context["structure"]
    if not structure:
        return ("no_structure",)
    raw = quaternion_structure_readout(structure)
    return tuple(sorted(_strip_identifiers(item[0]) for item in raw))


# Only these three mappings call the named operation on the declared structure.
# The other structural operations need their own argument selection and actual
# result/error normalization before an effect can be attributed to that operation.
OMITTED_OBSERVABLES: Mapping[str, ObservableFn] = {
    "charged_structure_readout": _identity_excluded_charged_structure,
    "topology_structure_readout": _identity_excluded_topology,
    "quaternion_structure_readout": _identity_excluded_quaternion_structure,
}
_UNMAPPED_OPERATION_PROBES = OMITTED_OBSERVABLE_OPERATION_NAMES - OMITTED_OBSERVABLES.keys()


def _classes_by_signature(signatures: Mapping[str, Any]) -> dict[Any, tuple[str, ...]]:
    classes: dict[Any, list[str]] = {}
    for state_id, signature in signatures.items():
        classes.setdefault(signature, []).append(state_id)
    return {
        key: tuple(sorted(state_ids))
        for key, state_ids in classes.items()
    }


def _observable_effect(operation_name: str, observable: ObservableFn) -> dict[str, Any]:
    contexts = _state_contexts()
    quotient = boundary_capacity_quotient_report()
    states: Mapping[str, BoundaryState] = {
        state_id: context["state"] for state_id, context in contexts.items()
    }
    outputs = {
        state_id: observable(context)
        for state_id, context in contexts.items()
    }
    augmented_signatures = {
        state_id: (states[state_id].b, outputs[state_id])
        for state_id in states
    }
    augmented_classes = _classes_by_signature(augmented_signatures)

    same_b_group_results = []
    same_b_distinguished_pairs = []
    for collision in quotient["state_sufficiency_collisions"]:
        state_ids = tuple(collision["state_ids"])
        output_groups = _classes_by_signature(
            {state_id: outputs[state_id] for state_id in state_ids}
        )
        split = len(output_groups) > 1
        if split:
            for left_id, right_id in combinations(state_ids, 2):
                if outputs[left_id] != outputs[right_id]:
                    same_b_distinguished_pairs.append(
                        {
                            "left": left_id,
                            "right": right_id,
                            "B": states[left_id].b,
                            "left_observable": outputs[left_id],
                            "right_observable": outputs[right_id],
                        }
                    )
        same_b_group_results.append(
            {
                "B": collision["B"],
                "state_ids": state_ids,
                "split_by_operation": split,
                "observable_partition": tuple(output_groups.values()),
            }
        )

    unequal_b_compared = 0
    unequal_b_same_observable = 0
    for left_id, right_id in combinations(states, 2):
        if states[left_id].b == states[right_id].b:
            continue
        unequal_b_compared += 1
        if outputs[left_id] == outputs[right_id]:
            unequal_b_same_observable += 1

    baseline_class_count = len(quotient["B_classes"])
    augmented_class_count = len(augmented_classes)
    return {
        "operation_name": operation_name,
        "baseline_class_count": baseline_class_count,
        "augmented_class_count": augmented_class_count,
        "quotient_partition_changes": augmented_class_count != baseline_class_count,
        "same_B_collision_group_results": tuple(same_b_group_results),
        "same_B_distinguished_pair_count": len(same_b_distinguished_pairs),
        "same_B_distinguished_pair_examples": tuple(same_b_distinguished_pairs[:12]),
        "unequal_B_comparison_count": unequal_b_compared,
        "unequal_B_operation_only_equal_count": unequal_b_same_observable,
        "identity_discriminators_excluded": True,
    }


def _combined_omitted_partition(effects: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    contexts = _state_contexts()
    states = {state_id: context["state"] for state_id, context in contexts.items()}
    outputs_by_operation = {
        operation_name: {
            state_id: OMITTED_OBSERVABLES[operation_name](context)
            for state_id, context in contexts.items()
        }
        for operation_name in effects
        if operation_name in OMITTED_OBSERVABLES
    }
    signatures = {
        state_id: (
            states[state_id].b,
            tuple(
                (operation_name, operation_outputs[state_id])
                for operation_name, operation_outputs in sorted(outputs_by_operation.items())
            ),
        )
        for state_id in states
    }
    classes = _classes_by_signature(signatures)
    baseline_class_count = len(boundary_capacity_quotient_report()["B_classes"])
    return {
        "baseline_class_count": baseline_class_count,
        "combined_augmented_class_count": len(classes),
        "quotient_partition_changes": len(classes) != baseline_class_count,
        "class_partition": tuple(classes.values()),
    }


@_independent_cached(maxsize=1)
def omitted_boundary_operation_effects() -> dict[str, dict[str, Any]]:
    """Evaluate omitted existing boundary observables on frozen states."""
    effects: dict[str, dict[str, Any]] = {}
    for operation_name, observable in OMITTED_OBSERVABLES.items():
        effects[operation_name] = _observable_effect(operation_name, observable)
    return effects


@_independent_cached(maxsize=1)
def declared_operation_ledger() -> tuple[OperationRecord, ...]:
    """Classify declared EPAC operations against the current quotient probes."""
    effects = omitted_boundary_operation_effects()
    records: list[OperationRecord] = []
    for raw in _declared_operations():
        relevance = _classify_operation(raw["module"], raw["name"])
        currently_probed = _is_currently_probed(raw["module"], raw["name"], relevance)
        effect = effects.get(raw["name"])
        can_distinguish_same_b = (
            None if relevance == AMBIGUOUS else
            bool(effect and effect["same_B_distinguished_pair_count"] > 0)
            if currently_probed is False
            else False
        )
        records.append(
            {
                **raw,
                "boundary_relevance": relevance,
                "currently_probed": currently_probed,
                "observable_carried": _observable_carried(raw["name"], relevance),
                "represented_by": _represented_by(raw["name"], currently_probed, relevance),
                "can_distinguish_same_B_states": can_distinguish_same_b,
                "effect_on_quotient": (
                    "unresolved_boundary_relevance" if relevance == AMBIGUOUS else
                    "refines_quotient_partition"
                    if can_distinguish_same_b
                    else (
                        "no_partition_change"
                        if currently_probed is False
                        else "already_represented_or_not_applicable"
                    )
                ),
            }
        )
    return tuple(records)


@_independent_cached(maxsize=1)
def boundary_probe_completeness_report() -> dict[str, Any]:
    """Run the EPAC boundary-probe completeness audit."""
    surface = freeze_current_construction_surface()
    quotient = boundary_capacity_quotient_report()
    effects = omitted_boundary_operation_effects()
    combined = _combined_omitted_partition(effects)
    ledger = declared_operation_ledger()
    ambiguous = tuple(
        row for row in ledger if row["boundary_relevance"] == AMBIGUOUS
    )
    boundary_relevant = tuple(
        row
        for row in ledger
        if row["boundary_relevance"] in {BOUNDARY_OBSERVING, BOUNDARY_TRANSFORMING}
    )
    omitted = tuple(
        row
        for row in boundary_relevant
        if row["currently_probed"] is False
    )
    omitted_distinguishing = tuple(
        row for row in omitted if row["can_distinguish_same_B_states"]
    )

    # A known counterexample remains falsifying even while other relevance is unknown.
    if omitted_distinguishing or combined["quotient_partition_changes"]:
        aggregate = FALSIFIED
    elif ambiguous:
        aggregate = UNRESOLVED
    else:
        aggregate = SURVIVED

    statuses = {
        "declared_operation_inventory": SURVIVED,
        "ambiguous_boundary_semantics": UNRESOLVED if ambiguous else SURVIVED,
        "omitted_boundary_relevant_operations": (
            FALSIFIED if omitted_distinguishing else SURVIVED
        ),
        "quotient_partition_stability_under_omitted_existing_observables": (
            FALSIFIED if combined["quotient_partition_changes"] else SURVIVED
        ),
        "boundary_probe_completeness": aggregate,
    }

    return {
        "decision": (
            "FALSIFIED: the current boundary-capacity quotient probe inventory "
            "omits already-declared EPAC coupling-structure readouts. With "
            "identifiers and labels excluded, those existing observables refine "
            "the 16-class B quotient."
            if aggregate == FALSIFIED
            else (
                "UNRESOLVED: at least one declared EPAC operation has ambiguous boundary semantics."
                if aggregate == UNRESOLVED
                else "SURVIVED: no omitted existing boundary-relevant operation refines the quotient."
            )
        ),
        "surface": {
            "surface_id": surface["surface_id"],
            "state_count": len(surface["states"]),
            "state_ids": surface["state_ids"],
            "frozen_before_audit": surface["frozen_before_controls"],
        },
        "current_probe_inventory": {
            "probe_kinds": BOUNDARY_CAPACITY_PROBES,
            "baseline_class_count": len(quotient["B_classes"]),
            "equal_B_pair_count": quotient["equal_B_pair_count"],
            "state_sufficiency_collision_group_count": len(
                quotient["state_sufficiency_collisions"]
            ),
        },
        "operation_inventory": {
            "source_files": OPERATION_SOURCE_FILES,
            "operation_count": len(ledger),
            "boundary_relevant_count": len(boundary_relevant),
            "omitted_boundary_relevant_count": len(omitted),
            "omitted_distinguishing_count": len(omitted_distinguishing),
            "ambiguous_count": len(ambiguous),
        },
        "operation_ledger": ledger,
        "omitted_operation_effects": effects,
        "unmapped_operation_probes": {
            name: "hmmm: no declared argument mapping and actual result/error normalization"
            for name in sorted(_UNMAPPED_OPERATION_PROBES)
        },
        "combined_omitted_observable_effect": combined,
        "omitted_distinguishing_operations": tuple(
            row["operation"] for row in omitted_distinguishing
        ),
        "statuses": statuses,
        "requires_more": (
            "the prior quotient remains valid only relative to its narrower probe inventory",
            "B is not complete for the full presently declared EPAC operational surface",
            "do not add a descriptor component in this audit",
            "state identity, source labels, concrete axis names, and coupling ids remain excluded as discriminators",
            "no PCEA mapping, UCNS continuum theorem, runtime encoding, or external physical claim is made",
        ),
    }


__all__ = [
    "AMBIGUOUS",
    "BOUNDARY_OBSERVING",
    "BOUNDARY_TRANSFORMING",
    "INTERNAL_NON_BOUNDARY",
    "PROVENANCE_IDENTITY",
    "boundary_probe_completeness_report",
    "declared_operation_ledger",
    "omitted_boundary_operation_effects",
]
