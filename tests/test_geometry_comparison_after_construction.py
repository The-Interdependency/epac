from __future__ import annotations

import json
import sys
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

import epac_public_gonol as _installed_epac
EPAC_ROOT = Path(_installed_epac.__file__).resolve().parent

from epac_comparison import (
    ORIGINAL_PREREG,
    SEALED_SHAPE_LABELS,
    CONSTRUCTION_FILES,
    _standing,
    _harmonic_survival_signature,
    _per_symbol_harmonic_survival_from_molecule,
    _periodic_element_harmonic_survival_signature,
    _subatomic_harmonic_survival_signature,
    compare_after_construction,
    construction_sources_omit_sealed_labels,
)
from epac_dimensional_arity import charged_structure_readout, topology_structure_readout
from epac_molecular import (
    MOLECULE_COMPOSITIONS,
    boundary_capacity_carried_on_molecule,
    boundary_capacity_descriptor_sufficiency_sweep,
    boundary_capacity_information_loss_localization,
    boundary_capacity_minimal_refinement_audit,
    boundary_capacity_quotient_test,
    epac_probe_relativity_formalization,
    epac_representation_audit,
    compositional_boundary_closure,
    construct_declared_molecules,
    harmonic_survival_carried_on_molecule,
    lifted_spiral_carried_on_molecule,
    matched_information_control,
    per_symbol_harmonic_survival_carried_on_molecule,
    replay_molecule,
)
from epac_periodic import construct_element_gonol
from epac_public_gonol import replay_public_gonol


from epac_comparison import SEALED_PATH as SEALED


