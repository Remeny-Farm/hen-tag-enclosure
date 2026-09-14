# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""2D sketch -> SVG helpers: the app's live preview and the proof image are
drawn from the same sketches the printer gets.

    uv run --python 3.12 cap_svg.py            # writes out/layout.json

layout.json (hen-cap-layout/1) carries every radius the preview needs, the
outlines of the digits 0-9 at the fixed number size (bbox-centred, y up,
millimetres) with their advance, and every icon and pattern as an SVG path.
The app bends the digits along the bottom arc itself, so no font has to be
installed on any device and the preview matches the print.
"""

import json
import math
import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).parent))
import cap_marking as cm  # noqa: E402
from cap_design import load_catalog  # noqa: E402
from hen_tag_enclosure import P  # noqa: E402

LAYOUT_SCHEMA = "hen-cap-layout/1"


SEG_LEN = 0.2   # mm per polyline segment on curved edges


def _wire_path(wire: bd.Wire) -> str:
    pts = []
    for e in wire.edges():
        # Curves are sampled by length so a full circle stays round and a
        # tiny glyph bezier is not over-sampled; lines need one point.
        n = 1 if e.geom_type == bd.GeomType.LINE else min(256, max(4, math.ceil(e.length / SEG_LEN)))
        for i in range(n):
            v = e.position_at(i / n)
            pts.append(f"{v.X:.3f} {v.Y:.3f}")
    return "M " + " L ".join(pts) + " Z"


def sketch_to_path(sk: bd.Sketch) -> str:
    """One SVG path string: outer wires and holes as closed subpaths, meant
    for fill-rule evenodd."""
    parts = []
    for f in sk.faces():
        parts.append(_wire_path(f.outer_wire()))
        for w in f.inner_wires():
            parts.append(_wire_path(w))
    return " ".join(parts)


def digit_outlines() -> dict[str, dict]:
    out = {}
    for d in "0123456789":
        one = bd.Text(d, font_size=cm.NUM_FONT, font_path=cm._font(),
                      align=(bd.Align.CENTER, bd.Align.CENTER))
        left = bd.Text(d, font_size=cm.NUM_FONT, font_path=cm._font(),
                       align=(bd.Align.MIN, bd.Align.MIN))
        two = bd.Text(d + d, font_size=cm.NUM_FONT, font_path=cm._font(),
                      align=(bd.Align.MIN, bd.Align.MIN))
        adv = two.bounding_box().size.X - left.bounding_box().size.X
        out[d] = {"d": sketch_to_path(one), "advance": round(adv, 3)}
    return out


def write_layout(path: Path) -> dict:
    cat = load_catalog()
    layout = {
        "schema": LAYOUT_SCHEMA,
        "generator_version": cat["generator_version"],
        "cap_r": round(P.r_cap_out, 3),
        "scallops": {"n": 8, "r": 1.4, "orbit": round(P.r_cap_out + 1.15, 3)},
        "core_r": cm.CORE_R_OUT,
        "band": {"r_min": cm.BAND_R_MIN, "r_max": cm.BAND_R_MAX},
        "band_window": list(cm.BAND_WINDOW),
        "number": {"font_pt": cm.NUM_FONT, "centre_deg": 270.0,
                   "base_r": round((cm.BAND_R_MIN + cm.BAND_R_MAX) / 2, 3),
                   "stroke": round(2 * cm.GLYPH_FATTEN, 3),
                   "digits": digit_outlines()},
        "icons": {k: sketch_to_path(f()) for k, f in cm.ICONS.items() if f is not None},
        "centre_patterns": {k: sketch_to_path(f()) for k, f in cm.PATTERNS_CENTRE.items()},
        "band_patterns": {k: sketch_to_path(f()) for k, f in cm.PATTERNS_BAND.items()},
    }
    layout["number"]["advance"] = max(v["advance"] for v in layout["number"]["digits"].values())
    path.write_text(json.dumps(layout, indent=1, sort_keys=True) + "\n")
    return layout


def write_proof(path: Path, mk: bd.Sketch, core: bd.Sketch, scheme: dict) -> None:
    """Top view of one cap in its scheme's filament colours, from the exact
    2D sketches: the authoritative preview a patron sees after the batch."""
    r = P.r_cap_out + 0.5
    text_hex, accent_hex = scheme["text"]["hex"], scheme["accent"]["hex"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-r} {-r} {2 * r} {2 * r}" '
           f'width="256" height="256"><g transform="scale(1,-1)">'
           f'<circle r="{P.r_cap_out:.2f}" fill="#e9eef2" stroke="#b7c0c8" stroke-width="0.2"/>'
           f'<path d="{sketch_to_path(core)}" fill="{accent_hex}" fill-rule="evenodd"/>'
           f'<path d="{sketch_to_path(mk)}" fill="{text_hex}" fill-rule="evenodd"/>'
           f'</g></svg>\n')
    path.write_text(svg)


if __name__ == "__main__":
    out = write_layout(cm.OUT / "layout.json")
    print(f"wrote layout.json: {len(out['number']['digits'])} digits, "
          f"{len(out['icons'])} icons, advance {out['number']['advance']}")
