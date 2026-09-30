"""Typed S0-through-S6 EPAC multi-origin join terms.

This module is a representation and correctness prototype.  It preserves an
authored recursive join tree, exact state properties and separate readouts, named ordered slots, holes,
leftovers, inferred bearing, and provenance.  It does not establish chemistry,
physics, energy coupling, UCNS correspondence, or production suitability.

Usage guidance
--------------
    from epac_join_term import construct_epac_join_tree, trace_origin_lineage

    tree = construct_epac_join_tree()
    assert trace_origin_lineage(tree, tree.origins[-1].origin_id)[0].endswith("S0")
"""

# === MODULE_BUILD ===
# id: epac_multi_origin_join_term_v0
#   module_name: epac_join_term
#   module_kind: schema
#   summary: strict public prototype for a typed ordered provenance-bearing S0-through-S6 EPAC join tree and its lossy legacy bag projection
#   owner: The Interdependency/epac
#   public_surface: ExactRatio, JoinSlot, ScaleOrigin, AuthoredJoin, LegacyBag, EPACJoinTree, construct_epac_join_tree, recover_epac_join_tree, join_isomorphic, trace_origin_lineage, legacy_bag_projection
#   internal_surface: canonical JSON, strict validators, structural signature, fixture declarations
#   auth_boundary: none
#   storage_boundary: caller-provided public bytes only; no secrets or mutable persistence
#   network_boundary: none
#   user_data_boundary: public deterministic research fixture only
#   admin_only: false
#   tests: tests.test_epac_join_term
#   rollout: research candidate and packaged deterministic receipt; not a release or protocol profile
#   rollback: remove this candidate module, its receipt, tests, and documentation without changing existing EPAC constructors or falsification evidence
#   requires: metapat.application.epac_join_terms@epac-join-terms-application-v4
#   since: 2026-09-29
#   unresolved: no native secret operation, external-domain interpretation, or useful physical coupling is established
# === END MODULE_BUILD ===

# === DOCS ===
# id: epac_multi_origin_join_term_v0_docs
#   summary: specifies the typed join tree, role licensing, exact wire, equality, lossy bag projection, recovery, and nonclaims
#   audience: developer, agent, independent replayer, domain reviewer
#   source: docs/multi-origin-join-term-v0.md
#   covers: epac_multi_origin_join_term_v0, data/epac-join-term-v0-receipt.json, tools/generate_join_term_v0.py
#   status: candidate
# === END DOCS ===

# === CAPABILITIES ===
# id: epac_multi_origin_join_recovery
#   summary: recovers and validates the complete typed S0-through-S6 join tree from public deterministic JSON and replays exact authored lineage
#   exposes: epac_join_term.recover_epac_join_tree, epac_join_term.trace_origin_lineage
#   inputs: public UTF-8 JSON bytes under epac.multi-origin-join-tree version 0.2.0
#   outputs: immutable validated join tree and exact S0-through-target origin lineage
#   boundaries: auth:none, storage:none, network:none, user_data:public fixture only
# === END CAPABILITIES ===

# === BOUNDARIES ===
# id: epac_multi_origin_join_term_v0_boundary
#   summary: representation evidence only; no confidentiality, cryptographic private structure, chemistry phase, physical energy, UCNS law, molecular-shape repair, PCEA compatibility, or release authority
#   auth_boundary: none
#   storage_boundary: no mutable persistence
#   network_boundary: none
#   user_data_boundary: public deterministic research fixture only
#   admin_only: false
# === END BOUNDARIES ===

# === CONTRACTS ===
# id: epac_join_tree_complete_scale_tensor
#   given: an EPAC join tree is constructed or recovered
#   then: it contains exactly one typed origin at every scale S0 through S6 and exactly six authored adjacent-scale joins
#   class: schema
#
# id: epac_join_tree_explicit_boundary
#   given: an origin boundary is serialized
#   then: positive k, named ordered slots, holes, leftovers, arity, and shape signature are explicit and mutually consistent
#   class: correctness
#
# id: epac_join_tree_inferred_bearing
#   given: stored slot-facing properties are present
#   then: ordered bearing components are derived by the declared sign rule and a mismatching serialized bearing is rejected
#   class: correctness
#
# id: epac_join_tree_recursive_identity
#   given: an origin above S0 is inspected
#   then: its member slot references only the immediately preceding origin and its authored join records exact source and new target identity
#   class: construction
#
# id: epac_join_tree_s5_energy_qualified
#   given: the S5 origin is serialized
#   then: its exact occupancy functional equals occupied slots over k while every non-S5 origin carries no S5 readout
#   class: boundary_contract
#
# id: epac_join_tree_semantic_customs
#   given: any semantic wire field is inspected
#   then: its schema path is paired with an exact METAPAT spine name, EPAC domain name, and application role under the pinned license
#   class: provenance
#
# id: epac_join_tree_join_isomorphism
#   given: two trees are compared
#   then: bijectively alpha-renamed identities may be isomorphic while identity aliasing, named order, holes, leftovers, state, phase chart, shape, or authored relation changes remain distinct
#   class: correctness
#
# id: epac_join_tree_bag_is_lossy
#   given: two same-count non-isomorphic join trees
#   then: their legacy bag projections may be equal but the bag cannot be parsed as or uniquely recover the tree
#   class: safety
#
# id: epac_join_tree_public_recovery
#   given: only canonical public receipt bytes
#   then: strict recovery verifies the digest and reconstructs exact tree state and lineage without constructor or private state
#   class: evidence
#
# id: epac_join_tree_strict_rejection
#   given: duplicate keys, unknown or missing fields, invalid modulus, omitted explicit slot state, duplicate identities, skip-scale references, or inconsistent joins
#   then: recovery fails closed
#   class: safety
#
# id: epac_join_tree_deterministic_serialization
#   given: the same typed tree is serialized repeatedly
#   then: canonical bytes and candidate digest are identical
#   class: evidence
#
# id: epac_join_tree_existing_falsification_preserved
#   given: this candidate is added to EPAC
#   then: the preregistered molecular-shape standings remain FALSIFIED and are neither deleted nor reinterpreted
#   class: boundary_contract
#
# id: epac_join_tree_readout_boundary
#   given: stored origin properties and derived readouts
#   then: each readout identifies its origin, measured property, and rule and cannot replace or alter the stored state
#   class: boundary_contract
#
# id: epac_join_tree_conditional_roles
#   given: static bearing and authored adjacent-scale joins without result or occurrence evidence
#   then: no field claims Vector, Transformation, or Time and the producer role projection matches the exact merged fixture
#   class: provenance
#
# id: epac_join_tree_canonical_wire
#   given: an equivalent unreduced ratio or other normalized wire value with an old or recomputed digest
#   then: recovery rejects it rather than silently normalizing the digest-bearing payload
#   class: safety
# === END CONTRACTS ===

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any

