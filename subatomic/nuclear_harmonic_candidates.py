"""Physically sourced nuclear harmonic-relation candidates (H -> He -> Li/C).

This module applies current METAPAT harmonic semantics — repeatable
commensurability, ratio, symmetry, inversion, phase relation, or recurrence
mapping — to physically sourced nuclear states of H-1/H-2, He-4, Li-7, and
C-12. It does NOT wait for a UCNS harmonic notation and it does NOT invent
Public Gonol position operations or unsourced phase.

Every candidate record declares the six METAPAT evidence fields:

    participants, ordered parameter, recurrence mapping,
    equivalence condition, information loss, physical provenance.

Ordered parameters are nucleon-content sequences (A, Z), which are
time-agnostic. No temporal phase is introduced.

Status: CROSS-DOMAIN-HYPOTHESIS / hmmm. No physics claim is advanced beyond
the cited nuclear data and declared candidate mappings.

Usage guidance:

    python3 - <<'PY'
    from nuclear_harmonic_candidates import CANDIDATES, recurrence_test

    for candidate in CANDIDATES:
        print(candidate.candidate_id, candidate.receipt)
    for candidate in CANDIDATES:
        print(candidate.candidate_id, recurrence_test(candidate))
    PY
"""

# === MODULE_BUILD ===
# id: epac_subatomic_nuclear_harmonic_candidates
#   module_name: nuclear_harmonic_candidates
#   module_kind: experiment
#   summary: physically sourced H/He/Li/C nuclear harmonic-relation candidates over METAPAT harmonic semantics with declared recurrence mappings and provenance
#   owner: The Interdependency
#   public_surface: NUCLIDE_FACTS, CANDIDATES, HarmonicCandidate, recurrence_test, harmonic_receipt
#   internal_surface: _canonical_record
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: subatomic.test_nuclear_harmonic_candidates
#   rollout: local candidate module under stack/research/epac/subatomic/
#   rollback: remove module, tests, and generated receipts
#   requires: none (pure stdlib; METAPAT semantics consumed as documented doctrine, not imported code)
#   since: 2026-08-22
#   unresolved: UCNS harmonic notation; exact alpha-cluster citations; approximate isospin symmetry ignores Coulomb effects
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: every_harmonic_candidate_declares_six_evidence_fields
#   given: any harmonic candidate record
#   then: participants, ordered_parameter, recurrence_mapping, equivalence_condition, information_loss, and physical_provenance are all non-empty and source-declared
#   class: doctrine
#
# id: harmonic_parameter_is_time_agnostic
#   given: any harmonic candidate ordered parameter
#   then: the parameter is an explicitly declared non-temporal sequence (nucleon content A, Z), never an unsourced phase or time
#   class: doctrine
#
# id: no_public_gonol_position_operation_invented
#   given: the harmonic candidate module is imported
#   then: no Public Gonol position operation is defined, inferred, or asserted
#   class: safety
#
# id: recurrence_test_is_deterministic
#   given: the same candidate record and the same declared equivalence condition
#   then: recurrence_test returns the same boolean and the receipt is byte-identical across independent constructions
#   class: correctness
#
# id: all_results_remain_cross_domain_hypothesis
#   given: any candidate or recurrence result
#   then: status remains CROSS-DOMAIN-HYPOTHESIS / hmmm and no physics validation, canon promotion, or theorem status is claimed
#   class: doctrine
# === END CONTRACTS ===

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

# Physically sourced nuclear facts. Provenance: compiled nuclear data
# (NNDC/AME-style ground-state table); values web-pinned 2026-08-22.
NUCLIDE_FACTS = {
    "H-1": {
        "Z": 1, "A": 1, "N": 0, "J_pi": "1/2+",
        "BE_total_MeV": 0.0, "BE_per_A_MeV": 0.0,
        "provenance": "compiled nuclear data; web-pinned 2026-08-22",
    },
    "H-2": {
        "Z": 1, "A": 2, "N": 1, "J_pi": "1+",
        "BE_total_MeV": 2.22, "BE_per_A_MeV": 1.11,
        "provenance": "compiled nuclear data; web-pinned 2026-08-22",
    },
    "He-4": {
        "Z": 2, "A": 4, "N": 2, "J_pi": "0+",
        "BE_total_MeV": 28.3, "BE_per_A_MeV": 7.07,
        "provenance": "compiled nuclear data; web-pinned 2026-08-22",
    },
    "Li-7": {
        "Z": 3, "A": 7, "N": 4, "J_pi": "3/2-",
        "BE_total_MeV": 39.2, "BE_per_A_MeV": 5.6,
        "provenance": "compiled nuclear data; web-pinned 2026-08-22",
    },
    "C-12": {
        "Z": 6, "A": 12, "N": 6, "J_pi": "0+",
        "BE_total_MeV": 92.2, "BE_per_A_MeV": 7.68,
        "provenance": "compiled nuclear data; web-pinned 2026-08-22",
    },
}

