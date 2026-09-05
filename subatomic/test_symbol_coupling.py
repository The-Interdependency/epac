"""Executable witnesses for nomenclature abbreviation coupling."""

# === CHECKS ===
# id: check_letters_are_not_physics_domain
#   proves: letters_are_not_physics_domain
#   call: self::test_letters_are_not_physics_domain
#   mutates: none
#   cleanup: none
#
# id: check_symbol_gonol_preserves_exact_abbreviation
#   proves: symbol_gonol_preserves_exact_abbreviation
#   call: self::test_symbol_gonol_preserves_exact_abbreviation
#   mutates: none
#   cleanup: none
#
# id: check_symbol_coupling_two_participants
#   proves: symbol_coupling_two_participants
#   call: self::test_symbol_coupling_two_participants
#   mutates: none
#   cleanup: none
#
# id: check_symbol_coupling_replays_byte_identical
#   proves: symbol_coupling_replays_byte_identical
#   call: self::test_symbol_coupling_replays_byte_identical
#   mutates: none
#   cleanup: none
#
# id: check_symbol_coupling_stays_cross_domain_hypothesis
#   proves: symbol_coupling_stays_cross_domain_hypothesis
#   call: self::test_symbol_coupling_stays_cross_domain_hypothesis
#   mutates: none
#   cleanup: none
# === END CHECKS ===

import symbol_coupling as m


def test_letters_are_not_physics_domain():
    source = open(m.__file__, encoding="utf-8").read()
    assert "from epac_dimensional_arity" not in source
    assert "import epac_dimensional_arity" not in source
    assert "SYMBOL_TO_Z" not in source
    assert "oriented_instance_couplings" not in source
    helium = m.construct_symbol_gonol("He")
    iron = m.construct_symbol_gonol("Fe")
    assert helium.gonol.structure is None
    assert helium.gonol.couplings == ()
    assert iron.gonol.structure is None
    assert dict(helium.gonol.carried_options)["domain"] == "nomenclature"
    for participant in helium.gonol.participants:
        assert dict(participant.carried_options)["domain"] == "nomenclature"
        assert "Z" not in dict(participant.carried_options)


def test_symbol_gonol_preserves_exact_abbreviation():
    h = m.construct_symbol_gonol("H").gonol
    assert len(h.participants) == 1
    assert dict(h.carried_options)["abbreviation-length"] == "1"

    he = m.construct_symbol_gonol("He").gonol
    assert len(he.participants) == 2
    assert [p.identity_glyph for p in he.participants] == ["H", "e"]
    assert dict(he.carried_options)["abbreviation-length"] == "2"

    fe = m.construct_symbol_gonol("Fe").gonol
    assert [p.identity_glyph for p in fe.participants] == ["F", "e"]


def test_symbol_coupling_two_participants():
    for symbol in ("H", "He", "Fe"):
        receipt = m.couple_symbol(symbol)
        assert len(receipt.gonol.participants) == 2
        assert dict(receipt.gonol.carried_options)["symbol"] == symbol
        assert dict(receipt.gonol.carried_options)["domain"] == "nomenclature"
        assert receipt.gonol.structure is None
        assert receipt.gonol.couplings == ()
        assert receipt.gonol.participants[0].relation == "epac.subatomic.element"
        assert receipt.gonol.participants[1].relation == "epac.nomenclature.abbreviation"


def test_symbol_coupling_replays_byte_identical():
    digests = set()
    for symbol in m.SUPPORTED_SYMBOLS:
        receipt = m.couple_symbol(symbol)
        assert m.replay_symbol_coupling(receipt) == receipt.receipt_digest
        digests.add(receipt.receipt_digest)
    assert len(digests) == len(m.SUPPORTED_SYMBOLS)


def test_symbol_coupling_stays_cross_domain_hypothesis():
    receipt = m.couple_symbol("Fe")
    assert receipt.standing == "implemented-candidate"
    assert receipt.selection_effect == "none"
