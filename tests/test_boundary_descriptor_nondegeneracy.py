"""Executable witnesses for EPAC boundary-descriptor non-degeneracy controls."""

# === CHECKS ===
# id: check_nondegeneracy_freezes_surface_before_controls
#   proves: nondegeneracy_freezes_surface_before_controls
#   call: self::test_freezes_current_surface_before_generating_controls
#   mutates: none
#   cleanup: none
#
# id: check_boundary_descriptor_label_invariance
#   proves: boundary_descriptor_label_invariance
#   call: self::test_label_and_order_controls_preserve_B
#   mutates: none
#   cleanup: none
#
# id: check_boundary_descriptor_equivalent_path_invariance
#   proves: boundary_descriptor_equivalent_path_invariance
#   call: self::test_equivalent_paths_remain_cross_scale_invariant
#   mutates: none
#   cleanup: none
#
# id: check_boundary_descriptor_d_boundary_sensitivity
#   proves: boundary_descriptor_d_boundary_sensitivity
#   call: self::test_d_boundary_controls_change_only_declared_dimension
#   mutates: none
#   cleanup: none
#
# id: check_boundary_descriptor_c_boundary_sensitivity
#   proves: boundary_descriptor_c_boundary_sensitivity
#   call: self::test_c_boundary_controls_change_only_declared_coupling_count
#   mutates: none
#   cleanup: none
#
# id: check_boundary_descriptor_non_singleton_control_discrimination
#   proves: boundary_descriptor_non_singleton_control_discrimination
#   call: self::test_non_singleton_controls_split_without_erasing_singleton_warning
#   mutates: none
#   cleanup: none
#
# id: check_boundary_descriptor_collision_search_classifies_collisions
#   proves: boundary_descriptor_collision_search_classifies_collisions
#   call: self::test_collision_search_classifies_coarse_same_B_pairs
#   mutates: none
#   cleanup: none
#
# id: check_boundary_descriptor_audit_does_not_extend_B
#   proves: boundary_descriptor_audit_does_not_extend_B
#   call: self::test_descriptor_shape_remains_three_component_count_tuple
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

from collections import Counter
import sys
import unittest
from pathlib import Path


from epac_boundary_nondegeneracy import (
    BoundaryState,
    boundary_descriptor_nondegeneracy_report,
    build_counterfactual_neighborhood,
    freeze_current_construction_surface,
)
from epac_cross_scale_closure import SURVIVED


