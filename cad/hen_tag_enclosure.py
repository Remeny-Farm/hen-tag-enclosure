# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["build123d"]
# ///
"""Parametric enclosure for the Holyiot 25008 hen tag.

Two-part transparent PETG housing: a cup-shaped body and a bayonet cap sealed
by a radial O-ring. Run with `uv run hen_tag_enclosure.py` -- uv resolves the
dependencies above, no virtualenv setup required.

Three decisions that are not obvious from the geometry alone:

1. Radial seal, not the axial face seal in docs/requirements.md. A face seal
   must sit outboard of the cap skirt, forcing a ~36 mm flange around a 25 mm
   board; measured, that overruns the mass budget by ~1.9 g. The radial seal
   needs none.

2. Closure low, seal high. The reverse -- seal below the closure -- cannot
   assemble: the cap's internal features would have to travel past a sealing
   band of larger radius. With the closure at the bottom, the cap's channels
   only ever pass the smaller seal band, and the O-ring never crosses the lugs.

3. Bayonet, not a thread (revision C). Revisions A/B used a Tr28.6 x 1.0
   trapezoidal thread. On a 0.4 mm nozzle its ridges are sub-nozzle-width
   (the cap's ridge crest computed to 0.05 mm) and its flanks are 15 deg from
   horizontal, i.e. 75 deg overhangs -- the operator's caps tore along the
   thread. The bayonet has three 0.8 mm lugs on the body and three L-channels
   in the cap; every face on both parts, in their print orientations, is
   either steeper than 45 deg or a flat overhang of one extrusion width. A
   shallow helical ramp on the channel floor draws the cap onto the base
   flange the way the thread did, and is self-locking.

MEASUREMENT STATUS -- read before trusting any printed part:
  VERIFIED   the board and its parts: manufacturer STEP, board_holyiot_25008.py
  VERIFIED   the PCB/holder tangency (geometric consequence of 25 and 21 mm)
  UNVERIFIED the holder: user caliper readings, 2026-08-28 (the STEP's clip
             model is generic and was discarded)
  UNVERIFIED the bayonet: modelled 2026-09-10, no coupon printed yet
  UNKNOWN    antenna location, elastic cross-section, actual O-ring ID/CS

Coordinate system: Z up, millimetres. z = 0 is the cavity floor -- the surface
the PCB rests on. Angles are degrees, counter-clockwise from +X viewed from
above (the cap side); the harness tabs lie on the X axis.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import build123d as bd

import board_holyiot_25008 as brd

OUT = Path(__file__).parent / "out"
PETG_DENSITY = 1.27e-3  # g/mm^3


@dataclass(frozen=True)
class Params:
    """Every dimension the design depends on, in one place."""

    # --- Board, VERIFIED from the manufacturer STEP (board_holyiot_25008) ---
    # Orientation: holder DOWN against the floor, PCB UP under the cap. The
    # LED sits on the PCB face, so it has to look outward, away from the bird.
    pcb_dia: float = brd.PCB_DIA
    pcb_t: float = brd.PCB_T     # bare board
    comp_h: float = brd.S1_H     # tallest part on the face, the centre switch
    # --- Holder, UNVERIFIED (user caliper 2026-08-28) -----------------------
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

    # --- Bayonet closure, UNVERIFIED (modelled 2026-09-10, no coupon yet) ---
    # Three lugs on the body's seal band, three L-channels in the cap skirt:
    # an axial entry slot at the skirt's open end, then a circumferential leg
    # whose floor -- the lip that carries the cap -- is a shallow helical
    # ramp. Turning the cap clockwise runs the lugs up the ramps until the
    # skirt lands on the base flange, exactly as the thread used to.
    #
    # Printability rule behind every number here: on both parts, in their
    # print orientations, NO face is flatter than chamfer_deg -- the slicer's
    # support detection (Bambu, 30 deg threshold) finds nothing to support.
    # Lug undersides and lip tops are matching 50 deg cones that bear on each
    # other. Revision C had a 0.5 mm flat bearing ledge here, and the slicer
    # put support under all three lips (2026-09-24).
    lug_n: int = 3
    lug_arc: float = 20.0        # angular width of one lug
    lug_d: float = 0.80          # radial protrusion off the seal band
    lug_h: float = 1.30          # axial height at the lug centre; the cone
                                 # takes 0.83 of it, leaving a 0.47 crest
    lug_z: float = 1.80          # underside above the cavity floor, at the centre
    chamfer_deg: float = 50.0    # lug/lip/groove cone, from horizontal (>45)
    fit_lug_r: float = 0.15      # radial clearance, lug crest to channel root
    fit_lug_z: float = 0.30      # axial clearance, lug top to channel ceiling
    fit_lug_t: float = 4.0       # angular clearance each side in the entry slot
    cam_rate: float = 0.012      # ramp rise per degree of cap rotation (mm/deg)
    cam_lock: float = 30.0       # cap rotation, entry to nominal contact
    cam_travel: float = 55.0     # lug-centre travel available before the end wall

    # --- Radial seal, UNVERIFIED (needs the actual ring measured) -----------
    oring_cs: float = 1.50
    oring_squeeze: float = 0.22  # fraction of CS compressed

    # --- Assembly -----------------------------------------------------------
    # The ceiling stays where revision A put it (holder 4.0 + the caliper's
    # 2.0 board + 0.6), because that pair closed over a real board. With the
    # STEP's 0.81 board and 1.60 switch the true head gap over S1 is 0.19.
    ceiling_h: float = 6.60
    # Foam is a RING, not a disc, and it sits inboard (r 6-8), under the
    # opaque core and clear of both the switch (r <= 2.26) and the LED
    # (r 8.78-10.91). The rim ring it replaces landed on the LED. 2.0 mm
    # because the board face is 1.79 below the ceiling; the ring bears on the
    # parts in its band (0.5-1.1 mm) and just kisses bare board.
    foam_od: float = 16.0
    foam_id: float = 12.0
    foam_t: float = 2.00
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
    def pcb_env_h(self) -> float:
        """Board plus its tallest part."""
        return self.pcb_t + self.comp_h

    @property
    def stack_h(self) -> float:
        return self.pcb_env_h + self.holder_h

    @property
    def head_gap(self) -> float:
        """Ceiling clearance over the switch, the tallest part."""
        return self.ceiling_h - self.stack_h

    @property
    def foam_gap(self) -> float:
        """Ceiling down to the bare board face under the foam ring."""
        return self.ceiling_h - self.holder_h - self.pcb_t

    # --- Radial stations ----------------------------------------------------
    @property
    def r_cav(self) -> float:
        return self.r_pcb + self.fit_board

    @property
    def r_core(self) -> float:
        """Body outer wall: the plain band the O-ring seals against."""
        return self.r_cav + self.body_wall

    @property
    def r_lug(self) -> float:
        """Lug crest."""
        return self.r_core + self.lug_d

    @property
    def r_cap_seal_bore(self) -> float:
        return self.r_core + self.fit_seal_r

    @property
    def r_cap_chan(self) -> float:
        """Root of the cap's bayonet channels."""
        return self.r_lug + self.fit_lug_r

    @property
    def r_groove_root(self) -> float:
        """Set by the squeeze target, not the other way round."""
        return self.r_core + self.oring_cs * (1 - self.oring_squeeze)

    @property
    def groove_depth(self) -> float:
        return self.r_groove_root - self.r_cap_seal_bore

    @property
    def groove_w(self) -> float:
        """Axial width at the root, where the ring sits."""
        return self.oring_cs * 1.35

    @property
    def groove_rise(self) -> float:
        """Axial run of the groove's lower cone, bore to root."""
        return self.chamfer_rise(self.r_groove_root - self.r_cap_seal_bore)

    @property
    def r_cap_out(self) -> float:
        return max(self.r_groove_root, self.r_cap_chan) + self.cap_wall

    # --- Bayonet kinematics -------------------------------------------------
    @property
    def cam_pitch(self) -> float:
        """Helix pitch (mm per turn) shared by the lugs and the lips."""
        return self.cam_rate * 360.0

    @property
    def cam_slack(self) -> float:
        """Axial play between lug and lip at the entry angle."""
        return self.cam_rate * self.cam_lock

    @property
    def cam_window(self) -> tuple[float, float]:
        """Axial print error the ramp absorbs: (tightest, loosest) still locking."""
        return (-self.cam_slack,
                self.cam_rate * (self.cam_travel - self.cam_lock))

    @property
    def entry_half(self) -> float:
        """Half-width of the entry slot, degrees."""
        return self.lug_arc / 2 + self.fit_lug_t

    @property
    def chan_end(self) -> float:
        """Angle of the channel's end wall from the entry-slot centre."""
        return self.cam_travel + self.lug_arc / 2

    def lug_angle(self, i: int) -> float:
        """Centre of lug i in the body frame; lug 0 sits on the tab axis."""
        return 360.0 * i / self.lug_n

    def chamfer_rise(self, run: float) -> float:
        return math.tan(math.radians(self.chamfer_deg)) * run

    @property
    def helix_deg(self) -> float:
        """Ramp helix angle at the lug radius; must stay below the friction angle."""
        return math.degrees(math.atan(self.cam_pitch / (2 * math.pi * self.r_lug)))

    # --- Z stations ---------------------------------------------------------
    @property
    def z_shoulder(self) -> float:
        """Top of the base flange; the cap skirt lands here."""
        return 0.20

    @property
    def z_chan_hi(self) -> float:
        """Ceiling of the cap's bayonet channels."""
        return self.lug_z + self.lug_h + self.fit_lug_z

    @property
    def z_lip_lo(self) -> float:
        """Lip top at its thin end (the entry-slot edge), cap frame."""
        return self.lug_z + self.cam_rate * (self.entry_half - self.cam_lock)

    @property
    def z_ceiling(self) -> float:
        return self.ceiling_h

    @property
    def z_body_rim(self) -> float:
        return self.z_ceiling - 0.15

    @property
    def z_groove_lo(self) -> float:
        """Seal sits high, above the channels, centred in the plain band."""
        return (self.z_chan_hi + self.z_body_rim) / 2 - self.groove_w / 2

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