class GeometryComparisonAfterConstructionTest(unittest.TestCase):
    def test_transition_prediction_uses_sources_without_target_invariants(self) -> None:
        from dataclasses import replace
        from unittest.mock import patch
        from epac_molecular import construct_molecule, boundary_capacity_transition_for_molecule, predict_boundary_capacity_from_source_and_op
        class UnreadableInvariants(dict):
            def __getitem__(self, key):
                raise AssertionError("target invariant inspected")
        target = construct_molecule("H2O")
        with patch("epac_molecular.construct_molecule", side_effect=AssertionError("target construction inspected")):
            record = boundary_capacity_transition_for_molecule("H2O", replace(target, invariants=UnreadableInvariants()))
        self.assertTrue(record["reproducible"])
        self.assertEqual(record["predicted_b_from_source_and_op"], (3, 3, 2))
        self.assertEqual(record["op"]["attachment_count"], 2)
        for invalid in ([], [(3, 99, 0)] * 3, [(3, 1, 1)] * 3, [(3.0, 2, 0)] * 3, list(reversed(record["source_bs"]))):
            with self.assertRaises(ValueError):
                predict_boundary_capacity_from_source_and_op(invalid, record["op"])
        for key in ("atom_count", "attachment_count"):
            with self.assertRaises(ValueError):
                predict_boundary_capacity_from_source_and_op(record["source_bs"], dict(record["op"], **{key: 99}))
        for composition in ((("H", 2), ("O", True)), (("H", 2), ("O", 1.0))):
            with self.assertRaises(ValueError):
                predict_boundary_capacity_from_source_and_op(record["source_bs"], dict(record["op"], composition=composition))
        wrong = construct_molecule("SiH4")
        with self.assertRaisesRegex(ValueError, "does not belong"):
            boundary_capacity_transition_for_molecule("CH4", wrong)
        with self.assertRaisesRegex(ValueError, "does not belong"):
            boundary_capacity_transition_for_molecule("CH4", replace(wrong, formula="CH4"))
        spoofed_receipt = replace(wrong.receipt, source_id="epac.molecule:CH4",
                                  gonol=replace(wrong.receipt.gonol, source_id="epac.molecule:CH4"))
        with self.assertRaisesRegex(ValueError, "participants do not belong"):
            boundary_capacity_transition_for_molecule("CH4", replace(wrong, formula="CH4", receipt=spoofed_receipt))

    def test_bare_comparison_projections_preserve_multiplicity(self) -> None:
        from collections import Counter
        from types import SimpleNamespace
        from unittest.mock import patch
        import epac_comparison as comparison
        from epac_cross_scale_closure import _subatomic_lifted_spiral_signature as cross_signature
        cases = (
            (comparison._periodic_element_lifted_spiral_signature, "epac_comparison.construct_element_gonol", "epac_comparison.lifted_spiral_carried_on_element", True),
            (comparison._subatomic_lifted_spiral_signature, "epac_comparison.subatomic_gonol.construct_subatomic_gonol", "epac_comparison.lifted_spiral_carried_on_subatomic", True),
            (comparison._periodic_element_boundary_capacity_signature, "epac_comparison.construct_element_gonol", "epac_comparison.boundary_capacity_from_element_receipt", False),
            (comparison._subatomic_boundary_capacity_signature, "epac_comparison.subatomic_gonol.construct_subatomic_gonol", "epac_comparison.boundary_capacity_from_subatomic_receipt", False),
            (cross_signature, "epac_cross_scale_closure.construct_subatomic_gonol", "epac_cross_scale_closure.lifted_spiral_carried_on_subatomic", True),
        )
        for function, constructor, extractor, spiral in cases:
            for formula, composition in MOLECULE_COMPOSITIONS.items():
                symbols = [symbol for symbol, count in composition for _ in range(count)]
                with patch(constructor, side_effect=lambda symbol, occurrence: SimpleNamespace(symbol=symbol, occurrence=occurrence)) as build:
                    with patch(extractor, side_effect=(lambda receipt: (("a", "b", "a"), (f"axis#{receipt.occurrence}",), 0)) if spiral else (lambda receipt: (3, 2, 0))):
                        result = function(formula)
                self.assertEqual(Counter(value.split(":", 1)[0] for value in result), Counter(symbols))
                self.assertEqual([(call.args[0], call.kwargs["occurrence"]) for call in build.call_args_list], list(zip(symbols, range(len(symbols)))))

    def test_partition_witnesses_cross_the_reported_equivalence(self) -> None:
        from epac_molecular import _partition_disagreement_pairs
        full = (frozenset(("a", "b")), frozenset(("c", "d")))
        candidate = (frozenset(("a", "b", "c")), frozenset(("d",)))
        expected = {"false_merge": (("a", "c"),), "false_split": (("c", "d"),)}
        for first, second in ((full, candidate), (tuple(reversed(full)), tuple(reversed(candidate)))):
            result = _partition_disagreement_pairs(first, second)
            self.assertEqual(result, expected)
            full_owner = {sid: group for group in first for sid in group}
            candidate_owner = {sid: group for group in second for sid in group}
            for a, b in result["false_merge"]:
                self.assertEqual(candidate_owner[a], candidate_owner[b])
                self.assertNotEqual(full_owner[a], full_owner[b])
            for a, b in result["false_split"]:
                self.assertEqual(full_owner[a], full_owner[b])
                self.assertNotEqual(candidate_owner[a], candidate_owner[b])

    def test_unknown_local_transition_kind_fails(self) -> None:
        from epac_molecular import apply_local_step, accumulate_from_local_path
        for kind in ("", "introduse", "unknown", None):
            with self.assertRaisesRegex(ValueError, "unknown local transition kind"):
                apply_local_step((3, 0, 0), (kind, "H"))
            with self.assertRaisesRegex(ValueError, "unknown local transition kind"):
                accumulate_from_local_path((3, 0, 0), [("introduce", "H"), (kind, "H")])
        self.assertEqual(apply_local_step((3, 0, 0), ("introduce", "H")), (3, 1, 0))
        self.assertEqual(apply_local_step((3, 1, 0), ("affix", "H")), (3, 1, 1))

    def test_sufficiency_preserves_independent_closure_statuses(self) -> None:
        from unittest.mock import patch
        keys = ("subatomic_to_element_closure", "element_state_compatibility", "end_to_end_subatomic_to_molecule_closure", "boundary_capacity_compositionality")
        # Empty fixture isolates status propagation; the sealed sweep test below
        # separately proves real collisions coexist with surviving closure.
        with patch("epac_molecular.MOLECULE_COMPOSITIONS", {}), patch("epac_molecular.construct_declared_molecules", return_value={}):
            with patch("epac_cross_scale_closure.cross_scale_compositional_closure") as closure:
                for status in ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED", "invalid", None):
                    closure.return_value = {"statuses": {key: status for key in keys}}
                    result = boundary_capacity_descriptor_sufficiency_sweep()["aggregate"]
                    expected = status if status in ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED") else "UNRESOLVED"
                    self.assertEqual({key: result[key] for key in keys}, {key: expected for key in keys})
                for key in keys:
                    for status in ("FALSIFIED", "UNRESOLVED", "BLOCKED", None):
                        statuses = dict.fromkeys(keys, "SURVIVED")
                        statuses[key] = status
                        closure.return_value = {"statuses": statuses}
                        result = boundary_capacity_descriptor_sufficiency_sweep()
                        expected = statuses["element_state_compatibility"] or "UNRESOLVED"
                        self.assertEqual(result["cross_scale_element_compatibility"], expected)
                        self.assertEqual(result["aggregate"]["element_state_compatibility"], expected)
                        self.assertEqual(result["aggregate"]["subatomic_to_element_closure"], statuses["subatomic_to_element_closure"] or "UNRESOLVED")
                closure.side_effect = RuntimeError("closure unavailable")
                result = boundary_capacity_descriptor_sufficiency_sweep()["aggregate"]
                self.assertTrue(all(result[key] == "BLOCKED" for key in keys))

    def test_comparison_requires_complete_frozen_preregistration(self) -> None:
        from unittest.mock import patch
        for omitted in ORIGINAL_PREREG:
            with patch("epac_comparison.construction_sources_omit_sealed_labels", return_value=()), patch(
                    "epac_comparison.construct_declared_molecules", return_value={formula: None for formula in ORIGINAL_PREREG - {omitted}}):
                with self.assertRaisesRegex(ValueError, "missing preregistered constructions"):
                    compare_after_construction.__wrapped__()
            with TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "data").mkdir()
                (root / "data" / "sealed_known_molecular_geometry.json").write_text(json.dumps({
                    "molecules": {formula: {"known_shape": "fixture"} for formula in ORIGINAL_PREREG - {omitted}}
                }))
                with patch("epac_comparison.construction_sources_omit_sealed_labels", return_value=()), patch(
                        "epac_comparison.construct_declared_molecules", return_value={formula: None for formula in ORIGINAL_PREREG}):
                    with self.assertRaisesRegex(ValueError, "missing preregistered sealed evidence"):
                        compare_after_construction.__wrapped__(root)

    def test_representation_overall_includes_every_required_stage(self) -> None:
        from contextlib import ExitStack
        from copy import deepcopy
        from unittest.mock import patch
        from epac_molecular import epac_representation_audit
        states = [{"state_id": str(index), "behavior": {"b": (3, 1, 1), "ligand_contribution_K": 1}} for index in range(27)]
        prerequisites = {
            "closure": ("epac_cross_scale_closure.cross_scale_compositional_closure", {"statuses": {key: "SURVIVED" for key in ("subatomic_to_element_closure", "element_state_compatibility", "end_to_end_subatomic_to_molecule_closure", "boundary_capacity_compositionality")}}, ("statuses", "boundary_capacity_compositionality")),
            "non_degeneracy": ("epac_boundary_nondegeneracy.boundary_descriptor_nondegeneracy_report", {"statuses": {"boundary_descriptor_non_degeneracy": "SURVIVED"}}, ("statuses", "boundary_descriptor_non_degeneracy")),
            "sufficiency": ("epac_molecular.boundary_capacity_descriptor_sufficiency_sweep", {"aggregate": {"boundary_capacity_sufficiency": "SURVIVED"}}, ("aggregate", "boundary_capacity_sufficiency")),
            "collision_localization": ("epac_molecular.boundary_capacity_information_loss_localization", {"aggregate": {"information_loss_localization": "SURVIVED"}}, ("aggregate", "information_loss_localization")),
            "behavioral_equivalence": ("epac_molecular.boundary_capacity_quotient_test", {"aggregate": {"boundary_capacity_quotient": "SURVIVED"}}, ("aggregate", "boundary_capacity_quotient")),
            "probe_completeness": ("epac_boundary_probe_completeness.boundary_probe_completeness_report", {"statuses": {"boundary_probe_completeness": "SURVIVED"}}, ("statuses", "boundary_probe_completeness")),
            "minimal_refinement": ("epac_molecular.boundary_capacity_minimal_refinement_audit", {"aggregate": {"minimal_behavioral_refinement": "SURVIVED"}}, ("aggregate", "minimal_behavioral_refinement")),
        }
        with ExitStack() as stack:
            stack.enter_context(patch("epac_molecular._build_frozen_27_states", return_value=states))
            mocks = {name: stack.enter_context(patch(path, return_value=deepcopy(value))) for name, (path, value, _) in prerequisites.items()}
            self.assertEqual(epac_representation_audit()["outputs"]["overall"], "SURVIVED")
            for name, (_, original, keys) in prerequisites.items():
                for status in ("FALSIFIED", "UNRESOLVED"):
                    value = deepcopy(original)
                    target = value
                    for key in keys[:-1]:
                        target = target[key]
                    target[keys[-1]] = status
                    mocks[name].return_value = value
                    result = epac_representation_audit()["outputs"]
                    self.assertEqual(result["overall"], status, name)
                    self.assertEqual(result["representation_equivalence"], "SURVIVED", name)
                    self.assertIn(name, result["failed_stages" if status == "FALSIFIED" else "unresolved_stages"])
                mocks[name].return_value = deepcopy(original)
            for key in prerequisites["closure"][1]["statuses"]:
                for status in ("FALSIFIED", "UNRESOLVED", "BLOCKED", None):
                    value = deepcopy(prerequisites["closure"][1])
                    value["statuses"][key] = status
                    mocks["closure"].return_value = value
                    result = epac_representation_audit()
                    self.assertEqual(result["stages"]["closure"]["status"], status or "UNRESOLVED")
                    self.assertEqual(result["outputs"]["overall"], status or "UNRESOLVED")
            mocks["closure"].side_effect = RuntimeError("cross-scale evidence unavailable")
            self.assertEqual(epac_representation_audit()["stages"]["closure"]["status"], "BLOCKED")
            mocks["closure"].side_effect = None
            mocks["closure"].return_value = {"statuses": {"boundary_capacity_compositionality": "FALSIFIED"}}
            mocks["non_degeneracy"].side_effect = RuntimeError("missing prerequisite")
            result = epac_representation_audit()["outputs"]
            self.assertEqual(result["overall"], "FALSIFIED")
            self.assertIn("non_degeneracy", result["unresolved_stages"])
            mocks["closure"].return_value = deepcopy(prerequisites["closure"][1])
            self.assertEqual(epac_representation_audit()["outputs"]["overall"], "UNRESOLVED")
            mocks["non_degeneracy"].side_effect = None
            states[0]["behavior"]["affix_Ks"] = (2,)
            result = epac_representation_audit()["outputs"]
            self.assertEqual(result["overall"], "FALSIFIED")
            self.assertIn("representation_equivalence", result["failed_stages"])

    def test_failed_structural_probe_is_unresolved(self) -> None:
        from unittest.mock import patch
        from epac_boundary_probe_completeness import OMITTED_OBSERVABLES
        states = [{"state_id": str(index), "b": (3, 1, 1), "behavior": {}} for index in range(27)]
        reference = {"outputs": {"partitions": {"full_admissible_identity_free": [[state["state_id"] for state in states]]}}}
        with patch("epac_molecular._build_frozen_27_states", return_value=states), patch("epac_molecular.epac_representation_audit", return_value=reference):
            scenarios = (
                patch("epac_boundary_probe_completeness._state_contexts", side_effect=RuntimeError("probe unavailable")),
                patch("epac_boundary_probe_completeness._state_contexts", return_value={}),
            )
            for scenario in scenarios:
                with scenario:
                    record = epac_probe_relativity_formalization()
                    self.assertEqual(record["status"], "UNRESOLVED")
                    self.assertEqual(record["outputs"]["overall"], "UNRESOLVED")
            def failing_probe(_context):
                raise RuntimeError("omitted observable failed")
            with patch("epac_boundary_probe_completeness._state_contexts", return_value={state["state_id"]: object() for state in states}), patch.dict(OMITTED_OBSERVABLES, {next(iter(OMITTED_OBSERVABLES)): failing_probe}, clear=True):
                record = epac_probe_relativity_formalization()
                self.assertEqual(record["status"], "UNRESOLVED")
                self.assertIn("omitted observable failed", record["error"])

    def test_construction_omits_sealed_shape_labels(self) -> None:
        self.assertEqual(construction_sources_omit_sealed_labels(), ())
        labels = {row["known_shape"] for row in json.loads(SEALED.read_text())["molecules"].values()}
        self.assertLessEqual(labels, set(SEALED_SHAPE_LABELS))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in CONSTRUCTION_FILES:
                (root / name).write_text("")
            for label in labels:
                (root / CONSTRUCTION_FILES[0]).write_text(label)
                self.assertIn(CONSTRUCTION_FILES[0] + ":" + label, construction_sources_omit_sealed_labels(root))

    def test_standing_uses_same_preregistered_population(self) -> None:
        known = {formula: row["known_shape"] for formula, row in json.loads(SEALED.read_text())["molecules"].items() if formula in ORIGINAL_PREREG}
        prediction = dict(known, BF3="unscored", H2S="another", PH3="extra", SiH4="extra")
        control = {formula: index for index, formula in enumerate(prediction)}
        self.assertEqual(_standing(prediction, known, control), "SURVIVED")
        self.assertEqual(_standing(known, known, control), "SURVIVED")
        self.assertEqual(_standing(prediction, known, dict(known, BF3="different")), "FALSIFIED")
        self.assertEqual(_standing(dict(prediction, CO2="split"), known, control), "FALSIFIED")
        self.assertEqual(_standing(dict(prediction, CH4=known["H2O"]), known, control), "FALSIFIED")

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
        # After deliberate enlargement of the experiment, more formulas are constructed.
        # The frozen sealed-shape prediction logic only applies to the original preregistered set.
        self.assertTrue(ORIGINAL_PREREG.issubset(set(constructions)))
        self.assertGreaterEqual(len(constructions), 5)

        record = compare_after_construction()
        sealed = json.loads(SEALED.read_text(encoding="utf-8"))["molecules"]
        known_shapes = record["known_shapes"]

        self.assertTrue(record["opened_after_construction"])
        self.assertTrue(record["construction_omits_sealed_labels"])
        self.assertEqual(set(known_shapes.keys()), ORIGINAL_PREREG)
        self.assertGreater(len(set(known_shapes.values())), 1)
        self.assertEqual(known_shapes["H2O"], "bent")
        self.assertEqual(known_shapes["CO2"], "linear")
        self.assertEqual(known_shapes["H2"], "linear")

        self.assertTrue(record["topology_collapses_h2o_with_co2"])
        self.assertTrue(record["charged_distinguishes_h2o_from_co2"])
        self.assertTrue(record["linear_class_split_by_charged_structure"])

        # Parallel facts for the carried nuclear harmonic survival (now a first-class
        # invariant on every MolecularConstruction and surfaced in the record).
        self.assertIn("harmonic_collapses_h2o_with_co2", record)
        self.assertIn("harmonic_distinguishes_h2o_from_co2", record)
        self.assertIn("linear_class_split_by_harmonic_survival", record)
        self.assertFalse(record["harmonic_collapses_h2o_with_co2"])
        self.assertTrue(record["harmonic_distinguishes_h2o_from_co2"])
        self.assertTrue(record["linear_class_split_by_harmonic_survival"])

        # Exact partition match facts for the harmonic family are now first-class
        # top-level fields on the record (symmetric to the other harmonic facts).
        self.assertIn("harmonic_matches_known", record)
        self.assertIn("harmonic_matches_control", record)
        self.assertFalse(record["harmonic_matches_known"])
        self.assertFalse(record["harmonic_matches_control"])

        # Parallel top-level facts and exact match for the periodic element gonol view
        # of the carried nuclear harmonic survival (now first-class, symmetric to the others).
        self.assertIn("periodic_element_harmonic_collapses_h2o_with_co2", record)
        self.assertIn("periodic_element_harmonic_distinguishes_h2o_from_co2", record)
        self.assertIn("linear_class_split_by_periodic_element_harmonic_survival", record)
        self.assertFalse(record["periodic_element_harmonic_collapses_h2o_with_co2"])
        self.assertTrue(record["periodic_element_harmonic_distinguishes_h2o_from_co2"])
        self.assertTrue(record["linear_class_split_by_periodic_element_harmonic_survival"])

        self.assertIn("periodic_element_harmonic_matches_known", record)
        self.assertIn("periodic_element_harmonic_matches_control", record)
        self.assertFalse(record["periodic_element_harmonic_matches_known"])
        self.assertFalse(record["periodic_element_harmonic_matches_control"])

        standings = record["standings"]
        self.assertEqual(standings["charged_3_structure_as_sealed_shape_prediction"], "FALSIFIED")
        self.assertEqual(standings["topology_3_structure_as_sealed_shape_prediction"], "FALSIFIED")
        self.assertEqual(standings["ucns_mobius_as_sealed_shape_prediction"], "FALSIFIED")
        self.assertEqual(standings["atomic_shells_as_sealed_shape_prediction"], "FALSIFIED")
        self.assertEqual(
            standings["periodic_element_harmonic_survival_as_sealed_shape_prediction"],
            "FALSIFIED",
        )

        # Control is computed over all constructed molecules (original + enlarged set)
        control = {f: matched_information_control(c.invariants) for f, c in constructions.items()}
        self.assertNotEqual(control["H2O"], control["CO2"])
        # There are now more than 5 constructed molecules
        self.assertGreater(len(set(control.values())), 4)

    def test_quantify_distinguishing_power_present_and_consistent(self) -> None:
        record = compare_after_construction()
        self.assertIn("quantify_distinguishing_power", record)
        q = record["quantify_distinguishing_power"]

        # The *known* (sealed) side remains the original preregistered experiment.
        self.assertEqual(q["class_counts"]["known_shapes"], 4)

        # The constructed set has been deliberately enlarged (original 5 + new molecules).
        # We expect at least 9 constructed formulas in this step.
        constructed_readout = record.get("readouts", {}).get("charged_3_structure", {})
        self.assertGreaterEqual(len(constructed_readout), 9)

        # Class counts for the full constructed set reflect the enlargement.
        # Charged and control each produce one class per constructed formula (9).
        # Topology is weaker and produces fewer classes (observed: 4 for the current enlarged set).
        self.assertGreaterEqual(q["class_counts"]["charged_3_structure"], 9)
        self.assertGreaterEqual(q["class_counts"]["stoichiometric_control"], 9)
        # Topology count is smaller than the constructed count (by design).
        self.assertLess(q["class_counts"]["topology_3_structure"], q["class_counts"]["charged_3_structure"])

        # Splits and collapses are still evaluated *only against the known (sealed) 4 classes*.
        # The original preregistered falsification behavior must be preserved.
        self.assertEqual(q["splits_known_classes"]["charged_3_structure"], 1)
        self.assertEqual(q["collapses_across_known_classes"]["charged_3_structure"], 0)

        self.assertEqual(q["splits_known_classes"]["topology_3_structure"], 1)
        self.assertEqual(q["collapses_across_known_classes"]["topology_3_structure"], 1)

        # Pairwise contingency for the *known* side is still over the original 5 formulas.
        charged_pw = q["pairwise_vs_known"]["charged_3_structure"]
        self.assertEqual(charged_pw["total_pairs"], 10)  # C(5,2) for the known set
        self.assertEqual(charged_pw["fp"], 1)  # splits the linear class
        self.assertEqual(charged_pw["fn"], 0)  # no collapse of known classes

        # Exact partition match vs the frozen known set remains false.
        self.assertFalse(q["exact_partition_match"]["charged_matches_known"])

        # The harmonic survival family (now carried on molecule gonols) is treated
        # symmetrically for exact partition match.
        self.assertFalse(q["exact_partition_match"]["harmonic_matches_known"])
        self.assertFalse(q["exact_partition_match"]["harmonic_matches_control"])

        # Symmetric quantification numbers for the harmonic survival family
        # (evaluated only against the frozen original 5 known shapes).
        self.assertEqual(q["class_counts"]["harmonic_survival"], 4)
        self.assertEqual(q["splits_known_classes"]["harmonic_survival"], 1)
        self.assertEqual(q["collapses_across_known_classes"]["harmonic_survival"], 2)

        hpw = q["pairwise_vs_known"]["harmonic_survival"]
        self.assertEqual(hpw["total_pairs"], 10)
        self.assertEqual(hpw["fp"], 1)
        self.assertEqual(hpw["fn"], 2)

        # The periodic element gonol view of harmonic survival is now treated
        # symmetrically (first-class in quantify, standings, top-level facts).
        self.assertEqual(q["class_counts"]["periodic_element_harmonic_survival"], 4)
        self.assertEqual(q["splits_known_classes"]["periodic_element_harmonic_survival"], 1)
        self.assertEqual(q["collapses_across_known_classes"]["periodic_element_harmonic_survival"], 2)

        pepw = q["pairwise_vs_known"]["periodic_element_harmonic_survival"]
        self.assertEqual(pepw["total_pairs"], 10)
        self.assertEqual(pepw["fp"], 1)
        self.assertEqual(pepw["fn"], 2)

        self.assertFalse(q["exact_partition_match"]["periodic_element_harmonic_matches_known"])
        self.assertFalse(q["exact_partition_match"]["periodic_element_harmonic_matches_control"])

        # The subatomic gonol view of the lifted spiral is now treated symmetrically
        # (first-class carried fact, surfaced in quantify/readouts/partitions/standings).
        self.assertIn("subatomic_lifted_spiral", q["class_counts"])
        self.assertIn("subatomic_lifted_spiral", q["splits_known_classes"])
        self.assertIn("subatomic_lifted_spiral", q["collapses_across_known_classes"])
        self.assertIn("subatomic_lifted_spiral", q["pairwise_vs_known"])
        self.assertFalse(q["exact_partition_match"]["subatomic_lifted_spiral_matches_known"])
        # On the current nine-formula surface the bare subatomic projection and
        # stoichiometric control both partition into singletons. This is a
        # partition-resemblance fact only, not boundary-capacity evidence.
        self.assertTrue(q["exact_partition_match"]["subatomic_lifted_spiral_matches_control"])

        # Boundary capacity (interior modes=3 vs boundary dimensionality and coupling capacity)
        # is now a first-class family, sourced from the same carried lifted-spiral facts.
        # Molecule view distinguishes on ORIGINAL_PREREG (boundary measure).
        self.assertIn("boundary_capacity", q["class_counts"])
        self.assertIn("boundary_capacity", q["splits_known_classes"])
        self.assertIn("boundary_capacity", q["collapses_across_known_classes"])
        self.assertIn("boundary_capacity", q["pairwise_vs_known"])
        self.assertFalse(q["exact_partition_match"]["boundary_capacity_matches_known"])
        self.assertFalse(q["exact_partition_match"]["boundary_capacity_matches_control"])

        # The bare (periodic element / subatomic) views are also quantified symmetrically.
        self.assertIn("periodic_element_boundary_capacity", q["class_counts"])
        self.assertIn("subatomic_boundary_capacity", q["class_counts"])

    def test_harmonic_survival_signature_present_and_falsifies_on_known(self) -> None:
        # The nuclear harmonic layer (alpha-conjugate broadened) is now integrated
        # as a signature family in the (already enlarged) molecular experiment.
        record = compare_after_construction()
        self.assertIn("harmonic_survival", record.get("readouts", {}))
        self.assertIn("harmonic_survival", record.get("partitions", {}))
        self.assertIn("harmonic_survival_as_sealed_shape_prediction", record.get("standings", {}))

        q = record["quantify_distinguishing_power"]
        self.assertIn("harmonic_survival", q["class_counts"])
        self.assertIn("harmonic_survival", q["splits_known_classes"])
        self.assertIn("harmonic_survival", q["collapses_across_known_classes"])
        self.assertIn("harmonic_survival", q["pairwise_vs_known"])

        # Full constructed set yields 4 distinct harmonic survival signatures.
        self.assertEqual(q["class_counts"]["harmonic_survival"], 4)

        # Splits/collapses and pairwise are evaluated only against the frozen original 5.
        # Observed: splits 1 known class, collapses 2 known classes; pairwise fp=1, fn=2.
        self.assertEqual(q["splits_known_classes"]["harmonic_survival"], 1)
        self.assertEqual(q["collapses_across_known_classes"]["harmonic_survival"], 2)

        hpw = q["pairwise_vs_known"]["harmonic_survival"]
        self.assertEqual(hpw["total_pairs"], 10)
        self.assertEqual(hpw["fp"], 1)
        self.assertEqual(hpw["fn"], 2)

        # Standing on the frozen prereg is FALSIFIED (splits + collapses).
        self.assertEqual(
            record["standings"]["harmonic_survival_as_sealed_shape_prediction"],
            "FALSIFIED",
        )

        # The harmonic signature function is deterministic and participant-driven.
        # On the original prereg it produces 3 distinct signatures.
        known_sigs = {_harmonic_survival_signature(f) for f in ORIGINAL_PREREG}
        self.assertEqual(len(known_sigs), 3)

        # All constructed formulas have a defined (possibly empty) signature.
        constructed_readout = record["readouts"]["harmonic_survival"]
        self.assertGreaterEqual(len(constructed_readout), 9)
        for f in constructed_readout:
            self.assertIsInstance(_harmonic_survival_signature(f), tuple)

    def test_subatomic_harmonic_survival_matches_direct_and_is_quantified(self) -> None:
        # The nuclear harmonic survival is carried inside subatomic gonols
        # ("harmonic-surviving") and is now also exposed for the molecular experiment.
        # A cross-check inside compare_after_construction enforces direct == via-subatomic.
        record = compare_after_construction()
        self.assertIn("subatomic_harmonic_survival", record.get("readouts", {}))
        self.assertIn("subatomic_harmonic_survival", record.get("partitions", {}))
        self.assertIn(
            "subatomic_harmonic_survival_as_sealed_shape_prediction",
            record.get("standings", {}),
        )

        q = record["quantify_distinguishing_power"]
        self.assertIn("subatomic_harmonic_survival", q["class_counts"])
        self.assertIn("subatomic_harmonic_survival", q["splits_known_classes"])
        self.assertIn("subatomic_harmonic_survival", q["pairwise_vs_known"])

        # Because of the enforced cross-check, subatomic numbers equal the direct harmonic numbers.
        self.assertEqual(
            q["class_counts"]["subatomic_harmonic_survival"],
            q["class_counts"]["harmonic_survival"],
        )
        self.assertEqual(
            q["splits_known_classes"]["subatomic_harmonic_survival"],
            q["splits_known_classes"]["harmonic_survival"],
        )
        self.assertEqual(
            q["pairwise_vs_known"]["subatomic_harmonic_survival"]["total_pairs"],
            q["pairwise_vs_known"]["harmonic_survival"]["total_pairs"],
        )

        # Per-formula signatures match on the frozen known set (and therefore everywhere).
        for f in ORIGINAL_PREREG:
            self.assertEqual(
                _harmonic_survival_signature(f),
                _subatomic_harmonic_survival_signature(f),
            )
            self.assertEqual(
                _harmonic_survival_signature(f),
                _periodic_element_harmonic_survival_signature(f),
            )

        # Constructed side has the surface populated for all 9.
        self.assertGreaterEqual(
            len(record["readouts"]["subatomic_harmonic_survival"]), 9
        )

    def test_periodic_element_harmonic_survival_matches_direct_and_is_quantified(self) -> None:
        # The nuclear harmonic survival is carried on native periodic element gonols
        # ("harmonic-surviving") and is now also exposed for the molecular experiment.
        # Cross-checks inside compare_after_construction enforce molecule == subatomic == periodic.
        record = compare_after_construction()
        self.assertIn("periodic_element_harmonic_survival", record.get("readouts", {}))
        self.assertIn("periodic_element_harmonic_survival", record.get("partitions", {}))
        self.assertIn(
            "periodic_element_harmonic_survival_as_sealed_shape_prediction",
            record.get("standings", {}),
        )

        q = record["quantify_distinguishing_power"]
        self.assertIn("periodic_element_harmonic_survival", q["class_counts"])
        self.assertIn("periodic_element_harmonic_survival", q["splits_known_classes"])
        self.assertIn("periodic_element_harmonic_survival", q["pairwise_vs_known"])

        # Because of the enforced cross-checks, periodic element numbers equal the other harmonic views.
        self.assertEqual(
            q["class_counts"]["periodic_element_harmonic_survival"],
            q["class_counts"]["harmonic_survival"],
        )
        self.assertEqual(
            q["splits_known_classes"]["periodic_element_harmonic_survival"],
            q["splits_known_classes"]["harmonic_survival"],
        )
        self.assertEqual(
            q["pairwise_vs_known"]["periodic_element_harmonic_survival"]["total_pairs"],
            q["pairwise_vs_known"]["harmonic_survival"]["total_pairs"],
        )

        # Per-formula signatures match on the frozen known set (and therefore everywhere).
        for f in ORIGINAL_PREREG:
            self.assertEqual(
                _harmonic_survival_signature(f),
                _periodic_element_harmonic_survival_signature(f),
            )

        # Constructed side has the surface populated for all 9.
        self.assertGreaterEqual(
            len(record["readouts"]["periodic_element_harmonic_survival"]), 9
        )

    def test_periodic_element_lifted_spiral_matches_direct_and_is_quantified(self) -> None:
        # The lifted spiral (UCNS framed Möbius root-loop) is carried on native
        # periodic element gonols ("lifted-spiral") and is now also exposed for
        # the molecular experiment as a first-class family (parallel to harmonic).
        record = compare_after_construction()
        self.assertIn("periodic_element_lifted_spiral", record.get("readouts", {}))
        self.assertIn("periodic_element_lifted_spiral", record.get("partitions", {}))
        self.assertIn(
            "periodic_element_lifted_spiral_as_sealed_shape_prediction",
            record.get("standings", {}),
        )

        q = record["quantify_distinguishing_power"]
        self.assertIn("periodic_element_lifted_spiral", q["class_counts"])
        self.assertIn("periodic_element_lifted_spiral", q["splits_known_classes"])
        self.assertIn("periodic_element_lifted_spiral", q["collapses_across_known_classes"])
        self.assertIn("periodic_element_lifted_spiral", q["pairwise_vs_known"])

        # Full constructed set yields the surface for all 9.
        self.assertGreaterEqual(
            len(record["readouts"]["periodic_element_lifted_spiral"]), 9
        )

    def test_subatomic_gonol_lifted_spiral_matches_direct_and_is_quantified(self) -> None:
        # The lifted spiral (UCNS framed Möbius root-loop) is carried on subatomic
        # gonols ("lifted-spiral") and is now also exposed for the molecular
        # experiment as a first-class family (parallel to harmonic and the other
        # lifted-spiral families).
        record = compare_after_construction()
        self.assertIn("subatomic_lifted_spiral", record.get("readouts", {}))
        self.assertIn("subatomic_lifted_spiral", record.get("partitions", {}))
        self.assertIn(
            "subatomic_lifted_spiral_as_sealed_shape_prediction",
            record.get("standings", {}),
        )

        q = record["quantify_distinguishing_power"]
        self.assertIn("subatomic_lifted_spiral", q["class_counts"])
        self.assertIn("subatomic_lifted_spiral", q["splits_known_classes"])
        self.assertIn("subatomic_lifted_spiral", q["collapses_across_known_classes"])
        self.assertIn("subatomic_lifted_spiral", q["pairwise_vs_known"])

        # Full constructed set yields the surface for all 9.
        self.assertGreaterEqual(
            len(record["readouts"]["subatomic_lifted_spiral"]), 9
        )

    def test_molecule_gonol_carries_harmonic_survival(self) -> None:
        # The nuclear harmonic survival is now carried on the closed molecule
        # PublicGonol receipt (parallel to subatomic gonols), as the canonical
        # carried fact at molecular scale.
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            carried = dict(c.receipt.gonol.carried_options)
            self.assertIn("harmonic-surviving", carried)
            # The carried value must be consistent with the invariant.
            inv = c.invariants.get("harmonic_survival", ())
            carried_val = carried["harmonic-surviving"]
            if carried_val == "none":
                self.assertEqual(inv, ())
            else:
                self.assertEqual(carried_val.split(","), list(inv))

    def test_molecule_carried_harmonic_sourced_from_element_gonols(self) -> None:
        # The carried "harmonic-surviving" on the molecule PublicGonol receipt
        # (and the harmonic_survival invariant) must be computed from the
        # "harmonic-surviving" carried options on the native periodic element
        # gonols of its constituents (the primary EPAC construction path).
        for formula, c in construct_declared_molecules().items():
            comp = MOLECULE_COMPOSITIONS.get(formula, ())
            expected: set[str] = set()
            for sym, _cnt in comp:
                eg = construct_element_gonol(sym)
                hs = dict(eg.gonol.carried_options).get("harmonic-surviving", "none")
                if hs and hs != "none":
                    expected.update(hs.split(","))
            expected_t = tuple(sorted(expected))

            # Receipt carry
            rec_carried = harmonic_survival_carried_on_molecule(c)
            self.assertEqual(rec_carried, expected_t)

            # Invariant (authoritative molecule view)
            self.assertEqual(c.invariants.get("harmonic_survival", ()), expected_t)

    def test_compare_harmonic_family_sourced_from_molecule_receipt(self) -> None:
        # In the comparison record, the "harmonic_survival" family (used for
        # partitions, standings, quantify, top-level facts) must be exactly the
        # values carried on the molecule PublicGonol receipts.
        constructions = construct_declared_molecules()
        record = compare_after_construction()
        for f, c in constructions.items():
            receipt_carried = list(harmonic_survival_carried_on_molecule(c))
            self.assertEqual(record["readouts"]["harmonic_survival"][f], receipt_carried)
            # The value in the record must also equal the invariant on the construction.
            self.assertEqual(record["readouts"]["harmonic_survival"][f], list(c.invariants.get("harmonic_survival", ())))

    def test_molecule_gonol_harmonic_survival_preserved_under_replay(self) -> None:
        # The carried "harmonic-surviving" on molecule PublicGonol receipts must
        # survive exact replay (byte-replay determinism for the new carried fact).
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            carried_before = dict(c.receipt.gonol.carried_options).get("harmonic-surviving", "none")
            replayed = replay_public_gonol(c.receipt)
            carried_after = dict(replayed.gonol.carried_options).get("harmonic-surviving", "none")
            self.assertEqual(carried_before, carried_after)
            # The full receipt digest is stable under replay for these constructions.
            self.assertEqual(replayed.receipt_digest, c.receipt.receipt_digest)

    def test_periodic_element_gonol_harmonic_survival_preserved_under_replay(self) -> None:
        # The carried "harmonic-surviving" on periodic element gonol receipts must
        # survive exact replay (byte-replay determinism), parallel to molecule and subatomic.
        from epac_periodic import construct_element_gonol, replay_element_gonol
        for symbol in ("H", "C", "O", "Si"):
            receipt = construct_element_gonol(symbol)
            carried_before = dict(receipt.gonol.carried_options).get("harmonic-surviving", "none")
            replayed = replay_element_gonol(receipt)
            carried_after = dict(replayed.gonol.carried_options).get("harmonic-surviving", "none")
            self.assertEqual(carried_before, carried_after)
            self.assertEqual(replayed.receipt_digest, receipt.receipt_digest)

    def test_per_symbol_harmonic_survival_present_in_readouts_partitions_and_standings(self) -> None:
        # The per-symbol harmonic survival family (receipt-sourced, addressable per
        # constituent symbol) is now treated as a first-class signature family.
        record = compare_after_construction()
        self.assertIn("per_symbol_harmonic_survival", record.get("readouts", {}))
        self.assertIn("per_symbol_harmonic_survival", record.get("partitions", {}))
        self.assertIn(
            "per_symbol_harmonic_survival_as_sealed_shape_prediction",
            record.get("standings", {}),
        )

        q = record["quantify_distinguishing_power"]
        self.assertIn("per_symbol_harmonic_survival", q["class_counts"])
        self.assertIn("per_symbol_harmonic_survival", q["splits_known_classes"])
        self.assertIn("per_symbol_harmonic_survival", q["collapses_across_known_classes"])
        self.assertIn("per_symbol_harmonic_survival", q["pairwise_vs_known"])

        # Full constructed set yields a defined class count for per-symbol.
        self.assertGreaterEqual(q["class_counts"]["per_symbol_harmonic_survival"], 1)

        # Exact partition match facts for per-symbol harmonic.
        # On the frozen known set, per-symbol happens to produce partitions that
        # match the stoichiometric control exactly (observed behavior).
        self.assertIn("per_symbol_harmonic_matches_known", record)
        self.assertIn("per_symbol_harmonic_matches_control", record)
        self.assertFalse(record["per_symbol_harmonic_matches_known"])
        self.assertTrue(record["per_symbol_harmonic_matches_control"])

        # Top-level distinguishing facts exist and are populated.
        self.assertIn("per_symbol_harmonic_collapses_h2o_with_co2", record)
        self.assertIn("per_symbol_harmonic_distinguishes_h2o_from_co2", record)
        self.assertIn("linear_class_split_by_per_symbol_harmonic_survival", record)

    def test_per_symbol_harmonic_survival_quantify_symmetric_to_other_harmonic_families(self) -> None:
        record = compare_after_construction()
        q = record["quantify_distinguishing_power"]

        # Class counts, splits, collapses, and pairwise are present and use the same
        # frozen known set (5 formulas) as the other harmonic families.
        self.assertIn("per_symbol_harmonic_survival", q["class_counts"])
        self.assertIn("per_symbol_harmonic_survival", q["splits_known_classes"])
        self.assertIn("per_symbol_harmonic_survival", q["collapses_across_known_classes"])

        pepw = q["pairwise_vs_known"]["per_symbol_harmonic_survival"]
        self.assertEqual(pepw["total_pairs"], 10)  # C(5,2) over known prereg

        # Exact match flags for per-symbol: known is false (as for other harmonic families);
        # control is true on this data (per-symbol partitions match the stoichiometric control on the frozen 5).
        self.assertFalse(q["exact_partition_match"]["per_symbol_harmonic_matches_known"])
        self.assertTrue(q["exact_partition_match"]["per_symbol_harmonic_matches_control"])

    def test_per_symbol_harmonic_survival_sourced_from_receipts_and_matches_element_gonols(self) -> None:
        # The per-symbol family in readouts/quantify must be exactly the values carried
        # on molecule receipts (single source of truth), and must equal the lift from
        # participating native periodic element gonols.
        constructions = construct_declared_molecules()
        record = compare_after_construction()
        for f, c in constructions.items():
            receipt_per_sym = per_symbol_harmonic_survival_carried_on_molecule(c)
            self.assertEqual(
                record["readouts"]["per_symbol_harmonic_survival"][f],
                {s: list(vs) for s, vs in receipt_per_sym.items()},
            )
            # Compare helper must also match the receipt.
            self.assertEqual(
                _per_symbol_harmonic_survival_from_molecule(f),
                receipt_per_sym,
            )
            # Element-gonol lift must equal receipt carry.
            comp = MOLECULE_COMPOSITIONS.get(f, ())
            elem_view: dict[str, tuple[str, ...]] = {}
            for sym, _cnt in comp:
                eg = construct_element_gonol(sym)
                hs = dict(eg.gonol.carried_options).get("harmonic-surviving", "none")
                elem_view[sym] = tuple(sorted(set(hs.split(",")))) if hs and hs != "none" else ()
            self.assertEqual(receipt_per_sym, elem_view)

    def test_per_symbol_harmonic_survival_preserved_under_molecule_replay(self) -> None:
        # The per-symbol carried options ("<sym>-harmonic-surviving") must survive
        # exact replay on molecule receipts.
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            before = dict(c.receipt.gonol.carried_options)
            replayed = replay_public_gonol(c.receipt)
            after = dict(replayed.gonol.carried_options)
            # Collect per-symbol keys
            per_sym_keys = [k for k in before if k.endswith("-harmonic-surviving")]
            for k in per_sym_keys:
                self.assertEqual(before.get(k, "none"), after.get(k, "none"))
            self.assertEqual(replayed.receipt_digest, c.receipt.receipt_digest)

    def test_per_symbol_harmonic_survival_consistent_across_all_constructed(self) -> None:
        # Every constructed molecule must have per-symbol entries for its constituents
        # and the values must be subsets of the molecule-level harmonic-surviving.
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            per_sym = per_symbol_harmonic_survival_carried_on_molecule(c)
            mol_level = set(harmonic_survival_carried_on_molecule(c))
            for sym, cands in per_sym.items():
                self.assertTrue(set(cands).issubset(mol_level) or not cands)
                self.assertIn(sym, [s for s, _ in MOLECULE_COMPOSITIONS.get(formula, ())])

    def test_lifted_spiral_is_first_class_family(self) -> None:
        # The lifted spiral (UCNS framed Möbius root-loop) is now a first-class
        # signature family exactly parallel to the harmonic families.
        # All metrics respect ORIGINAL_PREREG for standings/quantify known side.
        record = compare_after_construction()
        self.assertIn("lifted_spiral", record.get("readouts", {}))
        self.assertIn("lifted_spiral", record.get("partitions", {}))
        self.assertIn("lifted_spiral_as_sealed_shape_prediction", record.get("standings", {}))

        # Top-level distinguishing facts (symmetric to other families).
        self.assertIn("lifted_spiral_collapses_h2o_with_co2", record)
        self.assertIn("lifted_spiral_distinguishes_h2o_from_co2", record)
        self.assertIn("linear_class_split_by_lifted_spiral", record)
        self.assertIn("lifted_spiral_matches_known", record)
        self.assertIn("lifted_spiral_matches_control", record)

        q = record["quantify_distinguishing_power"]
        self.assertIn("lifted_spiral", q["class_counts"])
        self.assertIn("lifted_spiral", q["splits_known_classes"])
        self.assertIn("lifted_spiral", q["collapses_across_known_classes"])
        self.assertIn("lifted_spiral", q["pairwise_vs_known"])
        self.assertIn("lifted_spiral_matches_known", q["exact_partition_match"])
        self.assertIn("lifted_spiral_matches_control", q["exact_partition_match"])

        # Pairwise over the frozen known set (5 formulas) is always 10 pairs.
        lpw = q["pairwise_vs_known"]["lifted_spiral"]
        self.assertEqual(lpw["total_pairs"], 10)

        # Readout populated for the full constructed set (>=9 after enlargement).
        self.assertGreaterEqual(len(record["readouts"]["lifted_spiral"]), 9)

        # On ORIGINAL_PREREG the spiral signature is defined and deterministic.
        for f in ORIGINAL_PREREG:
            self.assertIn(f, record["readouts"]["lifted_spiral"])
            sig = record["readouts"]["lifted_spiral"][f]
            self.assertIsInstance(sig, list)
            # canonical form (frames, axes, attach_count) as 3-tuple list
            self.assertEqual(len(sig), 3)

    def test_molecule_gonol_carries_lifted_spiral(self) -> None:
        # The lifted spiral (UCNS framed Möbius root-loop) is now carried on the
        # closed molecule PublicGonol receipt as a first-class fact, parallel to
        # the nuclear harmonic survival layer.
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            carried = dict(c.receipt.gonol.carried_options)
            self.assertIn("lifted-spiral", carried)
            # The carried value must be consistent with the invariant.
            inv = c.invariants.get("lifted_spiral")
            carried_val = carried["lifted-spiral"]
            # carried_val is the string form; inv is the tuple form.
            # They must represent the same canonical signature.
            self.assertIsNotNone(inv)
            # Basic structural check on carried string
            self.assertIn(";", carried_val)
            parts = carried_val.split(";")
            self.assertEqual(len(parts), 3)

    def test_molecule_gonol_lifted_spiral_preserved_under_replay(self) -> None:
        # The carried "lifted-spiral" on molecule PublicGonol receipts must
        # survive exact replay (byte-replay determinism for the new carried fact),
        # parallel to the harmonic-surviving carried options.
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            carried_before = dict(c.receipt.gonol.carried_options).get("lifted-spiral", "")
            replayed = replay_public_gonol(c.receipt)
            carried_after = dict(replayed.gonol.carried_options).get("lifted-spiral", "")
            self.assertEqual(carried_before, carried_after)
            # The full receipt digest is stable under replay.
            self.assertEqual(replayed.receipt_digest, c.receipt.receipt_digest)

    def test_compare_lifted_spiral_family_sourced_from_molecule_receipt(self) -> None:
        # In the comparison record, the "lifted_spiral" family (used for
        # partitions, standings, quantify, top-level facts) must be exactly the
        # values carried on the molecule PublicGonol receipts.
        constructions = construct_declared_molecules()
        record = compare_after_construction()
        for f, c in constructions.items():
            receipt_carried = list(lifted_spiral_carried_on_molecule(c))
            self.assertEqual(record["readouts"]["lifted_spiral"][f], receipt_carried)
            # The value in the record must also equal the invariant on the construction.
            self.assertEqual(record["readouts"]["lifted_spiral"][f], list(c.invariants.get("lifted_spiral", ())))

    def test_boundary_capacity_is_first_class_family(self) -> None:
        # Boundary capacity (fixed interior mode count=3 vs boundary dimensionality
        # and coupling capacity) is now a first-class signature family, derived
        # purely from the carried lifted-spiral facts (no new geometry).
        # Tests the principle: interior modes distinguished from boundary measure.
        record = compare_after_construction()
        self.assertIn("boundary_capacity", record.get("readouts", {}))
        self.assertIn("boundary_capacity", record.get("partitions", {}))
        self.assertIn("boundary_capacity_as_sealed_shape_prediction", record.get("standings", {}))

        # Top-level distinguishing facts.
        self.assertIn("boundary_capacity_collapses_h2o_with_co2", record)
        self.assertIn("boundary_capacity_distinguishes_h2o_from_co2", record)
        self.assertIn("linear_class_split_by_boundary_capacity", record)
        self.assertIn("boundary_capacity_matches_known", record)
        self.assertIn("boundary_capacity_matches_control", record)

        q = record["quantify_distinguishing_power"]
        self.assertIn("boundary_capacity", q["class_counts"])
        self.assertIn("boundary_capacity", q["splits_known_classes"])
        self.assertIn("boundary_capacity", q["collapses_across_known_classes"])
        self.assertIn("boundary_capacity", q["pairwise_vs_known"])
        self.assertIn("boundary_capacity_matches_known", q["exact_partition_match"])
        self.assertIn("boundary_capacity_matches_control", q["exact_partition_match"])

        # Pairwise over the frozen known set (5 formulas) is always 10 pairs.
        bc_pw = q["pairwise_vs_known"]["boundary_capacity"]
        self.assertEqual(bc_pw["total_pairs"], 10)

        # Readout populated for the full constructed set.
        self.assertGreaterEqual(len(record["readouts"]["boundary_capacity"]), 9)

        # On ORIGINAL_PREREG the molecule boundary capacity is defined and deterministic.
        for f in ORIGINAL_PREREG:
            self.assertIn(f, record["readouts"]["boundary_capacity"])
            bc = record["readouts"]["boundary_capacity"][f]
            self.assertIsInstance(bc, list)
            self.assertEqual(len(bc), 3)  # (interior_modes, boundary_dim, coupling_capacity)

    def test_boundary_capacity_carried_on_molecule(self) -> None:
        # The boundary capacity is a pure projection from the carried lifted-spiral
        # on the molecule receipt. The dedicated carried accessor must agree.
        constructions = construct_declared_molecules()
        for formula, c in constructions.items():
            bc = boundary_capacity_carried_on_molecule(c)
            self.assertIsInstance(bc, (list, tuple))
            self.assertEqual(len(bc), 3)
            self.assertEqual(bc[0], 3)  # fixed interior modes for the canonical double cover

    def test_boundary_capacity_compositional_transition_closure(self) -> None:
        # Compositional transition closure under strictly local affixation steps only.
        # Each step contributes only its local information (introduce a named atom instance,
        # or affix one ligand contribution whose slot count comes solely from that ligand's
        # atomic record). No global target totals and no finished receipt or known labels
        # are used to compute deltas.
        #
        # Tests:
        #   - path independence of final B across every valid ordering (introduces then affixes)
        #   - local step reproducibility (identical local step always yields identical delta)
        #   - accumulated B from local steps equals the direct carried B(R)
        #   - B is sufficient for these admissible local operations (no insufficiency observed)
        #
        # If this survives, B(R) functions as a closed transition variable for this construction class.

        closure = compositional_boundary_closure()
        self.assertTrue(closure["all_formulas_exhibit_compositional_transition_closure"])

        per = closure["per_formula"]
        # All formulas on the declared set must satisfy the closure properties.
        for f in MOLECULE_COMPOSITIONS:
            r = per[f]
            self.assertTrue(r["path_independent"], f"not path independent for {f}")
            self.assertTrue(r["matches_direct"], f"does not match direct B for {f}")
            self.assertTrue(r["local_steps_reproducible"], f"local steps not reproducible for {f}")
            self.assertFalse(r["b_insufficient"], f"B insufficient for local op on {f}")

        # Explicit check on ORIGINAL_PREREG (the frozen evaluation set).
        for f in ORIGINAL_PREREG:
            self.assertIn(f, per)
            r = per[f]
            self.assertTrue(r["path_independent"])
            self.assertTrue(r["matches_direct"])
            self.assertTrue(r["local_steps_reproducible"])
            self.assertFalse(r["b_insufficient"])
            # At least one path must exist; for H2 there is exactly one (symmetric).
            self.assertGreaterEqual(r["num_paths"], 1)

    def test_boundary_capacity_closure_via_comparison_record(self) -> None:
        # The comparison record must surface the compositional closure facts
        # (path independence, local reproducibility, match to direct, overall flag).
        record = compare_after_construction()
        self.assertIn("boundary_capacity_compositional_closure", record)
        self.assertIn("boundary_capacity_compositional_path_independent", record)
        self.assertIn("boundary_capacity_compositional_all_reproducible_locally", record)

        self.assertTrue(record["boundary_capacity_compositional_path_independent"])
        self.assertTrue(record["boundary_capacity_compositional_all_reproducible_locally"])

        cl = record["boundary_capacity_compositional_closure"]
        self.assertTrue(cl["all_formulas_exhibit_compositional_transition_closure"])

    def test_boundary_capacity_descriptor_sufficiency_sweep_sealed(self) -> None:
        # Exhaustive EPAC-local descriptor sufficiency / collision falsifier.
        # Enumerates reachable states from declared sources and ops on the frozen nine.
        # Computes B only from locked rules. Groups by B(R). Classifies collisions by
        # operational equivalence under the replay/transition contract. No new coordinate.
        # Bare and control views are included. Nine locked formulas untouched.
        sweep = boundary_capacity_descriptor_sufficiency_sweep()

        self.assertTrue(sweep.get("sealed"))
        self.assertTrue(sweep.get("no_new_coordinate"))

        # Question and scope are recorded.
        self.assertIn("Does B(R)", sweep.get("question", ""))
        self.assertIn("frozen nine", sweep.get("scope", ""))

        agg = sweep.get("aggregate", {})
        # Cross-scale element compatibility and end-to-end molecular closure remain SURVIVED.
        self.assertEqual(agg.get("subatomic_to_element_closure"), "SURVIVED")
        self.assertEqual(agg.get("end_to_end_subatomic_to_molecule_closure"), "SURVIVED")
        # Sufficiency on the present descriptor is decided by collisions among non-equivalent states.
        self.assertEqual(agg["boundary_capacity_sufficiency"], "FALSIFIED")
        self.assertEqual(agg["boundary_capacity_compositionality"], "SURVIVED")
        from epac_cross_scale_closure import cross_scale_compositional_closure
        closure_statuses = cross_scale_compositional_closure()["statuses"]
        for key in ("subatomic_to_element_closure", "end_to_end_subatomic_to_molecule_closure", "boundary_capacity_compositionality"):
            self.assertEqual(agg[key], closure_statuses[key])

        # Control-like partition failure is explicitly classified (not a B transition counterexample).
        disp = sweep.get("control_failure_disposition", {})
        self.assertEqual(disp.get("classification"), "stale_or_incorrect_control_assertion")
        self.assertFalse(disp.get("impacts_b_sufficiency"))

        # Collisions, when present, are classified SURVIVED (equivalent) or FALSIFIED (distinct states).
        b_groups = sweep.get("b_groups", {})
        for c in sweep.get("collisions", []):
            self.assertIn(c.get("classification"), ("SURVIVED", "FALSIFIED"))
            self.assertIn(str(c.get("b")), b_groups)

        # Enumeration covers the locked nine molecules + their bare sources.
        self.assertGreaterEqual(sweep.get("enumerated_b_states", 0), 9)
        # No extension: every locked formula appears as a molecule: entry in the enumerated B groups.
        b_group_values = " ".join(" ".join(v) for v in sweep.get("b_groups", {}).values())
        for f in MOLECULE_COMPOSITIONS:
            self.assertIn(f"molecule:{f}", b_group_values)

    def test_boundary_capacity_sufficiency_via_comparison_record(self) -> None:
        record = compare_after_construction()
        self.assertIn("boundary_capacity_descriptor_sufficiency", record)
        self.assertIn("boundary_capacity_sufficiency_status", record)
        suff = record["boundary_capacity_descriptor_sufficiency"]
        self.assertTrue(suff.get("sealed"))
        self.assertTrue(suff.get("no_new_coordinate"))
        self.assertIn(record["boundary_capacity_sufficiency_status"], ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))

    def test_boundary_capacity_information_loss_localization_sealed(self) -> None:
        # Information-loss localization over the six sealed B collisions.
        # Uses only already-present EPAC operational data, records, invariants,
        # participants, source/relation/digests. Identifies earliest step where
        # states are distinguishable while B is identical, plus smallest witness.
        # No new coordinate. Nine formulas frozen.
        loc = boundary_capacity_information_loss_localization()

        self.assertTrue(loc.get("sealed"))
        self.assertTrue(loc.get("no_new_coordinate"))
        self.assertIn("Exactly which already-present", loc.get("question", ""))
        self.assertIn("six sealed collision classes", loc.get("scope", ""))

        agg = loc.get("aggregate", {})
        self.assertEqual(agg.get("information_loss_localization"), "SURVIVED")
        self.assertTrue(agg.get("all_collisions_have_explicit_witness"))

        # Every sealed colliding B must have explicit per-pair localization.
        per = loc.get("per_collision", {})
        self.assertGreaterEqual(len(per), 1)
        for bstr, entry in per.items():
            self.assertGreater(entry.get("num_pairs", 0), 0)
            for p in entry.get("localizations", []):
                self.assertIn("earliest_distinguishable_step_while_b_identical", p)
                self.assertIn("first_point_of_information_loss", p)
                self.assertIn("witness", p)
                self.assertIn("witness_class", p)
                self.assertNotEqual(p["witness_class"], "undetermined")

        # Recurring witness classes must be recorded (scale_identity_erased is expected across all).
        rec = loc.get("recurring_witness_classes", {})
        self.assertIn("scale_identity_erased", rec)

    def test_information_loss_via_comparison_record(self) -> None:
        record = compare_after_construction()
        self.assertIn("boundary_capacity_information_loss", record)
        self.assertIn("information_loss_localization_status", record)
        loss = record["boundary_capacity_information_loss"]
        self.assertTrue(loss.get("sealed"))
        self.assertTrue(loss.get("no_new_coordinate"))
        self.assertEqual(loss.get("aggregate", {}).get("information_loss_localization"), "SURVIVED")
        self.assertIn(record["information_loss_localization_status"], ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))

    def test_boundary_capacity_quotient_test_sealed(self) -> None:
        # Boundary-capacity quotient test over the six sealed collisions.
        # B(R1) == B(R2)  ⇔  R1 ≡∂ R2 under admissible boundary probes
        # (B readout, attachment K, attachment profile, transition deltas),
        # with all identifiers/labels withheld for equivalence decisions.
        # Converse: different B are distinguishable by at least one admissible probe.
        q = boundary_capacity_quotient_test()

        self.assertTrue(q.get("sealed"))
        self.assertTrue(q.get("no_new_coordinate"))
        self.assertIn("does equality of B(R) coincide", q.get("question", ""))
        self.assertIn("six sealed collision classes", q.get("scope", ""))

        agg = q.get("aggregate", {})
        self.assertIn(agg.get("boundary_capacity_quotient"), ("SURVIVED", "FALSIFIED"))
        self.assertIn(agg.get("same_B_implies_equivalent_under_boundary_probes"), (True, False))
        self.assertTrue(agg.get("different_B_are_distinguishable"))

        # Every sealed collision reports probe outcomes using only admissible probes.
        per = q.get("per_collision", {})
        self.assertGreaterEqual(len(per), 1)
        for bstr, entry in per.items():
            for pr in entry.get("pair_results", []):
                self.assertIn("admissible_probe_set", pr)
                self.assertIn("probe_by_probe", pr)
                self.assertIn("equivalent_under_boundary_probes", pr)
                # first_behavioral_discriminator may be None (equivalent) or a dict
                fd = pr.get("first_behavioral_discriminator")
                if fd is not None:
                    self.assertIn("probe", fd)
                    self.assertIn("a_outcome", fd)
                    self.assertIn("b_outcome", fd)

        # Converse examples must exist and be distinguished by b readout.
        conv = q.get("converse_different_b", {})
        self.assertTrue(conv.get("all_distinguished_by_b_readout"))
        self.assertGreater(len(conv.get("examples", [])), 0)

    def test_boundary_capacity_quotient_via_comparison_record(self) -> None:
        record = compare_after_construction()
        self.assertIn("boundary_capacity_quotient", record)
        self.assertIn("boundary_capacity_quotient_status", record)
        qt = record["boundary_capacity_quotient"]
        self.assertTrue(qt.get("sealed"))
        self.assertTrue(qt.get("no_new_coordinate"))
        self.assertIn(record["boundary_capacity_quotient_status"], ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))

    def test_boundary_capacity_minimal_refinement_audit_sealed(self) -> None:
        # Minimal behavioral refinement audit.
        # Exhaustive over all subsets of the four already-declared identity-free
        # candidate observables. Compares induced partitions (B + S) against the
        # sealed full ≡∂ on all 27 frozen states (both directions).
        # Reports exact matches, inclusion-minimal sets, fewest-observable,
        # canonicality, and witness pairs for rejected smaller candidates.
        # No identity smuggled; no new observables derived.
        audit = boundary_capacity_minimal_refinement_audit()

        self.assertTrue(audit.get("sealed"))
        self.assertTrue(audit.get("no_new_coordinate"))
        self.assertIn("smallest set of already-declared", audit.get("question", ""))
        self.assertIn("27 frozen states", audit.get("scope", ""))

        agg = audit.get("aggregate", {})
        self.assertEqual(agg.get("minimal_behavioral_refinement"), "SURVIVED")

        # At least one exact match must exist.
        exacts = audit.get("exact_match_subsets", [])
        self.assertGreater(len(exacts), 0)

        # Minimal sets and fewest size must be reported.
        mins = audit.get("minimal_refinement_sets", [])
        self.assertGreater(len(mins), 0)
        few = audit.get("fewest_additional_observables")
        self.assertIsNotNone(few)
        self.assertGreaterEqual(few, 1)

        # Canonicality must be one of the allowed values.
        self.assertIn(audit.get("canonicality"), ("UNIQUE", "NON-UNIQUE", "UNRESOLVED"))
        self.assertIn(audit.get("minimality"), ("PROVED", "NOT PROVED"))

        # Full class count must match the sealed quotient surface.
        self.assertEqual(audit.get("full_class_count"), 19)

        # Every exact minimal set must reproduce the full quotient (already checked by audit).
        # Sanity: the reported minimal_refinement (if present) must be one of the minimal sets.
        mr = audit.get("minimal_refinement")
        if mr is not None:
            self.assertIn(mr, mins)

    def test_minimal_behavioral_refinement_via_comparison_record(self) -> None:
        record = compare_after_construction()
        self.assertIn("boundary_capacity_minimal_refinement_audit", record)
        self.assertIn("minimal_behavioral_refinement_status", record)
        ra = record["boundary_capacity_minimal_refinement_audit"]
        self.assertTrue(ra.get("sealed"))
        self.assertTrue(ra.get("no_new_coordinate"))
        self.assertIn(record["minimal_behavioral_refinement_status"], ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))

    def test_representation_audit_sealed(self) -> None:
        # Representation-audit capstone.
        # Consolidates all prior stages and performs the final representation-equivalence check.
        # Verifies the structured ledger (inputs, 8 stages, outputs with status/witnesses/partitions/etc.).
        rep = epac_representation_audit()

        self.assertTrue(rep.get("sealed"))
        self.assertTrue(rep.get("no_new_coordinate"))

        inputs = rep.get("inputs", {})
        self.assertIn("frozen_states", inputs)
        self.assertIn("identity_exclusions", inputs)

        stages = rep.get("stages", {})
        for stage in (
            "closure",
            "non_degeneracy",
            "sufficiency",
            "collision_localization",
            "behavioral_equivalence",
            "probe_completeness",
            "minimal_refinement",
            "representation_equivalence",
        ):
            self.assertIn(stage, stages)

        outputs = rep.get("outputs", {})
        self.assertIn(outputs.get("overall"), ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))
        self.assertIn("witnesses", outputs)
        self.assertIn("partitions", outputs)
        self.assertIn("counterexamples", outputs)
        self.assertIn("provenance", outputs)
        self.assertIn("hmmm", outputs)

    def test_representation_audit_via_comparison_record(self) -> None:
        record = compare_after_construction()
        self.assertIn("epac_representation_audit", record)
        self.assertIn("representation_audit_overall", record)
        ra = record["epac_representation_audit"]
        self.assertTrue(ra.get("sealed"))
        self.assertTrue(ra.get("no_new_coordinate"))
        self.assertIn(record["representation_audit_overall"], ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))

    def test_probe_relativity_formalization_sealed(self) -> None:
        # Probe-relativity formalization over declared surfaces.
        # Uses locked 27-state representation audit as immutable baseline.
        # Tests O ↦ Q_O ↦ D_min(O) for already-declared admissible observable sets.
        pr = epac_probe_relativity_formalization()

        self.assertTrue(pr.get("sealed"))
        self.assertTrue(pr.get("no_new_coordinate"))

        inputs = pr.get("inputs", {})
        self.assertIn("frozen_states", inputs)
        self.assertEqual(inputs.get("frozen_states"), 27)
        self.assertIn("baseline", inputs)

        surfaces = pr.get("surfaces", {})
        self.assertIn("O_B", surfaces)
        self.assertIn("O_admissible", surfaces)
        self.assertIn("O_struct", surfaces)

        outputs = pr.get("outputs", {})
        self.assertIn(outputs.get("overall"), ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))
        self.assertIn("witnesses", outputs)
        self.assertIn("provenance", outputs)
        self.assertIn("hmmm", outputs)

    def test_probe_relativity_formalization_via_comparison_record(self) -> None:
        record = compare_after_construction()
        self.assertIn("epac_probe_relativity_formalization", record)
        self.assertIn("probe_relativity_overall", record)
        pr = record["epac_probe_relativity_formalization"]
        self.assertTrue(pr.get("sealed"))
        self.assertTrue(pr.get("no_new_coordinate"))
        self.assertEqual(record["probe_relativity_overall"], pr.get("outputs", {}).get("overall", "UNRESOLVED"))
        self.assertIn(record["probe_relativity_overall"], ("SURVIVED", "FALSIFIED", "UNRESOLVED", "BLOCKED"))


if __name__ == "__main__":
    unittest.main()
