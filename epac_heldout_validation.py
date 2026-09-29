"""Two-phase held-out chemistry validation for EPAC.

The construction side may create a prediction commitment without importing or
reading the oracle corpus.  Only the comparison phase accepts oracle facts.
This keeps empirical chemistry labels out of EPAC derivation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

STATUSES = ("SURVIVED", "FALSIFIED", "UNRESOLVED")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def freeze_predictions(predictions: Mapping[str, Any], *, source_identity: str) -> dict[str, Any]:
    """Commit predictions before any oracle is supplied."""
    if not source_identity:
        raise ValueError("source_identity is required")
    normalized = {str(k): v for k, v in sorted(predictions.items())}
    envelope = {
        "schema": "epac.heldout-prediction-commitment",
        "version": "v1",
        "source_identity": source_identity,
        "predictions": normalized,
    }
    return {**envelope, "commitment_sha256": _digest(envelope)}


def verify_commitment(commitment: Mapping[str, Any]) -> None:
    required = {"schema", "version", "source_identity", "predictions", "commitment_sha256"}
    if set(commitment) != required:
        raise ValueError("invalid prediction commitment envelope")
    if commitment["schema"] != "epac.heldout-prediction-commitment" or commitment["version"] != "v1":
        raise ValueError("unsupported prediction commitment")
    unsigned = {k: commitment[k] for k in ("schema", "version", "source_identity", "predictions")}
    if _digest(unsigned) != commitment["commitment_sha256"]:
        raise ValueError("prediction commitment digest mismatch")


def _compare(expected: Any, predicted: Any, rule: Mapping[str, Any]) -> str:
    kind = rule.get("kind", "exact")
    if kind == "exact":
        return "SURVIVED" if predicted == expected else "FALSIFIED"
    if kind == "set-equality":
        try:
            return "SURVIVED" if set(predicted) == set(expected) else "FALSIFIED"
        except TypeError:
            return "UNRESOLVED"
    if kind == "numeric-tolerance":
        tolerance = rule.get("absolute_tolerance")
        if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance < 0:
            return "UNRESOLVED"
        try:
            return "SURVIVED" if abs(float(predicted) - float(expected)) <= tolerance else "FALSIFIED"
        except (TypeError, ValueError):
            return "UNRESOLVED"
    return "UNRESOLVED"


def compare_after_freeze(commitment: Mapping[str, Any], oracle: Mapping[str, Any]) -> dict[str, Any]:
    """Reveal an independently sourced oracle only after commitment verification."""
    verify_commitment(commitment)
    if oracle.get("schema") != "epac.heldout-chemistry-oracle" or oracle.get("version") != "v1":
        raise ValueError("unsupported held-out oracle")
    cases = oracle.get("cases")
    if not isinstance(cases, list):
        raise ValueError("oracle cases must be a list")

    predictions = commitment["predictions"]
    results = []
    for case in cases:
        case_id = case.get("id")
        provenance = case.get("provenance", {})
        authoritative = provenance.get("authority")
        locator = provenance.get("locator")
        if not case_id or not authoritative or not locator:
            results.append({"id": case_id, "status": "UNRESOLVED", "reason": "missing case/provenance identity"})
            continue
        if case_id not in predictions:
            results.append({"id": case_id, "status": "UNRESOLVED", "reason": "no frozen prediction"})
            continue
        status = _compare(case.get("expected"), predictions[case_id], case.get("comparison", {"kind": "exact"}))
        results.append({
            "id": case_id,
            "domain": case.get("domain"),
            "status": status,
            "predicted": predictions[case_id],
            "expected": case.get("expected"),
            "provenance": provenance,
        })

    counts = {status: sum(r["status"] == status for r in results) for status in STATUSES}
    receipt = {
        "schema": "epac.heldout-validation-receipt",
        "version": "v1",
        "prediction_commitment_sha256": commitment["commitment_sha256"],
        "oracle_sha256": _digest(oracle),
        "results": results,
        "counts": counts,
    }
    return {**receipt, "receipt_sha256": _digest(receipt)}


def load_oracle(path: str | Path) -> dict[str, Any]:
    """Comparison-side helper. Construction modules must not call this."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
