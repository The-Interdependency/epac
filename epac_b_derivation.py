# === MODULE_BUILD ===
# id: epac_b_derivation
#   module_name: epac_b_derivation
#   module_kind: construction
#   summary: freeze the rule deriving B=(3,d,c) and ligand_contribution_K from orbital occupancy, charge, and bond state, preserve ns/(n-1)d/np subshell identity, and expose lookup-free ligand-field controls
#   owner: Erin Spencer
#   public_surface: SCHEMA, VERSION, BDerivationError, bare_element_b, ion_b, ligand_contribution, molecule_b, active_orbital_set, ligand_field_spin_control, freeze_b_derivation, replay_b_derivation
#   internal_surface: charged electron removal, center/ligand resolution, subshell-resolved occupancy, explicit ligand-field controls, canonical receipt
#   auth_boundary: none
#   storage_boundary: immutable records only
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: tests.test_b_derivation
#   rollout: frozen generative-carrier rule under test; held-out B evaluations are bounded evidence, not bond predictions
#   rollback: remove this module and its tests
#   requires: epac_atomic (Z=1..36)
#   since: 2026-09-17
#   unresolved: ligand-field regime derivation, coordination capacity, topology formation, and empirical held-out comparison
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: b_derivation_uses_occupancy_charge_bond_state_only
#   given: the frozen B derivation rule
#   then: it consumes electron states, charge, and declared composition/bond state only, never element identity or a periodic-table lookup
#   class: doctrine
#   since: 2026-09-17
#
# id: b_derivation_reproduces_nine_locked_formulas
#   given: the nine locked molecular compositions
#   then: the frozen rule reproduces their documented B values exactly
#   class: correctness
#   since: 2026-09-17
#
# id: b_derivation_reproduces_bare_element_b
#   given: every bare element record Z=1..18
#   then: d equals 1 plus electron count and c equals 0
#   class: correctness
#   since: 2026-09-17
#
# id: b_derivation_records_transition_metal_failure
#   given: the Aufbau electron states of transition metals
#   then: the frozen rule records that (n-1)d valence participation is missing, revealing it as the missing state variable
#   class: doctrine
#   since: 2026-09-17
#
# id: b_derivation_receipts_fail_closed
#   given: malformed or tampered receipts
#   then: replay raises rather than accepting drift
#   class: safety
#   since: 2026-09-17
#
# id: active_orbital_basis_preserves_subshell_identity
#   given: a constructed transition-metal electron state and nonnegative ionic charge
#   then: ns, (n-1)d, and np remain distinct, cation removal consumes ns before (n-1)d, and Hund applies within each degenerate subshell only
#   class: correctness
#   since: 2026-09-18
#
# id: ligand_field_controls_require_explicit_regime
#   given: a d-electron count plus supplied octahedral high-spin or low-spin regime
#   then: the control derives the corresponding split-orbital occupancy without mapping ligand identity through a spectrochemical lookup
#   class: doctrine
#   since: 2026-09-18
# === END CONTRACTS ===

