"""Identity-only subatomic element affixiation candidate.

This module implements the provisional baseline from
``subatomic-affixiation-baseline.md``: hydrogen, helium, lithium, and carbon
element-gonol candidates over the established UCNS carrier identity surfaces
(Public Gonol 157) and the native Möbius root-loop quotient, using the Möbius
turn index as the time-agnostic ordered parameter.

It consumes exactly two UCNS public surfaces:

- ``ucns.public_gonol_function`` for carrier identity positions;
- ``ucns.native_mobius_state`` for the established Möbius framing.

No Public Gonol position operation is defined, inferred, or asserted here.
Status: CROSS-DOMAIN-HYPOTHESIS / provisional. Not org canon.

Usage guidance:

    PYTHONPATH=<ucns-snapshot>/src python3 - <<'PY'
    from element_affixiation_candidate import affixiate_element, replay_element

    he = affixiate_element("He")
    print(he.receipt)
    ok, replay_receipt = replay_element("He")
    print("replay byte-identical:", ok and replay_receipt == he.receipt)
    PY
"""

# === MODULE_BUILD ===
# id: epac_subatomic_element_affixiation_candidate
#   module_name: element_affixiation_candidate
#   module_kind: experiment
#   summary: identity-only H/He/Li/C element-gonol candidates over established UCNS carrier identity and native Möbius framing; no position operation invented
#   owner: The Interdependency
#   public_surface: ISOTOPE_DEFAULTS, CONSTRUCTION_IDS, ElementCandidate, affixiate_element, replay_element, element_receipt
#   internal_surface: _canonical_record, _t_states
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: subatomic.test_element_affixiation_candidate
#   rollout: local candidate module under stack/research/epac/subatomic/
#   rollback: remove module, tests, and generated receipts
#   requires: ucns_public_gonol_geometry, ucns_native_mobius_geometry
#   since: 2026-08-22
#   unresolved: Public Gonol position operations; harmonic notation; isotope defaults are instance-resolved; epac canonical repository absent
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: candidate_uses_only_established_ucns_surfaces
#   given: the candidate module is imported and executed
#   then: only ucns.public_gonol_function and ucns.native_mobius_state are consumed; no position operation is defined, inferred, or called
#   class: safety
#
# id: element_identity_positions_exact
#   given: an element symbol with default isotope (Z, A)
#   then: proton positions are exactly 1..Z and neutron positions are exactly Z+1..A on the 157-position carrier, as identity coordinates only
#   class: correctness
#
# id: mobius_parameter_sequence_exact
#   given: the Möbius turn index t in {0, 1, 2} is traversed
#   then: visible phase is unchanged, the local frame sequence is POSITIVE -> REVERSED -> POSITIVE, and complete_key differs only at t=1
#   class: correctness
#
# id: receipt_deterministic_and_replayable
#   given: the same element and the same pinned source identities
#   then: the receipt is byte-identical across independent constructions
#   class: correctness
#
# id: no_physics_or_canon_claim
#   given: any constructed candidate
#   then: status remains CROSS-DOMAIN-HYPOTHESIS and no empirical validity, theorem status, measurement validity, or canon promotion is claimed
#   class: doctrine
# === END CONTRACTS ===

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json

from ucns import native_mobius_state, public_gonol_function

SOURCE_COMMITS = {
    "metapat": "34d954aa1e2092e615b03a180500f6b6977f501e",
    "ucns": "1975fe70cf4e0826a8020c2da3047569e277af64",
}

CONSTRUCTION_IDS = {
    "relation": "metapat.affixiation_harmonics.affixiation",
    "ordered_parameter": "ucns.native-mobius-turn-index",
    "closure_scale": "epac.subatomic.atomic",
    "status": "CROSS-DOMAIN-HYPOTHESIS",
}

# Default isotope instances are instance-resolved, not canonical admission law.
# Extended to Z=1..26 (through iron) for the subatomic gonol program.
ISOTOPE_DEFAULTS = {
    "H": (1, 1), "He": (2, 4), "Li": (3, 7), "Be": (4, 9),
    "B": (5, 11), "C": (6, 12), "N": (7, 14), "O": (8, 16),
    "F": (9, 19), "Ne": (10, 20), "Na": (11, 23), "Mg": (12, 24),
    "Al": (13, 27), "Si": (14, 28), "P": (15, 31), "S": (16, 32),
    "Cl": (17, 35), "Ar": (18, 40), "K": (19, 39), "Ca": (20, 40),
    "Sc": (21, 45), "Ti": (22, 48), "V": (23, 51), "Cr": (24, 52),
    "Mn": (25, 55), "Fe": (26, 56),
}


