# EPAC multi-origin join term v0

Status: **native correctness candidate / representation evidence only**

This document specifies one EPAC-owned typed multi-origin join tree. It is the working correctness prototype requested by the nomenclature handoff: METAPAT names the spine, while EPAC owns the domain object, constructor, equality, public recovery, and evidence.

It does not amend METAPAT or UCNS. It does not repair or reinterpret the preserved `FALSIFIED` molecular-shape result.

## Authority and customs

The semantic license is:

```text
application_id:      metapat.application.epac_join_terms
application_version: epac-join-terms-application-v4
application_digest:  461ef7e059aa65b514017683ba9b57058ee9f582bc63748fabd021cdeb660b4b
producer repository: The-Interdependency/metapat
```

This candidate uses the licensed roles `Thing`, `Boundary`, `State`, `Simplex`, `Tensor`, and `Scalar`. It claims no `Vector`, `Transformation`, or `Time`: its static bearing does not alter state, and an authored join or scale position establishes neither a resulting state change nor actual occurrence order. EPAC retains the domain names and all implementation/evidence obligations. Every semantic wire path is paired with both names in `semantic_field_bindings`; coverage is derived from the live serialized shape and checked exactly. The only exempt metadata are `schema_id`, `schema_version`, `candidate_digest`, `semantic_license`, and `semantic_field_bindings` itself. The object kind and every legacy-bag leaf remain meaning-bearing and are explicitly licensed.

Each binding also carries the exact METAPAT `catalog_module_id` selected by its `application_role`. The field's `spine_name` and the application role are two checked axes, not interchangeable labels: for example, an authored relation contributes to the `Tensor` structure under the `metapat.axiom.6.relate` license, while recursive source/target identity and provenance remain `Thing` fields under `metapat.axiom.7.emerge`. Domain qualification may accompany the six roles used here; it does not rename them. The adapter rejects any `(spine_name, application_role)` pair outside this pinned projection. The exact merged METAPAT fixture is preserved byte-for-byte in `data/metapat-epac-join-terms-application-v4.json`; generation verifies its SHA-256 and compares its catalog roles against the consumer projection. This is a pinned evidence snapshot, not an EPAC-owned semantic license.

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
- an exact stored slot-facing property `facing`;
- separate phase, capacity, and slot-facing readouts, plus static bearing inferred from the ordered facing properties;
- arity and shape signature derived from the explicit seating chart;
- provenance.

For each `n` from 0 through 5, the `S(n+1)` origin contains exactly one `member` slot referencing `S(n)`. A separately identified `AuthoredJoin` records that adjacent-scale relation in `joins`. Its `order` is the structural position S0–S1 through S5–S6, not Time evidence. No skip-scale join, shared-count ancestry, or geometric analogy is inferred.

A zero seat is serialized as a `hole` with null participant identity, null participant scale, and facing property zero. It is never represented by an omitted key.

## State, scalar readouts, and inferred bearing

Ratios are `{numerator, denominator}` with an integer numerator and strictly positive integer denominator. Typed construction reduces them exactly, but wire parsing rejects unreduced forms (including `0/2`) even when the candidate digest has been recomputed. Floating point is absent.

`phase`, `phase_chart`, `k`, and each slot’s `facing` remain stored properties. Separately computed scalar readouts name `origin_id`, `measured_property`, `rule_id`, and `value`. Phase uses `epac.readout.exact-phase.v0`; capacity uses `epac.readout.capacity.v0`; each `slots[index].facing` uses `epac.readout.slot-facing.v0`. These rules copy the declared value into an identified readout and do not establish an external observation or measurement validity. Readout metadata and values are validated against the stored state on recovery.

Bearing rule `epac.bearing.slot-facing-sign.v0` maps each ordered slot-facing property `s` to:

```text
-1 when s < 0
 0 when s = 0
+1 when s > 0
```

The serialized bearing readout identifies its origin, `slots[*].facing`, the sign rule, and an ordered list of component values. Strict recovery recomputes it from the stored properties and rejects disagreement. The readout describes static signs and performs no state-altering operation; it has no Vector binding.

## S5 energy readout

Only S5 carries `s5_energy_readout`. Its exact candidate law is:

```text
occupied slots / k
```

Its wire readout names the S5 origin, `slots[*].kind,k`, and rule `epac.readout.occupied-slots-over-k.v0`; the result is stored under `value`. Non-S5 origins store null. Here a hole is unoccupied and a member or leftover is occupied. This is an EPAC-qualified occupancy functional. It is not a fourth circle and establishes no physical energy, conservation, entropy, force, field, or coupling claim.

## Equality

`join_isomorphic(left, right)` compares the complete typed ordered structure after a bijective alpha-renaming of instance origin, authored-join, and leftover identities. It preserves identity equality and aliasing patterns as well as scale names, phase values and charts, named slot order, slot kinds, facing properties and identified readouts, inferred bearing, arity, shape, S5 occupancy readout, provenance labels, and authored adjacency. Recovery rejects duplicate declared object identities before comparison, so an alias cannot masquerade as an alpha-renaming.