_MODULE_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

JOIN_TREE_SCHEMA_ID = "epac.multi-origin-join-tree"
JOIN_TREE_SCHEMA_VERSION = "0.2.0"
BEARING_RULE_ID = "epac.bearing.slot-facing-sign.v0"
ADJACENT_JOIN_RELATION = "epac.join.adjacent-scale"
METAPAT_APPLICATION_ID = "metapat.application.epac_join_terms"
METAPAT_APPLICATION_VERSION = "epac-join-terms-application-v4"
METAPAT_APPLICATION_DIGEST = "461ef7e059aa65b514017683ba9b57058ee9f582bc63748fabd021cdeb660b4b"

SCALE_DOMAIN_NAMES: tuple[str, ...] = (
    "subatomic slot",
    "atomic",
    "join/arity",
    "embed",
    "electronic state",
    "EPAC energy readout",
    "ensemble",
)
SCALE_IDS: tuple[str, ...] = tuple(f"S{index}" for index in range(7))

# Exact role-to-catalog projection from the pinned METAPAT application.  An
# application role identifies the licensing clause; spine_name identifies the
# EPAC field's structural role.  Those axes are related but not synonymous.
_METAPAT_APPLICATION_ROLE_MODULES = MappingProxyType({
    "customs-boundary": "metapat.root_spine",
    "stored-join-term": "metapat.axiom.1.thing",
    "join-boundary": "metapat.axiom.2.boundary",
    "origin-state": "metapat.axiom.3.state",
    "scale-origin": "metapat.axiom.4.simplex",
    "multi-origin-tensor": "metapat.axiom.5.tensor",
    "authored-near-join": "metapat.axiom.6.relate",
    "recursive-origin": "metapat.axiom.7.emerge",
    "state-metric": "metapat.axiom.9.scalar",
    "join-transformation": "metapat.axiom.10.transformation",
    "transformation-sequence": "metapat.axiom.11.time",
    "domain-customs": "metapat.axiom.12.domain_qualification",
})
_SPINE_NAMES = frozenset(
    {
        "Thing",
        "Boundary",
        "State",
        "Simplex",
        "Tensor",
        "Scalar",
    }
)
_APPLICATION_ROLE_ALLOWED_SPINES = MappingProxyType({
    "customs-boundary": _SPINE_NAMES,
    "stored-join-term": frozenset({"Thing"}),
    "join-boundary": frozenset({"Boundary"}),
    "origin-state": frozenset({"State"}),
    "scale-origin": frozenset({"Simplex"}),
    "multi-origin-tensor": frozenset({"Tensor"}),
    "authored-near-join": frozenset({"Tensor"}),
    "recursive-origin": frozenset({"Thing"}),
    "state-metric": frozenset({"Scalar"}),
    "join-transformation": frozenset({"Transformation"}),
    "transformation-sequence": frozenset({"Time"}),
    "domain-customs": _SPINE_NAMES,
})

