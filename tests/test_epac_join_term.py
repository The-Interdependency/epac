"""Correctness and public-only recovery witnesses for EPAC join term v0."""

# === CHECKS ===
# id: check_epac_join_tree_complete_scale_tensor
#   proves: epac_join_tree_complete_scale_tensor
#   call: self::test_complete_s0_through_s6_tensor
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_explicit_boundary
#   proves: epac_join_tree_explicit_boundary
#   call: self::test_boundaries_store_named_ordered_holes_and_leftovers
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_inferred_bearing
#   proves: epac_join_tree_inferred_bearing
#   call: self::test_bearing_is_inferred_and_tamper_rejected
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_recursive_identity
#   proves: epac_join_tree_recursive_identity
#   call: self::test_recursive_origins_and_joins_are_adjacent
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_s5_energy_qualified
#   proves: epac_join_tree_s5_energy_qualified
#   call: self::test_s5_readout_is_exact_occupancy_only
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_semantic_customs
#   proves: epac_join_tree_semantic_customs
#   call: self::test_every_declared_semantic_field_is_dual_named
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_join_isomorphism
#   proves: epac_join_tree_join_isomorphism
#   call: self::test_join_isomorphism_preserves_structure_not_instance_ids
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_bag_is_lossy
#   proves: epac_join_tree_bag_is_lossy
#   call: self::test_same_bag_different_tree_and_bag_cannot_parse
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_public_recovery
#   proves: epac_join_tree_public_recovery
#   call: self::test_public_receipt_recovers_without_constructor_state
#   mutates: filesystem_read
#   cleanup: none
#
# id: check_epac_join_tree_strict_rejection
#   proves: epac_join_tree_strict_rejection
#   call: self::test_malformed_wires_fail_closed
#   mutates: none
#   cleanup: none
#
# id: check_epac_join_tree_deterministic_serialization
#   proves: epac_join_tree_deterministic_serialization
#   call: self::test_serialization_and_receipt_regeneration_are_deterministic
#   mutates: filesystem_read
#   cleanup: none
#
# id: check_epac_join_tree_existing_falsification_preserved
#   proves: epac_join_tree_existing_falsification_preserved
#   call: self::test_molecular_shape_falsification_remains_unchanged
#   mutates: filesystem_read
#   cleanup: none
#
# id: check_epac_join_tree_readout_boundary
#   proves: epac_join_tree_readout_boundary
#   call: self::test_readouts_identify_state_without_replacing_it
#   mutates: temporary_files
#   cleanup: pytest_tmp_path
#
# id: check_epac_join_tree_conditional_roles
#   proves: epac_join_tree_conditional_roles
#   call: self::test_merged_producer_and_conditional_roles
#   mutates: temporary_files
#   cleanup: pytest_tmp_path
#
# id: check_epac_join_tree_canonical_wire
#   proves: epac_join_tree_canonical_wire
#   call: self::test_noncanonical_ratios_rejected_even_with_recomputed_digest
#   mutates: temporary_files
#   cleanup: pytest_tmp_path
#
# id: check_epac_join_generator_direct_invocation
#   proves: epac_join_generator_direct_invocation
#   call: self::test_generator_runs_directly_without_installation
#   mutates: temporary_files
#   cleanup: pytest_tmp_path
#
# id: check_epac_join_generator_source_identity
#   proves: epac_join_generator_source_identity
#   call: self::test_generator_rejects_mismatched_source_before_writing
#   mutates: temporary_files
#   cleanup: pytest_tmp_path
# === END CHECKS ===

import json
import hashlib
import os
import subprocess
import sys
from copy import deepcopy
from importlib.resources import files
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

import epac_join_term
from epac_comparison import compare_after_construction
from epac_join_term import (
    METAPAT_APPLICATION_DIGEST,
    REQUIRED_SEMANTIC_FIELD_PATHS,
    SCALE_IDS,
    EPACJoinTree,
    ExactRatio,
    construct_epac_join_tree,
    join_isomorphic,
    legacy_bag_projection,
    recover_epac_join_tree,
    trace_origin_lineage,
)

