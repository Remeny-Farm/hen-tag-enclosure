# Hen Tag Enclosure — Design Specification

## Purpose & Status

Parametric two-part enclosure for the Holyiot 25008 tag, generated from code in
`cad/hen_tag_enclosure.py`.

- **Status**: Revision B. Geometry generated, machine-verified, exported.
  **Revision B has not been printed.**
- **Revision A was printed and fitted** on a Bambu Lab P1S — dimensions and
  thread both confirmed good. See
  `docs/lab/2026-08-28-enclosure-print-trial.md`. The thread clearances are
  therefore empirical; the board dimensions still are not.
- **Blocking caveat**: the board dimensions this design is built on are operator
  caliper readings that carry an unresolved ambiguity. See
  `docs/lab/2026-08-28-enclosure-board-measurements.md`.

---

## Summary

| | |
|---|---|
| Assembled envelope | **40.14 × 31.94 × 8.70 mm** (Ø31.94 body, tabs to 40.14) |
| Printed mass (PETG) | **5.05 g** (body 2.78 + cap 2.27) |
| Assembled mass | **10.92 g** — 0.92 g over the 10 g target |
| Orientation | Holder **down** toward the harness, PCB **up**, LED outward |
| Sealing | Radial NBR O-ring, **ID 26.74 × CS 1.50 mm** |
| Closure | Trapezoidal screw thread, Tr28.6 × 1.0, 30°, 2.8 mm engaged |
| Material | Transparent PETG. Conductive/CF filament remains prohibited. |

```
                              Ø31.94
              ┌──────────────────────────────┐   cap top 1.10
              │ ▁▁▁  Ø16 LED window  ▁▁▁     │   foam recess 0.30
         ═════╪══════════════════════════════╪═════  ceiling z=6.60
              │ ░░░           ░░░            │   foam RING OD25/ID16 x 1.0
              │ ▓▓▓▓▓▓▓ PCB Ø25 ▓▓▓▓▓▓▓ z=6.0│   ← LED faces the cap
         ○────┤ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ z=4.0 ├────○  O-ring, z=3.71…5.74
              │███┌──────────────────┐███████│   seals on band r=13.70
              │███│ CR2032 + holder  │███████│   ███ = fill, holds the holder
    ▓▓▓▓▓▓▓▓▓▓╪███│ Ø21, offset 2.0  │███████╪▓▓▓▓▓▓▓▓  thread z=0.20…3.00
    ┌─────┐   │▁▁▁└──────────────────┘▁▁▁▁▁▁▁│   ┌─────┐  floor 1.00
    │  ▄  │═══╡        cell rests on the floor  ╞═══│  ▄  │  ← in-plane tabs
    └─────┘   └──────────────────────────────┘   └─────┘     slot 8.8 x 1.8
                    FLAT UNDERSIDE                           bar 1.5
```

---

## Design Decisions

### 1. Radial seal, not the axial face seal

`docs/requirements.md` originally specified an axial face seal on an NBR 30 × 2 mm ring.
A face seal must sit **outboard of the cap skirt**, which forces a flange out to
Ø36 around a Ø25 board. Modelled and weighed, the three options were:

| Variant | OD | Plastic | Assembled |
|---|---|---|---|
| Face seal, NBR 30×2 (original spec) | 36.0 mm | 6.01 g | 11.88 g |
| Face seal, NBR 24×2 | 31.1 mm | 4.40 g | 10.26 g |
| **Radial seal (adopted)** | **31.9 mm** | **4.32 g** | **10.19 g** |

The flange was ~1.7 g of pure overhead. The radial seal needs none.

> Those masses compare the three sealing strategies on identical revision A
> bodies. Revision B is heavier (5.05 g) because of the cell fill and the tabs;
> the comparison between strategies is unaffected.

Second advantage, specific to FDM: a radial seal's compression is set by the bore
diameter, not by how hard the cap is tightened. The face seal needed a stop
flange precisely to stop the operator from shearing the ring — a failure mode the
radial arrangement does not have.

### 2. Thread low, seal high

The first layout put the seal below the thread and **could not be assembled**.
The cap's internal thread crests sit at r 14.00; sliding them down past a sealing
band at r 14.30 is a collision. Caught by `verify.py`, not by eye.

Inverting it fixes the assembly path and adds a second benefit: **the O-ring
never travels across the thread**, which would shred it. The check that enforces
this is `cap thread clears the seal band` in `verify.py`.

### 3. Holder down, PCB up

The LED sits on the PCB face. With the board the other way up it pointed at the
bird and was unreadable. Inverted, the PCB looks into the transparent cap and
the LED can be read on a closed tag.

