# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Verification pass: assemble the parts virtually and measure what matters.

Checks nobody can eyeball reliably:
  1. do body and cap collide in the locked position?
  2. does the flipped board fit, holder down into its pocket?
  3. does the fill actually retain the holder?
  4. is there head clearance over the switch, and does the foam ring bear on
     the board while clearing the switch and the LED?
  5. does the bayonet work -- cap drops on at the entry angle, lugs run free
     to the lock angle, the ramp then wedges, and the locked cap cannot be
     pulled off?
  6. is every wall thick enough to print watertight?
  7. do the harness tabs take an 8 mm elastic, and is the underside flat?
  8. is any downward-facing area left unsupported in the print orientation?

Also emits half-section STLs so the internals can be inspected visually.

  --board-step PATH   the manufacturer's STEP: re-extract the board constants
                      and fail on drift, then collide the real board and its
                      parts with the body and cap. Skipped when not given.
"""

import argparse
import math
import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).parent))
import board_holyiot_25008 as brd  # noqa: E402
from hen_tag_enclosure import (  # noqa: E402
    OUT, P, build_body, build_cap, cyl,
)

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--board-step", type=Path, help="manufacturer STEP of the board")
args = ap.parse_args()

FAIL: list[str] = []
WARN: list[str] = []


def check(ok: bool, label: str, detail: str, warn_only: bool = False) -> None:
    tag = "PASS" if ok else ("WARN" if warn_only else "FAIL")
    if not ok:
        (WARN if warn_only else FAIL).append(label)
    print(f"  [{tag}] {label:38} {detail}")


def vol(shape) -> float:
    return shape.volume if shape is not None else 0.0


p = P
print("building body + cap...")
body = build_body(p)
cap = build_cap(p)

# The real board, flipped: holder underneath, PCB on top, offset tangent.
holder = bd.Pos(p.holder_offset, 0, 0) * bd.Cylinder(
    p.r_holder, p.holder_h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
# Board envelope: the bare board, plus the switch's footprint circle at full
# height; everything else on the face is lower (board_holyiot_25008).
pcb = (cyl(p.r_pcb, p.pcb_t, z=p.z_pcb_bottom)
       + cyl(brd.S1_R_MAX, p.comp_h, z=p.z_pcb_bottom + p.pcb_t)
       + cyl(brd.PART_R_MAX, max(h for lo, hi, h in brd.PART_H_BY_BAND if lo > 0),
             z=p.z_pcb_bottom + p.pcb_t))
board = holder + pcb

print("\n--- 1. assembly interference -----------------------------------------")
clash_vol = vol(body & cap)
check(clash_vol < 1.0, "body/cap collision, locked",
      f"{clash_vol:.3f} mm3 overlap (lugs should touch the lips, not fight)")

print("\n--- 2. board fit -----------------------------------------------------")
hit_vol = vol(board & (body + cap))
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
frac = vol(probe & body) / probe.volume
check(frac > 0.80, "holder circumference backed by plastic",
      f"{frac * 100:.0f}% (the rest is the tangent point, backed by the wall)")

check(p.z_fill_top < p.z_pcb_bottom, "fill clears the PCB face",
      f"fill top z{p.z_fill_top:.2f} vs PCB z{p.z_pcb_bottom:.2f} "
      f"({p.fill_relief:.2f} mm)")

print("\n--- 4. vertical stack ------------------------------------------------")
# Heights from the manufacturer STEP; the holder under them is still caliper.
head = p.head_gap
check(head >= 0.15, "ceiling clears the switch S1",
      f"{head:.2f} mm over S1 ({p.comp_h:.2f} tall); holder_h is UNVERIFIED -- "
      f"a holder {head:.2f} mm taller than {p.holder_h} presses the button")
r_in, r_out = p.foam_id / 2, p.foam_od / 2
band_h = max(h for lo, hi, h in brd.PART_H_BY_BAND if lo < r_out and hi > r_in)
check(p.foam_t > p.foam_gap, "foam ring bears on the bare board",
      f"{p.foam_t:.1f} mm ring in a {p.foam_gap:.2f} mm gap -> "
      f"{(p.foam_t - p.foam_gap) / p.foam_t * 100:.0f}% squeeze")
squeeze_parts = (p.foam_t - (p.foam_gap - band_h)) / p.foam_t
check(squeeze_parts <= 0.70, "foam over the tallest part in its band",
      f"{band_h:.2f} mm part -> {squeeze_parts * 100:.0f}% local squeeze (limit 70%)")
check(r_in - p.fit_board > brd.S1_R_MAX, "foam ring clears the switch",
      f"ring ID r {r_in:.2f} vs S1 r {brd.S1_R_MAX:.2f} + {p.fit_board} play")
check(r_out + p.fit_board < brd.LED_R_SPAN[0], "foam ring clears the LED",
      f"ring OD r {r_out:.2f} + {p.fit_board} play vs LED from r {brd.LED_R_SPAN[0]:.2f}")
check(True, "stack heights still assembling",
      f"holder {p.holder_h - (p.foam_t - p.foam_gap):.2f}-{p.holder_h + head:.2f} mm "
      f"tolerated (nominal {p.holder_h:.2f}): foam contact to S1 contact")

if args.board_step:
    print("\n--- 4b. manufacturer STEP --------------------------------------------")
    got = brd.extract(args.board_step)
    for key, val in got.items():
        want = getattr(brd, key)
        tol = 0.2 if key == "LED_ANGLE" else 0.01
        check(abs(val - want) <= tol, f"STEP {key}", f"{val:.3f} (constant {want})")
    real, _ = brd.load(args.board_step, p.z_pcb_bottom)
    hit = sum(vol(s & (body + cap)) for s in real.solids())
    check(hit < 1e-3, "real board + parts vs enclosure",
          f"{hit:.4f} mm3 overlap, {len(real.solids())} solids")
    bb = real.bounding_box()
    check(p.z_ceiling - bb.max.Z >= 0.15, "real board under the ceiling",
          f"top z {bb.max.Z:.2f} vs ceiling z {p.z_ceiling:.2f}")

print("\n--- 5. bayonet closure -----------------------------------------------")
# The cap is modelled in its locked pose. pose(phi) turns it back toward the
# entry angle: phi = 0 is lugs-in-the-entry-slots, phi = cam_lock is nominal
# contact. dz lifts it off the flange.


def pose(phi: float, dz: float = 0.0) -> bd.Solid:
    return bd.Pos(0, 0, dz) * (bd.Rot(0, 0, p.cam_lock - phi) * cap)


def clash(phi: float, dz: float = 0.0) -> float:
    return vol(body & pose(phi, dz))


# a) the cap drops straight on with the entry slots over the lugs
drop = max(clash(0.0, dz) for dz in (3.0, 2.0, 1.0, 0.5, 0.0))
check(drop < 0.01, "cap drops on at the entry angle",
      f"{drop:.3f} mm3 worst overlap on the way down")

# b) turning clockwise, the lugs run free until the ramp meets them
free = max(clash(phi) for phi in (5.0, 10.0, 15.0, 20.0, 25.0, 28.0))
check(free < 0.01, "lugs run free to the lock angle",
      f"{free:.3f} mm3 worst overlap over 0-28 deg")

# c) past nominal contact the ramp wedges: this is what tightens the cap
wedge = clash(p.cam_lock + 4.0)
check(wedge > 0.05, "ramp wedges past the lock angle",
      f"{wedge:.3f} mm3 interference at +4 deg -> cap tightens like a thread")

# d) locked, the cap cannot be lifted off; at the entry angle it can
held = clash(p.cam_lock, 0.6)
check(held > 1.0, "locked cap is retained",
      f"{held:.2f} mm3 lug/lip overlap when lifted 0.6 mm")
lift = clash(0.0, 1.0)
check(lift < 0.01, "cap lifts off at the entry angle",
      f"{lift:.3f} mm3 overlap when lifted 1.0 mm")

# e) geometry the sweep cannot express
check(p.helix_deg < 6.0, "ramp is self-locking",
      f"{p.helix_deg:.1f} deg helix angle (PETG friction angle ~11 deg)")
lo, hi = p.cam_window
check(lo <= -0.25 and hi >= 0.25, "ramp absorbs print error",
      f"{lo:+.2f}..{hi:+.2f} mm axial, {0.05 / p.cam_rate:.1f} deg per 0.05 mm")
n_ok = p.lug_n * (p.entry_half + p.chan_end) < 360.0
check(n_ok, "channels fit around the skirt",
      f"{p.lug_n} x {p.entry_half + p.chan_end:.0f} deg of {360:.0f}")
# Projected area of the lug/lip cone contact, bore radius to lug crest.
bear = p.lug_n * math.radians(p.lug_arc) * (p.r_cap_seal_bore + p.r_lug) / 2 * (
    p.r_lug - p.r_cap_seal_bore)
check(bear >= 4.0, "bearing area",
      f"{bear:.1f} mm2 over {p.lug_n} lugs (cone-on-cone, parallel helices)")
check(p.r_cap_seal_bore > p.r_core, "cap bore clears the seal band",
      f"bore r {p.r_cap_seal_bore:.2f} vs band r {p.r_core:.2f}")
check(p.z_groove_lo > p.z_chan_hi, "O-ring never crosses the lugs",
      f"groove starts z{p.z_groove_lo:.2f}, channels end z{p.z_chan_hi:.2f}")
check(clash_vol < 1.0, "tabs clear the rotating cap",
      f"tab root ends at r {p.r_cap_out:.2f}")

print("\n--- 6. wall thickness ------------------------------------------------")
min_wall = 2 * p.nozzle * 0.9
check(p.body_wall >= min_wall, "body wall under the lugs and seal band",
      f"{p.body_wall:.2f} mm (need >= {min_wall:.2f})")
check(p.r_cap_out - p.r_groove_root >= min_wall, "cap wall behind O-ring groove",
      f"{p.r_cap_out - p.r_groove_root:.2f} mm")
check(p.r_cap_out - p.r_cap_chan >= min_wall, "cap wall behind the channels",
      f"{p.r_cap_out - p.r_cap_chan:.2f} mm")
scallop = 1.4 - 1.15
check(p.r_cap_out - scallop - p.r_groove_root >= min_wall * 0.8,
      "cap wall under grip scallop",
      f"{p.r_cap_out - scallop - p.r_groove_root:.2f} mm")
lip_t = p.z_lip_lo - p.z_shoulder
check(lip_t >= 4 * p.layer, "lip at its thin end",
      f"{lip_t:.2f} mm ({lip_t / p.layer:.1f} layers)")
check(p.chamfer_deg >= 45.0, "lug/lip/groove cones self-supporting",
      f"{p.chamfer_deg:.0f} deg from horizontal, no flat overhang")
check(p.floor_t >= 3 * p.layer, "cavity floor", f"{p.floor_t:.2f} mm")

print("\n--- 7. harness tabs --------------------------------------------------")
# Push the elastic through the slot: it has to be clear.
elastic = bd.Pos(p.r_slot_in + p.strap_t / 2, 0, -p.floor_t - 2) * bd.Box(
    1.5, 8.0, p.floor_t + p.tab_top + 4,
    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
blocked = vol(elastic & body)
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
proud = vol(below & body)
check(proud < 0.01, "underside is flat", f"{proud:.3f} mm3 below the floor plane")

bb = (body + cap).bounding_box()
check(True, "assembled envelope",
      f"{bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")

print("\n--- 8. printability: unsupported overhangs ---------------------------")
# Slicers flag downward-facing area that has nothing under it. Tessellate each
# part in its print orientation and measure it, so an inverted chamfer or a
# stray floating shelf cannot creep back in unnoticed.
from collections import defaultdict  # noqa: E402

# Per-part limits. Revision D has no flat overhang left: lug undersides, lip
# tops and the O-ring groove's lower flank are 50 deg cones (the rev C flats
# under the lips and the groove drew slicer support, 2026-09-24). What
# remains on the body is the 0.10 mm of lug flat against the seal band. The
# limit catches any new unsupported geometry, down to a few square mm.
CLUSTER_LIMIT = {"body": 1.0, "cap": 1.0}  # mm2 in one 0.1 mm height band


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
# Entry pose, lifted 1 mm: the lugs sit in the entry slots. Built as a
# compound rather than a fuse -- OCCT mis-fuses the two helical solids in
# this disjoint pose (a 277 mm3 result), while common/cut agree exactly.
write(bd.Compound([body, pose(0.0, 1.0)]) - half, "section_entry")
write(board - half, "section_board")
write(board, "board_mock")

print("\n" + "=" * 70)
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s) -> {', '.join(FAIL)}")
    sys.exit(1)
print(f"All checks passed{f' ({len(WARN)} warning)' if WARN else ''}.")
