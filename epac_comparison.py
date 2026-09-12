"""Sealed-shape comparison after EPAC Public Gonol construction.

The three-dimensional structure is the charged oriented couplings plus degree.
This module opens known chemistry only after those structures exist. It does
not import VSEPR names into construction.

Usage guidance
--------------
    from epac_comparison import compare_after_construction

    record = compare_after_construction()
    print(record["standings"])
"""

from __future__ import annotations

import json
from importlib.resources import files
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from epac_dimensional_arity import charged_structure_readout, topology_structure_readout
from epac_molecular import (
    MOLECULE_COMPOSITIONS,
    boundary_capacity_carried_on_molecule,
    boundary_capacity_descriptor_sufficiency_sweep,
    boundary_capacity_information_loss_localization,
    boundary_capacity_quotient_test,
    boundary_capacity_minimal_refinement_audit,
    epac_probe_relativity_formalization,
    epac_representation_audit,
    boundary_capacity_transition_for_molecule,
    compositional_boundary_closure,
    construct_declared_molecules,
    harmonic_survival_carried_on_molecule,
    lifted_spiral_carried_on_molecule,
    matched_information_control,
    observed_local_boundary_deltas,
    per_symbol_harmonic_survival_carried_on_molecule,
)

# Lifted spiral population (from the UCNS-framed gonol evidence)
from epac_viz.spiral_viz import extract_spiral_scene, extract_full_spiral_population

from epac_periodic import (
    boundary_capacity_from_element_receipt,
    construct_element_gonol,
    harmonic_survival_carried_on_element,
    lifted_spiral_carried_on_element,
)

from epac_subatomic import nuclear_harmonic_candidates as harmonics
from epac_subatomic import subatomic_gonol
from epac_subatomic.subatomic_gonol import (
    boundary_capacity_from_subatomic_receipt,
    lifted_spiral_carried_on_subatomic,
)


EPAC_ROOT = Path(__file__).resolve().parent
SEALED_PATH = files("epac_data").joinpath("sealed_known_molecular_geometry.json")
SEALED_SHAPE_LABELS = ("linear", "bent", "trigonal-pyramidal", "trigonal-planar", "tetrahedral", "vsepr")
CONSTRUCTION_FILES = (
    "epac_atomic.py",
    "epac_dimensional_arity.py",
    "epac_molecular.py",
    "epac_periodic.py",
    "epac_public_gonol.py",
)

# Frozen original preregistered set for sealed-shape prediction policy.
# Sealed standings and pairwise comparisons use this frozen population.
# Readout population summaries may cover every constructed formula, even when
# the sealed file or constructed set is enlarged for broader experiments.
ORIGINAL_PREREG = frozenset({"H2", "H2O", "NH3", "CH4", "CO2"})


def construction_sources_omit_sealed_labels(root: Path = EPAC_ROOT) -> tuple[str, ...]:
    hits: list[str] = []
    for name in CONSTRUCTION_FILES:
        text = (root / name).read_text(encoding="utf-8").lower()
        for label in SEALED_SHAPE_LABELS:
            if label in text:
                hits.append(f"{name}:{label}")
    return tuple(hits)


def _partitions(values: Mapping[str, Any]) -> dict[Any, tuple[str, ...]]:
    groups: dict[Any, list[str]] = defaultdict(list)
    for formula, value in values.items():
        groups[value].append(formula)
    return {key: tuple(sorted(formulas)) for key, formulas in groups.items()}


def _formula_sets(partitions: Mapping[Any, tuple[str, ...]]) -> frozenset[frozenset[str]]:
    return frozenset(frozenset(group) for group in partitions.values())


def _standing(
    readout: Mapping[str, Any],
    known_shapes: Mapping[str, str],
    control: Mapping[str, Any],
) -> str:
    """Preregistered shape-class prediction standing.

    SURVIVED only if the readout is invariant inside each sealed shape class,
    distinguishes different sealed classes, and is not the matched-information
    control.
    """

    readout = {formula: readout[formula] for formula in known_shapes}
    control = {formula: control[formula] for formula in known_shapes}
    by_shape: dict[str, set[Any]] = defaultdict(set)
    for formula, shape in known_shapes.items():
        by_shape[shape].add(readout[formula])
    splits_a_class = any(len(values) > 1 for values in by_shape.values())
    collapsed_classes = False
    shapes = list(by_shape)
    for i, left in enumerate(shapes):
        for right in shapes[i + 1 :]:
            if by_shape[left] & by_shape[right]:
                collapsed_classes = True
    if splits_a_class or collapsed_classes:
        return "FALSIFIED"
    if _formula_sets(_partitions(readout)) == _formula_sets(_partitions(control)):
        return "FALSIFIED"
    if _formula_sets(_partitions(readout)) == _formula_sets(_partitions(known_shapes)):
        return "SURVIVED"
    return "UNRESOLVED"


def _pairwise_counts(
    known_shapes: Mapping[str, str],
    signature: Mapping[str, Any],
) -> dict[str, int]:
    """Count pairwise agreements for a signature vs known shape classes.

    Returns counts for the four cells of the pair contingency table.
    """
    formulas = list(known_shapes.keys())
    tp = fp = fn = tn = 0  # tp = same_known and same_sig, etc.
    for i in range(len(formulas)):
        for j in range(i + 1, len(formulas)):
            f1, f2 = formulas[i], formulas[j]
            same_known = known_shapes[f1] == known_shapes[f2]
            same_sig = signature[f1] == signature[f2]
            if same_known and same_sig:
                tp += 1
            elif same_known and not same_sig:
                fp += 1  # splits a known class
            elif not same_known and same_sig:
                fn += 1  # collapses across known classes
            else:
                tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "total_pairs": tp + fp + fn + tn}


def _harmonic_survival_signature(formula: str) -> tuple[str, ...]:
    """Molecule-level union of surviving nuclear harmonic candidate ids.

    For each constituent symbol, include every candidate for which at least
    one of its isotope participants for that symbol satisfies the declared
    recurrence. This is the same survival rule used inside subatomic gonols.
    """
    comp = MOLECULE_COMPOSITIONS.get(formula, ())
    survivors: set[str] = set()
    for sym, _count in comp:
        for cand in harmonics.CANDIDATES:
            recmap = harmonics.recurrence_test(cand)
            for participant in cand.participants:
                if participant.startswith(f"{sym}-") and recmap.get(participant, False):
                    survivors.add(cand.candidate_id)
                    break
    return tuple(sorted(survivors))


def _subatomic_harmonic_survival_signature(formula: str) -> tuple[str, ...]:
    """Molecule-level harmonic survival read from constructed subatomic gonols.

    Uses the "harmonic-surviving" carried option produced by subatomic_gonol
    for each constituent symbol. This makes the nuclear harmonic layer a
    carried fact inside the element gonols rather than a side computation.
    """
    comp = MOLECULE_COMPOSITIONS.get(formula, ())
    survivors: set[str] = set()
    for sym, _count in comp:
        receipt = subatomic_gonol.construct_subatomic_gonol(sym)
        carried = dict(receipt.gonol.carried_options)
        hs = carried.get("harmonic-surviving", "none")
        if hs and hs != "none":
            for c in hs.split(","):
                survivors.add(c)
    return tuple(sorted(survivors))


