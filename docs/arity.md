# Dimensional arity

Status: **CROSS-DOMAIN-HYPOTHESIS / provisional**. Not org canon.

Dimension tells where. Arity tells what intersects at once. Degree tells how a
dimension is incident on declared couplings.

```text
(z, x) ≠ (x, z)
(x, z) and (y, z) ↛ (x, y, z)   without an explicit proof

every physical instance of x has its own (z, x_i)
every physical instance of y has its own (z, y_j)
```

A second atom occurrence is a second instance. `(z, x_0)` does not cover `x_1`.
`(x_i, z)` does not satisfy `(z, x_i)`. Letters and chemical-symbol
abbreviations are nomenclature, not physics, and are not these instances.

Precursors: each proton and each neutron is a closed gonol. The nucleus is
their affixiation. Neutrons couple to protons as `(proton_j, neutron_i)` with
slot charges `(+1, 0)`. Proton-proton and neutron-neutron are not inferred.
Hydrogen-1 is one proton and no neutrons.

At atomic scale the hub is that closed nucleus and every electron instance has
its own `(nucleus, electron_i)` with slot charges `(Z, -1)`. Molecular scale
does not reopen nucleons or electrons: water remains `(O#2, H#0)` and
`(O#2, H#1)`.

Degree is required. For ambient `{x,y,z}` with couplings `(z,x)` and `(z,y)`:

```text
deg(z) = 2 at slot 0
deg(x) = 1 at slot 1
deg(y) = 1 at slot 1
```

That incidence structure is the geometry of two binary couplings sharing `z`.
It is not a ternary coupling and not `(x,y)`.

Charge state rides on each coupling from the math already present: per-slot
dimension charges (nuclear `Z` when the axis is an atom) and Möbius `ε` at
`t=0`. `(z,x)` with charges `(q_z, q_x, ε)` is not `(x,z)` with
`(q_x, q_z, ε)`. The three-dimensional structure **is** that combination —
oriented couplings, each arity's charge state, and degree. Two charged
arity-2 couplings on a degree-2 hub already occupy three participating axes.
It still does not declare `(x,y,z)`.

Representing that 3 takes 4 dimensions: a quaternion
`(ε, q_z, q_x, q_y)`. The extra coordinate is the scalar, Möbius `ε`, already
in the math. It is not a fourth ambient axis, not Minkowski time, and not a
Hamilton-product proof of `(x,y,z)`. `ij = k` does not install a coupling.
Helium's nucleus plus two electrons is one local 3 in 4-representation;
the letters `H` and `e` are not those axes. A single binary (H₂, hydrogen
atom) is not a 3 and has no quaternion.

Construction is `epac.public_gonol` on the UCNS Public Gonol carrier, not
`edcm.gonol`.

Overlap of members is not a proof. Forbidden inference rules include
`overlap-closure`, `permutation-identity`, and `ambient-power-set`.

See `epac_dimensional_arity.py`. After construction, `epac_comparison.py` reads
that 3-structure against sealed known chemistry. Sealed shape names stay out
of construction.
