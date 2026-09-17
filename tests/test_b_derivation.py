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

    def test_reproduces_nine_locked_formulas(self) -> None:
        report = freeze_b_derivation()
        for entry in report["locked_formula_reproduction"]:
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
            self.assertEqual(entry["missing_state_variable"], "(n-1)d valence participation")
        self.assertIn("(n-1)d", report["missing_state_variable"])

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


if __name__ == "__main__":
    unittest.main()
