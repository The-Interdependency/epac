from __future__ import annotations

import sys
import unittest
from pathlib import Path

EPAC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EPAC_ROOT))

from epac_dimensional_arity import space, geometry_from_declared_couplings
from epac_public_gonol import (
    CONSTRUCTOR_ID,
    PINNED_PUBLIC_GONOL_SHA256,
    PublicGonolConstructionError,
    construct_public_gonol,
    replay_public_gonol,
)
from ucns import PUBLIC_GONOL_SHA256, native_mobius_state, public_gonol_function


class EpacPublicGonolTest(unittest.TestCase):
    def test_constructor_is_not_edcm(self) -> None:
        receipt = construct_public_gonol(
            source_id="epac.test:O",
            relation="epac.atomic.element",
            identity_glyph="O",
            carried_options=(("symbol", "O"), ("Z", "8")),
        )
        self.assertEqual(receipt.constructor_id, CONSTRUCTOR_ID)
        self.assertEqual(CONSTRUCTOR_ID, "epac.public_gonol")
        self.assertEqual(receipt.gonol.identity_glyph, "O")
        self.assertEqual(receipt.gonol.carrier_index, public_gonol_function("O").index)
        self.assertEqual(PINNED_PUBLIC_GONOL_SHA256, PUBLIC_GONOL_SHA256)
        for name in ("epac_public_gonol.py", "epac_periodic.py", "epac_molecular.py"):
            source = (EPAC_ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("from edcm", source, name)
            self.assertNotIn("import edcm", source, name)

    def test_two_letter_symbol_has_no_single_glyph(self) -> None:
        receipt = construct_public_gonol(
            source_id="epac.test:He",
            relation="epac.atomic.element",
            carried_options=(("symbol", "He"), ("Z", "2")),
        )
        self.assertIsNone(receipt.gonol.identity_glyph)
        self.assertIsNone(receipt.gonol.carrier_index)

    def test_replay_matches(self) -> None:
        first = construct_public_gonol(
            source_id="epac.test:H",
            relation="epac.atomic.element",
            identity_glyph="H",
            carried_options=(("symbol", "H"), ("Z", "1")),
        )
        second = replay_public_gonol(first)
        self.assertEqual(first.receipt_digest, second.receipt_digest)

    def test_charged_couplings_are_the_structure(self) -> None:
        declared = space(
            ["z", "x", "y"],
            [["z", "x"], ["z", "y"]],
            charges={"z": 8, "x": 1, "y": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        receipt = construct_public_gonol(
            source_id="epac.test:H2O-structure",
            relation="epac.affixiation.unpaired-valence",
            couplings=geometry["couplings"],
            structure=geometry["structure"],
        )
        self.assertEqual(receipt.structure["participating_dimension_count"], 3)
        self.assertFalse(receipt.structure["ternary_coupling_declared"])
        self.assertFalse(receipt.structure["inferred_cartesian_embedding"])
        self.assertEqual(
            [part["charge_state"] for part in receipt.structure["parts"]],
            [((8, 1), 1), ((8, 1), 1)],
        )
        self.assertEqual(native_mobius_state(0).frame.sign, 1)

    def test_nested_geometry_is_frozen_after_closure(self) -> None:
        declared = space(
            ["z", "x"],
            [["z", "x"]],
            charges={"z": 8, "x": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        receipt = construct_public_gonol(
            source_id="epac.test:frozen-structure",
            relation="epac.affixiation.unpaired-valence",
            couplings=geometry["couplings"],
            structure=geometry["structure"],
        )
        geometry["structure"]["parts"][0]["charge_state"] = ((999, 1), 1)
        self.assertEqual(receipt.structure["parts"][0]["charge_state"], ((8, 1), 1))
        with self.assertRaises(TypeError):
            receipt.structure["parts"][0]["charge_state"] = ((999, 1), 1)
        with self.assertRaises(AttributeError):
            receipt.structure["parts"].append({})
        self.assertEqual(replay_public_gonol(receipt).receipt_digest, receipt.receipt_digest)

    def test_structure_must_match_declared_couplings(self) -> None:
        declared = space(
            ["z", "x"],
            [["z", "x"]],
            charges={"z": 8, "x": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        bad_structure = {
            **geometry["structure"],
            "parts": (
                {
                    "coupling": ("z", "x"),
                    "arity": 2,
                    "charge_state": ((8, 99), 1),
                },
            ),
        }
        with self.assertRaisesRegex(PublicGonolConstructionError, "structure must match"):
            construct_public_gonol(
                source_id="epac.test:bad-structure",
                relation="epac.affixiation.unpaired-valence",
                couplings=geometry["couplings"],
                structure=bad_structure,
            )
        with self.assertRaisesRegex(PublicGonolConstructionError, "supplied together"):
            construct_public_gonol(
                source_id="epac.test:missing-structure",
                relation="epac.affixiation.unpaired-valence",
                couplings=geometry["couplings"],
            )

    def test_unknown_glyph_fails_closed(self) -> None:
        with self.assertRaises(PublicGonolConstructionError):
            construct_public_gonol(
                source_id="epac.test:bad",
                relation="epac.atomic.element",
                identity_glyph="He",
            )


if __name__ == "__main__":
    unittest.main()
