"""Extended atomic quantum layer Z=1..26 for subatomic gonols.

Delegates Z<=18 to ``epac_atomic`` (byte-identical electron records, so
existing H/He/Li/C receipts do not move). Adds Z=19..26 from declared
ground-state configurations with a standard Aufbau extension through 4s/3d and
a Slater-screening extension for d electrons.

Candidate rules declared here (consistent with the sibling ``epac_atomic``):

- valence electrons are those with ``n == max occupied n``;
- angular identities are hydrogenic ``Y_l{l}_m{m_l}`` labels;
- Slater screening: same-shell 0.35 (same-group), n-1 shell 0.85, deeper 1.00;
  for d electrons (l=2) all inner shells count 1.00.

Status: application-layer candidate data. Not physics canon.

Usage guidance:

    from extended_atomic import atomic_record, iter_table

    iron = atomic_record(26)
    print(iron.symbol, iron.configuration)
"""

# === MODULE_BUILD ===
# id: epac_subatomic_extended_atomic
#   module_name: extended_atomic
#   module_kind: schema
#   summary: atomic quantum-layer records Z=1..26 for subatomic gonols; Z<=18 delegates to epac_atomic, Z=19..26 from declared ground-state configurations with Aufbau/Slater extension
#   owner: The Interdependency
#   public_surface: EXTENDED_SYMBOLS, SYMBOL_TO_Z, atomic_record, iter_table
#   internal_surface: _config_occupancy, _fill_from_config, _slater_zeff_extended
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: subatomic.test_extended_atomic
#   rollout: local candidate module under stack/research/epac/subatomic/
#   rollback: remove module; subatomic_gonol returns to Z<=18 epac_atomic delegation
#   requires: epac_atomic
#   since: 2026-08-22
#   unresolved: configurations beyond Z=26; full f-block Aufbau; Slater rules are candidate extensions, not exact physics
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: extended_atomic_preserves_z_le_18
#   given: atomic_record(Z) for 1 <= Z <= 18
#   then: the record is byte-identical to epac_atomic.atomic_record(Z)
#   class: correctness
#
# id: extended_atomic_uses_declared_configurations
#   given: atomic_record(Z) for 19 <= Z <= 26
#   then: electron occupancy matches the declared ground-state configuration, including the Cr 4s1.3d5 exception
#   class: correctness
#
# id: extended_atomic_stays_candidate
#   given: any extended record
#   then: values are candidate application-layer data, not physics validation
#   class: doctrine
# === END CONTRACTS ===

from __future__ import annotations

from epac_atomic import (
    AtomicRecord,
    ElectronState,
    atomic_record as base_atomic_record,
)

EXTENDED_SYMBOLS: tuple[str, ...] = (
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe",
)
SYMBOL_TO_Z: dict[str, int] = {symbol: index + 1 for index, symbol in enumerate(EXTENDED_SYMBOLS)}

ISOTOPE_DEFAULTS_19_26: dict[int, int] = {
    19: 39, 20: 40, 21: 45, 22: 48, 23: 51, 24: 52, 25: 55, 26: 56,
}

PERIOD_GROUP_19_26: dict[int, tuple[int, int]] = {
    19: (4, 1), 20: (4, 2), 21: (4, 3), 22: (4, 4),
    23: (4, 5), 24: (4, 6), 25: (4, 7), 26: (4, 8),
}

# Declared ground-state configurations (standard Aufbau with the Cr exception).
CONFIGURATIONS_19_26: dict[int, str] = {
    19: "1s2.2s2.2p6.3s2.3p6.4s1",
    20: "1s2.2s2.2p6.3s2.3p6.4s2",
    21: "1s2.2s2.2p6.3s2.3p6.4s2.3d1",
    22: "1s2.2s2.2p6.3s2.3p6.4s2.3d2",
    23: "1s2.2s2.2p6.3s2.3p6.4s2.3d3",
    24: "1s2.2s2.2p6.3s2.3p6.4s1.3d5",
    25: "1s2.2s2.2p6.3s2.3p6.4s2.3d5",
    26: "1s2.2s2.2p6.3s2.3p6.4s2.3d6",
}

_SUBSHELL_NAME = "spdf"


def _ml_down(l: int) -> tuple[int, ...]:
    return tuple(range(l, -l - 1, -1))


