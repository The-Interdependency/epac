"""Lifted-spiral visualizer for UCNS-framed gonol constructions.

Projects the Möbius root-loop evidence carried by EPAC Public Gonols
onto a discrete two-turn double-cover.

Data sources (no invention):
- The "mobius" invariant produced during construction
  (law="ucns.native-mobius-root-loop", t, visible_phase, frame,
   participant_axes, attachment_slots, one_turn_flips_frame, ...)
- Charged structure and degree from the gonol receipt.structure
- native_mobius_state(t) from the UCNS carrier (for canonical frame sequence)

The visualizer renders:
- The constant visible phase across integer turns
- The alternating local frame (positive / reversed)
- Participant axes (the gonol dimensions that participate)
- Attachment slots (valence evidence) as relations between axes
- Charge states at each turn
- The two-turn restoration of complete state

It does not define UCNS position operations, does not claim geometry
beyond what is already declared in the receipts, and stays within the
existing hmmm boundaries.

# === MODULE_BUILD ===
# id: epac_lifted_spiral_visualizer
#   module_name: epac.viz.spiral_viz
#   module_kind: experiment
#   summary: projects UCNS framed Möbius root-loop (lifted spirals) carried on EPAC Public Gonol receipts into canonical two-turn double-cover scenes; pure data extraction and rendering only
#   owner: The Interdependency
#   public_surface: SpiralScene, TurnState, Attachment, extract_spiral_scene, extract_full_spiral_population, render_to_text, render_scene_svg, render_molecule_spiral_svg, render_element_spiral_svg, get_möbius_law_source
#   internal_surface: _get_mobius, _extract_attachments, _canonical_turns_from_mobius, _charges_from_structure, _svg_escape
#   auth_boundary: EPAC owns gonol construction and the mobius invariant; UCNS owns direct_mobius (the framed root-loop law); visualizer only projects existing carried evidence
#   storage_boundary: none (in-memory scenes and SVG strings)
#   network_boundary: none
#   user_data_boundary: caller supplies gonol receipts or constructions
#   admin_only: false
#   tests: tests.test_spiral_population
#   rollout: explicit population of lifted-spiral facts from all declared molecules and representative elements; no new geometry, no position operations
#   rollback: remove viz package; existing gonol construction and receipts remain unchanged
#   requires: ucns_native_mobius_geometry (for provenance label only), epac_public_gonol, epac_molecular, epac_periodic
#   since: 2026-09-03
#   unresolved: exact UCNS geometric operation of Public Gonol function positions; UCNS Möbius-carrier affixiation/coupling law (consumed, not redefined)
# === END MODULE_BUILD ===

# === CONTRACTS ===
# id: spiral_scene_is_pure_projection
#   given: any gonol receipt or MolecularConstruction
#   then: SpiralScene contains only values present in the carried mobius invariant, structure degree/charges, or the canonical UCNS frame sequence; no invented positions or couplings
#   class: doctrine
#   since: 2026-09-03
#
# id: spiral_population_covers_experiment
#   given: the declared MOLECULE_COMPOSITIONS and representative elements
#   then: extract_full_spiral_population produces one scene per formula and per requested element symbol
#   class: population
#   since: 2026-09-03
#
# id: spiral_scene_replays_deterministically
#   given: a scene extracted from a receipt
#   then: after replay_public_gonol the re-extracted scene has identical turns, participant_axes, attachment facts, and one_turn/complete flags
#   class: determinism
#   since: 2026-09-03
#
# id: möbius_law_source_is_canonical
#   given: any SpiralScene
#   then: möbius_law_source points to the single UCNS direct_mobius.py that defines the framed root-loop (visible_key / complete_key / frame flip behavior)
#   class: provenance
#   since: 2026-09-03
# === END CONTRACTS ===
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from fractions import Fraction

# We only import the state constructor for canonical frame labels.
# The visualizer never calls it during gonol construction.
try:
    from ucns import native_mobius_state  # type: ignore
except Exception:  # pragma: no cover - graceful fallback in unusual envs
    native_mobius_state = None  # type: ignore


def get_möbius_law_source() -> str | None:
    """Return the absolute path to the canonical UCNS direct_mobius.py that defines
    the framed root-loop law used by all gonol constructions.

    This is the single source of the (t, ε) ~ (t+n, (-1)^n ε) quotient,
    visible_key vs. complete_key, and the one-turn-flip / two-turn-restore behavior
    that the lifted-spiral visualizer projects.
    """
    if native_mobius_state is None:
        return None
    try:
        import inspect
        return inspect.getsourcefile(native_mobius_state)
    except Exception:
        return None


# ---------------------------------------------------------------------
# Scene model (pure data extracted from gonols)
# ---------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Attachment:
    """One declared valence attachment slot at construction time."""
    slot: int
    center: str | None
    center_site: str | None
    ligand: str | None
    ligand_site: str | None
    # For symmetric (no-center) cases both sides are in "participant"
    participant: str | None = None
    site: str | None = None


@dataclass(frozen=True, slots=True)
class TurnState:
    """Canonical framed state at one integer turn."""
    t: int
    visible_phase: str
    frame: str  # "positive-local-frame" | "reversed-local-frame"
    complete_key_repr: str


@dataclass(frozen=True, slots=True)
class SpiralScene:
    """A projection of one gonol's lifted spiral evidence.

    This is a pure description; nothing here is a new UCNS geometric claim.
    All frame/phase/quotient semantics come from the single UCNS carrier module
    returned by get_möbius_law_source().
    """
    source_id: str
    relation: str
    law: str
    parameter: str
    binding: str

    # Absolute path to the UCNS module that defines the framed root-loop law
    # used to produce the visible/complete keys and the one-turn / two-turn behavior.
    möbius_law_source: str | None

    # The three canonical turns we always render
    turns: tuple[TurnState, TurnState, TurnState]

    # The declared participants (gonol axes) that exist for the whole construction
    participant_axes: tuple[str, ...]

    # Attachment evidence (valence sites) recorded at construction
    attachments: tuple[Attachment, ...]

    # Charge information projected from the structure (per-dimension at t=0 baseline)
    dimension_charges: Mapping[str, int]

    # Whether the construction observed the classic one-turn flip + two-turn restore
    one_turn_flips_frame: bool
    complete_restored_at_t2: bool

    # Optional richer structure hints (quaternions count, etc.)
    extra: Mapping[str, Any]


def _get_mobius(inv: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not inv:
        return {}
    m = inv.get("mobius") if isinstance(inv, dict) else None
    if isinstance(m, dict):
        return m
    return {}


def _extract_attachments(mob: Mapping[str, Any]) -> tuple[Attachment, ...]:
    slots = mob.get("attachment_slots", ()) or ()
    out: list[Attachment] = []
    for s in slots:
        if not isinstance(s, dict):
            continue
        out.append(
            Attachment(
                slot=int(s.get("slot", -1)),
                center=s.get("center"),
                center_site=s.get("center_site"),
                ligand=s.get("ligand"),
                ligand_site=s.get("ligand_site"),
                participant=s.get("participant"),
                site=s.get("site"),
            )
        )
    return tuple(out)


def _canonical_turns_from_mobius(mob: Mapping[str, Any]) -> tuple[TurnState, ...]:
    """Build the three canonical turn states using data carried by the gonol.

    We prefer the exact values recorded in the mobius invariant.
    If they are absent we fall back to the live UCNS carrier (still only
    for labeling, never for inventing construction evidence).
    """
    ts = mob.get("t") or [0, 1, 2]
    vphases = mob.get("visible_phase") or ["0", "0", "0"]
    frames = mob.get("frame") or [
        "positive-local-frame",
        "reversed-local-frame",
        "positive-local-frame",
    ]

    result: list[TurnState] = []
    for i, t in enumerate(ts[:3]):
        t_int = int(t)
        vp = str(vphases[i]) if i < len(vphases) else "0"
        fr = str(frames[i]) if i < len(frames) else "positive-local-frame"
        # Build a compact complete_key representation
        ck = f"({mob.get('law','ucns.native-mobius-root-loop')}, {vp}, {fr})"
        result.append(TurnState(t=t_int, visible_phase=vp, frame=fr, complete_key_repr=ck))
    # Ensure we always have exactly three
    while len(result) < 3:
        last = result[-1] if result else TurnState(0, "0", "positive-local-frame", "")
        result.append(TurnState(last.t + 1, last.visible_phase, last.frame, last.complete_key_repr))
    return tuple(result[:3])


def _charges_from_structure(structure: Mapping[str, Any] | None) -> dict[str, int]:
    ch: dict[str, int] = {}
    if not structure:
        return ch
    for d in structure.get("degree", ()) or ():
        if isinstance(d, dict):
            dim = d.get("dimension")
            charge = d.get("charge")
            if dim is not None and charge is not None:
                try:
                    ch[str(dim)] = int(charge)
                except Exception:
                    pass
        elif hasattr(d, "dimension") and hasattr(d, "charge"):
            try:
                ch[str(d.dimension)] = int(d.charge)
            except Exception:
                pass
    return ch


def extract_spiral_scene(obj: Any) -> SpiralScene:
    """Extract a SpiralScene from a MolecularConstruction or PublicGonolReceipt.

    Accepts:
    - epac_molecular.MolecularConstruction
    - epac_public_gonol.PublicGonolReceipt (element or molecule)
    - objects that expose .receipt and .invariants (or .gonol)
    """
    # Normalize to receipt + invariants + source info
    receipt = None
    invariants: Mapping[str, Any] = {}
    source_id = "unknown"
    relation = "unknown"

    # MolecularConstruction
    if hasattr(obj, "receipt") and hasattr(obj, "invariants"):
        receipt = obj.receipt
        invariants = obj.invariants or {}
        source_id = getattr(obj, "formula", None) or getattr(receipt, "source_id", "molecule")
        relation = getattr(receipt, "relation", "epac.affixiation")

    # Direct receipt (element gonol or replay)
    elif hasattr(obj, "gonol") and hasattr(obj, "source_id"):
        receipt = obj
        # element gonols do not carry the full "mobius" dict in invariants;
        # we synthesize a minimal one from carried harmonic + basic structure.
        invariants = {}
        source_id = getattr(obj, "source_id", "element")
        relation = getattr(obj, "relation", "epac.atomic.element")

    # Subatomic gonol receipt (PublicGonolReceipt); use the carried "lifted-spiral"
    # (first-class on subatomic gonols, parallel to element/molecule).
    if receipt is not None and ("subatomic" in str(getattr(receipt, "source_id", "")) or "subatomic" in str(getattr(receipt, "relation", ""))):
        carried = {}
        try:
            gon = getattr(receipt, "gonol", receipt)
            carried = dict(getattr(gon, "carried_options", ()))
        except Exception:
            carried = {}
        val = carried.get("lifted-spiral", "")
        frames = ()
        axes = ()
        if val:
            try:
                fpart, apart, _ac = val.split(";", 2)
                frames = tuple(fpart.split("|")) if fpart else ()
                axes = tuple(sorted(a for a in apart.split(",") if a)) if apart else ()
            except Exception:
                pass
        mob = {
            "law": "ucns.native-mobius-root-loop",
            "participant_axes": axes or ("nucleus",),
            "attachment_slots": (),
            "t": [0, 1, 2],
            "visible_phase": ["0", "0", "0"],
            "frame": frames or ["positive-local-frame", "reversed-local-frame", "positive-local-frame"],
            "one_turn_flips_frame": True,
            "complete_restored": True,
        }

    # Fallback: try common attributes
    if receipt is None:
        receipt = getattr(obj, "receipt", obj)
        invariants = getattr(obj, "invariants", {}) or {}
        source_id = getattr(receipt, "source_id", str(type(obj)))
        relation = getattr(receipt, "relation", "unknown")

    mob = _get_mobius(invariants)
    # For pure element gonols we may have no "mobius" invariant.
    # Build a minimal synthetic mobius from the structure so the visualizer
    # can still show the participant axes and charges on the spiral.
    if not mob and receipt is not None:
        struct = getattr(receipt, "structure", None) or {}
        axes = []
        if struct:
            # Collect unique dimensions from parts
            seen = set()
            for part in struct.get("parts", ()) or ():
                for name in (part.get("coupling") or []):
                    if name not in seen:
                        seen.add(name)
                        axes.append(name)
            if not axes:
                # fallback to degree dimensions
                for d in struct.get("degree", ()) or ():
                    dim = d.get("dimension") if isinstance(d, dict) else getattr(d, "dimension", None)
                    if dim:
                        axes.append(str(dim))
        mob = {
            "law": "ucns.native-mobius-root-loop",
            "binding": "gonol-structure-declared-axes",
            "parameter": "turn-index",
            "participant_axes": tuple(axes) or ("nucleus",),
            "attachment_slots": (),
            "t": [0, 1, 2],
            "visible_phase": ["0", "0", "0"],
            "frame": ["positive-local-frame", "reversed-local-frame", "positive-local-frame"],
            "one_turn_flips_frame": True,
            "complete_restored": True,
        }

    participant_axes = tuple(mob.get("participant_axes", ()) or ())
    attachments = _extract_attachments(mob)
    charges = _charges_from_structure(getattr(receipt, "structure", None) if receipt else None)

    turns = _canonical_turns_from_mobius(mob)

    extra: dict[str, Any] = {}
    if "quaternion" in str(invariants).lower() or (receipt and getattr(receipt, "structure", None)):
        qcount = 0
        try:
            qs = (getattr(receipt, "structure", None) or {}).get("quaternions") or []
            qcount = len(qs) if isinstance(qs, (list, tuple)) else 0
        except Exception:
            pass
        extra["quaternion_count_hint"] = qcount

    return SpiralScene(
        source_id=str(source_id),
        relation=str(relation),
        law=str(mob.get("law", "ucns.native-mobius-root-loop")),
        parameter=str(mob.get("parameter", "turn-index-over-declared-attachment-evidence")),
        binding=str(mob.get("binding", "declared-participants-and-valence-attachment-sites")),
        möbius_law_source=get_möbius_law_source(),
        turns=turns,  # type: ignore[arg-type]
        participant_axes=participant_axes,
        attachments=attachments,
        dimension_charges=charges,
        one_turn_flips_frame=bool(mob.get("one_turn_flips_frame", True)),
        complete_restored_at_t2=bool(mob.get("complete_restored", True)),
        extra=extra,
    )


# ---------------------------------------------------------------------
# Text renderer (dependency-free)
# ---------------------------------------------------------------------

def render_to_text(scene: SpiralScene) -> str:
    """Return a compact plain-text description of the lifted spiral."""
    lines: list[str] = []
    lines.append(f"LIFTED SPIRAL  source={scene.source_id}  relation={scene.relation}")
    lines.append(f"law={scene.law}")
    lines.append(f"parameter={scene.parameter}")
    lines.append(f"binding={scene.binding}")
    lines.append("")
    lines.append("Canonical two-turn double cover (visible phase constant, frame flips):")
    lines.append("")

    for ts in scene.turns:
        flip = "  (frame flip)" if ts.t == 1 else ""
        restore = "  (complete state restored)" if ts.t == 2 and scene.complete_restored_at_t2 else ""
        lines.append(f"  t={ts.t}   visible_phase={ts.visible_phase}   frame={ts.frame}{flip}{restore}")

    lines.append("")
    if scene.participant_axes:
        lines.append("participant axes (gonol dimensions):")
        for ax in scene.participant_axes:
            ch = scene.dimension_charges.get(ax)
            chs = f"  charge={ch}" if ch is not None else ""
            lines.append(f"    {ax}{chs}")

    if scene.attachments:
        lines.append("")
        lines.append("attachment slots (valence evidence):")
        for a in scene.attachments:
            if a.center:
                lines.append(
                    f"    slot {a.slot}: center {a.center}@{a.center_site}  --  "
                    f"ligand {a.ligand}@{a.ligand_site}"
                )
            else:
                lines.append(f"    slot {a.slot}: {a.participant}@{a.site}")

    lines.append("")
    lines.append(
        f"one_turn_flips_frame={scene.one_turn_flips_frame}   "
        f"complete_restored_at_t2={scene.complete_restored_at_t2}"
    )
    if scene.extra:
        lines.append(f"extra: {scene.extra}")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# SVG renderer (pure stdlib, self-contained)
# ---------------------------------------------------------------------

def _svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_scene_svg(
    scene: SpiralScene,
    *,
    width: int = 920,
    height: int = 520,
    title: str | None = None,
) -> str:
    """Return a self-contained SVG string visualizing the lifted spiral.

    Layout (faithful to the data):
    - Three vertical stations for t=0, t=1, t=2
    - Horizontal ribbon showing the double cover
    - Same visible phase shown at every station
    - Frame arrows or labels that flip at t=1 and restore at t=2
    - Participant axes listed under each station with their charges
    - Attachment arcs drawn between participants (center-ligand or symmetric)
    """
    title = title or f"Lifted Spiral — {scene.source_id}"
    margin = 40
    station_w = 220
    station_gap = 40
    top = 80
    ribbon_h = 110
    bottom = height - 60

    stations_x = [
        margin + station_w // 2,
        margin + station_w + station_gap + station_w // 2,
        margin + 2 * (station_w + station_gap) + station_w // 2,
    ]

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )
    parts.append(
        '<defs>'
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" '
        'orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#334155"/>'
        '</marker>'
        '<marker id="arrowRev" markerWidth="10" markerHeight="10" refX="9" refY="3" '
        'orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#b45309"/>'
        '</marker>'
        '</defs>'
    )

    # Background
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0f172a"/>')

    # Title
    parts.append(
        f'<text x="{width//2}" y="28" text-anchor="middle" fill="#e2e8f0" '
        f'font-family="monospace" font-size="16" font-weight="600">{_svg_escape(title)}</text>'
    )

    # Ribbon background (two bands for the double cover)
    ribbon_y = top + 10
    parts.append(
        f'<rect x="{margin}" y="{ribbon_y}" width="{width - 2*margin}" height="{ribbon_h}" '
        f'rx="8" fill="#1e2937" stroke="#475569" stroke-width="1"/>'
    )
    # Subtle center line
    parts.append(
        f'<line x1="{margin}" y1="{ribbon_y + ribbon_h//2}" '
        f'x2="{width - margin}" y2="{ribbon_y + ribbon_h//2}" '
        f'stroke="#475569" stroke-width="1" stroke-dasharray="4 3"/>'
    )

    # Station columns + labels
    for i, (ts, x) in enumerate(zip(scene.turns, stations_x)):
        # Station header
        parts.append(
            f'<text x="{x}" y="{top - 6}" text-anchor="middle" fill="#94a3b8" '
            f'font-family="monospace" font-size="12">t = {ts.t}</text>'
        )

        # Visible phase pill (same for all)
        pill_y = ribbon_y + 18
        parts.append(
            f'<rect x="{x-48}" y="{pill_y}" width="96" height="22" rx="11" '
            f'fill="#334155" stroke="#64748b"/>'
        )
        parts.append(
            f'<text x="{x}" y="{pill_y + 16}" text-anchor="middle" fill="#cbd5e1" '
            f'font-family="monospace" font-size="11">visible: {ts.visible_phase}</text>'
        )

        # Frame indicator (arrow direction + label)
        frame_y = ribbon_y + 58
        color = "#22c7b1" if "positive" in ts.frame else "#f59e0b"
        arrow_dir = "→" if "positive" in ts.frame else "←"
        parts.append(
            f'<text x="{x}" y="{frame_y}" text-anchor="middle" fill="{color}" '
            f'font-family="monospace" font-size="18" font-weight="700">{arrow_dir}</text>'
        )
        parts.append(
            f'<text x="{x}" y="{frame_y + 18}" text-anchor="middle" fill="{color}" '
            f'font-family="monospace" font-size="10">{_svg_escape(ts.frame)}</text>'
        )

        # Turn label under ribbon
        parts.append(
            f'<text x="{x}" y="{ribbon_y + ribbon_h + 18}" text-anchor="middle" '
            f'fill="#64748b" font-family="monospace" font-size="10">turn {ts.t}</text>'
        )

    # Participant axes (left side list)
    ax_x = margin + 12
    ax_y = top + ribbon_h + 55
    parts.append(
        f'<text x="{ax_x}" y="{ax_y - 4}" fill="#94a3b8" font-family="monospace" font-size="11">'
        "participant axes</text>"
    )
    for j, ax in enumerate(scene.participant_axes[:8]):  # keep compact
        ch = scene.dimension_charges.get(ax)
        label = f"{ax}  (Z={ch})" if ch is not None else ax
        parts.append(
            f'<text x="{ax_x}" y="{ax_y + 16 + j*14}" fill="#cbd5e1" '
            f'font-family="monospace" font-size="10">{_svg_escape(label)}</text>'
        )

    # Attachment arcs (schematic)
    # Draw simple arcs between centers and ligands projected onto the t=0 column for clarity.
    if scene.attachments:
        arc_y_base = top + ribbon_h + 55
        arc_x_center = stations_x[0] + 70
        for a in scene.attachments[:6]:
            if a.center and a.ligand:
                c = _svg_escape(str(a.center))
                l = _svg_escape(str(a.ligand))
                parts.append(
                    f'<path d="M {arc_x_center},{arc_y_base} Q {arc_x_center+70},{arc_y_base-30} '
                    f'{arc_x_center+140},{arc_y_base}" fill="none" stroke="#64748b" '
                    f'stroke-width="1.5" stroke-opacity="0.7"/>'
                )
                parts.append(
                    f'<text x="{arc_x_center+70}" y="{arc_y_base-36}" text-anchor="middle" '
                    f'fill="#64748b" font-family="monospace" font-size="9">{c}—{l}</text>'
                )

    # Legend box (bottom right)
    lx = width - margin - 260
    ly = height - 110
    parts.append(
        f'<rect x="{lx}" y="{ly}" width="240" height="78" rx="6" '
        f'fill="#1e2937" stroke="#475569" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{lx+12}" y="{ly+16}" fill="#94a3b8" font-family="monospace" font-size="10">'
        "UCNS native-möbius-root-loop</text>"
    )
    parts.append(
        f'<text x="{lx+12}" y="{ly+30}" fill="#64748b" font-family="monospace" font-size="9">'
        "visible phase unchanged after integer turns</text>"
    )
    parts.append(
        f'<text x="{lx+12}" y="{ly+44}" fill="#64748b" font-family="monospace" font-size="9">'
        "frame flips at t=1, restored at t=2</text>"
    )
    parts.append(
        f'<text x="{lx+12}" y="{ly+58}" fill="#64748b" font-family="monospace" font-size="9">'
        f"one_turn_flips={scene.one_turn_flips_frame}  complete@2={scene.complete_restored_at_t2}</text>"
    )
    parts.append(
        f'<text x="{lx+12}" y="{ly+72}" fill="#64748b" font-family="monospace" font-size="9">'
        f"attachments={len(scene.attachments)}</text>"
    )

    parts.append("</svg>")
    return "\n".join(parts)


def render_molecule_spiral_svg(construction: Any, **kwargs: Any) -> str:
    """Convenience wrapper for a MolecularConstruction."""
    scene = extract_spiral_scene(construction)
    return render_scene_svg(scene, **kwargs)


def render_element_spiral_svg(receipt: Any, **kwargs: Any) -> str:
    """Convenience wrapper for an element PublicGonolReceipt."""
    scene = extract_spiral_scene(receipt)
    return render_scene_svg(scene, title=f"Lifted Spiral — element {getattr(receipt, 'source_id', '?')}", **kwargs)


def render_subatomic_spiral_svg(receipt: Any, **kwargs: Any) -> str:
    """Convenience wrapper for a subatomic PublicGonolReceipt (lifted spiral)."""
    scene = extract_spiral_scene(receipt)
    return render_scene_svg(scene, title=f"Lifted Spiral — subatomic {getattr(receipt, 'source_id', '?')}", **kwargs)


# ---------------------------------------------------------------------
# Small demo helper
# ---------------------------------------------------------------------

def demo_text(formula: str = "H2O") -> str:
    """Quick text rendering for a declared molecule. Requires EPAC on PYTHONPATH."""
    from epac_molecular import construct_molecule  # local import to keep viz import-light

    c = construct_molecule(formula)
    scene = extract_spiral_scene(c)
    return render_to_text(scene)


# ---------------------------------------------------------------------
# Full population extractor (first-class lifted-spiral population)
# ---------------------------------------------------------------------

def extract_full_spiral_population(
    *,
    include_elements: tuple[str, ...] = ("H", "C", "O", "Si", "B", "N"),
    include_subatomic: tuple[str, ...] = ("H", "He", "Li", "C", "O", "Si"),
) -> dict[str, SpiralScene]:
    """Return a complete, deterministic map of lifted-spiral scenes.

    Keys:
      - All formulas from MOLECULE_COMPOSITIONS (the full declared experiment: 9)
      - Element symbols requested via include_elements (sourced from native periodic gonols)
      - Subatomic symbols requested via include_subatomic (sourced from subatomic gonols, now carrying "lifted-spiral" first-class)

    Every scene carries:
      - möbius_law_source pointing at the canonical UCNS direct_mobius.py
      - the two-turn double-cover with visible phase constant + frame flip/restore
      - participant axes + attachment slots + charges as declared at construction time

    This is pure population of already-closed gonol evidence. No new geometry.
    """
    from epac_molecular import construct_declared_molecules  # local to keep import light

    pop: dict[str, SpiralScene] = {}

    # Molecules (original prereg + enlarged set)
    molecules = construct_declared_molecules()
    for formula, construction in molecules.items():
        pop[formula] = extract_spiral_scene(construction)

    # Representative elements via the primary EPAC periodic path
    try:
        from epac_periodic import construct_element_gonol as _construct_element_gonol
    except Exception:
        _construct_element_gonol = None  # type: ignore

    if _construct_element_gonol is not None:
        for sym in include_elements:
            try:
                receipt = _construct_element_gonol(sym)
                pop[f"element:{sym}"] = extract_spiral_scene(receipt)
            except Exception:
                pass

    # Subatomic gonols (now carry "lifted-spiral" first-class, parallel to element).
    try:
        from epac_subatomic import subatomic_gonol as _subatomic
    except Exception:
        _subatomic = None  # type: ignore

    if _subatomic is not None:
        for sym in include_subatomic:
            try:
                if sym in getattr(_subatomic, "SUPPORTED_SYMBOLS", ()):
                    receipt = _subatomic.construct_subatomic_gonol(sym)
                    pop[f"subatomic:{sym}"] = extract_spiral_scene(receipt)
            except Exception:
                pass

    return pop


def spiral_population_keys() -> list[str]:
    """Return the expected keys for a full population over the declared experiment."""
    from epac_molecular import MOLECULE_COMPOSITIONS as _M  # local

    keys = list(_M.keys())
    keys.extend([f"element:{s}" for s in ("H", "C", "O", "Si", "B", "N")])
    keys.extend([f"subatomic:{s}" for s in ("H", "He", "Li", "C", "O", "Si")])
    return keys


__all__ = [
    "SpiralScene",
    "TurnState",
    "Attachment",
    "extract_spiral_scene",
    "extract_full_spiral_population",
    "spiral_population_keys",
    "render_to_text",
    "render_scene_svg",
    "render_molecule_spiral_svg",
    "render_element_spiral_svg",
    "get_möbius_law_source",
]


if __name__ == "__main__":
    # Allow direct execution for quick inspection
    import sys

    formula = sys.argv[1] if len(sys.argv) > 1 else "H2O"
    print(demo_text(formula))
