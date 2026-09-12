"""UCNS / EPAC lifted-spiral visualizer.

Renders the framed Möbius root-loop (the "lifted spiral") that is witnessed
by gonol construction data.

The visualizer consumes only data already present in:
- PublicGonol receipts (structure, carried_options)
- MolecularConstruction / element gonol invariants (the "mobius" dict)
- native_mobius_state(t) from the UCNS carrier

It does not invent geometry, positions, or couplings. It projects the
declared attachment evidence and charge states onto the canonical
visible-phase + frame double-cover.

Full population of the declared experiment (all 9 molecules + representative
elements) is available via extract_full_spiral_population.

Usage:
    from epac.viz.spiral_viz import render_molecule_spiral_svg, render_to_text
    from epac_molecular import construct_molecule

    c = construct_molecule("H2O")
    svg = render_molecule_spiral_svg(c)
    print(render_to_text(c))
"""

from __future__ import annotations

from .spiral_viz import (  # noqa: F401
    extract_spiral_scene,
    extract_full_spiral_population,
    spiral_population_keys,
    render_molecule_spiral_svg,
    render_element_spiral_svg,
    render_to_text,
    render_scene_svg,
    get_möbius_law_source,
)

__all__ = [
    "extract_spiral_scene",
    "extract_full_spiral_population",
    "spiral_population_keys",
    "render_molecule_spiral_svg",
    "render_element_spiral_svg",
    "render_to_text",
    "render_scene_svg",
    "get_möbius_law_source",
]
