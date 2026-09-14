# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Per-tag cap: clear shell + big coin lettering + accent core ring.

    uv run --python 3.12 cap_marking.py 67 --top "Bözsi!" --icon heart
    uv run --python 3.12 cap_marking.py 12345 --icon star

Deterministic by design: font sizes are FIXED (no content-dependent
shrinking), inputs that do not fit are rejected with measured numbers, and the
same input always yields byte-identical output. Customer-facing inputs:
number (1-5 digits, required), short message (charset- and length-checked),
icon (heart / star / flower / none), font (curated list). See
test_cap_marking.py for the accepted envelope.

Three bodies, three filaments, one file: out/cap_<n>.3mf

    cap_<n>       the whole shell in CLEAR PETG -- the LED (r 10, angle
                  uncontrolled) shines through wherever it lands, so no
                  window part and no angular alignment at all
    marking_<n>   the lettering and the icon, in the customer's text colour
    core_<n>      an accent ring (r 6.6..8.6) framing the icon, third colour

Layout, viewed from outside (coin convention):

                . . B Ö Z S I !  . .          <- top arc, big caps
             /                      \
            |     ___________        |
            |    / accent    \       |
            |   |  ring  ♥    |      |          centre: icon in text colour,
            |    \___________/       |          framed by the accent ring
             \                      /
                ' ' '  6 7  ' ' '             <- bottom arc, big digits