class BoundaryDescriptorNondegeneracyTest(unittest.TestCase):
    surface: dict
    neighborhood: dict
    report: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.surface = freeze_current_construction_surface()
        cls.neighborhood = build_counterfactual_neighborhood(cls.surface)
        cls.report = boundary_descriptor_nondegeneracy_report()

    @classmethod
    def _mutations_of_kind(cls, kind: str) -> tuple:
        return tuple(
            mutation
            for mutation in cls.neighborhood["mutations"]
            if mutation.kind == kind
        )

    def test_freezes_current_surface_before_generating_controls(self) -> None:
        surface = self.surface
        self.assertTrue(surface["frozen_before_controls"])
        self.assertEqual(
            surface["formulas"],
            ("H2", "H2O", "NH3", "CH4", "CO2", "H2S", "BF3", "PH3", "SiH4"),
        )
        self.assertEqual(
            surface["required_elements"],
            ("H", "O", "N", "C", "S", "B", "F", "P", "Si"),
        )
        self.assertEqual(len(surface["states"]), 27)
        self.assertEqual(
            dict(Counter(state.scale for state in surface["states"].values())),
            {"subatomic": 9, "element": 9, "molecule": 9},
        )

        neighborhood = self.neighborhood
        self.assertEqual(neighborhood["surface_id"], surface["surface_id"])
        self.assertEqual(neighborhood["parent_states"], surface["states"])
        self.assertTrue(
            all(mutation.declared_before_evaluation for mutation in neighborhood["mutations"])
        )

    def test_label_and_order_controls_preserve_B(self) -> None:
        report = self.report
        self.assertEqual(report["label_invariance"]["status"], SURVIVED)
        self.assertTrue(report["label_invariance"]["all_expected_invariant"])

        surface = self.surface
        for kind in ("relabel", "reorder"):
            controls = self._mutations_of_kind(kind)
            self.assertEqual(len(controls), len(surface["states"]))
            for mutation in controls:
                parent = surface["states"][mutation.parent_id]
                self.assertEqual(mutation.expected_b, parent.b)
                self.assertEqual(mutation.actual_state.b, parent.b)
                self.assertFalse(mutation.requires_boundary_distinct_from_parent)

    def test_equivalent_paths_remain_cross_scale_invariant(self) -> None:
        report = self.report
        equivalent_paths = report["equivalent_path_invariance"]
        self.assertEqual(equivalent_paths["status"], SURVIVED)
        self.assertTrue(equivalent_paths["element_path_independent"])
        self.assertTrue(equivalent_paths["formula_path_independent"])
        self.assertEqual(
            set(equivalent_paths["cross_scale_closure_statuses"].values()),
            {SURVIVED},
        )

    def test_d_boundary_controls_change_only_declared_dimension(self) -> None:
        report = self.report
        d_sensitivity = report["d_boundary_sensitivity"]
        self.assertEqual(d_sensitivity["status"], SURVIVED)
        self.assertEqual(d_sensitivity["positive_failures"], ())
        self.assertEqual(d_sensitivity["negative_failures"], ())
        self.assertEqual(
            set(d_sensitivity["positive_control_kinds"]),
            {
                "add_axis",
                "delete_axis",
                "duplicate_participant",
                "hierarchy_refinement_perturbation",
            },
        )

        surface = self.surface
        neighborhood = self.neighborhood
        positive = [
            mutation
            for mutation in neighborhood["mutations"]
            if mutation.expected_relation == "distinct_by_d_boundary"
        ]
        self.assertTrue(
            any(mutation.kind == "hierarchy_refinement_perturbation" for mutation in positive)
        )
        for mutation in positive:
            parent = surface["states"][mutation.parent_id]
            self.assertEqual(mutation.actual_state.b, mutation.expected_b)
            self.assertEqual(mutation.actual_state.b[0], parent.b[0])
            self.assertNotEqual(mutation.actual_state.b[1], parent.b[1])
            self.assertEqual(mutation.actual_state.b[2], parent.b[2])

    def test_c_boundary_controls_change_only_declared_coupling_count(self) -> None:
        report = self.report
        c_sensitivity = report["c_boundary_sensitivity"]
        self.assertEqual(c_sensitivity["status"], SURVIVED)
        self.assertEqual(c_sensitivity["positive_failures"], ())
        self.assertEqual(c_sensitivity["negative_failures"], ())
        self.assertEqual(
            set(c_sensitivity["positive_control_kinds"]),
            {"add_coupling", "delete_coupling"},
        )
        self.assertEqual(
            set(c_sensitivity["negative_control_kinds"]),
            {"rewire_same_count"},
        )

        surface = self.surface
        neighborhood = self.neighborhood
        for mutation in neighborhood["mutations"]:
            parent = surface["states"][mutation.parent_id]
            if mutation.expected_relation == "distinct_by_c_boundary":
                self.assertEqual(mutation.actual_state.b, mutation.expected_b)
                self.assertEqual(mutation.actual_state.b[0], parent.b[0])
                self.assertEqual(mutation.actual_state.b[1], parent.b[1])
                self.assertNotEqual(mutation.actual_state.b[2], parent.b[2])
                self.assertEqual(mutation.actual_state.bulk_count, parent.bulk_count)
            elif mutation.kind == "rewire_same_count":
                self.assertEqual(mutation.actual_state.b, parent.b)
                self.assertNotEqual(
                    mutation.actual_state.structure_signature,
                    parent.structure_signature,
                )

    def test_non_singleton_controls_split_without_erasing_singleton_warning(self) -> None:
        report = self.report
        non_singleton = report["non_singleton_control_discrimination"]
        self.assertEqual(non_singleton["status"], SURVIVED)
        self.assertTrue(non_singleton["singleton_warning_retained"])
        self.assertTrue(non_singleton["non_singleton_bulk_groups"])
        self.assertTrue(non_singleton["split_non_singleton_groups"])

        b_by_formula = non_singleton["B_by_formula"]
        self.assertNotEqual(b_by_formula["H2O"], b_by_formula["CO2"])
        self.assertEqual(b_by_formula["H2O"], b_by_formula["H2S"])

        singleton = non_singleton["singleton_partition_regression"]
        self.assertTrue(singleton["observed_subatomic_lifted_spiral_matches_control"])
        self.assertEqual(singleton["classification"], "stale_or_incorrect_control_assertion")
        self.assertFalse(singleton["compositional_counterexample"])

    def test_collision_search_classifies_coarse_same_B_pairs(self) -> None:
        report = self.report
        collisions = report["descriptor_collision_search"]
        self.assertEqual(collisions["status"], SURVIVED)
        self.assertEqual(collisions["classification"], "complete_for_bounded_first_order_neighborhood")
        self.assertEqual(collisions["required_boundary_distinct_failures"], ())
        self.assertEqual(
            collisions["bounded_state_count"],
            report["surface"]["state_count"] + report["control_neighborhood"]["mutation_count"],
        )
        self.assertGreater(collisions["same_B_collision_count"], 0)
        self.assertEqual(
            collisions["same_B_collision_count"],
            collisions["classified_collision_count"],
        )

        classifications = {
            example["classification"]
            for example in collisions["coarse_collision_examples"]
        }
        self.assertIn("declared_invariance_or_same_count_control", classifications)
        self.assertIn("intentionally_coarse_equivalence_class", classifications)
        self.assertEqual(
            set(report["statuses"].values()),
            {SURVIVED},
        )

    def test_descriptor_shape_remains_three_component_count_tuple(self) -> None:
        surface = self.surface
        sample = next(iter(surface["states"].values()))
        self.assertIsInstance(sample, BoundaryState)
        self.assertEqual(
            sample.b,
            (
                sample.interior_modes,
                len(sample.boundary_axes),
                len(sample.coupling_slots),
            ),
        )
        self.assertEqual(len(sample.b), 3)


if __name__ == "__main__":
    unittest.main()
