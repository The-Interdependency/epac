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
#   call: self::test_recursive_origins_and_transformations_are_adjacent
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
# === END CHECKS ===

import json
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
    assert len(tree.transformations) == 6
    assert tuple(item.sequence for item in tree.transformations) == tuple(range(1, 7))
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


def test_bearing_is_inferred_and_tamper_rejected() -> None:
    tree = construct_epac_join_tree()
    assert all(
        origin.bearing
        == tuple((slot.facing_scalar > 0) - (slot.facing_scalar < 0) for slot in origin.slots)
        for origin in tree.origins
    )
    tampered = tree.to_dict()
    tampered["origins"][2]["bearing"]["components"][0] *= -1
    with pytest.raises(ValueError, match="bearing"):
        EPACJoinTree.from_dict(tampered)


def test_recursive_origins_and_transformations_are_adjacent() -> None:
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
        event = tree.transformations[index - 1]
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
    wire = tree.to_dict()
    assert set(wire["semantic_field_bindings"]) == REQUIRED_SEMANTIC_FIELD_PATHS
    assert wire["semantic_license"]["application_digest"] == METAPAT_APPLICATION_DIGEST
    for binding in wire["semantic_field_bindings"].values():
        assert set(binding) == {"spine_name", "domain_name", "application_role"}
        assert all(isinstance(value, str) and value for value in binding.values())


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
    assert legacy_bag_projection(first) == legacy_bag_projection(second)
    assert not join_isomorphic(first, second)
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
    skip_scale = tree.to_dict()
    member = next(slot for slot in skip_scale["origins"][2]["slots"] if slot["kind"] == "member")
    member["participant_id"] = skip_scale["origins"][0]["origin_id"]
    member["participant_scale"] = "S0"
    mutations.append(skip_scale)
    inconsistent_event = tree.to_dict()
    inconsistent_event["transformations"][0]["target_origin_id"] = inconsistent_event["origins"][2]["origin_id"]
    mutations.append(inconsistent_event)
    incomplete_license = tree.to_dict()
    del incomplete_license["semantic_field_bindings"]["origin.phase"]
    mutations.append(incomplete_license)
    bag_masquerade = tree.to_dict()
    bag_masquerade["object_kind"] = "bag"
    mutations.append(bag_masquerade)
    boolean_bearing = tree.to_dict()
    boolean_bearing["origins"][1]["bearing"]["components"][0] = True
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
