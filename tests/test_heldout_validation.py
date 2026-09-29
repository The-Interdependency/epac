from __future__ import annotations

from copy import deepcopy

import pytest

from epac_heldout_validation import compare_after_freeze, freeze_predictions, verify_commitment


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


def test_freeze_is_deterministic_and_oracle_free():
    a = freeze_predictions({"b": 2, "a": 1}, source_identity="epac@test")
    b = freeze_predictions({"a": 1, "b": 2}, source_identity="epac@test")
    assert a == b
    assert "oracle" not in repr(a).lower()
    verify_commitment(a)


def test_tampered_prediction_cannot_be_compared():
    frozen = freeze_predictions({"element:H:valence": 1}, source_identity="epac@test")
    tampered = deepcopy(frozen)
    tampered["predictions"]["element:H:valence"] = 2
    with pytest.raises(ValueError, match="digest mismatch"):
        compare_after_freeze(tampered, oracle())


def test_comparison_classifies_only_after_freeze():
    frozen = freeze_predictions({
        "element:H:valence": 1,
        "element:O:oxidation": [-2, 2],
        "isotope:H-1:mass": 1.0078251,
    }, source_identity="epac@test")
    receipt = compare_after_freeze(frozen, oracle())
    assert receipt["counts"] == {"SURVIVED": 2, "FALSIFIED": 1, "UNRESOLVED": 0}
    assert receipt["prediction_commitment_sha256"] == frozen["commitment_sha256"]
    assert len(receipt["oracle_sha256"]) == 64
    assert len(receipt["receipt_sha256"]) == 64


def test_missing_prediction_and_bad_provenance_are_unresolved():
    o = oracle()
    o["cases"].append({"id": "reaction:x", "expected": "y", "provenance": {}})
    frozen = freeze_predictions({}, source_identity="epac@test")
    receipt = compare_after_freeze(frozen, o)
    assert receipt["counts"]["UNRESOLVED"] == 4
