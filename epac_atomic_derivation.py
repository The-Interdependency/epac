# === MODULE_BUILD ===
# id: epac_atomic_quantum_receipts
#   module_name: epac_atomic_derivation
#   module_kind: construction
#   summary: derives period and valence electron count from the frozen epac_atomic quantum-shell electron states, and freezes byte-replayable receipts for Z=1-18
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, derive_period, derive_valence_electrons, atomic_quantum_receipt, freeze_atomic_quantum_receipts, replay_atomic_quantum_receipts, prove_derivation_not_lookup
#   internal_surface: electron-state reduction, canonical receipt serialization
#   auth_boundary: none
#   storage_boundary: immutable records only
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_atomic_quantum_derivation
#   rollout: frozen source evidence for the stack EPAC carrier audit; derivation from construction, not lookup
#   rollback: remove this module, its tests, and any downstream pins
#   requires: epac_atomic
#   since: 2026-09-17
#   unresolved: promotion of the stack carrier remains a stack-side decision
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: atomic_period_is_outermost_principal_quantum_number
#   given: the frozen electron states of any Z in 1..18
#   then: derived period equals the maximum principal quantum number n
#   class: correctness
#   since: 2026-09-17
#
# id: atomic_valence_is_outermost_shell_occupancy
#   given: the frozen electron states of any Z in 1..18
#   then: derived valence electron count equals the number of electrons in the outermost shell
#   class: correctness
#   since: 2026-09-17
#
# id: atomic_derivation_is_from_construction_not_lookup
#   given: the derivation functions
#   then: they consume only the electron states and never read a periodic-table data file or a group table
#   class: doctrine
#   since: 2026-09-17
#
# id: atomic_quantum_receipts_fail_closed
#   given: malformed or tampered receipt bytes
#   then: replay raises rather than accepting drifted records
#   class: safety
#   since: 2026-09-17
# === END CONTRACTS ===

"""Derive period and valence from epac_atomic quantum-shell construction.

The frozen ``epac_atomic`` module fills electrons by Aufbau, Pauli, and Hund
rules and computes Slater screening. Period and valence are therefore
derivable from the constructed electron states themselves:

* ``period`` is the outermost principal quantum number ``max(n)``;
* ``valence_electrons`` is the occupancy of that outermost shell.

This module exposes that derivation and freezes byte-replayable receipts so
downstream audits can bind exact source evidence instead of consulting a
periodic-table lookup.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from epac_atomic import AtomicRecord, ElectronState, atomic_record

SCHEMA = "epac.atomic-quantum-receipt"
SCHEMA_SET = "epac.atomic-quantum-receipt-set"
VERSION = "0.1.0"


class AtomicQuantumReceiptError(ValueError):
    """Raised when the quantum receipt fails closed."""


def derive_period(electrons: tuple[ElectronState, ...]) -> int:
    """Return the outermost principal quantum number."""

    if not electrons:
        raise AtomicQuantumReceiptError("electron states are empty")
    return max(electron.n for electron in electrons)


def derive_valence_electrons(electrons: tuple[ElectronState, ...]) -> int:
    """Return the electron occupancy of the outermost shell."""

    outermost = derive_period(electrons)
    return sum(1 for electron in electrons if electron.n == outermost)


def _electron_dict(electron: ElectronState) -> dict[str, Any]:
    return asdict(electron)


def atomic_quantum_receipt(Z: int) -> dict[str, Any]:
    """Build one canonical quantum-shell receipt for atomic number Z."""

    if isinstance(Z, bool) or not isinstance(Z, int) or not 1 <= Z <= 18:
        raise AtomicQuantumReceiptError("Z must be an integer in 1..18")
    record = atomic_record(Z)
    period_derived = derive_period(record.electrons)
    valence_derived = derive_valence_electrons(record.electrons)
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "Z": Z,
        "symbol": record.symbol,
        "period_recorded": record.period,
        "period_derived": period_derived,
        "valence_electrons_recorded": record.valence_electrons,
        "valence_electrons_derived": valence_derived,
        "derived_from": "electron-states",
        "lookup_used": False,
        "configuration": record.configuration,
        "electrons": [_electron_dict(electron) for electron in record.electrons],
    }


def freeze_atomic_quantum_receipts() -> dict[str, Any]:
    """Freeze the canonical quantum-shell receipt set for Z=1..18."""

    records = [atomic_quantum_receipt(Z) for Z in range(1, 19)]
    payload = {
        "schema": SCHEMA_SET,
        "version": VERSION,
        "module": "epac_atomic",
        "records": records,
    }
    payload["receipt_sha256"] = sha256(
        json.dumps(
            {key: value for key, value in payload.items() if key != "receipt_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def replay_atomic_quantum_receipts(data: bytes) -> dict[str, Any]:
    """Recompute the receipt set and verify it byte-for-byte."""

    if not isinstance(data, bytes):
        raise AtomicQuantumReceiptError("receipt must be bytes")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AtomicQuantumReceiptError("receipt is not valid canonical JSON") from exc
    if not isinstance(obj, dict):
        raise AtomicQuantumReceiptError("receipt root must be an object")
    if obj.get("schema") != SCHEMA_SET or obj.get("version") != VERSION:
        raise AtomicQuantumReceiptError("receipt schema or version mismatch")

    rebuilt = freeze_atomic_quantum_receipts()
    if rebuilt["receipt_sha256"] != obj.get("receipt_sha256"):
        raise AtomicQuantumReceiptError("receipt digest does not match recomputation")
    rebuilt_bytes = json.dumps(rebuilt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if rebuilt_bytes != data:
        raise AtomicQuantumReceiptError("receipt does not replay byte-identically")
    return rebuilt


def prove_derivation_not_lookup() -> dict[str, Any]:
    """Prove period and valence derive from the electron states alone."""

    results = []
    for Z in range(1, 19):
        record = atomic_record(Z)
        results.append(
            {
                "Z": Z,
                "period_derived": derive_period(record.electrons),
                "period_recorded": record.period,
                "period_matches": derive_period(record.electrons) == record.period,
                "valence_derived": derive_valence_electrons(record.electrons),
                "valence_recorded": record.valence_electrons,
                "valence_matches": derive_valence_electrons(record.electrons) == record.valence_electrons,
            }
        )
    return {
        "period_matches_for_all": all(item["period_matches"] for item in results),
        "valence_matches_for_all": all(item["valence_matches"] for item in results),
        "derivation_inputs": "electron states only (n, l, m_l, m_s)",
        "lookup_used": False,
        "results": results,
    }


__all__ = [
    "SCHEMA",
    "SCHEMA_SET",
    "VERSION",
    "AtomicQuantumReceiptError",
    "derive_period",
    "derive_valence_electrons",
    "atomic_quantum_receipt",
    "freeze_atomic_quantum_receipts",
    "replay_atomic_quantum_receipts",
    "prove_derivation_not_lookup",
]