This also removes an old awkwardness. Because the holder is internally tangent
to the PCB, **no rotationally symmetric ring lands on bare PCB all the way
round** when the holder faces up — at the tangent point the holder reaches the
board edge exactly. With the holder underneath, the PCB presents a full Ø25 disc
to the cap, so a plain annular clamp works.

### 4. Fill around the cell

The crescent of cavity the offset holder does not occupy is filled solid from
the floor to just under the PCB face. That fill is what holds the holder: 100 %
of the holder's circumference is backed either by fill or, at the tangent point,
by the cavity wall itself.

The fill deliberately stops 0.20 mm **short** of the PCB rather than seating it.
The board still rests on its own holder, and the fill never touches whatever
components sit on that face — which are not known. It costs about 0.7 g.

### 5. Tolerance lives in a foam ring, not a pad

A 1.0 mm closed-cell foam **ring**, OD 25 × ID 16, in an annular recess in the
cap ceiling. It presses the PCB rim and tolerates stack heights from about 5.2
to 6.6 mm, so a wrong reading of the height ambiguity is fixed by changing foam,
not by reprinting.

Ring rather than disc because a disc would cover the LED. The Ø16 centre stays
open as a viewing window.

> The LED's position on the PCB is unknown. If it turns out to sit under the
> ring rather than in the window, replace the ring with three foam pads at 120°.

### 6. Battery retention comes free

At the tangent point the cell edge is flush with the PCB edge, so the cavity wall
sits directly against the cell and blocks the direction it would slide out. With
the holder now facing down, the cavity floor also backs the cell face, pressing
it into its clip. No retention feature was added because none is needed.

### 7. In-plane side tabs for the harness

Two flat tabs in the plane of the base, each with a transverse slot and a bar at
the tip that the elastic wraps. The tag's **underside is completely flat** —
verified at 0.000 mm³ of material below the floor plane.

This replaced under-floor bridges, which stood 2.8 mm proud of the base. Losing
them took the assembled height from 11.50 mm to **8.70 mm**; the tabs widen the
tag to 40.14 mm across.

The tab root is only as thick as the base flange (1.2 mm), because above that
and inside the cap radius the space belongs to the rotating cap skirt. That root
carries harness load in tension, not bending, across 13 mm of width — so the
thin section is not the weak point it looks like. **Untested under load.**

### 8. Customer cap: clear shell, big coin lettering, accent core

`cad/cap_marking.py <number>` generates the per-hen cap as three bodies for
three filaments, delivered as a pre-registered Bambu project
(`cap_<n>_P1S.3mf`, slots 1/2/3 pre-assigned) plus a vendor-neutral 3MF:

| Body | Filament | What it is |
|---|---|---|
| `cap_<n>` | **clear PETG** | the whole shell — thread, seal, envelope untouched |
| `marking_<n>` | text colour | number (bottom arc, 6.0 pt), message (top arc, 5.2 pt caps), icon — 0.64 mm flush inlays |
| `core_<n>` | accent colour | full disc Ø17.2, the icon cut from it — colours meet edge to edge |

Two print trials shaped this. The first (opaque shell + clear LED ring)
proved the three-colour registration and the thread but the 2.9 mm lettering
was unreadable. The second revision makes the whole shell clear: the LED
(r 10.0, angle uncontrolled) shines through wherever it lands, so the window
part and every angular-alignment concern disappear, and the lettering band
grows to ~6 mm — letters twice the printed height, messages capped at
**8 guaranteed / ~12 typical characters**. The generator is deterministic
(fixed fonts, byte-identical output for identical input) and tested by a
29-case suite: envelope, rejections, determinism, full Bambu export.

---|---|---|
| `cap_<n>` | customer's cap colour, opaque | the shell — thread, seal, envelope untouched |
| `marking_<n>` | customer's text colour | coin-style lettering + centre heart, a 0.64 mm flush inlay |
| `window_<n>` | clear PETG | a **3.0 mm wide clear ring at r 10.0**, through the whole top plate |

Because the cap prints top-plate-down, all three meet in the first layers
against the plate: the outer face is one smooth plane, the id reads correctly
from outside, and the window is flush on both faces. The marking never reaches
the cavity (0.46 mm of shell above it); the window does, which is the point.

**Why a ring.** The LED centre is 2.5 mm in from the board edge (operator
caliper), i.e. r = 10.0. Its *angle* relative to the cap is not controlled —
the board can turn a few degrees in its pocket, and the cap's stop angle
carries print tolerance at 360° per millimetre of pitch — so a local window
would need bench-proven angular registration. A ring at the LED radius lights
wherever the LED is and needs no alignment at all. Its width only has to
cover the radial tolerance chain, which is small and known:

| Term | ± mm | Source |
|---|---|---|
| board radial play in the cavity | 0.30 | `fit_board` |
| cap concentricity, set by the seal bore | 0.10 | `fit_seal_r` |
| LED emitting-area half-size | ~0.8 | 0606–2020 package, UNVERIFIED |
| **half-width needed** | **1.2** | → 2.4 mm minimum ring |

