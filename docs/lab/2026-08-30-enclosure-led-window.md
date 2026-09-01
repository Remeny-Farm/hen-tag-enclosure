# Lab Note: Revision B Body Printed; LED Position for the Cap Window

- **Date**: 2026-08-30
- **Author**: Hen-Tag Engineering
- **Status**: Partial / Photo measurement, awaiting two operator confirmations

---

## Purpose & Objective

Locate the Holyiot 25008 LED in the enclosure's coordinate frame so the cap can
carry a clear window over it while the rest of the cap goes opaque for
customer colours.

---

## Verified Evidence

- **Revision B body printed** (black PETG) and the board seated in it: operator
  photo, 2026-08-30. The in-plane tabs, flat underside and the board sitting
  component-side-up inside the cavity are all visible. This is the first
  physical confirmation that the inverted stack and the cell fill accept the
  board.
- **Cap stop angle is repeatable for a printed pair.** On the rev A trial, the
  two-colour id landed level when the cap was tightened — i.e. the cap's
  angular position at the stop matched the model's nominal. Operator report,
  n = 1 pair.

## Reported / Measured

- Operator: the LED is in the board's "top-left corner", and the board's
  angular position is fixed by the cell holder.
- **Second photo, LED lit** (2026-08-30): with the tab axis vertical and the
  `HOLYIOT-25008` silkscreen toward the top tab, the lit LED sits **8.6 mm
  left of and 3.3 mm below the board centre** — r ≈ 9.2 mm. Taking the
  HOLYIOT-side tab as the model's +X and photo-left as +Y (right-handed,
  viewed from outside), that is **θ ≈ 111°**; if the other tab is +X, 291°.
- An earlier guess from the unlit photo (a small part under the silkscreen at
  r 9.0 / 6°) was **wrong** and is superseded by the lit photo.

- **Caliper, operator (2026-08-30): the LED centre is exactly 2.5 mm in from
  the board edge**, i.e. r = 10.0 mm on the Ø25 board. This supersedes the
  photo radius (9.2 mm, which was ~0.8 mm low — hand-held perspective).

The angle is still photo-derived, and which tab is +X is not derivable from
the photos. With the ring window adopted below, neither matters any more.

---

## Technical Interpretation

The window cannot be a small dot placed "exactly" over the LED, because two
angular tolerances stack between the LED (in the body) and the window (in the
cap):

1. **Board rotation in its pocket**: cavity clearance 0.30 mm, holder pocket
   clearance 0.25 mm, centres 2.0 mm apart → the board can turn
   asin(0.55 / 2.0) ≈ **±16°** before something touches.
2. **Cap stop angle**: with a 1.0 mm pitch, every 0.05 mm of print error in
   the skirt/flange stop faces is 18° of rotation. Repeatable within one
   printed pair (the rev A observation above), but not predictable across
   pairs.

The window is therefore a **10 × 6 mm pill elongated along the rim**: ±25° of
tangential coverage around the nominal LED angle and ±2.2 mm radially, without
growing into a disc that would eat the marking area.

---

## Key Decisions

- Cap becomes three bodies: opaque shell, id inlay, clear window
  (`cad/cap_marking.py`).
- **Window is a clear ring at r 10.0, 3.0 mm wide** (operator decision after
  the angular-tolerance analysis). Rotation-independent, so the +X-tab
  question and the LED angle drop out. Width from the radial tolerance
  chain: board play 0.30 + cap concentricity 0.10 + LED half-size ~0.8 =
  1.2 mm half-width → 2.4 mm minimum; 3.0 keeps 0.3 mm each side. A 2.5 mm
  ring was modelled and rejected: same 75 % id scale, 0.05 mm margin.
- The local pill window (r 9.2 / 111°) is retained as `--pill R THETA` for a
  cap whose angular registration is proven on the bench; not the default.
- Foam ring moves inboard to OD 16 / ID 12, off the LED radius.

---

## Open Questions & Verification Items

1. **Print the three-body ring cap** and check, lit, that the LED shows in
   the ring over a few open/close cycles and after reseating the board.
2. **LED package size.** The 0.8 mm half-size in the tolerance chain is an
   assumption; a caliper on the package, or the vendor part number, pins the
   minimum ring width down.
3. **Inboard foam ring (OD 16 / ID 12)** now bears on the board's r 6–8 zone.
   Confirm nothing tall or pressure-sensitive sits there; the tactile switch
   near the centre is inside the ID and should be untouched.
4. The `--pill` window stays unvalidated; the +X-tab question only returns if
   someone wants to use it.