ORDERED_PARAMETER = {
    "kind": "nucleon-content-sequence",
    "declaration": "ordered by increasing (A, Z): H-1, H-2, He-4, Li-7, C-12",
    "time_agnostic": True,
}


@dataclass(frozen=True, slots=True)
class HarmonicCandidate:
    """One harmonic-relation candidate with the six METAPAT evidence fields."""

    candidate_id: str
    relation_kind: str
    participants: tuple[str, ...]
    ordered_parameter: dict
    recurrence_mapping: str
    equivalence_condition: str
    information_loss: str
    physical_provenance: tuple[str, ...]
    status: str = "CROSS-DOMAIN-HYPOTHESIS"
    receipt: str = field(default="")


def harmonic_receipt(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_record(candidate: HarmonicCandidate) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "relation_kind": candidate.relation_kind,
        "participants": list(candidate.participants),
        "ordered_parameter": candidate.ordered_parameter,
        "recurrence_mapping": candidate.recurrence_mapping,
        "equivalence_condition": candidate.equivalence_condition,
        "information_loss": candidate.information_loss,
        "physical_provenance": list(candidate.physical_provenance),
        "status": candidate.status,
    }


def _seal(candidate: HarmonicCandidate) -> HarmonicCandidate:
    record = _canonical_record(candidate)
    receipt = harmonic_receipt(record)
    return HarmonicCandidate(
        candidate_id=candidate.candidate_id,
        relation_kind=candidate.relation_kind,
        participants=candidate.participants,
        ordered_parameter=candidate.ordered_parameter,
        recurrence_mapping=candidate.recurrence_mapping,
        equivalence_condition=candidate.equivalence_condition,
        information_loss=candidate.information_loss,
        physical_provenance=candidate.physical_provenance,
        status=candidate.status,
        receipt=receipt,
    )


CANDIDATES = (
    _seal(HarmonicCandidate(
        candidate_id="alpha_cluster_recurrence",
        relation_kind="recurrence",
        participants=("He-4", "Li-7", "C-12"),
        ordered_parameter=ORDERED_PARAMETER,
        recurrence_mapping=(
            "The closed-shell He-4 cluster (2p2n, J^pi=0+, doubly magic) recurs "
            "as a constituent: Li-7 ~ alpha + triton; C-12 ~ 3 x alpha "
            "(3-alpha cluster model; Hoyle 0+ state near 7.65 MeV excitation)."
        ),
        equivalence_condition=(
            "constituent decomposition contains one or more He-4 closed-shell "
            "clusters, each 2p2n with J^pi=0+; equivalence is cluster "
            "decomposition, not full state equality."
        ),
        information_loss=(
            "excited-state spectrum, cluster relative motion, and non-alpha "
            "constituents (triton, deuteron) are reduced to cluster labels."
        ),
        physical_provenance=(
            "standard nuclear cluster models; Hoyle (1954) prediction of the "
            "C-12 7.65 MeV 0+ state",
            "hmmm: exact literature citation not web-pinned this session",
        ),
    )),
    _seal(HarmonicCandidate(
        candidate_id="n_z_ratio_commensurability",
        relation_kind="ratio",
        participants=("H-1", "H-2", "He-4", "Li-7", "C-12"),
        ordered_parameter=ORDERED_PARAMETER,
        recurrence_mapping=(
            "Neutron/proton ratio N/Z as an exact rational: H-1 0/1, H-2 1/1, "
            "He-4 2/2 = 1, Li-7 4/3, C-12 6/6 = 1. The value N/Z = 1 recurs "
            "for the even-even N=Z nuclei He-4 and C-12."
        ),
        equivalence_condition="N/Z == 1 exactly (rational equality).",
        information_loss=(
            "reduces each nuclide to its (N, Z) pair; drops spin, excitation "
            "spectrum, and binding energy."
        ),
        physical_provenance=(
            "nuclide chart (N, Z) counts; standard nuclear data",
            "compiled nuclear data; web-pinned 2026-08-22",
        ),
    )),
    _seal(HarmonicCandidate(
        candidate_id="ground_state_spin_parity_symmetry",
        relation_kind="symmetry",
        participants=("H-1", "H-2", "He-4", "Li-7", "C-12"),
        ordered_parameter=ORDERED_PARAMETER,
        recurrence_mapping=(
            "Ground-state spin-parity J^pi: H-1 1/2+, H-2 1+, He-4 0+, "
            "Li-7 3/2-, C-12 0+. The value 0+ recurs for even-even, "
            "paired, closed-shell nuclei He-4 and C-12; odd-mass nuclei take "
            "half-integer spins."
        ),
        equivalence_condition='J^pi == "0+" for the even-even symmetry class.',
        information_loss=(
            "drops excited states, magnetic moments, and full level schemes."
        ),
        physical_provenance=(
            "compiled nuclear data; web-pinned 2026-08-22",
        ),
    )),
    _seal(HarmonicCandidate(
        candidate_id="binding_per_nucleon_commensurability",
        relation_kind="commensurability",
        participants=("H-2", "He-4", "Li-7", "C-12"),
        ordered_parameter=ORDERED_PARAMETER,
        recurrence_mapping=(
            "Binding energy per nucleon (MeV): H-2 1.11, He-4 7.07, Li-7 5.6, "
            "C-12 7.68. He-4 and C-12 are commensurable within a declared "
            "10% tolerance; Li-7 dips, reproducing the even-even peak / "
            "odd-mass dip recurrence of the light-nucleus binding curve."
        ),
        equivalence_condition=(
            "|BE/A(x) - BE/A(He-4)| / BE/A(He-4) <= 0.10 (declared tolerance)."
        ),
        information_loss=(
            "scalar reduction of the full binding relation; per METAPAT "
            "theory.5 this candidate is read together with the complete "
            "(Z, N, A) relation, not as one scalar difference alone."
        ),
        physical_provenance=(
            "compiled nuclear data; web-pinned 2026-08-22",
        ),
    )),
    _seal(HarmonicCandidate(
        candidate_id="proton_neutron_inversion_symmetry",
        relation_kind="inversion",
        participants=("He-4", "C-12"),
        ordered_parameter=ORDERED_PARAMETER,
        recurrence_mapping=(
            "Proton <-> neutron inversion (isospin mirror symmetry): N=Z "
            "nuclei He-4 and C-12 map to themselves under p <-> n exchange. "
            "H-1 inverts to the free neutron, which is unbound — a declared "
            "asymmetry, not a phase."
        ),
        equivalence_condition="N == Z (self-mirror under p <-> n exchange).",
        information_loss=(
            "ignores Coulomb/electromagnetic effects; isospin symmetry is "
            "approximate, not exact."
        ),
        physical_provenance=(
            "isospin symmetry; standard nuclear physics (Wigner)",
            "hmmm: exact citation not web-pinned this session",
        ),
    )),
)