def _periodic_element_harmonic_survival_signature(formula: str) -> tuple[str, ...]:
    """Molecule-level harmonic survival read from native periodic element gonols.

    Uses the "harmonic-surviving" carried option now attached to every
    periodic element gonol (sourced from the subatomic layer at construction).
    This is the view through the primary EPAC element gonol path.
    """
    comp = MOLECULE_COMPOSITIONS.get(formula, ())
    survivors: set[str] = set()
    for sym, _count in comp:
        receipt = construct_element_gonol(sym)
        hs = harmonic_survival_carried_on_element(receipt)
        for c in hs:
            survivors.add(c)
    return tuple(sorted(survivors))


def _periodic_element_lifted_spiral_signature(formula: str) -> tuple:
    """Molecule-level lifted spiral signature read from native periodic element gonols.

    Uses the "lifted-spiral" carried option now attached to every
    periodic element gonol (pure projection of the framed Möbius root-loop
    witnessed at element construction). This is the bare-element view.
    """
    comp = MOLECULE_COMPOSITIONS[formula]
    sigs = []
    occurrence = 0
    for sym, count in comp:
        for _ in range(count):
            receipt = construct_element_gonol(sym, occurrence=occurrence)
            value = lifted_spiral_carried_on_element(receipt)
            sigs.append(f"{sym}:{'|'.join(value[0])};{','.join(value[1])};{value[2]}")
            occurrence += 1
    return tuple(sorted(sigs))


def _subatomic_lifted_spiral_signature(formula: str) -> tuple:
    """Molecule-level lifted spiral signature read from subatomic gonols.

    Uses the "lifted-spiral" carried option now attached to every
    subatomic gonol (pure projection of the framed Möbius root-loop
    witnessed at subatomic construction). Bare-element view (attach=0).
    """
    comp = MOLECULE_COMPOSITIONS[formula]
    sigs = []
    occurrence = 0
    for sym, count in comp:
        for _ in range(count):
            receipt = subatomic_gonol.construct_subatomic_gonol(sym, occurrence=occurrence)
            value = lifted_spiral_carried_on_subatomic(receipt)
            sigs.append(f"{sym}:{'|'.join(value[0])};{','.join(value[1])};{value[2]}")
            occurrence += 1
    return tuple(sorted(sigs))