Therefore:

- the same tree under a different identity namespace is isomorphic;
- two seating charts with the same counts but different named order are not isomorphic;
- visible and lifted phase records remain distinct;
- a bag of counts cannot pass as the tree.

## Native operation and lossy public projection

The native typed tree supports exact authored lineage replay: for any present target origin, `trace_origin_lineage` returns the unique stored sequence from S0 through that target. Named seating is available at every step.

The legacy projection is deliberately typed `bag` and kept beside the tree. It retains only slot counts by scale and total counts by slot kind. It is excluded from the tensor-role object and from join-isomorphism. The minimal committed non-isomorphic witness keeps the identity namespace fixed and changes only S2 seating order, proving that the bag cannot uniquely reproduce authored seating or the complete tree. A separate alpha-renamed witness keeps structure and seating fixed: its bag is identical and it remains join-isomorphic, while its exact instance lineage identifiers differ. Thus the bag does not select instance labels; structural lineage shape up to alpha-renaming is unchanged. This is information loss, not a computational-hardness or confidentiality claim.

The complete canonical JSON receipt is public. Recovery from those public bytes reconstructs the tree and lineage without invoking the constructor or consulting private state. No secret key, cryptographic private structure, or confidentiality property exists here.

## Wire and fail-closed recovery

The canonical wire is sorted-key compact UTF-8 JSON under:

```text
schema_id:      epac.multi-origin-join-tree
schema_version: 0.2.0
object_kind:    multi-origin-join-tree
```

`candidate_digest` is SHA-256 of the canonical payload excluding only that digest field. Strict recovery rejects duplicate JSON keys, unknown or missing fields, invalid or unreduced ratios, omitted explicit slot state, duplicate identities, incomplete scales, invalid k, noncontiguous slot order, malformed holes, skip-scale references, inconsistent joins, changed semantic bindings, changed license identity, bag masquerading, and digest mismatch. Origin, authored-join, and leftover object identities occupy one globally unique declared-object scope. A member `participant_id` is a reference to an already declared origin and therefore intentionally repeats that origin identity; it does not declare a new object.

Mapping parsing also requires the supplied payload to equal the canonical serialization of the recovered object before its digest is accepted; normalization cannot hide changed wire data. JSON recovery additionally compares the original text with the canonical tree serialization. Whitespace, a trailing newline, reordered keys, alternate numeric spellings such as `-0`, and unnecessary Unicode escapes are rejected even if they parse to the same values. The newline terminating the outer evidence receipt is not part of the embedded candidate wire.

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

The generator works directly from an uninstalled checkout, including from a different working directory. `--root` may only identify the checkout containing that generator. Imported generation during installed-artifact replay additionally requires the loaded module’s import-time source hash to match the archived source. Identity failures occur before any output is written.

## Migration rule

Wire version `0.2.0` deliberately rejects `0.1.0` candidates carrying the superseded license. The pre-merge candidate API `JoinTransformation`/`transformations`/`transformation_id`/`sequence` becomes `AuthoredJoin`/`joins`/`join_id`/`order`, and `facing_scalar` becomes stored `facing` plus separate readouts. All six authored relations, seven origins, exact state, seating, provenance, equality, and public recovery mechanisms are retained. No historical state-change or temporal evidence is fabricated during migration. The released package version is unchanged; this is not a new release.

Existing formula/count collections remain explicitly typed bags. The candidate constructor writes the tree once and stores the lossy bag beside it. A bag is never promoted to a tree by inference. Molecular comparisons remain `FALSIFIED`; any future structural comparison must compare an S3 tree to an S3 tree under a separately preregistered question.

## Nonclaims

This candidate does not establish:

- Vector action, resulting Transformation, or actual Time sequence;
- chemical or physical truth;
- molecular geometry or shape prediction;
- UCNS correspondence, topology, theorem status, or gonol identity;
- energy coupling, conservation, entropy, force, or field behavior;
- a cryptographic secret, confidentiality, public-key separation, or computational hardness;
- PCEA compatibility;
- production suitability;
- release or protocol authority.

## hmmm

- Transformation requires an identified thing and property, before/after state, resulting difference, and responsible action. Time additionally requires at least two actual sequential changes with occurrence evidence independent of sorting or scale labels. This static candidate supplies neither; those uses remain unlicensed.

- Whether a useful operation exists that requires secret EPAC state and cannot be efficiently reproduced from a legitimate public projection remains unestablished; this candidate is wholly public.
- Whether exact lineage and seating replay improve an independently preregistered EPAC task remains unmeasured.
- Whether any later UCNS correspondence is useful requires a separate license and test without rewriting UCNS law.
- Nomenclature is not decoration: it determines which domain object a consumer is permitted to open.