def recurrence_test(candidate: HarmonicCandidate) -> dict:
    """Test whether the declared equivalence condition recurs in Li-7 and C-12.

    Returns ``{"Li-7": bool, "C-12": bool}``. Declared, source-bound outcome
    mapping. This is not a physics validation.
    """
    he4 = NUCLIDE_FACTS["He-4"]
    li7 = NUCLIDE_FACTS["Li-7"]
    c12 = NUCLIDE_FACTS["C-12"]

    def be_a_deviation(facts: dict) -> float:
        return abs(facts["BE_per_A_MeV"] - he4["BE_per_A_MeV"]) / he4["BE_per_A_MeV"]

    if candidate.candidate_id == "alpha_cluster_recurrence":
        # Li-7 = alpha + triton; C-12 = 3 x alpha. Survives both.
        return {"Li-7": True, "C-12": True}
    if candidate.candidate_id == "n_z_ratio_commensurability":
        # N/Z == 1: Li-7 is 4/3 (no); C-12 is 6/6 (yes).
        return {"Li-7": li7["N"] == li7["Z"], "C-12": c12["N"] == c12["Z"]}
    if candidate.candidate_id == "ground_state_spin_parity_symmetry":
        # J^pi == 0+: Li-7 is 3/2- (no); C-12 is 0+ (yes).
        return {"Li-7": li7["J_pi"] == "0+", "C-12": c12["J_pi"] == "0+"}
    if candidate.candidate_id == "binding_per_nucleon_commensurability":
        tolerance = 0.10
        return {
            "Li-7": be_a_deviation(li7) <= tolerance,
            "C-12": be_a_deviation(c12) <= tolerance,
        }
    if candidate.candidate_id == "proton_neutron_inversion_symmetry":
        # N == Z self-mirror: Li-7 (4/3) no; C-12 (6/6) yes.
        return {"Li-7": li7["N"] == li7["Z"], "C-12": c12["N"] == c12["Z"]}
    raise ValueError(f"no declared recurrence test for {candidate.candidate_id!r}")


__all__ = [
    "CANDIDATES",
    "HarmonicCandidate",
    "NUCLIDE_FACTS",
    "ORDERED_PARAMETER",
    "harmonic_receipt",
    "recurrence_test",
]
