> Migration note: this preregistration was frozen in the stack incubator before EPAC extraction. Its original authority/context statements are retained as historical evidence.

# Preregistration: molecular geometry from element gonols

- Status: **CROSS-DOMAIN-HYPOTHESIS / provisional research candidate**
- Owner of record: `The-Interdependency/stack` → `research/epac/`
- Constructor: `epac.public_gonol` on the pinned UCNS Public Gonol carrier.
  Not `edcm.gonol`.
- Comparison policy is frozen **before** construction. Known molecular-shape
  labels are sealed and may be opened only by the comparison step.

## Domain claims

| Surface form | Term id | Claiming domain | Claimed sense | Excluded |
|---|---|---|---|---|
| element gonol | `epac.periodic.element_gonol` | epac candidate | closed gonol of one periodic-table element carrying Z, ground-state electron configuration, and typical main-group valence | molecular shape, bond angle, hybridization |
| valence arity | `epac.periodic.typical_valence` | epac candidate | main-group hydride valence from the periodic table (group-derived) | VSEPR domain count as a shape rule |
| affixiation | `metapat.affixiation_harmonics.affixiation` | METAPAT | identity-preserving higher-order relation | UCNS topology selection |
| UCNS coupling | `ucns.native-mobius-root-loop` | UCNS | established 360° frame flip / 720° restore | invented 3-space arrangement |
| molecular gonol | `epac.molecular.affixiated_whole` | epac candidate | closed recursive gonol of element-gonol participants | known chemistry shape names |
| predicted geometry | `epac.molecular.construction_invariants` | epac candidate | atom count, center valence, slot occupancy, Möbius frame sequence | sealed comparison labels |

Collision check: physics/chemistry own empirical molecular shapes. This candidate
does not claim those senses during construction. Resolution: **clear** (separate
scopes) until comparison.

## Frozen pipeline

```text
proton gonols (charge +1) and neutron gonols (charge 0)
  -> nucleus = affixiation of those nucleons; (proton_j, neutron_i)
  -> every electron instance: (nucleus, electron_i) with charges (Z, -1)
  -> close that atomic 3-structure inside the element gonol
  -> unpaired-valence attachment sites
  -> declared oriented (center, ligand_i) couplings with per-slot Z and Möbius ε
  -> molecular three-dimensional structure = those atom-instance couplings + charge states + degree
  -> each local 3 represented in 4 quaternion components (scalar ε plus the three axis charges)
  -> molecular Public Gonol (closed atoms remain atomic participants)
  -> construction invariants
  -> (only then) compare to sealed known chemistry
```

## Inputs allowed in construction

- atomic number Z, default isotope A
- each proton instance and each neutron instance of that isotope (counts must match Z and A−Z)
- every electron: n, l, m_l, m_s, shell, subshell
- hydrogenic angular identity Y_l^m, radial node count n-l-1
- Slater atomic Z_eff and hydrogenic Rydberg energy -Z_eff²/n²
- unpaired valence electrons from Hund filling
- atomic s→p promotion in the same n when more unpaired sites are required
- caller-supplied stoichiometric formula (element counts only)

## Inputs forbidden in construction

- bond angles
- VSEPR shape names
- hybridization labels used as shape
- any sealed comparison filename contents

## UCNS coupling candidate

Only the implemented Möbius root loop is applied:

```text
(t, ε) ~ (t + n, (-1)^n ε)
t = 0, 1, 2
```

Public Gonol positions, when supplied, are identity coordinates. Position
operations remain `hmmm`. No spherical equal-spacing rule is added.

## Molecules in this run

`H2`, `H2O`, `NH3`, `CH4`, `CO2`

## Comparison policy (frozen)

Opened only after molecular gonols exist:

1. Construction source and receipts must not contain the sealed shape labels.
2. Record construction invariants per formula.
3. Open `data/sealed_known_molecular_geometry.json`.
4. Ask whether the constructed three-dimensional structure distinguishes
   formulas that chemistry distinguishes by shape.
5. Compare four signatures: charged oriented couplings plus degree (the
   3-structure already in the math); arity/degree topology without charge;
   UCNS Möbius coupling; atomic unpaired (l, m_l) plus ligand shell content;
   against a matched-information control of formula symbols only.
   Do not import sealed shape names into construction.

## Terminal standings for the hmmm question

The question: does gonol geometry predict molecular shape, or merely reproduce
information already present in the inputs?

- `SURVIVED` as prediction — only if the charged 3-structure is invariant
  inside each sealed shape class, distinguishes different sealed classes, and
  is not the matched-information control.
- `FALSIFIED` as prediction — if the 3-structure splits a sealed class, or
  collapses classes chemistry splits, or if distinguishing power is already
  present in valence+stoichiometry.
- `UNRESOLVED` — if the readout is incomplete.
- None of these standings select canon.

## hmmm

- Public Gonol function operations beyond carrier identity
- whether a later UCNS 3-space coupling exists that is not VSEPR imported
- expansion of the element table beyond Z=1–18
- epac still has no canonical source repository
