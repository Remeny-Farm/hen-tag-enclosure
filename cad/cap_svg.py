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
import cap_motifs as motifs  # noqa: E402
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
        # The clear LED window of a base-coloured shell (spec §3, palettes
        # 2026-09-14); the number band overlaps it, which is intended.
        "window": {"r_min": cm.LED_RING[0], "r_max": cm.LED_RING[1]},
        # The barcode band is generated per serial on both sides; this
        # sample lets the app's test prove its generator matches (bars as
        # [start_deg, width_deg]).
        "barcode_sample": {"serial": 67, "bars": [list(b) for b in motifs.barcode_bars(67)]},
        "number": {"font_pt": cm.NUM_FONT, "centre_deg": 270.0,
                   "base_r": round((cm.BAND_R_MIN + cm.BAND_R_MAX) / 2, 3),
                   "stroke": round(2 * cm.GLYPH_FATTEN, 3),
                   "digits": digit_outlines()},
        "icons": {k: sketch_to_path(f()) for k, f in cm.ICONS.items() if f is not None},
        "centre_patterns": {k: sketch_to_path(f()) for k, f in cm.PATTERNS_CENTRE.items()},
        # band paths for serial 0; the barcode is per serial and drawn by the app
        "band_patterns": {k: sketch_to_path(f(0)) for k, f in cm.PATTERNS_BAND.items() if k != "barcode"},
    }
    layout["number"]["advance"] = max(v["advance"] for v in layout["number"]["digits"].values())
    path.write_text(json.dumps(layout, indent=1, sort_keys=True) + "\n")
    return layout


def write_proof(path: Path, sketches: dict, scheme: dict, colours: dict) -> None:
    """Top view of one cap in its scheme's filament colours, from the exact
    2D sketches and the design's zone colours: the authoritative preview a
    patron sees after the batch."""
    r = P.r_cap_out + 0.5
    hex_of = {"base": scheme["base"]["hex"], "a": scheme["a"]["hex"], "b": scheme["b"]["hex"],
              "clear": "#E6EDF1"}   # glass: the clear filament's display tint
    lo, hi = cm.LED_RING
    ring = f"M {r:.2f} 0 A {r:.2f} {r:.2f} 0 1 0 {-r:.2f} 0 A {r:.2f} {r:.2f} 0 1 0 {r:.2f} 0 Z"
    def circ(rr): return f"M {rr} 0 A {rr} {rr} 0 1 0 {-rr} 0 A {rr} {rr} 0 1 0 {rr} 0 Z"
    layers = [
        f'<circle r="{P.r_cap_out:.2f}" fill="{hex_of[colours["ring"]]}" stroke="#b7c0c8" stroke-width="0.2"/>',
        f'<path d="{circ(hi)} {circ(lo)}" fill="#1f2830" fill-rule="evenodd" opacity="0.85"/>',
        f'<path d="{circ(cm.CORE_R_OUT)}" fill="{hex_of[colours["disc"]]}"/>',
    ]
    for key, zone in (("band", "band"), ("centre", "centre"), ("marking", "number")):
        sk = sketches.get(key)
        if sk is not None:
            layers.append(f'<path d="{sketch_to_path(sk)}" fill="{hex_of[colours[zone]]}" fill-rule="evenodd"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-r} {-r} {2 * r} {2 * r}" '
           f'width="256" height="256"><g transform="scale(1,-1)">' + "".join(layers) + '</g></svg>\n')
    path.write_text(svg)


if __name__ == "__main__":
    out = write_layout(cm.OUT / "layout.json")
    print(f"wrote layout.json: {len(out['number']['digits'])} digits, "
          f"{len(out['icons'])} icons, advance {out['number']['advance']}")
