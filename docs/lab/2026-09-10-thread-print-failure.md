# Lab Note: Thread Print Failure; Bayonet Closure Adopted (Revision C)

- **Date**: 2026-09-10
- **Author**: Hen-Tag Engineering
- **Status**: Completed (root cause) / Bayonet coupon printed once —
  dimensions good, lock-up angle unreported (print trial 1 below)

---

## Purpose & Objective

Record the operator's report that the cap and its screw thread do not print
cleanly, find the geometric cause, and replace the closure with one whose
every face prints on a 0.4 mm nozzle without support, on both parts, in
their real print orientations.

---

## Reported / Measured

- **Operator, 2026-09-10**: the cap and the screw thread "cannot be printed
  nicely — lots of tearing, too steep." Printer and filament not stated
  beyond the standing transparent-PETG profile (Bambu Lab P1S, 0.4 mm,
  0.16 mm layers).
- This contradicts the 2026-08-28 revision A note, where one printed pair
  was reported to mate without binding. That was a single pair; the caps
  printed since are the three-body clear-shell caps from `cap_marking.py`,
  which carry the same thread.

---

## Technical Interpretation

Computed from the revision B `Params` (Tr28.6 × 1.0, 30° included angle,
0.55 mm deep, `fit_thread_a` 0.15 per flank):

| Feature | Value | Why it tears |
|---|---|---|
| Flank angle from horizontal | 15° | A 75° overhang. Every ridge is a 0.55 mm shelf about three layers tall. |
| Male (body) crest width | 0.35 mm | Below one 0.40 mm extrusion. |
| Female (cap) crest width | **0.05 mm** | (1.0 − 0.647) − 2 × 0.15. A knife edge, two layers tall. |
| Female ridge root width | 0.35 mm | The whole ridge is thinner than one extrusion at its base. |

The cap prints top-plate-down, so its internal ridge is a knife edge hanging
from a 75° overhang. Tearing along the thread is the expected outcome of
this geometry, not a printer fault; the revision A pair mating was one good
print, not evidence the profile is robust. `verify.py`'s overhang check did
not catch it because its limits were calibrated to that same revision A
print.

---

## Key Decisions

1. **The thread is replaced by a three-lug bayonet (revision C).** Lugs on
   the body's seal band (20° × 0.80 mm proud, z 1.80–2.80); L-channels in the
   cap skirt with an entry slot at the open end and a helical lip under the
   circumferential leg. The cap turns **30° clockwise** to lock; the lips
   rise 12 µm per degree (2.7° helix angle, self-locking) and wedge the skirt
   onto the base flange exactly where the thread used to stop it.
2. **Printability rule that sized every number**: on both parts, in print
   orientation, the only flat overhang is the 0.50 mm bearing flat (one
   extrusion width); everything outboard of it is chamfered at 50°. Lugs
   stand on the band, lips hang from the skirt.
3. **Lug and lip bearing faces share one helix pitch**, so at lock they meet
   flat on flat (5.8 mm² over three lugs) rather than edge on face.
4. **Nothing else moved.** Radial seal and groove, cap OD 31.94 mm, grip
   scallops, tabs, lettering, LED ring, the accessory-platform interface and
   the assembly rule "closure below the seal" are unchanged. `cap_marking.py`
   and `hen_tag_platform.py` inherit the new skirt untouched.
5. **Thread code removed** from the source, along with the `bd_warehouse`
   dependency. Commit `e3cf940` has the revision B thread if it is ever
   needed for comparison.

---

## Verification (model only)

`cad/verify.py`, 38 checks, all passing, of which the closure-specific ones:

- cap drops on at the entry angle and the lugs run free for 0–28°:
  0.000 mm³ overlap at every step
- ramp wedges past the lock angle: 0.296 mm³ interference at +4°
- locked cap retained: 5.77 mm³ lug/lip overlap when lifted 0.6 mm; lifts
  off clean at the entry angle
- print-error window the ramp absorbs: −0.36 … +0.30 mm axial; the locked
  angle moves 4.2° per 0.05 mm of error (the thread moved 18°)
- lip 1.41 mm thick at its thin end (8.8 layers)
- worst unsupported overhang band: body 9.36 → **3.03 mm²**, cap total
  242 → 115 mm² (the remaining 96 mm² band is the O-ring groove ceiling,
  unchanged since revision A)

