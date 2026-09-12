"""Executable witnesses for EPAC cross-scale boundary-capacity closure."""

# === CHECKS ===
# id: check_cross_scale_required_elements_are_locked_formula_inputs
#   proves: cross_scale_required_elements_are_locked_formula_inputs
#   call: self::test_required_elements_are_exactly_the_locked_formula_inputs
#   mutates: none
#   cleanup: none
#
# id: check_subatomic_to_element_boundary_refines_shell_axes
#   proves: subatomic_to_element_boundary_refines_shell_axes
#   call: self::test_subatomic_to_element_derivation_matches_bare_elements
#   mutates: none
#   cleanup: none
#
# id: check_cross_scale_element_refinement_is_path_independent
#   proves: cross_scale_element_refinement_is_path_independent
#   call: self::test_element_refinement_is_path_independent
#   mutates: none
#   cleanup: none
#
# id: check_cross_scale_formula_closure_replays_from_subatomic_sources
#   proves: cross_scale_formula_closure_replays_from_subatomic_sources
#   call: self::test_all_formulas_close_end_to_end_from_subatomic_sources
#   mutates: none
#   cleanup: none
#
# id: check_subatomic_lifted_spiral_control_failure_is_classified
#   proves: subatomic_lifted_spiral_control_failure_is_classified
#   call: self::test_control_like_partition_failure_is_not_a_counterexample
#   mutates: none
#   cleanup: none
#
# id: check_cross_scale_promotion_blocks_descriptor_injection
#   proves: cross_scale_promotion_blocks_descriptor_injection
#   call: self::test_tampered_source_breaks_derivation_instead_of_passing_by_count
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from __future__ import annotations

from dataclasses import replace
import inspect
import sys
import unittest
from pathlib import Path


from epac_cross_scale_closure import (
    SURVIVED,
    control_like_partition_failure_disposition,
    cross_scale_compositional_closure,
    derive_element_boundary_from_subatomic,
    element_closure_ledger,
    formula_closure_ledger,
    required_element_symbols,
)
from epac_molecular import MOLECULE_COMPOSITIONS
from epac_periodic import construct_element_gonol, lifted_spiral_carried_on_element
from epac_subatomic.subatomic_gonol import construct_subatomic_gonol