# Exact metadata subtrees identify the wire or carry the semantic license and
# are not domain observations. Every other serialized field path is licensed
# here; _semantic_wire_field_paths derives that coverage from live wire data.
_WIRE_METADATA_FIELDS = frozenset(
    {
        "candidate_digest",
        "schema_id",
        "schema_version",
        "semantic_field_bindings",
        "semantic_license",
    }
)
_SEMANTIC_FIELD_BINDING_ROWS = {
    "tree.object_kind": {"spine_name": "Thing", "domain_name": "multi-origin join-tree kind", "application_role": "stored-join-term"},
    "origin.origin_id": {"spine_name": "Thing", "domain_name": "origin identity", "application_role": "stored-join-term"},
    "origin.scale": {"spine_name": "Simplex", "domain_name": "EPAC scale origin", "application_role": "scale-origin"},
    "origin.domain_name": {"spine_name": "Simplex", "domain_name": "EPAC scale name", "application_role": "domain-customs"},
    "origin.phase": {"spine_name": "State", "domain_name": "EPAC exact phase", "application_role": "origin-state"},
    "origin.phase_chart": {"spine_name": "State", "domain_name": "visible or lifted phase record", "application_role": "origin-state"},
    "origin.k": {"spine_name": "Boundary", "domain_name": "join window k", "application_role": "join-boundary"},
    "origin.slots": {"spine_name": "Boundary", "domain_name": "named ordered join slots", "application_role": "join-boundary"},
    "slot.name": {"spine_name": "Boundary", "domain_name": "slot name", "application_role": "join-boundary"},
    "slot.order": {"spine_name": "Boundary", "domain_name": "slot order", "application_role": "join-boundary"},
    "slot.kind": {"spine_name": "Boundary", "domain_name": "member, hole, or leftover", "application_role": "join-boundary"},
    "slot.participant_id": {"spine_name": "Thing", "domain_name": "member or leftover identity", "application_role": "stored-join-term"},
    "slot.participant_scale": {"spine_name": "Simplex", "domain_name": "member source scale", "application_role": "scale-origin"},
    "slot.facing": {"spine_name": "State", "domain_name": "stored slot-facing property", "application_role": "origin-state"},
    "origin.bearing": {"spine_name": "Scalar", "domain_name": "ordered static slot-facing sign readouts", "application_role": "state-metric"},
    "origin.arity": {"spine_name": "Boundary", "domain_name": "occupied seating arity", "application_role": "join-boundary"},
    "origin.shape_signature": {"spine_name": "Tensor", "domain_name": "ordered seating shape", "application_role": "multi-origin-tensor"},
    "origin.s5_energy_readout": {"spine_name": "Scalar", "domain_name": "EPAC S5 occupancy functional", "application_role": "state-metric"},
    "origin.readouts": {"spine_name": "Scalar", "domain_name": "identified phase, capacity, and slot-facing readouts", "application_role": "state-metric"},
    "readout.origin_id": {"spine_name": "Thing", "domain_name": "readout source origin identity", "application_role": "stored-join-term"},
    "readout.measured_property": {"spine_name": "State", "domain_name": "named source state property", "application_role": "origin-state"},
    "readout.rule_id": {"spine_name": "Thing", "domain_name": "EPAC readout rule identity", "application_role": "domain-customs"},
    "readout.value": {"spine_name": "Scalar", "domain_name": "computed EPAC readout value", "application_role": "state-metric"},
    "origin.provenance": {"spine_name": "Thing", "domain_name": "origin provenance", "application_role": "recursive-origin"},
    "join.join_id": {"spine_name": "Thing", "domain_name": "authored join record identity", "application_role": "stored-join-term"},
    "join.order": {"spine_name": "Tensor", "domain_name": "authored adjacent-scale relation position", "application_role": "authored-near-join"},
    "join.source_origin_id": {"spine_name": "Thing", "domain_name": "source origin identity", "application_role": "recursive-origin"},
    "join.target_origin_id": {"spine_name": "Thing", "domain_name": "new target origin identity", "application_role": "recursive-origin"},
    "join.relation": {"spine_name": "Tensor", "domain_name": "authored adjacent-scale join", "application_role": "authored-near-join"},
    "join.provenance": {"spine_name": "Thing", "domain_name": "authored join provenance", "application_role": "recursive-origin"},
    "tree.origins": {"spine_name": "Tensor", "domain_name": "S0-through-S6 origin tensor", "application_role": "multi-origin-tensor"},
    "tree.joins": {"spine_name": "Tensor", "domain_name": "ordered authored adjacent-scale relations", "application_role": "authored-near-join"},
    "tree.legacy_bag": {"spine_name": "Thing", "domain_name": "non-structural legacy bag sidecar", "application_role": "domain-customs"},
    "legacy_bag.kind": {"spine_name": "Thing", "domain_name": "legacy sidecar kind", "application_role": "domain-customs"},
    "legacy_bag.excluded_from_tensor": {"spine_name": "Thing", "domain_name": "tensor-exclusion marker", "application_role": "domain-customs"},
    "legacy_bag.scale_slot_counts": {"spine_name": "Thing", "domain_name": "lossy slot-count map by scale", "application_role": "domain-customs"},
    "legacy_bag.slot_kind_counts": {"spine_name": "Thing", "domain_name": "lossy slot-count map by kind", "application_role": "domain-customs"},
}
SEMANTIC_FIELD_BINDINGS: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        key: MappingProxyType(value)
        for key, value in _SEMANTIC_FIELD_BINDING_ROWS.items()
    }
)
del _SEMANTIC_FIELD_BINDING_ROWS

REQUIRED_SEMANTIC_FIELD_PATHS = frozenset(SEMANTIC_FIELD_BINDINGS)
SLOT_KINDS = frozenset({"member", "hole", "leftover"})
PHASE_CHARTS = frozenset({"visible", "lifted"})


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_keys(data: Mapping[str, Any], expected: set[str], name: str) -> None:
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown:
        raise ValueError(f"unknown {name} fields: {sorted(unknown)!r}")
    if missing:
        raise ValueError(f"missing {name} fields: {sorted(missing)!r}")


