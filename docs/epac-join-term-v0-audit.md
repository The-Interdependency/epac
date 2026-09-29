# EPAC join-term v0 deterministic audit

Classification: **PUBLIC_ONLY_RECOVERY_SURVIVED**

The public receipt recovers one complete typed S0-through-S6 join tree and its exact authored lineage without constructor or private state. The legacy count bag is retained beside the tree and is demonstrably non-injective.

## Exact authority

- EPAC base: `1e5c999286f12221eff9870d1372203ac7935f2a` (tree `ce7781938ff684d826bd91f475b5423bd56b146a`)
- EPAC feature source manifest: `0bbde982e3ed12f63198829558d521bc6d1ca7932cf902cf712431abaaaed477`
- METAPAT producer: `18011c2bf4c3c3c1f50c601add371702a7c1ff05` (tree `7e86e60d8bb5f4a9b51f031d0ca34202d0a28741`)
- METAPAT application: `metapat.application.epac_join_terms@epac-join-terms-application-v4`
- METAPAT application digest: `cba0ccc360a0ecd9b78ce582a7f54d1385beeaa83de495faa76f40112bd23e7d`
- skill-lib: `516933d98f9de376f4e498f44059043dc0d96470` (tree `a1465ddf1de9519c9abc1a97d058432ba71bb257`)
- UCNS consumed: `false`; UCNS law modified: `false`

The containing feature commit cannot be embedded in a file inside itself. The evidence therefore binds the exact pre-feature EPAC base plus SHA-256 of every non-generated feature input; the generated receipt and audit are excluded to avoid a self-hash cycle, and the final Git commit binds all bytes externally.

## Exact result

- Candidate digest: `44d162c5eaa14379d2a4c2bf00be18b33ed968de9b0a446b048b2cbb8c9ed819`
- Candidate JSON SHA-256: `7c85f97473c89b9828c27bb9b9db3574b5138858328ce920593b1b4d50469029`
- Evidence digest: `aad761e66a6a492245e6a7b41bc95c038ee1605fc4c191136672310c0f78040a`
- Origins: `7`
- Transformations: `6`
- Slots: `18` (`6` members, `6` holes, `6` leftovers)
- Native operation: exact authored origin-lineage and named-seating replay

## Minimal lossy-projection witness

- Baseline digest: `44d162c5eaa14379d2a4c2bf00be18b33ed968de9b0a446b048b2cbb8c9ed819`
- Reordered digest: `95a8eca88db6bd04ced715dab3f8e8e49ad097e6ebb76eb056ad9ca421032825`
- Shared bag SHA-256: `ae6e48f3245310cefc233eb091a2cb872ac7ab0302296735d3a1b5fe9e2a2f9f`
- Bags equal: `true`
- Join-isomorphic: `false`
- Conclusion: the legacy bag cannot uniquely recover authored seating or the complete join tree.

## Exact-instance identity projection witness

- Renamed identity namespace: `fixture-b`
- Renamed candidate digest: `22290cc32c4a6199f78078e0b46104f64fc35b11194ffb4e030bc2622fe6a8c7`
- Bags equal: `true`
- Join-isomorphic: `true`
- Exact instance lineages equal: `false`
- Conclusion: the legacy bag does not select exact instance identity labels, while structural lineage up to alpha-renaming is unchanged.

This is information loss. It is not a secrecy, computational-hardness, or confidentiality result.

## Source hashes

- `README.md`: `dc8f7bae3dfa0d8f679d428c662e0be829340553f6744829fd26f346c147bb3c`
- `docs/PROVENANCE.md`: `2a80647fc4ff53c4747cabdb5e8cb24831a9f29d6224abcc2eae6198c37b4974`
- `docs/domain-claims.md`: `a988e57a07dfe361fa4e00fd9bb9f4998fc952d8abfd456edba8ab544cadb428`
- `docs/multi-origin-join-term-v0.md`: `435d904cfc94aadd5dcbed8521c8a58e06a31b466893ce04f8bdeb23bc7b38b1`
- `docs/research-status.md`: `a30e6c2744cc4f932ef2c5de15f609fc9da3c928c27b2627673ef550059c0785`
- `docs/work-graph.json`: `149735d448f0788b97603741da271edbb13e1e91256d246c54f1d2021ade0261`
- `docs/work-graphs/epac-join-term-v0.json`: `3e9d1fee2fd3b410256cfb8b3fd1e842705e0b6eeb284fac9fd7bf8e4c275d06`
- `epac_boundary_probe_completeness.py`: `61df1624adc2970fe2e7d9d94ee15359decd42ddb7285ac223bd46eb748541ec`
- `epac_join_term.py`: `799ab7251352befb2897180693b2a5ff94157979ebc7b97cc4ca68a177d65c9b`
- `pyproject.toml`: `414cdc71cdb2e0ff859fcb59a359d57a5327e6b105e0ff010a522216dcd3881f`
- `tests/test_boundary_probe_completeness.py`: `0b532ff8e663a0eb1171642f0a0fb1364d94a5656540bc36c5a264c40b642928`
- `tests/test_epac_join_term.py`: `572e30697615296d176044d045f94f9c6cc743dbd8ea30932ad262561ab69e8a`
- `tools/generate_join_term_v0.py`: `6dbc94c2910514b1bfd65eb243161317cb20db6395e0d7f981b3524f34e2405c`

## Explicit nonclaims

- chemical or physical truth
- molecular geometry or shape prediction
- UCNS correspondence, topology, theorem status, or gonol identity
- energy coupling, conservation, entropy, force, or field behavior
- cryptographic secrecy, confidentiality, public-key separation, or computational hardness
- PCEA compatibility
- production suitability
- release or protocol authority

## hmmm

- Whether a useful operation exists that requires secret EPAC state and cannot be efficiently reproduced from a legitimate public projection remains unestablished; this candidate is wholly public.
- Whether exact lineage and seating replay improve an independently preregistered EPAC task remains unmeasured.
- Whether any later UCNS correspondence is useful requires a separate license and test without rewriting UCNS law.

## Replay

```bash
python tools/generate_join_term_v0.py --check
python -m pytest -q tests/test_epac_join_term.py
```
