"""Executable witnesses for the subatomic gonol constructor."""

# === CHECKS ===
# id: check_subatomic_gonol_combines_three_sources
#   proves: subatomic_gonol_combines_three_sources
#   call: self::test_combines_three_sources
#   mutates: none
#   cleanup: none
#
# id: check_subatomic_gonol_replays_byte_identical
#   proves: subatomic_gonol_replays_byte_identical
#   call: self::test_replays_byte_identical
#   mutates: none
#   cleanup: none
#
# id: check_subatomic_gonol_keeps_layers_distinct
#   proves: subatomic_gonol_keeps_layers_distinct
#   call: self::test_keeps_layers_distinct
#   mutates: none
#   cleanup: none
#
# id: check_subatomic_gonol_invents_no_geometry
#   proves: subatomic_gonol_invents_no_geometry
#   call: self::test_invents_no_geometry
#   mutates: none
#   cleanup: none
#
# id: check_subatomic_gonol_stays_cross_domain_hypothesis
#   proves: subatomic_gonol_stays_cross_domain_hypothesis
#   call: self::test_stays_cross_domain_hypothesis
#   mutates: none
#   cleanup: none
# === END CHECKS ===

import subatomic_gonol as m
from extended_atomic import atomic_record


def _receipts():
    return {symbol: m.construct_subatomic_gonol(symbol) for symbol in m.SUPPORTED_SYMBOLS}


def test_combines_three_sources():
    for symbol, receipt in _receipts().items():
        carried = dict(receipt.gonol.carried_options)
        nucleus_carried = dict(receipt.gonol.participants[0].carried_options)
        # Subatomic identity fields live on the nucleus participant.
        assert "proton-positions" in nucleus_carried
        assert "proton-glyphs" in nucleus_carried
        assert "mobius-t0-frame" in nucleus_carried
        assert "mobius-t2-frame" in nucleus_carried
        # Harmonic relation results live on the nucleus participant for the
        # elements that participate in the declared nuclear candidates.
        if symbol in {"H", "He", "Li", "C"}:
            assert any(key.startswith("harmonic:") for key in nucleus_carried)
        # Quantum-layer fields live on the element gonol.
        assert carried["electron-configuration"] == atomic_record(int(carried["Z"])).configuration
        assert "valence-electrons" in carried
        assert "harmonic-surviving" in carried


def test_replays_byte_identical():
    for symbol, receipt in _receipts().items():
        assert m.replay_subatomic_gonol(receipt) == receipt.receipt_digest
        assert len(receipt.receipt_digest) == 64
    digests = {r.receipt_digest for r in _receipts().values()}
    assert len(digests) == len(m.SUPPORTED_SYMBOLS)


def test_keeps_layers_distinct():
    for symbol, receipt in _receipts().items():
        kinds = [
            "nucleus" if "nucleus" in p.source_id else "shell"
            for p in receipt.gonol.participants
        ]
        assert kinds[0] == "nucleus"
        assert all(kind == "shell" for kind in kinds[1:])
        assert len(kinds) >= 2  # nucleus + at least one shell
        # Electron shells are individually addressable, not flattened.
        for participant in receipt.gonol.participants[1:]:
            assert "shell" in participant.source_id


def test_invents_no_geometry():
    source = open(m.__file__, encoding="utf-8").read()
    # The module consumes epac.public_gonol; it must not define position operations
    # and must not import the EDCM text-domain constructor.
    assert "def " + "public_gonol" not in source
    assert "from edcm" not in source
    assert "import edcm" not in source
    assert "advance(" not in source
    assert "NativeMobius" not in source
    receipt = m.construct_subatomic_gonol("H")
    assert receipt.constructor_id == "epac.public_gonol"
    assert receipt.gonol.geometry_digest


def test_stays_cross_domain_hypothesis():
    for symbol, receipt in _receipts().items():
        assert receipt.standing == "implemented-candidate"
        assert receipt.selection_effect == "none"
        assert dict(receipt.gonol.carried_options)["status"] == "CROSS-DOMAIN-HYPOTHESIS"
        assert receipt.nonclaims
        assert receipt.hmmm


def test_imports_do_not_mutate_sys_path():
    source = open(m.__file__, encoding="utf-8").read()
    assert "sys.path" not in source


def test_harmonic_survival_is_symbol_specific():
    surviving = {
        symbol: dict(m.construct_subatomic_gonol(symbol).gonol.carried_options)[
            "harmonic-surviving"
        ]
        for symbol in ("H", "He", "Li", "C")
    }
    assert surviving["H"] == "none"
    assert surviving["He"] == "none"
    assert surviving["Li"] == "alpha_cluster_recurrence"
    assert "proton_neutron_inversion_symmetry" in surviving["C"]