@dataclass(frozen=True, slots=True)
class ElementCandidate:
    """One closed element-gonol candidate record with deterministic receipt."""

    element_id: str
    symbol: str
    Z: int
    A: int
    proton_positions: tuple[int, ...]
    proton_glyphs: tuple[str, ...]
    neutron_positions: tuple[int, ...]
    neutron_glyphs: tuple[str, ...]
    t_states: tuple[dict, ...]
    relation_id: str
    ordered_parameter_id: str
    closure_scale: str
    source_commits: dict
    status: str
    receipt: str


def _t_states() -> tuple[dict, ...]:
    """Traverse the Möbius turn index t in {0, 1, 2}.

    Uses only the established native Möbius root-loop quotient. Time is not
    inserted: t is a declared ordered parameter, not physical time.
    """
    states = []
    for t in (0, 1, 2):
        state = native_mobius_state(Fraction(t))
        states.append(
            {
                "t": t,
                "visible_key": [state.visible_key[0], str(state.visible_key[1])],
                "complete_key": [
                    state.complete_key[0],
                    str(state.complete_key[1]),
                    state.complete_key[2].value,
                ],
                "frame": state.frame.value,
            }
        )
    return tuple(states)


def _canonical_record(
    element_id: str,
    symbol: str,
    Z: int,
    A: int,
    proton_positions: tuple[int, ...],
    proton_glyphs: tuple[str, ...],
    neutron_positions: tuple[int, ...],
    neutron_glyphs: tuple[str, ...],
) -> dict:
    return {
        "element_id": element_id,
        "symbol": symbol,
        "Z": Z,
        "A": A,
        "proton_positions": list(proton_positions),
        "proton_glyphs": list(proton_glyphs),
        "neutron_positions": list(neutron_positions),
        "neutron_glyphs": list(neutron_glyphs),
        "relation_id": CONSTRUCTION_IDS["relation"],
        "ordered_parameter_id": CONSTRUCTION_IDS["ordered_parameter"],
        "t_states": list(_t_states()),
        "closure_scale": CONSTRUCTION_IDS["closure_scale"],
        "source_commits": SOURCE_COMMITS,
        "status": CONSTRUCTION_IDS["status"],
    }


def element_receipt(record: dict) -> str:
    """SHA-256 over canonical JSON of the construction record."""
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def affixiate_element(symbol: str) -> ElementCandidate:
    """Construct one element-gonol candidate from its default isotope instance.

    Raises ``ValueError`` for symbols outside the declared isotope defaults.
    """
    if symbol not in ISOTOPE_DEFAULTS:
        raise ValueError(
            f"element {symbol!r} has no declared isotope default; "
            f"declared: {sorted(ISOTOPE_DEFAULTS)}"
        )
    Z, A = ISOTOPE_DEFAULTS[symbol]
    proton_positions = tuple(range(1, Z + 1))
    neutron_positions = tuple(range(Z + 1, A + 1))

    # Identity coordinates only. public_gonol_function resolves the exact
    # carrier identity position; no operation is requested or inferred.
    proton_glyphs = tuple(public_gonol_function(i).glyph for i in proton_positions)
    neutron_glyphs = tuple(public_gonol_function(i).glyph for i in neutron_positions)

    record = _canonical_record(
        element_id=f"epac.subatomic_affixiation.{symbol.lower()}",
        symbol=symbol,
        Z=Z,
        A=A,
        proton_positions=proton_positions,
        proton_glyphs=proton_glyphs,
        neutron_positions=neutron_positions,
        neutron_glyphs=neutron_glyphs,
    )
    receipt = element_receipt(record)
    return ElementCandidate(
        element_id=record["element_id"],
        symbol=symbol,
        Z=Z,
        A=A,
        proton_positions=proton_positions,
        proton_glyphs=proton_glyphs,
        neutron_positions=neutron_positions,
        neutron_glyphs=neutron_glyphs,
        t_states=record["t_states"],
        relation_id=record["relation_id"],
        ordered_parameter_id=record["ordered_parameter_id"],
        closure_scale=record["closure_scale"],
        source_commits=SOURCE_COMMITS,
        status=record["status"],
        receipt=receipt,
    )


def replay_element(symbol: str) -> tuple[bool, str]:
    """Independently reconstruct and compare the receipt.

    Returns ``(matches, receipt)``. Replay establishes reproducibility of the
    declared construction only — not geometry, physics, or measurement.
    """
    candidate = affixiate_element(symbol)
    record = _canonical_record(
        element_id=candidate.element_id,
        symbol=candidate.symbol,
        Z=candidate.Z,
        A=candidate.A,
        proton_positions=candidate.proton_positions,
        proton_glyphs=candidate.proton_glyphs,
        neutron_positions=candidate.neutron_positions,
        neutron_glyphs=candidate.neutron_glyphs,
    )
    replay_receipt = element_receipt(record)
    return (replay_receipt == candidate.receipt, replay_receipt)


__all__ = [
    "CONSTRUCTION_IDS",
    "ElementCandidate",
    "ISOTOPE_DEFAULTS",
    "SOURCE_COMMITS",
    "affixiate_element",
    "element_receipt",
    "replay_element",
]
