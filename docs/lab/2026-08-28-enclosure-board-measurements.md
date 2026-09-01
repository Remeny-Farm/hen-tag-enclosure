# Lab Note: Holyiot 25008 Board Measurements for Enclosure CAD

- **Date**: 2026-08-28
- **Author**: Hen-Tag Engineering
- **Status**: Partial / Caliper readings reported, not independently re-measured

---

## Purpose & Objective

Capture the physical board dimensions needed to unblock enclosure CAD, which
`docs/requirements.md` had listed as pending since repository scaffolding.

---

## Reported Measurements

Reported by the operator from caliper readings on the bench board. These have
**not** been independently re-measured or photographed, so they are recorded
here as reported values rather than as verified evidence.

| Quantity | Reported | Note |
|---|---|---|
| PCB outline | Ø25 mm, circular | Round board, not rectangular |
| PCB thickness | 2 mm | See ambiguity below |
| CR2032 holder outline | Ø21 mm | |
| CR2032 holder height | 4 mm | See ambiguity below |
| Bottom-side protrusion | not measured | Operator: "the panel is about 2 mm tall with everything" |
| Antenna location | not identifiable | "does not show, does not stick out anywhere" |

### Unresolved ambiguity in the height chain

The two height figures can be read two ways and the operator elected to proceed
without re-measuring:

- **Reading A (assumed)**: 2 mm is the full board envelope including bottom-side
  components; the 4 mm holder sits on top of it. Total stack **6.0 mm**.
- **Reading B**: 4 mm already contains the board. Total stack **4.0 mm**.

The CAD assumes **Reading A** and states the assumption in
`cad/hen_tag_enclosure.py`. A single caliper measurement of the whole
sandwich -- lowest point of the board to the top of a seated cell -- resolves
this. The design absorbs roughly +/-0.4 mm around the assumption via a foam pad,
so a wrong reading is recoverable by changing the pad, not by reprinting.

---

## Derived Geometry (verified by construction)

The holder is **internally tangent** to the PCB: the operator reports that the
two circles touch at exactly one point, and that the cell edge is flush with the
PCB edge there, which is where the cell slides in.

This is not an independent measurement but a geometric consequence that the two
reported diameters confirm:

```
centre offset = R_pcb - R_holder = 12.5 - 10.5 = 2.0 mm
```

Modelled and checked in `cad/verify.py`: edge gap at the tangent point
is 0.0000 mm, and the widest exposed PCB crescent opposite it is 4.00 mm. The
reported description and the reported diameters are therefore self-consistent.

Consequence for the enclosure: no rotationally symmetric shoulder can clamp the
board from above, because at the tangent point there is zero exposed PCB. The
design clamps the cell instead. See `DESIGN.md`.

---

## Key Decisions

- Proceed to CAD on Reading A, with every board dimension marked UNVERIFIED in
  the source and the tolerance absorbed by a replaceable foam pad.
- Do not design an antenna keep-out. The antenna could not be located, and
  inventing a zone would violate the no-invented-hardware rule. PETG is a low
  loss dielectric; the existing prohibition on conductive filament remains the
  operative RF constraint.

---

## Open Questions & Verification Items

1. **Total stack height** with a seated CR2032, measured in one span. Resolves
   Reading A vs. B.
2. **Assembly mass on a scale**: bare board, holder, and cell. The 10 g budget
   argument currently rests on two estimated figures (holder 0.6 g, O-ring
   0.4 g) and a calculated PCB mass.
3. **Elastic cross-section**: actual width and thickness of the 8 mm harness
   material. The strap channel is cut 8.6 x 2.0 mm on an assumed profile.
4. **O-ring**: actual ID and cord thickness of the ring to be used. The design
   calls for ID 26.74 x CS 1.50 mm; the previously specified 30 x 2 mm ring does
   not fit this geometry.
5. **Antenna location**, from vendor documentation or a board photograph under
   raking light.