def _config_occupancy(config: str) -> list[tuple[int, int, int]]:
    """Parse ``1s2.2s2...`` into ordered (n, l, count) entries."""
    entries: list[tuple[int, int, int]] = []
    for part in config.split("."):
        part = part.strip()
        n = int(part[0])
        l = _SUBSHELL_NAME.index(part[1])
        count = int(part[2:])
        entries.append((n, l, count))
    return entries


def _slater_zeff_extended(
    Z: int, n: int, l: int, occupied: tuple[tuple[int, int], ...]
) -> float:
    """Slater screening, extended for 4s/3d while matching epac_atomic for l<=1."""
    others = list(occupied)
    others.remove((n, l))
    sigma = 0.0
    same_group = 0
    for on, ol in others:
        if n == 1 and l == 0:
            if on == 1 and ol == 0:
                sigma += 0.30
            continue
        if l == 2:
            # d electron: same subshell 0.35, all inner shells 1.00.
            if on == n and ol == l:
                same_group += 1
            elif on < n:
                sigma += 1.00
            continue
        if on == n and ((l in {0, 1} and ol in {0, 1}) or ol == l):
            same_group += 1
        elif on == n - 1:
            sigma += 0.85
        elif on <= n - 2:
            sigma += 1.00
    sigma += 0.35 * same_group
    return round(Z - sigma, 3)


def _fill_from_config(Z: int, config: str) -> tuple[ElectronState, ...]:
    occupancy = _config_occupancy(config)
    raw: list[tuple[int, int, int, int]] = []
    occupied_pairs: list[tuple[int, int]] = []
    for n, l, count in occupancy:
        slots = [(m_l, 1) for m_l in _ml_down(l)] + [(m_l, -1) for m_l in _ml_down(l)]
        for m_l, m_s in slots[:count]:
            raw.append((n, l, m_l, m_s))
            occupied_pairs.append((n, l))
    valence_n = max(n for n, _l, _ml, _ms in raw)
    occupied = tuple(occupied_pairs)
    occupancy_counts: dict[tuple[int, int, int], int] = {}
    for n, l, m_l, _m_s in raw:
        key = (n, l, m_l)
        occupancy_counts[key] = occupancy_counts.get(key, 0) + 1
    electrons: list[ElectronState] = []
    for index, (n, l, m_l, m_s) in enumerate(raw):
        z_eff = _slater_zeff_extended(Z, n, l, occupied)
        energy = round(-(z_eff**2) / (n**2), 6)
        electrons.append(
            ElectronState(
                index=index,
                n=n,
                l=l,
                m_l=m_l,
                m_s=m_s,
                shell=f"n{n}",
                subshell=f"{n}{_SUBSHELL_NAME[l]}",
                angular_id=f"Y_l{l}_m{m_l}",
                radial_nodes=n - l - 1,
                z_eff=str(z_eff),
                e_rydberg=str(energy),
                valence=(n == valence_n),
                paired=occupancy_counts[(n, l, m_l)] == 2,
            )
        )
    return tuple(electrons)


def _configuration_string(electrons: tuple[ElectronState, ...]) -> str:
    counts: dict[str, int] = {}
    order: list[str] = []
    for electron in electrons:
        name = electron.subshell
        if name not in counts:
            order.append(name)
            counts[name] = 0
        counts[name] += 1
    return ".".join(f"{name}{counts[name]}" for name in order)


def atomic_record(Z: int) -> AtomicRecord:
    if not 1 <= Z <= 26:
        raise ValueError("extended atomic table is Z=1..26")
    if Z <= 18:
        return base_atomic_record(Z)
    electrons = _fill_from_config(Z, CONFIGURATIONS_19_26[Z])
    period, group = PERIOD_GROUP_19_26[Z]
    A = ISOTOPE_DEFAULTS_19_26[Z]
    unpaired = tuple(e for e in electrons if e.valence and not e.paired and e.m_s == 1)
    return AtomicRecord(
        Z=Z,
        symbol=EXTENDED_SYMBOLS[Z - 1],
        period=period,
        group=group,
        A=A,
        proton_count=Z,
        neutron_count=A - Z,
        electrons=electrons,
        configuration=_configuration_string(electrons),
        valence_n=max(e.n for e in electrons),
        valence_electrons=sum(1 for e in electrons if e.valence),
        unpaired_valence=unpaired,
        promoted_unpaired_valence=(),
    )


def iter_table():
    for Z in range(1, 27):
        yield atomic_record(Z)


__all__ = [
    "EXTENDED_SYMBOLS",
    "ISOTOPE_DEFAULTS_19_26",
    "SYMBOL_TO_Z",
    "atomic_record",
    "iter_table",
]