ROOT = Path(__file__).resolve().parents[1]


def _fixture_receipt() -> dict:
    return json.loads(
        files("epac_data").joinpath("epac-join-term-v0-receipt.json").read_text(encoding="utf-8")
    )


def test_complete_s0_through_s6_tensor() -> None:
    tree = construct_epac_join_tree()
    assert tuple(origin.scale for origin in tree.origins) == SCALE_IDS
    assert len(tree.origins) == 7
    assert len(tree.joins) == 6
    assert tuple(item.order for item in tree.joins) == tuple(range(1, 7))
    assert len({origin.origin_id for origin in tree.origins}) == 7


def test_boundaries_store_named_ordered_holes_and_leftovers() -> None:
    tree = construct_epac_join_tree()
    for origin in tree.origins:
        assert origin.k == len(origin.slots)
        assert tuple(slot.order for slot in origin.slots) == tuple(range(origin.k))
        assert len({slot.name for slot in origin.slots}) == origin.k
        assert origin.arity == sum(slot.kind != "hole" for slot in origin.slots)
        assert origin.shape_signature == tuple(
            f"{slot.order}:{slot.name}:{slot.kind}" for slot in origin.slots
        )
    holes = [slot for origin in tree.origins for slot in origin.slots if slot.kind == "hole"]
    leftovers = [slot for origin in tree.origins for slot in origin.slots if slot.kind == "leftover"]
    assert holes and leftovers
    assert all(slot.participant_id is None and slot.participant_scale is None for slot in holes)
    assert all(slot.participant_id and slot.participant_scale is None for slot in leftovers)
    declared_object_ids = (
        [origin.origin_id for origin in tree.origins]
        + [event.join_id for event in tree.joins]
        + [slot.participant_id for slot in leftovers]
    )
    assert len(declared_object_ids) == len(set(declared_object_ids))


def test_bearing_is_inferred_and_tamper_rejected() -> None:
    tree = construct_epac_join_tree()
    assert all(
        origin.bearing
        == tuple((slot.facing > 0) - (slot.facing < 0) for slot in origin.slots)
        for origin in tree.origins
    )
    tampered = tree.to_dict()
    tampered["origins"][2]["bearing"]["value"][0] *= -1
    with pytest.raises(ValueError, match="bearing"):
        EPACJoinTree.from_dict(tampered)


def test_recursive_origins_and_joins_are_adjacent() -> None:
    tree = construct_epac_join_tree()
    for index in range(1, 7):
        source = tree.origins[index - 1]
        target = tree.origins[index]
        members = [slot for slot in target.slots if slot.kind == "member"]
        assert len(members) == 1
        assert (members[0].participant_id, members[0].participant_scale) == (
            source.origin_id,
            source.scale,
        )
        event = tree.joins[index - 1]
        assert (event.source_origin_id, event.target_origin_id) == (
            source.origin_id,
            target.origin_id,
        )
    assert trace_origin_lineage(tree, tree.origins[-1].origin_id) == tuple(
        origin.origin_id for origin in tree.origins
    )


def test_s5_readout_is_exact_occupancy_only() -> None:
    tree = construct_epac_join_tree()
    for origin in tree.origins:
        if origin.scale == "S5":
            assert origin.s5_energy_readout == ExactRatio(2, 4) == ExactRatio(1, 2)
        else:
            assert origin.s5_energy_readout is None
    text = (ROOT / "docs/multi-origin-join-term-v0.md").read_text(encoding="utf-8")
    assert "establishes no physical energy" in text


