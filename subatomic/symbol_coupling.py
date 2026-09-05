"""Nomenclature coupling: element gonol + abbreviation.

Letters are not a physics domain. A chemical-symbol abbreviation is a name.
It is not an atom, not a charge, and not the dimensional 3-structure.

- physics: nuclei, electrons, nuclear Z, oriented atom-instance couplings
- nomenclature: ordered abbreviation characters as a name only
- UCNS Public Gonol: optional carrier identity for admitted glyphs

Two-letter names (He, Fe) are two ordered name-characters, not ``(z, x)`` and
``(z, y)`` in physical 3-space, and not a nuclear-Z hub.

Status: CROSS-DOMAIN-HYPOTHESIS / implemented candidate. Not selected canon.

Usage guidance:

    from symbol_coupling import couple_symbol

    receipt = couple_symbol("Fe")
    assert receipt.gonol.structure is None
    print(receipt.receipt_digest)
"""

# === MODULE_BUILD ===
# id: epac_subatomic_symbol_coupling
#   module_name: symbol_coupling
#   module_kind: experiment
#   summary: nomenclature-only coupling of a closed subatomic element gonol to its abbreviation; letters are not physics and do not enter dimensional 3-structure
#   owner: The Interdependency
#   public_surface: SUPPORTED_SYMBOLS, construct_symbol_gonol, couple_symbol, replay_symbol_coupling
#   internal_surface: none
#   auth_boundary: letters/nomenclature are excluded from epac physics couplings
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: subatomic.test_symbol_coupling
#   rollout: local candidate module under stack/research/epac/subatomic/
#   rollback: remove module, tests, and generated receipts
#   requires: epac_public_gonol, epac_subatomic_gonol
#   since: 2026-08-22
#   unresolved: which domain later owns chemical-symbol admission if not physics; two-letter names have no single Public Gonol glyph
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: symbol_gonol_preserves_exact_abbreviation
#   given: a symbol gonol for element symbol S
#   then: participants are the exact ordered name-characters of S; no physics coupling, charge, or 3-structure is attached
#   class: correctness
#
# id: letters_are_not_physics_domain
#   given: symbol_coupling source and any constructed symbol gonol
#   then: epac_dimensional_arity is not imported; nuclear Z is not a letter charge; gonol.structure is None
#   class: doctrine
#
# id: symbol_coupling_two_participants
#   given: a nomenclature-coupled gonol
#   then: exactly two participants (element gonol, symbol gonol) are declared and no physics 3-structure is minted
#   class: correctness
#
# id: symbol_coupling_replays_byte_identical
#   given: a symbol-coupled receipt
#   then: replay_public_gonol reproduces the same receipt_digest
#   class: correctness
#
# id: symbol_coupling_stays_cross_domain_hypothesis
#   given: any symbol-coupled receipt
#   then: standing is implemented-candidate, selection_effect is none, and no canon is selected
#   class: doctrine
# === END CONTRACTS ===

from __future__ import annotations

import os
import sys

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from epac_public_gonol import (  # noqa: E402
    ClosedPublicGonol,
    PublicGonolReceipt,
    construct_public_gonol,
    replay_public_gonol,
)

import subatomic_gonol  # noqa: E402

SUPPORTED_SYMBOLS: tuple[str, ...] = subatomic_gonol.SUPPORTED_SYMBOLS

RELATION_SYMBOL = "epac.nomenclature.abbreviation"
RELATION_COUPLING = "epac.nomenclature.element-abbreviation"


def construct_symbol_gonol(symbol: str, *, occurrence: int = 0) -> PublicGonolReceipt:
    """Close one abbreviation as nomenclature. Not a physics gonol."""

    if symbol not in SUPPORTED_SYMBOLS:
        raise ValueError(f"symbol {symbol!r} is outside the supported element table")
    characters = tuple(symbol)
    glyphs: list[ClosedPublicGonol] = []
    for index, character in enumerate(characters):
        glyphs.append(
            construct_public_gonol(
                source_id=f"epac.nomenclature.character:{symbol}#{occurrence}:{index}:{character}",
                relation="epac.nomenclature.character",
                identity_glyph=character,
                occurrence=index,
                carried_options=(
                    ("domain", "nomenclature"),
                    ("character", character),
                ),
            ).gonol
        )
    return construct_public_gonol(
        source_id=f"epac.nomenclature.abbreviation:{symbol}#{occurrence}",
        relation=RELATION_SYMBOL,
        participants=tuple(glyphs),
        occurrence=occurrence,
        carried_options=(
            ("domain", "nomenclature"),
            ("symbol", symbol),
            ("abbreviation-length", str(len(symbol))),
        ),
    )


def couple_symbol(symbol: str, *, occurrence: int = 0) -> PublicGonolReceipt:
    """Attach a nomenclature abbreviation to a closed physics element gonol.

    The two participants stay in their domains. This is not ``(z, x)``/``(z, y)``
    physics structure.
    """

    element = subatomic_gonol.construct_subatomic_gonol(symbol, occurrence=occurrence).gonol
    symbol_gonol = construct_symbol_gonol(symbol, occurrence=occurrence).gonol
    return construct_public_gonol(
        source_id=f"epac.nomenclature.element-abbreviation:{symbol}#{occurrence}",
        relation=RELATION_COUPLING,
        participants=(element, symbol_gonol),
        occurrence=occurrence,
        carried_options=(
            ("domain", "nomenclature"),
            ("symbol", symbol),
        ),
    )


def replay_symbol_coupling(receipt: PublicGonolReceipt) -> str:
    return replay_public_gonol(receipt).receipt_digest


__all__ = [
    "RELATION_COUPLING",
    "RELATION_SYMBOL",
    "SUPPORTED_SYMBOLS",
    "construct_symbol_gonol",
    "couple_symbol",
    "replay_symbol_coupling",
]
