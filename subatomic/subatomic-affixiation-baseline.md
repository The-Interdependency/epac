> Migration note: this document records the stack-incubation phase. Statements that no EPAC repository existed were true of that phase and are not current repository status.

# Subatomic Affixiation Baseline — hydrogen → helium (provisional candidate)

- Status: **CROSS-DOMAIN-HYPOTHESIS / provisional research candidate**
- Root impact: **none**
- Owner of record: `The-Interdependency/stack` → `research/epac/` placeholder (no canonical epac
  repository exists yet — see `STACK_MANIFEST.md`)
- Canon class: **proposed** — nothing in this document is org canon. Established facts are
  cited from current METAPAT and UCNS sources and marked `implemented`; everything else is
  candidate or `hmmm`.

## 1. Domain claims (before any definition)

Per `domain-claims`, the operative senses are claimed before the construction uses them.

| Surface form | Term id | Claiming domain | Claimed sense | Scope | Type | Status |
|---|---|---|---|---|---|---|
| hydrogen | `physics.atomic.hydrogen` | physics | element with atomic number Z=1 | empirical element identity | native | ratified in physics |
| hydrogen (here) | `epac.subatomic_affixiation.hydrogen` | epac candidate | declared participant set: one proton participant on declared carrier positions | this construction only | specialized | provisional |
| helium | `physics.atomic.helium` | physics | element with atomic number Z=2 | empirical element identity | native | ratified in physics |
| helium (here) | `epac.subatomic_affixiation.helium` | epac candidate | declared participant set: two proton + two neutron participants (default instance He-4) affixiated over the Möbius parameter | this construction only | specialized | provisional |
| lithium (here) | `epac.subatomic_affixiation.lithium` | epac candidate | same construction form at Z=3 (default instance Li-7) | program target | specialized | provisional |
| carbon (here) | `epac.subatomic_affixiation.carbon` | epac candidate | same construction form at Z=6 (default instance C-12) | program target | specialized | provisional |
| affixiation | `metapat.affixiation_harmonics.affixiation` | METAPAT | identity-preserving higher-order declared relation; participants stay addressable; may integrate as object-whole at a declared native scale | cross-domain application | borrowed (unchanged) | CROSS-DOMAIN-HYPOTHESIS (per METAPAT application) |
| carrier position | `ucns.public_gonol.position` | UCNS | exact glyph identity at exact index on the 157-position Public Gonol carrier | UCNS geometry | borrowed (unchanged) | implemented |
| derivation (here) | `epac.subatomic_affixiation.derivation` | epac candidate | replay of the same declared construction form for another element | this document | specialized | provisional |

**Collision check:** physics owns the empirical senses of hydrogen/helium/lithium/carbon; the
epac senses are explicitly scoped to this construction and do not contest physics. No prior
hydrogen/helium/lithium claims exist in current metapat or ucns checkouts. Resolution: **clear**
(separate scopes, no overlap).

## 2. METAPAT consultation

- question: what relation organizes the hydrogen → helium baseline over the UCNS carrier?
- METAPAT standing: **application** — `metapat.application.affixiation_harmonics`
  (CROSS-DOMAIN-HYPOTHESIS, root impact none); not axiom, postulate, or theorem.
- relevant relation: affixiation (identity-preserving higher-order relation), time-agnostic
  recurrence and oscillation, harmonic correspondence and resonance as candidate language.
- transfers: the shared question form only —

  ```text
  addressable participants
  -> declared relation
  -> declared ordered parameter or parameters
  -> recurrent structure
  -> harmonic correspondence or non-correspondence
  -> possible native-scale integration
  -> recursively addressable whole
  ```

- does not transfer: element identity or empirical facts (physics), carrier/containment/geometry
  selection (UCNS), geometric operation of carrier positions (UCNS `hmmm`), measurement validity
  (EDCM), physical frequency or temporal periodicity.
- downstream consequence: a named, bounded epac candidate may proceed with a declared admission
  profile, the Möbius turn index as the time-agnostic ordered parameter, and explicit `hmmm` on
  every position operation.

## 3. UCNS established baseline (implemented surfaces only)

Cited from current UCNS at `1975fe70`:

- **Public Gonol carrier** (`implemented`): exactly 157 one-scalar glyph positions in fixed order;
  digest `55d10c84529a4d7bc7714786357e977b68d9df2ac3f73d20e229580b552c2ef5`; every glyph is a
  function position; no linguistic subclassing.
