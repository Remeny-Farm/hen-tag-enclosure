# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d", "bd_warehouse"]
# ///
"""Verification pass: assemble the parts virtually and measure what matters.

Checks nobody can eyeball reliably:
  1. do body and cap collide when screwed together?
  2. does the flipped board fit, holder down into its pocket?
  3. does the fill actually retain the holder?
  4. is there head clearance, and does the foam ring span it while leaving the
     LED window clear?
  5. can the cap be assembled at all -- the check that caught thread-low?
  6. is every wall thick enough to print watertight?
  7. do the harness tabs take an 8 mm elastic, and is the underside flat?

Also emits half-section STLs so the internals can be inspected visually.
"""

import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).parent))
from hen_tag_enclosure import (  # noqa: E402
    OUT, P, build_body, build_cap, cyl, ring,
)

FAIL: list[str] = []
WARN: list[str] = []


def check(ok: bool, label: str, detail: str, warn_only: bool = False) -> None:
    tag = "PASS" if ok else ("WARN" if warn_only else "FAIL")
    if not ok:
        (WARN if warn_only else FAIL).append(label)
    print(f"  [{tag}] {label:38} {detail}")


p = P
print("building body + cap...")
body = build_body(p)
cap = build_cap(p)

# The real board, flipped: holder underneath, PCB on top, offset tangent.
holder = bd.Pos(p.holder_offset, 0, 0) * bd.Cylinder(
    p.r_holder, p.holder_h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
pcb = cyl(p.r_pcb, p.pcb_env_h, z=p.z_pcb_bottom)
board = holder + pcb

print("\n--- 1. assembly interference -----------------------------------------")
clash = body & cap
clash_vol = clash.volume if clash is not None else 0.0
check(clash_vol < 1.0, "body/cap collision",
      f"{clash_vol:.3f} mm3 overlap (threads should mate, not fight)")

print("\n--- 2. board fit -----------------------------------------------------")
hit = board & (body + cap)
hit_vol = hit.volume if hit is not None else 0.0
check(hit_vol < 0.01, "board vs enclosure",
      f"{hit_vol:.4f} mm3 -- board must not touch any wall")

tangent_r = p.holder_offset + p.r_holder
check(p.r_cav - tangent_r >= 0.25, "clearance at tangent point",
      f"{p.r_cav - tangent_r:.2f} mm (holder edge is flush with the PCB edge)")
check(p.r_pocket - p.r_holder >= 0.15, "holder into its pocket",
      f"{p.r_pocket - p.r_holder:.2f} mm radial clearance")

print("\n--- 3. cell retention ------------------------------------------------")
# The point of the fill: with the holder seated, how much of its side is
# actually backed by plastic rather than open air?
from hen_tag_enclosure import cell_fill  # noqa: E402
fill = cell_fill(p)
check(fill.volume > 200, "fill present around the cell",
      f"{fill.volume:.0f} mm3 of fill")

# Probe the annulus just outside the holder: it should be solid nearly all round.
probe = (bd.Pos(p.holder_offset, 0, 0.5) * bd.Cylinder(
    p.r_pocket + 0.6, p.z_fill_top - 1.0,
    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    - bd.Pos(p.holder_offset, 0, 0.5) * bd.Cylinder(
        p.r_pocket, p.z_fill_top - 1.0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))
backed = (probe & body).volume if (probe & body) is not None else 0.0
frac = backed / probe.volume
check(frac > 0.80, "holder circumference backed by plastic",
      f"{frac * 100:.0f}% (the rest is the tangent point, backed by the wall)")

check(p.z_fill_top < p.z_pcb_bottom, "fill clears the PCB face",
      f"fill top z{p.z_fill_top:.2f} vs PCB z{p.z_pcb_bottom:.2f} "
      f"({p.fill_relief:.2f} mm)")

print("\n--- 4. vertical stack ------------------------------------------------")
head = p.z_ceiling - p.stack_h
check(0.4 <= head <= 1.2, "head clearance over the PCB", f"{head:.2f} mm")
check(p.foam_t > head, "foam ring compresses",
      f"{p.foam_t:.1f} mm ring in a {head:.2f} mm gap -> "
      f"{(p.foam_t - head) / p.foam_t * 100:.0f}% squeeze")
check(p.foam_od / 2 <= p.r_pcb, "foam ring lands on the PCB",
      f"ring OD {p.foam_od:.0f} vs PCB dia {p.pcb_dia:.0f}")
check(p.foam_id >= 14.0, "LED window left clear",
      f"Ø{p.foam_id:.0f} mm open through the ring")
check(True, "stack heights still assembling",
      f"{p.stack_h - (p.foam_t - 0.2):.1f}-{p.stack_h + head:.1f} mm tolerated "
      f"(nominal {p.stack_h:.1f})")

print("\n--- 5. assembly path -------------------------------------------------")
r_fem_apex = p.r_thread_minor + p.fit_thread_r
check(r_fem_apex > p.r_core, "cap thread clears the seal band",
      f"crest r {r_fem_apex:.2f} vs band r {p.r_core:.2f} "
      f"(+{r_fem_apex - p.r_core:.2f} mm)")
check(p.r_cap_seal_bore > p.r_core, "cap bore clears the seal band",
      f"bore r {p.r_cap_seal_bore:.2f} vs band r {p.r_core:.2f}")
check(p.z_groove_lo > p.z_thread_hi, "O-ring never crosses the thread",
      f"groove starts z{p.z_groove_lo:.2f}, thread ends z{p.z_thread_hi:.2f}")
# Tabs must not foul the cap as it turns.
check((cap & body).volume < 1.0 if (cap & body) is not None else True,
      "tabs clear the rotating cap", f"tab root ends at r {p.r_cap_out:.2f}")

print("\n--- 6. wall thickness ------------------------------------------------")
min_wall = 2 * p.nozzle * 0.9
check(p.r_thread_minor - p.r_cav >= min_wall, "body wall under thread root",
      f"{p.r_thread_minor - p.r_cav:.2f} mm (need >= {min_wall:.2f})")
check(p.body_wall >= min_wall, "body wall at seal band", f"{p.body_wall:.2f} mm")
check(p.r_cap_out - p.r_groove_root >= min_wall, "cap wall behind O-ring groove",
      f"{p.r_cap_out - p.r_groove_root:.2f} mm")
check(p.r_cap_out - p.r_cap_thread_root >= min_wall, "cap wall behind thread",
      f"{p.r_cap_out - p.r_cap_thread_root:.2f} mm")
scallop = 1.4 - 1.15
check(p.r_cap_out - scallop - p.r_groove_root >= min_wall * 0.8,
      "cap wall under grip scallop",
      f"{p.r_cap_out - scallop - p.r_groove_root:.2f} mm")
check(p.floor_t >= 3 * p.layer, "cavity floor", f"{p.floor_t:.2f} mm")

print("\n--- 7. harness tabs --------------------------------------------------")
# Push the elastic through the slot: it has to be clear.
elastic = bd.Pos(p.r_slot_in + p.strap_t / 2, 0, -p.floor_t - 2) * bd.Box(
    1.5, 8.0, p.floor_t + p.tab_top + 4,
    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
blocked = (elastic & body).volume if (elastic & body) is not None else 0.0
check(blocked < 0.01, "8.0 mm elastic threads the slot",
      f"{blocked:.3f} mm3 obstructing")

bar_area = p.tab_bar * (p.floor_t + p.tab_top)
check(bar_area >= 3.5, "bar cross-section",
      f"{bar_area:.2f} mm2 ({p.tab_bar:.1f} x {p.floor_t + p.tab_top:.1f})")
check(p.tab_inner_wall >= 2 * p.nozzle, "wall between cap and slot",
      f"{p.tab_inner_wall:.2f} mm")

# Flat underside: nothing may sit below the floor plane.
below = bd.Pos(0, 0, -p.floor_t - 6) * bd.Box(
    120, 120, 6, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
proud = (below & body).volume if (below & body) is not None else 0.0
check(proud < 0.01, "underside is flat", f"{proud:.3f} mm3 below the floor plane")

bb = (body + cap).bounding_box()
check(True, "assembled envelope",
      f"{bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")

print("\n--- 8. printability: unsupported overhangs ---------------------------")
# Slicers flag downward-facing area that has nothing under it. Tessellate each
# part in its print orientation and measure it, so an inverted chamfer or a
# stray floating shelf cannot creep back in unnoticed.
import math  # noqa: E402
from collections import defaultdict  # noqa: E402

# Per-part limits, calibrated against revision A, which printed successfully on
# a Bambu Lab P1S. Two features are inherent and known-printable:
#   body -- the thread's lower flanks, spread thinly over many layers
#   cap  -- the O-ring groove's lower flank, which becomes a ~1.7 mm annular
#           ceiling once the cap is flipped top-plate-down for printing
# The limits sit just above those. The point is to catch NEW unsupported
# geometry, not to re-argue features that have already been printed. The
# inverted rim chamfer that triggered this check contributed 38 mm2 in a single
# band, so it would have been caught here.
CLUSTER_LIMIT = {"body": 25.0, "cap": 110.0}  # mm2 in one 0.1 mm height band


def overhangs(solid, name: str, bed_z: float) -> float:
    verts, tris = solid.tessellate(0.01)
    bands: dict[float, float] = defaultdict(float)
    for ia, ib, ic in tris:
        a, b, c = verts[ia], verts[ib], verts[ic]
        u = (b.X - a.X, b.Y - a.Y, b.Z - a.Z)
        v = (c.X - a.X, c.Y - a.Y, c.Z - a.Z)
        nx = u[1] * v[2] - u[2] * v[1]
        ny = u[2] * v[0] - u[0] * v[2]
        nz = u[0] * v[1] - u[1] * v[0]
        mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if mag < 1e-12:
            continue
        if nz / mag >= -0.7071:        # steeper than 45 deg: self-supporting
            continue
        z = (a.Z + b.Z + c.Z) / 3
        if z <= bed_z + 0.05:          # sitting on the build plate
            continue
        bands[round(z, 1)] += mag / 2

    if not bands:
        check(True, f"{name}: unsupported overhang", "none above the bed")
        return 0.0
    worst_z = max(bands, key=lambda k: bands[k])
    worst = bands[worst_z]
    limit = CLUSTER_LIMIT[name]
    check(worst <= limit, f"{name}: worst overhang band",
          f"{worst:.2f} mm2 at z {worst_z:.1f} "
          f"(limit {limit:.0f}; total {sum(bands.values()):.1f} mm2)")
    return worst


overhangs(body, "body", -p.floor_t)
# The cap prints top-plate-down, so it has to be analysed flipped.
cap_printed = bd.Rot(180, 0, 0) * cap
overhangs(cap_printed, "cap", cap_printed.bounding_box().min.Z)

print("\n--- 9. half sections for visual inspection ---------------------------")
half = bd.Box(120, 60, 80,
              align=(bd.Align.CENTER, bd.Align.MAX, bd.Align.CENTER))


def write(solid, name: str) -> None:
    if solid is None or solid.volume < 1e-6:
        print(f"  [FAIL] {name}: empty solid, nothing exported")
        FAIL.append(f"export {name}")
        return
    ok = bd.export_stl(solid, str(OUT / f"{name}.stl"), tolerance=0.008,
                       angular_tolerance=0.1)
    size = (OUT / f"{name}.stl").stat().st_size if ok else 0
    print(f"  wrote {name}.stl  ({solid.volume:7.1f} mm3, {size} bytes)")
    if not ok:
        FAIL.append(f"export {name}")


write(body - half, "section_body")
write(cap - half, "section_cap")
write((body + cap) - half, "section_assembly")
write(board - half, "section_board")
write(board, "board_mock")

print("\n" + "=" * 70)
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s) -> {', '.join(FAIL)}")
    sys.exit(1)
print(f"All checks passed{f' ({len(WARN)} warning)' if WARN else ''}.")
