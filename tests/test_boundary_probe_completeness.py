"""Executable witnesses for EPAC boundary-probe completeness audit."""

# === CHECKS ===
# id: check_boundary_probe_audit_freezes_current_surface
#   proves: boundary_probe_audit_freezes_current_surface
#   call: self::test_audit_uses_only_the_frozen_27_state_surface
#   mutates: none
#   cleanup: none
#
# id: check_boundary_probe_audit_inventory_covers_declared_operations
#   proves: boundary_probe_audit_inventory_covers_declared_operations
#   call: self::test_declared_operations_preserve_unresolved_semantics
#   mutates: none
#   cleanup: none
#
# id: check_boundary_probe_audit_uses_no_new_probe_or_descriptor
#   proves: boundary_probe_audit_uses_no_new_probe_or_descriptor
#   call: self::test_audit_adds_only_existing_observables_and_does_not_extend_B
#   mutates: none
#   cleanup: none
#
# id: check_boundary_probe_audit_excludes_identity_discriminators
#   proves: boundary_probe_audit_excludes_identity_discriminators
#   call: self::test_structural_observable_examples_exclude_ids_and_labels
#   mutates: none
#   cleanup: none
#
# id: check_boundary_probe_audit_imports_no_ucns_or_pcea
#   proves: boundary_probe_audit_imports_no_ucns_or_pcea
#   call: self::test_audit_module_has_no_direct_ucns_or_pcea_imports
#   mutates: none
#   cleanup: none
#
# id: check_boundary_probe_audit_reruns_same_B_and_unequal_B_comparisons
#   proves: boundary_probe_audit_reruns_same_B_and_unequal_B_comparisons
#   call: self::test_omitted_operations_rerun_same_B_and_unequal_B_comparisons
#   mutates: none
#   cleanup: none
#
# id: check_boundary_probe_audit_reports_partition_change
#   proves: boundary_probe_audit_reports_partition_change
#   call: self::test_omitted_existing_observables_refine_the_quotient_partition
#   mutates: none
#   cleanup: none
#
# id: check_boundary_probe_audit_classifies_completeness
#   proves: boundary_probe_audit_classifies_completeness
#   call: self::test_probe_completeness_is_falsified_not_unresolved
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

import epac_boundary_probe_completeness as _installed_audit
EPAC_ROOT = Path(_installed_audit.__file__).resolve().parent

from epac_boundary_probe_completeness import (
    AMBIGUOUS,
    BOUNDARY_OBSERVING,
    FALSIFIED,
    SURVIVED,
    UNRESOLVED,
    boundary_probe_completeness_report,
)
from epac_boundary_quotient import BOUNDARY_CAPACITY_PROBES


