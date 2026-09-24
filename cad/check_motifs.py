# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Printability of the whole motif library, in one run.

    uv run --python 3.12 check_motifs.py [--svg out/motifs.svg]

Every icon and centre pattern: inside r 7.4, features >= 0.8 mm, gaps >= 0.8 mm.
Every band pattern (for serial 67 and 12345): inside r 12.2-14.8 and the
window, same feature and gap rules. --svg writes a contact sheet.
"""
import math
import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).parent))
import cap_motifs as cm  # noqa: E402

FAIL = []


def fatten(sk, amount):
    out = sk
    for k in range(8):
        a = math.pi * k / 4
        out = out + bd.Pos(amount * math.cos(a), amount * math.sin(a)) * sk
    return out


def erode(sk, amount, r_big=24.0):
    """Erosion as the complement of a dilated complement: only booleans, so
    it cannot fail the way OCCT's 2D offset does on tangent unions."""
    big = bd.Circle(r_big)
    return big - fatten(big - sk, amount)


def real_faces(sk):
    """Faces that are not boolean slivers (crossings leave zero-area faces)."""
    return [f for f in sk.faces() if f.area > cm.SLIVER_AREA]


def feature_ok(sk):
    """Every island survives the erosion whole: nothing thinner than the
    minimum feature anywhere, no neck that would split it."""
    return len(real_faces(erode(sk, cm.PATTERN_ERODE))) == len(real_faces(sk))


def gap_ok(sk):
    return len(real_faces(fatten(sk, cm.PATTERN_GAP_MIN / 2))) == len(real_faces(sk))


def radial_range(sk):
    lo, hi = 1e9, 0.0
    for e in sk.edges():
        for i in range(25):
            p = e.position_at(i / 24)
            r = math.hypot(p.X, p.Y)
            lo, hi = min(lo, r), max(hi, r)
    return lo, hi


def angle_ok(sk):
    a0, a1 = cm.BAND_WINDOW
    for e in sk.edges():
        for i in range(9):
            p = e.position_at(i / 8)
            a = math.degrees(math.atan2(p.Y, p.X))
            a = a + 360 if a < a0 - 1 else a
            if not (a0 - 0.5 <= a <= a1 + 0.5):
                return False
    return True


def report(kind, name, sk, ok_extent, extent_txt):
    fo, go = feature_ok(sk), gap_ok(sk)
    ok = fo and go and ok_extent
    if not ok:
        FAIL.append(f"{kind}:{name}")
    print(f"  [{'PASS' if ok else 'FAIL'}] {kind:7} {name:14} islands {len(sk.faces()):2d}  "
          f"feature {'ok' if fo else 'THIN'}  gap {'ok' if go else 'NARROW'}  {extent_txt}")


sheet = []
print("=== icons and centre patterns (r <= 7.4) ===")
for name, fn in list(cm.ICONS.items()) + list(cm.PATTERNS_CENTRE.items()):
    if fn is None:
        continue
    sk = fn()
    lo, hi = radial_range(sk)
    report("icon" if name in cm.ICONS else "centre", name, sk, hi <= cm.CORE_PATTERN_R_MAX + 1e-6, f"r_max {hi:.2f}")
    sheet.append((name, sk))
print("=== band patterns (r 12.2-14.8, window -10..190) ===")
for name, fn in cm.PATTERNS_BAND.items():
    for serial in (67, 12345):
        sk = fn(serial)
        lo, hi = radial_range(sk)
        ext_ok = lo >= cm.BAND_PATTERN_R[0] - 0.05 and hi <= cm.BAND_PATTERN_R[1] + 0.05 and angle_ok(sk)
        report("band", f"{name}/{serial}", sk, ext_ok, f"r {lo:.2f}-{hi:.2f}")
        if serial == 67:
            sheet.append((name, sk))

if "--svg" in sys.argv:
    from cap_svg import sketch_to_path
    out = Path(sys.argv[sys.argv.index("--svg") + 1])
    cols = 6
    cell = 34
    rows = math.ceil(len(sheet) / cols)
    parts = []
    for i, (name, sk) in enumerate(sheet):
        cx, cy = (i % cols) * cell + cell / 2, (i // cols) * cell + cell / 2
        parts.append(f'<g transform="translate({cx},{cy}) scale(1,-1)"><circle r="16" fill="#e9eef2"/>'
                     f'<circle r="8.5" fill="#f6f6f2"/><path d="{sketch_to_path(sk)}" fill="#111" fill-rule="evenodd"/></g>'
                     f'<text x="{cx}" y="{cy + 16.5}" font-size="2.2" text-anchor="middle" font-family="sans-serif">{name}</text>')
    out.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cols * cell} {rows * cell}" width="{cols * 120}" height="{rows * 120}">'
                   + "".join(parts) + "</svg>\n")
    print(f"wrote {out}")

print("=" * 60)
print("all motifs printable" if not FAIL else f"FAILED: {', '.join(FAIL)}")
sys.exit(1 if FAIL else 0)