The default is **3.0 mm** (r 8.5–11.5): 0.3 mm margin each side and ~7
extrusion widths, so the colour boundary prints crisp. Narrower does not buy a
larger id — at 2.5 mm the "67 ♥" sample is still 75 %, only the margin drops
to 0.05 mm. `--ring-width` overrides; `--pill R THETA` gives the old local
window for a cap whose registration has been proven on the bench.

**Coin-style lettering.** The id no longer sits in the centre: it bends along
the opaque band outside the clear ring (r 12.5–15.4), like the lettering on a
coin — the id along the bottom arc with glyph tops toward the centre, an
optional per-customer message (`--top "Szeretlek Bözsi!"`) along the top arc
with tops outward, both reading left to right, the gaps falling on the tab
axis. The centre inside the ring carries only the heart (`--no-heart` to omit).
Fonts are fitted automatically: the largest size whose bent, dilated glyphs
stay inside the band wins (the sample lands at 3.4 pt for the id, 3.2 pt for
the message, thinnest feature 0.72 mm after the 0.2 mm dilation that makes
hairline strokes printable). A message longer than ~200° of arc is refused
rather than shrunk into illegibility.

**What the ring costs.** The shell's central disc is joined to the rest of the
shell only through the clear ring — fine for printing (same PETG, different
pigment, fused in place) but worth knowing. The foam ring cannot stay at the
rim, which is exactly the LED radius: it moves inboard to **OD 16 / ID 12**,
where it bears on the board's r 6–8 zone. Whether that zone is free of tall or
pressure-sensitive parts is **unverified**; the tactile switch near the centre
is inside the ID.

`--no-window` reproduces the earlier two-body transparent cap.

---

## Bill of Materials — non-printed

| Item | Spec | Status |
|---|---|---|
| O-ring | NBR, **ID 26.74 × CS 1.50 mm**, closest stock size | to source |
| Foam ring | closed-cell PE/EVA, adhesive backed, 1.0 mm: **OD 25 × ID 16** for a transparent cap, **OD 16 × ID 12** for a ring-window cap (the rim is the LED radius) | to source or punch |
| Clear PETG | third filament for the LED window; the cap shell and id are now opaque colours | per print |
| Elastic | 8 mm figure-eight harness | cross-section UNVERIFIED |
| Conformal coating | acrylic, per `docs/requirements.md` masking rules | unchanged |

> The previously specified 30 × 2 mm ring **does not fit this geometry**. Sourcing
> it would be wasted money.

---

## Print Settings

| Setting | Value | Why |
|---|---|---|
| Material | Transparent PETG | UV/impact per README; LEDs stay readable |
| Nozzle | 0.40 mm | thinnest wall in the design is 0.80 mm = 2 perimeters |
| Layer | 0.16 mm | thread flanks and the O-ring groove need the resolution |
| Perimeters | 3 | |
| Infill | 30 %+ | parts are nearly all perimeter anyway |
| Supports | **none** | verified by slicing; see below |
| Orientation | **already baked into the STLs** | drop them on the plate as-is |

The exported STLs lie in their print orientation: the body floor-down, the cap
and the female coupon flipped top-plate-down. Do not re-orient them. Left as
modelled, the cap lands opening-down and its top plate becomes a ~28 mm bridge
over the cavity. The STEP files keep the design coordinate system, so the model
stays readable in CAD.

Sliced with Bambu Studio 02.08.02.60 at default settings, all four parts return
`Success.` with **zero warnings** and `max_cantilever_dist = 0` for the body.

The coupons (`coupon_body.stl`, `coupon_cap.stl`, ~1.1 g each) carry the thread
pair and the groove and nothing else. **On a Bambu Lab P1S the thread fit is
already confirmed**, so they are only needed when moving to a different printer
or material. If a coupon binds there, change `fit_thread_r` in the source and
regenerate; do not file the parts.

---

## Assembly

1. Conformal-coat the PCB per `docs/requirements.md`, masking SWD pads, battery contacts and
   the antenna area.
2. Seat the CR2032 in the holder, sliding it in at the tangent edge.
3. Drop the board into the body cavity **holder first, PCB facing up**. The
   holder should drop into its pocket with about 0.25 mm of play, and the PCB
   should end up roughly 0.6 mm below the cap ceiling.
   - Check the LED is facing you. If the PCB is against the floor, the board is
     upside down and the LED will be pointed at the bird.
4. Stick the OD 25 × ID 16 × 1.0 mm foam ring into the cap's annular ceiling
   recess, leaving the centre window open.
5. Fit the O-ring into the cap's internal groove.
6. Thread the cap on hand-tight until the skirt meets the base flange. Do not
   overtighten — the radial seal does not need it.
