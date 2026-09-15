# Expanded construction challenge

The candidate list and inputs were frozen in `expansion-plan.json` before any
expanded construction was executed. The input comparison initially rejected a
tuple-versus-JSON-list mismatch before construction began; commit `e41f931`
corrected only that comparison and re-froze the script hash. No candidate,
state, target or threshold changed after observing results.

Scope: exact EPAC v0.1.0 and its pinned UCNS dependency, with occurrence zero.
There are **63** supported constructions: 36 subatomic states (H–Kr), 18 element
states (H–Ar), and all nine declared molecules. This adds **36** states to the
old domain and tests **1,953** pairs. All constructor calls completed and the
original 27-state observer values reproduced exactly: **SURVIVED**.

## Frozen-candidate outcomes

| Candidate family | Number of fixed pairs | Expanded identity result |
|---|---:|---|
| A + topology/charged/quaternion readout | 3 | FALSIFIED |
| Z + topology/charged/quaternion readout | 3 | SURVIVED |
| electron configuration + topology/charged/quaternion readout | 3 | SURVIVED |

Each A pair has the same counterexample: `subatomic:Ar` and `subatomic:Ca`.
Both carry A=`40` and the same absence-of-structure readout. Their retained
Z values are `18` and `20`; their periods, groups, electron configurations,
and valence counts also differ. No identity label or receipt digest is used
to distinguish their behavior.

The separate search over the previously declared eleven-observer pool checks
all **2,048** subsets. Minimum count remains **2**, with the six surviving
pairs above. There are **23** inclusion-minimal sets, including larger ones.
Every minimal set has field-removal counterexamples in the JSON. All six
minimum pairs have **zero** identity collisions on these 63 states.

This preserves the earlier 27-state SURVIVED result in its original scope
while falsifying the expanded claims for the three A pairs. The minimum is
not unique; canonicality remains **UNRESOLVED**.

## Actual composition and retained behavior

For the one nontrivial equal-input pair, the public `construct_public_gonol`
operation was called twice with identical source ID, relation, occurrence,
glyph, options and couplings, substituting only the single closed participant.
The relation `epac.audit.singleton-composition` explicitly denotes an external
structural test, not molecule formation or a physical process.

Both parent receipts replay successfully. Their child A/structural descriptors
still agree. Reading the actual retained child after composition yields Z=`18`
versus Z=`20` and the other differences above. Thus:

- Sufficiency of A pairs for the composed retained-field readout: **FALSIFIED**.
- Preservation of the A-pair descriptor by this singleton wrapper: **SURVIVED**.
- General substitutability of the six surviving pairs: **UNRESOLVED**. No
  nontrivial equal-descriptor inputs exist for them in this domain; the test
  cannot establish a general substitution law vacuously.

All **189** retained-field composition checks pass: seven fields over 18
subatomic→element comparisons and nine molecular multiset comparisons.
**SURVIVED** for that extraction law. Structural aggregation and general
compositionality remain **UNRESOLVED**.

## Fixed physical-target comparison

The preregistered mapping for this run is deliberately explicit: descriptor
equality predicts equal repository `known_shape`, and descriptor inequality
predicts unequal shape. It compares all 36 pairs of the nine supported molecules
against the source-hashed repository label file, after construction.

Every one of the nine candidate pairs fails on the same four pairs:

| Pair | Repository label shared by the pair | Failure |
|---|---|---|
| H2 / CO2 | linear | different descriptors for the same recorded shape |
| H2O / H2S | bent | different descriptors for the same recorded shape |
| NH3 / PH3 | trigonal-pyramidal | different descriptors for the same recorded shape |
| CH4 / SiH4 | tetrahedral | different descriptors for the same recorded shape |

The fixed shape-equivalence mapping is **FALSIFIED** for all nine candidates.
This is retrospective scoring on already exposed repository data. It is not
fresh held-out validation, an independent measurement, or evidence against all
possible functions from retained EPAC data to shape. Fresh physical validation
remains **UNRESOLVED**. All 14 original comparison standings remain **FALSIFIED**.

Adding fields to an already separating descriptor cannot make equal-shape
states equal. The next physical step therefore requires an explicit derived
shape observable and an independently testable mapping, rather than further
identity separation on this finite domain.

## Verification and reproduction

`verify_expansion.py` independently checks all frozen-candidate collisions,
all 2,048 field subsets, the post-composition readout differences, baseline
reproduction, and fixed label-comparison failures. The run asserts plan and
script hashes before constructing any state. A script exception aborts the
run; it is never converted into a successful outcome.

```sh
python3 verify_expansion.py /path/to/released/data/sealed_known_molecular_geometry.json
bash reproduce-expansion.sh
```

The replay command obtains exact source commits, verifies all 34 locked UCNS
Python source hashes, executes the frozen expansion, verifies the result, and
compares it with the archive. See `expansion-replay-validation.json` for the
recorded execution outcome.

## Stop and next boundary

Stop adding identity observers on the 63-state domain: six minimal pairs
already have zero collisions. The outstanding research questions are a
nonvacuous structural composition law and a derived observable that satisfies
a specified physical mapping. Neither is promoted by these results.
