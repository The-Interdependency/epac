"""Atomic and subatomic structure used by element gonols.

Nothing here is molecular. Electrons are filled by Aufbau, Pauli, and Hund.
Angular identities are hydrogenic spherical harmonics labeled by (n, l, m_l).
Screening is Slater's atomic Z_eff. Energies are hydrogenic Rydberg units
with that Z_eff. Nucleus instances are default isotopes, identity only.

Do not import the sealed molecular comparison file from this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


SUBSHELL_ORDER: tuple[tuple[int, int], ...] = (
    (1, 0),
    (2, 0),
    (2, 1),
    (3, 0),
    (3, 1),
)

ISOTOPE_DEFAULTS: dict[int, int] = {
    1: 1,
    2: 4,
    3: 7,
    4: 9,
    5: 11,
    6: 12,
    7: 14,
    8: 16,
    9: 19,
    10: 20,
    11: 23,
    12: 24,
    13: 27,
    14: 28,
    15: 31,
    16: 32,
    17: 35,
    18: 40,
}

SYMBOLS: tuple[str, ...] = (
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
)


@dataclass(frozen=True, slots=True)
class ElectronState:
    """One electron in an atom: quantum numbers plus atomic wave labels."""

    index: int
    n: int
    l: int
    m_l: int
    m_s: int
    shell: str
    subshell: str
    angular_id: str
    radial_nodes: int
    z_eff: str
    e_rydberg: str
    valence: bool
    paired: bool


@dataclass(frozen=True, slots=True)
class AtomicRecord:
    Z: int
    symbol: str
    period: int
    group: int
    A: int
    proton_count: int
    neutron_count: int
    electrons: tuple[ElectronState, ...]
    configuration: str
    valence_n: int
    valence_electrons: int
    unpaired_valence: tuple[ElectronState, ...]
    promoted_unpaired_valence: tuple[ElectronState, ...]


def _period_group(Z: int) -> tuple[int, int]:
    if Z == 1:
        return 1, 1
    if Z == 2:
        return 1, 18
    if Z <= 4:
        return 2, Z - 2
    if Z <= 10:
        return 2, Z + 8
    if Z <= 12:
        return 3, Z - 10
    return 3, Z


def _ml_down(l: int) -> tuple[int, ...]:
    return tuple(range(l, -l - 1, -1))


def _subshell_name(n: int, l: int) -> str:
    return f"{n}{'spdf'[l]}"


def _angular_id(l: int, m_l: int) -> str:
    return f"Y_l{l}_m{m_l}"


def _slater_zeff(Z: int, n: int, l: int, occupied: tuple[tuple[int, int], ...]) -> float:
    """Slater screening for one electron in subshell (n, l)."""

    others = list(occupied)
    others.remove((n, l))
    sigma = 0.0
    same_group = 0
    for on, ol in others:
        if n == 1 and l == 0:
            if on == 1 and ol == 0:
                sigma += 0.30
            continue
        if on == n and ((l in {0, 1} and ol in {0, 1}) or ol == l):
            same_group += 1
        elif on == n - 1:
            sigma += 0.85
        elif on <= n - 2:
            sigma += 1.00
    sigma += 0.35 * same_group
    return round(Z - sigma, 3)


def _fill_electrons(Z: int) -> tuple[ElectronState, ...]:
    remaining = Z
    occupied_pairs: list[tuple[int, int]] = []
    raw: list[tuple[int, int, int, int]] = []
    for n, l in SUBSHELL_ORDER:
        capacity = 2 * (2 * l + 1)
        take = min(remaining, capacity)
        slots = [(m_l, 1) for m_l in _ml_down(l)] + [(m_l, -1) for m_l in _ml_down(l)]
        for m_l, m_s in slots[:take]:
            raw.append((n, l, m_l, m_s))
            occupied_pairs.append((n, l))
        remaining -= take
        if remaining == 0:
            break
    valence_n = max(n for n, _l, _ml, _ms in raw)
    occupied = tuple(occupied_pairs)
    electrons: list[ElectronState] = []
    occupancy: dict[tuple[int, int, int], int] = {}
    for n, l, m_l, m_s in raw:
        occupancy[(n, l, m_l)] = occupancy.get((n, l, m_l), 0) + 1
    seen: dict[tuple[int, int, int], int] = {}
    for index, (n, l, m_l, m_s) in enumerate(raw):
        seen[(n, l, m_l)] = seen.get((n, l, m_l), 0) + 1
        z_eff = _slater_zeff(Z, n, l, occupied)
        energy = round(-(z_eff ** 2) / (n ** 2), 6)
        electrons.append(
            ElectronState(
                index=index,
                n=n,
                l=l,
                m_l=m_l,
                m_s=m_s,
                shell=f"n{n}",
                subshell=_subshell_name(n, l),
                angular_id=_angular_id(l, m_l),
                radial_nodes=n - l - 1,
                z_eff=str(z_eff),
                e_rydberg=str(energy),
                valence=(n == valence_n),
                paired=occupancy[(n, l, m_l)] == 2,
            )
        )
    return tuple(electrons)


def _configuration(electrons: tuple[ElectronState, ...]) -> str:
    counts: dict[str, int] = {}
    order: list[str] = []
    for electron in electrons:
        name = electron.subshell
        if name not in counts:
            order.append(name)
            counts[name] = 0
        counts[name] += 1
    return ".".join(f"{name}{counts[name]}" for name in order)


def _unpaired_valence(electrons: tuple[ElectronState, ...]) -> tuple[ElectronState, ...]:
    return tuple(e for e in electrons if e.valence and not e.paired and e.m_s == 1)


def _promoted_unpaired(electrons: tuple[ElectronState, ...]) -> tuple[ElectronState, ...]:
    """Atomic valence promotion: move valence s pair into empty valence p to unpair.

    This is an atomic excited configuration (same n). It is not a molecular hybrid.
    """

    unpaired = list(_unpaired_valence(electrons))
    valence = [e for e in electrons if e.valence]
    valence_n = valence[0].n if valence else 1
    if valence_n < 2:
        return tuple(unpaired)
    p_occupied_m = {e.m_l for e in valence if e.l == 1}
    empty_p_m = [m for m in _ml_down(1) if m not in p_occupied_m]
    s_pairs_by_orbital: dict[tuple[int, int, int], list[ElectronState]] = {}
    for electron in valence:
        if electron.l == 0 and electron.paired:
            s_pairs_by_orbital.setdefault((electron.n, electron.l, electron.m_l), []).append(electron)
    s_pair = next((pair for pair in s_pairs_by_orbital.values() if len(pair) == 2), None)
    if s_pair is None or not empty_p_m:
        return tuple(unpaired)
    # Promote the spin-down valence s electron into the first empty valence p
    # and flip it to spin-up. The spin-up s electron stays behind, so every
    # promoted unpaired electron carries m_s = +1, matching the ground-state
    # unpaired convention used by _unpaired_valence.
    promoted_from_s = next((item for item in s_pair if item.m_s == -1), s_pair[0])
    remaining_s = next(item for item in s_pair if item.index != promoted_from_s.index)
    new_p = ElectronState(
        index=promoted_from_s.index,
        n=valence_n,
        l=1,
        m_l=empty_p_m[0],
        m_s=1,
        shell=f"n{valence_n}",
        subshell=_subshell_name(valence_n, 1),
        angular_id=_angular_id(1, empty_p_m[0]),
        radial_nodes=valence_n - 2,
        z_eff=promoted_from_s.z_eff,
        e_rydberg=promoted_from_s.e_rydberg,
        valence=True,
        paired=False,
    )
    unpaired_s = ElectronState(
        index=remaining_s.index,
        n=remaining_s.n,
        l=0,
        m_l=remaining_s.m_l,
        m_s=remaining_s.m_s,
        shell=remaining_s.shell,
        subshell=remaining_s.subshell,
        angular_id=remaining_s.angular_id,
        radial_nodes=remaining_s.radial_nodes,
        z_eff=remaining_s.z_eff,
        e_rydberg=remaining_s.e_rydberg,
        valence=True,
        paired=False,
    )
    promoted = [unpaired_s, new_p, *[e for e in unpaired if e.l != 0]]
    # Canonical subshell ordering: s before p, p orbitals by ascending m_l.
    promoted.sort(key=lambda electron: (electron.l, electron.m_l))
    return tuple(promoted)


def atomic_record(Z: int) -> AtomicRecord:
    if not 1 <= Z <= 18:
        raise ValueError("this candidate table is Z=1-18")
    electrons = _fill_electrons(Z)
    valence_n = max(e.n for e in electrons)
    period, group = _period_group(Z)
    A = ISOTOPE_DEFAULTS[Z]
    return AtomicRecord(
        Z=Z,
        symbol=SYMBOLS[Z - 1],
        period=period,
        group=group,
        A=A,
        proton_count=Z,
        neutron_count=A - Z,
        electrons=electrons,
        configuration=_configuration(electrons),
        valence_n=valence_n,
        valence_electrons=sum(1 for e in electrons if e.valence),
        unpaired_valence=_unpaired_valence(electrons),
        promoted_unpaired_valence=_promoted_unpaired(electrons),
    )


def iter_table() -> Iterator[AtomicRecord]:
    for Z in range(1, 19):
        yield atomic_record(Z)