def _semantic_wire_field_paths(data: Mapping[str, Any]) -> frozenset[str]:
    """Derive every meaning-bearing schema path from one serialized tree."""
    if not isinstance(data, Mapping):
        raise ValueError("semantic wire coverage requires an object")
    paths = {
        f"tree.{key}"
        for key in data
        if key not in _WIRE_METADATA_FIELDS
    }
    origins = data.get("origins", ())
    for origin in origins if isinstance(origins, (list, tuple)) else ():
        if not isinstance(origin, Mapping):
            continue
        paths.update(f"origin.{key}" for key in origin)
        slots = origin.get("slots", ())
        for slot in slots if isinstance(slots, (list, tuple)) else ():
            if isinstance(slot, Mapping):
                paths.update(f"slot.{key}" for key in slot)
        readouts = origin.get("readouts", ())
        records = list(readouts) if isinstance(readouts, (list, tuple)) else []
        records.extend((origin.get("bearing"), origin.get("s5_energy_readout")))
        for readout in records:
            if isinstance(readout, Mapping):
                paths.update(f"readout.{key}" for key in readout)
    joins = data.get("joins", ())
    for join in (
        joins if isinstance(joins, (list, tuple)) else ()
    ):
        if isinstance(join, Mapping):
            paths.update(f"join.{key}" for key in join)
    legacy_bag = data.get("legacy_bag")
    if isinstance(legacy_bag, Mapping):
        paths.update(f"legacy_bag.{key}" for key in legacy_bag)
    return frozenset(paths)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _integer(value: Any, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _optional_text(value: Any, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _text_tuple(value: Any, name: str, *, minimum: int = 0) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be an array")
    result = tuple(_text(item, f"{name} item") for item in value)
    if len(result) < minimum:
        raise ValueError(f"{name} must contain at least {minimum} items")
    return result


def _reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class ExactRatio:
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _integer(self.numerator, "ratio numerator")
        denominator = _integer(self.denominator, "ratio denominator", minimum=1)
        reduced = Fraction(numerator, denominator)
        object.__setattr__(self, "numerator", reduced.numerator)
        object.__setattr__(self, "denominator", reduced.denominator)

    def to_dict(self) -> dict[str, int]:
        return {"numerator": self.numerator, "denominator": self.denominator}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExactRatio:
        if not isinstance(data, Mapping):
            raise ValueError("exact ratio must be an object")
        _strict_keys(data, {"numerator", "denominator"}, "exact-ratio")
        ratio = cls(
            _integer(data["numerator"], "ratio numerator"),
            _integer(data["denominator"], "ratio denominator", minimum=1),
        )
        if ratio.to_dict() != data:
            raise ValueError("exact ratio must be reduced on the wire")
        return ratio


@dataclass(frozen=True, slots=True)
class JoinSlot:
    name: str
    order: int
    kind: str
    participant_id: str | None
    participant_scale: str | None
    facing: int

    def __post_init__(self) -> None:
        _text(self.name, "slot name")
        _integer(self.order, "slot order", minimum=0)
        if self.kind not in SLOT_KINDS:
            raise ValueError(f"unsupported slot kind {self.kind!r}")
        _integer(self.facing, "slot facing")
        if self.kind == "hole":
            if self.participant_id is not None or self.participant_scale is not None:
                raise ValueError("hole must store null participant identity and scale")
            if self.facing != 0:
                raise ValueError("hole facing must be zero")
        elif self.kind == "member":
            _text(self.participant_id, "member participant_id")
            if self.participant_scale not in SCALE_IDS:
                raise ValueError("member participant_scale must be S0 through S6")
        else:
            _text(self.participant_id, "leftover participant_id")
            if self.participant_scale is not None:
                raise ValueError("leftover participant_scale must be null")

    @property
    def bearing_component(self) -> int:
        return (self.facing > 0) - (self.facing < 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "order": self.order,
            "kind": self.kind,
            "participant_id": self.participant_id,
            "participant_scale": self.participant_scale,
            "facing": self.facing,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> JoinSlot:
        if not isinstance(data, Mapping):
            raise ValueError("join slot must be an object")
        _strict_keys(
            data,
            {"name", "order", "kind", "participant_id", "participant_scale", "facing"},
            "join-slot",
        )
        return cls(
            name=_text(data["name"], "slot name"),
            order=_integer(data["order"], "slot order", minimum=0),
            kind=_text(data["kind"], "slot kind"),
            participant_id=_optional_text(data["participant_id"], "participant_id"),
            participant_scale=_optional_text(data["participant_scale"], "participant_scale"),
            facing=_integer(data["facing"], "slot facing"),
        )


@dataclass(frozen=True, slots=True)
class ScaleOrigin:
    origin_id: str
    scale: str
    domain_name: str
    phase: ExactRatio
    phase_chart: str
    k: int
    slots: tuple[JoinSlot, ...]
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.origin_id, "origin_id")
        if self.scale not in SCALE_IDS:
            raise ValueError("origin scale must be S0 through S6")
        expected_name = SCALE_DOMAIN_NAMES[int(self.scale[1:])]
        if self.domain_name != expected_name:
            raise ValueError(f"{self.scale} domain_name must be {expected_name!r}")
        if not isinstance(self.phase, ExactRatio):
            raise ValueError("origin phase must be ExactRatio")
        if self.phase_chart not in PHASE_CHARTS:
            raise ValueError("phase_chart must be visible or lifted")
        _integer(self.k, "origin k", minimum=1)
        slots = tuple(self.slots)
        if len(slots) != self.k:
            raise ValueError("origin k must equal the explicit slot count")
        if any(not isinstance(slot, JoinSlot) for slot in slots):
            raise ValueError("origin slots must contain JoinSlot values")
        if tuple(slot.order for slot in slots) != tuple(range(self.k)):
            raise ValueError("origin slot order must be explicit, unique, and contiguous")
        if len({slot.name for slot in slots}) != len(slots):
            raise ValueError("origin slot names must be unique")
        provenance = _text_tuple(self.provenance, "origin provenance", minimum=1)
        object.__setattr__(self, "slots", slots)
        object.__setattr__(self, "provenance", provenance)

    @property
    def bearing(self) -> tuple[int, ...]:
        return tuple(slot.bearing_component for slot in self.slots)

    @property
    def arity(self) -> int:
        return sum(slot.kind != "hole" for slot in self.slots)

    @property
    def shape_signature(self) -> tuple[str, ...]:
        return tuple(f"{slot.order}:{slot.name}:{slot.kind}" for slot in self.slots)

    @property
    def s5_energy_readout(self) -> ExactRatio | None:
        if self.scale != "S5":
            return None
        return ExactRatio(self.arity, self.k)

    def _readout(self, measured_property: str, rule_id: str, value: Any) -> dict[str, Any]:
        return {"origin_id": self.origin_id, "measured_property": measured_property,
                "rule_id": rule_id, "value": value}

    @property
    def readouts(self) -> list[dict[str, Any]]:
        return [
            self._readout("phase", "epac.readout.exact-phase.v0", self.phase.to_dict()),
            self._readout("k", "epac.readout.capacity.v0", self.k),
            *[self._readout(f"slots[{slot.order}].facing", "epac.readout.slot-facing.v0", slot.facing)
              for slot in self.slots],
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin_id": self.origin_id,
            "scale": self.scale,
            "domain_name": self.domain_name,
            "phase": self.phase.to_dict(),
            "phase_chart": self.phase_chart,
            "k": self.k,
            "slots": [slot.to_dict() for slot in self.slots],
            "bearing": self._readout("slots[*].facing", BEARING_RULE_ID, list(self.bearing)),
            "readouts": self.readouts,
            "arity": self.arity,
            "shape_signature": list(self.shape_signature),
            "s5_energy_readout": (
                self._readout("slots[*].kind,k", "epac.readout.occupied-slots-over-k.v0",
                              self.s5_energy_readout.to_dict())
                if self.s5_energy_readout is not None else None
            ),
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ScaleOrigin:
        if not isinstance(data, Mapping):
            raise ValueError("scale origin must be an object")
        expected = {
            "origin_id", "scale", "domain_name", "phase", "phase_chart", "k", "slots",
            "bearing", "readouts", "arity", "shape_signature", "s5_energy_readout", "provenance",
        }
        _strict_keys(data, expected, "scale-origin")
        if not isinstance(data["slots"], list):
            raise ValueError("origin slots must be an array")
        origin = cls(
            origin_id=_text(data["origin_id"], "origin_id"),
            scale=_text(data["scale"], "origin scale"),
            domain_name=_text(data["domain_name"], "origin domain_name"),
            phase=ExactRatio.from_dict(data["phase"]),
            phase_chart=_text(data["phase_chart"], "phase_chart"),
            k=_integer(data["k"], "origin k", minimum=1),
            slots=tuple(JoinSlot.from_dict(item) for item in data["slots"]),
            provenance=_text_tuple(data["provenance"], "origin provenance", minimum=1),
        )
        expected_wire = origin.to_dict()
        for field in ("bearing", "readouts", "s5_energy_readout"):
            if _canonical_json(data[field]) != _canonical_json(expected_wire[field]):
                raise ValueError(f"serialized {field} must match its identified state and readout rule")
        if _integer(data["arity"], "origin arity", minimum=0) != origin.arity:
            raise ValueError("serialized arity does not match explicit slots")
        if _text_tuple(data["shape_signature"], "shape_signature") != origin.shape_signature:
            raise ValueError("serialized shape_signature does not match explicit slots")
        return origin


@dataclass(frozen=True, slots=True)
class AuthoredJoin:
    """An authored relation and its structural position, not a state change."""
    join_id: str
    order: int
    source_origin_id: str
    target_origin_id: str
    relation: str
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.join_id, "join_id")
        _integer(self.order, "authored join order", minimum=1)
        _text(self.source_origin_id, "source_origin_id")
        _text(self.target_origin_id, "target_origin_id")
        if self.source_origin_id == self.target_origin_id:
            raise ValueError("join source and target identities must differ")
        if self.relation != ADJACENT_JOIN_RELATION:
            raise ValueError("only the authored adjacent-scale join relation is supported")
        object.__setattr__(
            self, "provenance", _text_tuple(self.provenance, "join provenance", minimum=1)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "join_id": self.join_id,
            "order": self.order,
            "source_origin_id": self.source_origin_id,
            "target_origin_id": self.target_origin_id,
            "relation": self.relation,
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AuthoredJoin:
        if not isinstance(data, Mapping):
            raise ValueError("authored join must be an object")
        _strict_keys(
            data,
            {"join_id", "order", "source_origin_id", "target_origin_id", "relation", "provenance"},
            "authored-join",
        )
        return cls(
            join_id=_text(data["join_id"], "join_id"),
            order=_integer(data["order"], "authored join order", minimum=1),
            source_origin_id=_text(data["source_origin_id"], "source_origin_id"),
            target_origin_id=_text(data["target_origin_id"], "target_origin_id"),
            relation=_text(data["relation"], "join relation"),
            provenance=_text_tuple(data["provenance"], "join provenance", minimum=1),
        )


@dataclass(frozen=True, slots=True)
class LegacyBag:
    scale_slot_counts: tuple[tuple[str, int], ...]
    slot_kind_counts: tuple[tuple[str, int], ...]
    kind: str = "bag"
    excluded_from_tensor: bool = True

    def __post_init__(self) -> None:
        if self.kind != "bag" or self.excluded_from_tensor is not True:
            raise ValueError("legacy bag must remain typed bag and excluded from tensor")
        if tuple(scale for scale, _count in self.scale_slot_counts) != SCALE_IDS:
            raise ValueError("legacy bag must count every scale S0 through S6")
        for scale, count in self.scale_slot_counts:
            _text(scale, "bag scale")
            _integer(count, "bag slot count", minimum=0)
        expected_kinds = tuple(sorted(SLOT_KINDS))
        if tuple(kind for kind, _count in self.slot_kind_counts) != expected_kinds:
            raise ValueError("legacy bag slot kinds must be complete and sorted")
        for kind, count in self.slot_kind_counts:
            _text(kind, "bag slot kind")
            _integer(count, "bag kind count", minimum=0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "excluded_from_tensor": self.excluded_from_tensor,
            "scale_slot_counts": {key: value for key, value in self.scale_slot_counts},
            "slot_kind_counts": {key: value for key, value in self.slot_kind_counts},
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LegacyBag:
        if not isinstance(data, Mapping):
            raise ValueError("legacy bag must be an object")
        _strict_keys(data, {"kind", "excluded_from_tensor", "scale_slot_counts", "slot_kind_counts"}, "legacy-bag")
        scale_counts = data["scale_slot_counts"]
        kind_counts = data["slot_kind_counts"]
        if not isinstance(scale_counts, Mapping) or not isinstance(kind_counts, Mapping):
            raise ValueError("legacy bag counts must be objects")
        return cls(
            kind=_text(data["kind"], "legacy bag kind"),
            excluded_from_tensor=data["excluded_from_tensor"],
            scale_slot_counts=tuple((key, _integer(value, f"{key} slot count", minimum=0)) for key, value in scale_counts.items()),
            slot_kind_counts=tuple((key, _integer(value, f"{key} kind count", minimum=0)) for key, value in kind_counts.items()),
        )


def _license_record() -> dict[str, Any]:
    return {
        "application_id": METAPAT_APPLICATION_ID,
        "application_version": METAPAT_APPLICATION_VERSION,
        "application_digest": METAPAT_APPLICATION_DIGEST,
        "authority": "The-Interdependency/metapat",
        "authority_transfer": False,
    }


def _field_binding_record() -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for key, value in sorted(SEMANTIC_FIELD_BINDINGS.items()):
        role = value["application_role"]
        spine = value["spine_name"]
        module_id = _METAPAT_APPLICATION_ROLE_MODULES.get(role)
        allowed_spines = _APPLICATION_ROLE_ALLOWED_SPINES.get(role, frozenset())
        if module_id is None or spine not in allowed_spines:
            raise RuntimeError(f"unlicensed METAPAT semantic pair for {key}")
        records[key] = {**value, "catalog_module_id": module_id}
    return records


def _bag_for(origins: Sequence[ScaleOrigin]) -> LegacyBag:
    scale_counts = tuple((origin.scale, len(origin.slots)) for origin in origins)
    kind_counts = tuple(
        (kind, sum(slot.kind == kind for origin in origins for slot in origin.slots))
        for kind in sorted(SLOT_KINDS)
    )
    return LegacyBag(scale_counts, kind_counts)


@dataclass(frozen=True, slots=True)
class EPACJoinTree:
    origins: tuple[ScaleOrigin, ...]
    joins: tuple[AuthoredJoin, ...]
    legacy_bag: LegacyBag
    object_kind: str = "multi-origin-join-tree"
    schema_id: str = JOIN_TREE_SCHEMA_ID
    schema_version: str = JOIN_TREE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.object_kind != "multi-origin-join-tree":
            raise ValueError("a bag cannot pass as a multi-origin join tree")
        if self.schema_id != JOIN_TREE_SCHEMA_ID or self.schema_version != JOIN_TREE_SCHEMA_VERSION:
            raise ValueError("unsupported EPAC join-tree schema")
        origins = tuple(self.origins)
        joins = tuple(self.joins)
        if any(not isinstance(item, ScaleOrigin) for item in origins):
            raise ValueError("origins must contain ScaleOrigin values")
        if any(not isinstance(item, AuthoredJoin) for item in joins):
            raise ValueError("joins must contain AuthoredJoin values")
        if tuple(origin.scale for origin in origins) != SCALE_IDS:
            raise ValueError("tensor must contain exactly one ordered origin S0 through S6")
        origin_ids = tuple(origin.origin_id for origin in origins)
        if len(set(origin_ids)) != len(origin_ids):
            raise ValueError("origin identities must be unique")
        if len(joins) != 6:
            raise ValueError("tensor must contain exactly six adjacent-scale joins")
        join_ids = tuple(item.join_id for item in joins)
        if len(set(join_ids)) != 6:
            raise ValueError("join identities must be unique")
        leftover_ids = tuple(
            slot.participant_id
            for origin in origins
            for slot in origin.slots
            if slot.kind == "leftover"
        )
        declared_object_ids = origin_ids + join_ids + leftover_ids
        if len(set(declared_object_ids)) != len(declared_object_ids):
            raise ValueError(
                "origin, join, and leftover object identities must be globally unique"
            )
        if tuple(item.order for item in joins) != tuple(range(1, 7)):
            raise ValueError("authored join order must be exactly 1 through 6")
        for index, origin in enumerate(origins):
            members = tuple(slot for slot in origin.slots if slot.kind == "member")
            if index == 0:
                if members:
                    raise ValueError("S0 cannot contain a lower-scale member reference")
                continue
            previous = origins[index - 1]
            if len(members) != 1:
                raise ValueError(f"{origin.scale} must contain exactly one adjacent-scale member")
            member = members[0]
            if member.participant_id != previous.origin_id or member.participant_scale != previous.scale:
                raise ValueError(f"{origin.scale} member must reference the immediately preceding origin")
            event = joins[index - 1]
            if event.source_origin_id != previous.origin_id or event.target_origin_id != origin.origin_id:
                raise ValueError(f"join {event.order} does not match adjacent origins")
        if not isinstance(self.legacy_bag, LegacyBag) or self.legacy_bag != _bag_for(origins):
            raise ValueError("legacy bag must be the exact lossy projection of the tree")
        object.__setattr__(self, "origins", origins)
        object.__setattr__(self, "joins", joins)
        if _semantic_wire_field_paths(self._payload()) != REQUIRED_SEMANTIC_FIELD_PATHS:
            raise RuntimeError("semantic field bindings do not cover the live wire schema")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "object_kind": self.object_kind,
            "semantic_license": _license_record(),
            "semantic_field_bindings": _field_binding_record(),
            "origins": [origin.to_dict() for origin in self.origins],
            "joins": [item.to_dict() for item in self.joins],
            "legacy_bag": self.legacy_bag.to_dict(),
        }

    @property
    def candidate_digest(self) -> str:
        return _sha256(_canonical_json(self._payload()).encode("utf-8"))

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "candidate_digest": self.candidate_digest}

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EPACJoinTree:
        if not isinstance(data, Mapping):
            raise ValueError("EPAC join tree must be an object")
        expected = {
            "schema_id", "schema_version", "object_kind", "semantic_license",
            "semantic_field_bindings", "origins", "joins", "legacy_bag",
            "candidate_digest",
        }
        _strict_keys(data, expected, "EPAC-join-tree")
        if data["semantic_license"] != _license_record():
            raise ValueError("semantic license identity mismatch")
        if data["semantic_field_bindings"] != _field_binding_record():
            raise ValueError("semantic field bindings are incomplete or changed")
        if set(data["semantic_field_bindings"]) != REQUIRED_SEMANTIC_FIELD_PATHS:
            raise ValueError("semantic field bindings do not cover the complete declared wire")
        if not isinstance(data["origins"], list) or not isinstance(data["joins"], list):
            raise ValueError("origins and joins must be arrays")
        tree = cls(
            schema_id=_text(data["schema_id"], "schema_id"),
            schema_version=_text(data["schema_version"], "schema_version"),
            object_kind=_text(data["object_kind"], "object_kind"),
            origins=tuple(ScaleOrigin.from_dict(item) for item in data["origins"]),
            joins=tuple(AuthoredJoin.from_dict(item) for item in data["joins"]),
            legacy_bag=LegacyBag.from_dict(data["legacy_bag"]),
        )
        raw_payload = {key: value for key, value in data.items() if key != "candidate_digest"}
        if _canonical_json(raw_payload) != _canonical_json(tree._payload()):
            raise ValueError("non-canonical EPAC join-tree payload")
        if _text(data["candidate_digest"], "candidate_digest") != tree.candidate_digest:
            raise ValueError("candidate_digest mismatch")
        return tree

    @classmethod
    def from_json(cls, text: str) -> EPACJoinTree:
        try:
            data = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid EPAC join-tree JSON") from exc
        return cls.from_dict(data)


def _slot(
    name: str,
    order: int,
    kind: str,
    facing: int,
    participant_id: str | None = None,
    participant_scale: str | None = None,
) -> JoinSlot:
    return JoinSlot(name, order, kind, participant_id, participant_scale, facing)


def construct_epac_join_tree(
    *,
    identity_namespace: str = "fixture-a",
    s2_seating_order: tuple[str, str, str] = ("core", "guest", "vacancy"),
    phase_chart_overrides: Mapping[str, str] | None = None,
) -> EPACJoinTree:
    """Construct the bounded public candidate with one origin at every scale.

    ``s2_seating_order`` may reorder the same three S2 seats.  It exists to
    exhibit that a bag of counts is not a join tree.  It does not infer a join.
    """
    namespace = _text(identity_namespace, "identity_namespace")
    if set(s2_seating_order) != {"core", "guest", "vacancy"} or len(s2_seating_order) != 3:
        raise ValueError("s2_seating_order must be a permutation of core, guest, vacancy")
    charts = {scale: ("visible" if index % 2 == 0 else "lifted") for index, scale in enumerate(SCALE_IDS)}
    for scale, chart in dict(phase_chart_overrides or {}).items():
        if scale not in SCALE_IDS or chart not in PHASE_CHARTS:
            raise ValueError("phase chart overrides must map S0 through S6 to visible or lifted")
        charts[scale] = chart
    origin_ids = {scale: f"epac.origin:{namespace}:{scale}" for scale in SCALE_IDS}
    phases = (
        ExactRatio(0, 1), ExactRatio(1, 8), ExactRatio(1, 4), ExactRatio(3, 8),
        ExactRatio(1, 2), ExactRatio(5, 8), ExactRatio(3, 4),
    )

    origins: list[ScaleOrigin] = []
    origins.append(
        ScaleOrigin(
            origin_ids["S0"], "S0", SCALE_DOMAIN_NAMES[0], phases[0], charts["S0"], 2,
            (
                _slot("seed", 0, "leftover", -2, f"epac.leftover:{namespace}:S0:seed"),
                _slot("zero", 1, "hole", 0),
            ),
            ("epac.join-term-v0", "declared-scale:S0"),
        )
    )
    origins.append(
        ScaleOrigin(
            origin_ids["S1"], "S1", SCALE_DOMAIN_NAMES[1], phases[1], charts["S1"], 2,
            (
                _slot("subatomic", 0, "member", 4, origin_ids["S0"], "S0"),
                _slot("zero", 1, "hole", 0),
            ),
            ("epac.join-term-v0", "declared-scale:S1"),
        )
    )
    s2_templates = {
        "core": ("member", 3, origin_ids["S1"], "S1"),
        "guest": ("leftover", -3, f"epac.leftover:{namespace}:S2:guest", None),
        "vacancy": ("hole", 0, None, None),
    }
    s2_slots = tuple(
        _slot(name, order, *s2_templates[name])
        for order, name in enumerate(s2_seating_order)
    )
    origins.append(
        ScaleOrigin(
            origin_ids["S2"], "S2", SCALE_DOMAIN_NAMES[2], phases[2], charts["S2"], 3,
            s2_slots,
            ("epac.join-term-v0", "declared-scale:S2", "authored-seating-chart"),
        )
    )
    fixed_slots = {
        "S3": (
            _slot("join", 0, "member", -5, origin_ids["S2"], "S2"),
            _slot("zero", 1, "hole", 0),
            _slot("embed-context", 2, "leftover", 2, f"epac.leftover:{namespace}:S3:context"),
        ),
        "S4": (
            _slot("embed", 0, "member", 2, origin_ids["S3"], "S3"),
            _slot("electronic-context", 1, "leftover", -1, f"epac.leftover:{namespace}:S4:context"),
        ),
        "S5": (
            _slot("electronic-state", 0, "member", 7, origin_ids["S4"], "S4"),
            _slot("zero-a", 1, "hole", 0),
            _slot("occupancy-context", 2, "leftover", -2, f"epac.leftover:{namespace}:S5:context"),
            _slot("zero-b", 3, "hole", 0),
        ),
        "S6": (
            _slot("energy-readout", 0, "member", 1, origin_ids["S5"], "S5"),
            _slot("ensemble-context", 1, "leftover", -1, f"epac.leftover:{namespace}:S6:context"),
        ),
    }
    for index in range(3, 7):
        scale = f"S{index}"
        slots = fixed_slots[scale]
        origins.append(
            ScaleOrigin(
                origin_ids[scale], scale, SCALE_DOMAIN_NAMES[index], phases[index], charts[scale],
                len(slots), slots, ("epac.join-term-v0", f"declared-scale:{scale}"),
            )
        )
    joins = tuple(
        AuthoredJoin(
            join_id=f"epac.join:{namespace}:S{index - 1}-S{index}",
            order=index,
            source_origin_id=origin_ids[f"S{index - 1}"],
            target_origin_id=origin_ids[f"S{index}"],
            relation=ADJACENT_JOIN_RELATION,
            provenance=("epac.join-term-v0", f"authored-near-join:S{index - 1}->S{index}"),
        )
        for index in range(1, 7)
    )
    origin_tuple = tuple(origins)
    return EPACJoinTree(origin_tuple, joins, _bag_for(origin_tuple))


def recover_epac_join_tree(public_bytes: bytes | str) -> EPACJoinTree:
    """Recover and validate the tree from public bytes only."""
    if isinstance(public_bytes, bytes):
        try:
            text = public_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("EPAC join-tree bytes must be UTF-8") from exc
    elif isinstance(public_bytes, str):
        text = public_bytes
    else:
        raise TypeError("public_bytes must be bytes or str")
    return EPACJoinTree.from_json(text)


def legacy_bag_projection(tree: EPACJoinTree) -> dict[str, Any]:
    """Return the explicitly lossy count bag kept beside, not as, the tree."""
    if not isinstance(tree, EPACJoinTree):
        raise TypeError("tree must be EPACJoinTree")
    return tree.legacy_bag.to_dict()


def _structural_signature(tree: EPACJoinTree) -> tuple[Any, ...]:
    by_id = {origin.origin_id: origin.scale for origin in tree.origins}
    leftover_by_id = {
        slot.participant_id: index
        for index, slot in enumerate(
            slot
            for origin in tree.origins
            for slot in origin.slots
            if slot.kind == "leftover"
        )
    }
    origin_rows = []
    for origin in tree.origins:
        slot_rows = tuple(
            (
                slot.name,
                slot.order,
                slot.kind,
                (
                    by_id.get(slot.participant_id)
                    if slot.kind == "member"
                    else ("leftover", leftover_by_id[slot.participant_id])
                    if slot.kind == "leftover"
                    else None
                ),
                slot.participant_scale,
                slot.facing,
            )
            for slot in origin.slots
        )
        origin_rows.append(
            (
                origin.scale,
                origin.domain_name,
                origin.phase.numerator,
                origin.phase.denominator,
                origin.phase_chart,
                origin.k,
                slot_rows,
                origin.bearing,
                origin.arity,
                origin.shape_signature,
                origin.s5_energy_readout.to_dict() if origin.s5_energy_readout else None,
                origin.provenance,
            )
        )
    event_rows = tuple(
        (
            item.order,
            by_id[item.source_origin_id],
            by_id[item.target_origin_id],
            item.relation,
            item.provenance,
        )
        for item in tree.joins
    )
    return tuple(origin_rows), event_rows


def join_isomorphic(left: EPACJoinTree, right: EPACJoinTree) -> bool:
    """Return label-preserving join isomorphism, excluding instance IDs/bag."""
    if not isinstance(left, EPACJoinTree) or not isinstance(right, EPACJoinTree):
        raise TypeError("join_isomorphic requires two EPACJoinTree values")
    return _structural_signature(left) == _structural_signature(right)


def trace_origin_lineage(tree: EPACJoinTree, target_origin_id: str) -> tuple[str, ...]:
    """Replay exact authored ancestry from S0 through the requested origin."""
    if not isinstance(tree, EPACJoinTree):
        raise TypeError("tree must be EPACJoinTree")
    _text(target_origin_id, "target_origin_id")
    by_target = {item.target_origin_id: item.source_origin_id for item in tree.joins}
    known = {origin.origin_id for origin in tree.origins}
    if target_origin_id not in known:
        raise ValueError("target origin is not present in the tree")
    reversed_path = [target_origin_id]
    while reversed_path[-1] in by_target:
        reversed_path.append(by_target[reversed_path[-1]])
    return tuple(reversed(reversed_path))


__all__ = [
    "ADJACENT_JOIN_RELATION",
    "BEARING_RULE_ID",
    "JOIN_TREE_SCHEMA_ID",
    "JOIN_TREE_SCHEMA_VERSION",
    "METAPAT_APPLICATION_DIGEST",
    "METAPAT_APPLICATION_ID",
    "METAPAT_APPLICATION_VERSION",
    "REQUIRED_SEMANTIC_FIELD_PATHS",
    "SCALE_DOMAIN_NAMES",
    "SCALE_IDS",
    "SEMANTIC_FIELD_BINDINGS",
    "EPACJoinTree",
    "ExactRatio",
    "JoinSlot",
    "AuthoredJoin",
    "LegacyBag",
    "ScaleOrigin",
    "construct_epac_join_tree",
    "join_isomorphic",
    "legacy_bag_projection",
    "recover_epac_join_tree",
    "trace_origin_lineage",
]
