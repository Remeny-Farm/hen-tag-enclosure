# Hen Tag Physical Enclosure & Ingress Protection

## Purpose & Status
This document specifies the mechanical design criteria, material selection, sealing mechanisms, and PCB coating procedures for the active hen tag enclosure.
- **Status**: Revision C (bayonet closure). Parametric CAD generated and
  machine-verified. **Revision A was printed and fitted on a Bambu Lab P1S —
  dimensions good; its thread mated on that pair, but later caps tore along it,
  so revision C replaced the thread with a bayonet (UNVERIFIED, no coupon
  printed). A revision B body was also printed and accepted the board; the cap
  and complete sealed assembly remain untested.**
- **Source of truth for geometry**: [`DESIGN.md`](../DESIGN.md) and `../cad/hen_tag_enclosure.py`. Where this document and `DESIGN.md` disagree on the sealing arrangement, `DESIGN.md` is current — see "Sealing" below.
- Board dimensions remain operator caliper readings with one unresolved ambiguity: [`docs/lab/2026-08-28-enclosure-board-measurements.md`](lab/2026-08-28-enclosure-board-measurements.md).

---

## Mechanical Specifications & Design Decisions

```
+-----------------------------------------------------------------------------+
| TWO-PART BAYONET-CAP ENCLOSURE, REV C    Assembled: 40.14 x 31.94 x 8.70 mm |
+-----------------------------------------------------------------------------+
|                            O31.94                                           |
|              +------------------------------+   Transparent PETG cap        |
|              | ---  O16 LED window  ---     |   foam recess 0.30            |
|         =====+==============================+=====  ceiling z=6.60          |
|              | :::                :::       |   foam RING OD25/ID16 x 1.0   |
|              | ####### PCB O25 ####### z=6.0|   <-- LED faces the cap, i.e. |
|         O----+ ####################### z=4.0+----O   away from the bird     |
|              |***+--------------------+*****|   O-ring ID 26.74 x CS 1.5    |
|              |***|  CR2032 + holder   |*****|   radial, seals on r=13.70    |
|    ##########+***|  O21, offset 2.0   |*****+##########  bayonet, lugs low  |
|    +-----+   |___+--------------------+_____|   +-----+  BELOW the seal     |
|    |  o  |===|   *** = fill that holds the holder |  o  |===  in-plane tabs |
|    +-----+   +------------------------------+   +-----+   slot 8.8 x 1.8    |
|                     FLAT UNDERSIDE                        bar 1.5           |
+-----------------------------------------------------------------------------+
```

### 1. Material Selection
- **Enclosure Body & Cap**: Transparent PETG (Polyethylene Terephthalate Glycol).
  - *Rationale*: PETG provides superior impact resistance, UV stability, low moisture absorption, and excellent layer adhesion compared to PLA.
- **Strict Prohibition on Conductive Filament**:
  > [!IMPORTANT]
  > Under no circumstances may carbon-fiber filled or conductive filaments be used. Conductive additives detune the 2.4 GHz PCB antenna and create electrostatic discharge / shorting hazards with exposed coin cell terminals.

### 2. Sealing & Water Ingress Protection

> [!IMPORTANT]
> **Superseded.** The axial face seal below was replaced by a **radial** seal
> during CAD. A face seal must sit outboard of the cap skirt, forcing a Ø36 mm
> flange around a Ø25 mm board — measured at 11.88 g assembled against a 10 g
> target. The radial seal needs no flange and lands at 10.19 g.
> The ring size changed with it: **ID 26.74 × CS 1.50 mm**, not 30 × 2 mm.
> Do not order the 30 × 2 ring. Rationale and the measured comparison are in
> [`DESIGN.md`](../DESIGN.md).

- **Gasket (current)**: NBR O-ring, ID 26.74 × CS 1.50 mm, 22 % squeeze.
- **Sealing Mechanism (current)**: Radial seal in a groove in the cap bore,
  compressed against a plain band on the body. Compression is set by the bore
  diameter, so it does not depend on how hard the cap is tightened — which is
  what the superseded design needed a stop flange to control.
