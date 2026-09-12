"""Tiny CLI for the UCNS / EPAC lifted-spiral visualizer.

Usage examples (from the epac directory with correct PYTHONPATH):

    PYTHONPATH=".:subatomic:../../libs/ucns/src" python -m epac.viz.cli H2O
    PYTHONPATH=".:subatomic:../../libs/ucns/src" python -m epac.viz.cli --svg H2O > /tmp/h2o_spiral.svg
    PYTHONPATH=".:subatomic:../../libs/ucns/src" python -m epac.viz.cli --element O
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .spiral_viz import (
    extract_spiral_scene,
    render_molecule_spiral_svg,
    render_element_spiral_svg,
    render_to_text,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render UCNS lifted spirals from gonols")
    parser.add_argument("formula_or_symbol", nargs="?", default="H2O",
                        help="Molecule formula (H2, H2O, CH4, ...) or element symbol when --element is used")
    parser.add_argument("--element", action="store_true",
                        help="Treat the argument as an element symbol and render its gonol spiral")
    parser.add_argument("--svg", action="store_true",
                        help="Emit SVG instead of text")
    parser.add_argument("--out", type=str, default=None,
                        help="Write output to this file instead of stdout")
    parser.add_argument("--width", type=int, default=920)
    parser.add_argument("--height", type=int, default=520)

    args = parser.parse_args(argv)

    try:
        if args.element:
            from epac_periodic import construct_element_gonol
            receipt = construct_element_gonol(args.formula_or_symbol)
            scene = extract_spiral_scene(receipt)
            if args.svg:
                out = render_element_spiral_svg(receipt, width=args.width, height=args.height)
            else:
                out = render_to_text(scene)
        else:
            from epac_molecular import construct_molecule
            construction = construct_molecule(args.formula_or_symbol)
            scene = extract_spiral_scene(construction)
            if args.svg:
                out = render_molecule_spiral_svg(construction, width=args.width, height=args.height)
            else:
                out = render_to_text(scene)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    else:
        print(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