class BoundaryProbeCompletenessTest(unittest.TestCase):
    report: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = boundary_probe_completeness_report()

    @staticmethod
    def _row_by_operation(report: dict, operation: str) -> dict:
        rows = {
            row["operation"]: row
            for row in report["operation_ledger"]
        }
        return rows[operation]

    @staticmethod
    def _contains_identifier(value: object) -> bool:
        if isinstance(value, str):
            return value.startswith("epac.") or "#" in value
        if isinstance(value, dict):
            return any(
                BoundaryProbeCompletenessTest._contains_identifier(key)
                or BoundaryProbeCompletenessTest._contains_identifier(item)
                for key, item in value.items()
            )
        if isinstance(value, (tuple, list)):
            return any(
                BoundaryProbeCompletenessTest._contains_identifier(item)
                for item in value
            )
        return False

    def test_audit_uses_only_the_frozen_27_state_surface(self) -> None:
        surface = self.report["surface"]
        self.assertTrue(surface["frozen_before_audit"])
        self.assertEqual(surface["state_count"], 27)
        self.assertEqual(
            self.report["current_probe_inventory"]["baseline_class_count"],
            16,
        )
        self.assertEqual(
            self.report["current_probe_inventory"]["equal_B_pair_count"],
            19,
        )
        self.assertEqual(
            self.report["current_probe_inventory"][
                "state_sufficiency_collision_group_count"
            ],
            6,
        )

    def test_inventory_covers_packaged_execution_modules(self) -> None:
        from importlib.resources import files
        expected = {path.name for path in _installed_audit.EPAC_ROOT.glob("epac_*.py")}
        for directory, package in (("subatomic", "epac_subatomic"), ("viz", "epac_viz"), ("data", "epac_data")):
            expected.update(directory + "/" + path.name for path in files(package).iterdir()
                            if path.name.endswith(".py"))
        self.assertEqual(set(_installed_audit.OPERATION_SOURCE_FILES), expected)
        operations = {row["operation"]: row for row in _installed_audit._declared_operations()}
        import epac_viz
        public_exports = {name for name in epac_viz.__all__ if callable(getattr(epac_viz, name))}
        self.assertEqual(public_exports, {row["name"] for row in operations.values() if row["module"] == "epac_viz"})
        for name in public_exports:
            self.assertIn("epac_viz." + name, operations)
            self.assertIn("epac_viz.spiral_viz." + name, operations)
            self.assertEqual(_installed_audit._classify_operation("epac_viz", name), AMBIGUOUS)
        for name in ("AtomicRecord", "ElectronState", "atomic_record", "iter_table"):
            row = operations["epac_atomic." + name]
            self.assertEqual(_installed_audit._classify_operation(row["module"], row["name"]), AMBIGUOUS)

    def test_declared_operations_preserve_unresolved_semantics(self) -> None:
        inventory = self.report["operation_inventory"]
        self.assertEqual(inventory["operation_count"], 153)
        self.assertEqual(inventory["boundary_relevant_count"], 58)
        self.assertEqual(inventory["ambiguous_count"], 56)
        self.assertEqual(inventory["omitted_boundary_relevant_count"], 14)
        for row in self.report["operation_ledger"]:
            if row["name"] in self.report["unmapped_operation_probes"]:
                self.assertEqual(row["boundary_relevance"], BOUNDARY_OBSERVING)
                self.assertFalse(row["currently_probed"])
                self.assertIsNone(row["can_distinguish_same_B_states"])
                self.assertEqual(row["effect_on_quotient"], "unresolved_quotient_effect")
        ambiguous = [row for row in self.report["operation_ledger"] if row["boundary_relevance"] == AMBIGUOUS]
        for row in ambiguous:
            self.assertIsNone(row["currently_probed"])
            self.assertIsNone(row["can_distinguish_same_B_states"])
            self.assertEqual(row["represented_by"], "unresolved_boundary_relevance")
            self.assertEqual(row["effect_on_quotient"], "unresolved_boundary_relevance")
        self.assertIn("epac_molecular.epac_representation_audit", {row["operation"] for row in ambiguous})
        self.assertIn("epac_molecular.epac_probe_relativity_formalization", {row["operation"] for row in ambiguous})
        self.assertIn("epac_atomic_derivation.derive_period", {row["operation"] for row in ambiguous})
        self.assertIn("epac_b_derivation.active_orbital_set", {row["operation"] for row in ambiguous})
        self.assertIn("epac_b_derivation.ligand_field_spin_control", {row["operation"] for row in ambiguous})
        for operation in ("epac_boundary_minimal_refinement.boundary_minimal_refinement_report",
                          "epac_boundary_probe_completeness.boundary_probe_completeness_report",
                          "epac_boundary_probe_completeness.declared_operation_ledger",
                          "epac_boundary_probe_completeness.omitted_boundary_operation_effects"):
            self.assertIn(operation, {row["operation"] for row in ambiguous})
        for name in ("new_operation", "boundary_new_operation", "new_harmonic_operation"):
            self.assertEqual(_installed_audit._classify_operation("fixture", name), AMBIGUOUS)

        charged = self._row_by_operation(
            self.report,
            "epac_dimensional_arity.charged_structure_readout",
        )
        self.assertEqual(charged["boundary_relevance"], BOUNDARY_OBSERVING)
        self.assertFalse(charged["currently_probed"])
        self.assertTrue(charged["can_distinguish_same_B_states"])

        capacity = self._row_by_operation(
            self.report,
            "epac_molecular.boundary_capacity_carried_on_molecule",
        )
        self.assertTrue(capacity["currently_probed"])

        local_step = self._row_by_operation(
            self.report,
            "epac_molecular.apply_local_step",
        )
        self.assertTrue(local_step["currently_probed"])

    def test_audit_adds_only_existing_observables_and_does_not_extend_B(self) -> None:
        self.assertEqual(
            self.report["current_probe_inventory"]["probe_kinds"],
            BOUNDARY_CAPACITY_PROBES,
        )
        self.assertIn(
            "do not add a descriptor component in this audit",
            self.report["requires_more"],
        )
        for effect in self.report["omitted_operation_effects"].values():
            for group in effect["same_B_collision_group_results"]:
                self.assertEqual(len(group["B"]), 3)
                self.assertTrue(all(isinstance(component, int) for component in group["B"]))

    def test_structural_observable_examples_exclude_ids_and_labels(self) -> None:
        for effect in self.report["omitted_operation_effects"].values():
            self.assertTrue(effect["identity_discriminators_excluded"])
            for example in effect["same_B_distinguished_pair_examples"]:
                self.assertFalse(self._contains_identifier(example["left_observable"]))
                self.assertFalse(self._contains_identifier(example["right_observable"]))

    def test_audit_module_has_no_direct_ucns_or_pcea_imports(self) -> None:
        source_path = EPAC_ROOT / "epac_boundary_probe_completeness.py"
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

    def test_omitted_operations_rerun_same_B_and_unequal_B_comparisons(self) -> None:
        effects = self.report["omitted_operation_effects"]
        self.assertEqual(set(effects), {"charged_structure_readout", "topology_structure_readout", "quaternion_structure_readout"})
        unmapped = self.report["unmapped_operation_probes"]
        self.assertEqual(len(unmapped), 11)
        for name, disposition in unmapped.items():
            self.assertIn("hmmm", disposition)
            self.assertNotIn(name, effects)
            for row in self.report["operation_ledger"]:
                if row["name"] == name:
                    self.assertEqual(row["boundary_relevance"], BOUNDARY_OBSERVING)
                    self.assertIsNone(row["can_distinguish_same_B_states"])
        for effect in effects.values():
            self.assertEqual(len(effect["same_B_collision_group_results"]), 6)
            self.assertEqual(effect["unequal_B_comparison_count"], 332)

        topology = effects["topology_structure_readout"]
        self.assertEqual(topology["same_B_distinguished_pair_count"], 1)
        self.assertEqual(topology["augmented_class_count"], 17)

        charged = effects["charged_structure_readout"]
        self.assertEqual(charged["same_B_distinguished_pair_count"], 6)
        self.assertEqual(charged["augmented_class_count"], 21)

    def test_omitted_existing_observables_refine_the_quotient_partition(self) -> None:
        combined = self.report["combined_omitted_observable_effect"]
        self.assertEqual(combined["baseline_class_count"], 16)
        self.assertEqual(combined["combined_augmented_class_count"], 21)
        self.assertTrue(combined["quotient_partition_changes"])

        omitted = self.report["omitted_distinguishing_operations"]
        self.assertIn(
            "epac_dimensional_arity.topology_structure_readout",
            omitted,
        )
        self.assertIn(
            "epac_dimensional_arity.charged_structure_readout",
            omitted,
        )
        self.assertIn(
            "epac_dimensional_arity.quaternion_structure_readout",
            omitted,
        )

    def test_probe_completeness_is_falsified_not_unresolved(self) -> None:
        self.assertEqual(
            self.report["statuses"],
            {
                "declared_operation_inventory": SURVIVED,
                "ambiguous_boundary_semantics": UNRESOLVED,
                "omitted_boundary_relevant_operations": FALSIFIED,
                "quotient_partition_stability_under_omitted_existing_observables": FALSIFIED,
                "boundary_probe_completeness": FALSIFIED,
            },
        )
        self.assertIn(
            "B is not complete for the full presently declared EPAC operational surface",
            self.report["requires_more"],
        )


if __name__ == "__main__":
    unittest.main()
