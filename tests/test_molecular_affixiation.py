from __future__ import annotations

import sys
import unittest
from pathlib import Path

EPAC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EPAC_ROOT))

from epac_dimensional_arity import quaternion_structure_readout
from epac_molecular import construct_declared_molecules, replay_molecule


class MolecularAffixiationTest(unittest.TestCase):
    def test_declared_formulas_close_and_replay(self) -> None:
        molecules = construct_declared_molecules()
        self.assertEqual(set(molecules), {"H2", "H2O", "NH3", "CH4", "CO2"})
        for formula, construction in molecules.items():
            replayed = replay_molecule(construction)
            self.assertEqual(construction.receipt.receipt_digest, replayed.receipt_digest, formula)

    def test_unpaired_valence_and_shells_are_used(self) -> None:
        molecules = construct_declared_molecules()
        water = molecules["H2O"].invariants
        methane = molecules["CH4"].invariants
        carbon_dioxide = molecules["CO2"].invariants
        self.assertEqual(water["center_symbol"], "O")
        self.assertEqual(water["center_configuration"], "1s2.2s2.2p4")
        self.assertEqual(water["center_unpaired_lm"], ["1:0", "1:-1"])
        self.assertFalse(water["ligand_has_p"])
        self.assertEqual(water["center_used_atomic_promotion"], False)
        self.assertEqual(methane["center_used_atomic_promotion"], True)
        self.assertEqual(methane["center_unpaired_lm"], ["0:0", "1:-1", "1:0", "1:1"])
        self.assertTrue(carbon_dioxide["ligand_has_p"])
        self.assertEqual(carbon_dioxide["center_unpaired_lm"], ["0:0", "1:-1", "1:0", "1:1"])
        self.assertEqual(carbon_dioxide["center_attachment_site_count"], 4)
        self.assertEqual(carbon_dioxide["ligand_attachment_site_count"], 4)

    def test_declared_couplings_are_binary_and_do_not_fill_ambient(self) -> None:
        molecules = construct_declared_molecules()
        water = molecules["H2O"].invariants["dimensional_geometry"]
        self.assertEqual(water["ambient_count"], 3)
        self.assertEqual([c["arity"] for c in water["couplings"]], [2, 2])
        ids = [c["declared_ids"] for c in water["couplings"]]
        self.assertEqual(len(ids), 2)
        self.assertTrue(all(len(item) == 2 for item in ids))
        methane = molecules["CH4"].invariants["dimensional_geometry"]
        self.assertEqual(methane["ambient_count"], 5)
        self.assertEqual([c["arity"] for c in methane["couplings"]], [2, 2, 2, 2])
        self.assertFalse(any(c["arity"] == 5 for c in methane["couplings"]))
        self.assertFalse(methane["inferred_from_ambient"])
        self.assertFalse(methane["inferred_higher_arity_from_overlap"])
        self.assertEqual(water["structure"]["participating_dimension_count"], 3)
        self.assertFalse(water["structure"]["ternary_coupling_declared"])
        self.assertFalse(water["structure"]["inferred_cartesian_embedding"])
        self.assertEqual(water["couplings"][0]["slot_charges"], (8, 1))
        self.assertEqual(methane["couplings"][0]["slot_charges"], (6, 1))
        water_receipt = molecules["H2O"].receipt
        self.assertEqual(water_receipt.constructor_id, "epac.public_gonol")
        self.assertEqual(len(water_receipt.structure["parts"]), 2)
        water_instances = molecules["H2O"].invariants["oriented_instance_couplings"]
        self.assertEqual(len(water_instances), 2)
        self.assertEqual({item[0] for item in water_instances}, {"O#2"})
        self.assertEqual([item[1] for item in water_instances], ["H#0", "H#1"])
        methane_instances = molecules["CH4"].invariants["oriented_instance_couplings"]
        self.assertEqual(len(methane_instances), 4)
        self.assertTrue(all(item[0] == "C#0" for item in methane_instances))
        self.assertEqual([item[1] for item in methane_instances], ["H#1", "H#2", "H#3", "H#4"])
        self.assertEqual(molecules["H2"].invariants["oriented_instance_couplings"], ())
        water_ids = {name for part in water_receipt.structure["parts"] for name in part["coupling"]}
        self.assertEqual(water_ids, {"O#2", "H#0", "H#1"})
        self.assertFalse(any(name.startswith("epac.electron:") for name in water_ids))
        oxygen = next(
            item
            for item in water_receipt.gonol.participants
            if dict(item.carried_options).get("symbol") == "O"
        )
        self.assertEqual(len(oxygen.structure["parts"]), 8)
        self.assertTrue(
            all(part["coupling"][0] == "epac.nucleus:O#2" for part in oxygen.structure["parts"])
        )
        o_nucleus = next(item for item in oxygen.participants if item.relation == "epac.atomic.nucleus")
        self.assertEqual(
            sum(1 for item in o_nucleus.participants if item.relation == "epac.atomic.neutron"),
            8,
        )
        self.assertEqual(
            sum(1 for item in o_nucleus.participants if item.relation == "epac.atomic.proton"),
            8,
        )
        self.assertFalse(any(name.startswith("epac.neutron:") for name in water_ids))
        self.assertEqual(water_receipt.structure["representation_dimension"], 4)
        self.assertEqual(water_receipt.structure["participating_dimension_count"], 3)
        self.assertEqual(
            quaternion_structure_readout(water_receipt.structure),
            (((1, 8, 1, 1), ("O#2", "H#0", "H#1")),),
        )
        self.assertEqual(
            quaternion_structure_readout(molecules["CO2"].receipt.structure),
            (((1, 6, 8, 8), ("C#0", "O#1", "O#2")),),
        )
        self.assertEqual(quaternion_structure_readout(molecules["H2"].receipt.structure), ())
        self.assertEqual(len(quaternion_structure_readout(molecules["CH4"].receipt.structure)), 6)

    def test_ucns_coupling_binds_declared_attachments(self) -> None:
        molecules = construct_declared_molecules()
        signatures = {formula: item.invariants["ucns_coupling_signature"] for formula, item in molecules.items()}
        self.assertEqual(len(set(signatures.values())), len(molecules))
        self.assertEqual({signature[0] for signature in signatures.values()}, {"ucns.native-mobius-root-loop"})
        self.assertEqual(len(signatures["CO2"][2]), 4)
        self.assertEqual(len(signatures["H2O"][2]), 2)

    def test_construction_text_avoids_sealed_labels(self) -> None:
        source = (EPAC_ROOT / "epac_molecular.py").read_text(encoding="utf-8").lower()
        for term in ("bent", "tetrahedral", "trigonal-pyramidal", "vsepr", "linear"):
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
