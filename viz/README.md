# UCNS / EPAC Lifted-Spiral Visualizer

Renders the framed Möbius root-loop ("lifted spiral") witnessed by gonol constructions.

The visualizer is driven exclusively by data that already exists after construction:

- The `mobius` invariant on `MolecularConstruction` (produced by `_mobius_coupling`)
- `receipt.structure` (charged couplings, degree, quaternions)
- `native_mobius_state` from the UCNS carrier (only for canonical frame labels)

It never invents UCNS positions, couplings, or geometry. It only projects what the gonols already declared.

## Quick start

From `src/stack/research/epac`:

```bash
export PYTHONPATH=".:subatomic:../../libs/ucns/src"

# Text view of the spiral for a molecule
python3 -m viz H2O

# SVG for the same molecule
python3 -m viz --svg H2O > /tmp/h2o.svg

# Element gonol (periodic path)
python3 -m viz --element --svg C > /tmp/carbon.svg
```

## What is shown

- Three canonical turns (t=0, t=1, t=2)
- Constant visible phase (the root-loop quotient)
- Local frame flip at one turn, restoration at two turns
- Participant axes (the gonol dimensions that participate)
- Attachment slots (valence attachment evidence)
- Charge states attached to those axes
- One-turn-flip / two-turn-complete restoration flags

## Provenance

Every `SpiralScene` carries `möbius_law_source` — the absolute path to the single UCNS module that defines the framed root-loop law:

    (t, ε) ~ (t + n, (-1)^n ε)

visible_key vs. complete_key, and the one-turn-flip / two-turn-restore behavior.

You can also call:

    from epac_viz.spiral_viz import get_möbius_law_source
    print(get_möbius_law_source())

This is the exact file the background search located and the file that all gonol constructions (subatomic → element → molecule) actually use.

## Files

- `spiral_viz.py` — core extraction + text + SVG renderers
- `cli.py` — small command-line driver
- `__init__.py`, `__main__.py` — package niceties

All output is pure data projection. No new claims, no position operations, no geometry invention.
