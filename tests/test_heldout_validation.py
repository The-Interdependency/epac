from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math

import pytest

from epac_heldout_validation import (
    compare_after_freeze,
    freeze_predictions,
    freeze_validation_plan,
    load_packaged_oracle,
    verify_commitment,
)


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


def test_prediction_cannot_escape_frozen_case_inventory():
    plan = freeze_validation_plan([{"id": "x", "comparison": {"kind": "exact"}}])
    with pytest.raises(ValueError, match="absent from frozen validation plan"):
        freeze_predictions({"y": 1}, source_identity="epac@test", validation_plan=plan)


def test_tampered_prediction_cannot_be_compared():
    plan, commitment = frozen({"element:H:valence": 1})
    tampered = deepcopy(commitment)
    tampered["predictions"]["element:H:valence"] = 2
    with pytest.raises(ValueError, match="digest mismatch"):
        compare_after_freeze(tampered, oracle(), validation_plan=plan)


def test_commitment_revalidates_nonempty_source_identity_even_with_matching_digest():
    _, commitment = frozen({"element:H:valence": 1})
    forged = deepcopy(commitment)
    forged["source_identity"] = ""
    unsigned = {
        k: forged[k]
        for k in ("schema", "version", "source_identity", "validation_plan_sha256", "predictions")
    }
    forged["commitment_sha256"] = _digest_envelope(unsigned)
    with pytest.raises(ValueError, match="source_identity"):
        verify_commitment(forged)


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


@pytest.mark.parametrize(
    ("expected", "predicted", "tolerance"),
    [
        (1.0, math.inf, 0.1),
        (math.inf, 1.0, 0.1),
        (1.0, 1.0, math.inf),
        (1.0, math.nan, 0.1),
        (1.0, 1.0, math.nan),
    ],
)
def test_nonfinite_numeric_operands_or_tolerance_are_unresolved(expected, predicted, tolerance):
    plan = freeze_validation_plan([
        {"id": "x", "domain": "fixture",
         "comparison": {"kind": "numeric-tolerance", "absolute_tolerance": tolerance}}
    ])
    commitment = freeze_predictions({"x": predicted}, source_identity="epac@test", validation_plan=plan)
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


def test_packaged_oracle_loader_works_from_checkout_or_install():
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

