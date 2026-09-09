"""EPAC Public Gonol constructor.

EPAC closes gonols on the UCNS Public Gonol carrier. This is not the EDCM
text-domain constructor. Glyphs are identity coordinates only; Public Gonol
function operations and a Möbius coupling law remain hmmm.

Charge state is already in the math: per-slot nuclear Z with Möbius ε at t=0
from ``(t, ε) ~ (t+n, (-1)^n ε)``. Oriented couplings plus those charge
states plus degree are the three-dimensional structure. Representing that 3
takes a 4-component quaternion; the extra coordinate is the scalar ε. No
cartesian embedding, ternary coupling, or Hamilton-product coupling is inferred.

Usage guidance
--------------
    from epac_public_gonol import construct_public_gonol, replay_public_gonol

    oxygen = construct_public_gonol(
        source_id="epac.atomic.element:O#0",
        relation="epac.atomic.element",
        identity_glyph="O",
        carried_options=(("Z", "8"), ("symbol", "O")),
    )
    assert oxygen.constructor_id == "epac.public_gonol"
    assert replay_public_gonol(oxygen).receipt_digest == oxygen.receipt_digest
"""

# === MODULE_BUILD ===
# id: epac_public_gonol
#   module_name: epac_public_gonol
#   module_kind: experiment
#   summary: EPAC candidate constructor that closes gonols on the UCNS Public Gonol carrier with oriented couplings and arity charge states; not the EDCM text-domain constructor
#   owner: The Interdependency
#   public_surface: CONSTRUCTOR_ID, CONSTRUCTOR_VERSION, PINNED_UCNS_COMMIT, PINNED_PUBLIC_GONOL_SHA256, ClosedPublicGonol, PublicGonolReceipt, PublicGonolConstructionError, construct_public_gonol, replay_public_gonol, canonical_receipt_bytes
#   internal_surface: _require_text, _validate_occurrence, _canonical_carried_options, _identity_position, _verified_ucns_commit, _geometry_record, _geometry, _validate_retained_geometry, _freeze_json, _json_ready, _tuple_tree, _canonical_coupling_record, _coupling_sort_key, _canonical_couplings_and_structure, _canonical_structure_tree, _participant_payload, _atomic_payload, _receipt_payload, _digest, _expected_structure_from_couplings, _validate_structure_matches_couplings, _validate_retained_gonol_tree, _validate_retained_receipt
#   auth_boundary: EPAC owns particle/energy gonol closure; UCNS owns Public Gonol carrier identity and native Möbius ε; EDCM text-domain constructor is not used; METAPAT affixiation is consumed, not redefined
#   storage_boundary: none; receipts remain caller-owned in-memory objects
#   network_boundary: none
#   user_data_boundary: caller-supplied source_id, relation, participants, and carried options remain in memory
#   admin_only: false
#   tests: tests.test_epac_public_gonol, tests.test_periodic_element_gonols, tests.test_molecular_affixiation
#   rollout: explicit EPAC candidate constructor; no canon selection, no EDCM scale option sets, no invented position operation
#   rollback: remove this module; do not fall back to edcm.gonol for EPAC construction
#   requires: ucns_public_gonol_geometry, ucns_native_mobius_geometry, epac_dimensional_arity
#   since: 2026-08-22
#   unresolved: exact UCNS geometric operation of Public Gonol function positions; UCNS Möbius-carrier affixiation/coupling law; two-letter element symbols have no single carrier glyph
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: epac_public_gonol_is_not_edcm_gonol
#   given: an EPAC gonol is constructed
#   then: constructor_id is epac.public_gonol and edcm.gonol is not imported or invoked
#   class: doctrine
#   since: 2026-08-22
#
# id: epac_public_gonol_binds_ucns_carrier_identity
#   given: identity_glyph is an admitted Public Gonol glyph
#   then: the closed gonol carries the exact UCNS index/glyph pair, EPAC-owned pinned carrier digest, and exact pinned UCNS dependency identity only when the imported checkout head and relevant source files verify clean; otherwise dependency identity remains hmmm
#   class: construction
#   since: 2026-08-22
#
# id: epac_public_gonol_replays_byte_identical
#   given: a PublicGonolReceipt
#   then: replay_public_gonol validates constructor-admissible scalars and options, canonical couplings and structure, the complete fixed geometry schema, and every retained identity before reproducing the same receipt_digest
#   class: correctness
#   since: 2026-08-22
#
# id: charged_oriented_couplings_are_the_structure
#   given: declared oriented couplings with per-slot charges
#   then: receipt.structure is exactly the structure derived from those couplings, arity charge states, degree, representation flags, and quaternion readouts; no caller-fabricated derived fields or (x,y,z) coupling are accepted
#   class: construction
#   since: 2026-08-22
# === END CONTRACTS ===

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from collections.abc import Sequence as SequenceABC
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from epac_dimensional_arity import (
    DimensionalArityError,
    MOBIUS_EPSILON_T0,
    space,
    structure_from_charged_couplings,
)
from epac_ucns_provenance import verify_loaded_ucns_commit
from ucns import (
    native_mobius_state,
    public_gonol_function,
    public_gonol_sha256,
)


