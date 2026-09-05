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
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

from epac_dimensional_arity import charged_structure_readout, topology_structure_readout
from epac_molecular import construct_declared_molecules, matched_information_control


EPAC_ROOT = Path(__file__).resolve().parent
SEALED_PATH = EPAC_ROOT / "data" / "sealed_known_molecular_geometry.json"
SEALED_SHAPE_LABELS = ("linear", "bent", "trigonal-pyramidal", "tetrahedral", "vsepr")
CONSTRUCTION_FILES = (
    "epac_atomic.py",
    "epac_dimensional_arity.py",
    "epac_molecular.py",
    "epac_periodic.py",
    "epac_public_gonol.py",
)


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


def compare_after_construction(root: Path = EPAC_ROOT) -> dict[str, Any]:
    """Construct first, then open the sealed shapes, then score standings."""

    label_hits = construction_sources_omit_sealed_labels(root)
    constructions = construct_declared_molecules()
    charged = {}
    topology = {}
    mobius = {}
    atomic = {}
    control = {}
    for formula, construction in constructions.items():
        structure = construction.receipt.structure
        if structure is None:
            raise ValueError(f"{formula} closed without a three-dimensional structure")
        charged[formula] = charged_structure_readout(structure)
        topology[formula] = topology_structure_readout(structure)
        mobius[formula] = construction.invariants["ucns_coupling_signature"]
        atomic[formula] = construction.invariants["atomic_coupling_signature"]
        control[formula] = matched_information_control(construction.invariants)

    sealed = json.loads((root / "data" / "sealed_known_molecular_geometry.json").read_text(encoding="utf-8"))
    known_shapes = {formula: sealed["molecules"][formula]["known_shape"] for formula in constructions}

    return {
        "opened_after_construction": True,
        "construction_omits_sealed_labels": not label_hits,
        "sealed_label_hits": label_hits,
        "known_shapes": known_shapes,
        "readouts": {
            "charged_3_structure": {formula: list(value) for formula, value in charged.items()},
            "topology_3_structure": {formula: list(value) for formula, value in topology.items()},
        },
        "partitions": {
            "known_shapes": {shape: formulas for shape, formulas in _partitions(known_shapes).items()},
            "charged_3_structure": {
                str(index): formulas for index, formulas in enumerate(_partitions(charged).values())
            },
            "topology_3_structure": {
                str(index): formulas for index, formulas in enumerate(_partitions(topology).values())
            },
        },
        "topology_collapses_h2o_with_co2": topology["H2O"] == topology["CO2"],
        "charged_distinguishes_h2o_from_co2": charged["H2O"] != charged["CO2"],
        "linear_class_split_by_charged_structure": charged["H2"] != charged["CO2"],
        "standings": {
            "charged_3_structure_as_sealed_shape_prediction": _standing(charged, known_shapes, control),
            "topology_3_structure_as_sealed_shape_prediction": _standing(topology, known_shapes, control),
            "ucns_mobius_as_sealed_shape_prediction": _standing(mobius, known_shapes, control),
            "atomic_shells_as_sealed_shape_prediction": _standing(atomic, known_shapes, control),
        },
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
    "compare_after_construction",
    "construction_sources_omit_sealed_labels",
]
