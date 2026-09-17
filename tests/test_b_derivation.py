# === CHECKS ===
# id: check_b_derivation_uses_occupancy_charge_bond_state_only
#   proves: b_derivation_uses_occupancy_charge_bond_state_only
#   call: self::test_uses_occupancy_charge_bond_state_only
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_b_derivation_reproduces_nine_locked_formulas
#   proves: b_derivation_reproduces_nine_locked_formulas
#   call: self::test_reproduces_nine_locked_formulas
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_b_derivation_reproduces_bare_element_b
#   proves: b_derivation_reproduces_bare_element_b
#   call: self::test_reproduces_bare_element_b
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_b_derivation_records_transition_metal_failure
#   proves: b_derivation_records_transition_metal_failure
#   call: self::test_records_transition_metal_failure
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_b_derivation_receipts_fail_closed
#   proves: b_derivation_receipts_fail_closed
#   call: self::test_receipts_fail_closed
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import json
import unittest

from epac_atomic import atomic_record
from epac_b_derivation import (
    SCHEMA_SET,
    BDerivationError,
    bare_element_b,
    freeze_b_derivation,
    ion_b,
    ligand_contribution,
    molecule_b,
    replay_b_derivation,
)


class BDerivationTest(unittest.TestCase):
    def test_uses_occupancy_charge_bond_state_only(self) -> None:
        report = freeze_b_derivation()
        rule = report["rule"]
        self.assertIn("electron_count", rule["bare_d"])
        self.assertEqual(rule["ion_electron_count"], "Z - charge")
        self.assertIn("unpaired valence", rule["ligand_K"])
        self.assertIn("ligand K only", rule["molecule_c"])
        self.assertIn("never counted", rule["molecule_c"])

    def test_supported_domain_and_nh4_ligand_selection(self) -> None:
        report = freeze_b_derivation()
        self.assertEqual(
            report["supported_domain"],
            ["bare atoms", "ions", "diatomics", "singleton-center star topologies"],
        )
        nh4 = next(
            entry
            for entry in report["held_out_molecule_b_evaluations"]
            if entry["formula"] == "NH4+"
        )
        # Only ligand K counts: H x 4 = 4; center N K = 3 is never counted.
        self.assertEqual(nh4["evaluated_b"], [3, 5, 4])
        self.assertEqual(nh4["status"], "evaluation-only")

    def test_reproduces_nine_locked_formulas(self) -> None:
        report = freeze_b_derivation()
        for entry in report["locked_formula_b_evaluations"]:
            self.assertTrue(entry["matches"], entry["formula"])

    def test_reproduces_bare_element_b(self) -> None:
        for Z in range(1, 19):
            record = atomic_record(Z)
            d, c = bare_element_b(record)[1], bare_element_b(record)[2]
            self.assertEqual(d, Z + 1)
            self.assertEqual(c, 0)

    def test_records_transition_metal_failure(self) -> None:
        report = freeze_b_derivation()
        failure = report["transition_metal_failure"]
        self.assertTrue(failure)
        for entry in failure:
            self.assertEqual(
                entry["missing_state_variable"],
                "bond-context active-orbital set (may include (n-1)d)",
            )
        self.assertIn("bond-context active-orbital set", report["missing_state_variable"])

    def test_receipts_fail_closed(self) -> None:
        frozen = freeze_b_derivation()
        self.assertEqual(frozen["schema"], SCHEMA_SET)
        data = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
        replayed = replay_b_derivation(data)
        self.assertEqual(replayed["receipt_sha256"], frozen["receipt_sha256"])

        tampered = bytearray(data)
        tampered[25] ^= 0x01
        with self.assertRaises(BDerivationError):
            replay_b_derivation(bytes(tampered))

    def test_ions_use_charge_rule(self) -> None:
        iron = atomic_record(26)
        self.assertEqual(ion_b(iron, 2), (3, 25, 0))  # 26 electrons -> 24 + 1 axis
        self.assertEqual(ion_b(iron, 3), (3, 24, 0))

    def test_active_orbital_set_derives_for_supplied_topologies(self) -> None:
        from epac_b_derivation import (
            active_orbital_set,
            evaluate_transition_metal_topology,
        )

        scandium = atomic_record(21)
        active = active_orbital_set(scandium, charge=3)
        self.assertEqual(active["kind"], "transition-metal")
        self.assertEqual(
            [sub["subshell"] for sub in active["subshells"]],
            ["4s", "3d"],
        )
        self.assertEqual(active["unpaired_electrons"], 0)
        self.assertEqual(active["vacant_orbitals"], 6)  # 4s0 + 3d0
        self.assertEqual(active["coordination_capacity"], "UNRESOLVED")
        self.assertEqual(active["capacity_rule_status"], "FALSIFIED")

        sccl3 = evaluate_transition_metal_topology("ScCl3")
        self.assertEqual(sccl3["b_value"], [3, 4, 3])
        self.assertEqual(sccl3["ligand_count_within_center_capacity"], "UNRESOLVED")

        report = freeze_b_derivation()
        self.assertEqual(report["capacity_rule_status"], "FALSIFIED")
        evaluations = report["transition_metal_topology_evaluations"]
        by_name = {entry["topology"]: entry for entry in evaluations}
        self.assertEqual(by_name["TiCl4"]["b_value"], [3, 5, 4])
        self.assertEqual(
            by_name["FeCl3"]["center_active_orbital_set"]["unpaired_electrons"],
            5,  # Fe3+: 3d5, five unpaired within the d subshell
        )

    def test_zn2_plus_d10_has_zero_unpaired_regression(self) -> None:
        from epac_b_derivation import active_orbital_set

        zinc = atomic_record(30)
        active = active_orbital_set(zinc, charge=2)
        by_subshell = {sub["subshell"]: sub for sub in active["subshells"]}
        self.assertEqual(by_subshell["3d"]["electrons"], 10)
        self.assertEqual(by_subshell["3d"]["unpaired"], 0)
        self.assertEqual(by_subshell["4s"]["electrons"], 0)
        self.assertEqual(active["unpaired_electrons"], 0)
        self.assertEqual(active["coordination_capacity"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
