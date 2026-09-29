"""Generate or verify deterministic EPAC join-term v0 evidence."""

# === MODULE_BUILD ===
# id: epac_join_term_v0_evidence_generator
#   module_name: tools.generate_join_term_v0
#   module_kind: instrument
#   summary: renders the canonical public join-tree receipt and its Markdown audit from the live candidate constructor and exact source identities
#   owner: The Interdependency/epac
#   public_surface: build_receipt, render_receipt, render_audit, write_outputs, main
#   internal_surface: fixed authority and runtime identities, canonical JSON and source hashing
#   auth_boundary: none
#   storage_boundary: read feature sources; write or compare two declared generated artifacts
#   network_boundary: none
#   user_data_boundary: public deterministic research fixture only
#   admin_only: false
#   tests: tests.test_epac_join_term
#   rollout: explicit generation and CI drift check
#   rollback: restore prior evidence only with matching constructor and source-manifest identity
#   requires: epac_multi_origin_join_term_v0
#   since: 2026-09-29
#   unresolved: the receipt records contract evidence, not external-domain validity or release authority
# === END MODULE_BUILD ===

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from epac_join_term import (
    METAPAT_APPLICATION_DIGEST,
    METAPAT_APPLICATION_ID,
    METAPAT_APPLICATION_VERSION,
    construct_epac_join_tree,
    join_isomorphic,
    legacy_bag_projection,
    trace_origin_lineage,
)

RECEIPT_PATH = Path("data/epac-join-term-v0-receipt.json")
AUDIT_PATH = Path("docs/epac-join-term-v0-audit.md")
SOURCE_PATHS = (
    Path("README.md"),
    Path("docs/PROVENANCE.md"),
    Path("docs/domain-claims.md"),
    Path("docs/work-graph.json"),
    Path("epac_join_term.py"),
    Path("epac_boundary_probe_completeness.py"),
    Path("docs/multi-origin-join-term-v0.md"),
    Path("docs/research-status.md"),
    Path("docs/work-graphs/epac-join-term-v0.json"),
    Path("pyproject.toml"),
    Path("tests/test_boundary_probe_completeness.py"),
    Path("tests/test_epac_join_term.py"),
    Path("tools/generate_join_term_v0.py"),
)

EPAC_BASE_COMMIT = "1e5c999286f12221eff9870d1372203ac7935f2a"
EPAC_BASE_TREE = "ce7781938ff684d826bd91f475b5423bd56b146a"
METAPAT_PRODUCER_COMMIT = "18011c2bf4c3c3c1f50c601add371702a7c1ff05"
METAPAT_PRODUCER_TREE = "7e86e60d8bb5f4a9b51f031d0ca34202d0a28741"
METAPAT_APPLICATION_FIXTURE_SHA256 = "b1b5a232b6f262e8fc210582d43f04b99d96bc381a46cb2252b21f9055b8bb9b"
METAPAT_APPLICATION_SOURCE_SHA256 = "519a5c06239c1ecfe8aef0367b7b0604425fc05310768ad91037084e4754103d"
SKILL_LIB_COMMIT = "516933d98f9de376f4e498f44059043dc0d96470"
SKILL_LIB_TREE = "a1465ddf1de9519c9abc1a97d058432ba71bb257"

AUTHORING_RUNTIME = {
    "implementation": "CPython",
    "version": "3.12.3",
    "executable": "/usr/bin/python3.12",
    "executable_sha256": "e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f",
}

NONCLAIMS = (
    "chemical or physical truth",
    "molecular geometry or shape prediction",
    "UCNS correspondence, topology, theorem status, or gonol identity",
    "energy coupling, conservation, entropy, force, or field behavior",
    "cryptographic secrecy, confidentiality, public-key separation, or computational hardness",
    "PCEA compatibility",
    "production suitability",
    "release or protocol authority",
)

HMMM = (
    "Whether a useful operation exists that requires secret EPAC state and cannot be efficiently reproduced from a legitimate public projection remains unestablished; this candidate is wholly public.",
    "Whether exact lineage and seating replay improve an independently preregistered EPAC task remains unmeasured.",
    "Whether any later UCNS correspondence is useful requires a separate license and test without rewriting UCNS law.",
)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_hashes(root: Path) -> dict[str, str]:
    return {
        path.as_posix(): _sha256((root / path).read_bytes())
        for path in SOURCE_PATHS
    }


