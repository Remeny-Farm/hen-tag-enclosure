"""Holyiot 25008 board geometry, taken from the manufacturer's STEP model.

Source: HOLYIOT-25008-V1.0.step (Open CASCADE export of the ECAD board,
dated 2025-07-07), sha256 c421a624...a75e, received and measured 2026-09-23.
The file itself is not committed -- it is the manufacturer's -- only the
numbers the enclosure depends on. `verify.py --board-step PATH` re-extracts
them from the file and fails if any drifted, then collides the real board
with the body and cap.

What is trusted and what is not:
  TRUSTED    the board outline and thickness, and every SMD part: position,
             footprint and height. That is the ECAD placement.
  DISCARDED  the "Free-Models" battery clip (spr_1). It is a generic model:
             its plate leaves 2.39 mm under the board, where a 3.2 mm CR2032
             cannot go; its outline would overrun the Rev A pocket that
             demonstrably fitted; its solder tabs miss the board's holes. The
             holder stays on the caliper numbers in Params.

Frame: the enclosure's. STEP board-relative coordinates are turned -90 deg so
the holder's tangent point (+Y in the STEP) lands on +X, where Params puts the
pocket offset. No mirror: the STEP already has components up and the holder
underneath, the way the board sits in the body. Radii are from the board
centre; angles from +X, counter-clockwise, viewed from the cap.
"""

import math
from pathlib import Path

STEP_SHA256 = "c421a62434d4f43e3f00cef6f1ebd7f0c10a48d75013abbaed9ac5e26547a75e"

PCB_DIA = 25.00
PCB_T = 0.81            # bare board; the caliper's 2.0 was board + parts

# Tallest part on the face: the tactile switch S1, dead centre.
S1_R_MAX = 2.26         # outermost corner radius
S1_H = 1.60             # above the board face

# LED1, 1.6 x 1.5 x 0.34 package.
LED_R = 9.84            # centre radius (caliper said 10.0)
LED_R_SPAN = (8.78, 10.91)   # radial extent of the package
LED_ANGLE = -59.8       # the board is keyed by the holder pocket, so fixed
LED_HALF = 0.80         # package half-size, the extent the tolerance chain uses

PART_R_MAX = 11.77      # outermost component corner (U2)

# Tallest part per annulus (r_in, r_out, height), for foam contact. S1 is the
# only part above 1.10; the inboard foam ring (r 6-8) sits on Q1 at worst.
PART_H_BY_BAND = (
    (0.0, 2.3, 1.60),   # S1
    (2.3, 6.0, 1.10),   # Q1, U1, Y1, the C/L/R field
    (6.0, 8.0, 1.10),   # Q1 reaches r 7.28; U1 0.65, C 0.50
    (8.0, 12.5, 0.95),  # U2 0.95, Y2 0.81, LED 0.34, C 0.50
)

# Mass: board volume at FR4 density plus the parts' summed volume at an
# assumed ~2.5 g/cm3 average (ceramic, silicon, mould compound). ESTIMATED.
PCB_MASS = 0.73
PARTS_MASS = 0.18

# Label of the model the STEP ships with the holder in; everything else is
# the board and its parts.
_CLIP_LABEL = "Free-Models"


def _board_centre(board):
    c = board.bounding_box().center()
    return c.X, c.Y


def load(step_path: str | Path, z_pcb_bottom: float):
    """The board and its SMD parts from the STEP, placed in the enclosure frame
    with the board's underside at z_pcb_bottom. The battery clip is left out."""
    import build123d as bd

    shape = bd.import_step(str(step_path))
    parts = {c.label: c for c in shape.children}
    board = parts["Board"]
    cx, cy = _board_centre(board)
    top = board.bounding_box().max.Z
    move = (bd.Pos(0, 0, z_pcb_bottom + PCB_T) * bd.Rot(0, 0, -90)
            * bd.Pos(-cx, -cy, -top))
    placed = [move * s for label, c in parts.items() if label != _CLIP_LABEL
              for s in c.solids()]
    return bd.Compound(placed), {k: v for k, v in parts.items() if k != _CLIP_LABEL}


def extract(step_path: str | Path) -> dict[str, float]:
    """Re-measure the constants above from the STEP, board-relative, enclosure frame."""
    import build123d as bd

    shape = bd.import_step(str(step_path))
    parts = {c.label: c for c in shape.children}
    board = parts.pop("Board")
    parts.pop(_CLIP_LABEL, None)
    cx, cy = _board_centre(board)
    bb = board.bounding_box()
    top = bb.max.Z

    def enc(x: float, y: float) -> tuple[float, float]:
        return y - cy, -(x - cx)          # -90 deg about the board centre

    def radii(b) -> tuple[float, float]:
        pts = [enc(x, y) for x in (b.min.X, b.max.X) for y in (b.min.Y, b.max.Y)]
        rs = [math.hypot(*q) for q in pts]
        spans_centre = (min(q[0] for q in pts) < 0 < max(q[0] for q in pts)
                        and min(q[1] for q in pts) < 0 < max(q[1] for q in pts))
        return (0.0 if spans_centre else min(rs)), max(rs)

    s1, led = parts["S1"].bounding_box(), parts["LED1"].bounding_box()
    lx, ly = enc(led.center().X, led.center().Y)
    return {
        "PCB_DIA": max(bb.size.X, bb.size.Y),
        "PCB_T": bb.size.Z,
        "S1_R_MAX": radii(s1)[1],
        "S1_H": s1.max.Z - top,
        "LED_R": math.hypot(lx, ly),
        "LED_ANGLE": math.degrees(math.atan2(ly, lx)),
        "PART_R_MAX": max(radii(c.bounding_box())[1] for c in parts.values()),
    }
