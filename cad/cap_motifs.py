# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Every icon and pattern a patron may put on a cap, as parametric 2D sketches.

Physical envelope (cap_marking.py enforces it on every generated cap):
  centre elements  inside r <= CORE_PATTERN_R_MAX (7.4 mm), the accent disc
  band elements    r 12.2-14.8 inside BAND_WINDOW (-10..190 deg), the top arc
  every island     survives a 0.4 mm erosion (feature >= 0.8 mm) and no two
                   islands merge under a 0.4 mm dilation (gap >= 0.8 mm)

No fonts, no emoji: every shape is built from circles, ellipses, polygons and
rectangles, so every machine renders the same outline. Band patterns take the
hen's serial so a pattern can be unique per hen (barcode); the others ignore
it. catalog.json lists the same ids with their packs and prices;
test_cap_marking.py keeps the two in step and check_motifs.py runs the
printability checks on the whole library.
"""

import math
import random

import build123d as bd

CORE_PATTERN_R_MAX = 7.4     # keeps >= 1.1 mm of accent disc outside (disc r 8.5)
BAND_PATTERN_R = (12.0, 14.9)
BAND_WINDOW = (-10.0, 190.0)  # deg; clear of a 5-digit number by > 40 deg each side
PATTERN_FEATURE_MIN = 0.8
PATTERN_GAP_MIN = 0.8
# The feature test erodes by a little less than half the minimum so a
# compliant 0.8-0.9 mm island keeps a measurable core (a 0.9 mm dot leaves
# r 0.1, area 0.03 mm2) while boolean slivers stay far below the cutoff.
PATTERN_ERODE = 0.35
SLIVER_AREA = 5e-3

HEART_W = 10.0
STAR_R = 6.9
FLOWER_R = 6.4


# --- helpers ----------------------------------------------------------------
def _at(x: float, y: float, shape) -> bd.Sketch:
    return bd.Pos(x, y) * shape


def _polar(r: float, deg: float) -> tuple[float, float]:
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))


def _bar(x0: float, y0: float, x1: float, y1: float, w: float) -> bd.Sketch:
    """A straight stroke of width w from (x0, y0) to (x1, y1), square ends."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    return (bd.Pos((x0 + x1) / 2, (y0 + y1) / 2) * bd.Rot(0, 0, math.degrees(math.atan2(dy, dx)))
            * bd.Rectangle(L, w))


def _polyline(pts, w: float) -> bd.Sketch:
    """Bars through the points with round joints, so the outline never
    pinches at a vertex."""
    out = bd.Sketch()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out = out + _bar(x0, y0, x1, y1, w)
    for x, y in pts[1:-1]:
        out = out + _at(x, y, bd.Circle(w / 2))
    return out


