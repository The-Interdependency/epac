"""Executable witnesses for EPAC boundary-capacity quotient evidence."""

# === CHECKS ===
# id: check_boundary_quotient_freezes_current_surface
#   proves: boundary_quotient_freezes_current_surface
#   call: self::test_quotient_uses_only_the_frozen_state_surface
#   mutates: none
#   cleanup: none
#
# id: check_boundary_quotient_probe_inventory_is_existing_and_count_valued
#   proves: boundary_quotient_probe_inventory_is_existing_and_count_valued
#   call: self::test_probe_inventory_is_existing_and_B_valued
#   mutates: none
#   cleanup: none
#
# id: check_boundary_quotient_ignores_identity_incidence_and_topology
#   proves: boundary_quotient_ignores_identity_incidence_and_topology
#   call: self::test_probe_signature_omits_identity_incidence_and_topology
#   mutates: none
#   cleanup: none
#
# id: check_boundary_quotient_relation_is_probe_signature_equality
#   proves: boundary_quotient_relation_is_probe_signature_equality
#   call: self::test_boundary_equivalence_is_probe_signature_equality
#   mutates: none
#   cleanup: none
#
# id: check_boundary_quotient_B_matches_probe_equivalence
#   proves: boundary_quotient_B_matches_probe_equivalence
#   call: self::test_B_equality_matches_boundary_capacity_probe_equivalence
#   mutates: none
#   cleanup: none
#
# id: check_boundary_quotient_preserves_state_sufficiency_falsification
#   proves: boundary_quotient_preserves_state_sufficiency_falsification
#   call: self::test_state_sufficiency_remains_falsified
#   mutates: none
#   cleanup: none
#
# id: check_boundary_quotient_does_not_extend_B
#   proves: boundary_quotient_does_not_extend_B
#   call: self::test_quotient_does_not_extend_descriptor
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import sys
import unittest
from pathlib import Path


from epac_boundary_quotient import (
    BOUNDARY_CAPACITY_PROBES,
    boundary_capacity_quotient_report,
)
from epac_cross_scale_closure import FALSIFIED, SURVIVED, UNRESOLVED


class BoundaryCapacityQuotientTest(unittest.TestCase):
    report: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = boundary_capacity_quotient_report()

    def test_quotient_uses_only_the_frozen_state_surface(self) -> None:
        surface = self.report["surface"]
        self.assertTrue(surface["frozen_before_quotient"])
        self.assertEqual(surface["state_count"], 27)
        self.assertEqual(
            surface["state_ids"],
            (
                "subatomic:H",
                "element:H",
                "subatomic:O",
                "element:O",
                "subatomic:N",
                "element:N",
                "subatomic:C",
                "element:C",
                "subatomic:S",
                "element:S",
                "subatomic:B",
                "element:B",
                "subatomic:F",
                "element:F",
                "subatomic:P",
                "element:P",
                "subatomic:Si",
                "element:Si",
                "molecule:H2",
                "molecule:H2O",
                "molecule:NH3",
                "molecule:CH4",
                "molecule:CO2",
                "molecule:H2S",
                "molecule:BF3",
                "molecule:PH3",
                "molecule:SiH4",
            ),
        )

    def test_probe_inventory_is_existing_and_B_valued(self) -> None:
        inventory = self.report["probe_inventory"]
        self.assertEqual(inventory["status"], SURVIVED)
        self.assertEqual(inventory["probe_kinds"], BOUNDARY_CAPACITY_PROBES)
        self.assertEqual(
            inventory["probe_source"],
            "epac_boundary_nondegeneracy.build_counterfactual_neighborhood",
        )
        self.assertTrue(inventory["all_admissible_outputs_are_B"])
        self.assertFalse(inventory["uses_identity_or_incidence_fields"])
        self.assertGreater(inventory["admissible_output_count"], 0)

    def test_probe_signature_omits_identity_incidence_and_topology(self) -> None:
        inventory = self.report["probe_inventory"]
        self.assertEqual(
            set(inventory["identity_fields_excluded"]),
            {
                "state_id",
                "scale",
                "source",
                "role",
                "bulk_count",
                "labels",
                "boundary_axes",
                "coupling_slots",
                "structure_signature",
                "parent_id",
                "mutation_id",
            },
        )
        for behavior_class in self.report["boundary_capacity_behavior_classes"]:
            self.assertIsInstance(behavior_class, tuple)
            for record in behavior_class:
                self.assertEqual(len(record), 5)
                self.assertIn(record[1], {"admissible", "inadmissible"})
                for value in record[2:4]:
                    if value is not None:
                        self.assertEqual(len(value), 3)
                        self.assertTrue(all(isinstance(component, int) for component in value))

    def test_boundary_equivalence_is_probe_signature_equality(self) -> None:
        statuses = self.report["statuses"]
        self.assertEqual(statuses["boundary_capacity_equivalence_relation"], SURVIVED)
        self.assertEqual(len(self.report["B_classes"]), 16)
        self.assertEqual(len(self.report["boundary_capacity_behavior_classes"]), 16)
        self.assertEqual(
            self.report["B_partition"],
            self.report["behavior_partition"],
        )

    def test_B_equality_matches_boundary_capacity_probe_equivalence(self) -> None:
        statuses = self.report["statuses"]
        self.assertEqual(statuses["B_matches_boundary_capacity_quotient"], SURVIVED)
        self.assertEqual(self.report["same_B_probe_mismatches"], ())
        self.assertEqual(self.report["unequal_B_equivalent_pairs"], ())
        self.assertEqual(self.report["equal_B_pair_count"], 19)

    def test_state_sufficiency_remains_falsified(self) -> None:
        statuses = self.report["statuses"]
        self.assertEqual(statuses["state_sufficiency"], FALSIFIED)
        self.assertEqual(statuses["incidence_completeness"], UNRESOLVED)
        self.assertEqual(statuses["topology_completeness"], UNRESOLVED)

        collision_groups = {
            tuple(group["state_ids"])
            for group in self.report["state_sufficiency_collisions"]
        }
        self.assertIn(("element:H", "subatomic:H"), collision_groups)
        self.assertIn(
            ("subatomic:B", "subatomic:C", "subatomic:F", "subatomic:N", "subatomic:O"),
            collision_groups,
        )
        self.assertIn(("molecule:H2O", "molecule:H2S"), collision_groups)
        self.assertIn(("molecule:BF3", "molecule:NH3", "molecule:PH3"), collision_groups)
        self.assertIn(("molecule:CH4", "molecule:SiH4"), collision_groups)

    def test_quotient_does_not_extend_descriptor(self) -> None:
        self.assertEqual(
            self.report["statuses"],
            {
                "probe_inventory": SURVIVED,
                "boundary_capacity_equivalence_relation": SURVIVED,
                "B_matches_boundary_capacity_quotient": SURVIVED,
                "state_sufficiency": FALSIFIED,
                "incidence_completeness": UNRESOLVED,
                "topology_completeness": UNRESOLVED,
            },
        )
        self.assertIn(
            "do not promote B as a complete EPAC state descriptor",
            self.report["requires_more"],
        )
        for b_value in self.report["B_classes"]:
            self.assertEqual(len(b_value), 3)
            self.assertTrue(all(isinstance(component, int) for component in b_value))


if __name__ == "__main__":
    unittest.main()
