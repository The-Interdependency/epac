"""Executable witnesses for the subatomic element affixiation candidate."""

# === CHECKS ===
# id: check_candidate_uses_only_established_ucns_surfaces
#   proves: candidate_uses_only_established_ucns_surfaces
#   call: self::test_imports_consume_only_established_ucns_surfaces
#   mutates: none
#   cleanup: none
#
# id: check_element_identity_positions_exact
#   proves: element_identity_positions_exact
#   call: self::test_element_identity_positions_exact
#   mutates: none
#   cleanup: none
#
# id: check_mobius_parameter_sequence_exact
#   proves: mobius_parameter_sequence_exact
#   call: self::test_mobius_parameter_sequence_exact
#   mutates: none
#   cleanup: none
#
# id: check_receipt_deterministic_and_replayable
#   proves: receipt_deterministic_and_replayable
#   call: self::test_receipt_deterministic_and_replayable
#   mutates: none
#   cleanup: none
#
# id: check_no_physics_or_canon_claim
#   proves: no_physics_or_canon_claim
#   call: self::test_no_physics_or_canon_claim
#   mutates: none
#   cleanup: none
# === END CHECKS ===

from fractions import Fraction

import element_affixiation_candidate as candidate
from ucns import (
    PUBLIC_GONOL_157,
    PUBLIC_GONOL_SHA256,
    NativeMobiusFrame,
    native_mobius_state,
    public_gonol_function,
)


def test_imports_consume_only_established_ucns_surfaces():
    assert candidate.CONSTRUCTION_IDS["ordered_parameter"] == "ucns.native-mobius-turn-index"
    assert candidate.CONSTRUCTION_IDS["relation"] == "metapat.affixiation_harmonics.affixiation"
    assert public_gonol_function(0).glyph == PUBLIC_GONOL_157[0]


def test_element_identity_positions_exact():
    cases = {
        "H": ((1,), ()),
        "He": ((1, 2), (3, 4)),
        "Li": ((1, 2, 3), (4, 5, 6, 7)),
        "C": ((1, 2, 3, 4, 5, 6), (7, 8, 9, 10, 11, 12)),
    }
    for symbol, (expected_p, expected_n) in cases.items():
        element = candidate.affixiate_element(symbol)
        assert element.proton_positions == expected_p
        assert element.neutron_positions == expected_n
        assert all(0 <= i < len(PUBLIC_GONOL_157) for i in element.proton_positions)
        assert all(0 <= i < len(PUBLIC_GONOL_157) for i in element.neutron_positions)
        assert element.proton_glyphs == tuple(
            public_gonol_function(i).glyph for i in element.proton_positions
        )
        assert element.neutron_glyphs == tuple(
            public_gonol_function(i).glyph for i in element.neutron_positions
        )


def test_mobius_parameter_sequence_exact():
    s0 = native_mobius_state(Fraction(0))
    s1 = native_mobius_state(Fraction(1))
    s2 = native_mobius_state(Fraction(2))
    assert s0.visible_key == s1.visible_key == s2.visible_key
    assert s0.frame is NativeMobiusFrame.POSITIVE
    assert s1.frame is NativeMobiusFrame.REVERSED
    assert s2.frame is NativeMobiusFrame.POSITIVE
    assert s0.complete_key == s2.complete_key
    assert s1.complete_key != s0.complete_key


def test_receipt_deterministic_and_replayable():
    for symbol in candidate.ISOTOPE_DEFAULTS:
        first = candidate.affixiate_element(symbol)
        matches, replay_receipt = candidate.replay_element(symbol)
        assert matches is True
        assert replay_receipt == first.receipt
        assert len(first.receipt) == 64
    receipts = {candidate.affixiate_element(s).receipt for s in candidate.ISOTOPE_DEFAULTS}
    assert len(receipts) == len(candidate.ISOTOPE_DEFAULTS)

    frozen = candidate.affixiate_element("He")
    before = frozen.receipt
    try:
        frozen.t_states[0]["frame"] = "tampered"
    except TypeError:
        pass
    else:
        raise AssertionError("closed t_states must be immutable")
    try:
        frozen.source_commits["ucns"] = "tampered"
    except TypeError:
        pass
    else:
        raise AssertionError("closed source_commits must be immutable")
    assert frozen.receipt == before
    assert candidate.replay_element("He") == (True, before)


def test_no_physics_or_canon_claim():
    for symbol in candidate.ISOTOPE_DEFAULTS:
        element = candidate.affixiate_element(symbol)
        assert element.status == "CROSS-DOMAIN-HYPOTHESIS"
        assert element.closure_scale == "epac.subatomic.atomic"
    assert candidate.SOURCE_COMMITS["metapat"] == "34d954aa1e2092e615b03a180500f6b6977f501e"
    assert candidate.SOURCE_COMMITS["ucns"] == "828c0b8bbcfc267efb5701da714191c1f73a81ff"
    assert PUBLIC_GONOL_SHA256 == "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5"
