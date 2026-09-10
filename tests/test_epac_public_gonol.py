from __future__ import annotations

# === CHECKS ===
# id: check_epac_public_gonol_retained_constructor_boundary
#   proves: epac_public_gonol_binds_ucns_carrier_identity, epac_public_gonol_replays_byte_identical, charged_oriented_couplings_are_the_structure
#   call: self::check_epac_public_gonol_retained_constructor_boundary
#   requires: python3
#   timeout: 30
#   mutates: none
#   cleanup: none
# === END CHECKS ===

import copy
from dataclasses import replace
import inspect
import sys
import unittest
from pathlib import Path

EPAC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EPAC_ROOT))

from epac_dimensional_arity import DimensionalArityError, space, geometry_from_declared_couplings
import epac_public_gonol as public_gonol_module
import epac_ucns_provenance
from epac_public_gonol import (
    CONSTRUCTOR_ID,
    CONSTRUCTOR_VERSION,
    PINNED_PUBLIC_GONOL_SHA256,
    PINNED_UCNS_COMMIT,
    PublicGonolConstructionError,
    construct_public_gonol,
    replay_public_gonol,
)
from ucns import PUBLIC_GONOL_SHA256, native_mobius_state, public_gonol_function


def _reseal_retained_gonol(gonol, **changes):
    candidate = replace(gonol, **changes)
    gonol_payload = public_gonol_module._atomic_payload(
        source_id=candidate.source_id,
        occurrence=candidate.occurrence,
        relation=candidate.relation,
        identity_glyph=candidate.identity_glyph,
        carrier_index=candidate.carrier_index,
        participants=candidate.participants,
        carried_options=candidate.carried_options,
        couplings=candidate.couplings,
        structure=candidate.structure,
    )
    atomic_id = public_gonol_module._digest({"atomic": gonol_payload})
    geometry_digest = public_gonol_module._digest({"geometry": candidate.geometry})
    receipt_digest = public_gonol_module._digest(
        public_gonol_module._receipt_payload(
            source_id=candidate.source_id,
            gonol_payload=gonol_payload,
            geometry=candidate.geometry,
            atomic_id=atomic_id,
            geometry_digest=geometry_digest,
        )
    )
    return replace(
        candidate,
        atomic_id=atomic_id,
        geometry_digest=geometry_digest,
        receipt_digest=receipt_digest,
    )