- **Structural Null origin** (`implemented`): fixed origin at carrier position `0` (glyph `" "`),
  singular, not ordinary numeric zero.
- **Native Möbius root loop** (`implemented`): quotient `(t, ε) ~ (t + n, (-1)^n ε)` with exact
  rational turns. One visible turn (t=1) returns to the same phase with the local frame reversed;
  two visible turns (t=2) restore the complete state.
- **Position operations** (`hmmm`, declared in `ucns/src/ucns/public_gonol.py` MODULE_BUILD):
  "the exact geometric operation expressed by each function position beyond its carrier identity"
  is unresolved. No construction here may invent one.

## 4. Candidate construction (named, bounded, provisional)

### 4.1 Admission profile (epac-owned candidate, instance-resolved)

- Element `E(Z, A)` is represented by `Z` proton-participant positions and `A − Z`
  neutron-participant positions on the Public Gonol carrier.
- Default isotope instances are declared per element — H-1, He-4, Li-7, C-12. Isotope choice is
  **instance-resolved**, not a law of the construction.
- Proton participants occupy the first `Z` carrier positions after the origin: positions
  `1 .. Z`. Neutron participants occupy the next `A − Z` positions: positions `Z+1 .. A`.
- Every assigned position is an **identity coordinate only**. No geometric operation is asserted
  for any position.

### 4.2 Baseline: hydrogen → helium

```text
hydrogen (H-1): participants {p0 @ position 1}
    relation: none (single participant)
    closure: participant-scale whole

helium (He-4): participants {p0 @1, p1 @2} ∪ {n0 @3, n1 @4}
    declared relation: affixiation
    ordered parameter: Möbius turn index t ∈ {0, 1, 2}   (time-agnostic)
      t=0: simultaneous tensor arrangement of participants (tensor-first)
      t=1: visible 360° return — local frame flips (distinguishable relational state)
      t=2: complete 720° return — full framed state restored
    recurrence: frame flip/restore is the recurrent structure over parameter t
    closure: affixiated helium-whole at the declared atomic native scale;
             constituents remain addressable with identity and provenance
```

The only geometry used is the established Möbius framing. The carrier positions supply identity;
they do not yet supply operations. Hydrogen and helium differ by participant set and affixiation
arity — nothing else is claimed.

### 4.3 Derivation of lithium, carbon, et al. (same construction form)

```text
lithium (Li-7): p @1,2,3 ; n @4..7    -> affixiate -> Möbius recurrence -> atomic-scale closure
carbon  (C-12): p @1..6  ; n @7..12   -> affixiate -> Möbius recurrence -> atomic-scale closure
```

Each further element is a **separate candidate instance** of the same construction form. "Derive"
in this document means **replay the same declared construction** for a different declared
participant set. It does not mean a physics derivation, a UCNS theorem, a chemical fact, or a
proof that one element emerges from another.

### 4.4 Deterministic receipt (replay contract)

For each closed element-whole, a receipt is the SHA-256 over canonical JSON of:

```text
element_id, isotope_instance, ordered proton positions, ordered neutron positions,
relation_id ("affixiation"), ordered parameter ("ucns.native-mobius-turn-index"),
t-state sequence (0 -> 1 -> 2), closure_scale ("atomic"), source_commits
```

Independent replay must reproduce the receipt byte-for-byte. A receipt establishes
reproducibility of the declared construction only — not geometry, physics, or measurement.

## 5. What this establishes — and what it does not

**Established (proposed candidate):** a source-bound, replayable baseline that binds current
METAPAT affixiation semantics to current UCNS carrier identity surfaces, using the native Möbius
turn index as the time-agnostic ordered parameter.

**Not established:** any Public Gonol position operation; any geometry between carrier positions;
any harmonic notation or resonance coupling; any physics or chemistry claim; any EDCM measurement
projection; any canon promotion in METAPAT, UCNS, or elsewhere.

## 6. Usage guidance

To replay by hand:

1. Pin sources: METAPAT `34d954a`, UCNS `1975fe7` (recorded above and in `STACK_MANIFEST.md`).
2. Read `metapat/docs/applications/affixiation-harmonics.md` for the semantic definitions used.
3. Read `ucns/src/ucns/public_gonol.py` and `ucns/src/ucns/direct_mobius.py` for the carrier and
   Möbius surfaces used.