def test_every_declared_semantic_field_is_dual_named() -> None:
    tree = construct_epac_join_tree()
    original_digest = tree.candidate_digest
    wire = tree.to_dict()
    assert set(wire["semantic_field_bindings"]) == REQUIRED_SEMANTIC_FIELD_PATHS
    assert epac_join_term._semantic_wire_field_paths(wire) == REQUIRED_SEMANTIC_FIELD_PATHS
    assert epac_join_term._WIRE_METADATA_FIELDS == {
        "candidate_digest",
        "schema_id",
        "schema_version",
        "semantic_field_bindings",
        "semantic_license",
    }
    assert wire["semantic_license"]["application_digest"] == METAPAT_APPLICATION_DIGEST
    for binding in wire["semantic_field_bindings"].values():
        assert set(binding) == {
            "spine_name",
            "domain_name",
            "application_role",
            "catalog_module_id",
        }
        assert all(isinstance(value, str) and value for value in binding.values())
        assert binding["catalog_module_id"] == epac_join_term._METAPAT_APPLICATION_ROLE_MODULES[
            binding["application_role"]
        ]
        assert binding["spine_name"] in epac_join_term._APPLICATION_ROLE_ALLOWED_SPINES[
            binding["application_role"]
        ]
    assert set(epac_join_term._METAPAT_APPLICATION_ROLE_MODULES) == {
        "customs-boundary",
        "stored-join-term",
        "join-boundary",
        "origin-state",
        "scale-origin",
        "multi-origin-tensor",
        "authored-near-join",
        "recursive-origin",
        "state-metric",
        "join-transformation",
        "transformation-sequence",
        "domain-customs",
    }
    with pytest.raises(TypeError):
        epac_join_term.SEMANTIC_FIELD_BINDINGS["origin.phase"]["spine_name"] = "MUTATED"
    with pytest.raises(TypeError):
        epac_join_term.SEMANTIC_FIELD_BINDINGS["new.path"] = {}
    with pytest.raises(TypeError):
        epac_join_term._METAPAT_APPLICATION_ROLE_MODULES["origin-state"] = "MUTATED"
    with pytest.raises(TypeError):
        epac_join_term._APPLICATION_ROLE_ALLOWED_SPINES["origin-state"] = frozenset()
    wire["semantic_field_bindings"]["origin.phase"]["spine_name"] = "MUTATED"
    assert tree.candidate_digest == original_digest
    assert tree.to_dict()["semantic_field_bindings"]["origin.phase"]["spine_name"] == "State"


def test_join_isomorphism_preserves_structure_not_instance_ids() -> None:
    original = construct_epac_join_tree(identity_namespace="first")
    renamed = construct_epac_join_tree(identity_namespace="second")
    reordered = construct_epac_join_tree(s2_seating_order=("guest", "core", "vacancy"))
    lifted_s0 = construct_epac_join_tree(phase_chart_overrides={"S0": "lifted"})
    assert join_isomorphic(original, renamed)
    assert not join_isomorphic(original, reordered)
    assert not join_isomorphic(original, lifted_s0)


def test_same_bag_different_tree_and_bag_cannot_parse() -> None:
    first = construct_epac_join_tree(s2_seating_order=("core", "guest", "vacancy"))
    second = construct_epac_join_tree(s2_seating_order=("guest", "core", "vacancy"))
    renamed = construct_epac_join_tree(identity_namespace="renamed")
    assert legacy_bag_projection(first) == legacy_bag_projection(second)
    assert not join_isomorphic(first, second)
    assert legacy_bag_projection(first) == legacy_bag_projection(renamed)
    assert join_isomorphic(first, renamed)
    assert trace_origin_lineage(first, first.origins[-1].origin_id) != trace_origin_lineage(
        renamed, renamed.origins[-1].origin_id
    )
    with pytest.raises(ValueError):
        recover_epac_join_tree(json.dumps(legacy_bag_projection(first)))