def build_receipt(root: Path) -> dict[str, Any]:
    root = root.resolve()
    tree = construct_epac_join_tree()
    reordered = construct_epac_join_tree(
        s2_seating_order=("guest", "core", "vacancy"),
    )
    renamed = construct_epac_join_tree(identity_namespace="fixture-b")
    source_hashes = _source_hashes(root)
    candidate_json = tree.to_json().encode("utf-8")
    bag_json = _canonical_json(legacy_bag_projection(tree)).encode("utf-8")
    reordered_bag_json = _canonical_json(legacy_bag_projection(reordered)).encode("utf-8")
    renamed_bag_json = _canonical_json(legacy_bag_projection(renamed)).encode("utf-8")
    if bag_json != reordered_bag_json:
        raise RuntimeError("same-count witness no longer has identical bag bytes")
    if join_isomorphic(tree, reordered):
        raise RuntimeError("same-count witness unexpectedly became join-isomorphic")
    if renamed_bag_json != bag_json or not join_isomorphic(tree, renamed):
        raise RuntimeError("alpha-renamed identity witness no longer preserves structure and bag")
    receipt: dict[str, Any] = {
        "schema_id": "epac.join-term-v0-evidence",
        "schema_version": "1.0.0",
        "evidence_epoch": "2026-09-29",
        "authority": {
            "epac": {
                "repository": "The-Interdependency/epac",
                "base_commit": EPAC_BASE_COMMIT,
                "base_tree": EPAC_BASE_TREE,
                "feature_identity": "source-manifest-sha256",
                "authority": "schema, constructor, equality, serialization, recovery, and evidence",
            },
            "metapat": {
                "repository": "The-Interdependency/metapat",
                "producer_commit": METAPAT_PRODUCER_COMMIT,
                "producer_tree": METAPAT_PRODUCER_TREE,
                "application_id": METAPAT_APPLICATION_ID,
                "application_version": METAPAT_APPLICATION_VERSION,
                "application_digest": METAPAT_APPLICATION_DIGEST,
                "application_fixture_sha256": METAPAT_APPLICATION_FIXTURE_SHA256,
                "application_source_sha256": METAPAT_APPLICATION_SOURCE_SHA256,
                "authority": "semantic spine role license only",
                "authority_transfer": False,
            },
            "skill_lib": {
                "repository": "The-Interdependency/skill-lib",
                "commit": SKILL_LIB_COMMIT,
                "tree": SKILL_LIB_TREE,
                "authority": "build and evidence doctrine only",
                "authority_transfer": False,
            },
            "ucns": {
                "consumed": False,
                "law_modified": False,
                "authority_transfer": False,
            },
        },
        "runtime_identity": AUTHORING_RUNTIME,
        "inputs": {
            "identity_namespace": "fixture-a",
            "s2_seating_order": ["core", "guest", "vacancy"],
            "phase_chart_rule": "visible on even-numbered scales; lifted on odd-numbered scales",
            "phase_values": [origin.phase.to_dict() for origin in tree.origins],
            "input_is_public": True,
            "private_input_supplied": False,
        },
        "source_files_sha256": source_hashes,
        "source_manifest_sha256": _sha256(_canonical_json(source_hashes).encode("utf-8")),
        "candidate": tree.to_dict(),
        "results": {
            "classification": "PUBLIC_ONLY_RECOVERY_SURVIVED",
            "candidate_digest": tree.candidate_digest,
            "candidate_json_sha256": _sha256(candidate_json),
            "origin_count": len(tree.origins),
            "transformation_count": len(tree.transformations),
            "slot_count": sum(origin.k for origin in tree.origins),
            "hole_count": sum(slot.kind == "hole" for origin in tree.origins for slot in origin.slots),
            "leftover_count": sum(slot.kind == "leftover" for origin in tree.origins for slot in origin.slots),
            "member_count": sum(slot.kind == "member" for origin in tree.origins for slot in origin.slots),
            "s6_lineage": list(trace_origin_lineage(tree, tree.origins[-1].origin_id)),
            "native_operation": "exact authored origin-lineage and named-seating replay",
            "legacy_projection": "slot-count bag",
            "legacy_bag_sha256": _sha256(bag_json),
            "same_bag_nonisomorphic_witness": {
                "baseline_candidate_digest": tree.candidate_digest,
                "reordered_candidate_digest": reordered.candidate_digest,
                "reordered_s2_seating_order": ["guest", "core", "vacancy"],
                "reordered_legacy_bag_sha256": _sha256(reordered_bag_json),
                "bags_equal": True,
                "join_isomorphic": False,
                "conclusion": "the legacy bag cannot uniquely recover authored seating or the complete join tree",
            },
            "same_bag_alpha_renamed_identity_witness": {
                "renamed_identity_namespace": "fixture-b",
                "renamed_candidate_digest": renamed.candidate_digest,
                "renamed_legacy_bag_sha256": _sha256(renamed_bag_json),
                "bags_equal": True,
                "join_isomorphic": True,
                "baseline_s6_lineage": list(
                    trace_origin_lineage(tree, tree.origins[-1].origin_id)
                ),
                "renamed_s6_lineage": list(
                    trace_origin_lineage(renamed, renamed.origins[-1].origin_id)
                ),
                "exact_instance_lineages_equal": False,
                "conclusion": "the legacy bag does not select exact instance identity labels, while structural lineage up to alpha-renaming is unchanged",
            },
        },
        "evidence": {
            "declared_contract_count": 12,
            "declared_check_count": 12,
            "public_recovery_uses_constructor_state": False,
            "molecular_shape_standing": "FALSIFIED (preserved; tested separately)",
            "deterministic_regeneration_command": "python tools/generate_join_term_v0.py --check",
        },
        "nonclaims": list(NONCLAIMS),
        "hmmm": list(HMMM),
    }
    receipt["evidence_digest"] = _sha256(_canonical_json(receipt).encode("utf-8"))
    return receipt


