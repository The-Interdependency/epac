# EPAC join-term v0 deterministic audit

Classification: **PUBLIC_ONLY_RECOVERY_SURVIVED**

The public receipt recovers one complete typed S0-through-S6 join tree and its exact authored lineage without constructor or private state. The legacy count bag is retained beside the tree and is demonstrably non-injective.

## Exact authority

- EPAC base: `1e5c999286f12221eff9870d1372203ac7935f2a` (tree `ce7781938ff684d826bd91f475b5423bd56b146a`)
- EPAC feature source manifest: `00184174b3086c35d1988438bbdd84df24326fdc28baf65455168225058bf5c6`
- METAPAT producer: `18011c2bf4c3c3c1f50c601add371702a7c1ff05` (tree `7e86e60d8bb5f4a9b51f031d0ca34202d0a28741`)
- METAPAT application: `metapat.application.epac_join_terms@epac-join-terms-application-v4`
- METAPAT application digest: `cba0ccc360a0ecd9b78ce582a7f54d1385beeaa83de495faa76f40112bd23e7d`
- skill-lib: `516933d98f9de376f4e498f44059043dc0d96470` (tree `a1465ddf1de9519c9abc1a97d058432ba71bb257`)
- UCNS consumed: `false`; UCNS law modified: `false`

The containing feature commit cannot be embedded in a file inside itself. The evidence therefore binds the exact pre-feature EPAC base plus SHA-256 of every feature source; the final Git commit binds those bytes externally.

## Exact result

- Candidate digest: `1ee218f4706d618473e68411569bc3e2f1b8a0b12e36e3db2240415ed4cd361d`
- Candidate JSON SHA-256: `9d4e983a74fd873774c02e2c7f124662b2d980abf761ab02fc221839b2fa4a18`
- Evidence digest: `6f6a700aeff21e79eecab9d825a7eb6d7d47d758923366aebb4e408d014d7e39`
- Origins: `7`
- Transformations: `6`
- Slots: `18` (`6` members, `6` holes, `6` leftovers)
- Native operation: exact authored origin-lineage and named-seating replay

## Minimal lossy-projection witness

- Baseline digest: `1ee218f4706d618473e68411569bc3e2f1b8a0b12e36e3db2240415ed4cd361d`
- Reordered digest: `31da2d9850188a9492e0d2d144d9e3ed5e2d51b426c799c4d8ad3691650a1fbc`
- Shared bag SHA-256: `ae6e48f3245310cefc233eb091a2cb872ac7ab0302296735d3a1b5fe9e2a2f9f`
- Bags equal: `true`
- Join-isomorphic: `false`
- Conclusion: the legacy bag cannot uniquely recover authored seating or lineage.

This is information loss. It is not a secrecy, computational-hardness, or confidentiality result.

## Source hashes

- `docs/multi-origin-join-term-v0.md`: `033261bf939679c2868ccebc0ec02d70746e27c219047fd6c316696822ae6f22`
- `docs/work-graphs/epac-join-term-v0.json`: `3e9d1fee2fd3b410256cfb8b3fd1e842705e0b6eeb284fac9fd7bf8e4c275d06`
- `epac_join_term.py`: `4981bc55b143f7fc76bf814d7dfa9f61b423c9bb9551ad9f6c2db8dc59d3e8d7`
- `tests/test_epac_join_term.py`: `76cfefa2df9f16f8e652e0226ae4a2c2fea05f1e5fccab627ae87aeba19f3e22`
- `tools/generate_join_term_v0.py`: `07f4ffb58921b4a0fb478314fba043c7466a7db8e40382495d5d7dbbe635c7e6`

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
