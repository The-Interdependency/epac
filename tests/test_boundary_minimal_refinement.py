"""Executable witnesses for the EPAC minimal boundary-refinement audit."""

# === CHECKS ===
# id: check_minimal_refinement_uses_only_existing_omitted_distinguishers
#   proves: minimal_refinement_uses_only_existing_omitted_distinguishers
#   call: self::test_scope_uses_only_the_13_existing_distinguishing_observables
#   mutates: none
#   cleanup: none
#
# id: check_minimal_refinement_searches_by_partition_equality
#   proves: minimal_refinement_searches_by_partition_equality
#   call: self::test_minimal_candidates_match_the_full_partition
#   mutates: none
#   cleanup: none
#
# id: check_minimal_refinement_reports_all_minimum_sets
#   proves: minimal_refinement_reports_all_minimum_sets
#   call: self::test_minimum_size_and_all_minimum_sets_are_reported
#   mutates: none
#   cleanup: none
#
# id: check_minimal_refinement_classifies_boundary_semantics
#   proves: minimal_refinement_classifies_boundary_semantics
#   call: self::test_minimal_candidates_are_intrinsic_and_not_label_history_codes
#   mutates: none
#   cleanup: none
#
# id: check_minimal_refinement_keeps_B_unmodified
#   proves: minimal_refinement_keeps_B_unmodified
#   call: self::test_B_is_not_modified_or_promoted
#   mutates: none
#   cleanup: none
#
# id: check_minimal_refinement_classifies_compositionality
#   proves: minimal_refinement_classifies_compositionality
#   call: self::test_local_reproducibility_and_cross_scale_compositionality_are_separate
#   mutates: none
#   cleanup: none
#
# id: check_minimal_refinement_blocks_pcea_mapping
#   proves: minimal_refinement_blocks_pcea_mapping
#   call: self::test_pcea_mapping_remains_blocked
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

import epac_boundary_minimal_refinement as _installed_audit
EPAC_ROOT = Path(_installed_audit.__file__).resolve().parent

from epac_boundary_minimal_refinement import (  # noqa: E402
    BLOCKED,
    SURVIVED,
    UNRESOLVED,
    boundary_minimal_refinement_report,
)


EXPECTED_MINIMAL_SETS = (
    ("charged_structure_readout",),
    ("quaternion_structure_readout",),
    ("geometry_from_declared_couplings",),
    ("structure_from_charged_couplings",),
    ("degree_relations",),
    ("oriented_instance_couplings",),
    ("quaternion_of_local_three",),
    ("quaternions_from_declared_couplings",),
)

EXPECTED_NONMINIMAL_SINGLETONS = {
    "topology_structure_readout": 17,
    "local_three_structures": 17,
    "has_declared_coupling": 17,
    "instances_missing_oriented_hub_coupling": 17,
    "require_every_instance_has_oriented_hub_coupling": 17,
}


class BoundaryMinimalRefinementTest(unittest.TestCase):
    report: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = boundary_minimal_refinement_report()

    def test_scope_uses_only_the_13_existing_distinguishing_observables(self) -> None:
        scope = self.report["scope"]
        self.assertEqual(self.report["surface"]["state_count"], 27)
        self.assertEqual(scope["candidate_observable_count"], 13)
        self.assertTrue(scope["uses_only_existing_omitted_distinguishers"])
        self.assertFalse(scope["B_descriptor_modified"])
        self.assertEqual(
            self.report["partitions"]["baseline_B_class_count"],
            16,
        )
        self.assertEqual(
            self.report["partitions"]["full_omitted_observable_class_count"],
            21,
        )
        self.assertTrue(
            self.report["partitions"]["full_partition_matches_completeness_audit"]
        )

    def test_minimal_candidates_match_the_full_partition(self) -> None:
        rows = {
            row["operation_name"]: row
            for row in self.report["candidate_ledger"]
        }
        for candidate in EXPECTED_MINIMAL_SETS:
            row = rows[candidate[0]]
            self.assertTrue(row["minimal_candidate"])
            self.assertEqual(row["singleton_class_count"], 21)
            self.assertTrue(row["singleton_reproduces_full_partition"])

        for name, class_count in EXPECTED_NONMINIMAL_SINGLETONS.items():
            row = rows[name]
            self.assertFalse(row["minimal_candidate"])
            self.assertEqual(row["singleton_class_count"], class_count)
            self.assertFalse(row["singleton_reproduces_full_partition"])

    def test_minimum_size_and_all_minimum_sets_are_reported(self) -> None:
        minimum = self.report["minimal_refinement"]
        self.assertEqual(minimum["minimum_size"], 1)
        self.assertFalse(minimum["minimum_unique"])
        self.assertEqual(minimum["minimal_set_count"], 8)
        self.assertEqual(minimum["minimal_equivalent_sets"], EXPECTED_MINIMAL_SETS)

    def test_minimal_candidates_are_intrinsic_and_not_label_history_codes(self) -> None:
        rows = [
            row for row in self.report["candidate_ledger"]
            if row["minimal_candidate"]
        ]
        self.assertTrue(rows)
        self.assertTrue(all(row["intrinsic_boundary_semantics"] for row in rows))
        self.assertTrue(
            all(
                row["normalized_observable_excludes_labels_ids_and_history"]
                for row in rows
            )
        )
        self.assertFalse(
            any(row["merely_encodes_construction_history_or_labels"] for row in rows)
        )

    def test_B_is_not_modified_or_promoted(self) -> None:
        self.assertFalse(self.report["scope"]["B_descriptor_modified"])
        self.assertIn(
            "do not modify B merely to rescue probe completeness",
            self.report["requires_more"],
        )
        self.assertEqual(
            self.report["descriptor_sufficiency"][
                "finite_21_class_partition_reproduction"
            ],
            SURVIVED,
        )
        self.assertEqual(
            self.report["descriptor_sufficiency"][
                "promotable_descriptor_sufficiency"
            ],
            UNRESOLVED,
        )

    def test_local_reproducibility_and_cross_scale_compositionality_are_separate(self) -> None:
        compositionality = self.report["compositionality"]
        self.assertEqual(
            compositionality["local_reproducibility_status"],
            SURVIVED,
        )
        self.assertEqual(
            compositionality["cross_scale_compositionality_status"],
            UNRESOLVED,
        )
        self.assertEqual(self.report["statuses"]["canonicality"], UNRESOLVED)
        self.assertEqual(self.report["statuses"]["compositionality"], UNRESOLVED)

    def test_pcea_mapping_remains_blocked(self) -> None:
        self.assertEqual(
            self.report["statuses"],
            {
                "minimal_refinement_size": SURVIVED,
                "all_minimal_equivalent_sets": SURVIVED,
                "intrinsic_boundary_semantics": SURVIVED,
                "history_or_label_encoding": SURVIVED,
                "canonicality": UNRESOLVED,
                "compositionality": UNRESOLVED,
                "refined_quotient_class_count": SURVIVED,
                "descriptor_sufficiency": UNRESOLVED,
                "pcea_mapping": BLOCKED,
            },
        )
        self.assertIn(
            "PCEA mapping remains blocked until canonicality and compositionality close",
            self.report["requires_more"],
        )

    def test_audit_module_has_no_direct_ucns_or_pcea_imports(self) -> None:
        source_path = EPAC_ROOT / "epac_boundary_minimal_refinement.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(
            any(name == "ucns" or name.startswith("ucns.") for name in imports)
        )
        self.assertFalse(
            any(name == "pcea" or name.startswith("pcea.") for name in imports)
        )


if __name__ == "__main__":
    unittest.main()
