"""Executable witnesses for the nuclear harmonic-relation candidates."""

# === CHECKS ===
# id: check_every_harmonic_candidate_declares_six_evidence_fields
#   proves: every_harmonic_candidate_declares_six_evidence_fields
#   call: self::test_every_candidate_declares_six_evidence_fields
#   mutates: none
#   cleanup: none
#
# id: check_harmonic_parameter_is_time_agnostic
#   proves: harmonic_parameter_is_time_agnostic
#   call: self::test_parameter_is_time_agnostic
#   mutates: none
#   cleanup: none
#
# id: check_no_public_gonol_position_operation_invented
#   proves: no_public_gonol_position_operation_invented
#   call: self::test_no_position_operation_invented
#   mutates: none
#   cleanup: none
#
# id: check_recurrence_test_is_deterministic
#   proves: recurrence_test_is_deterministic
#   call: self::test_recurrence_deterministic_and_replayable
#   mutates: none
#   cleanup: none
#
# id: check_all_results_remain_cross_domain_hypothesis
#   proves: all_results_remain_cross_domain_hypothesis
#   call: self::test_all_results_cross_domain_hypothesis
#   mutates: none
#   cleanup: none
# === END CHECKS ===

import nuclear_harmonic_candidates as m


def test_every_candidate_declares_six_evidence_fields():
    for candidate in m.CANDIDATES:
        assert candidate.participants
        assert candidate.ordered_parameter.get("kind")
        assert candidate.ordered_parameter.get("declaration")
        assert candidate.recurrence_mapping
        assert candidate.equivalence_condition
        assert candidate.information_loss
        assert candidate.physical_provenance
        assert len(candidate.receipt) == 64


def test_parameter_is_time_agnostic():
    for candidate in m.CANDIDATES:
        assert candidate.ordered_parameter["time_agnostic"] is True
        assert "time" not in candidate.ordered_parameter["kind"]
    assert m.ORDERED_PARAMETER["kind"] == "nucleon-content-sequence"


def test_no_position_operation_invented():
    # The module must not import UCNS geometry or call position operations.
    # (Contract ids legitimately name the forbidden surface, so only actual
    # imports and call forms are asserted absent.)
    source = open(m.__file__, encoding="utf-8").read()
    assert "import ucns" not in source
    assert "from ucns" not in source
    assert "public_gonol_function(" not in source
    assert "native_mobius_state(" not in source
    assert "phase" not in m.ORDERED_PARAMETER["declaration"]


def test_recurrence_deterministic_and_replayable():
    expected = {
        "alpha_cluster_recurrence": {"Li-7": True, "C-12": True},
        "n_z_ratio_commensurability": {"Li-7": False, "C-12": True},
        "ground_state_spin_parity_symmetry": {"Li-7": False, "C-12": True},
        "binding_per_nucleon_commensurability": {"Li-7": False, "C-12": True},
        "proton_neutron_inversion_symmetry": {"Li-7": False, "C-12": True},
    }
    for candidate in m.CANDIDATES:
        assert m.recurrence_test(candidate) == expected[candidate.candidate_id]
        # Receipts are deterministic across reconstruction.
        record = {
            "candidate_id": candidate.candidate_id,
            "relation_kind": candidate.relation_kind,
            "participants": list(candidate.participants),
            "ordered_parameter": candidate.ordered_parameter,
            "recurrence_mapping": candidate.recurrence_mapping,
            "equivalence_condition": candidate.equivalence_condition,
            "information_loss": candidate.information_loss,
            "physical_provenance": list(candidate.physical_provenance),
            "status": candidate.status,
        }
        assert m.harmonic_receipt(record) == candidate.receipt
    receipts = {c.receipt for c in m.CANDIDATES}
    assert len(receipts) == len(m.CANDIDATES)


def test_all_results_cross_domain_hypothesis():
    for candidate in m.CANDIDATES:
        assert candidate.status == "CROSS-DOMAIN-HYPOTHESIS"
    assert m.NUCLIDE_FACTS["He-4"]["J_pi"] == "0+"
    assert m.NUCLIDE_FACTS["C-12"]["J_pi"] == "0+"
    assert m.NUCLIDE_FACTS["Li-7"]["J_pi"] == "3/2-"
