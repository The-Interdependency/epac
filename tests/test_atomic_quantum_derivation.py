# === CHECKS ===
# id: check_atomic_period_is_outermost_principal_quantum_number
#   proves: atomic_period_is_outermost_principal_quantum_number
#   call: self::test_period_is_outermost_principal_quantum_number
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_atomic_valence_is_outermost_shell_occupancy
#   proves: atomic_valence_is_outermost_shell_occupancy
#   call: self::test_valence_is_outermost_shell_occupancy
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_atomic_derivation_is_from_construction_not_lookup
#   proves: atomic_derivation_is_from_construction_not_lookup
#   call: self::test_derivation_is_from_construction_not_lookup
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
#
# id: check_atomic_quantum_receipts_fail_closed
#   proves: atomic_quantum_receipts_fail_closed
#   call: self::test_quantum_receipts_fail_closed
#   requires: python3
#   timeout: 10
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import json
import unittest

from epac_atomic import atomic_record
from epac_atomic_derivation import (
    SCHEMA_SET,
    AtomicQuantumReceiptError,
    derive_period,
    derive_valence_electrons,
    freeze_atomic_quantum_receipts,
    prove_derivation_not_lookup,
    replay_atomic_quantum_receipts,
)


class AtomicQuantumDerivationTest(unittest.TestCase):
    def test_period_is_outermost_principal_quantum_number(self) -> None:
        for Z in range(1, 19):
            record = atomic_record(Z)
            self.assertEqual(
                derive_period(record.electrons),
                record.period,
                f"Z={Z}",
            )

    def test_valence_is_outermost_shell_occupancy(self) -> None:
        for Z in range(1, 19):
            record = atomic_record(Z)
            self.assertEqual(
                derive_valence_electrons(record.electrons),
                record.valence_electrons,
                f"Z={Z}",
            )

    def test_derivation_is_from_construction_not_lookup(self) -> None:
        proof = prove_derivation_not_lookup()
        self.assertTrue(proof["period_matches_for_all"])
        self.assertTrue(proof["valence_matches_for_all"])
        self.assertFalse(proof["lookup_used"])
        self.assertEqual(
            proof["derivation_inputs"],
            "electron states only (n, l, m_l, m_s)",
        )

    def test_quantum_receipts_fail_closed(self) -> None:
        frozen = freeze_atomic_quantum_receipts()
        self.assertEqual(frozen["schema"], SCHEMA_SET)
        self.assertEqual(len(frozen["records"]), 18)
        for receipt in frozen["records"]:
            self.assertEqual(receipt["period_derived"], receipt["period_recorded"])
            self.assertEqual(
                receipt["valence_electrons_derived"],
                receipt["valence_electrons_recorded"],
            )
            self.assertFalse(receipt["lookup_used"])

        data = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
        replayed = replay_atomic_quantum_receipts(data)
        self.assertEqual(replayed["receipt_sha256"], frozen["receipt_sha256"])

        tampered = bytearray(data)
        tampered[30] ^= 0x01
        with self.assertRaises(AtomicQuantumReceiptError):
            replay_atomic_quantum_receipts(bytes(tampered))


if __name__ == "__main__":
    unittest.main()