7. Thread the elastic through each side tab's slot and back around the bar.

---

## Verification Performed

`cad/verify.py`, 29 machine checks, all passing. Notable ones:

- body/cap collision: **0.000 mm³** at the assembled position
- board vs. enclosure interference: **0.0000 mm³**
- holder circumference backed by plastic: **100 %**
- fill clears the PCB face: 0.20 mm
- clearance at the tangent point: **0.30 mm**
- cap thread clears the seal band: **+0.30 mm** (the check that caught decision 2)
- O-ring never crosses the thread: groove starts z 3.71, thread ends z 3.00
- O-ring squeeze: **22 %** (static radial target is 15–30 %)
- thinnest wall: **0.80 mm** under the grip scallops
- 8.0 mm elastic threads the tab slot: **0.000 mm³** obstructing
- tab bar cross-section: **4.80 mm²**
- underside flat: **0.000 mm³** below the floor plane
- assembled envelope: 40.14 × 31.94 × 8.70 mm
- worst unsupported overhang band: **9.36 mm²** on the body, 96.33 mm² on the
  cap (the O-ring groove flank, which becomes a ceiling once the cap is flipped)
- meshes watertight: 0 non-manifold edges, 0 loose vertices, positive volume
- **sliced clean in Bambu Studio**: all four parts `Success.`, zero warnings

### The floating-cantilever defect

The rim's lead-in chamfer was cut with a cone tapering the wrong way. Instead of
narrowing toward the rim it widened, which thinned the wall to a **0.10 mm knife
edge** low down and left a downward-facing annular shelf above it — a genuine
undercut, and unprintable.

Confirmed by slicing both versions:

| | `max_cantilever_dist` | Slicer verdict |
|---|---|---|
| Inverted chamfer | 1.37 × 10⁶ | *"floating cantilever… enable support generation"* |
| Corrected | **0** | `Success.`, no warnings |

A second, smaller floating feature was found in the same pass: the thread began
0.2 mm above the base flange, leaving its first ridge unsupported. The thread now
starts flush on the flange, which took the body's worst overhang band from
18.95 mm² down to 9.36 mm².

`verify.py` now measures unsupported overhang area per part against limits
calibrated to revision A, which is known to print, so this class of defect
cannot return unnoticed.

Mesh volume matches the solid model to within 0.3 mm³, so STL tessellation is
not distorting the geometry.

**What revision A proved**: printed on a Bambu Lab P1S, dimensions and thread
fit both confirmed good on physical parts.

**What none of this proves**: revision B — the inverted stack, the cell fill and
the side tabs — has not been printed. No O-ring has been compressed, no water
has touched it, no elastic has loaded a tab, and no hen has worn it.

---

## Verified Evidence vs. Working Hypotheses

### Verified

- **Revision A printed and fitted on a Bambu Lab P1S: dimensions good, thread
  good.** The thread clearances (`fit_thread_r` 0.25, `fit_thread_a` 0.15) and
  the trapezoidal profile are therefore empirical for this printer, not assumed.
- The geometry is internally consistent, manifold, and assembles without
  interference **given the assumed inputs**.
- The internal tangency of PCB and holder follows from the two reported
  diameters and matches the operator's description.
- The mass comparison between sealing strategies is computed from real solids,
  not estimated.

### Assumed (UNVERIFIED)

- Board stack of 6.0 mm (Reading A of the ambiguity).
- PCB Ø25 × 2 mm, holder Ø21 × 4 mm.
- Holder mass 0.6 g and O-ring mass 0.4 g, both estimates that the 10 g budget
  argument depends on.
- Elastic cross-section fitting an 8.6 × 2.0 mm channel.

### Unknown

- Antenna location. No keep-out was designed because none could be grounded.

---

## Open Questions & Next Steps

1. **Print revision B** and check three things the model cannot: that the board
   drops in holder-first without fouling the fill, that the LED is actually
   visible through the Ø16 foam window, and that a tab survives being loaded
   with an elastic.
2. **Measure the total stack height** in one caliper span and the assembly mass
   on a scale. Both feed straight back into `Params`.
3. **Source the O-ring** at ID 26.74 × CS 1.50 mm, or report the nearest stock
   size available so the groove can be re-cut to it.
4. **Mass**: revision B lands 0.89 g over a 10 g target, up from 0.19 g, because
   the cell fill costs about 0.7 g. Roughly 1.0 g of the total is still
   estimated rather than weighed. If the weighed figures confirm the overrun,
   the cheapest reductions are lightening the fill in its thick sector, the cap
   top plate, and the base flange — but a decision on whether 10 g is a hard
   welfare limit or a design aspiration should come first.
5. **No ingress rating is claimed.** IP54 remains an intent, not a test result.
