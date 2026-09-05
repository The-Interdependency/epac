from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

EPAC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EPAC_ROOT))

from epac_comparison import compare_after_construction, construction_sources_omit_sealed_labels
from epac_dimensional_arity import charged_structure_readout, topology_structure_readout
from epac_molecular import construct_declared_molecules, matched_information_control


SEALED = EPAC_ROOT / "data" / "sealed_known_molecular_geometry.json"


class GeometryComparisonAfterConstructionTest(unittest.TestCase):
    def test_construction_omits_sealed_shape_labels(self) -> None:
        self.assertEqual(construction_sources_omit_sealed_labels(), ())

    def test_charged_couplings_are_the_three_dimensional_structure(self) -> None:
        constructions = construct_declared_molecules()
        water = constructions["H2O"].receipt.structure
        carbon_dioxide = constructions["CO2"].receipt.structure
        self.assertIsNotNone(water)
        self.assertIsNotNone(carbon_dioxide)
        self.assertEqual(water["participating_dimension_count"], 3)
        self.assertEqual(carbon_dioxide["participating_dimension_count"], 3)
        self.assertFalse(water["ternary_coupling_declared"])
        self.assertEqual(
            topology_structure_readout(water),
            topology_structure_readout(carbon_dioxide),
        )
        water_charged = charged_structure_readout(water)
        co2_charged = charged_structure_readout(carbon_dioxide)
        self.assertNotEqual(water_charged, co2_charged)
        self.assertEqual(
            water_charged[0],
            (
                (2, ((8, 1), 1), ("O#2", "H#0")),
                (2, ((8, 1), 1), ("O#2", "H#1")),
            ),
        )
        self.assertEqual(
            co2_charged[0],
            (
                (2, ((6, 8), 1), ("C#0", "O#1")),
                (2, ((6, 8), 1), ("C#0", "O#2")),
            ),
        )

    def test_sealed_shape_comparison_uses_charged_structure(self) -> None:
        constructions = construct_declared_molecules()
        self.assertEqual(set(constructions), {"H2", "H2O", "NH3", "CH4", "CO2"})
        record = compare_after_construction()
        sealed = json.loads(SEALED.read_text(encoding="utf-8"))["molecules"]
        known_shapes = {formula: sealed[formula]["known_shape"] for formula in constructions}

        self.assertTrue(record["opened_after_construction"])
        self.assertTrue(record["construction_omits_sealed_labels"])
        self.assertEqual(record["known_shapes"], known_shapes)
        self.assertGreater(len(set(known_shapes.values())), 1)
        self.assertEqual(known_shapes["H2O"], "bent")
        self.assertEqual(known_shapes["CO2"], "linear")
        self.assertEqual(known_shapes["H2"], "linear")

        self.assertTrue(record["topology_collapses_h2o_with_co2"])
        self.assertTrue(record["charged_distinguishes_h2o_from_co2"])
        self.assertTrue(record["linear_class_split_by_charged_structure"])

        standings = record["standings"]
        self.assertEqual(standings["charged_3_structure_as_sealed_shape_prediction"], "FALSIFIED")
        self.assertEqual(standings["topology_3_structure_as_sealed_shape_prediction"], "FALSIFIED")
        self.assertEqual(standings["ucns_mobius_as_sealed_shape_prediction"], "FALSIFIED")
        self.assertEqual(standings["atomic_shells_as_sealed_shape_prediction"], "FALSIFIED")

        control = {f: matched_information_control(c.invariants) for f, c in constructions.items()}
        self.assertNotEqual(control["H2O"], control["CO2"])
        self.assertEqual(len(set(control.values())), len(constructions))


if __name__ == "__main__":
    unittest.main()