CONSTRUCTOR_ID = "epac.public_gonol"
CONSTRUCTOR_VERSION = "v2"
PINNED_UCNS_COMMIT = "828c0b8bbcfc267efb5701da714191c1f73a81ff"
PINNED_PUBLIC_GONOL_SHA256 = "55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5"
STANDING = "implemented-candidate"
SELECTION_EFFECT = "none"

NONCLAIMS: tuple[str, ...] = (
    "not selected canon",
    "not EDCM text-domain gonol construction",
    "not a UCNS geometric function operation",
    "not a UCNS Möbius coupling law",
    "not METAPAT canon promotion",
    "not imported chemistry shape names",
)

HMMM: tuple[str, ...] = (
    "exact UCNS geometric operation of each Public Gonol function position",
    "UCNS Möbius-carrier affixiation/coupling law",
    "two-letter element symbols have no single Public Gonol glyph",
    "runtime UCNS commit identity when the imported checkout head and relevant source files cannot be verified clean against the pin",
)

ORDER_INSENSITIVE_STRUCTURE_FIELDS = frozenset(("parts", "degree", "quaternions"))
COUPLING_SCHEMA_FIELDS = frozenset(
    (
        "declared_ids",
        "coupling",
        "arity",
        "slot_charges",
        "charge_state",
        "mobius_epsilon_t0",
    )
)


class PublicGonolConstructionError(RuntimeError):
    """Fail-closed EPAC Public Gonol constructor error."""


@dataclass(frozen=True, slots=True)
class ClosedPublicGonol:
    """One closed EPAC gonol. Atomic at any later declared participation."""

    source_id: str
    occurrence: int
    relation: str
    identity_glyph: str | None
    carrier_index: int | None
    participants: tuple["ClosedPublicGonol", ...]
    carried_options: tuple[tuple[str, str], ...]
    couplings: tuple[Mapping[str, Any], ...]
    structure: Mapping[str, Any] | None
    geometry: Mapping[str, Any]
    atomic_id: str
    receipt_digest: str
    geometry_digest: str


@dataclass(frozen=True, slots=True)
class PublicGonolReceipt:
    """Deterministic construction receipt for one EPAC Public Gonol."""

    constructor_id: str
    constructor_version: str
    standing: str
    selection_effect: str
    source_id: str
    gonol: ClosedPublicGonol
    receipt_digest: str
    structure: Mapping[str, Any] | None
    geometry: Mapping[str, Any]
    nonclaims: tuple[str, ...]
    hmmm: tuple[str, ...]


def _require_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or value.isspace():
        raise PublicGonolConstructionError(f"{field} must be exact non-empty text")
    return value