The COMMON and CUT booleans were cross-checked at every pose and agree to
0.001 mm³. OCCT mis-fuses the two helical solids in the *lifted entry* pose
(a 277 mm³ union), so the `section_entry` inspection STL is built as a
compound; the fit checks do not use the fuse. `test_cap_marking.py`: 28/28;
platform coupons: 0.000 mm³ interference against the new body and cap.

---

## Open Questions & Verification Items

1. **Print the coupon pair** (`coupon_body.stl`, `coupon_cap.stl`) and
   record: does the cap drop on with the entry slots over the lugs; at what
   angle does it stop turning freely (nominal 30°, usable 5–55°); break-loose
   torque by feel; O-ring groove profile. The lock-up angle re-tunes
   `cam_lock`; a radial bind re-tunes `fit_lug_r`. Do not file the parts.
2. **Peck/snag resistance.** A bayonet opens with a 30° turn where the
   thread needed several. The platform collar's spring finger was already
   the intended deployment lock; bench a printed cap for break-loose torque
   before any flock trial.
3. **Remaining cap overhang** is the O-ring groove ceiling (1.07 mm wide,
   96 mm² band). It printed on revision A. If tearing persists there, a
   0.4 mm chamfer on the groove's outer corner removes 40 % of it without
   the ring ever touching the chamfer.
4. ~~Revision C has not been sliced yet.~~ Sliced 2026-09-10, no warnings on
   any part; see print trial 1 below.

---

## Print Trial 1 — coupon pair, same day

- **Operator, 2026-09-10 (photo)**: the bayonet coupon pair printed in red
  PETG. **Dimensions reported good.** The cap coupon came off the plate with
  a web of fine strands across its bore, converging near the centre.

### Technical Interpretation

Not a geometry defect: the strands are PETG ooze left on **travel moves**
that fly across the open bore. The G-code was read back to count them
(`cad/slice_check.py`; a travel counts when it is longer than 3 mm and
passes within 12 mm of the axis, above the top plate):

| Part | Stock Bambu profile (2 walls, classic, no travel routing) | 3 walls, Arachne, *Avoid crossing walls* |
|---|---|---|
| `coupon_cap` | **58** travels, 1.4 m | **3** travels, 81 mm |
| `cap` | 107 travels, 2.5 m | 19 travels, 0.4 m |
| `coupon_body` (bore) | 96 travels, 2.1 m | 0 |
| `body` (across the cell pocket) | 102 travels, 2.1 m | 68 travels, 0.8 m |
| `body` (cavity above the fill) | 1 | 0 |

Why the bayonet invites it: in every layer of the lip zone the skirt's
cross-section is a 1.32 mm wall with three 2.17 mm-thick arcs (the lips and
the plain skirt between them), separated by the three entry slots. Three
walls fill the thin part; the extra width of each arc needs its own line, so
the slicer prints three separate islands per layer and hops between them —
straight across the bore unless told to route around. The revision B thread
had the same issue in a different shape (the helical ridge is one arc per
layer): sliced the same way it gave **106** crossing travels on the cap
against revision C's 112, so the strands are not new, only more visible on an
open coupon ring. With travel routing on, the residual 3–19 are layer-change
hops (the nozzle lifts, then travels straight), inside the cap, and pull off
by hand.

No slicer warning was raised for any revision C part with either profile.
The slicer's `max_cantilever_dist` is 0 for the body and body coupon (as on
revisions A and B) and 64 966 for the cap and cap coupon — the revision B cap
measured 64 968, so that figure is the O-ring groove ceiling and the lips add
nothing to it.

### Key Decisions

1. **Three process settings become part of the print profile** and are
   recorded in `DESIGN.md` and `README.md`: wall loops **3**, wall generator
   **Arachne**, **Avoid crossing walls ON**. Nothing in the geometry changes.
2. **`cad/slice_check.py` added**: slices the four printables through the
   Bambu Studio CLI with those settings and fails when open-air travels
   exceed limits set just above today's numbers, or when the slicer warns.
   `--stock` shows the untouched profile for comparison. Skips when Bambu
   Studio is not installed.

### Open Questions & Verification Items

1. Reprint the coupon pair with the three settings and confirm the bore is
   clean; the remaining hairs should be at layer changes only.
2. **Lock-up angle still unreported** — the drop-on and the angle at which
   the cap stops turning freely are the numbers that tune `cam_lock`.
3. If the cell-pocket travels on the full body leave hairs on the cell
   holder, lower the lugs (`lug_z`) to shorten the lip zone, or accept and
   clean; the pocket is closed by the cell in service.
