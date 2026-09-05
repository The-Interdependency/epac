from __future__ import annotations

import sys
import unittest
from pathlib import Path

EPAC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EPAC_ROOT))

from epac_atomic import atomic_record
from epac_periodic import construct_element_gonol, replay_element_gonol


class AtomicPromotionTest(unittest.TestCase):
    def test_promoted_carbon_unpaired_accounting_and_ordering(self) -> None:
        carbon = atomic_record(6)
        self.assertEqual(carbon.configuration, "1s2.2s2.2p2")
        self.assertEqual(tuple((e.l, e.m_l) for e in carbon.unpaired_valence), ((1, 1), (1, 0)))
        promoted = carbon.promoted_unpaired_valence
        self.assertEqual(len(promoted), 4)
        # Every promoted unpaired electron uses the m_s = +1 convention.
        self.assertTrue(all(e.m_s == 1 for e in promoted))
        self.assertEqual(len({e.index for e in promoted}), len(promoted))
        # Canonical subshell ordering: s before p, p orbitals ascending m_l.
        self.assertEqual(
            tuple((e.l, e.m_l) for e in promoted),
            ((0, 0), (1, -1), (1, 0), (1, 1)),
        )
        self.assertEqual({e.subshell for e in promoted}, {"2s", "2p"})

    def test_promoted_beryllium_unpaired_accounting_and_ordering(self) -> None:
        beryllium = atomic_record(4)
        self.assertEqual(beryllium.configuration, "1s2.2s2")
        promoted = beryllium.promoted_unpaired_valence
        self.assertEqual(len(promoted), 2)
        self.assertTrue(all(e.m_s == 1 for e in promoted))
        self.assertEqual(tuple((e.l, e.m_l) for e in promoted), ((0, 0), (1, 1)))

    def test_ordinary_atoms_do_not_promote_without_an_empty_valence_p(self) -> None:
        # Helium has no valence shell; oxygen and nitrogen have no empty
        # valence p orbital, so their promoted sets equal their ground sets.
        helium = atomic_record(2)
        oxygen = atomic_record(8)
        nitrogen = atomic_record(7)
        self.assertEqual(helium.promoted_unpaired_valence, ())
        self.assertEqual(helium.unpaired_valence, ())
        self.assertEqual(
            tuple((e.l, e.m_l) for e in oxygen.promoted_unpaired_valence),
            ((1, 0), (1, -1)),
        )
        self.assertEqual(
            tuple((e.l, e.m_l) for e in oxygen.promoted_unpaired_valence),
            tuple((e.l, e.m_l) for e in oxygen.unpaired_valence),
        )
        self.assertEqual(len(nitrogen.promoted_unpaired_valence), 3)
        self.assertEqual(
            tuple((e.l, e.m_l) for e in nitrogen.promoted_unpaired_valence),
            tuple((e.l, e.m_l) for e in nitrogen.unpaired_valence),
        )

    def test_configuration_serialization_round_trip(self) -> None:
        carbon = construct_element_gonol("C")
        options = dict(carbon.gonol.carried_options)
        self.assertEqual(options["electron-configuration"], "1s2.2s2.2p2")
        self.assertEqual(options["unpaired-valence-lm"], "1:1,1:0")
        self.assertEqual(options["promoted-unpaired-count"], "4")
        self.assertEqual(options["promoted-unpaired-lm"], "0:0,1:-1,1:0,1:1")
        replayed = replay_element_gonol(carbon)
        self.assertEqual(carbon.receipt_digest, replayed.receipt_digest)


if __name__ == "__main__":
    unittest.main()
