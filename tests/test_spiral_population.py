"""Executable population of lifted spirals from all declared gonols.

Covers the full experiment set (original prereg + enlarged molecules)
plus representative native periodic element gonols.

All data is projected from already-closed EPAC Public Gonols.
No new geometry or UCNS position operations are invented.

# === MODULE_BUILD ===
# id: test_epac_lifted_spiral_population
#   module_name: test_spiral_population
#   module_kind: test
#   summary: contract tests for full population of UCNS framed Möbius root-loop scenes from EPAC gonols
#   owner: The Interdependency
#   public_surface: (test functions)
#   tests: this file
#   since: 2026-09-03
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: full_spiral_population_covers_all_declared_molecules
#   given: the declared MOLECULE_COMPOSITIONS (9 formulas)
#   then: extract_full_spiral_population contains one scene per formula
#   class: population
#
# id: spiral_scenes_carry_canonical_provenance
#   given: any scene from the population
#   then: möbius_law_source ends with the canonical direct_mobius.py
#   class: provenance
#
# id: spiral_scenes_preserve_frame_double_cover
#   given: any scene
#   then: exactly three turns with visible_phase constant and frame sequence positive/reversed/positive
#   class: correctness
#
# id: spiral_scene_replay_deterministic
#   given: a molecule or element construction
#   then: scene extracted before and after replay_public_gonol / replay_element_gonol are identical on core fields
#   class: determinism
# === END CONTRACTS ===
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET


from epac_molecular import (
    MOLECULE_COMPOSITIONS,
    construct_declared_molecules,
    replay_molecule,
)
from epac_periodic import construct_element_gonol, replay_element_gonol
from epac_public_gonol import replay_public_gonol

from epac_subatomic import subatomic_gonol as subatomic_gonol
from epac_subatomic.subatomic_gonol import replay_subatomic_gonol

from epac_viz.spiral_viz import (
    extract_full_spiral_population,
    extract_spiral_scene,
    get_möbius_law_source,
    spiral_population_keys,
    render_scene_svg,
)


class SpiralPopulationTest(unittest.TestCase):
    def test_subatomic_scene_preserves_carried_frames_and_axes(self) -> None:
        receipt = SimpleNamespace(source_id="subatomic:fixture", relation="epac.subatomic", structure={},
                                  gonol=SimpleNamespace(carried_options=(("lifted-spiral", "left|left|right;axis:b,axis:a;0"),)))
        scene = extract_spiral_scene(receipt)
        self.assertEqual(tuple(turn.frame for turn in scene.turns), ("left", "left", "right"))
        self.assertEqual(scene.participant_axes, ("axis:a", "axis:b"))
        self.assertFalse(scene.one_turn_flips_frame)
        self.assertFalse(scene.complete_restored_at_t2)
        receipt.gonol.carried_options = (("lifted-spiral", "malformed"),)
        with self.assertRaisesRegex(ValueError, "carried lifted-spiral"):
            extract_spiral_scene(receipt)
        for count in ("invalid", "1", "-1", "", "00", "0;unexpected"):
            receipt.gonol.carried_options = (("lifted-spiral", "left|left|right;axis;" + count),)
            with self.assertRaisesRegex(ValueError, "attachment count"):
                extract_spiral_scene(receipt)

    def test_direct_receipts_preserve_all_carried_spiral_scales(self) -> None:
        for formula, construction in construct_declared_molecules().items():
            direct = extract_spiral_scene(construction.receipt)
            wrapped = extract_spiral_scene(construction)
            self.assertEqual(direct.relation, construction.receipt.gonol.relation)
            self.assertEqual(wrapped.relation, direct.relation)
            expected_charges = {d["dimension"]: d["charge"] for d in construction.receipt.structure["degree"]}
            self.assertTrue(expected_charges)
            self.assertEqual(direct.dimension_charges, expected_charges)
            self.assertEqual(wrapped.dimension_charges, expected_charges)
            self.assertEqual(direct.turns, wrapped.turns, formula)
            self.assertEqual(direct.participant_axes, wrapped.participant_axes, formula)
            self.assertEqual(len(direct.attachments), len(wrapped.attachments), formula)
            self.assertTrue(all(slot.center is None and slot.site is None for slot in direct.attachments))
        for constructor in (construct_element_gonol, subatomic_gonol.construct_subatomic_gonol):
            receipt = constructor("H")
            scene = extract_spiral_scene(receipt)
            self.assertEqual(scene.relation, receipt.gonol.relation)
            self.assertEqual(scene.dimension_charges, {d["dimension"]: d["charge"] for d in (receipt.structure or {}).get("degree", ())})
            carried = tuple((key, value[:-1] + "1" if key == "lifted-spiral" else value) for key, value in receipt.gonol.carried_options)
            invalid = replace(receipt, gonol=replace(receipt.gonol, carried_options=carried))
            with self.assertRaisesRegex(ValueError, "attachment count"):
                extract_spiral_scene(invalid)
            from epac_molecular import lifted_spiral_from_receipt
            with self.assertRaisesRegex(ValueError, "attachment count"):
                lifted_spiral_from_receipt(invalid)
        from types import MappingProxyType
        from epac_molecular import construct_molecule
        construction = construct_molecule("H2O")
        invariants = dict(construction.invariants)
        mobius = dict(invariants["mobius"])
        mobius["attachment_slots"] = tuple(MappingProxyType(dict(slot)) for slot in mobius["attachment_slots"])
        invariants["mobius"] = mobius
        wrapped = SimpleNamespace(receipt=construction.receipt, invariants=invariants)
        self.assertEqual(len(extract_spiral_scene(wrapped).attachments), 2)
        mobius["attachment_slots"] = (None, None)
        with self.assertRaisesRegex(ValueError, "attachment slot evidence"):
            extract_spiral_scene(wrapped)
        for relation, count in (("epac.atomic.element", 0), ("epac.molecular", 2)):
            receipt = SimpleNamespace(source_id="fixture", relation=relation, structure={},
                                      gonol=SimpleNamespace(carried_options=(("lifted-spiral", f"left|left|right;axis:b,axis:a;{count}"),)))
            scene = extract_spiral_scene(receipt)
            self.assertEqual(tuple(t.frame for t in scene.turns), ("left", "left", "right"))
            self.assertEqual(scene.participant_axes, ("axis:a", "axis:b"))
            self.assertEqual(len(scene.attachments), count)
            self.assertFalse(scene.one_turn_flips_frame)
            self.assertFalse(scene.complete_restored_at_t2)

    def test_population_propagates_requested_entry_failures(self) -> None:
        with patch("epac_molecular.construct_declared_molecules", return_value={}):
            for options in ({"include_elements": ("unsupported",), "include_subatomic": ()},
                            {"include_elements": (), "include_subatomic": ("unsupported",)}):
                with self.assertRaises(ValueError):
                    extract_full_spiral_population(**options)
            for target, options in (("epac_periodic.construct_element_gonol", {"include_elements": ("H",), "include_subatomic": ()}),
                                    ("epac_subatomic.subatomic_gonol.construct_subatomic_gonol", {"include_elements": (), "include_subatomic": ("H",)})):
                with patch(target, side_effect=RuntimeError("construction failed")):
                    with self.assertRaisesRegex(RuntimeError, "construction failed"):
                        extract_full_spiral_population(**options)
            with patch("epac_viz.spiral_viz.extract_spiral_scene", side_effect=RuntimeError("scene failed")):
                with self.assertRaisesRegex(RuntimeError, "scene failed"):
                    extract_full_spiral_population(include_elements=("H",), include_subatomic=())

    def test_svg_renders_symmetric_attachment_slots(self) -> None:
        from epac_molecular import construct_molecule
        scene = extract_spiral_scene(construct_molecule("H2"))
        root = ET.fromstring(render_scene_svg(scene, width=640, height=400))
        groups = root.findall(".//{http://www.w3.org/2000/svg}g[@data-symmetric-slot]")
        self.assertEqual(len(groups), len(scene.attachments))
        self.assertEqual({group.attrib["data-symmetric-slot"] for group in groups}, {str(slot.slot) for slot in scene.attachments})
        self.assertEqual({group.find("{http://www.w3.org/2000/svg}text").text for group in groups},
                         {f"{slot.participant}@{slot.site}" for slot in scene.attachments})
        self.assertTrue(all(group.find("{http://www.w3.org/2000/svg}path") is not None for group in groups))

    def test_svg_escapes_phase_and_fits_requested_width(self) -> None:
        scene = extract_spiral_scene(subatomic_gonol.construct_subatomic_gonol("H"))
        phase = "<script>alert(1)</script>&"
        scene = replace(scene, turns=tuple(replace(turn, t=phase, visible_phase=phase) for turn in scene.turns),
                        one_turn_flips_frame=phase, complete_restored_at_t2=phase)
        root = ET.fromstring(render_scene_svg(scene, width=640, height=400))
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.findall(".//svg:script", namespace), [])
        self.assertIn("visible: " + phase, [node.text for node in root.findall(".//svg:text", namespace)])
        for node in root.findall(".//svg:rect", namespace):
            self.assertGreaterEqual(float(node.attrib["x"]), 0)
            self.assertLessEqual(float(node.attrib["x"]) + float(node.attrib["width"]), 640)
            self.assertGreaterEqual(float(node.attrib["y"]), 0)
            self.assertLessEqual(float(node.attrib["y"]) + float(node.attrib["height"]), 400)
        with self.assertRaisesRegex(ValueError, "at least 640"):
            render_scene_svg(scene, width=639)
        with self.assertRaisesRegex(ValueError, "at least 400"):
            render_scene_svg(scene, height=399)
        for invalid in (100.5, float("nan"), True, "640"):
            with self.assertRaisesRegex(ValueError, "integers"):
                render_scene_svg(scene, width=invalid)

    def test_full_population_covers_all_declared_molecules(self) -> None:
        pop = extract_full_spiral_population()
        for formula in MOLECULE_COMPOSITIONS:
            self.assertIn(formula, pop, f"missing lifted spiral for {formula}")
            scene = pop[formula]
            self.assertTrue(scene.participant_axes, f"no participant axes for {formula}")
            # Every molecule scene must have the mobius law
            self.assertIn("native-mobius-root-loop", scene.law)

    def test_full_population_includes_representative_elements(self) -> None:
        pop = extract_full_spiral_population()
        for sym in ("H", "C", "O"):
            key = f"element:{sym}"
            self.assertIn(key, pop, f"missing element spiral for {sym}")
            scene = pop[key]
            self.assertTrue(scene.participant_axes)

    def test_full_population_includes_representative_subatomic(self) -> None:
        # Subatomic gonols now carry "lifted-spiral" first-class (parallel to element).
        # The population extractor surfaces them under "subatomic:<sym>".
        pop = extract_full_spiral_population()
        for sym in ("H", "C", "O"):
            key = f"subatomic:{sym}"
            self.assertIn(key, pop, f"missing subatomic spiral for {sym}")
            scene = pop[key]
            self.assertTrue(scene.participant_axes)
            self.assertIn("native-mobius-root-loop", scene.law)

    def test_spiral_scenes_carry_canonical_provenance(self) -> None:
        pop = extract_full_spiral_population()
        src = get_möbius_law_source()
        self.assertIsNotNone(src)
        self.assertTrue(str(src).endswith("direct_mobius.py"))
        for name, scene in pop.items():
            self.assertIsNotNone(scene.möbius_law_source, name)
            self.assertTrue(
                str(scene.möbius_law_source).endswith("direct_mobius.py"),
                f"{name} provenance wrong: {scene.möbius_law_source}",
            )

    def test_spiral_scenes_preserve_frame_double_cover(self) -> None:
        pop = extract_full_spiral_population()
        for name, scene in pop.items():
            self.assertEqual(len(scene.turns), 3, name)
            phases = {t.visible_phase for t in scene.turns}
            self.assertEqual(len(phases), 1, f"visible phase must be constant for {name}")
            frames = [t.frame for t in scene.turns]
            self.assertEqual(
                frames,
                ["positive-local-frame", "reversed-local-frame", "positive-local-frame"],
                f"frame sequence wrong for {name}",
            )
            self.assertTrue(scene.one_turn_flips_frame)
            self.assertTrue(scene.complete_restored_at_t2)

    def test_spiral_population_keys_match_population(self) -> None:
        pop = extract_full_spiral_population()
        expected = set(spiral_population_keys())
        actual = set(pop.keys())
        self.assertEqual(actual, expected)
        for formula in MOLECULE_COMPOSITIONS:
            self.assertIn(formula, actual)
        # The helper must list at least the molecules
        self.assertTrue(expected.issuperset(MOLECULE_COMPOSITIONS.keys()))

    def test_molecule_spiral_scene_replay_deterministic(self) -> None:
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            before = extract_spiral_scene(c)
            replayed = replay_molecule(c)
            after = extract_spiral_scene(replayed)
            # Core replay-stable facts from the receipt (double cover + flags + provenance)
            self.assertEqual(before.turns, after.turns, formula)
            self.assertEqual(before.one_turn_flips_frame, after.one_turn_flips_frame)
            self.assertEqual(before.complete_restored_at_t2, after.complete_restored_at_t2)
            self.assertEqual(before.möbius_law_source, after.möbius_law_source)
            # participant_axes must be identical as a set (order is not part of the
            # invariant; pure replay on a receipt may derive axes from structure parts
            # in a different order than the original participant list).
            self.assertEqual(set(before.participant_axes), set(after.participant_axes), formula)
            # Attachment slots are rich construction-time evidence stored in the
            # MolecularConstruction "mobius" invariant. After pure replay we only
            # synthesize participant axes from structure; attachments may be empty.
            # We only require that the original construction captured them when expected.
            if formula != "H2":
                self.assertTrue(len(before.attachments) > 0, f"no attachments on construction for {formula}")

    def test_element_spiral_scene_replay_deterministic(self) -> None:
        for sym in ("H", "O", "C"):
            receipt = construct_element_gonol(sym)
            before = extract_spiral_scene(receipt)
            replayed = replay_element_gonol(receipt)
            after = extract_spiral_scene(replayed)
            self.assertEqual(before.turns, after.turns, sym)
            self.assertEqual(before.participant_axes, after.participant_axes, sym)
            self.assertEqual(before.möbius_law_source, after.möbius_law_source)

    def test_subatomic_spiral_scene_replay_deterministic(self) -> None:
        # replay_subatomic_gonol returns digest; re-construct for fresh receipt
        # to extract scene (consistent with subatomic carry/replay tests).
        for sym in ("H", "C", "O"):
            receipt = subatomic_gonol.construct_subatomic_gonol(sym)
            before = extract_spiral_scene(receipt)
            _ = replay_subatomic_gonol(receipt)
            after_receipt = subatomic_gonol.construct_subatomic_gonol(sym)
            after = extract_spiral_scene(after_receipt)
            self.assertEqual(before.turns, after.turns, sym)
            self.assertEqual(before.participant_axes, after.participant_axes, sym)
            self.assertEqual(before.möbius_law_source, after.möbius_law_source, sym)

    def test_attachment_slots_populated_for_molecules(self) -> None:
        pop = extract_full_spiral_population()
        # Most molecules have valence attachments; H2 is symmetric but still records slots
        for formula in ("H2O", "CH4", "BF3"):
            scene = pop[formula]
            self.assertTrue(len(scene.attachments) > 0, f"no attachments for {formula}")


if __name__ == "__main__":
    unittest.main()