def sector(r_out: float, r_in: float, a0: float, a1: float, h: float,
           z: float = 0.0) -> bd.Solid:
    """Annular sector from angle a0 to a1 (degrees, CCW from +X)."""
    n = max(2, int((a1 - a0) / 5) + 1)
    R = r_out + 2.0
    pts = [(0.0, 0.0)] + [
        (R * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         R * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
        for i in range(n + 1)]
    wedge = bd.Pos(0, 0, z) * bd.extrude(bd.Polygon(*pts, align=None), amount=h)
    return wedge & ring(r_out, r_in, h, z)


def helical_sector(profile_rz: list[tuple[float, float]], r_ref: float,
                   start: float, span: float, pitch: float,
                   z_start: float) -> bd.Solid:
    """Sweep an (r, z) polygon along a right-handed helix.

    The profile is given in radial/axial coordinates at `start`, z relative to
    z_start; the result covers `span` degrees and rises pitch * span / 360.
    Lugs and lips are both built this way with the same pitch, so at the
    locked position their bearing flats are parallel and touch over their
    full width instead of along one edge.
    """
    path = bd.Helix(pitch=pitch, height=pitch * span / 360.0, radius=r_ref)
    # Profile plane: x radial outward, y axial up. Using the negated path
    # tangent as the plane normal is what makes local y point up.
    plane = bd.Plane(origin=path @ 0, x_dir=(1, 0, 0), z_dir=-(path % 0))
    face = plane * bd.make_face(bd.Polyline(
        *[bd.Vector(r - r_ref, z, 0) for r, z in profile_rz], close=True))
    solid = bd.sweep(face, path=path, is_frenet=True)
    return bd.Pos(0, 0, z_start) * (bd.Rot(0, 0, start) * solid)


# --- closure -----------------------------------------------------------------
def body_lugs(p: Params) -> bd.Solid:
    """Bayonet lugs on the seal band.

    Underside: a cone at chamfer_deg from the cap's bore radius out to the
    crest -- no flat, so nothing for the slicer to support. It lies on the
    same cone as the cap's lip tops and follows the ramp helix, so the two
    mate face to face. The 0.10 mm under the bore radius is flat but sits
    against the band. The top is cut flat afterwards, it carries nothing.
    """
    r_bear = p.r_cap_seal_bore
    rise = p.chamfer_rise(p.r_lug - r_bear)
    over = p.lug_h + p.cam_rate * p.lug_arc + 0.5      # trimmed flat below
    prof = [(p.r_core - 0.30, 0.0), (r_bear, 0.0),
            (p.r_lug, rise), (p.r_lug, over), (p.r_core - 0.30, over)]
    lugs = None
    for i in range(p.lug_n):
        lug = helical_sector(prof, p.r_lug - 0.4,
                             p.lug_angle(i) - p.lug_arc / 2, p.lug_arc,
                             p.cam_pitch, p.lug_z - p.cam_rate * p.lug_arc / 2)
        lugs = lug if lugs is None else lugs + lug
    return lugs - cyl(p.r_lug + 1, 5, z=p.lug_z + p.lug_h)


def cap_channels(p: Params) -> tuple[bd.Solid, bd.Solid]:
    """The cap's L-channels: (material to cut, lips to add back).

    Built in the cap's LOCKED orientation, so the cap solid is already in its
    assembled pose. For lug i at angle a: the entry slot is centred at
    a - cam_lock (the cap turns clockwise to lock), full height from the
    skirt's open end to z_chan_hi; the circumferential leg runs from the slot
    to the end wall at a - cam_lock + chan_end. Under the leg sits the lip, a
    helical ramp rising cam_rate per degree, parallel to the lug undersides.
    Its top is a cone at chamfer_deg from the bore up to the channel root,
    the lug undersides' cone -- once the cap is flipped for printing it
    overhangs at 50 deg and needs no support.
    """
    r_in = p.r_cap_seal_bore
    r_out = p.r_cap_chan + 0.05          # embeds into the wall: no coincident face
    rise = p.chamfer_rise(r_out - r_in)
    prof = [(r_in, -1.0), (r_out, -1.0), (r_out, rise), (r_in, 0.0)]
    cut = lips = None
    for i in range(p.lug_n):
        e = p.lug_angle(i) - p.cam_lock
        c = sector(p.r_cap_chan, r_in - 0.8, e - p.entry_half, e + p.chan_end,
                   p.z_chan_hi - p.z_shoulder + 0.5, p.z_shoulder - 0.5)
        lip = helical_sector(prof, p.r_cap_chan - 0.4, e + p.entry_half,
                             p.chan_end - p.entry_half, p.cam_pitch, p.z_lip_lo)
        cut = c if cut is None else cut + c
        lips = lip if lips is None else lips + lip
    return cut, lips


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
    """Cup: floor, cavity, bayonet lugs low, sealing band high, cell fill, tabs."""
    body = cyl(p.r_cap_out, p.floor_t + p.z_shoulder, z=-p.floor_t)
    body += cyl(p.r_core, p.z_body_rim - p.z_shoulder, z=p.z_shoulder)
    body += body_lugs(p)
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


def cap_skirt(p: Params, z_top: float) -> bd.Solid:
    """Cap wall from the open end up to z_top: bore, bayonet channels, groove.

    Shared by the cap and its fit coupon so the coupon tests the real thing.
    """
    z0 = p.z_shoulder
    skirt = cyl(p.r_cap_out, z_top - z0, z=z0)
    skirt -= cyl(p.r_cap_seal_bore, z_top - z0 + 1, z=z0)
    cut, lips = cap_channels(p)
    skirt = (skirt - cut) + lips
    # The lips were swept from below the open end; trim them flush with it.
    skirt -= cyl(p.r_cap_out + 1, 3, z=z0 - 3)
    # Radial O-ring groove, above the channels. The ring sits on the root,
    # groove_w wide; the lower flank is a cone, not a flat, because printed
    # top-plate-down that flank faces the bed -- a flat one is a 1.07 mm
    # ledge the slicer supports. The cone may open into the channels' tops.
    lo, r_b = p.z_groove_lo, p.r_cap_seal_bore - 0.05
    groove = bd.revolve(bd.make_face(bd.Polyline(
        (r_b, 0, lo - p.groove_rise * (p.r_groove_root - r_b)
         / (p.r_groove_root - p.r_cap_seal_bore)),
        (p.r_groove_root, 0, lo), (p.r_groove_root, 0, lo + p.groove_w),
        (r_b, 0, lo + p.groove_w), close=True)), bd.Axis.Z)
    skirt -= groove
    return skirt


def build_cap(p: Params = P, foam_gap: tuple[float, float] | None = None,
              foam: tuple[float, float] | None = None) -> bd.Solid:
    """Bayonet cap: L-channels low, O-ring groove high, grip scallops.

    foam=(od, id) overrides the foam ring the ceiling recess is cut for; the
    default is the inboard ring in Params. A rim ring (r 8-12.5) would sit on
    the LED, which the STEP puts at r 8.78-10.91.

    foam_gap=(theta_deg, span_deg) leaves the recess open over that angular
    sector instead, for a cap with a local window. Angles are from +X,
    counter-clockwise, viewed from outside the cap.
    """
    z0 = p.z_shoulder
    top = p.z_ceiling + p.cap_top_t

    cap = cap_skirt(p, p.z_ceiling)
    cap += cyl(p.r_cap_out, top - p.z_ceiling, z=p.z_ceiling)

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
    """Fit coupon: the bayonet pair plus the O-ring groove, ~10 minutes to print.

    Print this before committing time to the full enclosure -- it settles the
    lug/lip fit, where along the ramp the cap locks up, and the groove profile
    on your actual machine. Same z stations as the real parts.
    """
    z_top = p.z_body_rim
    male = cyl(p.r_cap_out, p.floor_t + p.z_shoulder, z=-p.floor_t)
    male += cyl(p.r_core, z_top - p.z_shoulder, z=p.z_shoulder)
    male += body_lugs(p)
    male -= cyl(p.r_cav, z_top + 1, z=0)
    return male, cap_skirt(p, z_top)


# --- report ------------------------------------------------------------------
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p = P

    print("=" * 74)
    print("HEN TAG ENCLOSURE  --  Holyiot 25008, CR2032, radial seal + bayonet cap")
    print("=" * 74)
    print(f"  orientation        holder DOWN (z 0-{p.holder_h:.1f}), "
          f"PCB UP (z {p.z_pcb_bottom:.1f}-{p.z_pcb_top:.1f}), LED outward")
    print(f"  board stack        {p.stack_h:.2f} mm  "
          f"(holder {p.holder_h} UNVERIFIED + PCB {p.pcb_t} + S1 {p.comp_h}, STEP)")
    print(f"  ceiling            z {p.z_ceiling:.2f}, {p.head_gap:.2f} mm over S1")
    print(f"  holder offset      {p.holder_offset:.2f} mm  internally tangent")
    print(f"  cell pocket        r {p.r_pocket:.2f} mm, fill to z {p.z_fill_top:.2f}")
    print(f"  cavity radius      {p.r_cav:.2f} mm  (board {p.r_pcb} + {p.fit_board})")
    print(f"  seal band radius   {p.r_core:.2f} mm  (wall {p.body_wall:.2f})")
    print(f"  closure            bayonet, {p.lug_n} lugs x {p.lug_arc:.0f} deg, "
          f"{p.lug_d:.2f} mm proud at z {p.lug_z:.2f}-{p.lug_z + p.lug_h:.2f}, "
          f"low on the body")
    lo, hi = p.cam_window
    print(f"  lock               {p.cam_lock:.0f} deg clockwise; ramp "
          f"{p.cam_rate * 1000:.0f} um/deg ({p.helix_deg:.1f} deg helix, "
          f"self-locking), absorbs {lo:+.2f}..{hi:+.2f} mm of print error")
    print(f"  cap outer dia      {2 * p.r_cap_out:.2f} mm")
    print(f"  tab span           {2 * p.r_tab_out:.2f} mm  "
          f"(slot {p.strap_w:.1f} x {p.strap_t:.1f}, bar {p.tab_bar:.1f})")
    print(f"  O-RING TO SOURCE   ID {p.oring_id_target():.2f} x CS {p.oring_cs} mm"
          f"  -> {p.actual_squeeze() * 100:.0f}% squeeze")
    print(f"  FOAM RING TO MAKE  OD {p.foam_od:.0f} x ID {p.foam_id:.0f} x "
          f"{p.foam_t:.1f} mm closed-cell, over a {p.foam_gap:.2f} mm gap to the board")

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

    pcb_m = brd.PCB_MASS + brd.PARTS_MASS
    payload = pcb_m + 3.0 + 0.6 + 0.4
    total = printed + payload
    print("-" * 74)
    print(f"  printed plastic    {printed:6.2f} g")
    print(f"  payload            {payload:6.2f} g  (PCB {pcb_m:.2f} + cell 3.00 "
          f"+ holder 0.60 + ring 0.40; parts, holder, ring ESTIMATED)")
    verdict = "within" if total <= 10 else f"OVER by {total - 10:.2f} g"
    print(f"  ASSEMBLED TOTAL    {total:6.2f} g   {verdict} the 10 g target")

    # Export STLs already lying in their print orientation, so they drop onto
    # the plate correctly instead of relying on the operator to flip them. The
    # cap must print top-plate-down; left as modelled it would land opening-down
    # and the top plate would become a ~28 mm bridge over the cavity. The cap
    # coupon is flipped too, so its lips print as the real cap's do.
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