def _validate_occurrence(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PublicGonolConstructionError("occurrence must be a non-negative int")
    return value


def _canonical_carried_options(
    carried_options: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    if not isinstance(carried_options, SequenceABC) or isinstance(
        carried_options, (str, bytes)
    ):
        raise PublicGonolConstructionError("carried options must be an ordered sequence")
    options: list[tuple[str, str]] = []
    for pair in carried_options:
        if not isinstance(pair, SequenceABC) or isinstance(pair, (str, bytes)) or len(pair) != 2:
            raise PublicGonolConstructionError("each carried option must be a key/value pair")
        options.append(
            (
                _require_text(pair[0], field="carried option key"),
                _require_text(pair[1], field="carried option value"),
            )
        )
    return tuple(options)


def _identity_position(identity_glyph: str | None) -> tuple[str | None, int | None]:
    if identity_glyph is None:
        return (None, None)
    if not isinstance(identity_glyph, str) or len(identity_glyph) != 1:
        raise PublicGonolConstructionError(
            "identity_glyph must be one admitted Public Gonol scalar or None"
        )
    try:
        position = public_gonol_function(identity_glyph)
    except (TypeError, ValueError) as exc:
        raise PublicGonolConstructionError(str(exc)) from exc
    return (position.glyph, position.index)


def _verified_ucns_commit() -> str:
    """Return the pin only when current source and executing UCNS code agree."""

    return verify_loaded_ucns_commit(
        pinned_commit=PINNED_UCNS_COMMIT,
        dependencies=(public_gonol_function, public_gonol_sha256, native_mobius_state),
    )


def _geometry_record(
    identity_glyph: str | None,
    carrier_index: int | None,
    ucns_commit: str,
) -> dict[str, Any]:
    identity: dict[str, Any] | None = None
    if identity_glyph is not None and carrier_index is not None:
        identity = {"index": carrier_index, "glyph": identity_glyph}
    return {
        "state": "bound",
        "authority": "ucns.public_gonol",
        "authority_binding": "explicit",
        "ucns_commit": ucns_commit,
        "carrier_digest": PINNED_PUBLIC_GONOL_SHA256,
        "identity_position": identity,
        "mobius_epsilon_t0": MOBIUS_EPSILON_T0,
        "position_operation": "hmmm",
    }


def _geometry(identity_glyph: str | None, carrier_index: int | None) -> dict[str, Any]:
    digest = public_gonol_sha256()
    if digest != PINNED_PUBLIC_GONOL_SHA256:
        raise PublicGonolConstructionError(
            "UCNS Public Gonol digest mismatch: "
            f"constructor pins {PINNED_PUBLIC_GONOL_SHA256}, computed {digest}"
        )
    if native_mobius_state(0).frame.sign != MOBIUS_EPSILON_T0:
        raise PublicGonolConstructionError("UCNS native Möbius origin is not canonical")
    return _geometry_record(identity_glyph, carrier_index, _verified_ucns_commit())


def _validate_retained_geometry(
    geometry: Mapping[str, Any],
    identity_glyph: str | None,
    carrier_index: int | None,
) -> Mapping[str, Any]:
    ucns_commit = geometry.get("ucns_commit")
    if ucns_commit not in {PINNED_UCNS_COMMIT, "hmmm"}:
        raise PublicGonolConstructionError("retained UCNS commit is not pinned or hmmm")
    expected = _geometry_record(identity_glyph, carrier_index, ucns_commit)
    if _tuple_tree(geometry) != _tuple_tree(expected):
        raise PublicGonolConstructionError("retained geometry is not canonical")
    return _freeze_json(expected)


def _freeze_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, MappingABC):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, SequenceABC) and not isinstance(value, (str, bytes)):
        return tuple(_freeze_json(item) for item in value)
    raise PublicGonolConstructionError(f"value is not JSON-stable: {type(value)!r}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, MappingABC):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, SequenceABC) and not isinstance(value, (str, bytes)):
        return [_json_ready(item) for item in value]
    return value


def _tuple_tree(value: Any) -> Any:
    if isinstance(value, MappingABC):
        return tuple(sorted((str(key), _tuple_tree(item)) for key, item in value.items()))
    if isinstance(value, SequenceABC) and not isinstance(value, (str, bytes)):
        return tuple(_tuple_tree(item) for item in value)
    return value


def _canonical_structure_tree(structure: Mapping[str, Any]) -> Any:
    canonical: list[tuple[str, Any]] = []
    for key, value in structure.items():
        field = str(key)
        if field in ORDER_INSENSITIVE_STRUCTURE_FIELDS:
            if not isinstance(value, SequenceABC) or isinstance(value, (str, bytes)):
                canonical.append((field, _tuple_tree(value)))
                continue
            canonical_items = tuple(
                _canonical_degree_tree(item)
                if field == "degree"
                else _canonical_quaternion_tree(item)
                if field == "quaternions"
                else _tuple_tree(item)
                for item in value
            )
            canonical.append((field, tuple(sorted(canonical_items, key=repr))))
            continue
        canonical.append((field, _tuple_tree(value)))
    return tuple(sorted(canonical))


def _canonical_quaternion_tree(item: Any) -> Any:
    if not isinstance(item, MappingABC):
        return _tuple_tree(item)
    represented_ids = item.get("represented_ids")
    components = item.get("components")
    axes = item.get("axes")
    if (
        isinstance(represented_ids, SequenceABC)
        and not isinstance(represented_ids, (str, bytes))
        and isinstance(components, SequenceABC)
        and not isinstance(components, (str, bytes))
        and isinstance(axes, SequenceABC)
        and not isinstance(axes, (str, bytes))
        and len(represented_ids) == 3
        and len(components) == 4
        and len(axes) == 4
    ):
        local_three = (
            (axes[0], components[0]),
            (represented_ids[0], axes[1], components[1]),
            tuple(
                sorted(
                    (
                        (represented_ids[1], axes[2], components[2]),
                        (represented_ids[2], axes[3], components[3]),
                    ),
                    key=repr,
                )
            ),
        )
        generic_fields = tuple(
            sorted(
                (str(key), _tuple_tree(value))
                for key, value in item.items()
                if str(key) not in {"axes", "components", "represented_ids"}
            )
        )
        return generic_fields + (("local_three", _tuple_tree(local_three)),)
    return _tuple_tree(item)


def _canonical_degree_tree(item: Any) -> Any:
    if not isinstance(item, MappingABC):
        return _tuple_tree(item)
    canonical: list[tuple[str, Any]] = []
    for key, value in item.items():
        field = str(key)
        if field == "incidences" and isinstance(value, SequenceABC) and not isinstance(value, (str, bytes)):
            canonical.append((field, tuple(sorted((_tuple_tree(entry) for entry in value), key=repr))))
            continue
        canonical.append((field, _tuple_tree(value)))
    return tuple(sorted(canonical))


def _coupling_signature(item: Mapping[str, Any]) -> tuple[Any, int, Any]:
    if not isinstance(item, MappingABC):
        raise PublicGonolConstructionError("each coupling must be a mapping")
    arity = item.get("arity")
    if isinstance(arity, bool) or not isinstance(arity, int):
        raise PublicGonolConstructionError("coupling arity must be an integer")
    declared = item.get("declared_ids", item.get("coupling"))
    charge_state = item.get("charge_state")
    if charge_state is None:
        charge_state = (item.get("slot_charges"), item.get("mobius_epsilon_t0"))
    return (_tuple_tree(declared), arity, _tuple_tree(charge_state))


def _structure_part_signature(item: Mapping[str, Any]) -> tuple[Any, int, Any]:
    if not isinstance(item, MappingABC):
        raise PublicGonolConstructionError("each structure part must be a mapping")
    arity = item.get("arity")
    if isinstance(arity, bool) or not isinstance(arity, int):
        raise PublicGonolConstructionError("structure part arity must be an integer")
    return (
        _tuple_tree(item.get("coupling")),
        arity,
        _tuple_tree(item.get("charge_state")),
    )


def _coupling_declaration(item: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[int | None, ...]]:
    if not isinstance(item, MappingABC):
        raise PublicGonolConstructionError("each coupling must be a mapping")
    extra_fields = frozenset(str(key) for key in item) - COUPLING_SCHEMA_FIELDS
    if extra_fields:
        names = ", ".join(sorted(extra_fields))
        raise PublicGonolConstructionError(f"coupling carries undeclared field(s): {names}")
    if "declared_ids" in item and "coupling" in item and _tuple_tree(item["declared_ids"]) != _tuple_tree(
        item["coupling"]
    ):
        raise PublicGonolConstructionError("coupling declared_ids conflicts with coupling")
    declared = item.get("declared_ids", item.get("coupling"))
    if not isinstance(declared, SequenceABC) or isinstance(declared, (str, bytes)) or not declared:
        raise PublicGonolConstructionError("each coupling must declare ordered dimension ids")
    ids = tuple(declared)
    if any(not isinstance(name, str) or not name or name.isspace() for name in ids):
        raise PublicGonolConstructionError("coupling dimension ids must be exact non-empty text")
    arity = item.get("arity")
    if isinstance(arity, bool) or not isinstance(arity, int) or arity != len(ids):
        raise PublicGonolConstructionError("coupling arity must match declared dimension ids")

    slot_charges = item.get("slot_charges")
    charge_state = item.get("charge_state")
    if slot_charges is None:
        if (
            not isinstance(charge_state, SequenceABC)
            or isinstance(charge_state, (str, bytes))
            or len(charge_state) != 2
        ):
            raise PublicGonolConstructionError("coupling must carry slot charges or charge_state")
        slot_charges = charge_state[0]
    if not isinstance(slot_charges, SequenceABC) or isinstance(slot_charges, (str, bytes)):
        raise PublicGonolConstructionError("slot_charges must be an ordered sequence")
    charges = tuple(slot_charges)
    if len(charges) != len(ids) or any(
        charge is not None and (isinstance(charge, bool) or not isinstance(charge, int))
        for charge in charges
    ):
        raise PublicGonolConstructionError("slot_charges must align with declared dimensions")
    if "mobius_epsilon_t0" in item and (
        (epsilon := item["mobius_epsilon_t0"]) is None
        or isinstance(epsilon, bool)
        or not isinstance(epsilon, int)
        or epsilon != MOBIUS_EPSILON_T0
    ):
        raise PublicGonolConstructionError("coupling mobius_epsilon_t0 conflicts with canonical epsilon")
    if charge_state is not None and _tuple_tree(charge_state) != _tuple_tree(
        (charges, MOBIUS_EPSILON_T0)
    ):
        raise PublicGonolConstructionError("coupling charge_state conflicts with slot charges")
    return ids, charges


def _canonical_coupling_record(item: Mapping[str, Any]) -> Mapping[str, Any]:
    ids, charges = _coupling_declaration(item)
    return _freeze_json(
        {
            "declared_ids": ids,
            "arity": len(ids),
            "slot_charges": charges,
            "charge_state": (charges, MOBIUS_EPSILON_T0),
            "mobius_epsilon_t0": MOBIUS_EPSILON_T0,
        }
    )


def _coupling_sort_key(item: Mapping[str, Any]) -> str:
    return repr(_coupling_signature(item))


def _expected_structure_from_couplings(
    couplings: Sequence[Mapping[str, Any]],
) -> Mapping[str, object]:
    ambient_ids: list[str] = []
    charge_by_id: dict[str, int | None] = {}
    declarations: list[tuple[str, ...]] = []
    for item in couplings:
        ids, charges = _coupling_declaration(item)
        declarations.append(ids)
        for name, charge in zip(ids, charges):
            if name not in ambient_ids:
                ambient_ids.append(name)
            if name in charge_by_id and charge_by_id[name] != charge:
                raise PublicGonolConstructionError(
                    f"dimension {name!r} has conflicting charges across couplings"
                )
            charge_by_id[name] = charge
    try:
        declared = space(
            ambient_ids,
            declarations,
            charges={name: charge for name, charge in charge_by_id.items() if charge is not None},
        )
        return structure_from_charged_couplings(declared)
    except DimensionalArityError as exc:
        raise PublicGonolConstructionError(str(exc)) from exc


def _validate_structure_matches_couplings(
    couplings: Sequence[Mapping[str, Any]],
    structure: Mapping[str, Any] | None,
) -> Mapping[str, object] | None:
    if not couplings and structure is None:
        return None
    if not couplings or structure is None:
        raise PublicGonolConstructionError(
            "couplings and structure must be supplied together"
        )
    parts = structure.get("parts")
    if not isinstance(parts, SequenceABC) or isinstance(parts, (str, bytes)):
        raise PublicGonolConstructionError("structure parts must be a sequence")
    expected_parts = tuple(sorted((_coupling_signature(item) for item in couplings), key=repr))
    actual_parts = tuple(sorted((_structure_part_signature(item) for item in parts), key=repr))
    if expected_parts != actual_parts:
        raise PublicGonolConstructionError(
            "structure must match the supplied declared couplings before closure"
        )
    expected_structure = _expected_structure_from_couplings(couplings)
    if _canonical_structure_tree(structure) != _canonical_structure_tree(expected_structure):
        raise PublicGonolConstructionError(
            "structure derived fields must exactly match the declared couplings before closure"
        )
    return expected_structure


def _canonical_couplings_and_structure(
    couplings: Sequence[Mapping[str, Any]],
    structure: Mapping[str, Any] | None,
) -> tuple[tuple[Mapping[str, Any], ...], Mapping[str, Any] | None]:
    if not isinstance(couplings, SequenceABC) or isinstance(couplings, (str, bytes)):
        raise PublicGonolConstructionError("couplings must be an ordered sequence")
    if structure is not None and not isinstance(structure, MappingABC):
        raise PublicGonolConstructionError("structure must be a mapping")
    canonical_couplings = tuple(
        sorted(
            (_canonical_coupling_record(item) for item in couplings),
            key=_coupling_sort_key,
        )
    )
    supplied_structure = None if structure is None else _freeze_json(structure)
    derived_structure = _validate_structure_matches_couplings(
        canonical_couplings,
        supplied_structure,
    )
    canonical_structure = (
        None if derived_structure is None else _freeze_json(derived_structure)
    )
    return canonical_couplings, canonical_structure


def _participant_payload(item: ClosedPublicGonol) -> dict[str, Any]:
    return {
        "source_id": item.source_id,
        "occurrence": item.occurrence,
        "relation": item.relation,
        "identity_glyph": item.identity_glyph,
        "carrier_index": item.carrier_index,
        "atomic_id": item.atomic_id,
        "receipt_digest": item.receipt_digest,
        "geometry_digest": item.geometry_digest,
        "carried_options": [list(pair) for pair in item.carried_options],
        "couplings": _freeze_json(item.couplings),
        "structure": _freeze_json(item.structure),
        "participants": [_participant_payload(child) for child in item.participants],
    }


def _atomic_payload(
    *,
    source_id: str,
    occurrence: int,
    relation: str,
    identity_glyph: str | None,
    carrier_index: int | None,
    participants: tuple[ClosedPublicGonol, ...],
    carried_options: tuple[tuple[str, str], ...],
    couplings: tuple[Mapping[str, Any], ...],
    structure: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "constructor_id": CONSTRUCTOR_ID,
        "constructor_version": CONSTRUCTOR_VERSION,
        "standing": STANDING,
        "selection_effect": SELECTION_EFFECT,
        "source_id": source_id,
        "occurrence": occurrence,
        "relation": relation,
        "identity_glyph": identity_glyph,
        "carrier_index": carrier_index,
        "participants": [_participant_payload(item) for item in participants],
        "carried_options": [list(pair) for pair in carried_options],
        "couplings": _freeze_json(couplings),
        "structure": _freeze_json(structure),
        "closure_invariant": "once closed, a gonol is atomic at any later participation",
    }


def _receipt_payload(
    *,
    source_id: str,
    gonol_payload: Mapping[str, Any],
    geometry: Mapping[str, Any],
    atomic_id: str,
    geometry_digest: str,
) -> dict[str, Any]:
    return {
        "constructor_id": CONSTRUCTOR_ID,
        "constructor_version": CONSTRUCTOR_VERSION,
        "standing": STANDING,
        "selection_effect": SELECTION_EFFECT,
        "source_id": source_id,
        "gonol": gonol_payload,
        "atomic_id": atomic_id,
        "geometry": _freeze_json(geometry),
        "geometry_digest": geometry_digest,
        "nonclaims": list(NONCLAIMS),
        "hmmm": list(HMMM),
    }


def canonical_receipt_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        _json_ready(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(payload: Mapping[str, Any]) -> str:
    return sha256(canonical_receipt_bytes(payload)).hexdigest()


def _validate_retained_gonol_tree(gonol: ClosedPublicGonol) -> ClosedPublicGonol:
    """Validate and deeply freeze every retained participant envelope."""

    if not isinstance(gonol, ClosedPublicGonol):
        raise PublicGonolConstructionError(
            "retained participants must be closed EPAC public gonols"
        )
    source_id = _require_text(gonol.source_id, field="source_id")
    relation = _require_text(gonol.relation, field="relation")
    occurrence = _validate_occurrence(gonol.occurrence)
    carried_options = _canonical_carried_options(gonol.carried_options)
    frozen_participants = tuple(
        _validate_retained_gonol_tree(participant)
        for participant in gonol.participants
    )
    if not isinstance(gonol.geometry, MappingABC):
        raise PublicGonolConstructionError("retained geometry must be a mapping")
    frozen_geometry = _freeze_json(gonol.geometry)
    expected_geometry_digest = _digest({"geometry": frozen_geometry})
    if gonol.geometry_digest != expected_geometry_digest:
        raise PublicGonolConstructionError(
            "retained geometry digest does not match geometry"
        )
    if gonol.structure is not None and not isinstance(gonol.structure, MappingABC):
        raise PublicGonolConstructionError("retained structure must be a mapping")
    expected_glyph, expected_index = _identity_position(gonol.identity_glyph)
    if gonol.identity_glyph != expected_glyph or gonol.carrier_index != expected_index:
        raise PublicGonolConstructionError(
            "retained carrier identity does not match geometry"
        )
    geometry = _validate_retained_geometry(
        frozen_geometry,
        expected_glyph,
        expected_index,
    )
    canonical_couplings, canonical_structure = _canonical_couplings_and_structure(
        gonol.couplings,
        gonol.structure,
    )
    gonol_payload = _atomic_payload(
        source_id=source_id,
        occurrence=occurrence,
        relation=relation,
        identity_glyph=expected_glyph,
        carrier_index=expected_index,
        participants=frozen_participants,
        carried_options=carried_options,
        couplings=canonical_couplings,
        structure=canonical_structure,
    )
    expected_atomic_id = _digest({"atomic": gonol_payload})
    if gonol.atomic_id != expected_atomic_id:
        raise PublicGonolConstructionError("retained atomic id does not match gonol")
    expected_receipt_digest = _digest(
        _receipt_payload(
            source_id=source_id,
            gonol_payload=gonol_payload,
            geometry=geometry,
            atomic_id=expected_atomic_id,
            geometry_digest=expected_geometry_digest,
        )
    )
    if gonol.receipt_digest != expected_receipt_digest:
        raise PublicGonolConstructionError(
            "retained receipt digest does not match gonol"
        )
    return ClosedPublicGonol(
        source_id=source_id,
        occurrence=occurrence,
        relation=relation,
        identity_glyph=expected_glyph,
        carrier_index=expected_index,
        participants=frozen_participants,
        carried_options=carried_options,
        couplings=canonical_couplings,
        structure=canonical_structure,
        geometry=geometry,
        atomic_id=expected_atomic_id,
        receipt_digest=expected_receipt_digest,
        geometry_digest=expected_geometry_digest,
    )


def _validate_retained_receipt(receipt: PublicGonolReceipt) -> ClosedPublicGonol:
    """Reject contradictory or stale duplicate fields before replay."""

    if not isinstance(receipt, PublicGonolReceipt) or not isinstance(
        receipt.gonol, ClosedPublicGonol
    ):
        raise PublicGonolConstructionError("replay requires a PublicGonolReceipt")
    gonol = receipt.gonol
    expected_envelope = (
        receipt.constructor_id == CONSTRUCTOR_ID
        and receipt.constructor_version == CONSTRUCTOR_VERSION
        and receipt.standing == STANDING
        and receipt.selection_effect == SELECTION_EFFECT
        and receipt.nonclaims == NONCLAIMS
        and receipt.hmmm == HMMM
        and receipt.source_id == gonol.source_id
        and receipt.receipt_digest == gonol.receipt_digest
    )
    if not expected_envelope:
        raise PublicGonolConstructionError("receipt envelope is not canonical")
    outer_geometry = _freeze_json(receipt.geometry)
    gonol_geometry = _freeze_json(gonol.geometry)
    if _tuple_tree(outer_geometry) != _tuple_tree(gonol_geometry):
        raise PublicGonolConstructionError("retained receipt geometries disagree")
    if _tuple_tree(receipt.structure) != _tuple_tree(gonol.structure):
        raise PublicGonolConstructionError("retained receipt structures disagree")
    return _validate_retained_gonol_tree(gonol)


def _seal_public_gonol(
    *,
    source_id: str,
    relation: str,
    participants: tuple[ClosedPublicGonol, ...],
    identity_glyph: str | None,
    carrier_index: int | None,
    occurrence: int,
    carried_options: tuple[tuple[str, str], ...],
    couplings: tuple[Mapping[str, Any], ...],
    structure: Mapping[str, Any] | None,
    geometry: Mapping[str, Any],
) -> PublicGonolReceipt:
    """Seal already validated canonical fields with one immutable geometry receipt."""

    frozen_geometry = _freeze_json(geometry)
    gonol_payload = _atomic_payload(
        source_id=source_id,
        occurrence=occurrence,
        relation=relation,
        identity_glyph=identity_glyph,
        carrier_index=carrier_index,
        participants=participants,
        carried_options=carried_options,
        couplings=couplings,
        structure=structure,
    )
    atomic_id = _digest({"atomic": gonol_payload})
    geometry_digest = _digest({"geometry": frozen_geometry})
    receipt_payload = _receipt_payload(
        source_id=source_id,
        gonol_payload=gonol_payload,
        geometry=frozen_geometry,
        atomic_id=atomic_id,
        geometry_digest=geometry_digest,
    )
    receipt_digest = _digest(receipt_payload)
    gonol = ClosedPublicGonol(
        source_id=source_id,
        occurrence=occurrence,
        relation=relation,
        identity_glyph=identity_glyph,
        carrier_index=carrier_index,
        participants=participants,
        carried_options=carried_options,
        couplings=couplings,
        structure=structure,
        geometry=frozen_geometry,
        atomic_id=atomic_id,
        receipt_digest=receipt_digest,
        geometry_digest=geometry_digest,
    )
    return PublicGonolReceipt(
        constructor_id=CONSTRUCTOR_ID,
        constructor_version=CONSTRUCTOR_VERSION,
        standing=STANDING,
        selection_effect=SELECTION_EFFECT,
        source_id=source_id,
        gonol=gonol,
        receipt_digest=receipt_digest,
        structure=structure,
        geometry=frozen_geometry,
        nonclaims=NONCLAIMS,
        hmmm=HMMM,
    )


def construct_public_gonol(
    *,
    source_id: str,
    relation: str,
    participants: Sequence[ClosedPublicGonol] = (),
    identity_glyph: str | None = None,
    occurrence: int = 0,
    carried_options: Sequence[tuple[str, str]] = (),
    couplings: Sequence[Mapping[str, Any]] = (),
    structure: Mapping[str, Any] | None = None,
) -> PublicGonolReceipt:
    """Close one EPAC gonol on the pinned UCNS Public Gonol carrier."""

    source_id = _require_text(source_id, field="source_id")
    relation = _require_text(relation, field="relation")
    occurrence = _validate_occurrence(occurrence)
    closed_participants = tuple(
        _validate_retained_gonol_tree(item) for item in participants
    )
    options = _canonical_carried_options(carried_options)
    frozen_couplings, frozen_structure = _canonical_couplings_and_structure(
        couplings,
        structure,
    )
    glyph, index = _identity_position(identity_glyph)
    geometry = _geometry(glyph, index)
    return _seal_public_gonol(
        source_id=source_id,
        relation=relation,
        participants=closed_participants,
        identity_glyph=glyph,
        carrier_index=index,
        occurrence=occurrence,
        carried_options=options,
        couplings=frozen_couplings,
        structure=frozen_structure,
        geometry=geometry,
    )


def replay_public_gonol(receipt: PublicGonolReceipt) -> PublicGonolReceipt:
    """Replay one receipt from its closed gonol. Reproduces construction identity."""

    gonol = _validate_retained_receipt(receipt)
    derived_structure = _validate_structure_matches_couplings(
        gonol.couplings,
        gonol.structure,
    )
    frozen_structure = None if derived_structure is None else _freeze_json(derived_structure)
    replayed = _seal_public_gonol(
        source_id=gonol.source_id,
        relation=gonol.relation,
        participants=gonol.participants,
        identity_glyph=gonol.identity_glyph,
        carrier_index=gonol.carrier_index,
        occurrence=gonol.occurrence,
        carried_options=gonol.carried_options,
        couplings=gonol.couplings,
        structure=frozen_structure,
        geometry=gonol.geometry,
    )
    if replayed.receipt_digest != receipt.receipt_digest:
        raise PublicGonolConstructionError("receipt does not match its retained canonical payload")
    return replayed


__all__ = [
    "CONSTRUCTOR_ID",
    "CONSTRUCTOR_VERSION",
    "ClosedPublicGonol",
    "HMMM",
    "NONCLAIMS",
    "PINNED_PUBLIC_GONOL_SHA256",
    "PINNED_UCNS_COMMIT",
    "PublicGonolConstructionError",
    "PublicGonolReceipt",
    "canonical_receipt_bytes",
    "construct_public_gonol",
    "replay_public_gonol",
]
