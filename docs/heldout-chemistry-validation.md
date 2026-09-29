# Held-out chemistry validation

Purpose: test EPAC against chemistry facts without feeding those facts into EPAC construction.

## Boundary

1. Run EPAC construction and produce predictions keyed by stable case IDs.
2. Call `freeze_predictions(..., source_identity=<exact EPAC head/receipt>)`.
3. Persist the returned commitment. Its SHA-256 binds the predictions.
4. Only then expose/load an oracle corpus.
5. Call `compare_after_freeze(commitment, oracle)`.
6. Preserve the receipt and its `SURVIVED / FALSIFIED / UNRESOLVED` results.

The chemistry app is a **discovery/reference surface**, not an EPAC dependency and not the sole authority. Facts used for scoring carry an authority plus locator. Missing prediction, missing provenance, unsupported comparison, or incomparable data is `UNRESOLVED`; it is never silently counted as success.

The checked-in `data/heldout_chemistry_oracle.json` is intentionally empty. Populate it only with facts selected independently of EPAC outputs. This prevents choosing test cases after seeing what EPAC predicts.

Recommended stable IDs include `element:H:valence`, `element:O:oxidation`, `isotope:H-1:mass`, and `reaction:<canonical-id>:products`. The corpus can grow across isotope behavior, oxidation/valence, reaction outcomes, and element properties without changing EPAC construction code.

## Failure definition

- **SURVIVED**: frozen prediction satisfies the preregistered comparator.
- **FALSIFIED**: frozen prediction is comparable and disagrees.
- **UNRESOLVED**: the comparison cannot honestly decide.

The receipt binds both the frozen prediction commitment and the revealed oracle digest.
