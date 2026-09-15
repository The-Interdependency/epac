# Verified finite representation refinement

Research against EPAC v0.1.0, not a change to its released representation.

**Latest:** [the expanded 63-state test](expansion-results.md) falsifies the three
A-based minimum pairs and retains six minimum pairs with zero collisions across
1,953 pairs. All nine candidates fail the fixed repository shape-equivalence
mapping. General composition and independent physical validation remain unresolved.

**SURVIVED:** two named observers distinguish all 27 frozen constructions;
`Z multiset + topology` is one of nine minimum pairs. Exact subset searches and
independent direct enumeration check every pair and every candidate subset.
On 162 abstract ternary witnesses, charge information plus the existing slot
assignment distinguishes all exact ordered-degree outputs. No physical
primitive is inferred from either result.

Read [the executed results](verified-refinement-results.md) for scope, failures,
corrections, and counts. The two JSON files contain complete observer values,
pair witnesses, minimum sets, and ablation failures. [Next steps](next-steps.md)
defines the gates before broader claims. All 14 existing comparison standings
remain **FALSIFIED**.

## Reproduce

The published JSON records the original execution, including its temporary
source path and script hash. Check its archived bytes with:

```sh
cd docs/research/verified-refinement-20260915
sha256sum -c SHA256SUMS
python3 verify_cached_refinement.py
bash reproduce.sh
bash reproduce-expansion.sh
```

The replay commands clone the exact EPAC and UCNS commits into new temporary
directories, verify the locked UCNS Python sources, then regenerate and compare
their corresponding results. They need Git, network access, and Python 3.10–3.12 with the
release's runtime prerequisites. Errors fail the run; archived evidence is
not overwritten. Temporary checkout paths naturally differ between runs.

No release, dependency lock, production descriptor, or public API changes.
