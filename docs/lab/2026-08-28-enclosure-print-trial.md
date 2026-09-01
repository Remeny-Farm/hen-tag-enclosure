# Lab Note: Enclosure Print Trial, Revision A

- **Date**: 2026-08-28
- **Author**: Hen-Tag Engineering
- **Status**: Completed / Fit confirmed on printed parts

---

## Purpose & Objective

First physical print of the generated enclosure geometry, to confirm that the
modelled thread clearances and cavity dimensions survive contact with a real
FDM machine before committing to a revision.

---

## Verified Evidence

- **Printer**: Bambu Lab P1S.
- **Parts printed**: revision A body and cap as exported from
  `cad/hen_tag_enclosure.py`.
- **Result — dimensions**: reported good by the operator. The Ø25 board cavity
  and the 6.0 mm stack height accepted the hardware as modelled.
- **Result — thread**: reported good. The Tr28.6 × 1.0 trapezoidal pair with
  `fit_thread_r = 0.25` / `fit_thread_a = 0.15` mates on printed parts without
  binding or excessive play.

This is the first entry in this repository where enclosure geometry moves from
modelled to physically confirmed. It validates the print-process parameters —
clearances, wall thicknesses, thread profile — not the board dimensions those
parts were sized around, which remain unverified caliper readings.

---

## Technical Interpretation & Findings

1. **The thread clearance figures are now empirical, not assumed.** The values
   in `Params` can be treated as a known-good baseline for this printer and
   should not be changed without a fresh coupon print.
2. **The trapezoidal profile choice is validated for FDM.** A 30° included
   angle at 1.0 mm pitch prints and mates on a 0.4 mm nozzle.
3. **No dimensional correction was required** between the modelled and printed
   parts, so no printer-specific compensation factor is needed in the source.

---

## Key Decisions

Revision B, driven by the operator after handling the printed parts:

1. **Board orientation inverted.** The holder now faces down toward the harness
   and the PCB faces up, away from the bird, so the LED on the PCB is visible
   through the transparent cap. Previously the PCB faced down and the LED was
   pointed at the animal.
2. **Fill added around the cell.** The crescent of cavity the offset holder
   does not occupy is filled to just below the PCB face, so the enclosure body
   itself retains the holder rather than relying on the cavity wall alone.
3. **Harness moved from under-floor bridges to in-plane side tabs.** The
   underside is now completely flat; each tab carries a transverse slot and a
   bar the elastic wraps. Assembled height drops from 11.50 mm to 8.70 mm.

---

---

## Follow-up: Slicer-Reported Defect in Revision B

Bambu Studio rejected the first revision B body with *"It seems object body.stl
has floating cantilever. Please re-orient the object or enable support
generation."*

**Root cause, confirmed:** the rim's lead-in chamfer was cut with a cone tapering
the wrong way. It thinned the wall to a 0.10 mm knife edge low down and left a
downward-facing annular shelf above it. Mesh analysis located it as ~73 mm² of
near-horizontal down-facing area at z 5.8–5.9.

Verified by slicing both versions of the same part:

| Version | `max_cantilever_dist` | Result |
|---|---|---|
| Inverted chamfer | 1.37 × 10⁶ | floating-cantilever warning |
| Corrected chamfer | 0 | `Success.`, no warnings |

Two further printability items were found and fixed in the same pass:

1. **Thread started 0.2 mm above the base flange**, leaving its first ridge
   floating. Now flush; the body's worst overhang band fell from 18.95 mm² to
   9.36 mm².
2. **The cap exported in design orientation** would have landed opening-down on
   the plate, turning its top plate into a ~28 mm bridge over the cavity. STLs
   are now exported already lying in their print orientation.

All four parts now slice with `Success.` and zero warnings on Bambu Studio
02.08.02.60 at default settings.

---

## Open Questions & Verification Items

1. **Revision B has not been printed.** The fill, the tabs and the inverted
   stack are modelled and machine-checked but physically untested. In
   particular the tab root, which is only as thick as the base flange, has not
   been load-tested with an elastic.
2. **LED visibility through the cap is unconfirmed.** The foam ring leaves a
   Ø16 mm window, but the LED position on the PCB is still unknown, so it is
   not proven that the LED falls inside that window rather than under the ring.
3. **Mass**: revision B models at 10.89 g against the ~10 g target, up from
   10.19 g, because the cell fill adds about 0.7 g. Still unweighed.
4. **Ingress**: no water or dust test has been performed on any revision.
