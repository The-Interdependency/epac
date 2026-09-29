# EPAC multi-origin join term v0

Status: **native correctness candidate / representation evidence only**

This document specifies one EPAC-owned typed multi-origin join tree. It is the working correctness prototype requested by the nomenclature handoff: METAPAT names the spine, while EPAC owns the domain object, constructor, equality, public recovery, and evidence.

It does not amend METAPAT or UCNS. It does not repair or reinterpret the preserved `FALSIFIED` molecular-shape result.

## Authority and customs

The semantic license is:

```text
application_id:      metapat.application.epac_join_terms
application_version: epac-join-terms-application-v4
application_digest:  cba0ccc360a0ecd9b78ce582a7f54d1385beeaa83de495faa76f40112bd23e7d
producer repository: The-Interdependency/metapat
```

METAPAT supplies the roles `Thing`, `Boundary`, `State`, `Simplex`, `Tensor`, `Scalar`, `Vector`, `Transformation`, and `Time`. EPAC retains the domain names and all implementation/evidence obligations. Every semantic wire path is paired with both names in `semantic_field_bindings`. Schema identifiers, schema versions, and digests are wire metadata, not domain observations.

The license transfers no UCNS coordinate or law, chemistry-phase meaning, physical-energy interpretation, EDCM measurement validity, theorem standing, or ancestry by analogy.

## Complete native object

The object is a tensor-role structure indexed by all seven EPAC scales:

| scale | EPAC domain name |
|---|---|
| S0 | subatomic slot |
| S1 | atomic |
| S2 | join/arity |
| S3 | embed |
| S4 | electronic state |
| S5 | EPAC energy readout |
| S6 | ensemble |

There is exactly one origin at each scale in this bounded candidate. Every origin stores:

- a new origin identity;
- its exact scale and EPAC domain name;
- exact rational phase and an explicit `visible` or `lifted` phase chart;
- positive join window `k`;
- exactly `k` named, ordered slots;
- each slot as `member`, `hole`, or `leftover`;
- an exact slot-facing scalar;
- bearing inferred from the ordered facing scalars;
- arity and shape signature derived from the explicit seating chart;
- provenance.

For each `n` from 0 through 5, the `S(n+1)` origin contains exactly one `member` slot referencing `S(n)`. A separately identified transformation records that authored adjacent-scale join. No skip-scale join, shared-count ancestry, or geometric analogy is inferred.

A zero seat is serialized as a `hole` with null participant identity, null participant scale, and facing scalar zero. It is never represented by an omitted key.

## Exact metrics and inferred bearing

Ratios are `{numerator, denominator}` with an integer numerator and strictly positive integer denominator. Construction reduces them exactly. Floating point is absent.

Bearing rule `epac.bearing.slot-facing-sign.v0` maps each ordered slot-facing scalar `s` to:

```text
-1 when s < 0
 0 when s = 0
+1 when s > 0
```

The serialized bearing carries the rule identity and ordered components, but strict recovery recomputes it from scalar measurements and rejects disagreement. Bearing is therefore not a caller-selected free arrow collection.

## S5 energy readout

Only S5 carries `s5_energy_readout`. Its exact candidate law is:

```text
occupied slots / k
```

where a hole is unoccupied and a member or leftover is occupied. This is an EPAC-qualified occupancy functional. It is not a fourth circle and establishes no physical energy, conservation, entropy, force, field, or coupling claim.

## Equality

`join_isomorphic(left, right)` compares the complete typed ordered structure after alpha-renaming instance origin, transformation, and leftover identities. It preserves scale names, phase values and charts, named slot order, slot kinds, facing measurements, inferred bearing, arity, shape, S5 occupancy readout, provenance labels, and authored adjacency.

Therefore:

- the same tree under a different identity namespace is isomorphic;
- two seating charts with the same counts but different named order are not isomorphic;
- visible and lifted phase records remain distinct;
- a bag of counts cannot pass as the tree.

## Native operation and lossy public projection

The native typed tree supports exact authored lineage replay: for any present target origin, `trace_origin_lineage` returns the unique stored sequence from S0 through that target. Named seating is available at every step.

The legacy projection is deliberately typed `bag` and kept beside the tree. It retains only slot counts by scale and total counts by slot kind. It is excluded from the tensor-role object and from join-isomorphism. Two non-isomorphic trees can have byte-identical bag projections, so the bag cannot uniquely reproduce lineage or seating. This is information loss, not a computational-hardness or confidentiality claim.

The complete canonical JSON receipt is public. Recovery from those public bytes reconstructs the tree and lineage without invoking the constructor or consulting private state. No secret key, cryptographic private structure, or confidentiality property exists here.

## Wire and fail-closed recovery

The canonical wire is sorted-key compact UTF-8 JSON under:

```text
schema_id:      epac.multi-origin-join-tree
schema_version: 0.1.0
object_kind:    multi-origin-join-tree
```

`candidate_digest` is SHA-256 of the canonical payload excluding only that digest field. Strict recovery rejects duplicate JSON keys, unknown or missing fields, invalid ratio denominators, omitted explicit slot state, duplicate identities, incomplete scales, invalid k, noncontiguous slot order, malformed holes, skip-scale references, inconsistent transformations, changed semantic bindings, changed license identity, bag masquerading, and digest mismatch.

Canonical evidence:

```text
data/epac-join-term-v0-receipt.json
docs/epac-join-term-v0-audit.md
```

Regenerate and verify:

```bash
python tools/generate_join_term_v0.py
python tools/generate_join_term_v0.py --check
python -m pytest -q tests/test_epac_join_term.py
```

## Migration rule

Existing formula/count collections remain explicitly typed bags. The candidate constructor writes the tree once and stores the lossy bag beside it. A bag is never promoted to a tree by inference. Molecular comparisons remain `FALSIFIED`; any future structural comparison must compare an S3 tree to an S3 tree under a separately preregistered question.

## Nonclaims

This candidate does not establish:

- chemical or physical truth;
- molecular geometry or shape prediction;
- UCNS correspondence, topology, theorem status, or gonol identity;
- energy coupling, conservation, entropy, force, or field behavior;
- a cryptographic secret, confidentiality, public-key separation, or computational hardness;
- PCEA compatibility;
- production suitability;
- release or protocol authority.

## hmmm

- Whether a useful operation exists that requires secret EPAC state and cannot be efficiently reproduced from a legitimate public projection remains unestablished; this candidate is wholly public.
- Whether exact lineage and seating replay improve an independently preregistered EPAC task remains unmeasured.
- Whether any later UCNS correspondence is useful requires a separate license and test without rewriting UCNS law.
- Nomenclature is not decoration: it determines which domain object a consumer is permitted to open.