def test_public_receipt_recovers_without_constructor_state(monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = _fixture_receipt()
    public_tree_json = json.dumps(
        receipt["candidate"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    monkeypatch.setattr(
        epac_join_term,
        "construct_epac_join_tree",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("constructor state consulted")),
    )
    recovered = recover_epac_join_tree(public_tree_json.encode("utf-8"))
    assert recovered.candidate_digest == receipt["results"]["candidate_digest"]
    assert trace_origin_lineage(recovered, recovered.origins[-1].origin_id) == tuple(
        receipt["results"]["s6_lineage"]
    )


def test_malformed_wires_fail_closed() -> None:
    tree = construct_epac_join_tree()
    duplicate = '{"schema_id":"first","schema_id":"second"}'
    with pytest.raises(ValueError, match="duplicate JSON key"):
        recover_epac_join_tree(duplicate)

    mutations = []
    unknown = tree.to_dict()
    unknown["circle_count"] = 4
    mutations.append(unknown)
    missing = tree.to_dict()
    del missing["origins"][0]["slots"][1]["participant_id"]
    mutations.append(missing)
    invalid_modulus = tree.to_dict()
    invalid_modulus["origins"][0]["phase"]["denominator"] = 0
    mutations.append(invalid_modulus)
    duplicate_origin = tree.to_dict()
    duplicate_origin["origins"][1]["origin_id"] = duplicate_origin["origins"][0]["origin_id"]
    mutations.append(duplicate_origin)
    duplicate_leftover = tree.to_dict()
    leftover_rows = [
        slot
        for origin in duplicate_leftover["origins"]
        for slot in origin["slots"]
        if slot["kind"] == "leftover"
    ]
    leftover_rows[1]["participant_id"] = leftover_rows[0]["participant_id"]
    mutations.append(duplicate_leftover)
    leftover_origin_collision = tree.to_dict()
    next(
        slot
        for origin in leftover_origin_collision["origins"]
        for slot in origin["slots"]
        if slot["kind"] == "leftover"
    )["participant_id"] = leftover_origin_collision["origins"][0]["origin_id"]
    mutations.append(leftover_origin_collision)
    join_origin_collision = tree.to_dict()
    join_origin_collision["joins"][0]["join_id"] = (
        join_origin_collision["origins"][0]["origin_id"]
    )
    mutations.append(join_origin_collision)
    duplicate_join = tree.to_dict()
    duplicate_join["joins"][1]["join_id"] = (
        duplicate_join["joins"][0]["join_id"]
    )
    mutations.append(duplicate_join)
    leftover_join_collision = tree.to_dict()
    next(
        slot
        for origin in leftover_join_collision["origins"]
        for slot in origin["slots"]
        if slot["kind"] == "leftover"
    )["participant_id"] = leftover_join_collision["joins"][0][
        "join_id"
    ]
    mutations.append(leftover_join_collision)
    skip_scale = tree.to_dict()
    member = next(slot for slot in skip_scale["origins"][2]["slots"] if slot["kind"] == "member")
    member["participant_id"] = skip_scale["origins"][0]["origin_id"]
    member["participant_scale"] = "S0"
    mutations.append(skip_scale)
    inconsistent_event = tree.to_dict()
    inconsistent_event["joins"][0]["target_origin_id"] = inconsistent_event["origins"][2]["origin_id"]
    mutations.append(inconsistent_event)
    incomplete_license = tree.to_dict()
    del incomplete_license["semantic_field_bindings"]["origin.phase"]
    mutations.append(incomplete_license)
    bag_masquerade = tree.to_dict()
    bag_masquerade["object_kind"] = "bag"
    mutations.append(bag_masquerade)
    boolean_bearing = tree.to_dict()
    boolean_bearing["origins"][1]["bearing"]["value"][0] = True
    mutations.append(boolean_bearing)

    for mutation in mutations:
        with pytest.raises(ValueError):
            EPACJoinTree.from_dict(deepcopy(mutation))


def test_serialization_and_receipt_regeneration_are_deterministic() -> None:
    first = construct_epac_join_tree()
    second = construct_epac_join_tree()
    assert first.to_json() == second.to_json()
    assert first.candidate_digest == second.candidate_digest
    receipt_path = ROOT / "data/epac-join-term-v0-receipt.json"
    audit_path = ROOT / "docs/epac-join-term-v0-audit.md"
    assert receipt_path.read_bytes().endswith(b"\n")
    assert audit_path.read_bytes().endswith(b"\n")
    generator_path = ROOT / "tools/generate_join_term_v0.py"
    spec = spec_from_file_location("epac_join_term_v0_generator_fixture", generator_path)
    assert spec is not None and spec.loader is not None
    generator = module_from_spec(spec)
    spec.loader.exec_module(generator)

    rendered_receipt = generator.render_receipt(ROOT)
    assert receipt_path.read_text(encoding="utf-8") == rendered_receipt
    assert audit_path.read_text(encoding="utf-8") == generator.render_audit(
        json.loads(rendered_receipt)
    )


def test_molecular_shape_falsification_remains_unchanged() -> None:
    standings = compare_after_construction()["standings"]
    for name in (
        "charged_3_structure_as_sealed_shape_prediction",
        "topology_3_structure_as_sealed_shape_prediction",
        "ucns_mobius_as_sealed_shape_prediction",
        "atomic_shells_as_sealed_shape_prediction",
    ):
        assert standings[name] == "FALSIFIED"


def _generator():
    spec = spec_from_file_location("epac_join_generator_identity_test", ROOT / "tools/generate_join_term_v0.py")
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rehash(wire):
    payload = {key: value for key, value in wire.items() if key != "candidate_digest"}
    wire["candidate_digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def test_readouts_identify_state_without_replacing_it() -> None:
    tree = construct_epac_join_tree()
    original_bytes = tree.to_json()
    for origin in tree.origins:
        wire = origin.to_dict()
        assert wire["phase"] == origin.phase.to_dict()
        assert wire["k"] == origin.k
        assert wire["readouts"][0] == {
            "origin_id": origin.origin_id, "measured_property": "phase",
            "rule_id": "epac.readout.exact-phase.v0", "value": origin.phase.to_dict(),
        }
        assert wire["readouts"][1]["measured_property"] == "k"
        assert wire["readouts"][1]["value"] == origin.k
        for slot, readout in zip(origin.slots, wire["readouts"][2:]):
            assert readout["measured_property"] == f"slots[{slot.order}].facing"
            assert readout["value"] == slot.facing
        records = wire["readouts"] + [wire["bearing"]]
        if wire["s5_energy_readout"] is not None:
            records.append(wire["s5_energy_readout"])
        for readout in records:
            assert readout["origin_id"] == origin.origin_id
            assert readout["measured_property"] and readout["rule_id"]
        wire["readouts"][0]["value"]["numerator"] += 1
    assert tree.to_json() == original_bytes
    for field in ("origin_id", "measured_property", "rule_id", "value"):
        wire = tree.to_dict()
        wire["origins"][0]["readouts"][0][field] = "unrelated"
        _rehash(wire)
        with pytest.raises(ValueError, match="readouts"):
            EPACJoinTree.from_dict(wire)
    wire = tree.to_dict()
    wire["origins"][0]["readouts"][0]["value"]["numerator"] = False
    _rehash(wire)
    with pytest.raises(ValueError, match="readouts"):
        EPACJoinTree.from_dict(wire)


def test_merged_producer_and_conditional_roles() -> None:
    producer_bytes = files("epac_data").joinpath("metapat-epac-join-terms-application-v4.json").read_bytes()
    producer = json.loads(producer_bytes)
    generator = _generator()
    assert hashlib.sha256(producer_bytes).hexdigest() == generator.METAPAT_APPLICATION_FIXTURE_SHA256
    assert producer["application_digest"] == METAPAT_APPLICATION_DIGEST
    assert {item["application_role"]: item["module_id"] for item in producer["catalog_bindings"]} == epac_join_term._METAPAT_APPLICATION_ROLE_MODULES
    tree = construct_epac_join_tree()
    bindings = tree.to_dict()["semantic_field_bindings"]
    assert {row["spine_name"] for row in bindings.values()}.isdisjoint({"Vector", "Transformation", "Time"})
    assert bindings["origin.phase"]["spine_name"] == "State"
    assert bindings["slot.facing"]["spine_name"] == "State"
    assert bindings["origin.readouts"]["spine_name"] == "Scalar"
    assert bindings["origin.bearing"]["spine_name"] == "Scalar"
    assert bindings["tree.joins"]["application_role"] == "authored-near-join"
    assert "joins" in tree.to_dict() and "transformations" not in tree.to_dict()
    for path, role, spine in [("origin.bearing", "inferred-bearing", "Vector"),
                              ("join.join_id", "join-transformation", "Transformation"),
                              ("join.order", "transformation-sequence", "Time")]:
        wire = tree.to_dict()
        wire["semantic_field_bindings"][path].update(application_role=role, spine_name=spine)
        _rehash(wire)
        with pytest.raises(ValueError, match="semantic field bindings"):
            EPACJoinTree.from_dict(wire)


def test_noncanonical_ratios_rejected_even_with_recomputed_digest() -> None:
    tree = construct_epac_join_tree()
    # Nonzero phase, zero phase, phase readout, and occupancy readout.
    for origin_index, field in [(1, "phase"), (0, "phase"), (1, "readouts"), (5, "s5_energy_readout")]:
        for rehash in (False, True):
            wire = tree.to_dict()
            ratio = wire["origins"][origin_index][field]
            if field == "readouts":
                ratio = ratio[0]["value"]
            elif field == "s5_energy_readout":
                ratio = ratio["value"]
            ratio["numerator"] *= 2
            ratio["denominator"] *= 2
            if rehash:
                _rehash(wire)
            with pytest.raises(ValueError):
                EPACJoinTree.from_dict(wire)
    assert ExactRatio(2, 16) == ExactRatio(1, 8)  # typed construction still reduces
    assert EPACJoinTree.from_json(tree.to_json()) == tree
    # JSON parsing must not erase a different encoding under the same digest.
    canonical = tree.to_json()
    variants = [
        canonical + "\n",
        " " + canonical,
        json.dumps(tree.to_dict(), sort_keys=True, indent=2),
        json.dumps(tree.to_dict(), sort_keys=False, separators=(",", ":")),
        canonical.replace('"numerator":0', '"numerator":-0', 1),
    ]
    unicode_tree = construct_epac_join_tree(identity_namespace="fixture-é")
    variants.append(json.dumps(unicode_tree.to_dict(), sort_keys=True, separators=(",", ":")))
    for encoded in variants:
        assert encoded != EPACJoinTree.from_dict(json.loads(encoded)).to_json()
        with pytest.raises(ValueError, match="canonical encoding"):
            recover_epac_join_tree(encoded.encode("utf-8"))
    assert recover_epac_join_tree(unicode_tree.to_json().encode("utf-8")) == unicode_tree


def test_generator_runs_directly_without_installation(tmp_path) -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    # -S disables site packages and editable-install hooks. CWD is outside source.
    result = subprocess.run(
        [sys.executable, "-S", str(ROOT / "tools/generate_join_term_v0.py"), "--check"],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("CURRENT") == 2


def test_generator_rejects_mismatched_source_before_writing(tmp_path, monkeypatch) -> None:
    generator = _generator()
    with pytest.raises(ValueError, match="checkout containing this generator"):
        generator.write_outputs(tmp_path)
    assert not list(tmp_path.iterdir())
    # Also reject a copied source tree, even when its receipt could be recomputed.
    for relative in generator.SOURCE_PATHS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    source = tmp_path / "epac_join_term.py"
    source.write_text(source.read_text().replace("slot-facing-sign.v0", "slot-facing-sign.other"))
    with pytest.raises(ValueError, match="checkout containing this generator"):
        generator.write_outputs(tmp_path)
    assert not (tmp_path / generator.RECEIPT_PATH).exists()
    monkeypatch.setattr(epac_join_term, "_MODULE_SOURCE_SHA256", "different-loaded-source")
    with pytest.raises(ValueError, match="loaded epac_join_term source"):
        generator.build_receipt(ROOT)