class EpacPublicGonolTest(unittest.TestCase):
    def assert_retained_rejected(self, child, pattern: str) -> None:
        with self.assertRaisesRegex(PublicGonolConstructionError, pattern):
            construct_public_gonol(
                source_id="epac.test:retained-boundary-parent",
                relation="epac.molecular.participation",
                participants=(child,),
            )
        parent = construct_public_gonol(
            source_id="epac.test:replay-boundary-parent",
            relation="epac.molecular.participation",
        )
        forged_parent = replace(
            parent,
            gonol=replace(parent.gonol, participants=(child,)),
        )
        with self.assertRaisesRegex(PublicGonolConstructionError, pattern):
            replay_public_gonol(forged_parent)

    def test_constructor_is_not_edcm(self) -> None:
        receipt = construct_public_gonol(
            source_id="epac.test:O",
            relation="epac.atomic.element",
            identity_glyph="O",
            carried_options=(("symbol", "O"), ("Z", "8")),
        )
        self.assertEqual(receipt.constructor_id, CONSTRUCTOR_ID)
        self.assertEqual(CONSTRUCTOR_ID, "epac.public_gonol")
        self.assertEqual(CONSTRUCTOR_VERSION, "v2")
        self.assertEqual(receipt.gonol.identity_glyph, "O")
        self.assertEqual(receipt.gonol.carrier_index, public_gonol_function("O").index)
        self.assertEqual(receipt.geometry["ucns_commit"], PINNED_UCNS_COMMIT)
        self.assertEqual(receipt.gonol.geometry, receipt.geometry)
        self.assertEqual(PINNED_UCNS_COMMIT, "828c0b8bbcfc267efb5701da714191c1f73a81ff")
        self.assertEqual(
            PINNED_PUBLIC_GONOL_SHA256,
            "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5",
        )
        self.assertEqual(PINNED_PUBLIC_GONOL_SHA256, PUBLIC_GONOL_SHA256)
        source = (EPAC_ROOT / "epac_public_gonol.py").read_text(encoding="utf-8")
        self.assertIn(
            'PINNED_PUBLIC_GONOL_SHA256 = "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5"',
            source,
        )
        self.assertNotIn("PINNED_PUBLIC_GONOL_SHA256 = PUBLIC_GONOL_SHA256", source)
        for name in ("epac_public_gonol.py", "epac_periodic.py", "epac_molecular.py"):
            module_source = (EPAC_ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("from edcm", module_source, name)
            self.assertNotIn("import edcm", module_source, name)

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

        contradictory_geometry = dict(first.gonol.geometry)
        contradictory_geometry["ucns_commit"] = (
            "0" * 40
            if contradictory_geometry["ucns_commit"] != "0" * 40
            else "1" * 40
        )
        contradictory_gonol = replace(
            first.gonol,
            geometry=contradictory_geometry,
        )
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "retained receipt geometries disagree"
        ):
            replay_public_gonol(replace(first, gonol=contradictory_gonol))

        with self.assertRaisesRegex(
            PublicGonolConstructionError, "geometry digest"
        ):
            replay_public_gonol(
                replace(first, gonol=replace(first.gonol, geometry_digest="0" * 64))
            )

        with self.assertRaisesRegex(
            PublicGonolConstructionError, "receipt envelope"
        ):
            replay_public_gonol(replace(first, constructor_version="v1"))

        parent = construct_public_gonol(
            source_id="epac.test:H2",
            relation="epac.molecular.participation",
            participants=(first.gonol,),
        )
        forged_child_geometry = dict(first.gonol.geometry)
        forged_child_geometry["ucns_commit"] = "forged-child-commit"
        forged_child = replace(first.gonol, geometry=forged_child_geometry)
        forged_parent = replace(
            parent,
            gonol=replace(parent.gonol, participants=(forged_child,)),
        )
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "retained geometry digest"
        ):
            replay_public_gonol(forged_parent)
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "retained geometry digest"
        ):
            construct_public_gonol(
                source_id="epac.test:forged-child-parent",
                relation="epac.molecular.participation",
                participants=(forged_child,),
            )

        malformed_structure = replace(first.gonol, structure="not-a-mapping")
        malformed_parent = replace(
            parent,
            gonol=replace(parent.gonol, participants=(malformed_structure,)),
        )
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "retained structure must be a mapping"
        ):
            replay_public_gonol(malformed_parent)
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "retained structure must be a mapping"
        ):
            construct_public_gonol(
                source_id="epac.test:malformed-structure-parent",
                relation="epac.molecular.participation",
                participants=(malformed_structure,),
            )

        forged_identity = replace(first.gonol, source_id="epac.test:forged-H")
        forged_identity_parent = replace(
            parent,
            gonol=replace(parent.gonol, participants=(forged_identity,)),
        )
        with self.assertRaisesRegex(PublicGonolConstructionError, "atomic id"):
            replay_public_gonol(forged_identity_parent)
        with self.assertRaisesRegex(PublicGonolConstructionError, "atomic id"):
            construct_public_gonol(
                source_id="epac.test:forged-identity-parent",
                relation="epac.molecular.participation",
                participants=(forged_identity,),
            )

        bad_index = first.gonol.carrier_index + 1
        bad_payload = public_gonol_module._atomic_payload(
            source_id=first.gonol.source_id,
            occurrence=first.gonol.occurrence,
            relation=first.gonol.relation,
            identity_glyph=first.gonol.identity_glyph,
            carrier_index=bad_index,
            participants=first.gonol.participants,
            carried_options=first.gonol.carried_options,
            couplings=first.gonol.couplings,
            structure=first.gonol.structure,
        )
        bad_atomic_id = public_gonol_module._digest({"atomic": bad_payload})
        bad_receipt_digest = public_gonol_module._digest(
            public_gonol_module._receipt_payload(
                source_id=first.gonol.source_id,
                gonol_payload=bad_payload,
                geometry=first.gonol.geometry,
                atomic_id=bad_atomic_id,
                geometry_digest=first.gonol.geometry_digest,
            )
        )
        contradictory_carrier = replace(
            first.gonol,
            carrier_index=bad_index,
            atomic_id=bad_atomic_id,
            receipt_digest=bad_receipt_digest,
        )
        contradictory_parent = replace(
            parent,
            gonol=replace(parent.gonol, participants=(contradictory_carrier,)),
        )
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "carrier identity"
        ):
            replay_public_gonol(contradictory_parent)
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "carrier identity"
        ):
            construct_public_gonol(
                source_id="epac.test:contradictory-carrier-parent",
                relation="epac.molecular.participation",
                participants=(contradictory_carrier,),
            )

        mutable_geometry = public_gonol_module._json_ready(first.gonol.geometry)
        mutable_child = replace(first.gonol, geometry=mutable_geometry)
        frozen_parent = construct_public_gonol(
            source_id="epac.test:mutable-child-parent",
            relation="epac.molecular.participation",
            participants=(mutable_child,),
        )
        mutable_geometry["ucns_commit"] = "post-seal-drift"
        retained_geometry = frozen_parent.gonol.participants[0].geometry
        self.assertNotEqual(retained_geometry["ucns_commit"], "post-seal-drift")
        with self.assertRaises(TypeError):
            retained_geometry["ucns_commit"] = "blocked"

    def test_retained_geometry_requires_the_complete_constructor_schema(self) -> None:
        receipt = construct_public_gonol(
            source_id="epac.test:canonical-geometry",
            relation="epac.atomic.element",
            identity_glyph="O",
        )
        mutations = (
            ("state", "invented"),
            ("authority", "caller.asserted"),
            ("authority_binding", "implicit"),
            ("ucns_commit", "forged-commit"),
            ("ucns_commit", {"forged": "commit"}),
            ("carrier_digest", "0" * 64),
            ("mobius_epsilon_t0", -1),
            ("mobius_epsilon_t0", True),
            ("position_operation", "caller.asserted"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                geometry = public_gonol_module._json_ready(receipt.gonol.geometry)
                geometry[field] = value
                forged = _reseal_retained_gonol(receipt.gonol, geometry=geometry)
                self.assert_retained_rejected(forged, "retained")

        geometry = public_gonol_module._json_ready(receipt.gonol.geometry)
        geometry["invented_field"] = True
        self.assert_retained_rejected(
            _reseal_retained_gonol(receipt.gonol, geometry=geometry),
            "retained geometry is not canonical",
        )

    def test_retained_couplings_are_canonical_before_identity_checks(self) -> None:
        declared = space(
            ["z", "x", "y"],
            [["z", "x"], ["z", "y"]],
            charges={"z": 8, "x": 1, "y": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        receipt = construct_public_gonol(
            source_id="epac.test:canonical-retained-couplings",
            relation="epac.affixiation.unpaired-valence",
            couplings=geometry["couplings"],
            structure=geometry["structure"],
        )
        reversed_couplings = tuple(reversed(receipt.gonol.couplings))
        self.assertNotEqual(reversed_couplings, receipt.gonol.couplings)
        forged = _reseal_retained_gonol(
            receipt.gonol,
            couplings=reversed_couplings,
        )
        self.assert_retained_rejected(forged, "retained atomic id")

    def test_retained_scalars_reuse_constructor_validation(self) -> None:
        receipt = construct_public_gonol(
            source_id="epac.test:canonical-scalars",
            relation="epac.atomic.element",
            carried_options=(("symbol", "O"),),
        )
        mutations = (
            ({"source_id": ""}, "source_id"),
            ({"relation": "   "}, "relation"),
            ({"occurrence": -1}, "occurrence"),
            ({"occurrence": True}, "occurrence"),
            ({"carried_options": (("", "O"),)}, "carried option key"),
            ({"carried_options": (("symbol", " "),)}, "carried option value"),
        )
        for changes, pattern in mutations:
            with self.subTest(changes=changes):
                forged = _reseal_retained_gonol(receipt.gonol, **changes)
                self.assert_retained_rejected(forged, pattern)

    def test_boolean_integer_aliases_are_rejected_at_every_retained_boundary(self) -> None:
        carrier = construct_public_gonol(
            source_id="epac.test:boolean-carrier",
            relation="epac.atomic.element",
            identity_glyph=public_gonol_function(1).glyph,
        )
        forged_carrier = _reseal_retained_gonol(
            carrier.gonol, carrier_index=True
        )
        self.assert_retained_rejected(forged_carrier, "carrier identity")

        outer_geometry = public_gonol_module._json_ready(carrier.geometry)
        outer_geometry["mobius_epsilon_t0"] = True
        with self.assertRaisesRegex(PublicGonolConstructionError, "geometries disagree"):
            replay_public_gonol(replace(carrier, geometry=outer_geometry))

        declared = space(
            ["z", "x"], [["z", "x"]], charges={"z": 8, "x": 1}
        )
        geometry = geometry_from_declared_couplings(declared)
        boolean_structure = copy.deepcopy(geometry["structure"])
        boolean_structure["inferred_cartesian_embedding"] = 0
        with self.assertRaisesRegex(PublicGonolConstructionError, "derived fields"):
            construct_public_gonol(
                source_id="epac.test:boolean-structure",
                relation="epac.affixiation.unpaired-valence",
                couplings=geometry["couplings"],
                structure=boolean_structure,
            )

        boolean_charge = copy.deepcopy(geometry["couplings"])
        boolean_charge[0]["charge_state"] = ((8, True), True)
        with self.assertRaisesRegex(PublicGonolConstructionError, "charge_state"):
            construct_public_gonol(
                source_id="epac.test:boolean-charge",
                relation="epac.affixiation.unpaired-valence",
                couplings=boolean_charge,
                structure=geometry["structure"],
            )

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

    def test_order_insensitive_derived_collections_still_seal(self) -> None:
        declared = space(
            ["x", "z", "y"],
            [["z", "x"], ["z", "y"]],
            charges={"z": 8, "x": 1, "y": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        structure = copy.deepcopy(geometry["structure"])
        structure["parts"] = tuple(reversed(structure["parts"]))
        structure["degree"] = tuple(reversed(structure["degree"]))
        structure["quaternions"] = tuple(reversed(structure["quaternions"]))
        receipt = construct_public_gonol(
            source_id="epac.test:ambient-order-seal",
            relation="epac.affixiation.unpaired-valence",
            couplings=geometry["couplings"],
            structure=structure,
        )
        self.assertEqual(receipt.structure["participating_dimension_count"], 3)

    def test_coupling_collection_order_is_canonicalized_before_sealing(self) -> None:
        declared = space(
            ["z", "x", "y"],
            [["z", "x"], ["z", "y"]],
            charges={"z": 8, "x": 1, "y": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        first = construct_public_gonol(
            source_id="epac.test:reordered-couplings",
            relation="epac.affixiation.unpaired-valence",
            couplings=geometry["couplings"],
            structure=geometry["structure"],
        )
        second = construct_public_gonol(
            source_id="epac.test:reordered-couplings",
            relation="epac.affixiation.unpaired-valence",
            couplings=tuple(reversed(geometry["couplings"])),
            structure=geometry["structure"],
        )
        self.assertEqual(first.gonol.couplings, second.gonol.couplings)
        self.assertEqual(first.receipt_digest, second.receipt_digest)

    def test_structure_order_is_canonicalized_before_sealing(self) -> None:
        declared = space(
            ["x", "z", "y"],
            [["z", "x"], ["z", "y"]],
            charges={"z": 8, "x": 1, "y": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        reordered = copy.deepcopy(geometry["structure"])
        reordered["parts"] = tuple(reversed(reordered["parts"]))
        reordered["degree"] = tuple(reversed(reordered["degree"]))
        reordered["quaternions"] = tuple(reversed(reordered["quaternions"]))
        first = construct_public_gonol(
            source_id="epac.test:reordered-structure",
            relation="epac.affixiation.unpaired-valence",
            couplings=geometry["couplings"],
            structure=geometry["structure"],
        )
        second = construct_public_gonol(
            source_id="epac.test:reordered-structure",
            relation="epac.affixiation.unpaired-valence",
            couplings=geometry["couplings"],
            structure=reordered,
        )
        self.assertEqual(first.gonol.structure, second.gonol.structure)
        self.assertEqual(first.receipt_digest, second.receipt_digest)

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
            ["z", "x", "y"],
            [["z", "x"], ["z", "y"]],
            charges={"z": 8, "x": 1, "y": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        bad_part = copy.deepcopy(geometry["structure"])
        bad_part["parts"][0]["charge_state"] = ((8, 99), 1)
        with self.assertRaisesRegex(PublicGonolConstructionError, "structure must match"):
            construct_public_gonol(
                source_id="epac.test:bad-part",
                relation="epac.affixiation.unpaired-valence",
                couplings=geometry["couplings"],
                structure=bad_part,
            )

        malformed_arity = copy.deepcopy(geometry["structure"])
        malformed_arity["parts"][0]["arity"] = None
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "structure part arity must be an integer"
        ):
            construct_public_gonol(
                source_id="epac.test:null-structure-arity",
                relation="epac.affixiation.unpaired-valence",
                couplings=geometry["couplings"],
                structure=malformed_arity,
            )

        nonmapping_part = copy.deepcopy(geometry["structure"])
        nonmapping_part["parts"] = ("not-a-mapping",)
        with self.assertRaisesRegex(
            PublicGonolConstructionError, "structure part must be a mapping"
        ):
            construct_public_gonol(
                source_id="epac.test:nonmapping-structure-part",
                relation="epac.affixiation.unpaired-valence",
                couplings=geometry["couplings"],
                structure=nonmapping_part,
            )

        mutations = {
            "degree": (),
            "participating_dimension_count": 99,
            "ternary_coupling_declared": True,
            "inferred_cartesian_embedding": True,
            "representation_kind": "fabricated",
            "representation_dimension": 99,
            "represented_structure_dimension": 99,
            "quaternions": (),
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                bad_structure = copy.deepcopy(geometry["structure"])
                bad_structure[key] = value
                with self.assertRaisesRegex(PublicGonolConstructionError, "derived fields"):
                    construct_public_gonol(
                        source_id=f"epac.test:bad-{key}",
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

    def test_standalone_mobius_epsilon_must_match_charge_state(self) -> None:
        declared = space(
            ["z", "x"],
            [["z", "x"]],
            charges={"z": 8, "x": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        bad_couplings = copy.deepcopy(geometry["couplings"])
        bad_couplings[0]["mobius_epsilon_t0"] = -1
        with self.assertRaisesRegex(PublicGonolConstructionError, "mobius_epsilon_t0"):
            construct_public_gonol(
                source_id="epac.test:bad-epsilon",
                relation="epac.affixiation.unpaired-valence",
                couplings=bad_couplings,
                structure=geometry["structure"],
            )

        null_couplings = copy.deepcopy(geometry["couplings"])
        null_couplings[0]["mobius_epsilon_t0"] = None
        with self.assertRaisesRegex(PublicGonolConstructionError, "mobius_epsilon_t0"):
            construct_public_gonol(
                source_id="epac.test:null-epsilon",
                relation="epac.affixiation.unpaired-valence",
                couplings=null_couplings,
                structure=geometry["structure"],
            )

    def test_coupling_records_reject_undeclared_fields_before_sealing(self) -> None:
        declared = space(
            ["z", "x"],
            [["z", "x"]],
            charges={"z": 8, "x": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        bad_couplings = copy.deepcopy(geometry["couplings"])
        bad_couplings[0]["degree"] = 999
        with self.assertRaisesRegex(PublicGonolConstructionError, "undeclared field"):
            construct_public_gonol(
                source_id="epac.test:extra-coupling-field",
                relation="epac.affixiation.unpaired-valence",
                couplings=bad_couplings,
                structure=geometry["structure"],
            )

    def test_coupling_alias_input_seals_to_canonical_declared_ids_payload(self) -> None:
        declared = space(
            ["z", "x"],
            [["z", "x"]],
            charges={"z": 8, "x": 1},
        )
        geometry = geometry_from_declared_couplings(declared)
        alias_couplings = tuple(
            {
                "coupling": item["declared_ids"],
                "arity": item["arity"],
                "slot_charges": item["slot_charges"],
                "charge_state": item["charge_state"],
                "mobius_epsilon_t0": item["mobius_epsilon_t0"],
            }
            for item in geometry["couplings"]
        )
        receipt = construct_public_gonol(
            source_id="epac.test:coupling-alias",
            relation="epac.affixiation.unpaired-valence",
            couplings=alias_couplings,
            structure=geometry["structure"],
        )
        self.assertEqual(tuple(receipt.gonol.couplings[0]), ("declared_ids", "arity", "slot_charges", "charge_state", "mobius_epsilon_t0"))
        self.assertEqual(receipt.gonol.couplings[0]["declared_ids"], ("z", "x"))

    def test_dimensional_errors_are_normalized_at_public_boundary(self) -> None:
        duplicated = (
            {
                "declared_ids": ("x", "x"),
                "arity": 2,
                "slot_charges": (1, 1),
                "charge_state": ((1, 1), 1),
                "mobius_epsilon_t0": 1,
            },
        )
        structure = {
            "parts": (
                {
                    "coupling": ("x", "x"),
                    "arity": 2,
                    "charge_state": ((1, 1), 1),
                },
            )
        }
        with self.assertRaises(PublicGonolConstructionError) as raised:
            construct_public_gonol(
                source_id="epac.test:duplicate-dimension",
                relation="epac.affixiation.unpaired-valence",
                couplings=duplicated,
                structure=structure,
            )
        self.assertIsInstance(raised.exception.__cause__, DimensionalArityError)

    def test_ucns_commit_is_not_stamped_when_runtime_head_is_not_verified(self) -> None:
        original_pin = public_gonol_module.PINNED_UCNS_COMMIT
        public_gonol_module.PINNED_UCNS_COMMIT = "0" * 40
        try:
            geometry = public_gonol_module._geometry(None, None)
        finally:
            public_gonol_module.PINNED_UCNS_COMMIT = original_pin
        self.assertEqual(geometry["ucns_commit"], "hmmm")

    def test_ucns_commit_is_not_stamped_when_loaded_code_is_stale(self) -> None:
        original_function = public_gonol_module.public_gonol_function
        namespace: dict[str, object] = {}
        source_path = inspect.getfile(original_function)
        exec(
            compile(
                "def public_gonol_function(value):\n    return value\n",
                source_path,
                "exec",
            ),
            namespace,
        )
        public_gonol_module.public_gonol_function = namespace["public_gonol_function"]
        epac_ucns_provenance.clear_ucns_verification_cache()
        try:
            receipt = construct_public_gonol(
                source_id="epac.test:stale-ucns",
                relation="epac.provenance.test",
            )
        finally:
            public_gonol_module.public_gonol_function = original_function
            epac_ucns_provenance.clear_ucns_verification_cache()
        self.assertEqual(receipt.geometry["ucns_commit"], "hmmm")
        replayed = replay_public_gonol(receipt)
        self.assertEqual(replayed.receipt_digest, receipt.receipt_digest)
        self.assertEqual(replayed.geometry["ucns_commit"], "hmmm")

    def test_unknown_glyph_fails_closed(self) -> None:
        with self.assertRaises(PublicGonolConstructionError):
            construct_public_gonol(
                source_id="epac.test:bad",
                relation="epac.atomic.element",
                identity_glyph="He",
            )


def check_epac_public_gonol_retained_constructor_boundary() -> None:
    suite = unittest.TestSuite(
        EpacPublicGonolTest(name)
        for name in (
            "test_retained_geometry_requires_the_complete_constructor_schema",
            "test_retained_couplings_are_canonical_before_identity_checks",
            "test_retained_scalars_reuse_constructor_validation",
            "test_boolean_integer_aliases_are_rejected_at_every_retained_boundary",
        )
    )
    result = suite.run(unittest.TestResult())
    if not result.wasSuccessful():
        raise AssertionError(
            f"retained constructor boundary failed: {result.failures!r} {result.errors!r}"
        )


if __name__ == "__main__":
    unittest.main()