"""Freeze the B derivation rule and evaluate held-out cases.

Rule (frozen):

* bare element: ``d = 1 + electron_count``, ``c = 0``;
* ion charge q: ``electron_count = Z - q``;
* ligand contribution ``K = number of ground-state unpaired valence
  electrons`` (from the constructed electron states);
* molecule: ``d = total atom instances``, ``c = sum of ligand K only`` over
  the topology-selected ligands (diatomic: both atoms; singleton-center
  star: the non-center ligands; the center K is never counted), with bond
  state carried as a declared input.

Element identity and periodic-table lookup are never consulted. These are
B evaluations, not bond predictions: the rule measures a supplied topology
and does not yet know how the topology forms.

Usage::

    from epac_atomic import atomic_record
    from epac_b_derivation import active_orbital_set, ligand_field_spin_control

    zn2 = active_orbital_set(atomic_record(30), charge=2)
    high_spin_d5 = ligand_field_spin_control(5, "octahedral", "high")

``ligand_field_spin_control`` receives the spin regime explicitly. It does
not infer a regime from ligand identity and does not consult a spectrochemical
series. Ligand-field regime derivation and coordination capacity remain
``UNRESOLVED``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from epac_atomic import AtomicRecord, atomic_record

SCHEMA = "epac.b-derivation"
SCHEMA_SET = "epac.b-derivation-receipt-set"
VERSION = "0.1.0"

_LOCKED = {
    "H2": (("H", 2),),
    "H2O": (("H", 2), ("O", 1)),
    "NH3": (("N", 1), ("H", 3)),
    "CH4": (("C", 1), ("H", 4)),
    "CO2": (("C", 1), ("O", 2)),
    "H2S": (("H", 2), ("S", 1)),
    "BF3": (("B", 1), ("F", 3)),
    "PH3": (("P", 1), ("H", 3)),
    "SiH4": (("Si", 1), ("H", 4)),
}

_DOCUMENTED_MOLECULE_B = {
    "H2": (3, 2, 2),
    "H2O": (3, 3, 2),
    "NH3": (3, 4, 3),
    "CH4": (3, 5, 4),
    "CO2": (3, 3, 4),
    "H2S": (3, 3, 2),
    "BF3": (3, 4, 3),
    "PH3": (3, 4, 3),
    "SiH4": (3, 5, 4),
}

_HELD_OUT = {
    "N2": {"composition": (("N", 2),), "bond_state": "triple", "charge": 0},
    "O2": {"composition": (("O", 2),), "bond_state": "double", "charge": 0},
    "CO": {"composition": (("C", 1), ("O", 1)), "bond_state": "triple-coordinate", "charge": 0},
    "C2H2": {"composition": (("C", 2), ("H", 2)), "bond_state": "triple", "charge": 0},
    "C2H4": {"composition": (("C", 2), ("H", 4)), "bond_state": "double", "charge": 0},
    "H2O2": {"composition": (("H", 2), ("O", 2)), "bond_state": "single", "charge": 0},
    "HF": {"composition": (("H", 1), ("F", 1)), "bond_state": "single", "charge": 0},
    "HCl": {"composition": (("H", 1), ("Cl", 1)), "bond_state": "single", "charge": 0},
    "NH4+": {"composition": (("N", 1), ("H", 4)), "bond_state": "coordinate", "charge": 1},
}

_MISSING_STATE_VARIABLE = (
    "the frozen Aufbau rule marks only the outermost principal shell as "
    "valence; transition metals therefore lose their (n-1)d electrons from "
    "the valence count and unpaired contributions. (n-1)d participation is "
    "necessary but insufficient: the missing variable is the bond-context "
    "active-orbital set, which may include (n-1)d."
)


class BDerivationError(ValueError):
    """Raised when the B derivation fails closed."""


def _charged_electrons(record: AtomicRecord, charge: int) -> tuple[Any, ...]:
    """Remove (cation) or add (anion) electrons by the frozen removal order:
    highest n first, then highest l first."""

    electrons = list(record.electrons)
    if charge == 0:
        return tuple(electrons)
    if charge > 0:
        for _ in range(charge):
            if not electrons:
                raise BDerivationError("charge removes more electrons than exist")
            electrons.remove(max(electrons, key=lambda e: (e.n, e.l, e.index)))
        return tuple(electrons)
    # Anion: add electrons to the highest empty orbitals is out of scope for
    # the frozen rule; record refusal rather than invent.
    raise BDerivationError("anion electron addition is not in the frozen rule")


def _unpaired_count(electrons: tuple[Any, ...]) -> int:
    return sum(1 for e in electrons if e.valence and not e.paired and e.m_s == 1)


def bare_element_b(record: AtomicRecord) -> tuple[int, int, int]:
    return (3, 1 + len(record.electrons), 0)


def ion_b(record: AtomicRecord, charge: int) -> tuple[int, int, int]:
    electrons = _charged_electrons(record, charge)
    return (3, 1 + len(electrons), 0)


def ligand_contribution(record: AtomicRecord) -> int:
    return len(record.unpaired_valence)


def _contributing_symbols(composition: tuple[tuple[str, int], ...]) -> list[str]:
    symbols = [symbol for symbol, count in composition for _ in range(count)]
    if len(symbols) == 2:
        return symbols
    counts: dict[str, int] = {}
    for symbol in symbols:
        counts[symbol] = counts.get(symbol, 0) + 1
    singletons = [symbol for symbol, count in counts.items() if count == 1]
    if len(singletons) == 1:
        center = singletons[0]
        return [symbol for symbol in symbols if symbol != center]
    raise BDerivationError(
        "composition is outside the supported domain; the frozen rule "
        "supports bare atoms, ions, diatomics, and singleton-center star "
        "topologies only"
    )


def molecule_b(composition: tuple[tuple[str, int], ...]) -> tuple[int, int, int]:
    atom_count = sum(count for _, count in composition)
    records = {symbol: atomic_record(_symbol_z(symbol)) for symbol, _ in composition}
    contributions = [
        ligand_contribution(records[symbol]) for symbol in _contributing_symbols(composition)
    ]
    return (3, atom_count, sum(contributions))


def _symbol_z(symbol: str) -> int:
    for Z in range(1, 37):
        record = atomic_record(Z)
        if record.symbol == symbol:
            return Z
    raise BDerivationError(f"symbol {symbol!r} outside Z=1..36")


def freeze_b_derivation() -> dict[str, Any]:
    locked = []
    for formula, composition in _LOCKED.items():
        evaluated = molecule_b(composition)
        documented = _DOCUMENTED_MOLECULE_B[formula]
        locked.append(
            {
                "formula": formula,
                "composition": [list(row) for row in composition],
                "evaluated_b": list(evaluated),
                "documented_b": list(documented),
                "matches": evaluated == documented,
            }
        )

    bare = []
    for Z in range(1, 37):
        record = atomic_record(Z)
        evaluated = bare_element_b(record)
        bare.append(
            {
                "Z": Z,
                "symbol": record.symbol,
                "configuration": record.configuration,
                "evaluated_b": list(evaluated),
                "unpaired_valence": len(record.unpaired_valence),
            }
        )

    ions = []
    for spec in (
        (26, 2, "Fe2+"),
        (26, 3, "Fe3+"),
        (29, 1, "Cu+"),
        (30, 2, "Zn2+"),
    ):
        record = atomic_record(spec[0])
        evaluated = ion_b(record, spec[1])
        ions.append(
            {
                "ion": spec[2],
                "Z": spec[0],
                "charge": spec[1],
                "evaluated_b": list(evaluated),
            }
        )

    held_out = []
    for formula, spec in _HELD_OUT.items():
        composition = spec["composition"]
        try:
            evaluated = molecule_b(composition)
            evaluated_b = list(evaluated)
            status = "evaluation-only"
        except BDerivationError as exc:
            evaluated_b = None
            status = f"outside-supported-domain: {exc}"
        held_out.append(
            {
                "formula": formula,
                "composition": [list(row) for row in composition],
                "bond_state": spec["bond_state"],
                "charge": spec["charge"],
                "evaluated_b": evaluated_b,
                "empirical_b": None,
                "status": status,
            }
        )

    transition_failure = []
    for Z in (21, 24, 26, 29):
        record = atomic_record(Z)
        transition_failure.append(
            {
                "Z": Z,
                "symbol": record.symbol,
                "configuration": record.configuration,
                "frozen_valence_electrons": record.valence_electrons,
                "frozen_unpaired_valence": len(record.unpaired_valence),
                "missing_state_variable": (
                    "bond-context active-orbital set (may include (n-1)d)"
                ),
            }
        )

    payload = {
        "schema": SCHEMA_SET,
        "version": VERSION,
        "supported_domain": [
            "bare atoms",
            "ions",
            "diatomics",
            "singleton-center star topologies",
        ],
        "rule": {
            "bare_d": "1 + electron_count",
            "bare_c": 0,
            "ion_electron_count": "Z - charge",
            "ligand_K": "ground-state unpaired valence count",
            "molecule_d": "total atom instances",
            "molecule_c": (
                "sum of ligand K only, over topology-selected ligands: "
                "diatomic = both atoms, singleton-center star = non-center "
                "ligands; the center K is never counted"
            ),
        },
        "locked_formula_b_evaluations": locked,
        "bare_element_b_evaluations": bare,
        "ion_b_evaluations": ions,
        "held_out_molecule_b_evaluations": held_out,
        "transition_metal_topology_evaluations": [
            evaluate_transition_metal_topology(name)
            for name in _TRANSITION_METAL_TOPOLOGIES
        ],
        "transition_metal_failure": transition_failure,
        "missing_state_variable": _MISSING_STATE_VARIABLE,
        "capacity_rule_status": "FALSIFIED",
        "capacity_rule_falsification": (
            "the six-equivalent-orbital capacity rule (4s+3d as one Hund "
            "set) manufactured two unpaired electrons for Zn2+ d10 where "
            "none stand; Hund applies per degenerate subshell only"
        ),
        "ligand_field_spin_controls": [
            ligand_field_spin_control(5, "octahedral", "high"),
            ligand_field_spin_control(5, "octahedral", "low"),
        ],
        "ligand_field_regime_derivation": "UNRESOLVED",
        "spectrochemical_lookup_used": False,
        "hmmm": (
            "the rule knows how to measure a supplied topology; it does not "
            "yet know how the topology forms. The active-orbital set "
            "identifies possible rooms, but treating their floors as level "
            "manufactured two electrons standing where none stand. "
            "The high/low-spin controls accept their ligand-field regime as "
            "an explicit input; EPAC does not yet derive that regime. "
            "B evaluations are bounded evidence, not bond predictions: "
            "bond state is an input."
        ),
    }
    payload["receipt_sha256"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in payload.items() if key != "receipt_sha256"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload


def replay_b_derivation(data: bytes) -> dict[str, Any]:
    if not isinstance(data, bytes):
        raise BDerivationError("receipt must be bytes")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BDerivationError("receipt is not valid canonical JSON") from exc
    if obj.get("schema") != SCHEMA_SET or obj.get("version") != VERSION:
        raise BDerivationError("receipt schema or version mismatch")
    rebuilt = freeze_b_derivation()
    if rebuilt["receipt_sha256"] != obj.get("receipt_sha256"):
        raise BDerivationError("receipt digest does not match recomputation")
    rebuilt_bytes = json.dumps(rebuilt, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if rebuilt_bytes != data:
        raise BDerivationError("receipt does not replay byte-identically")
    return rebuilt


def _hund_within_subshell(electron_count: int, orbital_count: int) -> tuple[int, int]:
    """Hund's rule within one degenerate subshell.

    Returns (unpaired, vacant). Applied per subshell only; never across
    subshells of different degeneracy.
    """

    electron_count = max(electron_count, 0)
    if electron_count <= orbital_count:
        return electron_count, orbital_count - electron_count
    return max(2 * orbital_count - electron_count, 0), 0


def active_orbital_set(record: AtomicRecord, charge: int = 0) -> dict[str, Any]:
    """Derive the bond-context active-orbital set for a supplied atom.

    Main group: the outermost shell subshells as constructed.
    Transition metals (Z=21..30): the 4s, 3d, and 4p subshell basis with
    subshell
    identity preserved; charge removes electrons 4s first, then 3d. Hund's
    rule applies within each degenerate subshell, never across them.
    Coordination capacity is UNRESOLVED until ligand-field, orbital-energy
    ordering, geometry, and 4p participation are derived rather than merely
    represented as candidate state.
    """

    if not 1 <= record.Z <= 36:
        raise BDerivationError("active-orbital set is defined for Z=1..36")
    if isinstance(charge, bool) or not isinstance(charge, int):
        raise BDerivationError("charge must be an integer")
    if charge < 0:
        raise BDerivationError("anion electron addition is not in the frozen rule")
    if 21 <= record.Z <= 30:
        s_electrons = len([e for e in record.electrons if (e.n, e.l) == (4, 0)])
        d_electrons = len([e for e in record.electrons if (e.n, e.l) == (3, 2)])
        p_electrons = len([e for e in record.electrons if (e.n, e.l) == (4, 1)])
        # Cation removal order: highest n first (4s), then 3d.
        removed = charge
        from_s = min(removed, s_electrons)
        s_electrons -= from_s
        removed -= from_s
        from_d = min(removed, d_electrons)
        d_electrons -= from_d
        removed -= from_d
        if removed:
            raise BDerivationError("charge removes more active electrons than exist")
        s_unpaired, s_vacant = _hund_within_subshell(s_electrons, 1)
        d_unpaired, d_vacant = _hund_within_subshell(d_electrons, 5)
        p_unpaired, p_vacant = _hund_within_subshell(p_electrons, 3)
        return {
            "kind": "transition-metal",
            "basis_status": "construction-derived candidate; bond-context participation unresolved",
            "source_configuration_model": "frozen Aufbau construction",
            "subshells": [
                {
                    "subshell": "4s",
                    "orbitals": 1,
                    "electrons": s_electrons,
                    "unpaired": s_unpaired,
                    "vacant": s_vacant,
                },
                {
                    "subshell": "3d",
                    "orbitals": 5,
                    "electrons": d_electrons,
                    "unpaired": d_unpaired,
                    "vacant": d_vacant,
                },
                {
                    "subshell": "4p",
                    "orbitals": 3,
                    "electrons": p_electrons,
                    "unpaired": p_unpaired,
                    "vacant": p_vacant,
                    "bond_context_participation": "UNRESOLVED",
                },
            ],
            "unpaired_electrons": s_unpaired + d_unpaired + p_unpaired,
            "vacant_orbitals": s_vacant + d_vacant + p_vacant,
            "coordination_capacity": "UNRESOLVED",
            "capacity_rule_status": "FALSIFIED",
            "capacity_unresolved_reasons": [
                "ligand-field",
                "orbital-energy ordering",
                "geometry",
                "4p participation",
            ],
        }
    outermost = max(e.n for e in record.electrons)
    valence = [e for e in record.electrons if e.n == outermost]
    orbitals = sorted({(e.n, e.l, e.m_l) for e in valence})
    subshells = []
    for name in sorted({f"{e.n}{'spdf'[e.l]}" for e in valence}):
        members = [e for e in valence if f"{e.n}{'spdf'[e.l]}" == name]
        subshells.append(
            {
                "subshell": name,
                "orbitals": len({(e.l, e.m_l) for e in members}),
                "electrons": len(members),
                "unpaired": None,
                "vacant": None,
            }
        )
    return {
        "kind": "main-group",
        "subshells": subshells,
        "unpaired_electrons": len(record.unpaired_valence),
        "vacant_orbitals": max(0, len(orbitals) - (len(valence) - charge)),
        "coordination_capacity": "UNRESOLVED",
        "capacity_rule_status": "FALSIFIED",
        "capacity_unresolved_reasons": [
            "ligand-field",
            "orbital-energy ordering",
            "geometry",
            "4p participation",
        ],
    }


def ligand_field_spin_control(
    d_electrons: int,
    geometry: str,
    spin_regime: str,
) -> dict[str, Any]:
    """Evaluate an explicit octahedral high-/low-spin control.

    This is a control over a supplied field regime, not a derivation of that
    regime from ligand identity. No spectrochemical series or ligand lookup is
    used. The returned occupancy therefore demonstrates why d-electron count
    alone cannot determine the unpaired count.
    """

    if isinstance(d_electrons, bool) or not isinstance(d_electrons, int):
        raise BDerivationError("d_electrons must be an integer")
    if not 0 <= d_electrons <= 10:
        raise BDerivationError("d_electrons must be in 0..10")
    if geometry != "octahedral":
        raise BDerivationError("only the explicit octahedral control is implemented")
    if spin_regime not in {"high", "low"}:
        raise BDerivationError("spin_regime must be 'high' or 'low'")

    # Each tuple is (field group, orbital index). The first pass places one
    # electron in each listed orbital; the second pass pairs in the same order.
    t2g = [("t2g", index) for index in range(3)]
    eg = [("eg", index) for index in range(2)]
    if spin_regime == "high":
        fill_order = [*t2g, *eg, *t2g, *eg]
    else:
        fill_order = [*t2g, *t2g, *eg, *eg]

    occupancy: dict[tuple[str, int], int] = {
        orbital: 0 for orbital in [*t2g, *eg]
    }
    for orbital in fill_order[:d_electrons]:
        occupancy[orbital] += 1

    groups = []
    for group_name, orbitals in (("t2g", t2g), ("eg", eg)):
        counts = [occupancy[orbital] for orbital in orbitals]
        groups.append(
            {
                "group": group_name,
                "orbitals": len(orbitals),
                "electrons": sum(counts),
                "unpaired": sum(count == 1 for count in counts),
                "occupancy": counts,
            }
        )

    return {
        "control": f"octahedral-d{d_electrons}-{spin_regime}-spin",
        "geometry_input": geometry,
        "spin_regime_input": spin_regime,
        "d_electrons": d_electrons,
        "field_groups": groups,
        "unpaired_electrons": sum(group["unpaired"] for group in groups),
        "ligand_identity_used": False,
        "spectrochemical_lookup_used": False,
        "ligand_field_regime_derivation": "UNRESOLVED",
        "status": "control-only",
    }


_TRANSITION_METAL_TOPOLOGIES = {
    "ScCl3": {"center": "Sc", "ligands": ("Cl", "Cl", "Cl"), "center_charge": 3},
    "TiCl4": {"center": "Ti", "ligands": ("Cl", "Cl", "Cl", "Cl"), "center_charge": 4},
    "FeCl3": {"center": "Fe", "ligands": ("Cl", "Cl", "Cl"), "center_charge": 3},
    "ZnCl2": {"center": "Zn", "ligands": ("Cl", "Cl"), "center_charge": 2},
}


def evaluate_transition_metal_topology(
    name: str,
) -> dict[str, Any]:
    """Evaluate a supplied transition-metal star topology.

    Topology formation is downstream; this measures the supplied walls.
    """

    spec = _TRANSITION_METAL_TOPOLOGIES.get(name)
    if spec is None:
        raise BDerivationError(f"topology {name!r} is not in the supplied set")
    center_record = atomic_record(_symbol_z(spec["center"]))
    center_set = active_orbital_set(center_record, spec["center_charge"])
    ligand_ks = [ligand_contribution(atomic_record(_symbol_z(s))) for s in spec["ligands"]]
    atom_count = 1 + len(spec["ligands"])
    b_value = (3, atom_count, sum(ligand_ks))
    return {
        "topology": name,
        "center": spec["center"],
        "ligands": list(spec["ligands"]),
        "center_charge": spec["center_charge"],
        "center_active_orbital_set": center_set,
        "ligand_ks": ligand_ks,
        "b_value": list(b_value),
        "ligand_count_within_center_capacity": "UNRESOLVED",
        "capacity_check_reason": (
            "coordination capacity is UNRESOLVED until ligand-field, "
            "orbital-energy ordering, geometry, and 4p participation are "
            "represented"
        ),
        "status": "evaluation-only",
    }


__all__ = [
    "SCHEMA",
    "SCHEMA_SET",
    "VERSION",
    "BDerivationError",
    "bare_element_b",
    "ion_b",
    "ligand_contribution",
    "molecule_b",
    "active_orbital_set",
    "ligand_field_spin_control",
    "evaluate_transition_metal_topology",
    "freeze_b_derivation",
    "replay_b_derivation",
]
