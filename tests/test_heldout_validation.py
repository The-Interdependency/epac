"""Usage: python -m pytest -q tests/test_heldout_validation.py.

Synthetic evidence exercises validation integrity without assigning chemistry standing.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import epac_heldout_validation as heldout_validation
from epac_heldout_validation import (
    compare_after_freeze,
    freeze_predictions,
    freeze_validation_plan,
    load_oracle,
    load_packaged_oracle,
    load_prediction_commitment,
    load_validation_receipt,
    load_validation_plan,
    verify_commitment,
)


# === CHECKS ===
# id: check_freeze_is_deterministic_oracle_free_and_plan_bound
#   proves: heldout_selection_boundary_frozen_before_predictions, heldout_commitment_persistence_and_identity
#   call: self::test_freeze_is_deterministic_oracle_free_and_plan_bound
#   mutates: none
#   cleanup: none
#
# id: check_plan_rejects_duplicate_ids_and_oracle_fields
#   proves: heldout_selection_boundary_frozen_before_predictions
#   call: self::test_plan_rejects_duplicate_ids_and_oracle_fields
#   mutates: none
#   cleanup: none
#
# id: check_plan_rejects_oracle_fields_hidden_in_comparator_rules
#   proves: heldout_selection_boundary_frozen_before_predictions
#   call: self::test_plan_rejects_oracle_fields_hidden_in_comparator_rules
#   mutates: none
#   cleanup: none
#
# id: check_prediction_cannot_escape_frozen_case_inventory
#   proves: heldout_selection_boundary_frozen_before_predictions
#   call: self::test_prediction_cannot_escape_frozen_case_inventory
#   mutates: none
#   cleanup: none
#
# id: check_prediction_commitment_rejects_non_json_values_before_hashing
#   proves: heldout_commitment_persistence_and_identity
#   call: self::test_prediction_commitment_rejects_non_json_values_before_hashing
#   mutates: none
#   cleanup: none
#
# id: check_domain_is_identifier_shaped_and_revalidated
#   proves: heldout_selection_boundary_frozen_before_predictions
#   call: self::test_domain_is_identifier_shaped_and_revalidated
#   mutates: none
#   cleanup: none
#
# id: check_programmatic_oracle_rejects_non_json_values_before_evidence_hashing
#   proves: heldout_oracle_evidence_integrity
#   call: self::test_programmatic_oracle_rejects_non_json_values_before_evidence_hashing
#   mutates: none
#   cleanup: none
#
# id: check_tampered_prediction_cannot_be_compared
#   proves: heldout_commitment_persistence_and_identity
#   call: self::test_tampered_prediction_cannot_be_compared
#   mutates: none
#   cleanup: none
#
# id: check_commitment_revalidates_nonempty_source_identity_even_with_matching_digest
#   proves: heldout_commitment_persistence_and_identity
#   call: self::test_commitment_revalidates_nonempty_source_identity_even_with_matching_digest
#   mutates: none
#   cleanup: none
#
# id: check_case_inventory_and_comparator_are_bound_before_comparison
#   proves: heldout_selection_boundary_frozen_before_predictions
#   call: self::test_case_inventory_and_comparator_are_bound_before_comparison
#   mutates: none
#   cleanup: none
#
# id: check_external_commitment_rejects_predictions_outside_verified_plan
#   proves: heldout_selection_boundary_frozen_before_predictions, heldout_commitment_persistence_and_identity
#   call: self::test_external_commitment_rejects_predictions_outside_verified_plan
#   mutates: none
#   cleanup: none
#
# id: check_exact_comparison_preserves_arbitrary_size_integers
#   proves: heldout_comparison_tri_state_semantics
#   call: self::test_exact_comparison_preserves_arbitrary_size_integers
#   mutates: none
#   cleanup: none
#
# id: check_comparison_classifies_only_after_freeze
#   proves: heldout_comparison_tri_state_semantics, heldout_receipt_evidence_binding
#   call: self::test_comparison_classifies_only_after_freeze
#   mutates: none
#   cleanup: none
#
# id: check_absent_expected_null_provenance_and_missing_prediction_are_unresolved
#   proves: heldout_comparison_tri_state_semantics, heldout_oracle_evidence_integrity
#   call: self::test_absent_expected_null_provenance_and_missing_prediction_are_unresolved
#   mutates: none
#   cleanup: none
#
# id: check_exact_comparison_is_json_type_safe_including_nested_values
#   proves: heldout_comparison_tri_state_semantics
#   call: self::test_exact_comparison_is_json_type_safe_including_nested_values
#   mutates: none
#   cleanup: none
#
# id: check_duplicate_oracle_case_ids_are_rejected_before_scoring
#   proves: heldout_oracle_evidence_integrity
#   call: self::test_duplicate_oracle_case_ids_are_rejected_before_scoring
#   mutates: none
#   cleanup: none
#
# id: check_nonfinite_numeric_operands_or_tolerance_are_unresolved
#   proves: heldout_comparison_tri_state_semantics
#   call: self::test_nonfinite_numeric_operands_or_tolerance_are_unresolved
#   mutates: none
#   cleanup: none
#
# id: check_numeric_tolerance_preserves_large_integer_distinctions
#   proves: heldout_comparison_tri_state_semantics
#   call: self::test_numeric_tolerance_preserves_large_integer_distinctions
#   mutates: none
#   cleanup: none
#
# id: check_blank_provenance_identity_is_unresolved
#   proves: heldout_oracle_evidence_integrity
#   call: self::test_blank_provenance_identity_is_unresolved
#   mutates: none
#   cleanup: none
#
# id: check_receipt_and_commitment_detach_mutable_evidence_inputs
#   proves: heldout_receipt_evidence_binding
#   call: self::test_receipt_and_commitment_detach_mutable_evidence_inputs
#   mutates: none
#   cleanup: none
#
# id: check_load_oracle_rejects_duplicate_json_object_keys
#   proves: heldout_oracle_loading_is_unambiguous, heldout_oracle_evidence_integrity
#   call: self::test_load_oracle_rejects_duplicate_json_object_keys
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_persisted_commitment_loaders_reject_duplicate_keys_at_every_depth
#   proves: heldout_persisted_commitments_are_unambiguous
#   call: self::test_persisted_commitment_loaders_reject_duplicate_keys_at_every_depth
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_persisted_commitment_loaders_verify_envelopes_and_plan_binding
#   proves: heldout_persisted_commitments_are_unambiguous, heldout_commitment_persistence_and_identity, heldout_selection_boundary_frozen_before_predictions
#   call: self::test_persisted_commitment_loaders_verify_envelopes_and_plan_binding
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_receipt_loader_preserves_verified_evidence_and_unresolved_results
#   proves: heldout_persisted_receipts_preserve_evidence, heldout_comparison_tri_state_semantics
#   call: self::test_receipt_loader_preserves_verified_evidence_and_unresolved_results
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_receipt_loader_rejects_ambiguous_or_tampered_evidence
#   proves: heldout_persisted_receipts_preserve_evidence
#   call: self::test_receipt_loader_rejects_ambiguous_or_tampered_evidence
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_evidence_loaders_reject_decimal_value_loss
#   proves: heldout_json_numbers_preserve_decimal_value
#   call: self::test_evidence_loaders_reject_decimal_value_loss
#   mutates: filesystem
#   cleanup: tempdir_teardown
#
# id: check_packaged_oracle_loader_works_from_checkout_or_install_and_prefers_checkout
#   proves: heldout_oracle_loading_is_unambiguous
#   call: self::test_packaged_oracle_loader_works_from_checkout_or_install_and_prefers_checkout
#   mutates: none
#   cleanup: none
#
# id: check_set_equality_does_not_alias_boolean_and_numeric_values
#   proves: heldout_comparison_tri_state_semantics
#   call: self::test_set_equality_does_not_alias_boolean_and_numeric_values
#   mutates: none
#   cleanup: none
# === END CHECKS ===

def plan_cases():
    return [
        {"id": "element:H:valence", "domain": "valence", "comparison": {"kind": "exact"}},
        {"id": "element:O:oxidation", "domain": "oxidation-state", "comparison": {"kind": "set-equality"}},
        {"id": "isotope:H-1:mass", "domain": "isotope",
         "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": 0.000001}},
    ]


def oracle():
    return {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [
            {"id": "element:H:valence", "domain": "valence", "expected": 1,
             "comparison": {"kind": "exact"},
             "provenance": {"authority": "fixture-authority", "locator": "fixture:H"}},
            {"id": "element:O:oxidation", "domain": "oxidation-state", "expected": [-2],
             "comparison": {"kind": "set-equality"},
             "provenance": {"authority": "fixture-authority", "locator": "fixture:O"}},
            {"id": "isotope:H-1:mass", "domain": "isotope", "expected": 1.007825,
             "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": 0.000001},
             "provenance": {"authority": "fixture-authority", "locator": "fixture:H-1"}},
        ],
    }


def frozen(predictions):
    plan = freeze_validation_plan(plan_cases())
    commitment = freeze_predictions(predictions, source_identity="epac@test", validation_plan=plan)
    return plan, commitment


def _digest_envelope(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def test_freeze_is_deterministic_oracle_free_and_plan_bound():
    plan_a = freeze_validation_plan(list(reversed(plan_cases())))
    plan_b = freeze_validation_plan(plan_cases())
    assert plan_a == plan_b

    predictions_a = {"element:H:valence": 1, "element:O:oxidation": [-2, 2]}
    predictions_b = {"element:O:oxidation": [-2, 2], "element:H:valence": 1}
    frozen_a = freeze_predictions(predictions_a, source_identity="epac@test", validation_plan=plan_a)
    frozen_b = freeze_predictions(predictions_b, source_identity="epac@test", validation_plan=plan_b)

    assert frozen_a == frozen_b
    assert frozen_a["validation_plan_sha256"] == plan_a["plan_sha256"]
    assert "expected" not in repr(plan_a).lower()
    assert "provenance" not in repr(plan_a).lower()
    verify_commitment(frozen_a)


def test_plan_rejects_duplicate_ids_and_oracle_fields():
    with pytest.raises(ValueError, match="duplicate validation plan"):
        freeze_validation_plan([{"id": "x"}, {"id": "x"}])
    with pytest.raises(ValueError, match="cannot contain expected values"):
        freeze_validation_plan([{"id": "x", "expected": 1}])


def test_plan_rejects_oracle_fields_hidden_in_comparator_rules():
    invalid_rules = [
        {"kind": "exact", "expected": 7},
        {"kind": "set-equality", "expected": [7]},
        {"kind": "numeric-tolerance", "absolute_tolerance": 0, "expected": 7},
        {"kind": "future-comparator", "provenance": {"authority": "oracle"}},
        {"kind": "exact", "absolute_tolerance": 7},
    ]
    invalid_rules.extend(
        {"kind": "numeric-tolerance", "absolute_tolerance": value}
        for value in ({"expected": 7}, [{"provenance": "oracle"}], "expected=7", True)
    )
    for comparison in invalid_rules:
        error = "unexpected comparator fields|absolute_tolerance must be"
        with pytest.raises(ValueError, match=error):
            freeze_validation_plan([{"id": "x", "comparison": comparison}])

        plan = freeze_validation_plan([{"id": "x"}])
        forged = deepcopy(plan)
        forged["cases"][0]["comparison"] = comparison
        unsigned = {k: forged[k] for k in ("schema", "version", "cases")}
        forged["plan_sha256"] = _digest_envelope(unsigned)
        with pytest.raises(ValueError, match=error):
            freeze_predictions({"x": 1}, source_identity="epac@test", validation_plan=forged)

        commitment = freeze_predictions({"x": 1}, source_identity="epac@test", validation_plan=plan)
        heldout = {
            "schema": "epac.heldout-chemistry-oracle", "version": "v1",
            "cases": [{"id": "x", "comparison": comparison, "expected": 1,
                       "provenance": {"authority": "fixture", "locator": "x"}}],
        }
        with pytest.raises(ValueError, match=error):
            compare_after_freeze(commitment, heldout, validation_plan=plan)


def test_prediction_cannot_escape_frozen_case_inventory():
    plan = freeze_validation_plan([{"id": "x", "comparison": {"kind": "exact"}}])
    with pytest.raises(ValueError, match="absent from frozen validation plan"):
        freeze_predictions({"y": 1}, source_identity="epac@test", validation_plan=plan)


def test_prediction_commitment_rejects_non_json_values_before_hashing():
    plan = freeze_validation_plan([
        {"id": "x", "domain": "fixture", "comparison": {"kind": "exact"}}
    ])

    with pytest.raises(ValueError, match="JSON-shaped"):
        freeze_predictions(
            {"x": (1,)},
            source_identity="epac@test",
            validation_plan=plan,
        )
    with pytest.raises(ValueError, match="JSON-shaped"):
        freeze_predictions(
            {"x": [{"nested": (1,)}]},
            source_identity="epac@test",
            validation_plan=plan,
        )

    commitment = freeze_predictions(
        {"x": [1]},
        source_identity="epac@test",
        validation_plan=plan,
    )
    forged = deepcopy(commitment)
    forged["predictions"]["x"] = (1,)
    unsigned = {
        k: forged[k]
        for k in ("schema", "version", "source_identity", "validation_plan_sha256", "predictions")
    }
    # Python's JSON encoder gives tuple/list the same bytes; verification must
    # still reject the in-memory tuple representation before accepting the SHA.
    assert _digest_envelope(unsigned) == commitment["commitment_sha256"]
    forged["commitment_sha256"] = _digest_envelope(unsigned)
    with pytest.raises(ValueError, match="JSON-shaped"):
        verify_commitment(forged)

    round_tripped = json.loads(json.dumps(commitment))
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "x",
            "domain": "fixture",
            "comparison": {"kind": "exact"},
            "expected": [1],
            "provenance": {"authority": "fixture", "locator": "json-stability"},
        }],
    }
    before = compare_after_freeze(commitment, heldout, validation_plan=plan)
    after = compare_after_freeze(round_tripped, heldout, validation_plan=plan)
    assert before == after
    assert before["counts"] == {"SURVIVED": 1, "FALSIFIED": 0, "UNRESOLVED": 0}


def test_domain_is_identifier_shaped_and_revalidated():
    invalid_domains = (
        {"expected": 7},
        ["expected", 7],
        7,
        "   ",
        " padded ",
    )
    for domain in invalid_domains:
        with pytest.raises(ValueError, match="domain must be null or a nonempty canonical string"):
            freeze_validation_plan([
                {"id": "x", "domain": domain, "comparison": {"kind": "exact"}}
            ])

    plan = freeze_validation_plan([
        {"id": "x", "domain": "fixture", "comparison": {"kind": "exact"}}
    ])
    forged = deepcopy(plan)
    forged["cases"][0]["domain"] = {"expected": 7}
    unsigned = {k: forged[k] for k in ("schema", "version", "cases")}
    forged["plan_sha256"] = _digest_envelope(unsigned)
    with pytest.raises(ValueError, match="domain must be null or a nonempty canonical string"):
        freeze_predictions(
            {"x": 1},
            source_identity="epac@test",
            validation_plan=forged,
        )

    commitment = freeze_predictions(
        {"x": 1},
        source_identity="epac@test",
        validation_plan=plan,
    )
    oracle_with_structured_domain = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "x",
            "domain": {"expected": 7},
            "comparison": {"kind": "exact"},
            "expected": 1,
            "provenance": {"authority": "fixture", "locator": "domain"},
        }],
    }
    with pytest.raises(ValueError, match="domain must be null or a nonempty canonical string"):
        compare_after_freeze(
            commitment,
            oracle_with_structured_domain,
            validation_plan=plan,
        )


def test_programmatic_oracle_rejects_non_json_values_before_evidence_hashing():
    plan = freeze_validation_plan([
        {"id": "x", "domain": "fixture", "comparison": {"kind": "exact"}}
    ])
    commitment = freeze_predictions(
        {"x": [1]},
        source_identity="epac@test",
        validation_plan=plan,
    )
    oracle_with_tuple = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "x",
            "domain": "fixture",
            "comparison": {"kind": "exact"},
            "expected": (1,),
            "provenance": {"authority": "fixture", "locator": "tuple"},
        }],
    }
    with pytest.raises(ValueError, match="JSON-shaped"):
        compare_after_freeze(
            commitment,
            oracle_with_tuple,
            validation_plan=plan,
        )


def test_tampered_prediction_cannot_be_compared():
    plan, commitment = frozen({"element:H:valence": 1})
    tampered = deepcopy(commitment)
    tampered["predictions"]["element:H:valence"] = 2
    with pytest.raises(ValueError, match="digest mismatch"):
        compare_after_freeze(tampered, oracle(), validation_plan=plan)


def test_commitment_revalidates_nonempty_source_identity_even_with_matching_digest():
    plan, commitment = frozen({"element:H:valence": 1})
    for source_identity in ("", " \t", "hmmm", " HMMM ", "\thMmM\n"):
        with pytest.raises(ValueError, match="source_identity"):
            freeze_predictions({"element:H:valence": 1}, source_identity=source_identity, validation_plan=plan)
        forged = deepcopy(commitment)
        forged["source_identity"] = source_identity
        unsigned = {
            k: forged[k]
            for k in ("schema", "version", "source_identity", "validation_plan_sha256", "predictions")
        }
        forged["commitment_sha256"] = _digest_envelope(unsigned)
        with pytest.raises(ValueError, match="source_identity"):
            verify_commitment(forged)
        with pytest.raises(ValueError, match="source_identity"):
            compare_after_freeze(forged, oracle(), validation_plan=plan)


def test_case_inventory_and_comparator_are_bound_before_comparison():
    plan, commitment = frozen({"element:H:valence": 1})

    missing_case = oracle()
    missing_case["cases"].pop()
    with pytest.raises(ValueError, match="case inventory"):
        compare_after_freeze(commitment, missing_case, validation_plan=plan)

    changed_rule = oracle()
    changed_rule["cases"][2]["comparison"]["absolute_tolerance"] = 1.0
    with pytest.raises(ValueError, match="comparator"):
        compare_after_freeze(commitment, changed_rule, validation_plan=plan)


def test_external_commitment_rejects_predictions_outside_verified_plan():
    plan = freeze_validation_plan([
        {"id": "x", "domain": "fixture", "comparison": {"kind": "exact"}}
    ])
    commitment = freeze_predictions(
        {"x": 1},
        source_identity="epac@test",
        validation_plan=plan,
    )
    forged = deepcopy(commitment)
    forged["predictions"]["outside"] = 99
    unsigned = {
        k: forged[k]
        for k in ("schema", "version", "source_identity", "validation_plan_sha256", "predictions")
    }
    forged["commitment_sha256"] = _digest_envelope(unsigned)
    verify_commitment(forged)
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "x",
            "domain": "fixture",
            "comparison": {"kind": "exact"},
            "expected": 1,
            "provenance": {"authority": "fixture", "locator": "membership"},
        }],
    }
    with pytest.raises(ValueError, match="absent from frozen validation plan"):
        compare_after_freeze(forged, heldout, validation_plan=plan)


def test_exact_comparison_preserves_arbitrary_size_integers():
    huge = 10 ** 400
    plan = freeze_validation_plan([
        {"id": "same", "domain": "fixture", "comparison": {"kind": "exact"}},
        {"id": "different", "domain": "fixture", "comparison": {"kind": "exact"}},
    ])
    commitment = freeze_predictions(
        {"same": huge, "different": huge + 1},
        source_identity="epac@test",
        validation_plan=plan,
    )
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [
            {
                "id": "same",
                "domain": "fixture",
                "comparison": {"kind": "exact"},
                "expected": huge,
                "provenance": {"authority": "fixture", "locator": "huge-same"},
            },
            {
                "id": "different",
                "domain": "fixture",
                "comparison": {"kind": "exact"},
                "expected": huge,
                "provenance": {"authority": "fixture", "locator": "huge-different"},
            },
        ],
    }
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 1, "FALSIFIED": 1, "UNRESOLVED": 0}


def test_comparison_classifies_only_after_freeze():
    plan, commitment = frozen({
        "element:H:valence": 1,
        "element:O:oxidation": [-2, 2],
        "isotope:H-1:mass": 1.0078251,
    })
    receipt = compare_after_freeze(commitment, oracle(), validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 2, "FALSIFIED": 1, "UNRESOLVED": 0}
    assert receipt["validation_plan_sha256"] == plan["plan_sha256"]
    assert receipt["prediction_commitment_sha256"] == commitment["commitment_sha256"]
    assert len(receipt["oracle_sha256"]) == 64
    assert len(receipt["receipt_sha256"]) == 64


def test_absent_expected_null_provenance_and_missing_prediction_are_unresolved():
    cases = [
        {"id": "missing:expected", "domain": "fixture", "comparison": {"kind": "exact"}},
        {"id": "null:provenance", "domain": "fixture", "comparison": {"kind": "exact"}},
        {"id": "missing:prediction", "domain": "fixture", "comparison": {"kind": "exact"}},
    ]
    plan = freeze_validation_plan(cases)
    commitment = freeze_predictions(
        {"missing:expected": None, "null:provenance": 1},
        source_identity="epac@test",
        validation_plan=plan,
    )
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [
            {"id": "missing:expected", "domain": "fixture", "comparison": {"kind": "exact"},
             "provenance": {"authority": "fixture", "locator": "missing"}},
            {"id": "null:provenance", "domain": "fixture", "comparison": {"kind": "exact"},
             "expected": 1, "provenance": None},
            {"id": "missing:prediction", "domain": "fixture", "comparison": {"kind": "exact"},
             "expected": 1,
             "provenance": {"authority": "fixture", "locator": "missing-prediction"}},
        ],
    }
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 0, "FALSIFIED": 0, "UNRESOLVED": 3}
    reasons = {row["id"]: row["reason"] for row in receipt["results"]}
    assert reasons["missing:expected"] == "missing expected value"
    assert reasons["null:provenance"] == "missing provenance identity"
    assert reasons["missing:prediction"] == "no frozen prediction"


def test_exact_comparison_is_json_type_safe_including_nested_values():
    plan = freeze_validation_plan([
        {"id": "scalar", "comparison": {"kind": "exact"}},
        {"id": "nested", "comparison": {"kind": "exact"}},
    ])
    commitment = freeze_predictions(
        {"scalar": True, "nested": [True]},
        source_identity="epac@test",
        validation_plan=plan,
    )
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [
            {"id": "scalar", "domain": None, "comparison": {"kind": "exact"}, "expected": 1,
             "provenance": {"authority": "fixture", "locator": "scalar"}},
            {"id": "nested", "domain": None, "comparison": {"kind": "exact"}, "expected": [1],
             "provenance": {"authority": "fixture", "locator": "nested"}},
        ],
    }
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 0, "FALSIFIED": 2, "UNRESOLVED": 0}


def test_duplicate_oracle_case_ids_are_rejected_before_scoring():
    plan = freeze_validation_plan([{"id": "x", "comparison": {"kind": "exact"}}])
    commitment = freeze_predictions({"x": 1}, source_identity="epac@test", validation_plan=plan)
    duplicate = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [
            {"id": "x", "domain": None, "comparison": {"kind": "exact"}, "expected": 1,
             "provenance": {"authority": "fixture", "locator": "x1"}},
            {"id": "x", "domain": None, "comparison": {"kind": "exact"}, "expected": 2,
             "provenance": {"authority": "fixture", "locator": "x2"}},
        ],
    }
    with pytest.raises(ValueError, match="duplicate oracle case id"):
        compare_after_freeze(commitment, duplicate, validation_plan=plan)


def test_nonfinite_numeric_operands_or_tolerance_are_unresolved():
    cases = [
        (1.0, math.inf, 0.1),
        (math.inf, 1.0, 0.1),
        (1.0, 1.0, math.inf),
        (1.0, math.nan, 0.1),
        (1.0, 1.0, math.nan),
    ]
    for expected, predicted, tolerance in cases:
        plan = freeze_validation_plan([
            {"id": "x", "domain": "fixture",
             "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": tolerance}}
        ])
        commitment = freeze_predictions(
            {"x": predicted},
            source_identity="epac@test",
            validation_plan=plan,
        )
        heldout = {
            "schema": "epac.heldout-chemistry-oracle",
            "version": "v1",
            "cases": [{
                "id": "x",
                "domain": "fixture",
                "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": tolerance},
                "expected": expected,
                "provenance": {"authority": "fixture", "locator": "x"},
            }],
        }
        receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
        assert receipt["counts"] == {"SURVIVED": 0, "FALSIFIED": 0, "UNRESOLVED": 1}


def test_numeric_tolerance_preserves_large_integer_distinctions():
    plan = freeze_validation_plan([
        {"id": "x", "domain": "fixture",
         "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": 0}}
    ])
    commitment = freeze_predictions(
        {"x": 9007199254740993},
        source_identity="epac@test",
        validation_plan=plan,
    )
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "x",
            "domain": "fixture",
            "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": 0},
            "expected": 9007199254740992,
            "provenance": {"authority": "fixture", "locator": "large-int"},
        }],
    }
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 0, "FALSIFIED": 1, "UNRESOLVED": 0}


def test_blank_provenance_identity_is_unresolved():
    plan = freeze_validation_plan([
        {"id": "x", "domain": "fixture", "comparison": {"kind": "exact"}}
    ])
    commitment = freeze_predictions({"x": 1}, source_identity="epac@test", validation_plan=plan)
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "x",
            "domain": "fixture",
            "comparison": {"kind": "exact"},
            "expected": 1,
            "provenance": {"authority": "   ", "locator": "\t"},
        }],
    }
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 0, "FALSIFIED": 0, "UNRESOLVED": 1}
    assert receipt["results"][0]["reason"] == "missing provenance identity"
    for field in ("authority", "locator"):
        for unknown in ("hmmm", " HMMM ", "\thmmm\n"):
            heldout["cases"][0]["provenance"] = {"authority": "fixture", "locator": "x"}
            heldout["cases"][0]["provenance"][field] = unknown
            receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
            assert receipt["counts"] == {"SURVIVED": 0, "FALSIFIED": 0, "UNRESOLVED": 1}
            assert receipt["results"][0]["reason"] == "missing provenance identity"


def test_receipt_and_commitment_detach_mutable_evidence_inputs():
    predictions = {
        "element:H:valence": 1,
        "element:O:oxidation": [-2, 2],
        "isotope:H-1:mass": 1.0078251,
    }
    plan = freeze_validation_plan(plan_cases())
    commitment = freeze_predictions(predictions, source_identity="epac@test", validation_plan=plan)
    predictions["element:O:oxidation"].append(99)
    verify_commitment(commitment)

    heldout = oracle()
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    preserved = deepcopy(receipt)
    heldout["cases"][1]["expected"].append(99)
    heldout["cases"][1]["provenance"]["locator"] = "mutated"
    commitment["predictions"]["element:O:oxidation"].append(88)

    assert receipt == preserved
    assert receipt["receipt_sha256"] == preserved["receipt_sha256"]


def test_load_oracle_rejects_duplicate_json_object_keys():
    payload = (
        '{"schema":"epac.heldout-chemistry-oracle","version":"v1","cases":'
        '[{"id":"x","expected":1,"expected":2}]}'
    )
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "oracle.json"
        path.write_text(payload, encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate JSON key"):
            load_oracle(path)


def test_persisted_commitment_loaders_reject_duplicate_keys_at_every_depth():
    plan = freeze_validation_plan([{"id": "x"}])
    commitment = freeze_predictions(
        {"x": {"nested": [1]}}, source_identity="epac@test", validation_plan=plan
    )
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.json"
        for envelope, loader in (
            (plan, load_validation_plan),
            (commitment, lambda path: load_prediction_commitment(path, validation_plan=plan)),
        ):
            encoded = json.dumps(envelope)
            # Every root field, including cases/predictions and their digests:
            # last-key-wins would restore the valid envelope in each attack.
            attacks = [
                "{" + json.dumps(key) + ":null," + encoded[1:]
                for key in envelope
            ]
            if envelope is plan:
                attacks += [
                    encoded.replace('"id": "x"', '"id":"other","id": "x"'),
                    encoded.replace('"kind": "exact"', '"kind":"other","kind": "exact"'),
                    encoded.replace('"kind": "exact"', '"k\\u0069nd":"other","kind": "exact"'),
                ]
            else:
                attacks += [
                    encoded.replace('"x": {', '"x":null,"x": {'),
                    encoded.replace('"nested": [1]', '"nested":[99],"nested": [1]'),
                ]
            for payload in attacks:
                assert json.loads(payload) == envelope
                path.write_text(payload, encoding="utf-8")
                with pytest.raises(ValueError, match="duplicate JSON key"):
                    loader(path)


def test_persisted_commitment_loaders_verify_envelopes_and_plan_binding():
    plan, commitment = frozen({"element:H:valence": 1})
    with TemporaryDirectory() as tmp:
        plan_path = Path(tmp) / "plan.json"
        prediction_path = Path(tmp) / "predictions.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        prediction_path.write_text(json.dumps(commitment), encoding="utf-8")
        reloaded_plan = load_validation_plan(plan_path)
        reloaded_commitment = load_prediction_commitment(
            prediction_path, validation_plan=reloaded_plan
        )
        assert reloaded_plan == plan
        assert reloaded_commitment == commitment
        before = compare_after_freeze(commitment, oracle(), validation_plan=plan)
        after = compare_after_freeze(reloaded_commitment, oracle(), validation_plan=reloaded_plan)
        assert before == after
        assert after["counts"] == {"SURVIVED": 1, "FALSIFIED": 0, "UNRESOLVED": 2}

        for envelope, loader in (
            (plan, load_validation_plan),
            (commitment, lambda path: load_prediction_commitment(path, validation_plan=plan)),
        ):
            path = Path(tmp) / "invalid.json"
            for value in (None, [], 7, "not an object", {}):
                path.write_text(json.dumps(value), encoding="utf-8")
                with pytest.raises(ValueError):
                    loader(path)
            for key in envelope:
                forged = deepcopy(envelope)
                forged[key] = "tampered"
                path.write_text(json.dumps(forged), encoding="utf-8")
                with pytest.raises(ValueError):
                    loader(path)

        other_plan = freeze_validation_plan([{"id": "other"}])
        with pytest.raises(ValueError, match="different validation plan"):
            load_prediction_commitment(prediction_path, validation_plan=other_plan)

        forged = deepcopy(commitment)
        forged["predictions"]["outside"] = 99
        forged["commitment_sha256"] = _digest_envelope({
            key: value for key, value in forged.items() if key != "commitment_sha256"
        })
        prediction_path.write_text(json.dumps(forged), encoding="utf-8")
        with pytest.raises(ValueError, match="absent from frozen validation plan"):
            load_prediction_commitment(prediction_path, validation_plan=plan)

        for source_identity in ("hmmm", " HMMM ", "\thMmM\n"):
            forged = deepcopy(commitment)
            forged["source_identity"] = source_identity
            forged["commitment_sha256"] = _digest_envelope({
                key: value for key, value in forged.items() if key != "commitment_sha256"
            })
            prediction_path.write_text(json.dumps(forged), encoding="utf-8")
            with pytest.raises(ValueError, match="source_identity"):
                load_prediction_commitment(prediction_path, validation_plan=plan)

        forged_plan = deepcopy(plan)
        forged_plan["cases"][0]["comparison"]["expected"] = 7
        forged_plan["plan_sha256"] = _digest_envelope({
            key: value for key, value in forged_plan.items() if key != "plan_sha256"
        })
        plan_path.write_text(json.dumps(forged_plan), encoding="utf-8")
        with pytest.raises(ValueError, match="unexpected comparator fields"):
            load_validation_plan(plan_path)
        with pytest.raises(ValueError, match="unexpected comparator fields"):
            load_prediction_commitment(prediction_path, validation_plan=forged_plan)


def test_receipt_loader_preserves_verified_evidence_and_unresolved_results():
    cases = [
        {"id": name, "comparison": {"kind": "exact"}}
        for name in ("same", "different", "nonfinite", "missing_expected", "missing_prediction", "missing_provenance")
    ] + [{"id": "unsupported", "comparison": {"kind": "future"}}]
    plan = freeze_validation_plan(cases)
    commitment = freeze_predictions(
        {"same": 1, "different": 2, "nonfinite": math.inf, "missing_expected": None,
         "missing_provenance": 1, "unsupported": 1},
        source_identity="epac@test", validation_plan=plan,
    )
    heldout = {
        "schema": "epac.heldout-chemistry-oracle", "version": "v1",
        "cases": [dict(case, expected=1, provenance={"authority": "fixture", "locator": case["id"]}) for case in cases],
    }
    del heldout["cases"][3]["expected"]
    heldout["cases"][5]["provenance"] = {"authority": "hmmm", "locator": "x"}
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 1, "FALSIFIED": 1, "UNRESOLVED": 5}
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        preserved = load_validation_receipt(path)
        assert json.dumps(preserved, sort_keys=True) == json.dumps(receipt, sort_keys=True)
        empty_plan = freeze_validation_plan([])
        empty_commitment = freeze_predictions({}, source_identity="epac@test", validation_plan=empty_plan)
        empty = compare_after_freeze(empty_commitment, dict(heldout, cases=[]), validation_plan=empty_plan)
        path.write_text(json.dumps(empty), encoding="utf-8")
        assert load_validation_receipt(path) == empty


def test_receipt_loader_rejects_ambiguous_or_tampered_evidence():
    plan, commitment = frozen({"element:H:valence": 1})
    receipt = compare_after_freeze(commitment, oracle(), validation_plan=plan)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "receipt.json"
        encoded = json.dumps(receipt)
        attacks = ["{" + json.dumps(key) + ":null," + encoded[1:] for key in receipt]
        attacks += [
            encoded.replace('"status": "SURVIVED"', '"status":"FALSIFIED","status": "SURVIVED"'),
            encoded.replace('"SURVIVED": 1', '"SURVIVED":0,"SURVIVED": 1'),
            encoded.replace('"SURVIVED": 1', '"SURVIVED":1,"SURVIVED": 1'),
        ]
        for payload in attacks:
            assert json.loads(payload) == receipt
            path.write_text(payload, encoding="utf-8")
            with pytest.raises(ValueError, match="duplicate JSON key"):
                load_validation_receipt(path)

        for key in receipt:
            forged = deepcopy(receipt)
            del forged[key]
            path.write_text(json.dumps(forged), encoding="utf-8")
            with pytest.raises(ValueError):
                load_validation_receipt(path)

        def rejected(forged, *, rehash=False):
            if rehash:
                forged["receipt_sha256"] = _digest_envelope({
                    key: value for key, value in forged.items() if key != "receipt_sha256"
                })
            path.write_text(json.dumps(forged), encoding="utf-8")
            with pytest.raises(ValueError):
                load_validation_receipt(path)

        for value in (None, [], 7, "not an object"):
            rejected(value)
        # Keep every shape otherwise valid to witness digest verification itself.
        forged = deepcopy(receipt)
        forged["results"][0]["provenance"]["locator"] = "altered"
        rejected(forged)
        for field, value in (
            ("schema", "other"), ("version", "v2"), ("oracle_sha256", "g" * 64),
            ("results", {}), ("counts", {"SURVIVED": True, "FALSIFIED": 0, "UNRESOLVED": 2}),
            ("counts", {"SURVIVED": 0, "FALSIFIED": 0, "UNRESOLVED": 2}),
        ):
            forged = deepcopy(receipt)
            forged[field] = value
            rejected(forged, rehash=True)
        for field, value in (
            ("status", "UNREVIEWED"), ("domain", {"expected": 1}),
            ("provenance", {"authority": "hmmm", "locator": "x"}),
            ("comparison", {"kind": "exact", "expected": 1}),
            ("expected", 99), ("unexpected", "oracle"),
        ):
            forged = deepcopy(receipt)
            forged["results"][0][field] = value
            rejected(forged, rehash=True)
        forged = deepcopy(receipt)
        forged["results"].append(deepcopy(forged["results"][0]))
        forged["counts"]["SURVIVED"] += 1
        rejected(forged, rehash=True)
        # Even consistent counts plus a new digest cannot legitimize a flipped status.
        forged = deepcopy(receipt)
        forged["results"][0]["status"] = "FALSIFIED"
        forged["counts"].update(SURVIVED=0, FALSIFIED=1)
        rejected(forged, rehash=True)
        forged = deepcopy(receipt)
        forged["results"][1]["reason"] = "invented reason"
        rejected(forged, rehash=True)


def test_evidence_loaders_reject_decimal_value_loss():
    plan = freeze_validation_plan([
        {"id": "x", "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": 0.5}}
    ])
    commitment = freeze_predictions({"x": 0.5}, source_identity="epac@test", validation_plan=plan)
    heldout = {
        "schema": "epac.heldout-chemistry-oracle", "version": "v1",
        "cases": [{"id": "x", "comparison": plan["cases"][0]["comparison"], "expected": 0.5,
                   "provenance": {"authority": "fixture", "locator": "x"}}],
    }
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.json"
        for envelope, loader in (
            (plan, load_validation_plan),
            (commitment, lambda path: load_prediction_commitment(path, validation_plan=plan)),
            (heldout, load_oracle),
            (receipt, load_validation_receipt),
        ):
            encoded = json.dumps(envelope)
            path.write_text(encoded, encoding="utf-8")
            assert loader(path) == envelope
            for number in ("9007199254740993.0", "0.50000000000000001", "1e-4000", "1e4000"):
                payload = encoded.replace("0.5", number)
                assert payload != encoded
                if number == "0.50000000000000001":
                    # Default parsing would silently accept the original digests.
                    assert json.loads(payload) == envelope
                path.write_text(payload, encoding="utf-8")
                with pytest.raises(ValueError, match="without rounding"):
                    loader(path)

        exact_plan = freeze_validation_plan([{"id": "x"}])
        exact_commitment = freeze_predictions({"x": 9007199254740992}, source_identity="epac@test", validation_plan=exact_plan)
        for literal in ("9007199254740992.0", "9007199254740993.0"):
            payload = ('{"schema":"epac.heldout-chemistry-oracle","version":"v1",'
                       '"cases":[{"id":"x","expected":' + literal + ','
                       '"provenance":{"authority":"fixture","locator":"x"}}]}')
            path.write_text(payload, encoding="utf-8")
            if literal == "9007199254740993.0":
                with pytest.raises(ValueError, match="without rounding"):
                    load_oracle(path)
            else:
                loaded = load_oracle(path)
                assert compare_after_freeze(exact_commitment, loaded, validation_plan=exact_plan)["counts"]["SURVIVED"] == 1

        for literal in ("0.1", "1.007825", "1e-6", "1.2300", "-0.0"):
            path.write_text('{"expected":' + literal + '}', encoding="utf-8")
            assert load_oracle(path)["expected"] == float(literal)


def test_packaged_oracle_loader_works_from_checkout_or_install_and_prefers_checkout():
    source_oracle = (
        Path(heldout_validation.__file__).resolve().parent
        / "data"
        / "heldout_chemistry_oracle.json"
    )
    if source_oracle.is_file():
        original_files = heldout_validation.files

        def unexpected_installed_lookup(*_args, **_kwargs):
            raise AssertionError("source checkout must be preferred over installed epac_data")

        heldout_validation.files = unexpected_installed_lookup
        try:
            packaged = load_packaged_oracle()
        finally:
            heldout_validation.files = original_files
        assert packaged == load_oracle(source_oracle)
    else:
        packaged = load_packaged_oracle()

    assert packaged["schema"] == "epac.heldout-chemistry-oracle"
    assert packaged["cases"] == []


def test_set_equality_does_not_alias_boolean_and_numeric_values():
    plan = freeze_validation_plan([{"id": "x", "comparison": {"kind": "set-equality"}}])
    commitment = freeze_predictions({"x": [True]}, source_identity="epac@test", validation_plan=plan)
    heldout = {
        "schema": "epac.heldout-chemistry-oracle",
        "version": "v1",
        "cases": [{
            "id": "x",
            "domain": None,
            "comparison": {"kind": "set-equality"},
            "expected": [1],
            "provenance": {"authority": "fixture", "locator": "x"},
        }],
    }
    receipt = compare_after_freeze(commitment, heldout, validation_plan=plan)
    assert receipt["counts"] == {"SURVIVED": 0, "FALSIFIED": 1, "UNRESOLVED": 0}
