"""Caller annotations must not become later construction or audit evidence."""
# === CHECKS ===
# id: check_epac_cached_evidence_returns_independent_values
#   proves: epac_cached_evidence_returns_independent_values
#   call: self::test_cached_audit_reports_are_independent
#   mutates: caller-owned copies of cached evidence
#   cleanup: none; cached canonical records must remain unchanged
# === END CHECKS ===
from copy import deepcopy


def test_molecular_construction_and_population_are_independent():
    from epac_molecular import construct_molecule, construct_declared_molecules
    first = construct_molecule("H2O")
    expected = deepcopy(first.invariants)
    first.invariants["mobius"]["frame"].clear()
    first.invariants["caller annotation"] = "not evidence"
    second = construct_molecule("H2O")
    assert second.invariants == expected
    assert second is not first
    assert second.receipt.receipt_digest == first.receipt.receipt_digest
    population = construct_declared_molecules()
    population["H2O"].invariants["mobius"]["frame"].append("fabricated")
    population["H2O"].invariants["atom_count"] = 99
    assert construct_declared_molecules()["H2O"].invariants == expected
    assert construct_molecule("H2O").invariants == expected


def test_cached_audit_reports_are_independent():
    from epac_cross_scale_closure import element_closure_ledger, formula_closure_ledger, cross_scale_compositional_closure
    from epac_boundary_nondegeneracy import freeze_current_construction_surface, boundary_descriptor_nondegeneracy_report
    from epac_boundary_quotient import boundary_capacity_quotient_report
    from epac_boundary_minimal_refinement import boundary_minimal_refinement_report
    from epac_boundary_probe_completeness import omitted_boundary_operation_effects, declared_operation_ledger, boundary_probe_completeness_report
    from epac_molecular import epac_representation_audit

    def nested_container(value):
        children = value.values() if isinstance(value, dict) else value if isinstance(value, (tuple, list)) else ()
        for child in children:
            found = nested_container(child)
            if found is not None:
                return found
        return value if isinstance(value, (dict, list)) and value else None

    calls = (
        (element_closure_ledger, ("C",)), (formula_closure_ledger, ("H2O",)),
        (cross_scale_compositional_closure, ()), (freeze_current_construction_surface, ()),
        (boundary_descriptor_nondegeneracy_report, ()), (boundary_capacity_quotient_report, ()),
        (boundary_minimal_refinement_report, ()), (omitted_boundary_operation_effects, ()),
        (declared_operation_ledger, ()), (boundary_probe_completeness_report, ()),
    )
    for function, args in calls:
        first = function(*args)
        expected = deepcopy(first)
        nested = nested_container(first)
        assert nested is not None, function.__name__
        nested.clear()
        assert function(*args) == expected, function.__name__
        if isinstance(first, dict):
            first.clear()
            assert function(*args) == expected, function.__name__
    altered = cross_scale_compositional_closure()
    altered["statuses"]["element_state_compatibility"] = "FALSIFIED"
    assert epac_representation_audit()["stages"]["closure"]["status"] == "SURVIVED"
