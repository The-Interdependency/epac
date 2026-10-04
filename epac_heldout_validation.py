"""Staged held-out chemistry validation for EPAC.

The construction side may create a prediction commitment without importing or
reading the oracle corpus.  Only the comparison phase accepts oracle facts.
This keeps empirical chemistry labels out of EPAC derivation while preventing post-hoc case or
comparator selection after predictions are revealed.

Usage: freeze and persist freeze_validation_plan first; derive EPAC predictions
externally; call and persist freeze_predictions; only then load the held-out
oracle and call compare_after_freeze. Reload persisted inputs with
load_validation_plan(path) and load_prediction_commitment(path, validation_plan=plan)
to reject ambiguous JSON before verification. A complete runnable source/install
example lives in docs/heldout-chemistry-validation.md. Preserve and reload receipts
with load_validation_receipt(path) to verify their evidence and digest.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
from importlib.resources import files
import json
import math
from pathlib import Path
from typing import Any

# === MODULE_BUILD ===
# id: epac_heldout_validation
#   module_name: epac_heldout_validation
#   module_kind: experiment
#   summary: comparison-only held-out validation boundary that preregisters case identities and comparator rules before EPAC predictions are frozen and oracle values are revealed
#   owner: The Interdependency
#   public_surface: freeze_validation_plan, freeze_predictions, verify_commitment, compare_after_freeze, load_validation_plan, load_prediction_commitment, load_validation_receipt, load_oracle, load_packaged_oracle
#   internal_surface: _canonical, _digest, _required_nonempty_string, _normalize_json_value, _normalized_domain, _has_nonempty_provenance_identity, _normalized_comparison, _verify_validation_plan, _verify_prediction_plan_binding, _verify_validation_receipt, _json_exact_equal, _finite_number, _json_token, _numeric_within_tolerance, _compare, _reject_duplicate_object_pairs, _parse_roundtrip_float, _loads_evidence_json
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_heldout_validation
#   rollout: opt-in research validation surface; callers persist the validation-plan commitment before prediction commitment and reveal independently sourced oracle values only during comparison
#   rollback: remove this module, its package and boundary-inventory entries, tests, oracle fixture, and documentation without changing EPAC construction modules or chemistry derivation behavior
#   since: 2026-09-29
#   unresolved: external oracle authority selection and custody remain outside EPAC; this module binds supplied evidence but does not establish independent custody by itself
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: heldout_selection_boundary_frozen_before_predictions
#   given: a validation plan and prediction commitment are supplied for held-out comparison
#   then: case ids, canonical domains, and comparator rules are bound before predictions; prediction ids outside that verified plan are rejected
#   class: evidence
#   since: 2026-09-29
#
# id: heldout_commitment_persistence_and_identity
#   given: predictions and source identity are frozen, serialized, reloaded, or externally reconstructed
#   then: only persistence-stable JSON-shaped prediction values with a nonempty resolved source identity and matching digest are accepted; the reserved hmmm source sentinel is rejected
#   class: evidence
#   since: 2026-09-29
#
# id: heldout_comparison_tri_state_semantics
#   given: frozen predictions and held-out expected values are compared under a preregistered comparator
#   then: comparable agreement is SURVIVED, comparable disagreement is FALSIFIED, and missing or incomparable evidence is UNRESOLVED without bool/number aliasing or large-integer loss
#   class: correctness
#   since: 2026-09-29
#
# id: heldout_oracle_evidence_integrity
#   given: held-out oracle cases and provenance are revealed after prediction commitment
#   then: oracle ids are unique, values are persistence-stable, provenance identities are nonblank and not hmmm, and malformed evidence cannot be scored as success
#   class: evidence
#   since: 2026-09-29
#
# id: heldout_receipt_evidence_binding
#   given: a verified plan, verified prediction commitment, and held-out oracle are compared
#   then: returned receipt evidence is detached from mutable caller inputs and binds the plan, prediction commitment, oracle digest, results, and counts
#   class: evidence
#   since: 2026-09-29
#
# id: heldout_oracle_loading_is_unambiguous
#   given: oracle evidence is loaded from a file, source checkout, or installed distribution
#   then: duplicate JSON keys are rejected and source checkout data is preferred over an unrelated installed package
#   class: correctness
#   since: 2026-09-29
#
# id: heldout_persisted_commitments_are_unambiguous
#   given: a persisted validation plan or prediction commitment is loaded from a file
#   then: duplicate JSON keys at every depth and invalid envelopes or digests are rejected; prediction commitments are verified against the supplied frozen plan before being returned
#   class: evidence
#   since: 2026-10-04
#
# id: heldout_persisted_receipts_preserve_evidence
#   given: a persisted validation receipt is reloaded
#   then: duplicate keys, invalid envelopes or bindings, inconsistent results or counts, and digest mismatches are rejected; valid evidence is preserved without granting custody authentication
#   class: evidence
#   since: 2026-10-04
#
# id: heldout_json_numbers_preserve_decimal_value
#   given: a JSON number with a decimal point or exponent is loaded as held-out evidence
#   then: its exact decimal value must survive parsing and canonical float serialization; rounding, underflow, and overflow are rejected before commitment or scoring
#   class: evidence
#   since: 2026-10-04
# === END CONTRACTS ===

STATUSES = ("SURVIVED", "FALSIFIED", "UNRESOLVED")
_PLAN_SCHEMA = "epac.heldout-validation-plan"
_PREDICTION_SCHEMA = "epac.heldout-prediction-commitment"
_ORACLE_SCHEMA = "epac.heldout-chemistry-oracle"
_RECEIPT_SCHEMA = "epac.heldout-validation-receipt"
_VERSION = "v1"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _required_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    if field == "source_identity" and value.strip().casefold() == "hmmm":
        raise ValueError("source_identity must be resolved, not the hmmm sentinel")
    return value


def _normalize_json_value(value: Any, *, field: str) -> Any:
    """Normalize the supported JSON container/type model without coercing tuples."""
    if value is None:
        return None
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, str):
        return str(value)
    if isinstance(value, list):
        return [
            _normalize_json_value(item, field=f"{field}[]")
            for item in value
        ]
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{field} object keys must be strings")
            normalized[key] = _normalize_json_value(
                item,
                field=f"{field}.{key}",
            )
        return normalized
    raise ValueError(
        f"{field} must use JSON-shaped values; unsupported type: "
        f"{type(value).__name__}"
    )


def _normalized_domain(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("domain must be null or a nonempty canonical string")
    return value


def _has_nonempty_provenance_identity(provenance: Any) -> bool:
    if not isinstance(provenance, Mapping):
        return False
    return all(
        isinstance(provenance.get(field), str)
        and bool(provenance[field].strip())
        and provenance[field].strip().casefold() != "hmmm"
        for field in ("authority", "locator")
    )


def _normalized_comparison(case: Mapping[str, Any]) -> dict[str, Any]:
    comparison = case.get("comparison", {"kind": "exact"})
    if not isinstance(comparison, Mapping):
        raise ValueError("comparison must be a mapping")
    kind = comparison.get("kind", "exact")
    if not isinstance(kind, str) or not kind.strip() or kind != kind.strip():
        raise ValueError("comparison kind must be a nonempty canonical string")
    allowed = {"kind", "absolute_tolerance"} if kind == "numeric-tolerance" else {"kind"}
    extra = set(comparison) - allowed
    if extra:
        fields = ", ".join(sorted(str(field) for field in extra))
        raise ValueError(f"unexpected comparator fields for {kind}: {fields}")
    normalized: dict[str, Any] = {"kind": kind}
    if "absolute_tolerance" in comparison:
        tolerance = comparison["absolute_tolerance"]
        if tolerance is not None and (
            isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
        ):
            raise ValueError("absolute_tolerance must be a number or null")
        normalized["absolute_tolerance"] = _normalize_json_value(
            tolerance,
            field="absolute_tolerance",
        )
    return normalized


def freeze_validation_plan(cases: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Commit case identity, domain, and comparator rules before predictions."""
    if not isinstance(cases, list):
        raise ValueError("validation plan cases must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    allowed = {"id", "domain", "comparison"}
    for case in cases:
        if not isinstance(case, Mapping):
            raise ValueError("validation plan cases must be mappings")
        extra = set(case) - allowed
        if extra:
            raise ValueError("validation plan cannot contain expected values, provenance, or other oracle fields")
        case_id = _required_nonempty_string(case.get("id"), "case id")
        if case_id in seen:
            raise ValueError(f"duplicate validation plan case id: {case_id}")
        seen.add(case_id)
        normalized.append({
            "id": case_id,
            "domain": _normalized_domain(case.get("domain")),
            "comparison": _normalized_comparison(case),
        })
    normalized.sort(key=lambda case: case["id"])
    envelope = {
        "schema": _PLAN_SCHEMA,
        "version": _VERSION,
        "cases": normalized,
    }
    return {**envelope, "plan_sha256": _digest(envelope)}


def _verify_validation_plan(plan: Mapping[str, Any]) -> None:
    required = {"schema", "version", "cases", "plan_sha256"}
    if set(plan) != required:
        raise ValueError("invalid validation plan envelope")
    if plan["schema"] != _PLAN_SCHEMA or plan["version"] != _VERSION:
        raise ValueError("unsupported validation plan")
    cases = plan["cases"]
    if not isinstance(cases, list):
        raise ValueError("validation plan cases must be a list")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, Mapping) or set(case) != {"id", "domain", "comparison"}:
            raise ValueError("invalid validation plan case")
        case_id = _required_nonempty_string(case.get("id"), "case id")
        _normalized_domain(case.get("domain"))
        if case_id in seen:
            raise ValueError(f"duplicate validation plan case id: {case_id}")
        seen.add(case_id)
        normalized_comparison = _normalized_comparison(case)
        if _canonical(normalized_comparison) != _canonical(case["comparison"]):
            raise ValueError("validation plan comparison must be canonical")
    unsigned = {k: plan[k] for k in ("schema", "version", "cases")}
    if _digest(unsigned) != plan["plan_sha256"]:
        raise ValueError("validation plan digest mismatch")