class CrossScaleCompositionalClosureTest(unittest.TestCase):
    def test_source_refinement_is_independent_of_element_field_compatibility(self) -> None:
        from unittest.mock import patch
        import epac_cross_scale_closure as closure
        bare = construct_element_gonol("C")
        original_carried = closure._carried
        for mismatched_field in ("Z", "harmonic-surviving"):
            def carried(receipt):
                result = dict(original_carried(receipt))
                if receipt is bare:
                    result[mismatched_field] = "mismatching evidence"
                return result
            with patch.object(closure, "construct_element_gonol", return_value=bare), patch.object(closure, "_carried", side_effect=carried):
                ledger = element_closure_ledger.__wrapped__("C")
            self.assertEqual(ledger["source_refinement_status"], SURVIVED)
            self.assertEqual(ledger["status"], closure.FALSIFIED)
            with patch.object(closure, "required_element_symbols", return_value=("C",)), patch.object(closure, "element_closure_ledger", return_value=ledger), patch.object(closure, "MOLECULE_COMPOSITIONS", {}), patch.object(closure, "control_like_partition_failure_disposition", return_value={"compositional_counterexample": False}):
                statuses = cross_scale_compositional_closure.__wrapped__()["statuses"]
            self.assertEqual(statuses["subatomic_to_element_closure"], SURVIVED)
            self.assertEqual(statuses["element_state_compatibility"], closure.FALSIFIED)
            self.assertEqual(statuses["boundary_capacity_compositionality"], closure.FALSIFIED)
        with patch.object(closure, "_refinement_path_variants", return_value={"first": ("a",), "second": ("b",)}):
            ledger = element_closure_ledger.__wrapped__("C")
        self.assertEqual(ledger["source_refinement_status"], closure.FALSIFIED)
        self.assertTrue(all(ledger["compatibility"]["common_field_matches"].values()))

    def test_required_elements_are_exactly_the_locked_formula_inputs(self) -> None:
        self.assertEqual(
            tuple(MOLECULE_COMPOSITIONS),
            ("H2", "H2O", "NH3", "CH4", "CO2", "H2S", "BF3", "PH3", "SiH4"),
        )
        self.assertEqual(
            required_element_symbols(),
            ("H", "O", "N", "C", "S", "B", "F", "P", "Si"),
        )

    def test_subatomic_to_element_derivation_matches_bare_elements(self) -> None:
        source = inspect.getsource(derive_element_boundary_from_subatomic)
        self.assertNotIn("construct_element_gonol", source)
        self.assertEqual(
            tuple(inspect.signature(derive_element_boundary_from_subatomic).parameters),
            ("receipt",),
        )

        for symbol in required_element_symbols():
            ledger = element_closure_ledger(symbol)
            self.assertEqual(ledger["status"], SURVIVED, symbol)
            self.assertFalse(ledger["local_operation"]["uses_future_molecule"], symbol)
            self.assertFalse(ledger["local_operation"]["uses_target_descriptor"], symbol)
            self.assertFalse(ledger["local_operation"]["descriptor_injected"], symbol)
            self.assertEqual(
                ledger["derived_element"]["boundary_capacity"],
                ledger["bare_element"]["boundary_capacity"],
                symbol,
            )
            self.assertEqual(
                ledger["derived_element"]["lifted_spiral"],
                ledger["bare_element"]["lifted_spiral"],
                symbol,
            )
            self.assertTrue(
                all(ledger["compatibility"]["common_field_matches"].values()),
                symbol,
            )
            self.assertTrue(ledger["compatibility"]["harmonic_survival_matches"], symbol)

    def test_element_refinement_is_path_independent(self) -> None:
        for symbol in required_element_symbols():
            ledger = element_closure_ledger(symbol)
            path = ledger["path_independence"]
            self.assertEqual(len(path["admissible_variants"]), 4, symbol)
            self.assertTrue(path["path_independent"], symbol)
            self.assertEqual(len(set(path["variant_axes"].values())), 1, symbol)

    def test_all_formulas_close_end_to_end_from_subatomic_sources(self) -> None:
        report = cross_scale_compositional_closure()
        self.assertEqual(
            report["statuses"],
            {
                "subatomic_to_element_closure": SURVIVED,
                "element_state_compatibility": SURVIVED,
                "end_to_end_subatomic_to_molecule_closure": SURVIVED,
                "boundary_capacity_compositionality": SURVIVED,
            },
        )

        for formula in MOLECULE_COMPOSITIONS:
            ledger = formula_closure_ledger(formula)
            self.assertEqual(ledger["status"], SURVIVED, formula)
            self.assertTrue(
                ledger["paths"]["consumes_only_compatible_elements"],
                formula,
            )
            self.assertTrue(ledger["paths"]["path_independent"], formula)
            self.assertTrue(ledger["paths"]["local_steps_reproducible"], formula)
            self.assertTrue(ledger["direct_composed_agreement"], formula)
            self.assertEqual(
                ledger["composed_boundary_capacity"],
                ledger["direct_boundary_capacity"],
                formula,
            )
            self.assertTrue(
                ledger["molecule_projection"]["projected_axes_match_direct"],
                formula,
            )
            self.assertFalse(
                ledger["molecule_projection"]["uses_future_molecule_descriptor"],
                formula,
            )
            self.assertFalse(ledger["molecule_projection"]["descriptor_injected"], formula)

    def test_control_like_partition_failure_is_not_a_counterexample(self) -> None:
        disposition = control_like_partition_failure_disposition()
        self.assertTrue(
            disposition["observed_subatomic_lifted_spiral_matches_control"]
        )
        self.assertEqual(
            disposition["classification"],
            "stale_or_incorrect_control_assertion",
        )
        self.assertFalse(disposition["compositional_counterexample"])
        self.assertEqual(disposition["status"], SURVIVED)

    def test_tampered_source_breaks_derivation_instead_of_passing_by_count(self) -> None:
        receipt = construct_subatomic_gonol("C")
        participants = list(receipt.gonol.participants)
        first_shell_index = next(
            index
            for index, participant in enumerate(participants)
            if participant.relation == "epac.atomic.shell"
        )
        shell = participants[first_shell_index]
        tampered_shell = replace(shell, participants=shell.participants[:-1])
        participants[first_shell_index] = tampered_shell
        tampered_receipt = replace(
            receipt,
            gonol=replace(receipt.gonol, participants=tuple(participants)),
        )

        derived = derive_element_boundary_from_subatomic(tampered_receipt)
        bare = lifted_spiral_carried_on_element(construct_element_gonol("C"))

        self.assertNotEqual(derived["derived_lifted_spiral"][1], bare[1])
        self.assertNotEqual(derived["derived_boundary_capacity"], (3, len(bare[1]), 0))


if __name__ == "__main__":
    unittest.main()
