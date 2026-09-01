# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d", "bd_warehouse"]
# ///
"""Accessory platform parts -- keeper collar coupons + platform body variant.

    uv run --python 3.12 hen_tag_platform.py

Separate from the shipping design on purpose: `hen_tag_enclosure.py` is
imported, never modified, and still builds the exact same body and cap. This
file adds the parts described in `../platform/`:

    body_platform     the body with ONE extra cut: a lateral retention
                      groove on the base-flange OD. Thread, seal band,
                      cavity, tabs, flat underside: untouched.
    coupon_collar     120 deg segment of the keeper collar's working zone:
                      bore, bottom retention bead, spring finger, deck +
                      lip, bayonet ring blank. Prints standing, ~15 min.
    coupon_flangering base slice of body_platform (flange + groove + tab
                      roots), ~8 min. Mates with coupon_collar to settle
                      bore fit and bead click before any full part.

THE CAP IS NEVER TOUCHED. The personalised transparent cap (lettering, LED
window) stays exactly as shipped and is never replaced: the collar retains
itself on the BODY -- its bead enters the flange groove laterally as the
clamshell closes (positive up/down lock, zero flexing), its windows key on
the harness tabs (rotation lock), and every accessory load routes
collar -> body -> harness, bypassing the cap thread entirely. A first
iteration put this groove on the cap OD; rejected 2026-08-30 because it
would have meant reprinting personalised caps. Existing bodies accept the
collar in friction-only mode for bench work; a deployable fit wants the
grooved body, swapped in at a normal battery service while the personal cap
carries over unchanged.

Nothing here has been printed. Status: coupon stage.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import build123d as bd

from hen_tag_enclosure import (OUT, PETG_DENSITY, P, Params, build_body,
                               build_cap, cyl, ring)


# --- platform parameters -----------------------------------------------------
@dataclass(frozen=True)
class PlatformParams:
    # Collar fit and shell
    fit_collar: float = 0.25   # radial, collar bore over the cap skirt
    wall: float = 1.55         # >= 3 perimeters at 0.4 nozzle
    z_bottom: float = -0.60    # collar lower edge: 0.40 ABOVE the floor plane
    deck_gap: float = 0.15     # deck underside clearance over the cap face
    deck_t: float = 1.20
    lip_r_in: float = 15.55    # deck lip inner radius; lettering ends at 15.4

    # Flange OD retention groove (body_platform) and the mating bead
    groove_z: float = -0.55    # groove spans z -0.55 .. 0.00
    groove_w: float = 0.55
    groove_d: float = 0.50     # root at r_cap_out - 0.50 = 15.47
    bead_z: float = -0.45      # bead spans z -0.45 .. -0.10 (0.10 play each way)
    bead_w: float = 0.35
    bead_d: float = 0.35       # radial engagement under the groove's flank

    # Spring finger clicking into a stock grip scallop (bonus cap lock; the
    # load path no longer needs the cap, so partial engagement is fine)
    finger_span: float = 24.0
    finger_slit: float = 0.80
    finger_z_lo: float = 4.00
    finger_z_hi: float = 6.50
    finger_bump_r: float = 1.20
    finger_bump_d: float = 0.30   # stock scallops are 0.25 deep

    # Bayonet ring blank (slots come with the full collar, not the coupon)
    bay_r_in: float = 16.20
    bay_r_out: float = 17.80
    bay_h: float = 1.60

    def r_bore(self, p: Params) -> float:
        return p.r_cap_out + self.fit_collar

    def r_out(self, p: Params) -> float:
        return self.r_bore(p) + self.wall

    def z_face(self, p: Params) -> float:
        """Cap outer face in design coordinates."""
        return p.z_ceiling + p.cap_top_t

    def z_deck(self, p: Params) -> float:
        return self.z_face(p) + self.deck_gap


PP = PlatformParams()


# --- helpers -----------------------------------------------------------------
def sector(span_deg: float, height: float, z: float, r_reach: float = 60.0,
           mid_deg: float = 0.0) -> bd.Solid:
    """Triangular prism covering the angular sector, for intersections."""
    half = math.radians(span_deg / 2)
    mid = math.radians(mid_deg)
    pts = [(0.0, 0.0)]
    for a in (mid - half, mid + half):
        pts.append((r_reach * math.cos(a), r_reach * math.sin(a)))
    return bd.Pos(0, 0, z) * bd.extrude(bd.Polygon(*pts, align=None),
                                        amount=height)


# --- parts -------------------------------------------------------------------
def build_body_platform(p: Params = P, pp: PlatformParams = PP) -> bd.Solid:
    """The shipping body + the flange-OD retention groove. Nothing else.

    The groove root is backed by the solid floor disc (2.7 mm of material to
    the cavity), and on the floor-down print its ceiling is a 0.5 mm overhang
    ring -- far smaller than the O-ring groove flank the cap already prints.
    """
    body = build_body(p)
    body -= ring(p.r_cap_out + 0.20, p.r_cap_out - pp.groove_d,
                 pp.groove_w, z=pp.groove_z)
    return body


def build_coupon_collar(p: Params = P, pp: PlatformParams = PP) -> bd.Solid:
    """120 deg of the collar's working zone, centred BETWEEN the tabs
    (mid 90 deg): the wall descends past the tab plane, so at tab azimuths
    the real collar has full-height windows instead of wall."""
    r_in, r_out = pp.r_bore(p), pp.r_out(p)
    z_deck = pp.z_deck(p)
    z_top = z_deck + pp.deck_t

    seg = ring(r_out, r_in, z_top - pp.z_bottom, z=pp.z_bottom)      # wall
    seg += ring(r_out, pp.lip_r_in, pp.deck_t, z=z_deck)             # deck+lip
    seg += ring(pp.bay_r_out, pp.bay_r_in, pp.bay_h, z=z_top)        # bay blank

    # Bottom retention bead: enters the flange groove laterally as the
    # clamshell closes -- no snap-over, no flexing, zero-fatigue lock.
    seg += ring(r_in, p.r_cap_out - pp.bead_d, pp.bead_w, z=pp.bead_z)

    # Spring finger: two vertical slits free a strip of wall; a bump at its
    # tip clicks into the nearest stock grip scallop.
    for s in (-1, 1):
        slit_mid = 90 + (pp.finger_span / 2 + 1.5) * s
        seg -= sector(pp.finger_slit / (math.pi * r_in / 180) * 90,
                      pp.finger_z_hi - pp.finger_z_lo, pp.finger_z_lo,
                      mid_deg=slit_mid) & ring(r_out + 1, r_in - 1,
                                              pp.finger_z_hi - pp.finger_z_lo,
                                              z=pp.finger_z_lo)
    bump_z = (pp.finger_z_lo + pp.finger_z_hi) / 2
    seg += (bd.Pos(0, r_in - pp.finger_bump_d + pp.finger_bump_r, bump_z) *
            bd.Sphere(pp.finger_bump_r)) & ring(r_in, r_in - pp.finger_bump_d,
                                                pp.finger_z_hi - bump_z,
                                                z=bump_z)

    seg &= sector(120, z_top + pp.bay_h - pp.z_bottom + 1, pp.z_bottom,
                  mid_deg=90)
    return seg


def build_coupon_flangering(p: Params = P, pp: PlatformParams = PP) -> bd.Solid:
    """Base slice of body_platform: flange, groove and the tab roots."""
    body = build_body_platform(p, pp)
    return body & ring(21.0, 12.0, 1.60, z=-p.floor_t)


# --- report + export ---------------------------------------------------------
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p, pp = P, PP

    print("=" * 74)
    print("HEN TAG PLATFORM  --  keeper collar coupons + platform body variant")
    print("=" * 74)
    print("  THE CAP IS UNTOUCHED: retention is on the body flange")
    print(f"  collar bore        r {pp.r_bore(p):.2f}  (skirt {p.r_cap_out:.2f}"
          f" + fit {pp.fit_collar})")
    print(f"  collar OD          {2 * pp.r_out(p):.2f} mm  "
          f"(tab span is {2 * p.r_tab_out:.2f})")
    print(f"  collar lower edge  z {pp.z_bottom:.2f}  "
          f"({pp.z_bottom + p.floor_t:.2f} above the floor plane)")
    print(f"  deck / lip         z {pp.z_deck(p):.2f}, lip to r {pp.lip_r_in}"
          f"  (lettering ends r 15.40)")
    print(f"  flange groove      z {pp.groove_z:.2f}..{pp.groove_z + pp.groove_w:.2f},"
          f" depth {pp.groove_d}  (body_platform only)")
    print(f"  bead engagement    {pp.bead_d} radial, "
          f"{(pp.groove_w - pp.bead_w) / 2:.2f} axial play each way")

    print("\nbuilding...")
    parts = {
        "body_platform": build_body_platform(p, pp),
        "coupon_collar": build_coupon_collar(p, pp),
        "coupon_flangering": build_coupon_flangering(p, pp),
    }

    print(f"\n{'part':18} {'valid':>6} {'volume':>11} {'mass':>9}   bbox (mm)")
    print("-" * 74)
    for name, solid in parts.items():
        m = solid.volume * PETG_DENSITY
        b = solid.bounding_box()
        print(f"{name:18} {str(solid.is_valid):>6} {solid.volume:9.1f} mm3 "
              f"{m:6.2f} g   {b.size.X:.1f} x {b.size.Y:.1f} x {b.size.Z:.1f}")

    # Machine checks: the variant only removes material; the collar clears
    # body, cap and the hen (nothing below the floor plane).
    base = build_body(p)
    plat = parts["body_platform"]
    grown = (plat - base).volume
    collar = parts["coupon_collar"]
    cap = build_cap(p)
    print("-" * 74)
    print(f"  body_platform vs body: removed {base.volume - plat.volume:7.1f} mm3,"
          f" added {grown:.1f} mm3 (must be 0.0)")
    print(f"  collar vs body_platform interference: "
          f"{(collar & plat).volume:.4f} mm3 (must be 0)")
    print(f"  collar vs cap interference:           "
          f"{(collar & cap).volume:.4f} mm3 (must be 0)")
    below = collar.bounding_box().min.Z - (-p.floor_t)
    print(f"  collar lowest point vs floor plane:   +{below:.2f} mm (must be > 0)")

    FLIP = {"coupon_flangering"}
    print()
    for name, solid in parts.items():
        oriented = bd.Rot(180, 0, 0) * solid if name in FLIP else solid
        oriented = bd.Pos(0, 0, -oriented.bounding_box().min.Z) * oriented
        bd.export_stl(oriented, str(OUT / f"{name}.stl"),
                      tolerance=0.008, angular_tolerance=0.1)
        bd.export_step(solid, str(OUT / f"{name}.step"))
        note = "  (flipped for printing)" if name in FLIP else ""
        print(f"  exported {name}.stl / .step{note}")

    print("\nbench checklist (record in a dated lab note):")
    print("  1. print coupon_flangering + coupon_collar, same profile as body")
    print("  2. bore fit over the flange ring: light slide, no rock")
    print("  3. bead clicks into the groove laterally; no lift by hand pull")
    print("  4. finger clicks into a stock 0.25 scallop on a printed cap;")
    print("     note the force (bonus lock only -- loads bypass the cap)")
    print("  5. print body_platform, move a board + the personal cap over,")
    print("     hold two coupon_collar segments closed: pull >= 30 N up,")
    print("     accessory-torque 3x cap break-loose -> no motion anywhere")


if __name__ == "__main__":
    main()