def freeze_predictions(
    predictions: Mapping[str, Any],
    *,
    source_identity: str,
    validation_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Commit predictions only after case inventory/comparators are frozen."""
    _verify_validation_plan(validation_plan)
    _required_nonempty_string(source_identity, "source_identity")
    if not isinstance(predictions, Mapping):
        raise ValueError("predictions must be a mapping")
    allowed_ids = {case["id"] for case in validation_plan["cases"]}
    normalized: dict[str, Any] = {}
    for case_id, value in predictions.items():
        case_id = _required_nonempty_string(case_id, "prediction case id")
        if case_id not in allowed_ids:
            raise ValueError(f"prediction case is absent from frozen validation plan: {case_id}")
        normalized[case_id] = _normalize_json_value(
            value,
            field=f"prediction[{case_id}]",
        )
    normalized = dict(sorted(normalized.items()))
    envelope = {
        "schema": _PREDICTION_SCHEMA,
        "version": _VERSION,
        "source_identity": source_identity,
        "validation_plan_sha256": validation_plan["plan_sha256"],
        "predictions": normalized,
    }
    return {**envelope, "commitment_sha256": _digest(envelope)}


def verify_commitment(commitment: Mapping[str, Any]) -> None:
    """Verify this envelope; plan membership is checked at load/comparison time."""
    required = {
        "schema",
        "version",
        "source_identity",
        "validation_plan_sha256",
        "predictions",
        "commitment_sha256",
    }
    if set(commitment) != required:
        raise ValueError("invalid prediction commitment envelope")
    if commitment["schema"] != _PREDICTION_SCHEMA or commitment["version"] != _VERSION:
        raise ValueError("unsupported prediction commitment")
    _required_nonempty_string(commitment["source_identity"], "source_identity")
    _required_nonempty_string(commitment["validation_plan_sha256"], "validation_plan_sha256")
    if not isinstance(commitment["predictions"], Mapping):
        raise ValueError("predictions must be a mapping")
    for case_id, value in commitment["predictions"].items():
        _required_nonempty_string(case_id, "prediction case id")
        _normalize_json_value(value, field=f"prediction[{case_id}]")
    unsigned = {
        k: commitment[k]
        for k in ("schema", "version", "source_identity", "validation_plan_sha256", "predictions")
    }
    if _digest(unsigned) != commitment["commitment_sha256"]:
        raise ValueError("prediction commitment digest mismatch")


def _verify_prediction_plan_binding(
    commitment: Mapping[str, Any], validation_plan: Mapping[str, Any]
) -> None:
    _verify_validation_plan(validation_plan)
    verify_commitment(commitment)
    if commitment["validation_plan_sha256"] != validation_plan["plan_sha256"]:
        raise ValueError("prediction commitment is bound to a different validation plan")
    allowed_ids = {case["id"] for case in validation_plan["cases"]}
    unexpected_ids = sorted(set(commitment["predictions"]) - allowed_ids)
    if unexpected_ids:
        raise ValueError(
            "prediction commitment includes cases absent from frozen validation plan: "
            + ", ".join(unexpected_ids)
        )


def _json_exact_equal(left: Any, right: Any) -> bool | None:
    """JSON-type-aware equality; None means the values are not comparable JSON."""
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, bool) or isinstance(right, bool):
        if not isinstance(left, bool) or not isinstance(right, bool):
            return False
        return left == right
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        if not isinstance(left, (int, float)) or isinstance(left, bool):
            return False
        if not isinstance(right, (int, float)) or isinstance(right, bool):
            return False
        if isinstance(left, float) and not math.isfinite(left):
            return None
        if isinstance(right, float) and not math.isfinite(right):
            return None
        return left == right
    if isinstance(left, str) or isinstance(right, str):
        return left == right if isinstance(left, str) and isinstance(right, str) else False
    if isinstance(left, list) or isinstance(right, list):
        if not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right):
            return False
        comparisons = [_json_exact_equal(a, b) for a, b in zip(left, right)]
        if any(value is None for value in comparisons):
            return None
        return all(comparisons)
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            return False
        if not all(isinstance(key, str) for key in left) or not all(isinstance(key, str) for key in right):
            return None
        if set(left) != set(right):
            return False
        comparisons = [_json_exact_equal(left[key], right[key]) for key in left]
        if any(value is None for value in comparisons):
            return None
        return all(comparisons)
    return None


def _finite_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _json_token(value: Any) -> tuple[Any, ...] | None:
    """Hashable JSON-type token used by set equality without bool/int aliasing."""
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, float)):
        finite = _finite_number(value)
        return None if finite is None else ("number", value)
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, list):
        items = tuple(_json_token(item) for item in value)
        return None if any(item is None for item in items) else ("array", items)
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            return None
        items = tuple((key, _json_token(value[key])) for key in sorted(value))
        return None if any(item is None for _, item in items) else ("object", items)
    return None


def _numeric_within_tolerance(
    expected: Any,
    predicted: Any,
    tolerance_value: Any,
) -> bool | None:
    tolerance = _finite_number(tolerance_value)
    left = _finite_number(predicted)
    right = _finite_number(expected)
    if tolerance is None or tolerance < 0 or left is None or right is None:
        return None
    return abs(Fraction(left) - Fraction(right)) <= Fraction(tolerance)


def _compare(expected: Any, predicted: Any, rule: Mapping[str, Any]) -> str:
    kind = rule.get("kind", "exact")
    if kind == "exact":
        equal = _json_exact_equal(predicted, expected)
        if equal is None:
            return "UNRESOLVED"
        return "SURVIVED" if equal else "FALSIFIED"
    if kind == "set-equality":
        if not isinstance(predicted, list) or not isinstance(expected, list):
            return "UNRESOLVED"
        predicted_tokens = {_json_token(item) for item in predicted}
        expected_tokens = {_json_token(item) for item in expected}
        if None in predicted_tokens or None in expected_tokens:
            return "UNRESOLVED"
        return "SURVIVED" if predicted_tokens == expected_tokens else "FALSIFIED"
    if kind == "numeric-tolerance":
        within = _numeric_within_tolerance(
            expected,
            predicted,
            rule.get("absolute_tolerance"),
        )
        if within is None:
            return "UNRESOLVED"
        return "SURVIVED" if within else "FALSIFIED"
    return "UNRESOLVED"


def compare_after_freeze(
    commitment: Mapping[str, Any],
    oracle: Mapping[str, Any],
    *,
    validation_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Reveal independently sourced oracle values only after both commitments."""
    plan_snapshot = _normalize_json_value(
        validation_plan,
        field="validation_plan",
    )
    commitment_snapshot = _normalize_json_value(
        commitment,
        field="commitment",
    )
    oracle_snapshot = _normalize_json_value(
        oracle,
        field="oracle",
    )
    if not isinstance(plan_snapshot, dict):
        raise ValueError("validation plan must be a JSON object")
    if not isinstance(commitment_snapshot, dict):
        raise ValueError("prediction commitment must be a JSON object")
    if not isinstance(oracle_snapshot, dict):
        raise ValueError("oracle must be a JSON object")

    _verify_prediction_plan_binding(commitment_snapshot, plan_snapshot)
    if oracle_snapshot.get("schema") != _ORACLE_SCHEMA or oracle_snapshot.get("version") != _VERSION:
        raise ValueError("unsupported held-out oracle")
    cases = oracle_snapshot.get("cases")
    if not isinstance(cases, list):
        raise ValueError("oracle cases must be a list")

    oracle_by_id: dict[str, Mapping[str, Any]] = {}
    for case in cases:
        if not isinstance(case, Mapping):
            raise ValueError("oracle cases must be mappings")
        case_id = _required_nonempty_string(case.get("id"), "oracle case id")
        if case_id in oracle_by_id:
            raise ValueError(f"duplicate oracle case id: {case_id}")
        oracle_by_id[case_id] = case

    plan_by_id = {case["id"]: case for case in plan_snapshot["cases"]}
    if set(oracle_by_id) != set(plan_by_id):
        raise ValueError("oracle case inventory does not match frozen validation plan")

    predictions = commitment_snapshot["predictions"]
    results: list[dict[str, Any]] = []
    for case_id in sorted(plan_by_id):
        case = oracle_by_id[case_id]
        plan_case = plan_by_id[case_id]
        oracle_rule = _normalized_comparison(case)
        if _canonical(oracle_rule) != _canonical(plan_case["comparison"]):
            raise ValueError(f"oracle comparator does not match frozen validation plan: {case_id}")
        oracle_domain = _normalized_domain(case.get("domain"))
        if oracle_domain != plan_case["domain"]:
            raise ValueError(f"oracle domain does not match frozen validation plan: {case_id}")

        provenance = case.get("provenance")
        if not _has_nonempty_provenance_identity(provenance):
            results.append({
                "id": case_id,
                "domain": plan_case["domain"],
                "status": "UNRESOLVED",
                "reason": "missing provenance identity",
            })
            continue
        if "expected" not in case:
            results.append({
                "id": case_id,
                "domain": plan_case["domain"],
                "status": "UNRESOLVED",
                "reason": "missing expected value",
                "provenance": deepcopy(provenance),
            })
            continue
        if case_id not in predictions:
            results.append({
                "id": case_id,
                "domain": plan_case["domain"],
                "status": "UNRESOLVED",
                "reason": "no frozen prediction",
                "expected": deepcopy(case["expected"]),
                "provenance": deepcopy(provenance),
            })
            continue

        status = _compare(case["expected"], predictions[case_id], plan_case["comparison"])
        results.append({
            "id": case_id,
            "domain": plan_case["domain"],
            "status": status,
            "predicted": deepcopy(predictions[case_id]),
            "expected": deepcopy(case["expected"]),
            "comparison": deepcopy(plan_case["comparison"]),
            "provenance": deepcopy(provenance),
        })

    counts = {status: sum(result["status"] == status for result in results) for status in STATUSES}
    receipt = {
        "schema": _RECEIPT_SCHEMA,
        "version": _VERSION,
        "validation_plan_sha256": plan_snapshot["plan_sha256"],
        "prediction_commitment_sha256": commitment_snapshot["commitment_sha256"],
        "oracle_sha256": _digest(oracle_snapshot),
        "results": results,
        "counts": counts,
    }
    return {**receipt, "receipt_sha256": _digest(receipt)}


def _reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key in held-out evidence: {key}")
        value[key] = item
    return value


def _parse_roundtrip_float(token: str) -> float:
    """Accept only decimal values preserved by our JSON float representation.

This protects decimal-value identity across JSON round trips; it does not claim
that ordinary decimals such as 0.1 have exact binary floating-point encodings.
"""
    value = float(token)
    if not math.isfinite(value) or Decimal(str(value)) != Decimal(token):
        raise ValueError("JSON number cannot round-trip without rounding")
    return value


def _loads_evidence_json(payload: str, *, document: str) -> dict[str, Any]:
    value = json.loads(
        payload, object_pairs_hook=_reject_duplicate_object_pairs,
        parse_float=_parse_roundtrip_float,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{document} document must be a JSON object")
    return value


def load_validation_plan(path: str | Path) -> dict[str, Any]:
    """Reload an unambiguous, verified plan before deriving predictions."""
    plan = _loads_evidence_json(
        Path(path).read_text(encoding="utf-8"), document="validation plan"
    )
    _verify_validation_plan(plan)
    return plan


def load_prediction_commitment(
    path: str | Path, *, validation_plan: Mapping[str, Any]
) -> dict[str, Any]:
    """Reload unambiguous predictions bound to a verified plan, without an oracle."""
    commitment = _loads_evidence_json(
        Path(path).read_text(encoding="utf-8"), document="prediction commitment"
    )
    _verify_prediction_plan_binding(commitment, validation_plan)
    return commitment


def _verify_validation_receipt(receipt: Mapping[str, Any]) -> None:
    required = {
        "schema", "version", "validation_plan_sha256", "prediction_commitment_sha256",
        "oracle_sha256", "results", "counts", "receipt_sha256",
    }
    if set(receipt) != required:
        raise ValueError("invalid validation receipt envelope")
    if receipt["schema"] != _RECEIPT_SCHEMA or receipt["version"] != _VERSION:
        raise ValueError("unsupported validation receipt")
    for field in ("validation_plan_sha256", "prediction_commitment_sha256", "oracle_sha256", "receipt_sha256"):
        value = receipt[field]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"{field} must be a canonical SHA-256 digest")
    if not isinstance(receipt["results"], list):
        raise ValueError("receipt results must be a list")
    counts = receipt["counts"]
    if not isinstance(counts, Mapping) or set(counts) != set(STATUSES):
        raise ValueError("invalid receipt counts")
    if any(type(value) is not int or value < 0 for value in counts.values()):
        raise ValueError("receipt counts must be nonnegative integers")
    observed = dict.fromkeys(STATUSES, 0)
    seen: set[str] = set()
    base_fields = {"id", "domain", "status"}
    reason_fields = {
        "missing provenance identity": base_fields | {"reason"},
        "missing expected value": base_fields | {"reason", "provenance"},
        "no frozen prediction": base_fields | {"reason", "expected", "provenance"},
    }
    for result in receipt["results"]:
        if not isinstance(result, Mapping) or not base_fields <= result.keys():
            raise ValueError("invalid receipt result")
        case_id = _required_nonempty_string(result["id"], "receipt case id")
        if case_id in seen:
            raise ValueError(f"duplicate receipt case id: {case_id}")
        seen.add(case_id)
        _normalized_domain(result["domain"])
        status = result["status"]
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("invalid receipt result status")
        if "reason" in result:
            reason = result["reason"]
            if not isinstance(reason, str) or reason not in reason_fields:
                raise ValueError("invalid receipt unresolved reason")
            if status != "UNRESOLVED" or set(result) != reason_fields[reason]:
                raise ValueError("receipt result contradicts its unresolved reason")
        else:
            if set(result) != base_fields | {"predicted", "expected", "comparison", "provenance"}:
                raise ValueError("invalid scored receipt result")
            rule = _normalized_comparison(result)
            if _canonical(rule) != _canonical(result["comparison"]):
                raise ValueError("receipt comparison must be canonical")
            if _compare(result["expected"], result["predicted"], rule) != status:
                raise ValueError("receipt result status disagrees with preserved evidence")
        if "provenance" in result and not _has_nonempty_provenance_identity(result["provenance"]):
            raise ValueError("receipt result has unresolved provenance identity")
        observed[status] += 1
    if counts != observed:
        raise ValueError("receipt counts do not match results")
    if _digest({key: receipt[key] for key in required - {"receipt_sha256"}}) != receipt["receipt_sha256"]:
        raise ValueError("validation receipt digest mismatch")


def load_validation_receipt(path: str | Path) -> dict[str, Any]:
    """Reload duplicate-safe, internally verified evidence; this is not authentication."""
    receipt = _loads_evidence_json(
        Path(path).read_text(encoding="utf-8"), document="validation receipt"
    )
    _verify_validation_receipt(receipt)
    return receipt


def load_oracle(path: str | Path) -> dict[str, Any]:
    """Comparison-side helper. Construction modules must not call this."""
    return _loads_evidence_json(Path(path).read_text(encoding="utf-8"), document="oracle")


def load_packaged_oracle() -> dict[str, Any]:
    """Load this checkout's oracle first, otherwise the installed package resource."""
    source_oracle = Path(__file__).resolve().parent / "data" / "heldout_chemistry_oracle.json"
    if source_oracle.is_file():
        return load_oracle(source_oracle)
    resource = files("epac_data").joinpath("heldout_chemistry_oracle.json")
    return _loads_evidence_json(resource.read_text(encoding="utf-8"), document="oracle")