A print trial killed the previous opaque-shell + clear-LED-ring layout: the
2.9 mm lettering was unreadable. With the shell clear, the lettering band
runs from the accent core to the scallops (r 9.6..15.55, ~6 mm tall), the
digits are 6.0 pt and the message 5.2 pt caps -- roughly twice the printed
letter height, at the price of a shorter message.
"""

import argparse
import math
import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).parent))
from hen_tag_enclosure import OUT, P, PETG_DENSITY, build_cap  # noqa: E402
from cap_design import COLOUR_ROLES, ZONES, default_colours, load_catalog  # noqa: E402
from cap_motifs import (  # noqa: E402
    BAND_PATTERN_R, BAND_WINDOW, CORE_PATTERN_R_MAX, ICONS, PATTERN_ERODE, PATTERN_FEATURE_MIN,
    PATTERN_GAP_MIN, PATTERNS_BAND, PATTERNS_CENTRE, SLIVER_AREA,
)

# --- inlay ----------------------------------------------------------------
DEPTH_DEFAULT = 0.64   # coloured PETG is translucent; thinner reads washed-out
COVER_MIN = 0.30       # PETG that must remain above the inlay
# Curated faces, all with full Hungarian diacritics (ő/ű included). Verdana is
# the default: it was designed for legibility at small sizes -- open apertures,
# generous spacing -- and stays readable where chunkier faces blur together.
FONT_CHOICES = {
    "verdana": "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "tahoma": "/System/Library/Fonts/Supplemental/Tahoma.ttf",
    "arial": "/System/Library/Fonts/Supplemental/Arial.ttf",
    "futura": "/System/Library/Fonts/Supplemental/Futura.ttc",
    "din": "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf",
    "rounded": "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
}
FONT_DEFAULT = "verdana"
# Dilation radius. Thin faces at 3 mm cap height run ~0.25 mm raw strokes;
# +2x0.18 lands ~0.6 mm, which a 0.4 nozzle still draws cleanly while keeping
# the letterforms slim. Chunky faces can take less; the check below gates it.
GLYPH_FATTEN = 0.18
# A 0.4 nozzle with arachne walls draws a clean 0.45 mm single line; 0.58 sits
# safely above that. (0.60 put the ALL-CAPS message right on the boundary and
# failed on float rounding.)
FEATURE_MIN = 0.58     # smallest printable glyph feature accepted
GAP_MIN = 1.0          # opaque wall between the marking and the clear ring

# --- transparent shell ------------------------------------------------------
# The whole shell prints in clear PETG, so the LED (r 10.0, angle
# uncontrolled) shines through wherever it lands -- no dedicated window part,
# and rotation-independence comes free. A print trial killed the previous
# opaque-shell + clear-ring layout: at the 2.9 mm band the lettering was
# unreadable, and the customer look wanted a clear body anyway.
LED_R = 10.0           # LED centre 2.5 mm in from the Ø25 edge; operator caliper
# The clear window: an annulus through the whole top plate of an otherwise
# base-coloured shell. The LED can land anywhere in it, so it stays free of
# every inlay; the number sits entirely outside it (BAND_R_MIN below).
LED_RING = (8.5, 11.5)
WINDOW_MARGIN = 0.10
FOAM_INNER = (16.0, 12.0)   # foam ring kept inboard, off the LED radius

# --- accent core (third colour) ---------------------------------------------
# A full disc, not a ring: the accent colour fills the centre right up to the
# icon's outline (the icon is cut from the disc, so the two colours meet
# edge to edge with no clear gap -- same as the printed first trial looked).
CORE_R_OUT = LED_RING[0]   # the disc meets the window edge to edge

# --- coin lettering band --------------------------------------------------
# Deterministic: the font SIZES are fixed, so every tag in a production run
# looks consistent. Inputs that do not fit at these sizes are rejected with
# the measured numbers instead of being silently shrunk.
# With no clear ring to dodge, the band runs from just outside the accent
# core to the scallops: 9.6..15.55, nearly 6 mm tall -- twice the letter
# height of the failed print.
BAND_R_MIN = LED_RING[1] + WINDOW_MARGIN   # 11.60: the number never enters the window
BAND_R_MAX = 15.40
NUM_FONT = 4.5         # digits; ~3.4 mm tall on the print, 3.8 mm with the dilation
NUM_MAX_DIGITS = 5
# The message is set in ALL CAPS, classic coin typography -- and a hard
# physical necessity, found by the test suite: a lowercase descender (g j p q
# y) combined with an accented capital needs ~1.15 em of band height, which at
# any printable stroke width does not fit the 2.9 mm band. Capitals with
# Hungarian accents alone do.
TOP_FONT = 3.6         # caps ~2.6 mm tall on the print (staff-only message; accented
                       # capitals need 3.85 mm of the 3.95 mm band above the window)
TOP_R_MIN = LED_RING[1] + 0.05   # the message may come 0.05 closer to the window than the number
TOP_R_MAX = 15.60      # 0.12 mm to the scallop nicks
SPAN_TOP_MAX = 200.0   # deg the top message may occupy
GAP_ARC = 14.0         # deg clearance between top and bottom texts, each side

# Message charset. Every character was verified to exist in all curated
# faces; anything outside is rejected rather than rendered as tofu. No comma,
# semicolon or parentheses: those dip below the baseline, and a descending
# glyph combined with an accented capital cannot fit the band at any printable
# size -- with them excluded, EVERY allowed message fits the band height at
# TOP_FONT and only the arc length limits it.
TOP_CHARSET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "áéíóöőúüűÁÉÍÓÖŐÚÜŰ0123456789 .:!?'\"+-")

# --- centre icons and patterns: cap_motifs.py ---------------------------------


_ACTIVE_FONT: str | None = None


def set_font(choice: str) -> None:
    global _ACTIVE_FONT
    path = FONT_CHOICES.get(choice.lower(), choice)
    if not Path(path).exists():
        raise SystemExit(f"font not found: {path} "
                         f"(choices: {', '.join(FONT_CHOICES)} or a .ttf path)")
    _ACTIVE_FONT = path


def _font() -> str:
    if _ACTIVE_FONT is None:
        set_font(FONT_DEFAULT)
    return _ACTIVE_FONT


def fatten(sk: bd.Sketch, amount: float = GLYPH_FATTEN) -> bd.Sketch:
    """Dilate the glyphs by ~`amount`: union of the sketch with copies shifted
    around a circle of that radius. OCCT's 2D outline offset fails outright on
    some glyph faces (small sizes especially); a union of translations cannot
    fail, approximates disc-dilation well at 8 directions, and adds twice the
    radius to every stroke width."""
    out = sk
    for k in range(8):
        a = math.pi * k / 4
        out = out + bd.Pos(amount * math.cos(a), amount * math.sin(a)) * sk
    return out


def min_feature(sk: bd.Sketch) -> float:
    """Smallest printable feature: stroke width for elongated glyph faces,
    diameter for dot-like ones (umlauts, the tittle of an i, a full stop).
    2A/P measures width for a long stroke but only HALF the diameter of a
    dot, so dots get the honest sqrt(4A/pi) instead."""
    worst = 1e9
    for f in sk.faces():
        area = f.area
        per = sum(e.length for e in f.edges())
        if area < 0.5:                       # dot-like
            worst = min(worst, math.sqrt(4 * area / math.pi))
        else:
            worst = min(worst, 2 * area / per)
    return worst


def radial_range(sk: bd.Sketch) -> tuple[float, float]:
    lo, hi = 1e9, 0.0
    for e in sk.edges():
        for i in range(25):
            pt = e.position_at(i / 24)
            r = math.hypot(pt.X, pt.Y)
            lo, hi = min(lo, r), max(hi, r)
    return lo, hi


def angle_span(sk: bd.Sketch, centre_deg: float) -> tuple[float, float]:
    """Occupied angular interval in ABSOLUTE deg (lo, hi), measured relative
    to centre_deg so a text straddling 0/360 does not read as a full circle."""
    rel = []
    for e in sk.edges():
        for i in range(9):
            pt = e.position_at(i / 8)
            a = math.degrees(math.atan2(pt.Y, pt.X))
            rel.append((a - centre_deg + 180) % 360 - 180)
    return centre_deg + min(rel), centre_deg + max(rel)


def arc_text(txt: str, font_size: float, centre_deg: float, upright: bool,
             base_r: float) -> bd.Sketch:
    """Text bent along the lettering band, centred on centre_deg.

    upright=True: glyph tops point outward (coin top). False: tops point
    toward the centre (coin bottom). Both read left to right."""
    # Generous arc; position_on_path=0.5 centres the text on its midpoint.
    if upright:
        path = bd.Edge.make_circle(
            base_r, start_angle=centre_deg + 160, end_angle=centre_deg - 160,
            angular_direction=bd.AngularDirection.CLOCKWISE)
    else:
        path = bd.Edge.make_circle(
            base_r, start_angle=centre_deg - 160, end_angle=centre_deg + 160,
            angular_direction=bd.AngularDirection.COUNTER_CLOCKWISE)
    return bd.Text(txt, font_size=font_size, font_path=_font(), path=path,
                   position_on_path=0.5, align=(bd.Align.CENTER, bd.Align.CENTER))


def fit_arc_text(txt: str, font_size: float, centre_deg: float, upright: bool,
                 r_min: float, r_max: float):
    """Bent, fattened text at a FIXED size, radially centred in its band.

    Built once at the band centre to measure, then rebuilt with the base
    radius corrected so the glyph body is centred -- diacritics and descenders
    are not symmetric about the baseline, so the correction is measured, not
    assumed. Rejects (rather than shrinks) anything that still leaves the
    band: sizes are fixed so a production run looks uniform."""
    mid = (r_min + r_max) / 2
    raw = arc_text(txt, font_size, centre_deg, upright, mid)
    probe = fatten(raw)
    lo, hi = radial_range(probe)
    dr = ((r_max - hi) - (lo - r_min)) / 2
    if abs(dr) >= 0.05:
        raw = arc_text(txt, font_size, centre_deg, upright, mid + dr)
        probe = fatten(raw)
    lo, hi = radial_range(probe)
    if lo < r_min - 1e-3 or hi > r_max + 1e-3:
        raise SystemExit(
            f"{txt!r} is too tall for the lettering band at the fixed font "
            f"size {font_size} (needs r {lo:.2f}..{hi:.2f}, band "
            f"{r_min}..{r_max})")
    return probe, min_feature(raw)


def top_char_budget() -> tuple[float, int]:
    """(widest allowed character's arc advance in deg, guaranteed safe char
    count). Any message of at most that many charset characters fits the
    SPAN_TOP_MAX arc regardless of which characters it uses. Deterministic:
    measured from the font file at the fixed size, on the uppercased charset
    the message is actually set in."""
    base_r = (TOP_R_MIN + TOP_R_MAX) / 2
    widest = 0.0
    for c in sorted(set(TOP_CHARSET.upper())):
        probe = "a a" if c == " " else c * 11
        ref = "aa" if c == " " else c
        # true advance incl. spacing: width(n chars) - width(1 char), / (n-1)
        w_n = bd.Text(probe, font_size=TOP_FONT, font_path=_font()).bounding_box().size.X
        w_1 = bd.Text(ref, font_size=TOP_FONT, font_path=_font()).bounding_box().size.X
        widest = max(widest, (w_n - w_1) / (len(probe) - len(ref)))
    per_char_deg = math.degrees(widest / base_r)
    return per_char_deg, int((SPAN_TOP_MAX - 2.0) // per_char_deg)


def pattern_feature_ok(sk: bd.Sketch) -> bool:
    """Every island survives an erosion by half of PATTERN_FEATURE_MIN, so its
    narrowest part is at least that wide. Exact on the simple shapes patterns
    are made of, where the 2A/P estimator used for glyphs under-reads short
    bars (a 0.9 x 2.6 mm stripe measures 0.67)."""
    big = bd.Circle(24.0)
    eroded = big - fatten(big - sk, PATTERN_ERODE)   # complement trick: booleans only
    return len(real_faces(eroded)) == len(real_faces(sk))


def real_faces(sk: bd.Sketch) -> list:
    """Faces that are not boolean slivers (crossings leave zero-area faces)."""
    return [f for f in sk.faces() if f.area > SLIVER_AREA]


def led_ring_clear_fraction(*inlays: bd.Sketch) -> float:
    """Fraction of the LED window (r 8.5-11.5) not covered by any inlay."""
    ring = bd.Circle(LED_RING[1]) - bd.Circle(LED_RING[0])
    covered = 0.0
    for sk in inlays:
        hit = ring & sk
        covered += hit.area if hit is not None else 0.0
    return 1.0 - covered / ring.area


def pattern_gap_ok(sk: bd.Sketch) -> bool:
    """Islands closer than PATTERN_GAP_MIN merge when each is dilated by half
    of it, so a changed face count means a gap too narrow to print."""
    return len(real_faces(fatten(sk, PATTERN_GAP_MIN / 2))) == len(real_faces(sk))


def build_lettering(number: str, top: str, icon: str, centre: str | None = None,
                    band: str | None = None):
    """Compose the marking: bottom number arc, optional top message arc,
    optional centre icon or centre pattern, optional band pattern. Fixed font
    sizes; misfits are rejected, never shrunk.
    Returns (marking sketch, centre element, spans_deg, stroke_raw, band sketch)."""
    bot, stroke_raw = fit_arc_text(number, NUM_FONT, 270.0, upright=False,
                                   r_min=BAND_R_MIN, r_max=BAND_R_MAX)
    mk = bot
    b_lo, b_hi = angle_span(bot, 270.0)
    spans = {"number": b_hi - b_lo}

    if top:
        msg, s2 = fit_arc_text(top, TOP_FONT, 90.0, upright=True,
                               r_min=TOP_R_MIN, r_max=TOP_R_MAX)
        stroke_raw = min(stroke_raw, s2)
        t_lo, t_hi = angle_span(msg, 90.0)
        span_top = t_hi - t_lo
        if span_top > SPAN_TOP_MAX:
            raise SystemExit(
                f"message spans {span_top:.0f} deg of arc, max is "
                f"{SPAN_TOP_MAX:.0f} -- shorten it "
                f"(guaranteed-safe length: {top_char_budget()[1]} characters)")
        if t_hi > b_lo - GAP_ARC or t_lo < b_hi - 360 + GAP_ARC:
            raise SystemExit("top and bottom lettering meet at the sides; "
                             "shorten the message")
        mk = mk + msg
        spans["top"] = span_top

    ic = None
    if centre is not None:
        ic = PATTERNS_CENTRE[centre]()
    elif ICONS[icon] is not None:
        ic = ICONS[icon]()
    if ic is not None:
        if radial_range(ic)[1] > CORE_PATTERN_R_MAX + 1e-6:
            raise SystemExit(f"centre element too large for the disc (r {radial_range(ic)[1]:.2f} > {CORE_PATTERN_R_MAX})")
        mk = mk + ic
    band_sk = PATTERNS_BAND[band](int(number)) if band is not None else None
    if band_sk is not None:
        # Keep the accent-colour band pattern away from the text-colour number:
        # the window is fixed, so this only trips if BAND_WINDOW is widened.
        lo_w, hi_w = BAND_WINDOW
        gap = min((b_lo - hi_w) % 360, (lo_w - b_hi) % 360)
        if gap < GAP_ARC / 2:
            raise SystemExit(f"band pattern within {gap:.0f} deg of the number")
    return mk, ic, spans, stroke_raw, band_sk


def build(number: str, top: str, icon: str, depth: float, centre: str | None = None,
          band: str | None = None, cap: bd.Solid | None = None,
          colours: dict | None = None):
    """Four bodies for four AMS slots, all the colour work in the top plate:

        shell   base colour: the cap, its top plate outside the window, and
                every zone or inlay a design leaves in the base colour
        window  clear: the LED annulus r 8.5-11.5 through the whole plate
        a, b    the scheme's two free colours: whichever zones (outer ring,
                inner disc, full plate depth) and inlays (number, centre
                element, band pattern; `depth` deep, flush outside) the design
                assigns to them

    colours maps the five zones (cap_design.ZONES) to 'base' | 'a' | 'b';
    the catalog's must_differ_from rules keep every inlay visible on its zone.
    Returns (cap, bodies, sketches, spans, stroke_raw) with
    bodies = {"shell", "window", "a", "b"} (a/b may be None) and
    sketches = {"marking", "centre", "band", "ring", "disc"}."""
    p = P
    z_top = p.z_ceiling + p.cap_top_t
    col = dict(colours or default_colours(load_catalog()))
    mk, ic, spans, stroke_raw, band_sk = build_lettering(number, top, icon, centre, band)
    lettering = mk - ic if ic is not None else mk           # number (+ message) only

    if cap is None:
        cap = build_cap(p, foam=FOAM_INNER)

    def plate(sk: bd.Sketch) -> bd.Solid:
        return (bd.Pos(0, 0, p.z_ceiling) * bd.extrude(sk, amount=p.cap_top_t)) & cap

    def inlay(sk: bd.Sketch | None) -> bd.Solid | None:
        return None if sk is None else (bd.Pos(0, 0, z_top - depth) * bd.extrude(sk, amount=depth)) & cap

    window = plate(bd.Circle(LED_RING[1]) - bd.Circle(LED_RING[0]))
    zones = {"ring": plate(bd.Circle(p.r_cap_out + 2) - bd.Circle(LED_RING[1])),
             "disc": plate(bd.Circle(CORE_R_OUT))}
    inlays = {"number": inlay(lettering), "centre": inlay(ic), "band": inlay(band_sk)}
    host = {"number": "ring", "band": "ring", "centre": "disc"}

    bodies = {}
    for c in ("a", "b"):
        body = None
        for z, solid in zones.items():
            if col[z] == c:
                body = solid if body is None else body + solid
        # inlays of another colour sitting in this colour's zone leave it
        for k, solid in inlays.items():
            if solid is not None and col[host[k]] == c and col[k] != c and body is not None:
                body = body - solid
        for k, solid in inlays.items():
            if solid is not None and col[k] == c:
                body = solid if body is None else body + solid
        bodies[c] = body
    shell = cap - window
    for c in ("a", "b"):
        if bodies[c] is not None:
            shell = shell - bodies[c]
    bodies = {"shell": shell, "window": window, **bodies}
    sketches = {"marking": lettering, "centre": ic, "band": band_sk,
                "ring": bd.Circle(p.r_cap_out) - bd.Circle(LED_RING[1]), "disc": bd.Circle(CORE_R_OUT)}
    return cap, bodies, sketches, spans, stroke_raw


def canonical_mesh(solid, name: str) -> tuple[list, list]:
    """Welded, canonically ordered triangle mesh of a solid.

    Welding: OCCT tessellates face by face and hands back every face's
    vertices separately, so shared edges arrive as duplicated points and the
    mesh is not connected at all. STL importers weld on load; 3MF importers
    take the index buffer at its word, and the resulting hairline cracks slice
    into slivers that the slicer reports as floating regions.

    Canonical order: OCCT meshes faces in parallel, so the same geometry comes
    back with a different triangle order on every run. Sorting vertices and
    triangles (rotation-normalised, winding preserved) makes the serialised
    mesh reproducible byte for byte.

    Refuses non-manifold results."""
    from collections import Counter

    raw_verts, raw_tris = solid.tessellate(0.008, 0.1)
    index: dict[tuple, int] = {}
    verts: list[tuple] = []
    remap = []
    for v in raw_verts:
        key = (round(v.X, 4) or 0.0, round(v.Y, 4) or 0.0, round(v.Z, 4) or 0.0)
        if key not in index:
            index[key] = len(verts)
            verts.append(key)
        remap.append(index[key])

    order = sorted(range(len(verts)), key=lambda i: verts[i])
    rank = [0] * len(verts)
    for new, old in enumerate(order):
        rank[old] = new
    verts = [verts[old] for old in order]

    tris = []
    for a, b, c in raw_tris:
        t = (rank[remap[a]], rank[remap[b]], rank[remap[c]])
        if len(set(t)) != 3:
            continue                                  # drop degenerates
        m = t.index(min(t))
        tris.append(t[m:] + t[:m])                    # rotate, keep winding
    tris.sort()

    edges = Counter()
    for a, b, c in tris:
        for e in ((a, b), (b, c), (c, a)):
            edges[(min(e), max(e))] += 1
    bad = sum(1 for n in edges.values() if n != 2)
    if bad:
        raise SystemExit(f"{name}: {bad} non-manifold edges after welding; "
                         f"refusing to write a leaky mesh")
    return verts, tris


def write_stl(path: Path, verts: list, tris: list) -> None:
    """Deterministic binary STL from a canonical mesh."""
    import struct

    with open(path, "wb") as f:
        f.write(b"hen-tag deterministic STL".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            va, vb, vc = verts[a], verts[b], verts[c]
            ux, uy, uz = (vb[i] - va[i] for i in range(3))
            wx, wy, wz = (vc[i] - va[i] for i in range(3))
            nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
            mag = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            f.write(struct.pack("<12fH", nx / mag, ny / mag, nz / mag,
                                *va, *vb, *vc, 0))


def write_3mf(path: Path, named_meshes: dict) -> None:
    """Minimal spec-conforming 3MF: one mesh object per named canonical mesh,
    one build item each, no transforms (geometry is already placed).
    Millimetres. Byte-deterministic: canonical meshes, fixed timestamps.

    Written by hand rather than via Mesher: Mesher emits one 3MF object per
    solid, which explodes the marking into its disjoint glyphs and hands the
    slicer a dozen objects instead of two. Disjoint shells inside one mesh
    are fine."""
    import zipfile

    objects, items = [], []
    for i, (name, (verts, tris)) in enumerate(named_meshes.items()):
        oid = i + 1
        vx = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
        tx = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        objects.append(f'<object id="{oid}" type="model" name="{name}">'
                       f'<mesh><vertices>{vx}</vertices>'
                       f'<triangles>{tx}</triangles></mesh></object>')
        items.append(f'<item objectid="{oid}"/>')

    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(objects)}</resources>'
             f'<build>{"".join(items)}</build></model>')
    ctypes = ('<?xml version="1.0" encoding="UTF-8"?>'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
              '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        # Fixed timestamps: identical input must produce byte-identical files,
        # so a regenerated tag can be diffed against the shipped one.
        for name, payload in (("[Content_Types].xml", ctypes),
                              ("_rels/.rels", rels),
                              ("3D/3dmodel.model", model)):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, payload)


def vol(shape) -> float:
    return shape.volume if shape is not None else 0.0


BAMBU_APP = Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
BAMBU_PROFILES = Path("/Applications/BambuStudio.app/Contents/Resources/profiles/BBL")


def write_bambu_project(generic: Path, out: Path, extruder_by_name: dict,
                        object_name: str, true_bbox_by_name: dict) -> bool:
    """Bambu Studio project 3MF: ONE object, three parts, filament slots
    pre-assigned.

    A vendor-neutral 3MF reaches Bambu Studio as "other vendor" geometry: the
    objects get auto-arranged apart on the plate (rotations included) and the
    filament mapping is left to the user. A real Bambu project fixes both, and
    the CLI is the only reliable writer of the format. So: export the generic
    3MF through the CLI with `--assemble --arrange 0` (one object, the bodies
    as parts with identity transforms -- in register and inseparable), with
    the P1S machine, 0.16 mm process and three PETG filament slots loaded;
    then patch each part's `extruder` in Metadata/model_settings.config and
    drop the object onto the plate centre. Verified to reload in Bambu Studio
    with the 1/2/3 mapping intact.

    Returns False (skipping quietly) when Bambu Studio is not installed."""
    import re
    import subprocess
    import tempfile

    mach = BAMBU_PROFILES / "machine/Bambu Lab P1S 0.4 nozzle.json"
    proc = BAMBU_PROFILES / "process/0.16mm Optimal @BBL X1C.json"
    fil = BAMBU_PROFILES / "filament/Bambu PETG Basic @BBL X1C.json"
    if not (BAMBU_APP.exists() and mach.exists() and proc.exists() and fil.exists()):
        return False

    with tempfile.TemporaryDirectory() as td:
        tmp3mf = Path(td) / "project.3mf"
        r = subprocess.run(
            [str(BAMBU_APP), "--load-settings", f"{mach};{proc}",
             "--load-filaments", f"{fil};{fil};{fil};{fil}",
             "--assemble", "--arrange", "0",
             "--export-3mf", str(tmp3mf), str(generic)],
            capture_output=True, text=True)
        if r.returncode != 0 or not tmp3mf.exists():
            print(f"  (Bambu project export failed, rc={r.returncode}; "
                  f"generic 3MF still valid)")
            return False

        ex = Path(td) / "x"
        subprocess.run(["unzip", "-q", str(tmp3mf), "-d", str(ex)], check=True)

        # The CLI's assembler recentres EVERY part about its own bounding-box
        # middle and leaves identity transforms, which stacks all three bodies
        # concentric at mid-height -- the lettering and the ring float in the
        # middle of the cap. The registration is restored by translating each
        # part back to its true world-space centre, which we know exactly from
        # the solids we exported. Patch it in both places Bambu stores it.
        cfg_path = ex / "Metadata/model_settings.config"
        cfg = cfg_path.read_text()
        part_id_by_name = dict(
            (m.group(2), m.group(1)) for m in re.finditer(
                r'<part id="(\d+)"[^>]*>\s*<metadata key="name" value="([^"]+)"/>', cfg))

        centres = {
            name: ((bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2,
                   (bb.min.Z + bb.max.Z) / 2)
            for name, bb in true_bbox_by_name.items()}

        for name, extr in extruder_by_name.items():
            cx, cy, cz = centres[name]
            block, n = re.subn(
                rf'(<part id="\d+"[^>]*>\s*<metadata key="name" value="{name}"/>'
                rf'(?:(?!</part>).)*?<metadata key="extruder" value=")\d+(")',
                rf'\g<1>{extr}\g<2>', cfg, flags=re.S)
            if n != 1:
                print(f"  (could not patch extruder for {name}; skipping project)")
                return False
            cfg = block
            cfg, n = re.subn(
                rf'(<part id="{part_id_by_name[name]}"[^>]*>(?:(?!</part>).)*?'
                rf'<metadata key="matrix" value=")[^"]+(")',
                rf'\g<1>1 0 0 {cx:.6g} 0 1 0 {cy:.6g} 0 0 1 {cz:.6g} 0 0 0 1\g<2>',
                cfg, flags=re.S)
            if n != 1:
                print(f"  (could not patch matrix for {name}; skipping project)")
                return False
        cfg = cfg.replace('<metadata key="name" value="Assembly"/>',
                          f'<metadata key="name" value="{object_name}"/>', 1)
        cfg_path.write_text(cfg)

        # Same translations on the geometry side: the component transforms.
        model_path = ex / "3D/3dmodel.model"
        model = model_path.read_text()
        for name, pid in part_id_by_name.items():
            cx, cy, cz = centres[name]
            model, n = re.subn(
                rf'(<component [^>]*objectid="{pid}"[^>]*transform=")[-\d.e ]+(")',
                rf'\g<1>1 0 0 0 1 0 0 0 1 {cx:.6g} {cy:.6g} {cz:.6g}\g<2>', model)
            if n != 1:
                print(f"  (could not patch component for {name}; skipping project)")
                return False
        # Assembly-local coords now equal our world coords (bottom at z 0), so
        # the build item just moves the object to the plate centre.
        model, n = re.subn(
            r'(<item objectid="\d+"[^>]*transform=")[-\d.e ]+(")',
            r'\g<1>1 0 0 0 1 0 0 0 1 128 128 0\g<2>', model)
        if n != 1:
            print("  (unexpected build layout; skipping project)")
            return False
        model_path.write_text(model)

        # Numeric proof before shipping: stored part bbox + its translation
        # must reproduce the true world bbox of every body.
        mesh = (ex / "3D/Objects/object_1.model").read_text()
        stored = {}
        for m in re.finditer(r'<object id="(\d+)"[^>]*>.*?<vertices>(.*?)</vertices>',
                             mesh, re.S):
            vs = re.findall(r'<vertex x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"',
                            m.group(2))
            cols = list(zip(*[(float(a), float(b), float(c)) for a, b, c in vs]))
            stored[m.group(1)] = [(min(c), max(c)) for c in cols]
        for name, pid in part_id_by_name.items():
            bb = true_bbox_by_name[name]
            true = [(bb.min.X, bb.max.X), (bb.min.Y, bb.max.Y), (bb.min.Z, bb.max.Z)]
            for ax in range(3):
                lo = stored[pid][ax][0] + centres[name][ax]
                hi = stored[pid][ax][1] + centres[name][ax]
                if abs(lo - true[ax][0]) > 0.02 or abs(hi - true[ax][1]) > 0.02:
                    print(f"  (registration verify failed for {name} axis {ax}: "
                          f"{lo:.2f}..{hi:.2f} vs {true[ax][0]:.2f}..{true[ax][1]:.2f}; "
                          f"skipping project)")
                    return False

        # Rebuild preserving the original entry order -- 3MF readers care.
        order = subprocess.run(["unzip", "-Z1", str(tmp3mf)],
                               capture_output=True, text=True, check=True).stdout.split()
        out.unlink(missing_ok=True)
        for entry in order:
            subprocess.run(["zip", "-q", "-X", str(out.resolve()), entry],
                           cwd=ex, check=True)
    return True


def parse_colours(text: str | None, cat: dict) -> dict:
    """'ring=base,number=a,disc=b,centre=a,band=b' -> zone map; missing
    zones take the catalog defaults."""
    col = default_colours(cat)
    if text:
        for item in text.split(","):
            zone, _, role = item.strip().partition("=")
            if zone not in ZONES or role not in COLOUR_ROLES:
                raise SystemExit(f"--colours: use zone=role with zones {', '.join(ZONES)} "
                                 f"and roles {', '.join(COLOUR_ROLES)} (got {item!r})")
            col[zone] = role
    return col


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("number", help="tag id, bent along the bottom arc, e.g. 67")
    ap.add_argument("--top", default="",
                    help='staff-only message bent along the top arc, e.g. "Szeretlek Bözsi!"')
    ap.add_argument("--icon", default="heart", choices=sorted(ICONS),
                    help="centre symbol (default heart)")
    ap.add_argument("--centre", default=None, choices=sorted(PATTERNS_CENTRE),
                    help="centre pattern instead of an icon")
    ap.add_argument("--band", default=None, choices=sorted(PATTERNS_BAND),
                    help="pattern in the band above the number")
    ap.add_argument("--colours", default=None,
                    help="zone colours, e.g. ring=base,number=a,disc=b,centre=a,band=b")
    ap.add_argument("--scheme", default="pasture",
                    help="catalog scheme id for the proof colours (default pasture)")
    ap.add_argument("--depth", type=float, default=DEPTH_DEFAULT,
                    help=f"inlay thickness in mm (default {DEPTH_DEFAULT}); must leave "
                         f">= {COVER_MIN} mm of cover")
    ap.add_argument("--font", default=FONT_DEFAULT, choices=sorted(FONT_CHOICES),
                    help=f"lettering face (default {FONT_DEFAULT})")
    ap.add_argument("--layout-json", default=None,
                    help="also write the preview layout JSON (hen-cap-layout/1) here")
    ap.add_argument("--proof", default=None, help="write a top-view proof SVG here")
    ap.add_argument("--skip-bambu", action="store_true",
                    help="skip the Bambu Studio project export (tests, CI)")
    a = ap.parse_args()
    set_font(a.font)
    cat = load_catalog()

    number = a.number.strip()
    if not number.isdigit() or not 1 <= len(number) <= NUM_MAX_DIGITS:
        raise SystemExit(f"number must be 1-{NUM_MAX_DIGITS} digits")
    # Coin typography: the message is set in ALL CAPS. Also load-bearing --
    # see the TOP_FONT comment for why mixed case cannot print at this size.
    top = a.top.strip().upper()
    bad = sorted(set(top) - set(TOP_CHARSET))
    if bad:
        raise SystemExit(f"message contains unsupported characters: {bad!r} "
                         f"(allowed: letters incl. Hungarian, digits, "
                         f"space and .,:;!?'\"()+-)")
    if a.centre is not None and "--icon" in sys.argv and a.icon != "none":
        raise SystemExit("--centre and --icon are mutually exclusive")
    colours = parse_colours(a.colours, cat)
    from cap_design import validate_design
    scheme = next((s for s in cat["schemes"] if s["id"] == a.scheme), None)
    if scheme is None:
        raise SystemExit(f"unknown scheme {a.scheme!r}")
    problems = validate_design(cat, {"serial": int(number), "scheme": a.scheme,
                                     "icon": None if a.icon == "none" or a.centre else a.icon,
                                     "centre": a.centre, "band": a.band, "colours": colours})
    if problems:
        raise SystemExit("design refused: " + "; ".join(problems))
    depth = a.depth
    if not 0.16 <= depth <= P.cap_top_t - COVER_MIN:
        raise SystemExit(f"--depth must be between 0.16 and {P.cap_top_t - COVER_MIN:.2f} mm")

    OUT.mkdir(parents=True, exist_ok=True)
    cap, bodies, sk, spans, stroke_raw = build(
        number, top, a.icon, depth, centre=a.centre, band=a.band, colours=colours)

    # --- machine checks ------------------------------------------------------
    ok = True

    def check(cond: bool, label: str, detail: str) -> None:
        nonlocal ok
        ok &= cond
        print(f"  [{'PASS' if cond else 'FAIL'}] {label:38} {detail}")

    p = P
    z_top = p.z_ceiling + p.cap_top_t
    present = {k: v for k, v in bodies.items() if v is not None}
    gap_v = abs(cap.volume - sum(vol(b) for b in present.values()))
    check(gap_v / cap.volume < 5e-4, "parts add up to the cap",
          f"|cap - sum(parts)| = {gap_v:.4f} mm3 ({gap_v / cap.volume * 100:.4f}%), "
          f"bodies: {', '.join(present)}")
    wb = bodies["window"].bounding_box()
    check(abs(wb.max.Z - z_top) < 1e-6 and abs(wb.min.Z - p.z_ceiling) < 1e-6,
          "clear window through the whole plate",
          f"z {wb.min.Z:.2f}..{wb.max.Z:.2f}, r {LED_RING[0]}..{LED_RING[1]}")
    for c in ("a", "b"):
        if bodies[c] is not None:
            bb = bodies[c].bounding_box()
            check(abs(bb.max.Z - z_top) < 1e-6 and bb.min.Z >= p.z_ceiling - 1e-6,
                  f"colour {c} flush with the outer face", f"z {bb.min.Z:.2f}..{bb.max.Z:.2f}")
    names = list(present)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            check(vol(present[x] & present[y]) < 1e-3, f"{x}/{y} do not overlap",
                  f"{vol(present[x] & present[y]):.5f} mm3")
    check(all(b.is_valid for b in present.values()), "solids valid",
          "; ".join(f"{k} {vol(v):.1f} mm3" for k, v in present.items()))
    stroke = stroke_raw + 2 * GLYPH_FATTEN
    check(stroke >= FEATURE_MIN, "thinnest glyph stroke printable",
          f"{stroke:.2f} mm ({stroke_raw:.2f} raw + 2x{GLYPH_FATTEN} dilation); "
          f"fixed fonts number={NUM_FONT} top={TOP_FONT}")
    check(True, "arc occupancy",
          "  ".join(f"{k} {v:.0f} deg" for k, v in spans.items()) + f"  (top max {SPAN_TOP_MAX:.0f})")
    lo, hi = radial_range(sk["marking"])
    check(lo >= LED_RING[1] - 1e-6, "number clear of the LED window",
          f"innermost point r {lo:.2f} >= {LED_RING[1]}")
    check(hi <= TOP_R_MAX + 1e-6, "lettering clear of the grip scallops",
          f"outermost point r {hi:.2f} <= {TOP_R_MAX}")
    for label, sk_ in (("centre element", sk["centre"]), ("band pattern", sk["band"])):
        if sk_ is None:
            continue
        if label == "centre element":
            check(radial_range(sk_)[1] <= CORE_PATTERN_R_MAX + 1e-6, "centre element inside the disc",
                  f"r_max {radial_range(sk_)[1]:.2f} <= {CORE_PATTERN_R_MAX}")
        check(pattern_feature_ok(sk_), f"{label} feature printable",
              f"every island survives a {PATTERN_ERODE:.2f} mm erosion "
              f"({len(real_faces(sk_))} islands)")
        check(pattern_gap_ok(sk_), f"{label} gaps printable",
              f">= {PATTERN_GAP_MIN} mm between islands")
    clear = led_ring_clear_fraction(*[x for x in (sk["marking"], sk["centre"], sk["band"]) if x is not None])
    check(clear >= 0.999, "LED window stays clear", f"{clear * 100:.0f}% of r {LED_RING[0]}-{LED_RING[1]} open")
    check(True, "zone colours", ", ".join(f"{z}={colours[z]}" for z in ZONES) + f"  scheme {scheme['id']}")

    if not ok:
        raise SystemExit("checks failed, nothing exported")

    if a.layout_json:
        from cap_svg import write_layout
        write_layout(Path(a.layout_json))
        print(f"  exported {Path(a.layout_json).name}  (preview layout)")
    if a.proof:
        from cap_svg import write_proof
        write_proof(Path(a.proof), sk, scheme, colours)
        print(f"  exported {Path(a.proof).name}  (proof, scheme {a.scheme})")

    # --- export, print orientation, one shared transform ---------------------
    flipped = bd.Rot(180, 0, 0) * bodies["shell"]
    dz = -flipped.bounding_box().min.Z
    parts = {f"cap_{number}": bodies["shell"], f"window_{number}": bodies["window"]}
    for c in ("a", "b"):
        if bodies[c] is not None:
            parts[f"{c}_{number}"] = bodies[c]
    oriented = {}
    for name, solid in parts.items():
        oriented[name] = bd.Pos(0, 0, dz) * (bd.Rot(180, 0, 0) * solid)
    meshes = {name: canonical_mesh(solid, name) for name, solid in oriented.items()}
    for name, (verts, tris) in meshes.items():
        write_stl(OUT / f"{name}.stl", verts, tris)
        print(f"  exported {name}.stl")
    write_3mf(OUT / f"cap_{number}.3mf", meshes)
    print(f"  exported cap_{number}.3mf  ({len(parts)} bodies, registered)")

    # AMS slots: 1 base, 2 clear, 3 colour a, 4 colour b
    extruders = {f"cap_{number}": 1, f"window_{number}": 2, f"a_{number}": 3, f"b_{number}": 4}
    extruders = {k: v for k, v in extruders.items() if k in parts}
    if not a.skip_bambu and write_bambu_project(OUT / f"cap_{number}.3mf",
                           OUT / f"cap_{number}_P1S.3mf", extruders,
                           f"cap_{number}",
                           {n: s.bounding_box() for n, s in oriented.items()}):
        print(f"  exported cap_{number}_P1S.3mf  (Bambu project, AMS 1 = base "
              f"{scheme['base']['filament']}, 2 = clear, 3 = {scheme['a']['filament']}, "
              f"4 = {scheme['b']['filament']})")
    else:
        print(f"\nSlicer: open cap_{number}.3mf, assign filaments: cap = base colour, "
              f"window = clear PETG, a/b = the scheme's two colours.")


if __name__ == "__main__":
    main()