def _annular_sector(r_in: float, r_out: float, a0: float, a1: float) -> bd.Sketch:
    n = max(2, int((a1 - a0) / 5) + 1)
    pts = [(0.0, 0.0)] + [
        ((r_out + 2) * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         (r_out + 2) * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
        for i in range(n + 1)]
    return (bd.Circle(r_out) - bd.Circle(r_in)) & bd.Polygon(*pts, align=None)


def _star(r_out: float, r_in: float, n: int, phase: float = 90.0) -> bd.Sketch:
    pts = []
    for k in range(n):
        pts.append(_polar(r_out, phase + 360 * k / n))
        pts.append(_polar(r_in, phase + 360 * (k + 0.5) / n))
    return bd.Sketch() + bd.Polygon(*pts, align=None)


def _union(parts) -> bd.Sketch:
    out = bd.Sketch()
    for p in parts:
        out = out + p
    return out


# --- free icons -------------------------------------------------------------
def heart_sketch(width: float = HEART_W) -> bd.Sketch:
    """Parametric heart: two lobes on a 45-deg square."""
    s = width / (2 ** 0.5)
    body = bd.Rot(0, 0, 45) * bd.Rectangle(s, s)
    o = s / (2 * 2 ** 0.5)
    return body + bd.Pos(-o, o) * bd.Circle(s / 2) + bd.Pos(o, o) * bd.Circle(s / 2)


def star_sketch(r_out: float = STAR_R) -> bd.Sketch:
    """Five-point star; the dilation in the inlay pipeline rounds the tips."""
    return _star(r_out, r_out * 0.5, 5)


def flower_sketch(r: float = FLOWER_R) -> bd.Sketch:
    """Six-petal daisy: petals overlap the centre disc so it prints as one shape."""
    petal_r = r * 0.40
    orbit = r - petal_r
    out = bd.Circle(r * 0.40)
    for k in range(6):
        out = out + _at(*_polar(orbit, 60 * k), bd.Circle(petal_r))
    return out


def egg_sketch(h: float = 12.0) -> bd.Sketch:
    return bd.Sketch() + bd.Ellipse(h / 2 / 1.3, h / 2)


def sun_sketch(r: float = 6.9) -> bd.Sketch:
    out = bd.Circle(r * 0.5)
    for k in range(8):
        out = out + bd.Rot(0, 0, 45 * k) * bd.Pos(r * 0.62, 0) * bd.Rectangle(r * 0.76, 1.1)
    return out


def moon_sketch(r: float = 6.6) -> bd.Sketch:
    return bd.Circle(r) - bd.Pos(r * 0.45, 0) * bd.Circle(r * 0.82)


# --- "vibe" icons -----------------------------------------------------------
def sparkles_sketch() -> bd.Sketch:
    big = _at(-1.4, -0.6, _star(4.6, 1.5, 4))
    return big + _at(3.8, 3.6, _star(2.4, 0.85, 4)) + _at(4.2, -3.8, _star(1.9, 0.7, 4))


def bolt_sketch() -> bd.Sketch:
    pts = [(-1.1, 6.6), (-3.9, 0.4), (-0.8, 0.4), (-2.4, -6.6), (3.9, 1.1), (0.8, 1.1), (2.1, 6.6)]
    return bd.Sketch() + bd.Polygon(*pts, align=None)


def smiley_sketch() -> bd.Sketch:
    face = bd.Circle(6.8) - _at(-2.4, 2.0, bd.Circle(1.05)) - _at(2.4, 2.0, bd.Circle(1.05))
    return face - _annular_sector(3.0, 4.1, 205, 335)


def cherry_sketch() -> bd.Sketch:
    left, right = (-2.9, -3.6), (2.9, -2.8)
    top = (0.6, 6.4)
    out = _at(*left, bd.Circle(2.7)) + _at(*right, bd.Circle(2.7))
    out = out + _bar(left[0], left[1] + 1.5, top[0], top[1], 1.0) + _bar(right[0], right[1] + 1.5, top[0], top[1], 1.0)
    return out + _at(1.2, 5.6, bd.Rot(0, 0, 20) * bd.Ellipse(2.2, 1.0))


def butterfly_sketch() -> bd.Sketch:
    parts = [_at(-3.1, 1.9, bd.Rot(0, 0, 25) * bd.Ellipse(3.2, 2.3)),
             _at(3.1, 1.9, bd.Rot(0, 0, -25) * bd.Ellipse(3.2, 2.3)),
             _at(-2.4, -2.6, bd.Rot(0, 0, -20) * bd.Ellipse(2.4, 1.8)),
             _at(2.4, -2.6, bd.Rot(0, 0, 20) * bd.Ellipse(2.4, 1.8)),
             bd.Rectangle(1.1, 8.0)]
    return _union(parts)


def mushroom_sketch() -> bd.Sketch:
    cap = (bd.Circle(6.4) & _at(0, 3.5, bd.Rectangle(14, 7))) + _at(0, 0.2, bd.Rectangle(12.8, 1.4))
    cap = cap - _at(-2.6, 2.6, bd.Circle(0.95)) - _at(2.2, 4.2, bd.Circle(0.75)) - _at(3.9, 1.6, bd.Circle(0.6))
    stem = _at(0, -3.2, bd.Rectangle(3.6, 6.0))
    return cap + stem


def clover_sketch() -> bd.Sketch:
    out = bd.Sketch()
    for k in range(4):
        out = out + _at(*_polar(2.7, 45 + 90 * k), bd.Circle(2.5))
    return out + _bar(0.4, -0.4, 2.6, -6.6, 1.0)


def rainbow_sketch() -> bd.Sketch:
    out = bd.Sketch()
    for r_in in (2.4, 4.2, 6.0):
        out = out + _annular_sector(r_in, r_in + 1.0, 0, 180)
    return bd.Pos(0, -2.2) * out


def ghost_sketch() -> bd.Sketch:
    body = _at(0, 1.6, bd.Circle(4.6)) + _at(0, -1.8, bd.Rectangle(9.2, 6.8))
    for x in (-3.1, 0.0, 3.1):
        body = body - _at(x, -5.2, bd.Circle(1.4))
    return body - _at(-1.7, 2.2, bd.Circle(0.95)) - _at(1.7, 2.2, bd.Circle(0.95))


def saturn_sketch() -> bd.Sketch:
    ring = bd.Rot(0, 0, -22) * (bd.Ellipse(7.2, 2.3) - bd.Ellipse(5.6, 1.35))
    return bd.Circle(3.9) + ring


# --- "drop" icons -----------------------------------------------------------
def skull_sketch() -> bd.Sketch:
    head = _at(0, 1.2, bd.Circle(5.2)) + _at(0, -3.0, bd.Rectangle(6.4, 4.4))
    head = head - _at(-2.0, 1.7, bd.Circle(1.55)) - _at(2.0, 1.7, bd.Circle(1.55))
    head = head - bd.Polygon((0, -0.2), (-0.9, -1.8), (0.9, -1.8), align=None)
    for x in (-1.15, 1.15):
        head = head - _at(x, -4.6, bd.Rectangle(0.85, 1.6))
    return head


def alien_sketch() -> bd.Sketch:
    head = _at(0, 0.4, bd.Ellipse(5.0, 6.8))
    head = head - _at(-1.9, 0.8, bd.Rot(0, 0, 35) * bd.Ellipse(1.25, 2.3))
    return head - _at(1.9, 0.8, bd.Rot(0, 0, -35) * bd.Ellipse(1.25, 2.3))


def diamond_sketch() -> bd.Sketch:
    gem = bd.Sketch() + bd.Polygon((-6.6, 1.6), (-3.4, 5.4), (3.4, 5.4), (6.6, 1.6), (0, -6.6), align=None)
    gem = gem - _at(0, 1.6, bd.Rectangle(13.4, 0.85))
    return gem - _bar(-3.4, 1.6, 0, -6.6, 0.85) - _bar(3.4, 1.6, 0, -6.6, 0.85)


def crown_sketch() -> bd.Sketch:
    pts = [(-5.6, -4.4), (5.6, -4.4), (5.6, -1.0), (3.8, 4.9), (1.85, 0.4), (0, 6.0),
           (-1.85, 0.4), (-3.8, 4.9), (-5.6, -1.0)]
    return bd.Sketch() + bd.Polygon(*pts, align=None)


def yinyang_sketch() -> bd.Sketch:
    r = 6.8
    right = bd.Circle(r) & _at(r / 2, 0, bd.Rectangle(r, 2 * r))
    out = right + _at(0, r / 2, bd.Circle(r / 2)) - _at(0, -r / 2, bd.Circle(r / 2))
    return out + _at(0, -r / 2, bd.Circle(1.1)) - _at(0, r / 2, bd.Circle(1.1))


def peace_sketch() -> bd.Sketch:
    out = bd.Circle(6.8) - bd.Circle(5.7)
    out = out + bd.Rectangle(1.1, 13.6)
    return out + _bar(0, 0, *_polar(6.2, 225), 1.1) + _bar(0, 0, *_polar(6.2, 315), 1.1)


def _teardrop(cx: float, cy: float, r: float, tip_y: float) -> bd.Sketch:
    """One polygon: the tip, then the round bottom between the two tangent
    points -- a single face, unlike a circle fused with a triangle."""
    d = tip_y - cy
    theta = math.degrees(math.acos(r / d))
    pts = [(0.0, tip_y)]
    a = 90 - theta
    while a >= -(270 - (90 - theta)) - 1e-9:
        pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
        a -= 6
    return bd.Sketch() + bd.Polygon(*pts, align=None)


def drop_sketch() -> bd.Sketch:
    """Water drop with a hollow core; walls >= 2 mm everywhere."""
    return _teardrop(0, -2.4, 3.9, 6.8) - _teardrop(0, -2.6, 1.5, 1.6)


def broken_heart_sketch() -> bd.Sketch:
    heart = heart_sketch()
    pts = [(0.5, 7.5), (-1.0, 3.2), (1.0, 0.0), (-0.8, -3.4), (0.4, -8.0)]
    return heart - _polyline(pts, 1.0)


def eye_sketch() -> bd.Sketch:
    almond = _at(0, -4.0, bd.Circle(8.0)) & _at(0, 4.0, bd.Circle(8.0))
    return almond - bd.Circle(2.5) + bd.Circle(1.25)


def paw_sketch() -> bd.Sketch:
    pad = _at(0, -2.4, bd.Ellipse(4.2, 3.3))
    toes = [(-4.9, 1.5), (-1.75, 3.6), (1.75, 3.6), (4.9, 1.5)]
    return _union([pad] + [_at(x, y, bd.Circle(1.25)) for x, y in toes])


# --- centre patterns --------------------------------------------------------
def rings_sketch() -> bd.Sketch:
    out = bd.Sketch()
    for r_in in (1.6, 4.0, 6.4):
        out = out + (bd.Circle(r_in + 0.9) - bd.Circle(r_in))
    return out


def solid_sketch() -> bd.Sketch:
    return bd.Sketch() + bd.Circle(7.3)


def centre_dots_sketch() -> bd.Sketch:
    out = bd.Circle(1.0)
    for k in range(8):
        out = out + _at(*_polar(5.2, 45 * k), bd.Circle(0.9))
    return out


# --- band patterns: f(serial) -> sketch ------------------------------------
def _band_bars(angles, r_in, r_out, w):
    out = bd.Sketch()
    for a in angles:
        out = out + bd.Rot(0, 0, a) * bd.Pos((r_in + r_out) / 2, 0) * bd.Rectangle(r_out - r_in, w)
    return out


def stripes_sketch(serial: int = 0) -> bd.Sketch:
    return _band_bars(range(-6, 187, 12), 12.2, 14.8, 0.9)


def band_dots_sketch(serial: int = 0) -> bd.Sketch:
    out = bd.Sketch()
    for a in range(-5, 186, 10):
        out = out + _at(*_polar(13.5, a), bd.Circle(0.6))
    return out


def arc_sketch(serial: int = 0) -> bd.Sketch:
    return _annular_sector(13.05, 13.95, BAND_WINDOW[0], BAND_WINDOW[1])


def _two_rows(mask_row1, mask_row2, step_deg: float = 8.0) -> bd.Sketch:
    """Two rows of 0.9 mm squares (r 12.2-13.1 and 13.9-14.8, 0.8 mm apart)
    switched on by two bit masks that repeat along the window."""
    out = bd.Sketch()
    a0, a1 = BAND_WINDOW
    n = int((a1 - a0) / step_deg)
    for i in range(n + 1):
        a = a0 + 4 + step_deg * i
        if a > a1 - 4:
            break
        if mask_row1[i % len(mask_row1)]:
            out = out + bd.Rot(0, 0, a) * bd.Pos(12.65, 0) * bd.Rectangle(0.9, 0.9)
        if mask_row2[i % len(mask_row2)]:
            out = out + bd.Rot(0, 0, a) * bd.Pos(14.35, 0) * bd.Rectangle(0.9, 0.9)
    return out


def checker_sketch(serial: int = 0) -> bd.Sketch:
    return _two_rows((1, 0), (0, 1))


def pixel_sketch(serial: int = 0) -> bd.Sketch:
    return _two_rows((1, 1, 0, 1, 0, 0, 1, 0), (0, 1, 1, 0, 1, 0, 0, 1))


def zigzag_sketch(serial: int = 0) -> bd.Sketch:
    out = bd.Sketch()
    a0, a1 = BAND_WINDOW
    pts = []
    a = a0 + 3
    up = True
    while a <= a1 - 3:
        pts.append(_polar(14.2 if up else 12.8, a))
        up = not up
        a += 10
    return _polyline(pts, 0.9)


def wave_sketch(serial: int = 0) -> bd.Sketch:
    out = bd.Sketch()
    a0, a1 = BAND_WINDOW
    pts = [_polar(13.5 + 0.8 * math.sin(math.radians(a * 9)), a) for a in range(int(a0) + 3, int(a1) - 2, 4)]
    return _polyline(pts, 0.9)


def dashes_sketch(serial: int = 0) -> bd.Sketch:
    """Loading-bar segments: 12 deg on, 4 deg off."""
    out = bd.Sketch()
    a = BAND_WINDOW[0] + 2
    while a + 12 <= BAND_WINDOW[1] - 2:
        out = out + _annular_sector(12.8, 14.2, a, a + 12)
        a += 16
    return out


def double_arc_sketch(serial: int = 0) -> bd.Sketch:
    a0, a1 = BAND_WINDOW
    return _annular_sector(12.0, 12.95, a0, a1) + _annular_sector(13.95, 14.9, a0, a1)


def tally_sketch(serial: int = 0) -> bd.Sketch:
    """Groups of four strokes struck through by a fifth."""
    out = bd.Sketch()
    a0, a1 = BAND_WINDOW
    group_span = 4 * 5.0
    a = a0 + 6
    while a + group_span <= a1 - 6:
        for k in range(4):
            out = out + _band_bars([a + 5.0 * k], 12.3, 14.7, 1.0)
        out = out + _annular_sector(13.0, 14.0, a - 2.5, a + group_span - 2.5)
        a += group_span + 14
    return out


def growing_dots_sketch(serial: int = 0) -> bd.Sketch:
    out = bd.Sketch()
    n = 15
    a0, a1 = BAND_WINDOW
    for i in range(n):
        a = a0 + 8 + (a1 - a0 - 16) * i / (n - 1)
        r_dot = 0.45 + 0.6 * i / (n - 1)
        out = out + _at(*_polar(13.5, a), bd.Circle(r_dot))
    return out


def sparkle_dots_sketch(serial: int = 0) -> bd.Sketch:
    spec = [(-6, 13.1, 0.7), (6, 14.0, 0.45), (18, 12.9, 0.5), (30, 13.9, 0.75), (44, 13.0, 0.45),
            (56, 14.1, 0.6), (70, 13.2, 0.75), (84, 14.0, 0.45), (96, 13.0, 0.6), (110, 14.0, 0.7),
            (124, 13.1, 0.45), (136, 13.9, 0.75), (150, 12.9, 0.5), (164, 14.1, 0.6), (178, 13.2, 0.7)]
    return _union([_at(*_polar(r, a), bd.Circle(rd)) for a, r, rd in spec])


def lcg(seed: int):
    """Deterministic generator shared with the app (editor/src/cap-editor/barcode.ts)."""
    x = (seed * 2654435761 + 12345) % 2147483648
    while True:
        x = (x * 1103515245 + 12345) % 2147483648
        yield (x >> 16) & 0x7FFF


def barcode_bars(serial: int) -> list[tuple[float, float]]:
    """(start_deg, width_deg) of every bar in the window; bars are 0.9 or
    1.8 mm wide at r 13.5, gaps 0.9 or 1.8 mm, from the hen's serial."""
    per_mm = 180 / (math.pi * 13.5)
    g = lcg(serial)
    bars = []
    a = BAND_WINDOW[0] + 2
    end = BAND_WINDOW[1] - 2
    while True:
        w = (1.8 if next(g) % 3 == 0 else 0.9) * per_mm
        gap = (1.8 if next(g) % 4 == 0 else 0.9) * per_mm
        if a + w > end:
            break
        bars.append((round(a, 3), round(w, 3)))
        a += w + gap
    return bars


def barcode_sketch(serial: int = 0) -> bd.Sketch:
    out = bd.Sketch()
    for a, w in barcode_bars(serial):
        out = out + _annular_sector(12.1, 14.9, a, a + w)
    return out


ICONS = {
    "heart": heart_sketch, "star": star_sketch, "flower": flower_sketch,
    "egg": egg_sketch, "sun": sun_sketch, "moon": moon_sketch,
    "sparkles": sparkles_sketch, "bolt": bolt_sketch, "smiley": smiley_sketch,
    "cherry": cherry_sketch, "butterfly": butterfly_sketch, "mushroom": mushroom_sketch,
    "clover": clover_sketch, "rainbow": rainbow_sketch, "ghost": ghost_sketch,
    "saturn": saturn_sketch,
    "skull": skull_sketch, "alien": alien_sketch, "diamond": diamond_sketch,
    "crown": crown_sketch, "yinyang": yinyang_sketch, "peace": peace_sketch,
    "drop": drop_sketch, "broken_heart": broken_heart_sketch, "eye": eye_sketch,
    "paw": paw_sketch,
    "none": None,
}
PATTERNS_CENTRE = {"rings": rings_sketch, "solid": solid_sketch, "dots": centre_dots_sketch}
PATTERNS_BAND = {
    "stripes": stripes_sketch, "dots": band_dots_sketch, "arc": arc_sketch,
    "checker": checker_sketch, "zigzag": zigzag_sketch, "wave": wave_sketch,
    "dashes": dashes_sketch, "pixel": pixel_sketch,
    "barcode": barcode_sketch, "tally": tally_sketch, "sparkle_dots": sparkle_dots_sketch,
    "growing_dots": growing_dots_sketch, "double_arc": double_arc_sketch,
}
