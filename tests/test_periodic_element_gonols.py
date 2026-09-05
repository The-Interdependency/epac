from __future__ import annotations

import sys
import unittest
from pathlib import Path

EPAC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EPAC_ROOT))

from epac_dimensional_arity import (
    charged_structure_readout,
    has_declared_coupling,
    quaternion_structure_readout,
    space,
)
from epac_periodic import construct_element_gonol, construct_periodic_table, replay_element_gonol


class PeriodicElementGonolTest(unittest.TestCase):
    def test_constructs_z1_to_z18(self) -> None:
        table = construct_periodic_table()
        self.assertEqual(len(table), 18)
        self.assertEqual(set(table), {
            "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
            "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
        })
        carbon = table["C"]
        options = dict(carbon.gonol.carried_options)
        self.assertEqual(options["Z"], "6")
        self.assertEqual(options["electron-configuration"], "1s2.2s2.2p2")
        self.assertEqual(options["valence-electrons"], "4")
        self.assertEqual(options["unpaired-valence-count"], "2")
        self.assertEqual(options["promoted-unpaired-count"], "4")
        self.assertEqual(carbon.constructor_id, "epac.public_gonol")
        self.assertEqual(len(carbon.gonol.participants), 3)
        shells = [item for item in carbon.gonol.participants if item.relation == "epac.atomic.shell"]
        electrons = [e for shell in shells for e in shell.participants]
        self.assertEqual(len(electrons), 6)
        quantum = {(dict(e.carried_options)["n"], dict(e.carried_options)["l"], dict(e.carried_options)["m_l"], dict(e.carried_options)["m_s"]) for e in electrons}
        self.assertEqual(len(quantum), 6)
        oxygen = table["O"]
        self.assertEqual(dict(oxygen.gonol.carried_options)["unpaired-valence-lm"], "1:0,1:-1")

    def test_replay_matches(self) -> None:
        first = construct_element_gonol("O")
        second = replay_element_gonol(first)
        self.assertEqual(first.receipt_digest, second.receipt_digest)

    def test_hund_unpaired_and_shells(self) -> None:
        from epac_atomic import atomic_record

        carbon = atomic_record(6)
        oxygen = atomic_record(8)
        nitrogen = atomic_record(7)
        self.assertEqual(len(carbon.electrons), 6)
        self.assertEqual(tuple((e.l, e.m_l) for e in carbon.unpaired_valence), ((1, 1), (1, 0)))
        self.assertEqual(len(carbon.promoted_unpaired_valence), 4)
        self.assertEqual(
            len({e.index for e in carbon.promoted_unpaired_valence}),
            len(carbon.promoted_unpaired_valence),
        )
        self.assertEqual(tuple((e.l, e.m_l) for e in oxygen.unpaired_valence), ((1, 0), (1, -1)))
        self.assertEqual(len(nitrogen.unpaired_valence), 3)
        self.assertEqual({e.m_l for e in nitrogen.unpaired_valence}, {1, 0, -1})

    def test_every_electron_instance_has_nucleus_coupling(self) -> None:
        oxygen = construct_element_gonol("O")
        helium = construct_element_gonol("He")
        self.assertIsNotNone(oxygen.structure)
        oxygen_readout = charged_structure_readout(oxygen.structure)
        self.assertEqual(
            oxygen_readout[0],
            tuple(
                (2, ((8, -1), 1), ("epac.nucleus:O#0", f"epac.electron:O#0:{index}"))
                for index in range(8)
            ),
        )
        nucleus_degree = next(
            item for item in oxygen.structure["degree"] if item["dimension"] == "epac.nucleus:O#0"
        )
        self.assertEqual(nucleus_degree["degree"], 8)
        self.assertEqual(nucleus_degree["charge"], 8)
        helium_readout = charged_structure_readout(helium.structure)
        self.assertEqual(
            helium_readout[0],
            (
                (2, ((2, -1), 1), ("epac.nucleus:He#0", "epac.electron:He#0:0")),
                (2, ((2, -1), 1), ("epac.nucleus:He#0", "epac.electron:He#0:1")),
            ),
        )
        ids = {name for part in helium_readout[0] for name in part[2]}
        self.assertNotIn("H", ids)
        self.assertNotIn("e", ids)
        self.assertNotIn("He", ids)
        self.assertFalse(helium.structure["ternary_coupling_declared"])
        self.assertEqual(helium.structure["representation_dimension"], 4)
        self.assertEqual(helium.structure["participating_dimension_count"], 3)
        self.assertEqual(
            quaternion_structure_readout(helium.structure),
            (
                (
                    (1, 2, -1, -1),
                    ("epac.nucleus:He#0", "epac.electron:He#0:0", "epac.electron:He#0:1"),
                ),
            ),
        )
        hydrogen = construct_element_gonol("H")
        self.assertEqual(hydrogen.structure["participating_dimension_count"], 2)
        self.assertEqual(hydrogen.structure["representation_dimension"], 4)
        self.assertEqual(quaternion_structure_readout(hydrogen.structure), ())

    def test_nucleus_is_affixiation_of_proton_and_neutron_gonols(self) -> None:
        hydrogen = construct_element_gonol("H")
        helium = construct_element_gonol("He")
        oxygen = construct_element_gonol("O")
        h_nucleus = next(
            item for item in hydrogen.gonol.participants if item.relation == "epac.atomic.nucleus"
        )
        he_nucleus = next(
            item for item in helium.gonol.participants if item.relation == "epac.atomic.nucleus"
        )
        o_nucleus = next(
            item for item in oxygen.gonol.participants if item.relation == "epac.atomic.nucleus"
        )
        self.assertEqual([item.relation for item in h_nucleus.participants], ["epac.atomic.proton"])
        self.assertEqual(dict(h_nucleus.carried_options)["neutrons"], "0")
        self.assertEqual(h_nucleus.couplings, ())
        self.assertIsNone(h_nucleus.structure)
        self.assertEqual(
            [item.relation for item in he_nucleus.participants],
            [
                "epac.atomic.proton",
                "epac.atomic.proton",
                "epac.atomic.neutron",
                "epac.atomic.neutron",
            ],
        )
        self.assertEqual(dict(he_nucleus.participants[2].carried_options)["charge"], "0")
        self.assertEqual(dict(he_nucleus.participants[0].carried_options)["charge"], "1")
        he_ids = {name for part in he_nucleus.structure["parts"] for name in part["coupling"]}
        self.assertTrue(all(name.startswith("epac.proton:") or name.startswith("epac.neutron:") for name in he_ids))
        self.assertNotIn("H", he_ids)
        self.assertNotIn("e", he_ids)
        self.assertFalse(has_declared_coupling(
            space(
                ["epac.proton:He#0:0", "epac.proton:He#0:1", "epac.neutron:He#0:0", "epac.neutron:He#0:1"],
                [part["coupling"] for part in he_nucleus.structure["parts"]],
            ),
            ["epac.proton:He#0:0", "epac.proton:He#0:1"],
        ))
        self.assertEqual(len(he_nucleus.structure["parts"]), 4)
        self.assertEqual(
            quaternion_structure_readout(he_nucleus.structure),
            (
                (
                    (1, 1, 0, 0),
                    ("epac.proton:He#0:0", "epac.neutron:He#0:0", "epac.neutron:He#0:1"),
                ),
                (
                    (1, 1, 0, 0),
                    ("epac.proton:He#0:1", "epac.neutron:He#0:0", "epac.neutron:He#0:1"),
                ),
            ),
        )
        self.assertEqual(len(o_nucleus.participants), 16)
        self.assertEqual(
            sum(1 for item in o_nucleus.participants if item.relation == "epac.atomic.neutron"),
            8,
        )
        electron_ids = {
            name
            for part in oxygen.structure["parts"]
            for name in part["coupling"]
        }
        self.assertFalse(any(name.startswith("epac.proton:") for name in electron_ids))
        self.assertFalse(any(name.startswith("epac.neutron:") for name in electron_ids))

    def test_construction_does_not_carry_shape_labels(self) -> None:
        receipt = construct_element_gonol("N")
        blob = str(receipt.gonol.carried_options) + receipt.gonol.relation
        for term in ("bent", "tetrahedral", "trigonal-pyramidal", "vsepr"):
            self.assertNotIn(term, blob.lower())


if __name__ == "__main__":
    unittest.main()
