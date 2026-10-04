# EPAC join-term v0 deterministic audit

Classification: **PUBLIC_ONLY_RECOVERY_SURVIVED**

The public receipt recovers one complete typed S0-through-S6 join tree and its exact authored lineage without constructor or private state. The legacy count bag is retained beside the tree and is demonstrably non-injective.

## Exact authority

- EPAC base: `1e5c999286f12221eff9870d1372203ac7935f2a` (tree `ce7781938ff684d826bd91f475b5423bd56b146a`)
- EPAC feature source manifest: `aaa855bba19979641bedf562dfe90cf18884fcec17ab92fd052f3e11691447c5`
- METAPAT producer: `1cdfb09dd00a451cee30eec2e78624df8c682662` (tree `d946a5a18b0c53fd561dcd9d68fdf36d5dd11638`)
- METAPAT application: `metapat.application.epac_join_terms@epac-join-terms-application-v4`
- METAPAT application digest: `461ef7e059aa65b514017683ba9b57058ee9f582bc63748fabd021cdeb660b4b`
- skill-lib: `516933d98f9de376f4e498f44059043dc0d96470` (tree `a1465ddf1de9519c9abc1a97d058432ba71bb257`)
- UCNS consumed: `false`; UCNS law modified: `false`

The containing feature commit cannot be embedded in a file inside itself. The evidence therefore binds the exact pre-feature EPAC base plus SHA-256 of every non-generated feature input; the generated receipt and audit are excluded to avoid a self-hash cycle, and the final Git commit binds all bytes externally.

## Exact result

- Candidate digest: `11504eb61c4952fc3da04a51d3779484194292db2c8a5c3174b3c3ea540e6442`
- Candidate JSON SHA-256: `821d35a1e42c8d22423f78fdce8449066af40392d47f3e79e5b30b8f993fcbfd`
- Evidence digest: `e3a5160c642050cc2d4f4bae126b34328b91fe17425fec5431182a7486adab95`
- Origins: `7`
- Authored joins (no Transformation or Time claim): `6`
- Slots: `18` (`6` members, `6` holes, `6` leftovers)
- Native operation: exact authored origin-lineage and named-seating replay

## Minimal lossy-projection witness

- Baseline digest: `11504eb61c4952fc3da04a51d3779484194292db2c8a5c3174b3c3ea540e6442`
- Reordered digest: `f74f9227a79acf84588b11d153bf66f9490d3aa18d8e899b6266c11ca3594633`
- Shared bag SHA-256: `ae6e48f3245310cefc233eb091a2cb872ac7ab0302296735d3a1b5fe9e2a2f9f`
- Bags equal: `true`
- Join-isomorphic: `false`
- Conclusion: the legacy bag cannot uniquely recover authored seating or the complete join tree.

## Exact-instance identity projection witness

- Renamed identity namespace: `fixture-b`
- Renamed candidate digest: `7e30d6f4942e215462254dec9723a1deeb4e71d680e2cc960f227b02240f420d`
- Bags equal: `true`
- Join-isomorphic: `true`
- Exact instance lineages equal: `false`
- Conclusion: the legacy bag does not select exact instance identity labels, while structural lineage up to alpha-renaming is unchanged.

This is information loss. It is not a secrecy, computational-hardness, or confidentiality result.

## Source hashes

- `README.md`: `7e28c7c092f7551b11a03c9db7862e27ec88ff6f81167ed3d3f99db26e29a18b`
- `data/metapat-epac-join-terms-application-v4.json`: `7f3ff74394b48c2162818fad8a373d1b88547b0df73beb8a604376022dcddf07`
- `docs/PROVENANCE.md`: `b410815a47ea9a8229406241616a9dc143ff09eb8da717456c019379efa6d5ee`
- `docs/domain-claims.md`: `f6f7f517e127a517a4acccba5527692239700c128b7bf0ecef9603e8c155c911`
- `docs/multi-origin-join-term-v0.md`: `6efb441f4421edf84c22556b46e438cc2da4f51536c522d3b6556af7b1c66a39`
- `docs/research-status.md`: `1f5194f0dc44521b6dc81d9a9494c72ff385fd879b8eb2b2849824640c5c2d07`
- `docs/work-graph.json`: `4edb37ace798511ff4b5f667afd1f0a3852ce78b7335349aaa9662171de0b9e9`
- `docs/work-graphs/epac-join-term-v0.json`: `7487441ec7e3ff3203635e245fccba5d293192cef5201c657946a15788166f16`
- `epac_boundary_probe_completeness.py`: `1bc8a3e990e99d52b9636eb1f656f3da0d6178c42de9dd86d811d9211e87f014`
- `epac_join_term.py`: `4697da5c76d5dfc77aedc5c84c71b7175180550824b6a1a2c1bf23a8548839af`
- `pyproject.toml`: `44936ff75383ab25d3e295c6574b1759709fef7a072773d4c5774dd00243bcdd`
- `tests/test_boundary_probe_completeness.py`: `c0d0196718e14126a82d669359ae58b207d46b1a20ff5158828c9ca1c7422c8f`
- `tests/test_epac_join_term.py`: `ed060a6ef7903f178e3da6b94890f088de8b37dc7b94e6e41b4ccc15a3b7f5c8`
- `tools/generate_join_term_v0.py`: `1836734e0ba692f23f604838ed3146c811528266a341979366eff6b19447e331`

## Explicit nonclaims

- Vector action, resulting state Transformation, or actual Time sequence
- chemical or physical truth
- molecular geometry or shape prediction
- UCNS correspondence, topology, theorem status, or gonol identity
- energy coupling, conservation, entropy, force, or field behavior
- cryptographic secrecy, confidentiality, public-key separation, or computational hardness
- PCEA compatibility
- production suitability
- release or protocol authority

## hmmm

- Authored adjacency and its stored order do not establish state changes or actual occurrence order; Transformation and Time remain unlicensed for this candidate.
- Whether a useful operation exists that requires secret EPAC state and cannot be efficiently reproduced from a legitimate public projection remains unestablished; this candidate is wholly public.
- Whether exact lineage and seating replay improve an independently preregistered EPAC task remains unmeasured.
- Whether any later UCNS correspondence is useful requires a separate license and test without rewriting UCNS law.

## Replay

```bash
python tools/generate_join_term_v0.py --check
python -m pytest -q tests/test_epac_join_term.py
```