4. Apply the admission profile in §4.1, run the construction in §4.2/§4.3, and verify the receipt
   in §4.4 against an independent replay.

To implement later (only after UCNS establishes position operations, or as a pure identity-profile
consumer):

```text
entry points: ucns.public_gonol_function(index)  # carrier identity position
              ucns.native_mobius_state(turns)    # established Möbius framing
```

Do not add local geometry, position-operation semantics, or physics status inside this candidate.

## 7. Next decisive step (action-calibration)

- decision: is the H→He affixiation baseline a usable identity-level candidate for the epac program?
- minimal decisive action: an executable H→He candidate that consumes only the two UCNS public
  surfaces above, produces the §4.4 receipt, and is independently replayed byte-identically.
- positive outcome → escalate to Li/C instances of the same constructor.
- negative outcome → the admission profile or receipt contract needs repair before any Li/C work.
- unresolved outcome → UCNS position operations remain `hmmm`; keep identity-only scope.
- frozen stop condition: receipt mismatch or any invented position operation fails the candidate.

## 8. hmmm

- The geometric operation of every Public Gonol position beyond carrier identity remains unresolved
  (UCNS-owned `hmmm`); this baseline deliberately does not fill it.
- No UCNS harmonic-resonance notation is selected (METAPAT-owned `hmmm`); phase/ratio/coupling
  fields remain candidates.
- Isotope defaults (H-1, He-4, Li-7, C-12) are instance-resolved, not canonical admission law.
- epac has no canonical source repository; this record lives in the stack placeholder and must
  migrate if `The-Interdependency/epac` is created.
- No EDCM measurement projection is declared; nothing here may become empirical validation.
- Promotion of affixiation from application terminology into METAPAT postulates/theories remains
  unresolved and is not advanced by this candidate.

## 9. Local implementation status (2026-08-22)

The frozen minimal decisive action from §7 is now implemented locally (not pushed):

- `element_affixiation_candidate.py` — identity-only constructor for H/He/Li/C consuming only
  `ucns.public_gonol_function` and `ucns.native_mobius_state`. Carries `MODULE_BUILD` and
  `CONTRACTS` blocks; no position operation is defined or inferred.
- `test_element_affixiation_candidate.py` — five executable witnesses with a `CHECKS` block.
  Result: **5 passed** against the pinned UCNS snapshot package (`ucns/src` at `1975fe7`).
- `receipts/` — sealed construction receipts, one per element:

  | Element | Receipt (SHA-256) |
  |---|---|
  | H | `be411f204e10c14ac42b2983677f6b22a02d1cb6c4b158bf2026b0b6e88ca3da` |
  | He | `5d7d82a86bb59223495663cbf285310900fdad9499fb8b50f8fe355786a9edc7` |
  | Li | `5efefff19f97e4f42fa0d85d9719adbe07c39fc7dab700a5eea13f434611bb3f` |
  | C | `a4026f197d6a0425b4ea5b3ff72d09d49fd159d5f59440480b5f97793b64cdc6` |

- Independent replay (`replay_element`) is byte-identical for all four elements.
- Status remains `CROSS-DOMAIN-HYPOTHESIS / provisional`. Nothing here establishes position
  operations, geometry between positions, harmonic notation, physics, or canon.

## 10. Physically sourced harmonic candidates (2026-08-22)

Per METAPAT's evidence contract, harmonic candidates do **not** wait for a UCNS harmonic
notation. Each candidate declares participants, ordered parameter, recurrence mapping,
equivalence condition, information loss, and physical provenance. The ordered parameter is
the time-agnostic nucleon-content sequence `(A, Z)`, not time and not an unsourced phase.
No Public Gonol position operation is invented.

- `nuclear_harmonic_candidates.py` — five candidates with `MODULE_BUILD` + `CONTRACTS`.
- `test_nuclear_harmonic_candidates.py` — five witnesses with `CHECKS`. **10/10 tests pass**
  across both modules; CONTRACTS↔CHECKS audit **closed** (10 contracts / 10 checks).
- `receipts/harmonic_*.json` — sealed candidate records.