def render_receipt(root: Path) -> str:
    return _canonical_json(build_receipt(root)) + "\n"


def render_audit(receipt: Mapping[str, Any]) -> str:
    authority = receipt["authority"]
    results = receipt["results"]
    witness = results["same_bag_nonisomorphic_witness"]
    identity_witness = results["same_bag_alpha_renamed_identity_witness"]
    lines = [
        "# EPAC join-term v0 deterministic audit",
        "",
        f"Classification: **{results['classification']}**",
        "",
        "The public receipt recovers one complete typed S0-through-S6 join tree and its exact authored lineage without constructor or private state. The legacy count bag is retained beside the tree and is demonstrably non-injective.",
        "",
        "## Exact authority",
        "",
        f"- EPAC base: `{authority['epac']['base_commit']}` (tree `{authority['epac']['base_tree']}`)",
        f"- EPAC feature source manifest: `{receipt['source_manifest_sha256']}`",
        f"- METAPAT producer: `{authority['metapat']['producer_commit']}` (tree `{authority['metapat']['producer_tree']}`)",
        f"- METAPAT application: `{authority['metapat']['application_id']}@{authority['metapat']['application_version']}`",
        f"- METAPAT application digest: `{authority['metapat']['application_digest']}`",
        f"- skill-lib: `{authority['skill_lib']['commit']}` (tree `{authority['skill_lib']['tree']}`)",
        "- UCNS consumed: `false`; UCNS law modified: `false`",
        "",
        "The containing feature commit cannot be embedded in a file inside itself. The evidence therefore binds the exact pre-feature EPAC base plus SHA-256 of every non-generated feature input; the generated receipt and audit are excluded to avoid a self-hash cycle, and the final Git commit binds all bytes externally.",
        "",
        "## Exact result",
        "",
        f"- Candidate digest: `{results['candidate_digest']}`",
        f"- Candidate JSON SHA-256: `{results['candidate_json_sha256']}`",
        f"- Evidence digest: `{receipt['evidence_digest']}`",
        f"- Origins: `{results['origin_count']}`",
        f"- Transformations: `{results['transformation_count']}`",
        f"- Slots: `{results['slot_count']}` (`{results['member_count']}` members, `{results['hole_count']}` holes, `{results['leftover_count']}` leftovers)",
        f"- Native operation: {results['native_operation']}",
        "",
        "## Minimal lossy-projection witness",
        "",
        f"- Baseline digest: `{witness['baseline_candidate_digest']}`",
        f"- Reordered digest: `{witness['reordered_candidate_digest']}`",
        f"- Shared bag SHA-256: `{results['legacy_bag_sha256']}`",
        "- Bags equal: `true`",
        "- Join-isomorphic: `false`",
        f"- Conclusion: {witness['conclusion']}.",
        "",
        "## Exact-instance identity projection witness",
        "",
        f"- Renamed identity namespace: `{identity_witness['renamed_identity_namespace']}`",
        f"- Renamed candidate digest: `{identity_witness['renamed_candidate_digest']}`",
        "- Bags equal: `true`",
        "- Join-isomorphic: `true`",
        "- Exact instance lineages equal: `false`",
        f"- Conclusion: {identity_witness['conclusion']}.",
        "",
        "This is information loss. It is not a secrecy, computational-hardness, or confidentiality result.",
        "",
        "## Source hashes",
        "",
    ]
    lines.extend(
        f"- `{path}`: `{digest}`"
        for path, digest in sorted(receipt["source_files_sha256"].items())
    )
    lines.extend(["", "## Explicit nonclaims", ""])
    lines.extend(f"- {item}" for item in receipt["nonclaims"])
    lines.extend(["", "## hmmm", ""])
    lines.extend(f"- {item}" for item in receipt["hmmm"])
    lines.extend(
        [
            "",
            "## Replay",
            "",
            "```bash",
            "python tools/generate_join_term_v0.py --check",
            "python -m pytest -q tests/test_epac_join_term.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path) -> tuple[Path, Path]:
    root = root.resolve()
    receipt_text = render_receipt(root)
    receipt = json.loads(receipt_text)
    receipt_path = root / RECEIPT_PATH
    audit_path = root / AUDIT_PATH
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(receipt_text, encoding="utf-8")
    audit_path.write_text(render_audit(receipt), encoding="utf-8")
    return receipt_path, audit_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    receipt_text = render_receipt(root)
    audit_text = render_audit(json.loads(receipt_text))
    failures = 0
    for relative, expected in ((RECEIPT_PATH, receipt_text), (AUDIT_PATH, audit_text)):
        path = root / relative
        if args.check:
            try:
                actual = path.read_text(encoding="utf-8")
            except OSError:
                print(f"GAP  missing generated evidence: {path}")
                failures += 1
                continue
            if actual != expected:
                print(f"GAP  stale generated evidence: {path}")
                failures += 1
                continue
            print(f"CURRENT  {relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
            print(path)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