def _per_symbol_harmonic_survival_from_molecule(
    formula: str,
    constructions: Mapping[str, Any] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Per-constituent-symbol harmonic survival carried on the molecule receipt.

    For each symbol in the composition, return the union of surviving candidate ids
    carried under "<sym>-harmonic-surviving" (or empty if none).
    Sources from the closed molecule PublicGonol receipt (the single source of truth).
    An existing construction map may be supplied by comparison runs to avoid
    rebuilding the full declared molecule set for each formula.
    """
    from epac_molecular import per_symbol_harmonic_survival_carried_on_molecule

    if constructions is None:
        constructions = construct_declared_molecules()
    if formula not in constructions:
        return {}
    c = constructions[formula]
    return per_symbol_harmonic_survival_carried_on_molecule(c)


def _lifted_spiral_signature(formula: str) -> tuple:
    """Stable signature for the lifted spiral (UCNS framed Möbius root-loop).

    Sources exclusively from the carried "lifted-spiral" fact on the molecule
    PublicGonol receipt (single source of truth, parallel to harmonic layers).
    Returns the canonical (frames_tuple, sorted_axes_tuple, attachment_count).
    """
    from epac_molecular import lifted_spiral_carried_on_molecule
    constructions = construct_declared_molecules()
    if formula not in constructions:
        return ((), (), 0)
    c = constructions[formula]
    sig = lifted_spiral_carried_on_molecule(c)
    if isinstance(sig, (list, tuple)) and len(sig) == 3:
        frames, axes, ac = sig
        return (tuple(frames), tuple(sorted(axes)) if axes else (), int(ac))
    return ((), (), 0)


def _boundary_capacity_signature(
    formula: str,
    construction: Any | None = None,
) -> tuple:
    """Stable signature for boundary capacity of the bounded standing-wave configuration.

    Distinguishes fixed interior mode count (3) from boundary dimensionality
    (participant axes count) and boundary coupling capacity (attachment count).
    Sources exclusively from the carried facts on the molecule receipt.
    Returns (interior_modes, boundary_dim, boundary_coupling_capacity).
    """
    if construction is None:
        constructions = construct_declared_molecules()
        construction = constructions.get(formula)
    if construction is None:
        return (3, 0, 0)
    bc = boundary_capacity_carried_on_molecule(construction)
    if isinstance(bc, (list, tuple)) and len(bc) == 3:
        im, bd, bcc = bc
        return (int(im), int(bd), int(bcc))
    return (3, 0, 0)


def _periodic_element_boundary_capacity_signature(formula: str) -> tuple:
    """Molecule-level boundary capacity read from native periodic element gonols.

    For bare elements attachment capacity is 0; boundary dim comes from element axes.
    Encoded per-constituent for the composite (parallel to periodic_element_lifted_spiral).
    """
    comp = MOLECULE_COMPOSITIONS[formula]
    sigs = []
    occurrence = 0
    for sym, count in comp:
        for _ in range(count):
            receipt = construct_element_gonol(sym, occurrence=occurrence)
            value = boundary_capacity_from_element_receipt(receipt)
            sigs.append(f"{sym}:{value[0]},{value[1]},{value[2]}")
            occurrence += 1
    return tuple(sorted(sigs))


def _subatomic_boundary_capacity_signature(formula: str) -> tuple:
    """Molecule-level boundary capacity read from subatomic gonols.

    Bare subatomic gonols have attachment capacity 0.
    """
    comp = MOLECULE_COMPOSITIONS[formula]
    sigs = []
    occurrence = 0
    for sym, count in comp:
        for _ in range(count):
            receipt = subatomic_gonol.construct_subatomic_gonol(sym, occurrence=occurrence)
            value = boundary_capacity_from_subatomic_receipt(receipt)
            sigs.append(f"{sym}:{value[0]},{value[1]},{value[2]}")
            occurrence += 1
    return tuple(sorted(sigs))


def _quantify_distinguishing_power(
    known_shapes: Mapping[str, str],
    charged: Mapping[str, Any],
    topology: Mapping[str, Any],
    control: Mapping[str, Any],
    harmonic: Mapping[str, Any] | None = None,
    subatomic_harmonic: Mapping[str, Any] | None = None,
    periodic_element_harmonic: Mapping[str, Any] | None = None,
    per_symbol_harmonic: Mapping[str, Mapping[str, tuple[str, ...]]] | None = None,
    lifted_spiral: Mapping[str, Any] | None = None,
    periodic_element_lifted_spiral: Mapping[str, Any] | None = None,
    subatomic_lifted_spiral: Mapping[str, Any] | None = None,
    boundary_capacity: Mapping[str, Any] | None = None,
    periodic_element_boundary_capacity: Mapping[str, Any] | None = None,
    subatomic_boundary_capacity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Quantitative distinguishing power under the frozen preregistration policy.

    All metrics are computed after construction, using only the sealed known
    shape labels for evaluation (never during construction).
    """

    known_partitions = _partitions(known_shapes)
    charged_partitions = _partitions(charged)
    topology_partitions = _partitions(topology)
    control_partitions = _partitions(control)
    harmonic_partitions = _partitions(harmonic or {})
    subatomic_harmonic_partitions = _partitions(subatomic_harmonic or {})

    known_classes = len(known_partitions)
    charged_classes = len(charged_partitions)
    topology_classes = len(topology_partitions)
    control_classes = len(control_partitions)
    harmonic_classes = len(harmonic_partitions)
    subatomic_harmonic_classes = len(subatomic_harmonic_partitions)

    # Splits / collapses relative to known
    def _splits_and_collapses(sig: Mapping[str, Any]) -> tuple[int, int]:
        by_shape: dict[str, set[Any]] = defaultdict(set)
        for f, shape in known_shapes.items():
            by_shape[shape].add(sig[f])
        splits = sum(1 for vals in by_shape.values() if len(vals) > 1)
        shapes = list(by_shape.keys())
        collapses = 0
        for i, left in enumerate(shapes):
            for right in shapes[i + 1 :]:
                if by_shape[left] & by_shape[right]:
                    collapses += 1
        return splits, collapses

    charged_splits, charged_collapses = _splits_and_collapses(charged)
    topology_splits, topology_collapses = _splits_and_collapses(topology)
    control_splits, control_collapses = _splits_and_collapses(control)
    harmonic_splits, harmonic_collapses = _splits_and_collapses(harmonic) if harmonic else (0, 0)
    subatomic_harmonic_splits, subatomic_harmonic_collapses = (
        _splits_and_collapses(subatomic_harmonic) if subatomic_harmonic else (0, 0)
    )
    subatomic_lifted_spiral_splits, subatomic_lifted_spiral_collapses = (
        _splits_and_collapses(subatomic_lifted_spiral) if subatomic_lifted_spiral else (0, 0)
    )

    # Pairwise agreement tables
    known_pw = _pairwise_counts(known_shapes, known_shapes)  # sanity: all tp or tn
    charged_pw = _pairwise_counts(known_shapes, charged)
    topology_pw = _pairwise_counts(known_shapes, topology)
    control_pw = _pairwise_counts(known_shapes, control)
    harmonic_pw = _pairwise_counts(known_shapes, harmonic) if harmonic else {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total_pairs": 0}
    subatomic_harmonic_pw = (
        _pairwise_counts(known_shapes, subatomic_harmonic) if subatomic_harmonic else {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total_pairs": 0}
    )
    subatomic_lifted_spiral_pw = (
        _pairwise_counts(known_shapes, subatomic_lifted_spiral) if subatomic_lifted_spiral else {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total_pairs": 0}
    )

    # Per-symbol harmonic family (dict-of-dicts) must be canonicalized to flat signature tuples for partitioning.
    per_symbol_harmonic_flat = {}
    if per_symbol_harmonic:
        for f, symmap in per_symbol_harmonic.items():
            per_symbol_harmonic_flat[f] = tuple(sorted(f"{s}:{','.join(vs)}" for s, vs in symmap.items()))
    per_symbol_harmonic_partitions = _partitions(per_symbol_harmonic_flat)
    per_symbol_harmonic_classes = len(per_symbol_harmonic_partitions)
    per_symbol_harmonic_splits, per_symbol_harmonic_collapses = (
        _splits_and_collapses(per_symbol_harmonic_flat) if per_symbol_harmonic_flat else (0, 0)
    )
    per_symbol_harmonic_pw = (
        _pairwise_counts(known_shapes, per_symbol_harmonic_flat) if per_symbol_harmonic_flat else {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total_pairs": 0}
    )

    # Exact partition matches
    matches_known = _formula_sets(charged_partitions) == _formula_sets(known_partitions)
    matches_control = _formula_sets(charged_partitions) == _formula_sets(control_partitions)

    # Harmonic family exact matches (symmetric to charged)
    harmonic_matches_known = _formula_sets(harmonic_partitions) == _formula_sets(known_partitions) if harmonic else False
    harmonic_matches_control = _formula_sets(harmonic_partitions) == _formula_sets(control_partitions) if harmonic else False

    # Periodic element harmonic family exact matches (symmetric to the other harmonic views)
    periodic_element_harmonic_partitions = _partitions(periodic_element_harmonic or {})
    periodic_element_harmonic_matches_known = _formula_sets(periodic_element_harmonic_partitions) == _formula_sets(known_partitions) if periodic_element_harmonic else False
    periodic_element_harmonic_matches_control = _formula_sets(periodic_element_harmonic_partitions) == _formula_sets(control_partitions) if periodic_element_harmonic else False

    # Per-symbol harmonic family exact matches (symmetric to the molecule-level harmonic family)
    per_symbol_harmonic_matches_known = _formula_sets(per_symbol_harmonic_partitions) == _formula_sets(known_partitions) if per_symbol_harmonic_flat else False
    per_symbol_harmonic_matches_control = _formula_sets(per_symbol_harmonic_partitions) == _formula_sets(control_partitions) if per_symbol_harmonic_flat else False

    # Simple information ratios (higher is more distinguishing relative to known)
    def _ratio(classes: int) -> float:
        return classes / known_classes if known_classes else 0.0

    class_counts = {
        "known_shapes": known_classes,
        "charged_3_structure": charged_classes,
        "topology_3_structure": topology_classes,
        "stoichiometric_control": control_classes,
    }
    splits_known = {
        "charged_3_structure": charged_splits,
        "topology_3_structure": topology_splits,
        "stoichiometric_control": control_splits,
    }
    collapses_across = {
        "charged_3_structure": charged_collapses,
        "topology_3_structure": topology_collapses,
        "stoichiometric_control": control_collapses,
    }
    pairwise = {
        "charged_3_structure": charged_pw,
        "topology_3_structure": topology_pw,
        "stoichiometric_control": control_pw,
    }
    ratios = {
        "charged": _ratio(charged_classes),
        "topology": _ratio(topology_classes),
        "control": _ratio(control_classes),
    }

    if harmonic:
        class_counts["harmonic_survival"] = harmonic_classes
        splits_known["harmonic_survival"] = harmonic_splits
        collapses_across["harmonic_survival"] = harmonic_collapses
        pairwise["harmonic_survival"] = harmonic_pw
        ratios["harmonic"] = _ratio(harmonic_classes)

    if subatomic_harmonic:
        class_counts["subatomic_harmonic_survival"] = subatomic_harmonic_classes
        splits_known["subatomic_harmonic_survival"] = subatomic_harmonic_splits
        collapses_across["subatomic_harmonic_survival"] = subatomic_harmonic_collapses
        pairwise["subatomic_harmonic_survival"] = subatomic_harmonic_pw
        ratios["subatomic_harmonic"] = _ratio(subatomic_harmonic_classes)

    if periodic_element_harmonic:
        pe_partitions = _partitions(periodic_element_harmonic)
        pe_classes = len(pe_partitions)
        pe_splits, pe_collapses = _splits_and_collapses(periodic_element_harmonic)
        pe_pw = _pairwise_counts(known_shapes, periodic_element_harmonic)
        class_counts["periodic_element_harmonic_survival"] = pe_classes
        splits_known["periodic_element_harmonic_survival"] = pe_splits
        collapses_across["periodic_element_harmonic_survival"] = pe_collapses
        pairwise["periodic_element_harmonic_survival"] = pe_pw
        ratios["periodic_element_harmonic"] = _ratio(pe_classes)

    if periodic_element_lifted_spiral:
        pel_partitions = _partitions(periodic_element_lifted_spiral)
        pel_classes = len(pel_partitions)
        pel_splits, pel_collapses = _splits_and_collapses(periodic_element_lifted_spiral)
        pel_pw = _pairwise_counts(known_shapes, periodic_element_lifted_spiral)
        class_counts["periodic_element_lifted_spiral"] = pel_classes
        splits_known["periodic_element_lifted_spiral"] = pel_splits
        collapses_across["periodic_element_lifted_spiral"] = pel_collapses
        pairwise["periodic_element_lifted_spiral"] = pel_pw
        ratios["periodic_element_lifted_spiral"] = _ratio(pel_classes)

        # Exact matches for the periodic element lifted spiral family
        periodic_element_lifted_spiral_matches_known = _formula_sets(pel_partitions) == _formula_sets(known_partitions)
        periodic_element_lifted_spiral_matches_control = _formula_sets(pel_partitions) == _formula_sets(control_partitions)

    if subatomic_lifted_spiral:
        sal_partitions = _partitions(subatomic_lifted_spiral)
        sal_classes = len(sal_partitions)
        sal_splits, sal_collapses = _splits_and_collapses(subatomic_lifted_spiral)
        sal_pw = _pairwise_counts(known_shapes, subatomic_lifted_spiral)
        class_counts["subatomic_lifted_spiral"] = sal_classes
        splits_known["subatomic_lifted_spiral"] = sal_splits
        collapses_across["subatomic_lifted_spiral"] = sal_collapses
        pairwise["subatomic_lifted_spiral"] = sal_pw
        ratios["subatomic_lifted_spiral"] = _ratio(sal_classes)

        # Exact matches for the subatomic lifted spiral family
        subatomic_lifted_spiral_matches_known = _formula_sets(sal_partitions) == _formula_sets(known_partitions)
        subatomic_lifted_spiral_matches_control = _formula_sets(sal_partitions) == _formula_sets(control_partitions)

    if boundary_capacity:
        bc_partitions = _partitions(boundary_capacity)
        bc_classes = len(bc_partitions)
        bc_splits, bc_collapses = _splits_and_collapses(boundary_capacity)
        bc_pw = _pairwise_counts(known_shapes, boundary_capacity)
        class_counts["boundary_capacity"] = bc_classes
        splits_known["boundary_capacity"] = bc_splits
        collapses_across["boundary_capacity"] = bc_collapses
        pairwise["boundary_capacity"] = bc_pw
        ratios["boundary_capacity"] = _ratio(bc_classes)

        # Exact matches for boundary capacity family
        boundary_capacity_matches_known = _formula_sets(bc_partitions) == _formula_sets(known_partitions)
        boundary_capacity_matches_control = _formula_sets(bc_partitions) == _formula_sets(control_partitions)

    if periodic_element_boundary_capacity:
        pebc_partitions = _partitions(periodic_element_boundary_capacity)
        pebc_classes = len(pebc_partitions)
        pebc_splits, pebc_collapses = _splits_and_collapses(periodic_element_boundary_capacity)
        pebc_pw = _pairwise_counts(known_shapes, periodic_element_boundary_capacity)
        class_counts["periodic_element_boundary_capacity"] = pebc_classes
        splits_known["periodic_element_boundary_capacity"] = pebc_splits
        collapses_across["periodic_element_boundary_capacity"] = pebc_collapses
        pairwise["periodic_element_boundary_capacity"] = pebc_pw
        ratios["periodic_element_boundary_capacity"] = _ratio(pebc_classes)

        periodic_element_boundary_capacity_matches_known = _formula_sets(pebc_partitions) == _formula_sets(known_partitions)
        periodic_element_boundary_capacity_matches_control = _formula_sets(pebc_partitions) == _formula_sets(control_partitions)

    if subatomic_boundary_capacity:
        sabc_partitions = _partitions(subatomic_boundary_capacity)
        sabc_classes = len(sabc_partitions)
        sabc_splits, sabc_collapses = _splits_and_collapses(subatomic_boundary_capacity)
        sabc_pw = _pairwise_counts(known_shapes, subatomic_boundary_capacity)
        class_counts["subatomic_boundary_capacity"] = sabc_classes
        splits_known["subatomic_boundary_capacity"] = sabc_splits
        collapses_across["subatomic_boundary_capacity"] = sabc_collapses
        pairwise["subatomic_boundary_capacity"] = sabc_pw
        ratios["subatomic_boundary_capacity"] = _ratio(sabc_classes)

        subatomic_boundary_capacity_matches_known = _formula_sets(sabc_partitions) == _formula_sets(known_partitions)
        subatomic_boundary_capacity_matches_control = _formula_sets(sabc_partitions) == _formula_sets(control_partitions)

    if per_symbol_harmonic and per_symbol_harmonic_flat:
        class_counts["per_symbol_harmonic_survival"] = per_symbol_harmonic_classes
        splits_known["per_symbol_harmonic_survival"] = per_symbol_harmonic_splits
        collapses_across["per_symbol_harmonic_survival"] = per_symbol_harmonic_collapses
        pairwise["per_symbol_harmonic_survival"] = per_symbol_harmonic_pw
        ratios["per_symbol_harmonic"] = _ratio(per_symbol_harmonic_classes)

    if lifted_spiral:
        # lifted_spiral values are carried canonical signatures (frames, axes, attach_count)
        # already sourced from the molecule receipt (first-class carried fact).
        spiral_sigs = {}
        for f, sig in lifted_spiral.items():
            if isinstance(sig, (list, tuple)) and len(sig) == 3:
                frames, axes, ac = sig
                spiral_sigs[f] = (tuple(frames), tuple(sorted(axes)) if axes else (), int(ac))
            else:
                spiral_sigs[f] = ((), (), 0)
        spiral_partitions = _partitions(spiral_sigs)
        spiral_classes = len(spiral_partitions)
        spiral_splits, spiral_collapses = _splits_and_collapses(spiral_sigs)
        spiral_pw = _pairwise_counts(known_shapes, spiral_sigs)
        class_counts["lifted_spiral"] = spiral_classes
        splits_known["lifted_spiral"] = spiral_splits
        collapses_across["lifted_spiral"] = spiral_collapses
        pairwise["lifted_spiral"] = spiral_pw
        ratios["lifted_spiral"] = _ratio(spiral_classes)

        # Exact matches for spiral family
        spiral_matches_known = _formula_sets(spiral_partitions) == _formula_sets(known_partitions)
        spiral_matches_control = _formula_sets(spiral_partitions) == _formula_sets(control_partitions)

    return {
        "class_counts": class_counts,
        "splits_known_classes": splits_known,
        "collapses_across_known_classes": collapses_across,
        "pairwise_vs_known": pairwise,
        "exact_partition_match": {
            "charged_matches_known": matches_known,
            "charged_matches_control": matches_control,
            "harmonic_matches_known": harmonic_matches_known,
            "harmonic_matches_control": harmonic_matches_control,
            "periodic_element_harmonic_matches_known": periodic_element_harmonic_matches_known,
            "periodic_element_harmonic_matches_control": periodic_element_harmonic_matches_control,
            "per_symbol_harmonic_matches_known": per_symbol_harmonic_matches_known,
            "per_symbol_harmonic_matches_control": per_symbol_harmonic_matches_control,
            "lifted_spiral_matches_known": spiral_matches_known if lifted_spiral else False,
            "lifted_spiral_matches_control": spiral_matches_control if lifted_spiral else False,
            "periodic_element_lifted_spiral_matches_known": periodic_element_lifted_spiral_matches_known if periodic_element_lifted_spiral else False,
            "periodic_element_lifted_spiral_matches_control": periodic_element_lifted_spiral_matches_control if periodic_element_lifted_spiral else False,
            "subatomic_lifted_spiral_matches_known": subatomic_lifted_spiral_matches_known if subatomic_lifted_spiral else False,
            "subatomic_lifted_spiral_matches_control": subatomic_lifted_spiral_matches_control if subatomic_lifted_spiral else False,
            "boundary_capacity_matches_known": boundary_capacity_matches_known if boundary_capacity else False,
            "boundary_capacity_matches_control": boundary_capacity_matches_control if boundary_capacity else False,
            "periodic_element_boundary_capacity_matches_known": periodic_element_boundary_capacity_matches_known if periodic_element_boundary_capacity else False,
            "periodic_element_boundary_capacity_matches_control": periodic_element_boundary_capacity_matches_control if periodic_element_boundary_capacity else False,
            "subatomic_boundary_capacity_matches_known": subatomic_boundary_capacity_matches_known if subatomic_boundary_capacity else False,
            "subatomic_boundary_capacity_matches_control": subatomic_boundary_capacity_matches_control if subatomic_boundary_capacity else False,
        },
        "class_count_ratios_vs_known": ratios,
        "note": "All metrics respect the frozen preregistration policy: construction never saw sealed labels.",
    }


@lru_cache(maxsize=4)
def compare_after_construction(root: Path = EPAC_ROOT) -> dict[str, Any]:
    """Construct first, then open the sealed shapes, then score standings.

    The comparison record is deterministic for a given root, so tests share a
    cached record rather than rebuilding the full receipt surface repeatedly.
    """

    label_hits = construction_sources_omit_sealed_labels(root)
    constructions = construct_declared_molecules()
    missing_constructions = ORIGINAL_PREREG.difference(constructions)
    if missing_constructions:
        raise ValueError(f"missing preregistered constructions: {sorted(missing_constructions)}")
    sealed_path = SEALED_PATH if root == EPAC_ROOT else root / "data" / "sealed_known_molecular_geometry.json"
    sealed = json.loads(sealed_path.read_text(encoding="utf-8"))
    missing_sealed = ORIGINAL_PREREG.difference(sealed.get("molecules", {}))
    if missing_sealed:
        raise ValueError(f"missing preregistered sealed evidence: {sorted(missing_sealed)}")
    charged = {}
    topology = {}
    mobius = {}
    atomic = {}
    control = {}
    harmonic = {}
    subatomic_harmonic = {}
    periodic_element_harmonic = {}
    periodic_element_lifted_spiral: dict[str, tuple] = {}
    subatomic_lifted_spiral: dict[str, tuple] = {}
    per_symbol: dict[str, dict[str, tuple[str, ...]]] = {}
    lifted_spiral = {}
    boundary_capacity: dict[str, tuple] = {}
    periodic_element_boundary_capacity: dict[str, tuple] = {}
    subatomic_boundary_capacity: dict[str, tuple] = {}
    for formula, construction in constructions.items():
        structure = construction.receipt.structure
        if structure is None:
            raise ValueError(f"{formula} closed without a three-dimensional structure")
        charged[formula] = charged_structure_readout(structure)
        topology[formula] = topology_structure_readout(structure)
        mobius[formula] = construction.invariants["ucns_coupling_signature"]
        atomic[formula] = construction.invariants["atomic_coupling_signature"]
        control[formula] = matched_information_control(construction.invariants)

        # Exclusively source the molecule-level harmonic survival from the carried
        # fact on the molecule PublicGonol receipt. This is the single source of
        # truth for the lifted nuclear harmonic layer at molecular scale.
        harmonic[formula] = harmonic_survival_carried_on_molecule(construction)

        # Molecule-level lifted spiral from the carried fact on the molecule receipt
        # (single source of truth, parallel to harmonic).
        lifted_spiral[formula] = lifted_spiral_carried_on_molecule(construction)

        # The per-constituent (subatomic) view for the same formula.
        subatomic_harmonic[formula] = construction.invariants["subatomic_harmonic_survival"]

        # The view through native periodic element gonols (also sourced from the
        # same subatomic layer at construction time).
        periodic_element_harmonic[formula] = _periodic_element_harmonic_survival_signature(formula)

        # Lifted spiral view through native periodic element gonols (first-class
        # carried fact on element gonols, parallel to the molecule view).
        periodic_element_lifted_spiral[formula] = _periodic_element_lifted_spiral_signature(formula)

        # Lifted spiral view through subatomic gonols (first-class carried fact
        # on subatomic gonols, parallel to harmonic-surviving and to the other
        # lifted-spiral families).
        subatomic_lifted_spiral[formula] = _subatomic_lifted_spiral_signature(formula)

        # Boundary capacity (interior modes vs boundary dim vs coupling capacity)
        # as a first-class family, sourced from the same carried facts.
        boundary_capacity[formula] = _boundary_capacity_signature(formula, construction)
        periodic_element_boundary_capacity[formula] = _periodic_element_boundary_capacity_signature(formula)
        subatomic_boundary_capacity[formula] = _subatomic_boundary_capacity_signature(formula)

        # Cross-check: molecule-carried (from receipt) must equal the subatomic-derived union.
        if harmonic[formula] != subatomic_harmonic[formula]:
            raise AssertionError(f"molecule-carried harmonic mismatch for {formula}")

        # Cross-check: periodic element view must equal the subatomic view (all three families identical).
        if periodic_element_harmonic[formula] != subatomic_harmonic[formula]:
            raise AssertionError(f"periodic-element harmonic mismatch for {formula}")

        # Cross-check: the molecule carried (now sourced from element gonols at construction)
        # must equal the direct periodic element gonol view for the same formula.
        if harmonic[formula] != periodic_element_harmonic[formula]:
            raise AssertionError(f"molecule harmonic not equal to element-gonol harmonic for {formula}")

        # Note on lifted spiral layers:
        # The molecule-level lifted spiral (carried on the molecule receipt) includes
        # the actual attachment slots and participant axes declared for the closed
        # structure. The periodic element view is the bare-element projection (axes
        # from element gonols, attachment count 0). They are intentionally different
        # projections; both are first-class families for partitioning/quantify.
        # No equality cross-check is imposed (unlike the harmonic-survival union rule).

        # Per-symbol harmonic survival sourced exclusively from the molecule receipt
        # (single source of truth). Compute here for cross-checks.
        per_symbol[formula] = per_symbol_harmonic_survival_carried_on_molecule(construction)

        # Cross-check: per-symbol carried on receipt must match the per-symbol view
        # derived from the participating element gonols (lifted at construction).
        # The receipt always carries every symbol in the composition (with "none" when empty).
        elem_per_sym: dict[str, tuple[str, ...]] = {}
        for sym, _cnt in MOLECULE_COMPOSITIONS.get(formula, ()):
            eg = construct_element_gonol(sym)
            hs = dict(eg.gonol.carried_options).get("harmonic-surviving", "none")
            elem_per_sym[sym] = tuple(sorted(set(hs.split(",")))) if hs and hs != "none" else ()
        # Normalize receipt side (already has "none" for empty symbols) and compare.
        if per_symbol[formula] != elem_per_sym:
            raise AssertionError(f"per-symbol harmonic receipt != element-gonols for {formula}")

    # Canonical signatures for the lifted spiral family (first-class, parallel to harmonic families).
    # Values are already the carried canonical signatures (frames_tuple, axes_tuple, attach_count)
    # sourced exclusively from the molecule PublicGonol receipt (single source of truth).
    spiral_sigs: dict[str, tuple] = {}
    for f, sig in lifted_spiral.items():
        # sig is already the tuple; normalize to 3-tuple form defensively.
        if isinstance(sig, (list, tuple)) and len(sig) == 3:
            frames, axes, ac = sig
            spiral_sigs[f] = (tuple(frames), tuple(sorted(axes)) if axes else (), int(ac))
        else:
            spiral_sigs[f] = ((), (), 0)

    # Cross-layer determinism (carried values must match the subatomic gonol layer).
    for f, c in constructions.items():
        if c.invariants["harmonic_survival"] != c.invariants["subatomic_harmonic_survival"]:
            raise AssertionError(f"harmonic survival mismatch for {f}")

    # known_shapes for standings and quantify_distinguishing_power is *always* restricted
    # to the frozen original preregistered set, even when the sealed file or constructed
    # set is enlarged for broader experiments. Policy is sealed on the original 5.
    known_shapes = {
        formula: sealed["molecules"][formula]["known_shape"]
        for formula in ORIGINAL_PREREG
    }

    # per_symbol already populated inside the loop (receipt-sourced single source of truth)
    # with cross-checks against element gonols. Recompute via helper for safety/readouts only.
    for formula in list(per_symbol.keys()):
        # No-op re-assert via the public helper to keep readouts in sync.
        _ = _per_symbol_harmonic_survival_from_molecule(formula, constructions)

    quantify = _quantify_distinguishing_power(
        known_shapes, charged, topology, control, harmonic, subatomic_harmonic, periodic_element_harmonic, per_symbol, lifted_spiral, periodic_element_lifted_spiral, subatomic_lifted_spiral,
        boundary_capacity, periodic_element_boundary_capacity, subatomic_boundary_capacity
    )

    # Boundary-capacity transitions: record R0 -> R1 and B(R0) -> B(R1) for every declared molecule.
    # The reproducibility test must be computable from source state + declared coupling operation only.
    # No inspection of the finished target receipt or known empirical labels is allowed for the prediction.
    transitions = {
        f: boundary_capacity_transition_for_molecule(f, construction)
        for f, construction in constructions.items()
    }
    all_transitions_reproducible = all(t.get("reproducible", False) for t in transitions.values())

    # Compositional transition closure under local affixation steps only.
    # Each step contributes only its local information (introduce a named atom instance,
    # or affix one ligand contribution whose slot count comes solely from that ligand's record).
    # Paths are built from every valid ordering of introduces followed by every valid ordering of affixes.
    # We test: path independence of final B, local step reproducibility, and that accumulated B
    # equals the direct carried B(R) without ever reading the finished target or known labels for deltas.
    closure = compositional_boundary_closure()

    # The observed local transition signature (the law) for the current construction class.
    # Any candidate geometric explanation (including a future UCNS continuum/gonal boundary trace)
    # must reproduce these exact (Δd_∂, Δc_∂) values for the admissible local steps.
    # Computed from local steps only (no target receipt, no global totals, no known labels).
    local_transition_signature = observed_local_boundary_deltas()

    # Descriptor sufficiency / collision falsifier over the locked nine.
    # Exhaustive EPAC-local enumeration of reachable states under declared sources and ops.
    # Groups by B(R); classifies collisions by operational equivalence under replay/transition contract.
    # No new coordinate invented; nine formulas frozen.
    descriptor_sufficiency = boundary_capacity_descriptor_sufficiency_sweep()

    # Information-loss localization over the six sealed collision classes.
    # Uses only already-declared operational data, records, invariants, participants,
    # source/relation/digests. Identifies earliest distinguishable step while B identical
    # and the smallest existing witness. No new coordinate.
    information_loss = boundary_capacity_information_loss_localization()

    # Boundary-capacity quotient test.
    # B(R1) = B(R2)  ⇔  R1 ≡∂ R2 , where ≡∂ is indistinguishability under admissible
    # boundary-capacity probes (B readout, attachment contributions K, attachment profiles,
    # transition deltas) with all identifiers/labels withheld for distinction decisions.
    # Converse check: different B are distinguishable by at least one admissible probe.
    # Uses only the six sealed collision classes. No source_id or labels used to decide equivalence.
    quotient = boundary_capacity_quotient_test()

    # Minimal behavioral refinement audit.
    # Exhaustive search over all subsets of the four already-declared identity-free candidate
    # observables (ligand_contribution_K, affix_Ks, attachment_profile, transition_deltas).
    # For each D_S = B + S, compare the induced partition against the sealed full ≡∂
    # on all 27 frozen states (both directions).
    # Identify exact matches, inclusion-minimal sets, fewest-observable sets, canonicality,
    # and concrete witness pairs for rejected smaller candidates.
    # No identity smuggled via absent probes or record shape. No new observables derived.
    refinement_audit = boundary_capacity_minimal_refinement_audit()

    # Representation audit (capstone).
    # Consolidates all prior stages with the final representation-equivalence check:
    # whether B + the minimal already-declared identity-free observables exactly
    # reproduces the sealed full admissible boundary behavior partition over the
    # frozen states (identifiers withheld).
    representation = epac_representation_audit()
    probe_relativity = epac_probe_relativity_formalization()

    return {
        "opened_after_construction": True,
        "construction_omits_sealed_labels": not label_hits,
        "sealed_label_hits": label_hits,
        "known_shapes": known_shapes,
        "readouts": {
            "charged_3_structure": {formula: list(value) for formula, value in charged.items()},
            "topology_3_structure": {formula: list(value) for formula, value in topology.items()},
            "harmonic_survival": {formula: list(value) for formula, value in harmonic.items()},
            "subatomic_harmonic_survival": {formula: list(value) for formula, value in subatomic_harmonic.items()},
            "periodic_element_harmonic_survival": {formula: list(value) for formula, value in periodic_element_harmonic.items()},
            "per_symbol_harmonic_survival": {formula: {s: list(v) for s, v in per_symbol[formula].items()} for formula in per_symbol},
            "lifted_spiral": {formula: list(value) for formula, value in spiral_sigs.items()},
            "periodic_element_lifted_spiral": {formula: list(value) for formula, value in periodic_element_lifted_spiral.items()},
            "subatomic_lifted_spiral": {formula: list(value) for formula, value in subatomic_lifted_spiral.items()},
            "boundary_capacity": {formula: list(value) for formula, value in boundary_capacity.items()},
            "periodic_element_boundary_capacity": {formula: list(value) for formula, value in periodic_element_boundary_capacity.items()},
            "subatomic_boundary_capacity": {formula: list(value) for formula, value in subatomic_boundary_capacity.items()},
        },
        "partitions": {
            "known_shapes": {shape: formulas for shape, formulas in _partitions(known_shapes).items()},
            "charged_3_structure": {
                str(index): formulas for index, formulas in enumerate(_partitions(charged).values())
            },
            "topology_3_structure": {
                str(index): formulas for index, formulas in enumerate(_partitions(topology).values())
            },
            "harmonic_survival": {
                str(index): formulas for index, formulas in enumerate(_partitions(harmonic).values())
            },
            "subatomic_harmonic_survival": {
                str(index): formulas for index, formulas in enumerate(_partitions(subatomic_harmonic).values())
            },
            "periodic_element_harmonic_survival": {
                str(index): formulas for index, formulas in enumerate(_partitions(periodic_element_harmonic).values())
            },
            "per_symbol_harmonic_survival": {
                str(index): formulas for index, formulas in enumerate(_partitions({f: tuple(sorted((s + ":" + ",".join(vs)) for s, vs in per_symbol[f].items())) for f in per_symbol}).values())
            },
            "lifted_spiral": {
                str(index): formulas for index, formulas in enumerate(_partitions(spiral_sigs).values())
            },
            "periodic_element_lifted_spiral": {
                str(index): formulas for index, formulas in enumerate(_partitions(periodic_element_lifted_spiral).values())
            },
            "subatomic_lifted_spiral": {
                str(index): formulas for index, formulas in enumerate(_partitions(subatomic_lifted_spiral).values())
            },
            "boundary_capacity": {
                str(index): formulas for index, formulas in enumerate(_partitions(boundary_capacity).values())
            },
            "periodic_element_boundary_capacity": {
                str(index): formulas for index, formulas in enumerate(_partitions(periodic_element_boundary_capacity).values())
            },
            "subatomic_boundary_capacity": {
                str(index): formulas for index, formulas in enumerate(_partitions(subatomic_boundary_capacity).values())
            },
        },
        "topology_collapses_h2o_with_co2": topology["H2O"] == topology["CO2"],
        "charged_distinguishes_h2o_from_co2": charged["H2O"] != charged["CO2"],
        "linear_class_split_by_charged_structure": charged["H2"] != charged["CO2"],
        # Parallel facts for the carried nuclear harmonic survival signature.
        "harmonic_collapses_h2o_with_co2": harmonic["H2O"] == harmonic["CO2"],
        "harmonic_distinguishes_h2o_from_co2": harmonic["H2O"] != harmonic["CO2"],
        "linear_class_split_by_harmonic_survival": harmonic["H2"] != harmonic["CO2"],
        # Exact partition match facts for the harmonic family (symmetric to charged).
        "harmonic_matches_known": quantify["exact_partition_match"]["harmonic_matches_known"],
        "harmonic_matches_control": quantify["exact_partition_match"]["harmonic_matches_control"],
        # Parallel facts for the nuclear harmonic survival via native periodic element gonols.
        "periodic_element_harmonic_collapses_h2o_with_co2": periodic_element_harmonic["H2O"] == periodic_element_harmonic["CO2"],
        "periodic_element_harmonic_distinguishes_h2o_from_co2": periodic_element_harmonic["H2O"] != periodic_element_harmonic["CO2"],
        "linear_class_split_by_periodic_element_harmonic_survival": periodic_element_harmonic["H2"] != periodic_element_harmonic["CO2"],
        "periodic_element_harmonic_matches_known": quantify["exact_partition_match"].get("periodic_element_harmonic_matches_known", False),
        "periodic_element_harmonic_matches_control": quantify["exact_partition_match"].get("periodic_element_harmonic_matches_control", False),
        # Parallel facts for the per-constituent-symbol nuclear harmonic survival (receipt-sourced).
        "per_symbol_harmonic_collapses_h2o_with_co2": per_symbol.get("H2O", {}) == per_symbol.get("CO2", {}),
        "per_symbol_harmonic_distinguishes_h2o_from_co2": per_symbol.get("H2O", {}) != per_symbol.get("CO2", {}),
        "linear_class_split_by_per_symbol_harmonic_survival": per_symbol.get("H2", {}) != per_symbol.get("CO2", {}),
        "per_symbol_harmonic_matches_known": quantify["exact_partition_match"].get("per_symbol_harmonic_matches_known", False),
        "per_symbol_harmonic_matches_control": quantify["exact_partition_match"].get("per_symbol_harmonic_matches_control", False),
        # Parallel facts for the lifted spiral (UCNS framed Möbius root-loop) first-class family (molecule receipt view).
        "lifted_spiral_collapses_h2o_with_co2": spiral_sigs.get("H2O") == spiral_sigs.get("CO2"),
        "lifted_spiral_distinguishes_h2o_from_co2": spiral_sigs.get("H2O") != spiral_sigs.get("CO2"),
        "linear_class_split_by_lifted_spiral": spiral_sigs.get("H2") != spiral_sigs.get("CO2"),
        "lifted_spiral_matches_known": quantify["exact_partition_match"].get("lifted_spiral_matches_known", False),
        "lifted_spiral_matches_control": quantify["exact_partition_match"].get("lifted_spiral_matches_control", False),
        # Parallel facts for the lifted spiral view through native periodic element gonols (first-class).
        "periodic_element_lifted_spiral_collapses_h2o_with_co2": periodic_element_lifted_spiral.get("H2O") == periodic_element_lifted_spiral.get("CO2"),
        "periodic_element_lifted_spiral_distinguishes_h2o_from_co2": periodic_element_lifted_spiral.get("H2O") != periodic_element_lifted_spiral.get("CO2"),
        "linear_class_split_by_periodic_element_lifted_spiral": periodic_element_lifted_spiral.get("H2") != periodic_element_lifted_spiral.get("CO2"),
        "periodic_element_lifted_spiral_matches_known": quantify["exact_partition_match"].get("periodic_element_lifted_spiral_matches_known", False),
        "periodic_element_lifted_spiral_matches_control": quantify["exact_partition_match"].get("periodic_element_lifted_spiral_matches_control", False),
        # Parallel facts for the lifted spiral view through subatomic gonols (first-class).
        "subatomic_lifted_spiral_collapses_h2o_with_co2": subatomic_lifted_spiral.get("H2O") == subatomic_lifted_spiral.get("CO2"),
        "subatomic_lifted_spiral_distinguishes_h2o_from_co2": subatomic_lifted_spiral.get("H2O") != subatomic_lifted_spiral.get("CO2"),
        "linear_class_split_by_subatomic_lifted_spiral": subatomic_lifted_spiral.get("H2") != subatomic_lifted_spiral.get("CO2"),
        "subatomic_lifted_spiral_matches_known": quantify["exact_partition_match"].get("subatomic_lifted_spiral_matches_known", False),
        "subatomic_lifted_spiral_matches_control": quantify["exact_partition_match"].get("subatomic_lifted_spiral_matches_control", False),
        # Parallel facts for boundary capacity (interior modes vs boundary dim/coupling capacity).
        "boundary_capacity_collapses_h2o_with_co2": boundary_capacity.get("H2O") == boundary_capacity.get("CO2"),
        "boundary_capacity_distinguishes_h2o_from_co2": boundary_capacity.get("H2O") != boundary_capacity.get("CO2"),
        "linear_class_split_by_boundary_capacity": boundary_capacity.get("H2") != boundary_capacity.get("CO2"),
        "boundary_capacity_matches_known": quantify["exact_partition_match"].get("boundary_capacity_matches_known", False),
        "boundary_capacity_matches_control": quantify["exact_partition_match"].get("boundary_capacity_matches_control", False),
        "periodic_element_boundary_capacity_collapses_h2o_with_co2": periodic_element_boundary_capacity.get("H2O") == periodic_element_boundary_capacity.get("CO2"),
        "periodic_element_boundary_capacity_distinguishes_h2o_from_co2": periodic_element_boundary_capacity.get("H2O") != periodic_element_boundary_capacity.get("CO2"),
        "linear_class_split_by_periodic_element_boundary_capacity": periodic_element_boundary_capacity.get("H2") != periodic_element_boundary_capacity.get("CO2"),
        "periodic_element_boundary_capacity_matches_known": quantify["exact_partition_match"].get("periodic_element_boundary_capacity_matches_known", False),
        "periodic_element_boundary_capacity_matches_control": quantify["exact_partition_match"].get("periodic_element_boundary_capacity_matches_control", False),
        "subatomic_boundary_capacity_collapses_h2o_with_co2": subatomic_boundary_capacity.get("H2O") == subatomic_boundary_capacity.get("CO2"),
        "subatomic_boundary_capacity_distinguishes_h2o_from_co2": subatomic_boundary_capacity.get("H2O") != subatomic_boundary_capacity.get("CO2"),
        "linear_class_split_by_subatomic_boundary_capacity": subatomic_boundary_capacity.get("H2") != subatomic_boundary_capacity.get("CO2"),
        "subatomic_boundary_capacity_matches_known": quantify["exact_partition_match"].get("subatomic_boundary_capacity_matches_known", False),
        "subatomic_boundary_capacity_matches_control": quantify["exact_partition_match"].get("subatomic_boundary_capacity_matches_control", False),
        # Boundary-capacity transition facts (R0 -> R1 with B(R0) -> B(R1)).
        # Reproducibility must be computed from source state + declared coupling operation only.
        "boundary_capacity_transitions": {f: {
            "source_bs": list(t["source_bs"]),
            "op": t["op"],
            "actual_b": list(t["actual_b"]),
            "predicted_b_from_source_and_op": list(t["predicted_b_from_source_and_op"]),
            "reproducible": t["reproducible"],
        } for f, t in transitions.items()},
        "boundary_capacity_transitions_all_reproducible": all_transitions_reproducible,
        # Compositional transition closure under strictly local affixation steps only.
        "boundary_capacity_compositional_closure": closure,
        "boundary_capacity_compositional_path_independent": closure.get("all_formulas_exhibit_compositional_transition_closure", False),
        "boundary_capacity_compositional_all_reproducible_locally": closure.get("all_formulas_exhibit_compositional_transition_closure", False),
        # Descriptor sufficiency / collision falsifier (locked nine only).
        # Exhaustive enumeration of reachable EPAC states from declared sources/ops.
        # B(R) grouped; collisions classified by operational equivalence (replay/transition contract).
        # No new coordinate; no extension of cases.
        "boundary_capacity_descriptor_sufficiency": descriptor_sufficiency,
        "boundary_capacity_sufficiency_status": descriptor_sufficiency.get("aggregate", {}).get("boundary_capacity_sufficiency", "UNRESOLVED"),
        # Information-loss localization over the six sealed B collisions.
        # Per-collision: earliest step while B identical, smallest existing witness,
        # witness class. Recurring classes grouped. Only already-present EPAC data used.
        "boundary_capacity_information_loss": information_loss,
        "information_loss_localization_status": information_loss.get("aggregate", {}).get("information_loss_localization", "UNRESOLVED"),
        # Boundary-capacity quotient test over the six sealed collisions.
        # B(R1) == B(R2)  ⇔  R1 ≡∂ R2 under admissible boundary probes (identifiers withheld).
        # Converse: different B are probe-distinguishable.
        "boundary_capacity_quotient": quotient,
        "boundary_capacity_quotient_status": quotient.get("aggregate", {}).get("boundary_capacity_quotient", "UNRESOLVED"),
        # Minimal behavioral refinement audit.
        # Exhaustive over subsets of the four candidate observables against the sealed full ≡∂.
        # Reports exact matches, inclusion-minimal sets, fewest-observable, canonicality,
        # and witness pairs for non-exact smaller candidates. No identity, no new observables.
        "boundary_capacity_minimal_refinement_audit": refinement_audit,
        "minimal_behavioral_refinement_status": refinement_audit.get("aggregate", {}).get("minimal_behavioral_refinement", "UNRESOLVED"),
        # Representation audit (capstone stage ledger).
        # Consolidates the full progression and reports whether the refined descriptor
        # (B + minimal already-declared identity-free observables) exactly reproduces
        # the sealed full admissible boundary behavior partition.
        "epac_representation_audit": representation,
        "representation_audit_overall": representation.get("outputs", {}).get("overall", "UNRESOLVED"),
        # Probe-relativity formalization (O ↦ Q_O ↦ D_min(O)).
        # Uses the locked 27-state representation audit as immutable baseline.
        # Only already-declared admissible observable surfaces; no new observables.
        "epac_probe_relativity_formalization": probe_relativity,
        "probe_relativity_overall": probe_relativity.get("outputs", {}).get("overall", "UNRESOLVED"),
        "standings": {
            "charged_3_structure_as_sealed_shape_prediction": _standing(charged, known_shapes, control),
            "topology_3_structure_as_sealed_shape_prediction": _standing(topology, known_shapes, control),
            "ucns_mobius_as_sealed_shape_prediction": _standing(mobius, known_shapes, control),
            "atomic_shells_as_sealed_shape_prediction": _standing(atomic, known_shapes, control),
            "harmonic_survival_as_sealed_shape_prediction": _standing(harmonic, known_shapes, control),
            "subatomic_harmonic_survival_as_sealed_shape_prediction": _standing(subatomic_harmonic, known_shapes, control),
            "periodic_element_harmonic_survival_as_sealed_shape_prediction": _standing(periodic_element_harmonic, known_shapes, control),
            "per_symbol_harmonic_survival_as_sealed_shape_prediction": _standing(
                {f: tuple(sorted((s + ":" + ",".join(vs)) for s, vs in per_symbol[f].items())) for f in per_symbol},
                known_shapes,
                control,
            ),
            "lifted_spiral_as_sealed_shape_prediction": _standing(spiral_sigs, known_shapes, control),
            "periodic_element_lifted_spiral_as_sealed_shape_prediction": _standing(periodic_element_lifted_spiral, known_shapes, control),
            "subatomic_lifted_spiral_as_sealed_shape_prediction": _standing(subatomic_lifted_spiral, known_shapes, control),
            "boundary_capacity_as_sealed_shape_prediction": _standing(boundary_capacity, known_shapes, control),
            "periodic_element_boundary_capacity_as_sealed_shape_prediction": _standing(periodic_element_boundary_capacity, known_shapes, control),
            "subatomic_boundary_capacity_as_sealed_shape_prediction": _standing(subatomic_boundary_capacity, known_shapes, control),
        },
        "quantify_distinguishing_power": quantify,
        "nonclaims": (
            "not selected canon",
            "not an imported VSEPR construction rule",
            "not a cartesian embedding",
        ),
        "hmmm": (
            "whether a later mapping from charged 3-structure to empirical angles exists without importing VSEPR",
            "exact UCNS geometric operation of each Public Gonol function position",
        ),
    }


__all__ = [
    "CONSTRUCTION_FILES",
    "SEALED_PATH",
    "SEALED_SHAPE_LABELS",
    "ORIGINAL_PREREG",
    "compare_after_construction",
    "construction_sources_omit_sealed_labels",
    "_harmonic_survival_signature",
    "_subatomic_harmonic_survival_signature",
    "_periodic_element_harmonic_survival_signature",
    "_per_symbol_harmonic_survival_from_molecule",
    "_quantify_distinguishing_power",  # internal but useful for direct inspection
]
