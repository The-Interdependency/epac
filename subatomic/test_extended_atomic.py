"""Executable witnesses for the extended atomic quantum layer Z=1..26."""

# === CHECKS ===
# id: check_extended_atomic_preserves_z_le_18
#   proves: extended_atomic_preserves_z_le_18
#   call: self::test_extended_atomic_preserves_z_le_18
#   mutates: none
#   cleanup: none
#
# id: check_extended_atomic_uses_declared_configurations
#   proves: extended_atomic_uses_declared_configurations
#   call: self::test_extended_atomic_uses_declared_configurations
#   mutates: none
#   cleanup: none
#
# id: check_extended_atomic_stays_candidate
#   proves: extended_atomic_stays_candidate
#   call: self::test_extended_atomic_stays_candidate
#   mutates: none
#   cleanup: none
# === END CHECKS ===

import epac_atomic
import extended_atomic as m


def test_extended_atomic_preserves_z_le_18():
    for Z in range(1, 19):
        assert m.atomic_record(Z) == epac_atomic.atomic_record(Z)


def test_extended_atomic_uses_declared_configurations():
    iron = m.atomic_record(26)
    assert iron.symbol == "Fe"
    assert iron.Z == 26
    assert iron.A == 56
    assert iron.configuration == "1s2.2s2.2p6.3s2.3p6.4s2.3d6"
    assert sum(1 for e in iron.electrons) == 26

    chromium = m.atomic_record(24)
    assert chromium.configuration == "1s2.2s2.2p6.3s2.3p6.4s1.3d5"

    potassium = m.atomic_record(19)
    assert potassium.configuration == "1s2.2s2.2p6.3s2.3p6.4s1"
    assert potassium.symbol == "K"

    assert m.SYMBOL_TO_Z["Fe"] == 26
    assert m.EXTENDED_SYMBOLS[25] == "Fe"
    assert len(m.EXTENDED_SYMBOLS) == 26


def test_extended_atomic_stays_candidate():
    record = m.atomic_record(26)
    # Candidate data is complete but carries no physics-validation claim.
    for electron in record.electrons:
        assert electron.n >= 1
        assert electron.z_eff
        assert electron.e_rydberg


def test_extended_atomic_does_not_mutate_sys_path():
    source = open(m.__file__, encoding="utf-8").read()
    assert "sys.path" not in source
