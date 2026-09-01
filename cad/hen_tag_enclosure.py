# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d", "bd_warehouse"]
# ///
"""Parametric enclosure for the Holyiot 25008 hen tag.

Two-part transparent PETG housing: a cup-shaped body and a screw cap sealed by
a radial O-ring. Run with `uv run hen_tag_enclosure.py` -- uv resolves the
dependencies above, no virtualenv setup required.

Two decisions that are not obvious from the geometry alone:

1. Radial seal, not the axial face seal in docs/requirements.md. A face seal
   must sit outboard of the cap skirt, forcing a ~36 mm flange around a 25 mm
   board; measured, that overruns the mass budget by ~1.9 g. The radial seal
   needs no flange.

2. Thread low, seal high. The reverse -- seal below thread -- cannot assemble:
   the cap's internal thread crests (r 14.00) would have to travel past a
   sealing band of larger radius. With the thread at the bottom, the cap's
   thread only ever passes the smaller seal band, and the O-ring never crosses
   the thread, which would shred it.

MEASUREMENT STATUS -- read before trusting any printed part:
  VERIFIED   the PCB/holder tangency (geometric consequence of 25 and 21 mm)
  UNVERIFIED every dimension marked below; user caliper readings, 2026-08-28
  UNKNOWN    antenna location, elastic cross-section, actual O-ring ID/CS

Coordinate system: Z up, millimetres. z = 0 is the cavity floor -- the surface
the PCB rests on.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import build123d as bd
from bd_warehouse.thread import Thread

OUT = Path(__file__).parent / "out"
PETG_DENSITY = 1.27e-3  # g/mm^3


@dataclass(frozen=True)
class Params:
    """Every dimension the design depends on, in one place."""

    # --- Board, UNVERIFIED (user caliper 2026-08-28) -------------------------
    # Orientation: holder DOWN against the floor, PCB UP under the cap. The
    # LED sits on the PCB face, so it has to look outward, away from the bird.
    pcb_dia: float = 25.0
    pcb_env_h: float = 2.0       # full board envelope incl. components
    holder_dia: float = 21.0
    holder_h: float = 4.0        # holder + seated cell, off the PCB face

    # --- Print process ------------------------------------------------------
    nozzle: float = 0.4
    layer: float = 0.16
    fit_board: float = 0.30      # radial clearance, board edge to cavity wall
    body_wall: float = 0.90
    floor_t: float = 1.00
    cap_wall: float = 1.10
    cap_top_t: float = 1.10

    # --- Thread (trapezoidal; blunter than ISO, far better on FDM) ----------
    thread_pitch: float = 1.0
    thread_angle: float = 30.0   # total included angle
    thread_depth: float = 0.55
    thread_len: float = 2.8
    fit_thread_r: float = 0.25   # radial clearance, male crest to female root
    fit_thread_a: float = 0.15   # axial backlash per flank

    # --- Radial seal, UNVERIFIED (needs the actual ring measured) -----------
    oring_cs: float = 1.50
    oring_squeeze: float = 0.22  # fraction of CS compressed

    # --- Assembly -----------------------------------------------------------
    head_gap: float = 0.60       # ceiling clearance over the PCB, foam-filled
    # Foam is a RING, not a disc: the middle stays clear so the PCB's LED can
    # be read through the transparent cap.
    foam_od: float = 25.0
    foam_id: float = 16.0
    foam_t: float = 1.00
    fit_seal_r: float = 0.10     # slide clearance, cap bore over the seal band

    # --- Cell pocket --------------------------------------------------------
    fit_holder: float = 0.25     # radial clearance, holder to its pocket wall
    fill_relief: float = 0.20    # gap between the fill top and the PCB face

    # --- Harness tabs, UNVERIFIED (8 mm elastic, cross-section not measured)
    # Flat side tabs in the plane of the base, each with a transverse slot and
    # a bar at the tip. The underside of the tag stays completely flat.
    strap_w: float = 8.80        # slot length, across the spine
    strap_t: float = 1.80        # slot width, along the spine
    tab_w: float = 13.00
    tab_top: float = 2.20        # tab upper face, outboard of the cap
    tab_inner_wall: float = 0.80  # material between cap skirt and slot
    tab_bar: float = 1.50        # the bar the elastic wraps around

    # --- Board geometry -----------------------------------------------------
    @property
    def r_pcb(self) -> float:
        return self.pcb_dia / 2

    @property
    def r_holder(self) -> float:
        return self.holder_dia / 2

    @property
    def holder_offset(self) -> float:
        """Centre offset making the two circles internally tangent."""
        return self.r_pcb - self.r_holder

    @property
    def stack_h(self) -> float:
        return self.pcb_env_h + self.holder_h

    # --- Radial stations ----------------------------------------------------
    @property
    def r_cav(self) -> float:
        return self.r_pcb + self.fit_board

    @property
    def r_core(self) -> float:
        """Body outer wall: the plain band the O-ring seals against."""
        return self.r_cav + self.body_wall

    @property
    def r_thread_major(self) -> float:
        return self.r_core + self.thread_depth + 0.05

    @property
    def r_thread_minor(self) -> float:
        return self.r_thread_major - self.thread_depth

    @property
    def r_cap_seal_bore(self) -> float:
        return self.r_core + self.fit_seal_r

    @property
    def r_groove_root(self) -> float:
        """Set by the squeeze target, not the other way round."""
        return self.r_core + self.oring_cs * (1 - self.oring_squeeze)

    @property
    def groove_depth(self) -> float:
        return self.r_groove_root - self.r_cap_seal_bore

    @property
    def groove_w(self) -> float:
        return self.oring_cs * 1.35

    @property
    def r_cap_thread_root(self) -> float:
        return self.r_thread_major + self.fit_thread_r

    @property
    def r_cap_out(self) -> float:
        return max(self.r_groove_root, self.r_cap_thread_root) + self.cap_wall

    # --- Thread profile -----------------------------------------------------
    @property
    def _flank(self) -> float:
        return math.tan(math.radians(self.thread_angle / 2)) * self.thread_depth

    @property
    def apex_w(self) -> float:
        return self.thread_pitch / 2 - self._flank

    @property
    def root_w(self) -> float:
        return self.thread_pitch / 2 + self._flank

    # --- Z stations ---------------------------------------------------------
    @property
    def z_shoulder(self) -> float:
        """Top of the base flange; the cap skirt lands here."""
        return 0.20

    @property
    def z_thread_lo(self) -> float:
        # Start the thread exactly on the base flange, not above it. A gap here
        # leaves the first ridge floating 0.2 mm clear of anything.
        return self.z_shoulder

    @property
    def z_thread_hi(self) -> float:
        return self.z_thread_lo + self.thread_len

    @property
    def z_ceiling(self) -> float:
        return self.stack_h + self.head_gap

    @property
    def z_body_rim(self) -> float:
        return self.z_ceiling - 0.15

    @property
    def z_groove_lo(self) -> float:
        """Seal sits high, above the thread, centred in the plain band."""
        return (self.z_thread_hi + self.z_body_rim) / 2 - self.groove_w / 2

    # --- Flipped board stack ------------------------------------------------
    @property
    def r_pocket(self) -> float:
        """Pocket the holder nests in, centred on the offset."""
        return self.r_holder + self.fit_holder

    @property
    def z_fill_top(self) -> float:
        """Top of the fill around the cell; clears the PCB face."""
        return self.holder_h - self.fill_relief

    @property
    def z_pcb_bottom(self) -> float:
        return self.holder_h

    @property
    def z_pcb_top(self) -> float:
        return self.holder_h + self.pcb_env_h

    # --- Harness tabs -------------------------------------------------------
    @property
    def r_slot_in(self) -> float:
        return self.r_cap_out + self.tab_inner_wall

    @property
    def r_slot_out(self) -> float:
        return self.r_slot_in + self.strap_t

    @property
    def r_tab_out(self) -> float:
        return self.r_slot_out + self.tab_bar

    # --- Sourcing -----------------------------------------------------------
    def oring_id_target(self) -> float:
        return 2 * (self.r_groove_root - self.oring_cs)

    def actual_squeeze(self) -> float:
        return (self.r_core - (self.r_groove_root - self.oring_cs)) / self.oring_cs


P = Params()


# --- helpers -----------------------------------------------------------------
def cyl(r: float, h: float, z: float = 0.0) -> bd.Solid:
    return bd.Pos(0, 0, z) * bd.Cylinder(
        r, h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def ring(r_out: float, r_in: float, h: float, z: float = 0.0) -> bd.Solid:
    return cyl(r_out, h, z) - cyl(r_in, h, z)


def place(shape, z_base: float):
    return bd.Pos(0, 0, z_base - shape.bounding_box().min.Z) * shape


def male_thread(p: Params) -> bd.Solid:
    return Thread(
        apex_radius=p.r_thread_major, apex_width=p.apex_w,
        root_radius=p.r_thread_minor, root_width=p.root_w,
        pitch=p.thread_pitch, length=p.thread_len,
        end_finishes=("chamfer", "fade"))


def female_thread(p: Params) -> bd.Solid:
    """Nut ridge filling the male groove, shrunk by the clearances.

    Phased 180 deg so the ridges land in the male's grooves rather than on its
    crests -- same-phase pairs model as a collision.
    """
    t = Thread(
        apex_radius=p.r_thread_minor + p.fit_thread_r,
        apex_width=(p.thread_pitch - p.root_w) - 2 * p.fit_thread_a,
        root_radius=p.r_thread_major + p.fit_thread_r,
        root_width=(p.thread_pitch - p.apex_w) - 2 * p.fit_thread_a,
        pitch=p.thread_pitch, length=p.thread_len,
        end_finishes=("chamfer", "chamfer"))
    return bd.Rot(0, 0, 180) * t


def cell_fill(p: Params) -> bd.Solid:
    """Fill around the cell, so the enclosure itself holds the holder.

    With the board flipped the holder sits on the floor, and the crescent of
    cavity it does not occupy gets filled to just under the PCB face. That fill
    is what stops the holder shifting. At the tangent point the cavity wall
    already backs the cell, so nothing extra is needed there.

    The fill deliberately stops short of the PCB (fill_relief): the board still
    rests on its own holder, and the foam ring in the cap still absorbs the
    unresolved stack tolerance. Seating the PCB on the fill instead would put
    the fill in contact with whatever components sit on that face, which is
    not known.
    """
    pocket = bd.Pos(p.holder_offset, 0, 0) * bd.Cylinder(
        p.r_pocket, p.z_fill_top + 1,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return cyl(p.r_cav, p.z_fill_top, z=0.0) - pocket


def strap_tabs(p: Params) -> bd.Solid:
    """Two flat side tabs in the plane of the base, each a slot plus a bar.

    Replaces the earlier under-floor bridges. The tag's underside is now
    completely flat and the elastic wraps the bar at each tip, lying level with
    the base instead of running beneath the tag.

    The root is only as tall as the base flange, because above z_shoulder and
    inside r_cap_out the space belongs to the cap skirt. Outboard of the cap the
    tab is full thickness. The root carries harness load in tension rather than
    bending, so the thin section is not the weak point it appears to be.
    """
    tabs = None
    for sign in (+1, -1):
        root = bd.Pos(sign * (p.r_cav + p.r_cap_out) / 2, 0, -p.floor_t) * bd.Box(
            p.r_cap_out - p.r_cav, p.tab_w, p.floor_t + p.z_shoulder,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        outer = bd.Pos(sign * (p.r_cap_out + p.r_tab_out) / 2, 0,
                       -p.floor_t) * bd.Box(
            p.r_tab_out - p.r_cap_out, p.tab_w, p.floor_t + p.tab_top,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        # Trim the outer edge to an arc about the tag centre. The tab is wider
        # than it is long, so a semicircular tip would overhang; this rounds it
        # without adding reach.
        outer &= cyl(p.r_tab_out, p.floor_t + p.tab_top + 2, z=-p.floor_t - 1)

        slot = bd.Pos(sign * (p.r_slot_in + p.r_slot_out) / 2, 0,
                      -p.floor_t - 1) * bd.Box(
            p.strap_t, p.strap_w, p.floor_t + p.tab_top + 2,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))

        tab = (root + outer) - slot
        tabs = tab if tabs is None else tabs + tab
    return tabs


# --- parts -------------------------------------------------------------------
def build_body(p: Params = P) -> bd.Solid:
    """Cup: floor, cavity, thread low, sealing band high, cell fill, side tabs."""
    body = cyl(p.r_cap_out, p.floor_t + p.z_shoulder, z=-p.floor_t)
    body += cyl(p.r_core, p.z_body_rim - p.z_shoulder, z=p.z_shoulder)
    body += place(male_thread(p), p.z_thread_lo)
    body -= cyl(p.r_cav, p.z_body_rim + 1, z=0)

    # Lead-in chamfer so the O-ring rolls onto the band instead of shearing.
    # The cone must taper INWARD going up. Widening it upward instead cuts the
    # wall to a 0.10 mm edge low down and leaves a downward-facing annular
    # shelf above it -- an undercut the slicer reports as a floating
    # cantilever, and a knife edge that cannot print.
    ch = 0.4
    body -= bd.Pos(0, 0, p.z_body_rim - ch) * (
        bd.Cylinder(p.r_core + 1, ch,
                    align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        - bd.Cone(p.r_core + 1.0, p.r_core - ch, ch,
                  align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))

    return body + cell_fill(p) + strap_tabs(p)


def build_cap(p: Params = P, foam_gap: tuple[float, float] | None = None,
              foam: tuple[float, float] | None = None) -> bd.Solid:
    """Screw cap: internal thread low, O-ring groove high, grip scallops.

    foam=(od, id) overrides the foam ring the ceiling recess is cut for; the
    default is the rim ring in Params. A cap with a clear ring window over the
    LED radius needs the foam moved inboard, or it sits on the LED.

    foam_gap=(theta_deg, span_deg) leaves the recess open over that angular
    sector instead, for a cap with a local window. Angles are from +X,
    counter-clockwise, viewed from outside the cap.
    """
    z0 = p.z_shoulder
    top = p.z_ceiling + p.cap_top_t

    cap = cyl(p.r_cap_out, top - z0, z=z0)
    # Thread bore (low) and sealing bore (high).
    cap -= cyl(p.r_cap_thread_root, p.z_thread_hi + 0.3 - z0, z=z0)
    cap -= cyl(p.r_cap_seal_bore, p.z_ceiling - (p.z_thread_hi + 0.3),
               z=p.z_thread_hi + 0.3)
    cap += place(female_thread(p), p.z_thread_lo)

    # Radial O-ring groove, above the thread.
    cap -= ring(p.r_groove_root, p.r_cap_seal_bore, p.groove_w, z=p.z_groove_lo)

    # Annular locator recess for the foam ring. Ring, not disc: the centre
    # window keeps the PCB's LED readable through the cap.
    foam_od, foam_id = foam if foam is not None else (p.foam_od, p.foam_id)
    recess = ring(foam_od / 2, foam_id / 2, 0.30, z=p.z_ceiling - 0.30)
    if foam_gap is not None:
        theta, span = foam_gap
        pts = [(0.0, 0.0)] + [
            (20 * math.cos(math.radians(theta + a)), 20 * math.sin(math.radians(theta + a)))
            for a in (-span / 2, -span / 4, 0, span / 4, span / 2)]
        wedge = bd.extrude(bd.Polygon(*pts, align=None), amount=2)
        recess -= bd.Pos(0, 0, p.z_ceiling - 1) * wedge
    cap -= recess

    # Grip scallops -- shallow enough to leave 2 perimeters behind the groove.
    for i in range(8):
        a = math.radians(i * 45)
        cap -= bd.Pos(math.cos(a) * (p.r_cap_out + 1.15),
                      math.sin(a) * (p.r_cap_out + 1.15), z0) * bd.Cylinder(
            1.4, top - z0,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))

    return cap


def build_coupon(p: Params = P) -> tuple[bd.Solid, bd.Solid]:
    """Fit coupon: thread pair plus groove only, ~10 minutes to print.

    Print this before committing time to the full enclosure -- it settles the
    thread clearance and the groove profile on your actual machine.
    """
    h = p.thread_len + 3.4

    male = cyl(p.r_core, h, z=0) - cyl(p.r_cav, h, z=0)
    male += cyl(p.r_cap_out, 1.2, z=-1.2) - cyl(p.r_cav, 1.2, z=-1.2)
    male += place(male_thread(p), 0.6)

    fem = cyl(p.r_cap_out, h, z=0)
    fem -= cyl(p.r_cap_thread_root, p.thread_len + 1.2, z=0)
    fem -= cyl(p.r_cap_seal_bore, h - (p.thread_len + 1.2), z=p.thread_len + 1.2)
    fem += place(female_thread(p), 0.6)
    fem -= ring(p.r_groove_root, p.r_cap_seal_bore, p.groove_w,
                z=p.thread_len + 1.8)
    return male, fem


# --- report ------------------------------------------------------------------
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p = P

    print("=" * 74)
    print("HEN TAG ENCLOSURE  --  Holyiot 25008, CR2032, radial seal + screw cap")
    print("=" * 74)
    print(f"  orientation        holder DOWN (z 0-{p.holder_h:.1f}), "
          f"PCB UP (z {p.z_pcb_bottom:.1f}-{p.z_pcb_top:.1f}), LED outward")
    print(f"  board stack        {p.stack_h:.2f} mm  "
          f"(holder {p.holder_h} + PCB {p.pcb_env_h})   UNVERIFIED")
    print(f"  holder offset      {p.holder_offset:.2f} mm  internally tangent")
    print(f"  cell pocket        r {p.r_pocket:.2f} mm, fill to z {p.z_fill_top:.2f}")
    print(f"  cavity radius      {p.r_cav:.2f} mm  (board {p.r_pcb} + {p.fit_board})")
    print(f"  seal band radius   {p.r_core:.2f} mm  (wall {p.body_wall:.2f})")
    print(f"  thread             Tr{2 * p.r_thread_major:.1f} x {p.thread_pitch}, "
          f"{p.thread_angle:.0f} deg, {p.thread_len} mm, low on the body")
    print(f"  cap outer dia      {2 * p.r_cap_out:.2f} mm")
    print(f"  tab span           {2 * p.r_tab_out:.2f} mm  "
          f"(slot {p.strap_w:.1f} x {p.strap_t:.1f}, bar {p.tab_bar:.1f})")
    print(f"  O-RING TO SOURCE   ID {p.oring_id_target():.2f} x CS {p.oring_cs} mm"
          f"  -> {p.actual_squeeze() * 100:.0f}% squeeze")
    print(f"  FOAM RING TO MAKE  OD {p.foam_od:.0f} x ID {p.foam_id:.0f} x "
          f"{p.foam_t:.1f} mm closed-cell, over a {p.head_gap:.2f} mm gap")

    print("\nbuilding...")
    parts = {"body": build_body(p), "cap": build_cap(p)}
    parts["coupon_body"], parts["coupon_cap"] = build_coupon(p)

    print(f"\n{'part':14} {'valid':>6} {'volume':>11} {'mass':>9}   bbox (mm)")
    print("-" * 74)
    printed = 0.0
    for name, solid in parts.items():
        m = solid.volume * PETG_DENSITY
        if name in ("body", "cap"):
            printed += m
        b = solid.bounding_box()
        print(f"{name:14} {str(solid.is_valid):>6} {solid.volume:9.1f} mm3 "
              f"{m:6.2f} g   {b.size.X:.1f} x {b.size.Y:.1f} x {b.size.Z:.1f}")

    pcb_m = math.pi * p.r_pcb ** 2 * p.pcb_env_h * 1.90e-3
    payload = pcb_m + 3.0 + 0.6 + 0.4
    total = printed + payload
    print("-" * 74)
    print(f"  printed plastic    {printed:6.2f} g")
    print(f"  payload            {payload:6.2f} g  (PCB {pcb_m:.2f} + cell 3.00 "
          f"+ holder 0.60 + ring 0.40, last two ESTIMATED)")
    verdict = "within" if total <= 10 else f"OVER by {total - 10:.2f} g"
    print(f"  ASSEMBLED TOTAL    {total:6.2f} g   {verdict} the 10 g target")

    # Export STLs already lying in their print orientation, so they drop onto
    # the plate correctly instead of relying on the operator to flip them. The
    # cap must print top-plate-down; left as modelled it would land opening-down
    # and the top plate would become a ~28 mm bridge over the cavity.
    FLIP = {"cap", "coupon_cap"}
    print()
    for name, solid in parts.items():
        oriented = bd.Rot(180, 0, 0) * solid if name in FLIP else solid
        oriented = bd.Pos(0, 0, -oriented.bounding_box().min.Z) * oriented
        bd.export_stl(oriented, str(OUT / f"{name}.stl"),
                      tolerance=0.008, angular_tolerance=0.1)
        # STEP keeps the design coordinate system, so the model stays readable
        # in CAD; only the STL is reoriented for the slicer.
        bd.export_step(solid, str(OUT / f"{name}.step"))
        note = "  (flipped for printing)" if name in FLIP else ""
        print(f"  exported {name}.stl / .step{note}")


if __name__ == "__main__":
    main()