| Candidate | Kind | Li-7 | C-12 | Receipt |
|---|---|---|---|---|
| alpha-cluster recurrence | recurrence | recurs | recurs | `212fd1bf…e5ad` |
| N/Z ratio commensurability | ratio | no (4/3) | recurs (1) | `8a49097a…f030` |
| ground-state spin-parity symmetry | symmetry | no (3/2⁻) | recurs (0⁺) | `b0d5eded…dd77a` |
| binding-per-nucleon commensurability | commensurability | no (~21% dev) | recurs (~8% dev) | `6a888f65…54e9` |
| proton↔neutron inversion symmetry | inversion | no (N≠Z) | recurs (N=Z) | `9ac380f4…52f9` |

Surviving relation across Li and C: **only the alpha-cluster recurrence** survives both;
the four N=Z / even-even relations survive C-12 but not Li-7. Physical provenance for the
numeric nuclear data is web-pinned 2026-08-22; alpha-cluster and isospin citations remain
`hmmm` (standard references, exact citation not web-pinned this session). All results remain
`CROSS-DOMAIN-HYPOTHESIS / hmmm` — no physics validation or canon is claimed.

## 11. Subatomic gonol (2026-08-22)

The subatomic gonol closes one element gonol per symbol from three separately addressable
layers, using the EPAC Public Gonol constructor (`epac.public_gonol`) on the UCNS
Public Gonol carrier. This is not `edcm.gonol`:

1. **nucleus participant** — subatomic identity (proton/neutron Public Gonol carrier
   positions and glyphs, Möbius t-state frame sequence) plus harmonic relation results;
2. **electron-shell participants** — the quantum layer from `epac_atomic` (n, l, m_l, m_s,
   shell, subshell, hydrogenic angular id, radial nodes, Slater Z_eff, Rydberg energy);
3. **element closure** — relation `epac.subatomic.element`, carried options Z/period/group/A,
   electron configuration, valence count, surviving harmonic relations, status
   `CROSS-DOMAIN-HYPOTHESIS`.

- `subatomic_gonol.py` — constructor with `MODULE_BUILD` + `CONTRACTS`.
- `test_subatomic_gonol.py` — five witnesses with `CHECKS`. **15/15 tests pass** across all
  three subatomic modules; CONTRACTS↔CHECKS audit **closed** (15 contracts / 15 checks).
- `receipts/gonol_*.json` — historical EDCM-constructor receipts, superseded as
  constructor identity. Replay of the current constructor is `replay_public_gonol`.

| Element | Gonol receipt digest |
|---|---|
| H | `3191f743…bc22b` |
| He | `37991f4b…6c3c37` |
| Li | `ff23abd7…312c95` |
| C | `f951b648…45f0e3` |

Layers stay distinct inside the gonol: nucleus and electron shells remain individually
addressable participants with their own source_ids. No position operation, no Möbius coupling
law, and no scale interchange is introduced. Standing is `implemented-candidate`,
`selection_effect: none` — the gonol is a candidate, not selected canon.

## 13. Extension to iron and symbol-abbreviation coupling (2026-08-22)

- **Extended quantum layer** (`extended_atomic.py`): Z=1..26. Z≤18 delegates byte-identically
  to `epac_atomic`; Z=19..26 uses declared ground-state configurations (K through Fe), including
  the Cr `4s1.3d5` exception. Fe = `1s2.2s2.2p6.3s2.3p6.4s2.3d6`, A=56.
- **Subatomic gonol now supports all 26 symbols** (`subatomic_gonol.py`), using
  `extended_atomic` and the EPAC Public Gonol constructor (`epac_public_gonol`).
- **Nomenclature abbreviation** (`symbol_coupling.py`): letters are **not** a physics
  domain. A chemical-symbol abbreviation is a name attached to a closed element gonol.
  Two-letter names (He, Fe) are two ordered name-characters, not physical `(z, x)` /
  `(z, y)` couplings and not nuclear-Z charge states. Physics 3-structure stays on
  atom instances only.
- Evidence: **26/26 subatomic tests pass**; sibling epac suite **29 tests OK**;
  CONTRACTS↔CHECKS audit **closed** (26 contracts / 26 checks).
- The dimensional-arity doctrine is implemented by the sibling `epac_dimensional_arity.py`
  (committed); no duplicate is maintained here. Status remains `CROSS-DOMAIN-HYPOTHESIS`.
