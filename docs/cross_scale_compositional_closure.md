# EPAC Cross-Scale Compositional Closure

Status: internal EPAC evidence result for the presently implemented stack.

Decision: **SURVIVED** for the locked nine-formula construction surface, under
the explicit scale-local rules tested in `epac_cross_scale_closure.py`.

This report does not import, inspect, map, or depend on PCEA internals. It does
not inspect UCNS internals, define a continuum theorem, make an external
physics/chemistry claim, or define a runtime encoding.

## Descriptor Semantics

`B(R) = (3, d_boundary, c_boundary)`

- `3`: fixed interior mode count carried by the implemented EPAC receipts.
- `d_boundary`, subatomic: count of lifted-spiral axes at subatomic scale
  (nucleus plus shell participants).
- `d_boundary`, element: count of periodic element axes (nucleus plus electron
  axes), derived from subatomic receipts by refining shell participants into
  their electron children.
- `d_boundary`, molecule: count of closed element gonol participant axes at
  molecule scale.
- `c_boundary`: count of declared valence attachment slots. Bare subatomic and
  bare element states carry `0`.

The scale rule is the existing Public Gonol closure invariant: once closed, a
gonol is atomic at later participation. Lower-scale internal axes are refined
or projected by explicit local operations; they are not conserved as
molecule-scale axes.

## Per-Element Ledger

Required elements from the nine formulas: `H`, `O`, `N`, `C`, `S`, `B`, `F`,
`P`, `Si`.

| element | required by | raw subatomic B | derived element B | bare element B | status |
|---|---|---:|---:|---:|---|
| H | H2, H2O, NH3, CH4, H2S, PH3, SiH4 | `(3, 2, 0)` | `(3, 2, 0)` | `(3, 2, 0)` | SURVIVED |
| O | H2O, CO2 | `(3, 3, 0)` | `(3, 9, 0)` | `(3, 9, 0)` | SURVIVED |
| N | NH3 | `(3, 3, 0)` | `(3, 8, 0)` | `(3, 8, 0)` | SURVIVED |
| C | CH4, CO2 | `(3, 3, 0)` | `(3, 7, 0)` | `(3, 7, 0)` | SURVIVED |
| S | H2S | `(3, 4, 0)` | `(3, 17, 0)` | `(3, 17, 0)` | SURVIVED |
| B | BF3 | `(3, 3, 0)` | `(3, 6, 0)` | `(3, 6, 0)` | SURVIVED |
| F | BF3 | `(3, 3, 0)` | `(3, 10, 0)` | `(3, 10, 0)` | SURVIVED |
| P | PH3 | `(3, 4, 0)` | `(3, 16, 0)` | `(3, 16, 0)` | SURVIVED |
| Si | SiH4 | `(3, 4, 0)` | `(3, 15, 0)` | `(3, 15, 0)` | SURVIVED |

Element closure is not raw-count equality. For non-hydrogen elements, the
subatomic descriptor counts shell axes, while the element descriptor counts
electron axes. The tested local operation is:

`epac.boundary.subatomic-shells-to-periodic-electron-axes`

It derives periodic element axes from the subatomic receipt's nucleus
participant and shell electron children, with no target descriptor input.
Declared, reversed-shell, reversed-electron, and reversed-both traversal
variants all derive the same element axes.

## Per-Formula Ledger

| formula | local paths | composed B | locked direct B | status |
|---|---:|---:|---:|---|
| H2 | 1 | `(3, 2, 2)` | `(3, 2, 2)` | SURVIVED |
| H2O | 3 | `(3, 3, 2)` | `(3, 3, 2)` | SURVIVED |
| NH3 | 4 | `(3, 4, 3)` | `(3, 4, 3)` | SURVIVED |
| CH4 | 5 | `(3, 5, 4)` | `(3, 5, 4)` | SURVIVED |
| CO2 | 3 | `(3, 3, 4)` | `(3, 3, 4)` | SURVIVED |
| H2S | 3 | `(3, 3, 2)` | `(3, 3, 2)` | SURVIVED |
| BF3 | 4 | `(3, 4, 3)` | `(3, 4, 3)` | SURVIVED |
| PH3 | 4 | `(3, 4, 3)` | `(3, 4, 3)` | SURVIVED |
| SiH4 | 5 | `(3, 5, 4)` | `(3, 5, 4)` | SURVIVED |

The molecule-scale rule is:

`epac.boundary.closed-elements-to-molecule-affixiation`

Each compatible closed element contributes one molecule-scale atom axis. Each
affix step adds the ligand's local unpaired-valence attachment count to
`c_boundary`. All generated local paths are path-independent, locally
reproducible, and equal to the already locked molecule receipt descriptor.

## Control Failure Disposition

`subatomic_lifted_spiral_matches_control` is classified as
**stale_or_incorrect_control_assertion**, not as a compositional counterexample.

On the current nine-formula surface, the bare subatomic lifted-spiral projection
and the stoichiometric control both partition into nine singleton classes, so a
prior expectation that this exact-match flag must be false is stale. More
importantly, the exact-match flag is a partition-resemblance fact; it is not a
direct/composed boundary-transition invariant and does not promote or falsify
cross-scale boundary-capacity compositionality by itself.

## Aggregate Status

| item | status |
|---|---|
| subatomic_to_element_closure | SURVIVED |
| element_state_compatibility | SURVIVED |
| end_to_end_subatomic_to_molecule_closure | SURVIVED |
| boundary_capacity_compositionality | SURVIVED |

## Requires More

- External physical interpretation remains outside this EPAC evidence layer.
- Future alternate element or molecule construction paths must be added to this
  audit before claiming path independence over them.
- No continuum or runtime channel encoding is derived here.

Verification command:

```bash
PYTHONPATH="research/epac:research/epac/subatomic:libs/ucns/src" python3 -m unittest research/epac/tests/test_cross_scale_compositional_closure.py -q
```
