# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Full keeper collar, bench prototype v1 -- two clamshell halves plus a demo
halo accessory. Built on the verified coupon parameters in
hen_tag_platform.py; nothing here has been printed.

v1 is designed to print support-free, upright, as installed: every feature
grows from the bed or overhangs less than 1 mm (bridges excepted).
  - parting plane x = 0, so each half carries ONE whole tab window and is
    captive on that tab; the halves close along X
  - the wall starts at the bead's lower face, so the bead sits on the bed
  - no shoulder pads (they floated 2.8 mm above the bed); the deck lip over
    the cap rim and the bead in the flange groove carry the vertical load
  - joint = a vertical tongue standing on the bed (+Y end) into a slot open
    at the bottom (-Y end), with a vertical detent rib; halves close along X
  - bayonet channels are open down to the deck, so the accessory's lugs are
    flush with its bed face; a radial detent bump sits at the channel root
"""
from __future__ import annotations

import math

import build123d as bd

from hen_tag_enclosure import OUT, PETG_DENSITY, P, build_cap, cyl, ring, sector
from hen_tag_platform import PP, build_body_platform

p, pp = P, PP

R_IN = pp.r_bore(p)                # 16.22
R_OUT = pp.r_out(p)                # 17.77
Z_BOT = pp.bead_z                  # -0.45: bead flush with the bed
Z_DECK = pp.z_deck(p)              # 7.85
Z_TOP = Z_DECK + pp.deck_t         # 9.05

WIN_W = 13.40                      # window over each tab

# joint boss + tongue/slot at +/-Y
BOSS_X = 4.0
BOSS_R = 20.2
TONGUE_W, TONGUE_L, TONGUE_Z1 = 1.8, 3.5, 6.0
TONGUE_Y = 18.1                    # centre
FIT = 0.15
RIB_R, RIB_D, GROOVE_D = 0.5, 0.20, 0.30

# bayonet
BAY_H = 2.4
BAY_R_IN, BAY_R_OUT = pp.bay_r_in, pp.bay_r_out     # 16.2 .. 17.8
CH_ROOT = 16.85                    # channel root radius
CH_Z0, CH_Z1 = Z_TOP, Z_TOP + 1.40  # open down to the deck
ENTRY_DEG, TRAVEL_DEG = 14.0, 45.0
ENTRIES = (60.0, 180.0, 300.0)
DETENT_DEG = TRAVEL_DEG - 8.0

# accessory (halo ring), prints upright: ring and lugs share the bed face
ACC_Z0 = Z_TOP + 0.10
ACC_R_IN, ACC_R_OUT = BAY_R_OUT + 0.20, 20.0
ACC_Z1 = Z_TOP + BAY_H + 0.20
LUG_DEG, LUG_R0 = 8.0, CH_ROOT + 0.10
LUG_Z1 = CH_Z1 - 0.20


def box(x0, x1, y0, y1, z0, z1) -> bd.Solid:
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * bd.Box(
        x1 - x0, y1 - y0, z1 - z0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def zcyl(x, y, r, z0, z1) -> bd.Solid:
    return bd.Pos(x, y, z0) * bd.Cylinder(
        r, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def bayonet_ring() -> bd.Solid:
    rg = ring(BAY_R_OUT, BAY_R_IN, BAY_H, z=Z_TOP)
    for e in ENTRIES:
        a0 = e - ENTRY_DEG / 2
        # vertical entry notch, open at the top
        rg -= sector(BAY_R_OUT + 1, CH_ROOT, a0, a0 + ENTRY_DEG,
                     BAY_H + 1, z=CH_Z0)
        # horizontal channel, CCW travel, open to the deck
        rg -= sector(BAY_R_OUT + 1, CH_ROOT, a0, a0 + ENTRY_DEG + TRAVEL_DEG,
                     CH_Z1 - CH_Z0, z=CH_Z0)
        # radial detent bump at the channel root, 1.5 deg wide
        d = e + DETENT_DEG
        rg += sector(CH_ROOT + 0.20, CH_ROOT - 0.10, d - 0.75, d + 0.75,
                     CH_Z1 - CH_Z0, z=CH_Z0)
    return rg


def build_half_base() -> bd.Solid:
    """Half at x <= 0 without the bayonet ring: carries the -X tab window,
    tongue at +Y, slot at -Y. Half B is this rotated 180 deg about Z."""
    h = ring(R_OUT, R_IN, Z_TOP - Z_BOT, z=Z_BOT)                    # wall
    h += ring(R_OUT, pp.lip_r_in, pp.deck_t, z=Z_DECK)               # deck
    h += ring(R_IN, p.r_cap_out - pp.bead_d, pp.bead_w, z=pp.bead_z) # bead
    # tab window, full height below the deck
    h -= box(-30, -10, -WIN_W / 2, WIN_W / 2, Z_BOT - 1, Z_DECK)
    # joint bosses, standing on the bed
    for s in (1, -1):
        y0, y1 = sorted((s * (R_IN + 0.5), s * BOSS_R))
        h += box(-BOSS_X, BOSS_X, y0, y1, Z_BOT, Z_TOP) - cyl(R_IN, 20, -5)
    # spring finger at 135 deg: two slits + bump
    fz0, fz1 = pp.finger_z_lo, pp.finger_z_hi
    for a in (135 - 13.5, 135 + 13.5):
        h -= sector(R_OUT + 1, R_IN - 1, a - 1.4, a + 1.4, fz1 - fz0, z=fz0)
    c = math.radians(135)
    bz = (fz0 + fz1) / 2
    bump = bd.Pos((R_IN - pp.finger_bump_d + pp.finger_bump_r) * math.cos(c),
                  (R_IN - pp.finger_bump_d + pp.finger_bump_r) * math.sin(c),
                  bz) * bd.Sphere(pp.finger_bump_r)
    h += bump & ring(R_IN, R_IN - pp.finger_bump_d, 3, z=bz - 1.5)
    # keep x <= 0
    h &= box(-40, 0, -40, 40, -5, 20)
    # tongue at +Y, standing on the bed, protruding into x > 0
    ty0, ty1 = TONGUE_Y - TONGUE_W / 2, TONGUE_Y + TONGUE_W / 2
    h += box(-1, TONGUE_L, ty0, ty1, Z_BOT, TONGUE_Z1)
    rib_x = TONGUE_L - 1.0
    h += zcyl(rib_x, ty1, RIB_R, Z_BOT, TONGUE_Z1) & box(
        rib_x - 1, rib_x + 1, ty1, ty1 + RIB_D, Z_BOT, TONGUE_Z1)
    # slot at -Y, open at the bottom, for the other half's tongue
    sy0, sy1 = -ty1 - FIT, -ty0 + FIT
    h -= box(-TONGUE_L - 0.3, 0.01, sy0, sy1, Z_BOT - 1, TONGUE_Z1 + FIT)
    h -= zcyl(-rib_x, sy0, RIB_R + 0.1, Z_BOT - 1, TONGUE_Z1 + FIT) & box(
        -rib_x - 1, -rib_x + 1, sy0 - GROOVE_D, sy0, Z_BOT - 1,
        TONGUE_Z1 + FIT)
    return h


def build_halves() -> tuple[bd.Solid, bd.Solid]:
    """The 3 J-slots are not 180-deg symmetric, so the ring is cut in global
    coordinates and split between the halves: A (x<0) and B (x>0) differ
    only in where their ring notches fall."""
    base = build_half_base()
    rg = bayonet_ring()
    a = base + (rg & box(-40, 0, -40, 40, -5, 20))
    b = (bd.Rot(0, 0, 180) * base) + (rg & box(0, 40, -40, 40, -5, 20))
    return a, b


def build_halo() -> bd.Solid:
    a = ring(ACC_R_OUT, ACC_R_IN, ACC_Z1 - ACC_Z0, z=ACC_Z0)
    for e in ENTRIES:
        a += sector(ACC_R_IN + 0.01, LUG_R0, e - LUG_DEG / 2, e + LUG_DEG / 2,
                    LUG_Z1 - ACC_Z0, z=ACC_Z0)
    return a


def main() -> None:
    body = build_body_platform(p, pp)
    cap = build_cap(p)
    half_a, half_b = build_halves()
    halo = build_halo()
    halo_seated = bd.Rot(0, 0, TRAVEL_DEG) * halo

    print(f"{'part':14} {'valid':>6} {'mass':>8}   bbox")
    for n, s in (("collar_half_a", half_a), ("collar_half_b", half_b),
                 ("halo", halo)):
        b = s.bounding_box()
        print(f"{n:14} {str(s.is_valid):>6} {s.volume * PETG_DENSITY:6.2f} g  "
              f"{b.size.X:.1f} x {b.size.Y:.1f} x {b.size.Z:.1f}")
    checks = {
        "half A vs body": (half_a & body).volume,
        "half B vs body": (half_b & body).volume,
        "half A vs cap": (half_a & cap).volume,
        "half B vs cap": (half_b & cap).volume,
        "half A vs half B": (half_a & half_b).volume,
        "halo (entry) vs collar": (halo & (half_a + half_b)).volume,
        "halo (seated) vs collar": (halo_seated & (half_a + half_b)).volume,
    }
    for k, v in checks.items():
        print(f"  {k:26} {v:8.4f} mm3")
    low = min(half_a.bounding_box().min.Z, half_b.bounding_box().min.Z)
    print(f"  collar lowest point vs floor plane: {low + p.floor_t:+.2f} mm")
    print(f"  collar pair mass: {2 * half_a.volume * PETG_DENSITY:.2f} g")

    OUT.mkdir(exist_ok=True)
    exports = {
        "collar_half_a": half_a,
        "collar_half_b": half_b,
        "halo_accessory": halo,
        "asm_body_platform": body,
        "asm_cap": cap,
        "asm_collar_half_a": half_a,
        "asm_collar_half_b": half_b,
        "asm_halo_seated": halo_seated,
    }
    for n, s in exports.items():
        solid = s
        if not n.startswith("asm_"):
            solid = bd.Pos(0, 0, -s.bounding_box().min.Z) * s
            bd.export_step(s, str(OUT / f"{n}.step"))
        bd.export_stl(solid, str(OUT / f"{n}.stl"),
                      tolerance=0.008, angular_tolerance=0.1)
    print("exported")


if __name__ == "__main__":
    main()