- **Closure**: Three-lug bayonet — 0.80 mm lugs on the body, self-locking
  helical ramps in the cap, 30° clockwise to lock — positioned **below** the
  seal so the O-ring never crosses the lugs. Replaced the Tr28.6 × 1.0 thread
  on 2026-09-10 after caps tore along it; see
  [`DESIGN.md`](../DESIGN.md#9-bayonet-not-a-thread) decision 9 and
  [`docs/lab/2026-09-10-thread-print-failure.md`](lab/2026-09-10-thread-print-failure.md).
  UNVERIFIED in print.
- **Target Ingress Rating**: Realistic IP54-level dust and splash protection.
  No certified ingress rating is claimed, and none has been tested.

<details>
<summary>Original face-seal specification (historical)</summary>

- **Gasket**: NBR O-ring, nominal dimensions around 30 x 2 mm.
- **Sealing Mechanism**: Axial face-seal compressed by a threaded screw cap with defined stop-flange to prevent O-ring over-compression or shearing.

</details>

### 3. Conformal Coating Protocol
To protect bare board traces from moisture condensation and corrosive ammonia vapours:
- Apply a thin acrylic conformal coating across the Holyiot 25008 PCB.
- **Mandatory Masking Zones**:
  - SWD programming pads / test points (for future firmware flashing and debugging).
  - Battery holder spring contacts (positive leaf and negative base pad).
  - 2.4 GHz PCB trace antenna (preferably masked to avoid dielectric loading and RF detuning).

### 4. Form Factor & Battery Fitment
- Designed specifically around the Holyiot 25008 module with integrated CR2032 coin cell holder.
  > [!NOTE]
  > Historical or experimental concepts utilizing CR2477 cells are **stale** and superseded. The active enclosure volume is strictly sized for CR2032 cells.

---

## Verified Evidence vs. Working Hypotheses

### Verified Evidence
- Holyiot 25008 board with CR2032 battery holder physically observed on test bench.
- PCB and holder are **internally tangent**: the cell edge is flush with the PCB edge at one point. Confirmed geometrically from the reported Ø25 and Ø21 diameters (2.00 mm centre offset, 0.0000 mm edge gap).
- **Revision A printed on a Bambu Lab P1S — dimensions good; its thread mated on that pair.** The thread has since been replaced by the revision C bayonet after later caps tore along it (`docs/lab/2026-09-10-thread-print-failure.md`). See [`docs/lab/2026-08-28-enclosure-print-trial.md`](lab/2026-08-28-enclosure-print-trial.md).
- Revision B geometry is watertight and assembles without interference — 29
  machine checks in `../cad/verify.py`, all passing, and all four parts slice clean
  in Bambu Studio. Its printed body accepted the board in the intended
  component-up orientation. The revision B cap, sealed assembly and load path
  remain physically untested.

### Key Decisions
- Two-part transparent PETG bayonet cap with a **radial** NBR O-ring (ID 26.74 × CS 1.50 mm). The 30 × 2 mm face-seal ring is superseded.
- Closure positioned below the seal, so the cap can actually be assembled and the O-ring never crosses it. Revision C's closure is a bayonet; the thread it replaced tore in print.
- **Holder faces down toward the harness, PCB faces up.** The LED is on the PCB and must be readable through the cap rather than pointed at the bird.
- **Fill around the cell** so the body itself retains the holder: 100 % of the holder circumference is backed by fill or by the cavity wall.
- Board clamped by a foam **ring** (OD 25 × ID 16 × 1.0 mm) on the PCB rim, leaving a Ø16 LED window. Ring, not disc, so the LED stays visible.
- **Harness moved to in-plane side tabs**; the underside is now completely flat and the assembled height dropped from 11.50 mm to 8.70 mm.
- Masked conformal coating applied before field deployment.
- No antenna keep-out designed. The antenna could not be located, and inventing a zone would breach the no-invented-hardware rule.

### Open Questions & Next Steps
1. **Print the revision C bayonet coupons, then the cap and complete assembly.** The body/board
   fit is observed, but the model cannot prove cap fit, LED visibility through
   the current clear-shell/inlay design, sealing, or that a tab survives an
   elastic under load.
2. **Total stack height** in one caliper span, board bottom to seated cell top. Resolves the ambiguity the CAD currently assumes past.
3. **Weigh the assembly**: bare board, holder, cell. Revision B models at 10.92 g against the ~10 g target, and about 1.0 g of that is estimated rather than measured.
4. **Source the O-ring** at ID 26.74 × CS 1.50 mm, or report the nearest stock size so the groove can be re-cut.
5. **Elastic cross-section**: the tab slot is cut 8.8 × 1.8 mm on an assumption.
