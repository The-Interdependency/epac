# Executed minimal refinement: bounded collision closure

## Domain claim

Term: `epac.external.finite-observer-refinement`. Scope: information retained by
named observers on explicitly enumerated released constructions. Claim type:
provisional research. Minimum means number of named observers in the declared
candidate set; a multiset or structural readout counts as one observer. This is
not a minimum number of bits or physical primitives. Physics, spatial embedding,
chirality, and universal sufficiency remain outside this finite claim. No
descriptor is promoted. Authority for the operation behavior is the release
source; no cross-domain semantic authority transfers.

## Reproducible inputs

- EPAC exact release source: `949cb1cb304927942966c9fb396caf6227120e7f`.
- Extracted source for this run: `/tmp/epac-v010-refinement.BP387j`.
- UCNS: `6eea1828a34ed8ec99879f8090ea5d48352d8c2d` at
  `/tmp/ucns-epac-pinned.UvRD6f`; all 34 locked Python file hashes matched.
- `verified-refinement.json` contains every observer value, every colliding pair,
  all inclusion-minimal sets and their field-removal counterexamples, plus the
  script SHA-256 and complete ternary witnesses.
- Candidate fields: B, Z, A, period, group, electron configuration, valence
  electrons, harmonic survival, topology, charged structure, quaternion readout.
- Intrinsic fields are read from each atom's carried options. Molecules use sorted
  multisets of participant values, retaining multiplicity and discarding order.
  Missing fields raise an error; state IDs and formulas are not observer inputs.
- Structural observers use the existing released audit's identity-excluding
  mappings. Those mappings themselves lose information, tested separately below.

## All 27 frozen states and all 351 pairs

| Descriptor | Classes | Colliding pairs | Finite identity status |
|---|---:|---:|---|
| B | 16 | 19 | FALSIFIED |
| Z multiset | 18 | 9 | FALSIFIED |
| topology readout | 13 | 44 | FALSIFIED |
| Z multiset + topology | 27 | 0 | SURVIVED |
| B + Z multiset + topology | 27 | 0 | SURVIVED |

Exhaustive subset search over the ten candidate additions to fixed B has 1,024
subsets. Minimum addition count is **2**, with **13** minimum pairs and **15**
inclusion-minimal sets. Searching all eleven fields without mandatory B has
2,048 subsets: **2** observers are necessary and sufficient, with **9** minimum
pairs and **19** inclusion-minimal sets. Independent direct pairwise enumeration
verified both complete subset spaces against the search result.

The nine minimum pairs without mandatory B are:

- A + charged structure
- A + quaternion readout
- A + topology
- Z + charged structure
- Z + quaternion readout
- Z + topology
- electron configuration + charged structure
- electron configuration + quaternion readout
- electron configuration + topology

Each field deletion has an explicit counterexample in the JSON. For the Z plus
topology pair, removing topology leaves nine subatomic/element collisions;
removing Z leaves 44 collisions. B is therefore redundant for **this finite
identity target**, while remaining the released boundary-capacity descriptor.
Uniqueness of the minimum: **FALSIFIED** (multiple equal-size solutions).
Canonicality: **UNRESOLVED**.

## Composition and ternary challenges

All **126** retained-field checks passed: seven fields on nine subatomic→element
comparisons and nine element→molecule multiset comparisons. **SURVIVED** for
that field-extraction law. No aggregation law for the structural observer was
proved; structural compositionality is **UNRESOLVED**.

The challenge set has **162** ordered ternary declarations: six slot permutations
times 27 charge assignments from {-1,0,1}. Its target is exact ordered degree
output on fixed labeled axes. This target deliberately observes axis roles;
it is not a physical chirality classification.

| Identity-excluding observer | Same-observer, different-degree pairs | Status for this target |
|---|---:|---|
| charged structure | 405 | FALSIFIED |
| topology | 13,041 | FALSIFIED |
| quaternion readout | 13,041 | FALSIFIED |

These are failures of the individual projected observers on the abstract
challenge. Atomic Z is not defined for these witnesses, so this is not a direct
test of the combined Z+topology descriptor outside its domain.

An exact subset search over seven ternary observers finds two minimum pairs:

- fixed-axis charge assignment + slot assignment;
- identity-excluding charged structure + slot assignment.

Both leave **zero** collisions across the 162 witnesses and all **13,041** pairs.
Removing either observer reintroduces collisions. The alternative
charge-information + first-slot-axis + parity also succeeds, but uses three
named observers. All these additions are derived from the existing ordered
coupling; no missing source primitive has been demonstrated.

There are **4,860** bijective-renaming comparisons (162 witnesses × 6 renamings ×
5 direct operations). All pass after applying the known inverse rename to exact
identifier values while preserving schema keys, numeric charges, and order.
Relabeling equivariance: **SURVIVED**. This checks known isomorphisms; it does not
prove general graph isomorphism, nor that physically different slot assignments
should be quotiented as equivalent.

## Corrections to earlier external reports

- The previous closure claim was unexecuted. This run now verifies it on all 27
  states, and establishes that B can be removed for that particular target.
- Topology is not interchangeable with charged/quaternion readouts alone.
  Their combinations with Z happen to separate this finite population.
- An ordered arity-3 declaration is available in the release. The earlier
  claimed constructor blockage was incorrect. Absence of pair declarations
  does not establish geometric nonintersection or cyclic semantics.
- Raw tuple order contains parity information; absence of a dedicated parity
  field does not mean that parity is missing from the representation.
- Earlier geometry/charged-structure relabeling failures arose from the external
  normalizer converting nested data to strings. They were not EPAC failures.
- Different raw outputs under rotations establish slot sensitivity. They do not
  falsify the possibility of deriving a cyclic quotient from retained data.
- Empty specialized local-three/quaternion outputs are evidence against treating
  those projections as general ternary observers, not automatically software bugs.

Those earlier interpretations are **DEPRECATED** where superseded here. Original
files remain as historical evidence. All 14 original comparison standings stay
**FALSIFIED**. Global state sufficiency and physical correspondence remain
**UNRESOLVED**; a finite collision-free result does not establish either.

## Usage and stopping boundary

```sh
PYTHONPATH=/tmp/epac-v010-refinement.BP387j:/tmp/ucns-epac-pinned.UvRD6f/src \
  python3 verified_refinement.py --output verified-refinement.json
python3 verify_cached_refinement.py
PYTHONPATH=/tmp/epac-v010-refinement.BP387j:/tmp/ucns-epac-pinned.UvRD6f/src \
  python3 ternary_refinement_search.py
```

Temporary roots can be reconstructed from the exact Git commits above. The EPAC
source archive needs import aliases `epac_subatomic→subatomic`, `epac_data→data`,
`epac_viz→viz` (or installation under its package metadata). These are import-path
aliases, not changed implementation.

Stop adding observables on these two tested domains: zero target collisions
remain, field necessity is witnessed, and no unique physical primitive is
selected. Larger construction domains and structural composition require their
own declared targets before a broader sufficiency claim.
